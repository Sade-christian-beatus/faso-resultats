"""Endpoints super-admin de gestion des partenaires B2B et de leurs clés API
(docs/ROADMAP.md § Phase 4) — fondation technique avant intégration commerciale."""

import pytest
from httpx import AsyncClient

_PAYLOAD_PARTENAIRE = {
    "nom": "École Privée Test",
    "contact_nom": "Référent Partenaire",
    "contact_email": "contact@ecole-test.bf",
}


async def _creer_partenaire(client: AsyncClient, super_admin_headers: dict) -> dict:
    response = await client.post(
        "/api/v1/admin/partenaires", json=_PAYLOAD_PARTENAIRE, headers=super_admin_headers
    )
    return response.json()


@pytest.mark.asyncio
async def test_creation_partenaire_requiert_super_admin(
    client: AsyncClient, admin_headers: dict
) -> None:
    response = await client.post(
        "/api/v1/admin/partenaires", json=_PAYLOAD_PARTENAIRE, headers=admin_headers
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_creation_partenaire_sans_token_rejetee(client: AsyncClient) -> None:
    response = await client.post("/api/v1/admin/partenaires", json=_PAYLOAD_PARTENAIRE)

    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_super_admin_cree_un_partenaire(
    client: AsyncClient, super_admin_headers: dict
) -> None:
    partenaire = await _creer_partenaire(client, super_admin_headers)

    assert partenaire["nom"] == "École Privée Test"
    assert partenaire["statut"] == "ACTIF"


@pytest.mark.asyncio
async def test_super_admin_suspend_un_partenaire(
    client: AsyncClient, super_admin_headers: dict
) -> None:
    partenaire = await _creer_partenaire(client, super_admin_headers)

    response = await client.patch(
        f"/api/v1/admin/partenaires/{partenaire['id']}",
        json={"statut": "SUSPENDU"},
        headers=super_admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["statut"] == "SUSPENDU"


@pytest.mark.asyncio
async def test_emission_cle_api_renvoie_la_cle_en_clair_une_seule_fois(
    client: AsyncClient, super_admin_headers: dict
) -> None:
    partenaire = await _creer_partenaire(client, super_admin_headers)

    creation = await client.post(
        f"/api/v1/admin/partenaires/{partenaire['id']}/api-keys",
        json={},
        headers=super_admin_headers,
    )

    assert creation.status_code == 201
    corps = creation.json()
    assert corps["cle"].startswith("frb_live_")
    assert corps["tier"] == "STANDARD"
    assert corps["quota_quotidien"] == 1000
    assert corps["statut"] == "ACTIVE"

    liste = await client.get(
        f"/api/v1/admin/partenaires/{partenaire['id']}/api-keys", headers=super_admin_headers
    )
    assert liste.status_code == 200
    assert "cle" not in liste.json()[0]
    assert liste.json()[0]["prefixe"] == corps["prefixe"]


@pytest.mark.asyncio
async def test_revocation_cle_api(client: AsyncClient, super_admin_headers: dict) -> None:
    partenaire = await _creer_partenaire(client, super_admin_headers)
    creation = await client.post(
        f"/api/v1/admin/partenaires/{partenaire['id']}/api-keys",
        json={},
        headers=super_admin_headers,
    )
    api_key_id = creation.json()["id"]

    revocation = await client.post(
        f"/api/v1/admin/partenaires/{partenaire['id']}/api-keys/{api_key_id}/revoke",
        headers=super_admin_headers,
    )

    assert revocation.status_code == 200
    assert revocation.json()["statut"] == "REVOQUEE"
