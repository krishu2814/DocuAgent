import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["project"] == "DocuAgent"
    assert data["environment"] == "development"


@pytest.mark.asyncio
async def test_frontend_home_page(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    assert "DocuAgent" in response.text
    assert "Knowledge Base" in response.text
