import pytest
from datetime import datetime
from database import NetworkNode, NetworkEdge, Chat, GraphUpdate
from sqlalchemy import select


@pytest.mark.asyncio
async def test_network_node_creation():
    from tests.conftest import TestAsyncSessionLocal
    async with TestAsyncSessionLocal() as session:
        node = NetworkNode(
            name="db-test-node",
            type="router",
            ip_address="10.0.0.1",
            status="active",
            layer="network",
            position_x=100.0,
            position_y=200.0,
            node_metadata={"test": True},
            last_updated=datetime.now()
        )
        session.add(node)
        await session.commit()

        result = await session.execute(select(NetworkNode).where(NetworkNode.name == "db-test-node"))
        fetched = result.scalar_one()
        assert fetched.name == "db-test-node"
        assert fetched.type == "router"
        assert fetched.ip_address == "10.0.0.1"
        assert fetched.position_x == 100.0


@pytest.mark.asyncio
async def test_network_edge_relationships():
    from tests.conftest import TestAsyncSessionLocal
    async with TestAsyncSessionLocal() as session:
        node1 = NetworkNode(name="edge-node-1", type="router", node_metadata={}, last_updated=datetime.now())
        node2 = NetworkNode(name="edge-node-2", type="switch", node_metadata={}, last_updated=datetime.now())
        session.add_all([node1, node2])
        await session.flush()

        edge = NetworkEdge(
            source_id=node1.id,
            target_id=node2.id,
            type="ethernet",
            bandwidth="1Gbps",
            utilization=50.0,
            status="active",
            edge_metadata={},
            last_updated=datetime.now()
        )
        session.add(edge)
        await session.commit()

        result = await session.execute(select(NetworkEdge))
        fetched_edge = result.scalar_one()
        assert fetched_edge.source_id == node1.id
        assert fetched_edge.target_id == node2.id
        assert fetched_edge.bandwidth == "1Gbps"


@pytest.mark.asyncio
async def test_chat_model():
    from tests.conftest import TestAsyncSessionLocal
    async with TestAsyncSessionLocal() as session:
        chat = Chat(
            session_id="test-session",
            message="Hello",
            response="Hi there!",
            timestamp=datetime.now()
        )
        session.add(chat)
        await session.commit()

        result = await session.execute(select(Chat).where(Chat.session_id == "test-session"))
        fetched = result.scalar_one()
        assert fetched.message == "Hello"
        assert fetched.response == "Hi there!"


@pytest.mark.asyncio
async def test_graph_update_model():
    from tests.conftest import TestAsyncSessionLocal
    async with TestAsyncSessionLocal() as session:
        update = GraphUpdate(
            update_type="node_created",
            entity_type="node",
            entity_id=1,
            old_data=None,
            new_data={"name": "new-node"},
            source="api",
            timestamp=datetime.now()
        )
        session.add(update)
        await session.commit()

        result = await session.execute(select(GraphUpdate))
        fetched = result.scalar_one()
        assert fetched.update_type == "node_created"
        assert fetched.entity_type == "node"
        assert fetched.new_data == {"name": "new-node"}
