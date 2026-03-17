import pytest


@pytest.mark.asyncio
async def test_create_node(client):
    node_data = {
        "name": "new-router",
        "type": "router",
        "ip_address": "10.0.0.1",
        "status": "active",
        "layer": "network",
        "position": {"x": 0.0, "y": 0.0},
        "metadata": {"vendor": "juniper"}
    }
    resp = await client.post("/network/nodes", json=node_data)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    node = data["node"]
    assert node["name"] == "new-router"
    assert node["type"] == "router"
    assert node["ip_address"] == "10.0.0.1"
    assert node["status"] == "active"


@pytest.mark.asyncio
async def test_get_nodes(client, seed_nodes):
    resp = await client.get("/network/nodes")
    assert resp.status_code == 200
    nodes = resp.json()
    assert len(nodes) >= 3
    names = [n["name"] for n in nodes]
    assert "test-router" in names
    assert "test-switch" in names
    assert "test-server" in names


@pytest.mark.asyncio
async def test_get_graph(client, seed_nodes):
    resp = await client.get("/network/graph")
    assert resp.status_code == 200
    data = resp.json()
    assert "nodes" in data
    assert "edges" in data
    assert "last_updated" in data
    assert len(data["nodes"]) >= 3


@pytest.mark.asyncio
async def test_update_node(client, seed_nodes):
    node_id = seed_nodes[0]["id"]
    resp = await client.put(f"/network/nodes/{node_id}", json={
        "name": seed_nodes[0]["name"],
        "type": seed_nodes[0]["type"],
        "status": "warning",
        "position": {"x": 0, "y": 0},
        "metadata": {}
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["node"]["status"] == "warning"


@pytest.mark.asyncio
async def test_delete_node(client, seed_nodes):
    node_id = seed_nodes[2]["id"]
    resp = await client.delete(f"/network/nodes/{node_id}")
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # Verify it's gone
    resp = await client.get("/network/nodes")
    node_ids = [n["id"] for n in resp.json()]
    assert node_id not in node_ids


@pytest.mark.asyncio
async def test_create_edge(client, seed_nodes):
    edge_data = {
        "source": seed_nodes[0]["id"],
        "target": seed_nodes[2]["id"],
        "type": "wireless",
        "bandwidth": "100Mbps",
        "utilization": 10.0,
        "status": "active",
        "metadata": {}
    }
    resp = await client.post("/network/edges", json=edge_data)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    edge = data["edge"]
    assert edge["source"] == seed_nodes[0]["id"]
    assert edge["target"] == seed_nodes[2]["id"]
    assert edge["type"] == "wireless"


@pytest.mark.asyncio
async def test_update_edge(client, seed_edges):
    edge_id = seed_edges[0]["id"]
    resp = await client.put(f"/network/edges/{edge_id}", json={
        "source": seed_edges[0]["source"],
        "target": seed_edges[0]["target"],
        "utilization": 80.0,
        "metadata": {}
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["edge"]["utilization"] == 80.0


@pytest.mark.asyncio
async def test_delete_edge(client, seed_edges):
    edge_id = seed_edges[0]["id"]
    resp = await client.delete(f"/network/edges/{edge_id}")
    assert resp.status_code == 200
    assert resp.json()["success"] is True


@pytest.mark.asyncio
async def test_get_network_stats(client, seed_nodes, seed_edges):
    resp = await client.get("/network/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_nodes"] >= 3
    assert data["total_edges"] >= 2


@pytest.mark.asyncio
async def test_delete_node_cascades_edges(client, seed_nodes, seed_edges):
    """Deleting a node should also remove its connected edges"""
    # seed_nodes[1] (switch) is connected by both edges
    node_id = seed_nodes[1]["id"]
    resp = await client.delete(f"/network/nodes/{node_id}")
    assert resp.status_code == 200

    # Both edges should be gone
    resp = await client.get("/network/graph")
    data = resp.json()
    for edge in data["edges"]:
        assert edge["source"] != node_id
        assert edge["target"] != node_id
