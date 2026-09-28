"""Administrations SUSPENDU / RESILIE invisibles côté public et B2B (audit 2026-08-17).

`/api/v1/public/administrations` ne listait déjà que les administrations ACTIF/PILOTE,
mais `/exams` et `/results` (public et B2B) continuaient de servir les examens et
résultats d'un tenant suspendu ou résilié.
"""

import pytest
from httpx import AsyncClient

from tests.test_b2b_results import _emettre_cle_api
from tests.test_public_results import _publier_examen_avec_resultat


async def _changer_statut_tenant(
    client: AsyncClient, super_admin_headers: dict, statut: str, code: str = "tenant-test"
) -> None:
    administrations = await client.get("/api/v1/admin/administrations", headers=super_admin_headers)
    administration_id = next(a["id"] for a in administrations.json() if a["code"] == code)
    response = await client.patch(
        f"/api/v1/admin/administrations/{administration_id}",
        json={"statut": statut},
        headers=super_admin_headers,
    )
    assert response.status_code == 200


def _params_recherche(examen: dict) -> dict:
    return {"examen_id": examen["id"], "numero_pv": "001", "jury": "Ouaga 1"}


@pytest.mark.asyncio
@pytest.mark.parametrize("statut", ["SUSPENDU", "RESILIE"])
async def test_examens_et_resultats_invisibles_cote_public(
    client: AsyncClient, admin_headers: dict, super_admin_headers: dict, statut: str
) -> None:
    examen = await _publier_examen_avec_resultat(client, admin_headers)
    # Liste mise en cache avant le changement de statut : doit être invalidée.
    assert len((await client.get("/api/v1/public/exams")).json()) == 1

    await _changer_statut_tenant(client, super_admin_headers, statut)

    assert (await client.get("/api/v1/public/exams")).json() == []
    assert (await client.get("/api/v1/public/administrations")).json() == []
    resultat = await client.get("/api/v1/public/results", params=_params_recherche(examen))
    assert resultat.status_code == 404
    assert resultat.json()["detail"] == "Aucun résultat trouvé"


@pytest.mark.asyncio
@pytest.mark.parametrize("statut", ["SUSPENDU", "RESILIE"])
async def test_examens_et_resultats_invisibles_cote_b2b(
    client: AsyncClient, admin_headers: dict, super_admin_headers: dict, statut: str
) -> None:
    examen = await _publier_examen_avec_resultat(client, admin_headers)
    cle = await _emettre_cle_api(client, super_admin_headers)
    headers_b2b = {"X-API-Key": cle}
    assert len((await client.get("/api/v1/b2b/exams", headers=headers_b2b)).json()) == 1

    await _changer_statut_tenant(client, super_admin_headers, statut)

    assert (await client.get("/api/v1/b2b/exams", headers=headers_b2b)).json() == []
    resultat = await client.get(
        "/api/v1/b2b/results", params=_params_recherche(examen), headers=headers_b2b
    )
    assert resultat.status_code == 404


@pytest.mark.asyncio
@pytest.mark.parametrize("statut", ["ACTIF", "PILOTE"])
async def test_examens_et_resultats_visibles_pour_un_tenant_actif_ou_pilote(
    client: AsyncClient, admin_headers: dict, super_admin_headers: dict, statut: str
) -> None:
    examen = await _publier_examen_avec_resultat(client, admin_headers)

    await _changer_statut_tenant(client, super_admin_headers, statut)

    assert len((await client.get("/api/v1/public/exams")).json()) == 1
    resultat = await client.get("/api/v1/public/results", params=_params_recherche(examen))
    assert resultat.status_code == 200


@pytest.mark.asyncio
async def test_reactivation_rend_de_nouveau_visible(
    client: AsyncClient, admin_headers: dict, super_admin_headers: dict
) -> None:
    await _publier_examen_avec_resultat(client, admin_headers)
    await _changer_statut_tenant(client, super_admin_headers, "SUSPENDU")
    assert (await client.get("/api/v1/public/exams")).json() == []

    await _changer_statut_tenant(client, super_admin_headers, "ACTIF")

    assert len((await client.get("/api/v1/public/exams")).json()) == 1


@pytest.mark.asyncio
async def test_suspension_n_affecte_pas_les_autres_tenants(
    client: AsyncClient,
    admin_headers: dict,
    autre_administration_headers: dict,
    super_admin_headers: dict,
) -> None:
    await _publier_examen_avec_resultat(client, admin_headers)
    examen_autre = await _publier_examen_avec_resultat(client, autre_administration_headers)

    await _changer_statut_tenant(client, super_admin_headers, "SUSPENDU")

    examens = (await client.get("/api/v1/public/exams")).json()
    assert [e["id"] for e in examens] == [examen_autre["id"]]
