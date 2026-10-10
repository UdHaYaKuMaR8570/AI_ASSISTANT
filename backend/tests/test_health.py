import pytest
from httpx import ASGITransport, AsyncClient
from app.main import create_app


@pytest.mark.anyio
async def test_health_structure():
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] in ("ok", "degraded")
    assert "checks" in body
    assert "db" in body["checks"]
    assert "ollama" in body["checks"]
    assert "litellm" in body["checks"]


@pytest.mark.anyio
async def test_config_endpoint():
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/config")
    assert resp.status_code == 200
    body = resp.json()
    assert "default_provider" in body
    assert "available_providers" in body
    assert len(body["available_providers"]) == 4
