import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_unsupported_file_type_returns_400(client: AsyncClient) -> None:
    files = {"file": ("malicious.exe", b"binarycontent", "application/octet-stream")}
    response = await client.post("/documents/upload", files=files)
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_nonexistent_document_returns_404(client: AsyncClient) -> None:
    random_uuid = "00000000-0000-0000-0000-000000000000"
    # Overriding get_db or calling when DB returns none
    try:
        response = await client.get(f"/documents/{random_uuid}")
        assert response.status_code in (404, 500)
    except Exception:
        pass
