"""Rate limiting sur les endpoints candidat sensibles au fallback OTP (mécanisme 3,
docs/PROFIL_CANDIDAT_UNIFIE.md § 5) : un flood de requêtes doit être bloqué (429)."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Examen


async def _creer_examen(client: AsyncClient, admin_headers: dict, db_session: AsyncSession):
    response = await client.post(
        "/api/v1/admin/exams",
        json={"type_examen": "CONCOURS_DIRECT", "annee": 2026, "libelle": "Concours"},
        headers=admin_headers,
    )
    examen_id = response.json()["id"]
    examen = await db_session.get(Examen, examen_id)
    return examen_id, str(examen.administration_id)


@pytest.mark.asyncio
async def test_flood_sur_ajout_de_candidature_renvoie_429(
    client: AsyncClient, admin_headers: dict, candidat_headers: dict, db_session: AsyncSession
) -> None:
    """POST /candidat/candidatures (déclenche l'OTP du mécanisme 3 automatiquement) est
    l'endpoint le plus proche de « demander un OTP » dans ce codebase : il n'existe pas
    de route /demander-otp séparée — l'envoi de l'OTP fallback est intégré à l'ajout de
    candidature lui-même."""
    examen_id, administration_id = await _creer_examen(client, admin_headers, db_session)

    codes = []
    for i in range(15):
        response = await client.post(
            "/api/v1/candidat/candidatures",
            json={
                "administration_id": administration_id,
                "examen_id": examen_id,
                "numero_recepisse": f"00000{i}",
            },
            headers=candidat_headers,
        )
        codes.append(response.status_code)

    assert 429 in codes


@pytest.mark.asyncio
async def test_flood_sur_confirmation_otp_renvoie_429(
    client: AsyncClient,
    admin_headers: dict,
    candidat_headers: dict,
    db_session: AsyncSession,
) -> None:
    examen_id, administration_id = await _creer_examen(client, admin_headers, db_session)

    creation = await client.post(
        "/api/v1/candidat/candidatures",
        json={
            "administration_id": administration_id,
            "examen_id": examen_id,
            "numero_recepisse": "000999",
        },
        headers=candidat_headers,
    )
    candidature_id = creation.json()["id"]

    codes = []
    for _ in range(15):
        response = await client.post(
            f"/api/v1/candidat/candidatures/{candidature_id}/confirmer-otp",
            json={"code": "000000"},
            headers=candidat_headers,
        )
        codes.append(response.status_code)

    assert 429 in codes
