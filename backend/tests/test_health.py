import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    """Test that the health endpoint returns 200 with correct payload"""
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
