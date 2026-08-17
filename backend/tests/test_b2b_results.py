"""API B2B (docs/ROADMAP.md § Phase 4) : mêmes données que l'API publique, mais
authentifiée par clé API (en-tête X-API-Key) avec un quota par clé plutôt qu'un
rate-limit par IP."""

import io

import openpyxl
import pytest
from httpx import AsyncClient


def _construire_xlsx(lignes: list[list]) -> bytes:
    classeur = openpyxl.Workbook()
    feuille = classeur.active
    feuille.append(
        ["Numéro PV", "Jury", "Nom", "Prénom", "Date de naissance", "Décision", "Moyenne"]
    )
    for ligne in lignes:
        feuille.append(ligne)
    buffer = io.BytesIO()
    classeur.save(buffer)
    return buffer.getvalue()


async def _publier_examen_avec_resultat(client: AsyncClient, admin_headers: dict) -> dict:
    exam_response = await client.post(
        "/api/v1/admin/exams",
        json={"type_examen": "BAC", "annee": 2026, "libelle": "BAC 2026"},
        headers=admin_headers,
    )
    examen = exam_response.json()

    contenu = _construire_xlsx([["001", "Ouaga 1", "Traore", "Awa", "12/05/2008", "Admis", 13.45]])
    upload = await client.post(
        "/api/v1/admin/ingestions",
        data={"examen_id": examen["id"], "type_fichier": "EXCEL"},
        files={
            "file": (
                "resultats.xlsx",
                contenu,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        headers=admin_headers,
    )
    ingestion_id = upload.json()["id"]
    await client.post(f"/api/v1/admin/ingestions/{ingestion_id}/publish", headers=admin_headers)
    await client.post(f"/api/v1/admin/exams/{examen['id']}/publish", headers=admin_headers)
    return examen


async def _emettre_cle_api(
    client: AsyncClient, super_admin_headers: dict, *, quota_quotidien: int = 1000
) -> str:
    partenaire = await client.post(
        "/api/v1/admin/partenaires",
        json={
            "nom": "Partenaire Test",
            "contact_nom": "Référent",
            "contact_email": "contact@partenaire-test.bf",
        },
        headers=super_admin_headers,
    )
    creation = await client.post(
        f"/api/v1/admin/partenaires/{partenaire.json()['id']}/api-keys",
        json={"quota_quotidien": quota_quotidien},
        headers=super_admin_headers,
    )
    return creation.json()["cle"]


@pytest.mark.asyncio
async def test_b2b_sans_cle_api_rejete(client: AsyncClient) -> None:
    response = await client.get("/api/v1/b2b/exams")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_b2b_avec_cle_invalide_rejete(client: AsyncClient) -> None:
    response = await client.get("/api/v1/b2b/exams", headers={"X-API-Key": "frb_live_invalide"})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_b2b_liste_les_examens_publies(
    client: AsyncClient, admin_headers: dict, super_admin_headers: dict
) -> None:
    examen = await _publier_examen_avec_resultat(client, admin_headers)
    cle = await _emettre_cle_api(client, super_admin_headers)

    response = await client.get("/api/v1/b2b/exams", headers={"X-API-Key": cle})

    assert response.status_code == 200
    assert response.json()[0]["id"] == examen["id"]


@pytest.mark.asyncio
async def test_b2b_recherche_resultat_meme_champs_que_public(
    client: AsyncClient, admin_headers: dict, super_admin_headers: dict
) -> None:
    examen = await _publier_examen_avec_resultat(client, admin_headers)
    cle = await _emettre_cle_api(client, super_admin_headers)

    response = await client.get(
        "/api/v1/b2b/results",
        params={"examen_id": examen["id"], "numero_pv": "001", "jury": "Ouaga 1"},
        headers={"X-API-Key": cle},
    )

    assert response.status_code == 200
    corps = response.json()[0]
    assert corps["nom"] == "Traore"
    assert corps["decision"] == "ADMIS"
    # Pas d'accès élargi aux données sensibles pour un partenaire B2B.
    assert "date_naissance" not in corps
    assert "lieu_naissance" not in corps
    assert "numero_cnib" not in corps


@pytest.mark.asyncio
async def test_b2b_cle_revoquee_rejetee(
    client: AsyncClient, admin_headers: dict, super_admin_headers: dict
) -> None:
    partenaire = await client.post(
        "/api/v1/admin/partenaires",
        json={
            "nom": "Partenaire À Révoquer",
            "contact_nom": "Référent",
            "contact_email": "contact@a-revoquer.bf",
        },
        headers=super_admin_headers,
    )
    creation = await client.post(
        f"/api/v1/admin/partenaires/{partenaire.json()['id']}/api-keys",
        json={},
        headers=super_admin_headers,
    )
    cle = creation.json()["cle"]
    await client.post(
        f"/api/v1/admin/partenaires/{partenaire.json()['id']}/api-keys/{creation.json()['id']}/revoke",
        headers=super_admin_headers,
    )

    response = await client.get("/api/v1/b2b/exams", headers={"X-API-Key": cle})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_b2b_partenaire_suspendu_rejete_meme_avec_cle_active(
    client: AsyncClient, admin_headers: dict, super_admin_headers: dict
) -> None:
    partenaire = await client.post(
        "/api/v1/admin/partenaires",
        json={
            "nom": "Partenaire À Suspendre",
            "contact_nom": "Référent",
            "contact_email": "contact@a-suspendre.bf",
        },
        headers=super_admin_headers,
    )
    creation = await client.post(
        f"/api/v1/admin/partenaires/{partenaire.json()['id']}/api-keys",
        json={},
        headers=super_admin_headers,
    )
    cle = creation.json()["cle"]
    await client.patch(
        f"/api/v1/admin/partenaires/{partenaire.json()['id']}",
        json={"statut": "SUSPENDU"},
        headers=super_admin_headers,
    )

    response = await client.get("/api/v1/b2b/exams", headers={"X-API-Key": cle})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_b2b_quota_quotidien_depasse_renvoie_429(
    client: AsyncClient, admin_headers: dict, super_admin_headers: dict
) -> None:
    await _publier_examen_avec_resultat(client, admin_headers)
    cle = await _emettre_cle_api(client, super_admin_headers, quota_quotidien=2)

    premiere = await client.get("/api/v1/b2b/exams", headers={"X-API-Key": cle})
    deuxieme = await client.get("/api/v1/b2b/exams", headers={"X-API-Key": cle})
    troisieme = await client.get("/api/v1/b2b/exams", headers={"X-API-Key": cle})

    assert premiere.status_code == 200
    assert deuxieme.status_code == 200
    assert troisieme.status_code == 429


@pytest.mark.asyncio
async def test_b2b_met_a_jour_derniere_utilisation(
    client: AsyncClient, admin_headers: dict, super_admin_headers: dict
) -> None:
    partenaire = await client.post(
        "/api/v1/admin/partenaires",
        json={
            "nom": "Partenaire Utilisation",
            "contact_nom": "Référent",
            "contact_email": "contact@utilisation.bf",
        },
        headers=super_admin_headers,
    )
    creation = await client.post(
        f"/api/v1/admin/partenaires/{partenaire.json()['id']}/api-keys",
        json={},
        headers=super_admin_headers,
    )
    cle = creation.json()["cle"]

    await client.get("/api/v1/b2b/exams", headers={"X-API-Key": cle})

    liste = await client.get(
        f"/api/v1/admin/partenaires/{partenaire.json()['id']}/api-keys", headers=super_admin_headers
    )
    assert liste.json()[0]["derniere_utilisation"] is not None
