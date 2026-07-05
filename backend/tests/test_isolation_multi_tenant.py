"""Un opérateur de l'administration A ne doit en aucun cas pouvoir accéder aux
données de l'administration B (docs/PIVOT_SAAS_B2G.md § 8, item critique)."""

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


async def _creer_examen(client: AsyncClient, headers: dict) -> str:
    response = await client.post(
        "/api/v1/admin/exams",
        json={"type_examen": "BAC", "annee": 2026, "libelle": "BAC 2026"},
        headers=headers,
    )
    return response.json()["id"]


async def _creer_ingestion(client: AsyncClient, headers: dict, examen_id: str) -> str:
    contenu = _construire_xlsx([["001", "Ouaga 1", "Traore", "Awa", None, "Admis", None]])
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
        headers=headers,
    )
    return response.json()["id"]


@pytest.mark.asyncio
async def test_publish_exam_dune_autre_administration_renvoie_404(
    client: AsyncClient, admin_headers: dict, autre_administration_headers: dict
) -> None:
    exam_id = await _creer_examen(client, admin_headers)

    response = await client.post(
        f"/api/v1/admin/exams/{exam_id}/publish", headers=autre_administration_headers
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_exams_ne_montre_pas_les_examens_dune_autre_administration(
    client: AsyncClient, admin_headers: dict, autre_administration_headers: dict
) -> None:
    await _creer_examen(client, admin_headers)

    response = await client.get("/api/v1/admin/exams", headers=autre_administration_headers)

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_upload_ingestion_sur_examen_dune_autre_administration_renvoie_404(
    client: AsyncClient, admin_headers: dict, autre_administration_headers: dict
) -> None:
    exam_id = await _creer_examen(client, admin_headers)
    contenu = _construire_xlsx([["001", "Ouaga 1", "Traore", "Awa", None, "Admis", None]])

    response = await client.post(
        "/api/v1/admin/ingestions",
        data={"examen_id": exam_id, "type_fichier": "EXCEL"},
        files={
            "file": (
                "resultats.xlsx",
                contenu,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        headers=autre_administration_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_ingestion_dune_autre_administration_renvoie_404(
    client: AsyncClient, admin_headers: dict, autre_administration_headers: dict
) -> None:
    exam_id = await _creer_examen(client, admin_headers)
    ingestion_id = await _creer_ingestion(client, admin_headers, exam_id)

    response = await client.get(
        f"/api/v1/admin/ingestions/{ingestion_id}", headers=autre_administration_headers
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_ingestions_ne_montre_pas_celles_dune_autre_administration(
    client: AsyncClient, admin_headers: dict, autre_administration_headers: dict
) -> None:
    exam_id = await _creer_examen(client, admin_headers)
    await _creer_ingestion(client, admin_headers, exam_id)

    response = await client.get("/api/v1/admin/ingestions", headers=autre_administration_headers)

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_correct_ingestion_dune_autre_administration_renvoie_404(
    client: AsyncClient, admin_headers: dict, autre_administration_headers: dict
) -> None:
    exam_id = await _creer_examen(client, admin_headers)
    ingestion_id = await _creer_ingestion(client, admin_headers, exam_id)

    response = await client.patch(
        f"/api/v1/admin/ingestions/{ingestion_id}",
        json={"lignes": []},
        headers=autre_administration_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_publish_ingestion_dune_autre_administration_renvoie_404(
    client: AsyncClient, admin_headers: dict, autre_administration_headers: dict
) -> None:
    exam_id = await _creer_examen(client, admin_headers)
    ingestion_id = await _creer_ingestion(client, admin_headers, exam_id)

    response = await client.post(
        f"/api/v1/admin/ingestions/{ingestion_id}/publish", headers=autre_administration_headers
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_reject_ingestion_dune_autre_administration_renvoie_404(
    client: AsyncClient, admin_headers: dict, autre_administration_headers: dict
) -> None:
    exam_id = await _creer_examen(client, admin_headers)
    ingestion_id = await _creer_ingestion(client, admin_headers, exam_id)

    response = await client.post(
        f"/api/v1/admin/ingestions/{ingestion_id}/reject", headers=autre_administration_headers
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_chaque_administration_ne_voit_que_ses_propres_examens(
    client: AsyncClient, admin_headers: dict, autre_administration_headers: dict
) -> None:
    await _creer_examen(client, admin_headers)
    await _creer_examen(client, autre_administration_headers)
    await _creer_examen(client, autre_administration_headers)

    reponse_a = await client.get("/api/v1/admin/exams", headers=admin_headers)
    reponse_b = await client.get("/api/v1/admin/exams", headers=autre_administration_headers)

    assert len(reponse_a.json()) == 1
    assert len(reponse_b.json()) == 2


@pytest.mark.asyncio
async def test_utilisateur_sans_administration_est_rejete(client: AsyncClient, db_session) -> None:
    """Un compte SUPER_ADMIN/SUPPORT (administration_id NULL) ne peut pas utiliser les
    routes tenant-scopées : il n'a par définition aucune administration à filtrer."""
    from app.core.security import hash_password
    from app.models import RoleUtilisateur, Utilisateur

    db_session.add(
        Utilisateur(
            email="superadmin@faso-resultats.bf",
            mot_de_passe_hash=hash_password("ChangeMe123!"),
            nom_complet="Super Admin",
            role=RoleUtilisateur.SUPER_ADMIN,
            administration_id=None,
        )
    )
    await db_session.commit()

    login = await client.post(
        "/api/v1/admin/login",
        json={"email": "superadmin@faso-resultats.bf", "password": "ChangeMe123!"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/admin/exams", headers=headers)

    assert response.status_code == 400
