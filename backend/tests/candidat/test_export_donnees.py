"""Droit à la portabilité (docs/APDP_PROFIL_CANDIDAT.md § 8) :
GET /api/v1/candidat/me/export renvoie l'intégralité des données du profil connecté,
dans un format structuré et exploitable — distinct de GET /me qui n'expose que les
champs utiles au dashboard courant."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidature import Candidature
from app.models.journal_consultation_profil import (
    ActionJournalConsultation,
    JournalConsultationProfil,
)
from app.models.profil_candidat import ProfilCandidat


@pytest.mark.asyncio
async def test_export_renvoie_les_donnees_dechiffrees_du_profil(
    client: AsyncClient, candidat_headers: dict, candidat_profil: ProfilCandidat
) -> None:
    response = await client.get("/api/v1/candidat/me/export", headers=candidat_headers)

    assert response.status_code == 200
    corps = response.json()
    # Contrairement à GET /me, l'export porte l'identité déchiffrée — c'est tout le
    # sens du droit à la portabilité.
    assert corps["numero_cnib"] == "B00000001"
    assert corps["telephone"] == "+22670000001"
    assert corps["date_naissance"] == "2000-01-01"
    assert corps["candidatures"] == []
    assert corps["journal"] == []


@pytest.mark.asyncio
async def test_export_inclut_les_candidatures_du_profil(
    client: AsyncClient,
    candidat_headers: dict,
    candidat_profil: ProfilCandidat,
    db_session: AsyncSession,
) -> None:
    db_session.add(
        Candidature(
            profil_candidat_id=candidat_profil.id,
            administration_id=uuid.uuid4(),
            examen_id=uuid.uuid4(),
            numero_recepisse="000042",
        )
    )
    await db_session.commit()

    response = await client.get("/api/v1/candidat/me/export", headers=candidat_headers)

    assert response.status_code == 200
    candidatures = response.json()["candidatures"]
    assert len(candidatures) == 1
    assert candidatures[0]["numero_recepisse"] == "000042"


@pytest.mark.asyncio
async def test_export_sans_authentification_est_refuse(client: AsyncClient) -> None:
    response = await client.get("/api/v1/candidat/me/export")

    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_export_journalise_l_action(
    client: AsyncClient,
    candidat_headers: dict,
    candidat_profil: ProfilCandidat,
    db_session: AsyncSession,
) -> None:
    await client.get("/api/v1/candidat/me/export", headers=candidat_headers)

    entree = (
        (
            await db_session.execute(
                select(JournalConsultationProfil).where(
                    JournalConsultationProfil.profil_candidat_id == candidat_profil.id,
                    JournalConsultationProfil.action == ActionJournalConsultation.EXPORT_DONNEES,
                )
            )
        )
        .scalars()
        .first()
    )
    assert entree is not None
