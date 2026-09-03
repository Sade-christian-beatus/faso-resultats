"""Purge des données candidat (docs/PROFIL_CANDIDAT_UNIFIE.md § 7,
docs/CIL_PROFIL_CANDIDAT.md § 5) : candidatures orphelines à la résiliation d'une
administration, et comptes inactifs.

Pas de file de tâches en Phase 1 (RQ prévu en Phase 2, voir CLAUDE.md) : ces
fonctions sont appelées soit ponctuellement (marquage à la résiliation, depuis la
route super-admin), soit depuis le script `purge_candidats.py` à planifier via cron
côté infrastructure — voir ce script pour l'usage."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.candidature import Candidature, StatutVerificationCandidature
from app.models.profil_candidat import ProfilCandidat

settings = get_settings()


async def marquer_candidatures_administration_resiliee(
    db: AsyncSession, administration_id: UUID
) -> int:
    """Au moment où une administration passe au statut RESILIE : ses candidatures
    deviennent orphelines. Marquées `ADMINISTRATION_RESILIEE` et le cache dénormalisé
    du dernier résultat est purgé, puisqu'il ne sera plus jamais rafraîchi."""
    result = await db.execute(
        select(Candidature).where(
            Candidature.administration_id == administration_id,
            Candidature.statut_verification
            != StatutVerificationCandidature.ADMINISTRATION_RESILIEE,
        )
    )
    candidatures = list(result.scalars().all())
    for candidature in candidatures:
        candidature.statut_verification = StatutVerificationCandidature.ADMINISTRATION_RESILIEE
        candidature.dernier_resultat_id = None
        candidature.dernier_resultat_phase = None
        candidature.dernier_resultat_statut = None
        candidature.dernier_resultat_publie_at = None
    return len(candidatures)


async def purger_candidatures_administration_resiliee_expirees(db: AsyncSession) -> int:
    """Supprime les candidatures marquées `ADMINISTRATION_RESILIEE` depuis plus de
    `candidat_purge_candidature_resiliee_jours` (6 mois par défaut, § 7)."""
    seuil = datetime.now(UTC) - timedelta(days=settings.candidat_purge_candidature_resiliee_jours)
    result = await db.execute(
        delete(Candidature).where(
            Candidature.statut_verification
            == StatutVerificationCandidature.ADMINISTRATION_RESILIEE,
            Candidature.updated_at < seuil,
        )
        # "fetch" (SELECT préalable puis retrait de l'identity map) plutôt que le mode
        # "evaluate" par défaut, qui échoue en comparant des datetimes naive/aware sur
        # SQLite (tests) — voir sqlalchemy.orm.evaluator.
        .execution_options(synchronize_session="fetch")
    )
    return result.rowcount or 0


async def purger_profils_inactifs(db: AsyncSession) -> int:
    """Supprime les profils candidats sans activité depuis `candidat_purge_inactivite_jours`
    (durée provisoire, non validée par la CIL — voir docs/CIL_PROFIL_CANDIDAT.md § 5).
    L'inactivité se mesure depuis la dernière connexion, ou depuis l'inscription si le
    profil ne s'est jamais reconnecté. Passe par l'ORM (pas un DELETE en masse) pour
    déclencher les cascades `all, delete-orphan` vers les candidatures et le journal."""
    seuil = datetime.now(UTC) - timedelta(days=settings.candidat_purge_inactivite_jours)
    result = await db.execute(
        select(ProfilCandidat).where(
            ((ProfilCandidat.derniere_connexion.is_(None)) & (ProfilCandidat.created_at < seuil))
            | (ProfilCandidat.derniere_connexion < seuil)
        )
    )
    profils = list(result.scalars().all())
    for profil in profils:
        await db.delete(profil)
    return len(profils)
