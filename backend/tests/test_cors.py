import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cors_preflight_allows_patch_on_admin_ingestions(client: AsyncClient) -> None:
    """Régression : le correctif d'une ingestion (PATCH) doit passer le preflight CORS,
    sinon la correction échoue silencieusement dans tout vrai navigateur (curl ne le
    détecte pas, seul un navigateur envoie une requête preflight OPTIONS).
    """
    response = await client.options(
        "/api/v1/admin/ingestions/00000000-0000-0000-0000-000000000000",
        headers={
            "Origin": "http://localhost:8080",
            "Access-Control-Request-Method": "PATCH",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:8080"
    allowed_methods = response.headers.get("access-control-allow-methods", "")
    assert "PATCH" in allowed_methods
