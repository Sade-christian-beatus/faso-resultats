"""Validation applicative de administration_id/examen_id à l'ajout d'une candidature :
Candidature n'a pas de FK vers ces tables (schéma plateforme indépendant, voir
docs/MULTI_TENANCY.md), donc sans ce contrôle un candidat pourrait créer des
candidatures orphelines référençant des UUID inexistants."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Administration, Examen, StatutAdministration


async def _creer_examen(client: AsyncClient, admin_headers: dict, db_session: AsyncSession):
    response = await client.post(
        "/api/v1/admin/exams",
        json={"type_examen": "BAC", "annee": 2026, "libelle": "BAC 2026"},
        headers=admin_headers,
    )
    examen_id = response.json()["id"]
    examen = await db_session.get(Examen, examen_id)
    return examen_id, str(examen.administration_id)


@pytest.mark.asyncio
async def test_ajout_avec_administration_id_invalide_renvoie_404(
    client: AsyncClient, admin_headers: dict, candidat_headers: dict, db_session: AsyncSession
) -> None:
    examen_id, _ = await _creer_examen(client, admin_headers, db_session)

    response = await client.post(
        "/api/v1/candidat/candidatures",
        json={
            "administration_id": str(uuid.uuid4()),
            "examen_id": examen_id,
            "numero_recepisse": "000001",
        },
        headers=candidat_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_ajout_avec_examen_id_invalide_renvoie_404(
    client: AsyncClient, admin_headers: dict, candidat_headers: dict, db_session: AsyncSession
) -> None:
    _, administration_id = await _creer_examen(client, admin_headers, db_session)

    response = await client.post(
        "/api/v1/candidat/candidatures",
        json={
            "administration_id": administration_id,
            "examen_id": str(uuid.uuid4()),
            "numero_recepisse": "000002",
        },
        headers=candidat_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_ajout_sur_administration_suspendue_renvoie_404(
    client: AsyncClient,
    admin_headers: dict,
    candidat_headers: dict,
    db_session: AsyncSession,
) -> None:
    examen_id, administration_id = await _creer_examen(client, admin_headers, db_session)
    administration = await db_session.get(Administration, administration_id)
    administration.statut = StatutAdministration.SUSPENDU
    await db_session.commit()

    response = await client.post(
        "/api/v1/candidat/candidatures",
        json={
            "administration_id": administration_id,
            "examen_id": examen_id,
            "numero_recepisse": "000003",
        },
        headers=candidat_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_ajout_sur_administration_pilote_reste_autorise(
    client: AsyncClient, admin_headers: dict, candidat_headers: dict, db_session: AsyncSession
) -> None:
    """PILOTE est un statut opérationnel (les 3 tenants de démonstration du seed le
    sont) : il ne doit pas être bloqué par la validation."""
    examen_id, administration_id = await _creer_examen(client, admin_headers, db_session)
    administration = await db_session.get(Administration, administration_id)
    administration.statut = StatutAdministration.PILOTE
    await db_session.commit()

    response = await client.post(
        "/api/v1/candidat/candidatures",
        json={
            "administration_id": administration_id,
            "examen_id": examen_id,
            "numero_recepisse": "000004",
        },
        headers=candidat_headers,
    )

    assert response.status_code == 201
