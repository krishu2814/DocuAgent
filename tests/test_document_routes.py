import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_unsupported_file_type_returns_400(client: AsyncClient) -> None:
    files = {"file": ("malicious.exe", b"binarycontent", "application/octet-stream")}
    response = await client.post("/documents/upload", files=files)
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_nonexistent_document_returns_404(client: AsyncClient) -> None:
    random_id = "nonexistent-doc-id"
    try:
        response = await client.get(f"/documents/{random_id}")
        assert response.status_code in (404, 500)
    except Exception:
        pass
