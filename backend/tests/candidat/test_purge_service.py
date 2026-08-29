"""Purge des données candidat (docs/PROFIL_CANDIDAT_UNIFIE.md § 7,
docs/CIL_PROFIL_CANDIDAT.md § 5) : candidatures orphelines à la résiliation d'une
administration, et comptes inactifs."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.candidature import Candidature, StatutVerificationCandidature
from app.models.profil_candidat import ProfilCandidat
from app.services.candidat.purge_service import (
    marquer_candidatures_administration_resiliee,
    purger_candidatures_administration_resiliee_expirees,
    purger_profils_inactifs,
)

settings = get_settings()


async def _creer_candidature(
    db_session: AsyncSession,
    *,
    profil_id: uuid.UUID,
    administration_id: uuid.UUID,
    statut: StatutVerificationCandidature = StatutVerificationCandidature.VERIFIE_AUTO,
) -> Candidature:
    candidature = Candidature(
        profil_candidat_id=profil_id,
        administration_id=administration_id,
        examen_id=uuid.uuid4(),
        numero_recepisse=f"R{uuid.uuid4().hex[:8]}",
        statut_verification=statut,
        dernier_resultat_id=uuid.uuid4(),
        dernier_resultat_phase="phase1",
        dernier_resultat_statut="ADMIS",
        dernier_resultat_publie_at=datetime.now(UTC),
    )
    db_session.add(candidature)
    await db_session.commit()
    await db_session.refresh(candidature)
    return candidature


@pytest.mark.asyncio
async def test_marquer_candidatures_administration_resiliee(
    db_session: AsyncSession, candidat_profil: ProfilCandidat
) -> None:
    administration_id = uuid.uuid4()
    candidature = await _creer_candidature(
        db_session, profil_id=candidat_profil.id, administration_id=administration_id
    )

    nb = await marquer_candidatures_administration_resiliee(db_session, administration_id)
    await db_session.commit()
    await db_session.refresh(candidature)

    assert nb == 1
    assert candidature.statut_verification == StatutVerificationCandidature.ADMINISTRATION_RESILIEE
    assert candidature.dernier_resultat_id is None
    assert candidature.dernier_resultat_phase is None
    assert candidature.dernier_resultat_statut is None
    assert candidature.dernier_resultat_publie_at is None


@pytest.mark.asyncio
async def test_marquer_candidatures_est_idempotent(
    db_session: AsyncSession, candidat_profil: ProfilCandidat
) -> None:
    """Un second appel (ex. double résiliation accidentelle) ne doit pas re-compter les
    candidatures déjà marquées."""
    administration_id = uuid.uuid4()
    await _creer_candidature(
        db_session, profil_id=candidat_profil.id, administration_id=administration_id
    )

    await marquer_candidatures_administration_resiliee(db_session, administration_id)
    await db_session.commit()

    nb_second_appel = await marquer_candidatures_administration_resiliee(
        db_session, administration_id
    )
    assert nb_second_appel == 0


@pytest.mark.asyncio
async def test_resiliation_administration_declenche_le_marquage(
    client: AsyncClient,
    super_admin_headers: dict,
    admin_headers: dict,
    db_session: AsyncSession,
    candidat_profil: ProfilCandidat,
) -> None:
    """Bout en bout : PATCH .../administrations/{id} avec statut=RESILIE doit marquer
    automatiquement les candidatures de ce tenant."""
    administrations = await client.get("/api/v1/admin/administrations", headers=super_admin_headers)
    administration_id = administrations.json()[0]["id"]

    candidature = await _creer_candidature(
        db_session,
        profil_id=candidat_profil.id,
        administration_id=uuid.UUID(administration_id),
    )

    response = await client.patch(
        f"/api/v1/admin/administrations/{administration_id}",
        json={"statut": "RESILIE"},
        headers=super_admin_headers,
    )
    assert response.status_code == 200

    await db_session.refresh(candidature)
    assert candidature.statut_verification == StatutVerificationCandidature.ADMINISTRATION_RESILIEE


@pytest.mark.asyncio
async def test_purge_candidatures_administration_resiliee_expirees(
    db_session: AsyncSession, candidat_profil: ProfilCandidat
) -> None:
    administration_id = uuid.uuid4()
    ancienne = await _creer_candidature(
        db_session,
        profil_id=candidat_profil.id,
        administration_id=administration_id,
        statut=StatutVerificationCandidature.ADMINISTRATION_RESILIEE,
    )
    recente = await _creer_candidature(
        db_session,
        profil_id=candidat_profil.id,
        administration_id=administration_id,
        statut=StatutVerificationCandidature.ADMINISTRATION_RESILIEE,
    )

    # Simule une candidature marquée ADMINISTRATION_RESILIEE il y a plus longtemps que
    # le délai de rétention — la récente reste à l'intérieur du délai.
    seuil_depasse = datetime.now(UTC) - timedelta(
        days=settings.candidat_purge_candidature_resiliee_jours + 1
    )
    ancienne.updated_at = seuil_depasse
    await db_session.commit()

    nb = await purger_candidatures_administration_resiliee_expirees(db_session)
    await db_session.commit()

    assert nb == 1
    assert await db_session.get(Candidature, ancienne.id) is None
    assert await db_session.get(Candidature, recente.id) is not None


@pytest.mark.asyncio
async def test_purge_ne_supprime_pas_les_candidatures_actives(
    db_session: AsyncSession, candidat_profil: ProfilCandidat
) -> None:
    """Une candidature vérifiée normalement, même ancienne, n'est jamais purgée par ce
    mécanisme — seules celles marquées ADMINISTRATION_RESILIEE le sont."""
    administration_id = uuid.uuid4()
    candidature = await _creer_candidature(
        db_session,
        profil_id=candidat_profil.id,
        administration_id=administration_id,
        statut=StatutVerificationCandidature.VERIFIE_AUTO,
    )
    candidature.updated_at = datetime.now(UTC) - timedelta(days=1000)
    await db_session.commit()

    nb = await purger_candidatures_administration_resiliee_expirees(db_session)
    await db_session.commit()

    assert nb == 0
    assert await db_session.get(Candidature, candidature.id) is not None


@pytest.mark.asyncio
async def test_purge_profils_inactifs(db_session: AsyncSession) -> None:
    from tests.conftest import _creer_profil_candidat

    inactif = await _creer_profil_candidat(
        db_session, numero_cnib="B00000090", telephone="+22670000090"
    )
    inactif.derniere_connexion = datetime.now(UTC) - timedelta(
        days=settings.candidat_purge_inactivite_jours + 1
    )
    actif = await _creer_profil_candidat(
        db_session, numero_cnib="B00000091", telephone="+22670000091"
    )
    actif.derniere_connexion = datetime.now(UTC) - timedelta(days=1)
    await db_session.commit()

    candidature_orpheline = await _creer_candidature(
        db_session, profil_id=inactif.id, administration_id=uuid.uuid4()
    )

    nb = await purger_profils_inactifs(db_session)
    await db_session.commit()

    assert nb == 1
    assert await db_session.get(ProfilCandidat, inactif.id) is None
    assert await db_session.get(ProfilCandidat, actif.id) is not None
    # La cascade ORM doit aussi purger la candidature liée au profil supprimé.
    assert await db_session.get(Candidature, candidature_orpheline.id) is None


@pytest.mark.asyncio
async def test_purge_profils_jamais_connectes_mais_inscrits_depuis_longtemps(
    db_session: AsyncSession,
) -> None:
    """Un profil qui ne s'est jamais reconnecté (derniere_connexion NULL) doit quand
    même être purgé si son inscription est ancienne."""
    from tests.conftest import _creer_profil_candidat

    profil = await _creer_profil_candidat(
        db_session, numero_cnib="B00000092", telephone="+22670000092"
    )
    assert profil.derniere_connexion is None
    profil.created_at = datetime.now(UTC) - timedelta(
        days=settings.candidat_purge_inactivite_jours + 1
    )
    await db_session.commit()

    nb = await purger_profils_inactifs(db_session)
    await db_session.commit()

    assert nb == 1
    assert await db_session.get(ProfilCandidat, profil.id) is None
