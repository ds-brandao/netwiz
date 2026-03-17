import os
import pytest
import tempfile
from unittest.mock import AsyncMock, MagicMock

# Set dummy API key before any imports that touch agent.py
os.environ.setdefault("LLAMA_API_KEY", "test-key-not-used")

# Create a temp file for the SQLite database
_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.close(_db_fd)
TEST_DB_URL = f"sqlite+aiosqlite:///{_db_path}"

# Override database before importing app
import database
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from contextlib import asynccontextmanager


# Create test engine using file-based SQLite
test_engine = create_async_engine(
    TEST_DB_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)
TestAsyncSessionLocal = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

# Monkey-patch the database module before anything imports app
database.engine = test_engine
database.AsyncSessionLocal = TestAsyncSessionLocal


@asynccontextmanager
async def test_get_db_session():
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


database.get_db_session = test_get_db_session

# Also patch it in graph_service and tools since they import it directly
import graph_service as gs_module
gs_module.get_db_session = test_get_db_session

import tools as tools_module
tools_module.get_db_session = test_get_db_session

# Create tables synchronously at module load (avoids event loop issues)
_sync_engine = create_engine(f"sqlite:///{_db_path}", connect_args={"check_same_thread": False})
database.Base.metadata.create_all(_sync_engine)
_sync_engine.dispose()


@pytest.fixture(autouse=True)
async def cleanup_database():
    """Clean data after each test (tables already exist)"""
    yield
    # Clear all data but keep tables
    async with test_engine.begin() as conn:
        for table in reversed(database.Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    # Reset graph service cache between tests
    gs_module.graph_service._cache_valid = False
    gs_module.graph_service._graph_cache = {"nodes": {}, "edges": {}, "last_updated": None}


@pytest.fixture
def app():
    from app import app
    return app


@pytest.fixture
async def client(app):
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def seed_nodes(client):
    """Create sample nodes and return their data"""
    nodes = [
        {
            "name": "test-router",
            "type": "router",
            "ip_address": "192.168.1.1",
            "status": "active",
            "layer": "network",
            "position": {"x": 100.0, "y": 200.0},
            "metadata": {"vendor": "cisco"}
        },
        {
            "name": "test-switch",
            "type": "switch",
            "ip_address": "192.168.1.2",
            "status": "active",
            "layer": "datalink",
            "position": {"x": 300.0, "y": 200.0},
            "metadata": {"ports": "24"}
        },
        {
            "name": "test-server",
            "type": "server",
            "ip_address": "192.168.1.3",
            "status": "warning",
            "layer": "application",
            "position": {"x": 500.0, "y": 200.0},
            "metadata": {"os": "linux"}
        }
    ]
    created = []
    for node in nodes:
        resp = await client.post("/network/nodes", json=node)
        assert resp.status_code == 200, f"Failed to create node: {resp.text}"
        data = resp.json()
        created.append(data["node"])
    return created


@pytest.fixture
async def seed_edges(client, seed_nodes):
    """Create sample edges between seeded nodes"""
    edges = [
        {
            "source": seed_nodes[0]["id"],
            "target": seed_nodes[1]["id"],
            "type": "ethernet",
            "bandwidth": "1Gbps",
            "utilization": 45.0,
            "status": "active",
            "metadata": {}
        },
        {
            "source": seed_nodes[1]["id"],
            "target": seed_nodes[2]["id"],
            "type": "fiber",
            "bandwidth": "10Gbps",
            "utilization": 20.0,
            "status": "active",
            "metadata": {}
        }
    ]
    created = []
    for edge in edges:
        resp = await client.post("/network/edges", json=edge)
        assert resp.status_code == 200, f"Failed to create edge: {resp.text}"
        data = resp.json()
        created.append(data["edge"])
    return created
