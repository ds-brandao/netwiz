import pytest
from unittest.mock import AsyncMock, patch
from graph_service import GraphService


@pytest.mark.asyncio
async def test_get_graph_returns_dict():
    service = GraphService()
    graph = await service.get_graph()
    assert "nodes" in graph
    assert "edges" in graph
    assert "last_updated" in graph
    assert isinstance(graph["nodes"], dict)
    assert isinstance(graph["edges"], dict)


@pytest.mark.asyncio
async def test_cache_invalidation():
    service = GraphService()

    # Load graph to populate cache
    await service.get_graph()
    assert service._cache_valid is True

    # Invalidate
    await service._invalidate_cache()
    assert service._cache_valid is False


@pytest.mark.asyncio
async def test_create_node_invalidates_cache():
    service = GraphService()

    # Pre-load cache
    await service.get_graph()
    assert service._cache_valid is True

    # Create a node
    with patch("graph_service.connection_manager") as mock_cm:
        mock_cm.broadcast_graph_update = AsyncMock()
        node = await service.create_node({
            "name": "cache-test-node",
            "type": "router",
            "position": {"x": 0, "y": 0},
            "metadata": {}
        })

    assert node is not None
    assert node["name"] == "cache-test-node"

    # Cache should have been invalidated and re-loaded
    graph = await service.get_graph()
    assert any(n["name"] == "cache-test-node" for n in graph["nodes"].values())


@pytest.mark.asyncio
async def test_update_nonexistent_node_raises():
    service = GraphService()
    with pytest.raises(ValueError, match="not found"):
        with patch("graph_service.connection_manager") as mock_cm:
            mock_cm.broadcast_graph_update = AsyncMock()
            await service.update_node("99999", {"status": "active"})


@pytest.mark.asyncio
async def test_get_graph_stats_counts():
    service = GraphService()

    # Get initial count
    initial_stats = await service.get_graph_stats()
    initial_count = initial_stats["total_nodes"]

    with patch("graph_service.connection_manager") as mock_cm:
        mock_cm.broadcast_graph_update = AsyncMock()

        await service.create_node({
            "name": "stats-node-1", "type": "router", "status": "active",
            "position": {"x": 0, "y": 0}, "metadata": {}
        })
        await service.create_node({
            "name": "stats-node-2", "type": "switch", "status": "warning",
            "position": {"x": 0, "y": 0}, "metadata": {}
        })

    stats = await service.get_graph_stats()
    assert stats["total_nodes"] == initial_count + 2
    assert stats["node_status_counts"].get("active", 0) >= 1
    assert stats["node_status_counts"].get("warning", 0) >= 1


@pytest.mark.asyncio
async def test_create_node_broadcasts():
    service = GraphService()

    with patch("graph_service.connection_manager") as mock_cm:
        mock_cm.broadcast_graph_update = AsyncMock()
        await service.create_node({
            "name": "broadcast-test",
            "type": "server",
            "position": {"x": 0, "y": 0},
            "metadata": {}
        })
        mock_cm.broadcast_graph_update.assert_called_once()
        args = mock_cm.broadcast_graph_update.call_args
        assert args[0][0] == "created"
        assert args[0][1] == "node"
