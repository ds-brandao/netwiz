import pytest
from unittest.mock import AsyncMock, MagicMock
from websocket_manager import ConnectionManager


@pytest.fixture
def manager():
    return ConnectionManager()


def make_mock_ws():
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    return ws


@pytest.mark.asyncio
async def test_connect_and_disconnect(manager):
    ws = make_mock_ws()
    await manager.connect(ws, "session1")

    assert manager.get_connection_count() == 1
    assert manager.get_session_count() == 1

    manager.disconnect(ws)
    assert manager.get_connection_count() == 0
    assert manager.get_session_count() == 0


@pytest.mark.asyncio
async def test_send_to_session(manager):
    ws1 = make_mock_ws()
    ws2 = make_mock_ws()

    await manager.connect(ws1, "session1")
    await manager.connect(ws2, "session1")

    await manager.send_to_session("session1", {"msg": "hello"})

    # Both should have received the message (accept + initial confirm + our message)
    assert ws1.send_text.call_count >= 2
    assert ws2.send_text.call_count >= 2


@pytest.mark.asyncio
async def test_broadcast(manager):
    ws1 = make_mock_ws()
    ws2 = make_mock_ws()

    await manager.connect(ws1, "session1")
    await manager.connect(ws2, "session2")

    await manager.broadcast({"msg": "broadcast"})

    # Both should receive broadcast
    assert ws1.send_text.call_count >= 2
    assert ws2.send_text.call_count >= 2


@pytest.mark.asyncio
async def test_broadcast_with_exclude(manager):
    ws1 = make_mock_ws()
    ws2 = make_mock_ws()

    await manager.connect(ws1, "session1")
    await manager.connect(ws2, "session2")

    # Reset call counts after connect
    ws1.send_text.reset_mock()
    ws2.send_text.reset_mock()

    await manager.broadcast({"msg": "selective"}, exclude_session="session1")

    assert ws1.send_text.call_count == 0
    assert ws2.send_text.call_count == 1


@pytest.mark.asyncio
async def test_get_connection_count(manager):
    assert manager.get_connection_count() == 0

    ws1 = make_mock_ws()
    ws2 = make_mock_ws()
    ws3 = make_mock_ws()

    await manager.connect(ws1, "s1")
    await manager.connect(ws2, "s1")
    await manager.connect(ws3, "s2")

    assert manager.get_connection_count() == 3
    assert manager.get_session_count() == 2


@pytest.mark.asyncio
async def test_disconnect_on_send_error(manager):
    ws = make_mock_ws()
    await manager.connect(ws, "session1")
    assert manager.get_connection_count() == 1

    # Make send_text raise an error
    ws.send_text.side_effect = Exception("connection closed")
    await manager.send_to_session("session1", {"msg": "fail"})

    # Should have been cleaned up
    assert manager.get_connection_count() == 0
