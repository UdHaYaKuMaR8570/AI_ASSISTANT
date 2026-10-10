import pytest
from httpx import ASGITransport, AsyncClient
from app.main import create_app
from app.db import get_db
from unittest.mock import AsyncMock, patch


@pytest.mark.anyio
async def test_session_lifecycle():
    app = create_app()

    # Mock DB session and repos for isolated unit testing
    mock_db = AsyncMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Validation error on missing user_id
        res = await client.post("/api/sessions", json={})
        assert res.status_code == 422
        body = res.json()
        assert "error" in body
        assert body["error"]["code"] == "validation_error"


@pytest.mark.anyio
async def test_search_endpoint_validation():
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Invalid search (empty query)
        res = await client.post("/api/search", json={"query": ""})
        assert res.status_code == 422
