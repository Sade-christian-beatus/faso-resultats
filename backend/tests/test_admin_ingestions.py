import io

import openpyxl
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Resultat


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


async def _creer_examen(client: AsyncClient, admin_headers: dict) -> str:
    response = await client.post(
        "/api/v1/admin/exams",
        json={"type_examen": "BAC", "annee": 2026, "libelle": "BAC 2026"},
        headers=admin_headers,
    )
    return response.json()["id"]


@pytest.mark.asyncio
async def test_upload_excel_valide_cree_apercu_sans_erreur(
    client: AsyncClient, admin_headers: dict
) -> None:
    examen_id = await _creer_examen(client, admin_headers)
    contenu = _construire_xlsx([["001", "Ouaga 1", "Traore", "Awa", "12/05/2008", "Admis", 13.45]])

    response = await client.post(
        "/api/v1/admin/ingestions",
        data={"examen_id": examen_id, "type_fichier": "EXCEL"},
        files={
            "file": (
                "resultats.xlsx",
                contenu,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        headers=admin_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["statut"] == "PREVISUALISATION"
    assert body["nombre_lignes_detectees"] == 1
    assert body["nombre_erreurs"] == 0
    assert body["lignes"][0]["donnees"]["numero_pv"] == "001"


@pytest.mark.asyncio
async def test_upload_rejette_extension_incompatible(
    client: AsyncClient, admin_headers: dict
) -> None:
    examen_id = await _creer_examen(client, admin_headers)

    response = await client.post(
        "/api/v1/admin/ingestions",
        data={"examen_id": examen_id, "type_fichier": "EXCEL"},
        files={"file": ("resultats.pdf", b"%PDF-1.4", "application/pdf")},
        headers=admin_headers,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_upload_examen_introuvable(client: AsyncClient, admin_headers: dict) -> None:
    contenu = _construire_xlsx([])

    response = await client.post(
        "/api/v1/admin/ingestions",
        data={"examen_id": "00000000-0000-0000-0000-000000000000", "type_fichier": "EXCEL"},
        files={
            "file": (
                "resultats.xlsx",
                contenu,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        headers=admin_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_publish_bloque_si_erreurs_restantes(
    client: AsyncClient, admin_headers: dict
) -> None:
    examen_id = await _creer_examen(client, admin_headers)
    # Ligne incomplète : nom manquant.
    contenu = _construire_xlsx([["001", "Ouaga 1", None, "Awa", None, "Admis", None]])

    upload = await client.post(
        "/api/v1/admin/ingestions",
        data={"examen_id": examen_id, "type_fichier": "EXCEL"},
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

    response = await client.post(
        f"/api/v1/admin/ingestions/{ingestion_id}/publish", headers=admin_headers
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_correction_puis_publication_cree_les_resultats(
    client: AsyncClient, admin_headers: dict, db_session: AsyncSession
) -> None:
    examen_id = await _creer_examen(client, admin_headers)
    contenu = _construire_xlsx([["001", "Ouaga 1", None, "Awa", None, "Admis", None]])

    upload = await client.post(
        "/api/v1/admin/ingestions",
        data={"examen_id": examen_id, "type_fichier": "EXCEL"},
        files={
            "file": (
                "resultats.xlsx",
                contenu,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        headers=admin_headers,
    )
    ingestion = upload.json()

    ligne_corrigee = ingestion["lignes"][0]
    ligne_corrigee["donnees"]["nom"] = "Traore"
    ligne_corrigee["erreurs"] = []

    correction = await client.patch(
        f"/api/v1/admin/ingestions/{ingestion['id']}",
        json={"lignes": [ligne_corrigee]},
        headers=admin_headers,
    )
    assert correction.status_code == 200
    assert correction.json()["nombre_erreurs"] == 0

    publish = await client.post(
        f"/api/v1/admin/ingestions/{ingestion['id']}/publish", headers=admin_headers
    )

    assert publish.status_code == 200
    assert publish.json()["statut"] == "PUBLIEE"

    resultats = (await db_session.execute(select(Resultat))).scalars().all()
    assert len(resultats) == 1
    assert resultats[0].nom == "Traore"
    assert resultats[0].ingestion_id is not None


@pytest.mark.asyncio
async def test_reject_ingestion(client: AsyncClient, admin_headers: dict) -> None:
    examen_id = await _creer_examen(client, admin_headers)
    contenu = _construire_xlsx([["001", "Ouaga 1", "Traore", "Awa", None, "Admis", None]])

    upload = await client.post(
        "/api/v1/admin/ingestions",
        data={"examen_id": examen_id, "type_fichier": "EXCEL"},
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

    response = await client.post(
        f"/api/v1/admin/ingestions/{ingestion_id}/reject", headers=admin_headers
    )

    assert response.status_code == 200
    assert response.json()["statut"] == "REJETEE"


@pytest.mark.asyncio
async def test_ingestions_require_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/admin/ingestions")

    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_list_ingestions_filtered_by_examen(client: AsyncClient, admin_headers: dict) -> None:
    examen_id = await _creer_examen(client, admin_headers)
    autre_examen_id = await _creer_examen(client, admin_headers)
    contenu = _construire_xlsx([["001", "Ouaga 1", "Traore", "Awa", None, "Admis", None]])

    await client.post(
        "/api/v1/admin/ingestions",
        data={"examen_id": examen_id, "type_fichier": "EXCEL"},
        files={
            "file": (
                "resultats.xlsx",
                contenu,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        headers=admin_headers,
    )

    response = await client.get(
        "/api/v1/admin/ingestions", params={"examen_id": autre_examen_id}, headers=admin_headers
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_ingestion_introuvable(client: AsyncClient, admin_headers: dict) -> None:
    response = await client.get(
        "/api/v1/admin/ingestions/00000000-0000-0000-0000-000000000000",
        headers=admin_headers,
    )

    assert response.status_code == 404
