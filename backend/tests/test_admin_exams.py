import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_exam_defaults_to_draft(client: AsyncClient, admin_headers: dict) -> None:
    response = await client.post(
        "/api/v1/admin/exams",
        json={"type_examen": "BAC", "annee": 2026, "libelle": "BAC 2026 - Session normale"},
        headers=admin_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["statut"] == "DRAFT"


@pytest.mark.asyncio
async def test_create_exam_requires_auth(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/admin/exams", json={"type_examen": "BAC", "annee": 2026, "libelle": "BAC 2026"}
    )

    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_publish_exam_changes_statut(client: AsyncClient, admin_headers: dict) -> None:
    create_response = await client.post(
        "/api/v1/admin/exams",
        json={"type_examen": "CEP", "annee": 2026, "libelle": "CEP 2026"},
        headers=admin_headers,
    )
    exam_id = create_response.json()["id"]

    response = await client.post(f"/api/v1/admin/exams/{exam_id}/publish", headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["statut"] == "PUBLISHED"


@pytest.mark.asyncio
async def test_list_exams(client: AsyncClient, admin_headers: dict) -> None:
    await client.post(
        "/api/v1/admin/exams",
        json={"type_examen": "BEPC", "annee": 2026, "libelle": "BEPC 2026"},
        headers=admin_headers,
    )

    response = await client.get("/api/v1/admin/exams", headers=admin_headers)

    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_create_exam_champs_par_defaut_non_invasifs(
    client: AsyncClient, admin_headers: dict
) -> None:
    """Les nouveaux champs de cartographie (categorie, source_donnees...) ne doivent
    pas être requis à la création : une charge utile minimale doit toujours marcher."""
    response = await client.post(
        "/api/v1/admin/exams",
        json={"type_examen": "BAC", "annee": 2026, "libelle": "BAC 2026"},
        headers=admin_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["categorie"] is None
    assert body["source_donnees"] == "FILE_IMPORT"
    assert body["partenariat_officiel"] is False
    assert body["phases_publication"] == []


@pytest.mark.asyncio
async def test_create_exam_avec_la_taxonomie_etendue(
    client: AsyncClient, admin_headers: dict
) -> None:
    """La taxonomie étendue (concours paramilitaires, catégories de concours direct...)
    est utilisable en plus des valeurs historiques (BAC, CONCOURS_DIRECT)."""
    response = await client.post(
        "/api/v1/admin/exams",
        json={
            "type_examen": "ARMEE",
            "annee": 2026,
            "libelle": "Concours Armée 2026",
            "categorie": "CONCOURS_PARAMILITAIRE",
            "ministere_tutelle": "Ministère de la Défense",
            "source_donnees": "PRESS_MONITORING",
            "phases_publication": ["EPREUVES_SPORTIVES", "ADMISSIBILITE", "ADMISSION_DEFINITIVE"],
        },
        headers=admin_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["type_examen"] == "ARMEE"
    assert body["categorie"] == "CONCOURS_PARAMILITAIRE"
    assert body["source_donnees"] == "PRESS_MONITORING"
    assert body["phases_publication"] == [
        "EPREUVES_SPORTIVES",
        "ADMISSIBILITE",
        "ADMISSION_DEFINITIVE",
    ]
