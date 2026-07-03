import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models import Admin

EMAIL = "admin@faso-resultats.bf"
PASSWORD = "ChangeMe123!"


async def _create_admin(db_session: AsyncSession, *, actif: bool = True) -> Admin:
    admin = Admin(
        email=EMAIL, mot_de_passe_hash=hash_password(PASSWORD), nom_complet="Admin", actif=actif
    )
    db_session.add(admin)
    await db_session.commit()
    return admin


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_admin(db_session)

    response = await client.post("/api/v1/admin/login", json={"email": EMAIL, "password": PASSWORD})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_admin(db_session)

    response = await client.post(
        "/api/v1/admin/login", json={"email": EMAIL, "password": "mauvais-mot-de-passe"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client: AsyncClient, db_session: AsyncSession) -> None:
    response = await client.post(
        "/api/v1/admin/login", json={"email": "inconnu@faso-resultats.bf", "password": PASSWORD}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_admin_rejected(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_admin(db_session, actif=False)

    response = await client.post("/api/v1/admin/login", json={"email": EMAIL, "password": PASSWORD})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_token(client: AsyncClient) -> None:
    response = await client.get("/api/v1/admin/me")

    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_me_with_valid_token(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_admin(db_session)
    login_response = await client.post(
        "/api/v1/admin/login", json={"email": EMAIL, "password": PASSWORD}
    )
    token = login_response.json()["access_token"]

    response = await client.get("/api/v1/admin/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == EMAIL


@pytest.mark.asyncio
async def test_me_with_invalid_token_rejected(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/admin/me", headers={"Authorization": "Bearer token-invalide"}
    )

    assert response.status_code == 401
