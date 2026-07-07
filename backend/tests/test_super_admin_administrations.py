"""Endpoints super-admin de gestion des administrations clientes
(docs/PIVOT_SAAS_B2G.md § 8, item 8) : ferme le manque d'onboarding self-service —
jusqu'ici seul seed.py ou un accès direct base permettait de créer un tenant."""

import pytest
from httpx import AsyncClient

_PAYLOAD_ADMINISTRATION = {
    "code": "nouvelle-admin",
    "nom_officiel": "Nouvelle Administration",
    "sigle": "NA",
    "ministere_tutelle": "Ministère de test",
    "contact_referent_nom": "Référent",
    "contact_referent_email": "contact@nouvelle-admin.bf",
    "contact_referent_telephone": "+22600000000",
}


@pytest.mark.asyncio
async def test_creation_administration_requiert_super_admin(
    client: AsyncClient, admin_headers: dict
) -> None:
    """Un ADMIN_ADMINISTRATION (tenant) ne peut pas créer d'autres tenants."""
    response = await client.post(
        "/api/v1/admin/administrations", json=_PAYLOAD_ADMINISTRATION, headers=admin_headers
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_creation_administration_sans_token_rejetee(client: AsyncClient) -> None:
    response = await client.post("/api/v1/admin/administrations", json=_PAYLOAD_ADMINISTRATION)

    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_super_admin_cree_une_administration(
    client: AsyncClient, super_admin_headers: dict
) -> None:
    response = await client.post(
        "/api/v1/admin/administrations", json=_PAYLOAD_ADMINISTRATION, headers=super_admin_headers
    )

    assert response.status_code == 201
    body = response.json()
    assert body["code"] == "nouvelle-admin"
    assert body["statut"] == "PILOTE"


@pytest.mark.asyncio
async def test_creation_administration_code_duplique_rejetee(
    client: AsyncClient, super_admin_headers: dict
) -> None:
    await client.post(
        "/api/v1/admin/administrations", json=_PAYLOAD_ADMINISTRATION, headers=super_admin_headers
    )

    response = await client.post(
        "/api/v1/admin/administrations", json=_PAYLOAD_ADMINISTRATION, headers=super_admin_headers
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_super_admin_liste_les_administrations(
    client: AsyncClient, super_admin_headers: dict, admin_headers: dict
) -> None:
    """admin_headers crée déjà une administration "tenant-test" via la fixture."""
    response = await client.get("/api/v1/admin/administrations", headers=super_admin_headers)

    assert response.status_code == 200
    codes = {a["code"] for a in response.json()}
    assert "tenant-test" in codes


@pytest.mark.asyncio
async def test_admin_administration_ne_peut_pas_lister_les_administrations(
    client: AsyncClient, admin_headers: dict
) -> None:
    response = await client.get("/api/v1/admin/administrations", headers=admin_headers)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_super_admin_met_a_jour_le_statut_dune_administration(
    client: AsyncClient, super_admin_headers: dict
) -> None:
    creation = await client.post(
        "/api/v1/admin/administrations", json=_PAYLOAD_ADMINISTRATION, headers=super_admin_headers
    )
    administration_id = creation.json()["id"]

    response = await client.patch(
        f"/api/v1/admin/administrations/{administration_id}",
        json={"statut": "SUSPENDU"},
        headers=super_admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["statut"] == "SUSPENDU"


@pytest.mark.asyncio
async def test_super_admin_cree_le_premier_utilisateur_dun_tenant(
    client: AsyncClient, super_admin_headers: dict
) -> None:
    creation = await client.post(
        "/api/v1/admin/administrations", json=_PAYLOAD_ADMINISTRATION, headers=super_admin_headers
    )
    administration_id = creation.json()["id"]

    response = await client.post(
        f"/api/v1/admin/administrations/{administration_id}/utilisateurs",
        json={
            "email": "admin@nouvelle-admin.bf",
            "password": "ChangeMe123!",
            "nom_complet": "Admin Nouvelle Administration",
        },
        headers=super_admin_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["role"] == "ADMIN_ADMINISTRATION"
    assert body["administration_id"] == administration_id

    # Le nouvel utilisateur peut se connecter et n'a accès qu'à son propre tenant.
    login = await client.post(
        "/api/v1/admin/login", json={"email": "admin@nouvelle-admin.bf", "password": "ChangeMe123!"}
    )
    assert login.status_code == 200


@pytest.mark.asyncio
async def test_creation_utilisateur_avec_role_plateforme_rejetee(
    client: AsyncClient, super_admin_headers: dict
) -> None:
    creation = await client.post(
        "/api/v1/admin/administrations", json=_PAYLOAD_ADMINISTRATION, headers=super_admin_headers
    )
    administration_id = creation.json()["id"]

    response = await client.post(
        f"/api/v1/admin/administrations/{administration_id}/utilisateurs",
        json={
            "email": "faux-super-admin@nouvelle-admin.bf",
            "password": "ChangeMe123!",
            "nom_complet": "Faux Super Admin",
            "role": "SUPER_ADMIN",
        },
        headers=super_admin_headers,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_creation_administration_dans_tenant_inexistant_renvoie_404(
    client: AsyncClient, super_admin_headers: dict
) -> None:
    response = await client.post(
        "/api/v1/admin/administrations/00000000-0000-0000-0000-000000000000/utilisateurs",
        json={
            "email": "x@x.bf",
            "password": "ChangeMe123!",
            "nom_complet": "X",
        },
        headers=super_admin_headers,
    )

    assert response.status_code == 404
