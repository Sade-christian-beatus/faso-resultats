"""Isolation du profil candidat (plateforme, transversal aux tenants) :
docs/PROFIL_CANDIDAT_UNIFIE.md § 2 et § 11, item 10."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Examen
from app.models.candidature import Candidature
from app.models.journal_consultation_profil import JournalConsultationProfil
from app.models.profil_candidat import ProfilCandidat


async def _creer_examen(
    client: AsyncClient, admin_headers: dict, db_session: AsyncSession
) -> tuple[str, str]:
    response = await client.post(
        "/api/v1/admin/exams",
        json={"type_examen": "BAC", "annee": 2026, "libelle": "BAC 2026"},
        headers=admin_headers,
    )
    examen_id = response.json()["id"]
    examen = await db_session.get(Examen, examen_id)
    return examen_id, str(examen.administration_id)


@pytest.mark.asyncio
async def test_candidat_ne_peut_pas_voir_les_candidatures_dun_autre_candidat(
    client: AsyncClient,
    admin_headers: dict,
    candidat_headers: dict,
    autre_candidat_headers: dict,
    db_session: AsyncSession,
) -> None:
    examen_id, administration_id = await _creer_examen(client, admin_headers, db_session)
    await client.post(
        "/api/v1/candidat/candidatures",
        json={
            "administration_id": administration_id,
            "examen_id": examen_id,
            "numero_recepisse": "000001",
        },
        headers=candidat_headers,
    )

    response = await client.get("/api/v1/candidat/candidatures", headers=autre_candidat_headers)

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_candidat_ne_peut_pas_supprimer_la_candidature_dun_autre_candidat(
    client: AsyncClient,
    admin_headers: dict,
    candidat_headers: dict,
    autre_candidat_headers: dict,
    db_session: AsyncSession,
) -> None:
    examen_id, administration_id = await _creer_examen(client, admin_headers, db_session)
    creation = await client.post(
        "/api/v1/candidat/candidatures",
        json={
            "administration_id": administration_id,
            "examen_id": examen_id,
            "numero_recepisse": "000002",
        },
        headers=candidat_headers,
    )
    candidature_id = creation.json()["id"]

    response = await client.delete(
        f"/api/v1/candidat/candidatures/{candidature_id}", headers=autre_candidat_headers
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_token_admin_ne_fonctionne_pas_sur_les_routes_candidat(
    client: AsyncClient, admin_headers: dict
) -> None:
    response = await client.get("/api/v1/candidat/me", headers=admin_headers)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_token_candidat_ne_fonctionne_pas_sur_les_routes_admin(
    client: AsyncClient, candidat_headers: dict
) -> None:
    response = await client.get("/api/v1/admin/exams", headers=candidat_headers)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_administration_na_aucun_endpoint_pour_lister_les_profils_candidats(
    client: AsyncClient, admin_headers: dict
) -> None:
    """Aucune route admin ne doit exposer les profils candidats plateforme — seul le
    candidat lui-même y accède, via son propre token."""
    for chemin in ("/api/v1/admin/candidats", "/api/v1/admin/profils-candidats"):
        response = await client.get(chemin, headers=admin_headers)
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_suppression_profil_purge_candidatures_et_journal(
    client: AsyncClient,
    admin_headers: dict,
    candidat_headers: dict,
    candidat_profil,
    db_session: AsyncSession,
) -> None:
    examen_id, administration_id = await _creer_examen(client, admin_headers, db_session)
    await client.post(
        "/api/v1/candidat/candidatures",
        json={
            "administration_id": administration_id,
            "examen_id": examen_id,
            "numero_recepisse": "000003",
        },
        headers=candidat_headers,
    )
    await client.get(
        "/api/v1/candidat/me", headers=candidat_headers
    )  # génère une entrée de journal

    profil_id = candidat_profil.id
    response = await client.delete("/api/v1/candidat/me", headers=candidat_headers)
    assert response.status_code == 204

    candidatures = (
        (
            await db_session.execute(
                select(Candidature).where(Candidature.profil_candidat_id == profil_id)
            )
        )
        .scalars()
        .all()
    )
    journal = (
        (
            await db_session.execute(
                select(JournalConsultationProfil).where(
                    JournalConsultationProfil.profil_candidat_id == profil_id
                )
            )
        )
        .scalars()
        .all()
    )
    profil = await db_session.get(ProfilCandidat, profil_id)

    assert candidatures == []
    assert journal == []
    assert profil is None


@pytest.mark.asyncio
async def test_candidat_voit_ses_resultats_a_travers_plusieurs_tenants(
    client: AsyncClient,
    admin_headers: dict,
    autre_administration_headers: dict,
    candidat_headers: dict,
    db_session: AsyncSession,
) -> None:
    """Le dashboard candidat agrège les candidatures de tenants différents, sans que
    ceux-ci n'aient de visibilité les uns sur les autres."""
    examen_a_id, administration_a_id = await _creer_examen(client, admin_headers, db_session)
    examen_b_id, administration_b_id = await _creer_examen(
        client, autre_administration_headers, db_session
    )

    await client.post(
        "/api/v1/candidat/candidatures",
        json={
            "administration_id": administration_a_id,
            "examen_id": examen_a_id,
            "numero_recepisse": "000010",
        },
        headers=candidat_headers,
    )
    await client.post(
        "/api/v1/candidat/candidatures",
        json={
            "administration_id": administration_b_id,
            "examen_id": examen_b_id,
            "numero_recepisse": "000020",
        },
        headers=candidat_headers,
    )

    response = await client.get("/api/v1/candidat/candidatures", headers=candidat_headers)

    assert response.status_code == 200
    administrations_vues = {c["administration_id"] for c in response.json()}
    assert administrations_vues == {administration_a_id, administration_b_id}
