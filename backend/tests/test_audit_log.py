"""AuditLog trace les actions admin clés (docs/PIVOT_SAAS_B2G.md § 8, item 11)."""

import io

import openpyxl
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ActionAuditLog, AuditLog


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


async def _actions_journalisees(db_session: AsyncSession) -> list[ActionAuditLog]:
    result = await db_session.execute(select(AuditLog))
    return [log.action for log in result.scalars().all()]


@pytest.mark.asyncio
async def test_login_est_journalise(
    client: AsyncClient, db_session: AsyncSession, admin_headers: dict
) -> None:
    actions = await _actions_journalisees(db_session)
    assert ActionAuditLog.LOGIN in actions


@pytest.mark.asyncio
async def test_creation_et_publication_examen_journalisees(
    client: AsyncClient, admin_headers: dict, db_session: AsyncSession
) -> None:
    creation = await client.post(
        "/api/v1/admin/exams",
        json={"type_examen": "BAC", "annee": 2026, "libelle": "BAC 2026"},
        headers=admin_headers,
    )
    examen_id = creation.json()["id"]

    await client.post(f"/api/v1/admin/exams/{examen_id}/publish", headers=admin_headers)

    actions = await _actions_journalisees(db_session)
    assert ActionAuditLog.CREATE_EXAMEN in actions
    assert ActionAuditLog.PUBLISH_EXAMEN in actions


@pytest.mark.asyncio
async def test_cycle_ingestion_journalise(
    client: AsyncClient, admin_headers: dict, db_session: AsyncSession
) -> None:
    examen = await client.post(
        "/api/v1/admin/exams",
        json={"type_examen": "BAC", "annee": 2026, "libelle": "BAC 2026"},
        headers=admin_headers,
    )
    examen_id = examen.json()["id"]

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

    await client.post(f"/api/v1/admin/ingestions/{ingestion_id}/reject", headers=admin_headers)

    actions = await _actions_journalisees(db_session)
    assert ActionAuditLog.UPLOAD_INGESTION in actions
    assert ActionAuditLog.REJECT_INGESTION in actions


@pytest.mark.asyncio
async def test_audit_log_capture_administration_et_utilisateur(
    client: AsyncClient, admin_headers: dict, db_session: AsyncSession
) -> None:
    await client.post(
        "/api/v1/admin/exams",
        json={"type_examen": "BAC", "annee": 2026, "libelle": "BAC 2026"},
        headers=admin_headers,
    )

    result = await db_session.execute(
        select(AuditLog).where(AuditLog.action == ActionAuditLog.CREATE_EXAMEN)
    )
    log = result.scalar_one()
    assert log.utilisateur_id is not None
    assert log.administration_id is not None
    assert log.details["examen_id"]
