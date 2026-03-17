import pytest
from unittest.mock import patch, AsyncMock


async def mock_streaming_chat(message, context=None, conversation_history=None):
    """Mock streaming chat that yields text chunks"""
    yield {"type": "text", "content": "Hello! "}
    yield {"type": "text", "content": "I can help with that."}
    yield {"type": "done"}


@pytest.mark.asyncio
async def test_chat_endpoint_returns_response(client):
    with patch("app.simple_streaming_chat", side_effect=mock_streaming_chat):
        resp = await client.post("/chat", json={
            "message": "What is the network status?",
            "session_id": "test-session"
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "response" in data
    assert data["response"] == "Hello! I can help with that."
    assert data["session_id"] == "test-session"


@pytest.mark.asyncio
async def test_get_chat_history(client):
    # First, create a chat record
    with patch("app.simple_streaming_chat", side_effect=mock_streaming_chat):
        await client.post("/chat", json={
            "message": "Test message",
            "session_id": "history-session"
        })

    # Then retrieve history
    resp = await client.get("/chats/history-session")
    assert resp.status_code == 200
    history = resp.json()
    assert len(history) >= 1
    assert history[0]["message"] == "Test message"
    assert history[0]["response"] == "Hello! I can help with that."


@pytest.mark.asyncio
async def test_chat_with_default_session(client):
    with patch("app.simple_streaming_chat", side_effect=mock_streaming_chat):
        resp = await client.post("/chat", json={
            "message": "Hello"
        })
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "default"
