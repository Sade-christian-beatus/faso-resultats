"""Tests de MatchingService.traiter_publication_examen — jusqu'ici vérifié seulement à
la main en session (voir points d'attention de l'audit), aucun test automatisé n'existait.

Note de fidélité au comportement réel (voir le rapport du BLOC B) : ce service ne connaît
pas de statut "NON_TROUVE" ni de dépublication d'examen (aucune route admin ne permet de
repasser un examen PUBLISHED en DRAFT) — les tests ci-dessous vérifient le comportement
réel du code, pas un comportement hypothétique non implémenté."""

from datetime import UTC, date, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_deterministe, hash_password
from app.models import (
    Administration,
    Examen,
    Ingestion,
    Resultat,
    RoleUtilisateur,
    StatutExamen,
    StatutIngestion,
    TypeExamen,
    TypeFichier,
    Utilisateur,
)
from app.models.candidature import Candidature, MethodeVerification, StatutVerificationCandidature
from app.models.profil_candidat import ProfilCandidat
from app.services.candidat.matching_service import MatchingService


async def _creer_administration(db_session: AsyncSession, code: str) -> Administration:
    administration = Administration(
        code=code,
        nom_officiel=f"Administration {code}",
        sigle=code.upper(),
        ministere_tutelle="Ministère de test",
        contact_referent_nom="Référent Test",
        contact_referent_email=f"contact@{code}.bf",
        contact_referent_telephone="+22600000000",
    )
    db_session.add(administration)
    await db_session.commit()
    await db_session.refresh(administration)
    return administration


async def _creer_examen(
    db_session: AsyncSession, administration: Administration, *, statut: StatutExamen
) -> Examen:
    examen = Examen(
        administration_id=administration.id,
        type_examen=TypeExamen.CONCOURS_DIRECT,
        annee=2026,
        libelle=f"Concours {administration.code}",
        statut=statut,
    )
    db_session.add(examen)
    await db_session.commit()
    await db_session.refresh(examen)
    return examen


async def _publier_resultat(
    db_session: AsyncSession,
    administration: Administration,
    examen: Examen,
    *,
    numero_recepisse: str,
    numero_cnib: str | None = None,
    date_naissance: date | None = None,
    decision: str = "ADMISSIBLE",
) -> Resultat:
    utilisateur = Utilisateur(
        administration_id=administration.id,
        email=f"admin-{numero_recepisse}@{administration.code}.bf",
        mot_de_passe_hash=hash_password("x"),
        nom_complet="Admin",
        role=RoleUtilisateur.ADMIN_ADMINISTRATION,
    )
    db_session.add(utilisateur)
    await db_session.commit()
    await db_session.refresh(utilisateur)

    ingestion = Ingestion(
        administration_id=administration.id,
        examen_id=examen.id,
        admin_id=utilisateur.id,
        nom_fichier="f.xlsx",
        chemin_fichier="x",
        type_fichier=TypeFichier.EXCEL,
        statut=StatutIngestion.PUBLIEE,
    )
    db_session.add(ingestion)
    await db_session.commit()
    await db_session.refresh(ingestion)

    resultat = Resultat(
        administration_id=administration.id,
        examen_id=examen.id,
        ingestion_id=ingestion.id,
        numero_pv=numero_recepisse,
        numero_recepisse=numero_recepisse,
        jury="03",
        nom="TRAORE",
        prenom="Awa",
        numero_cnib=numero_cnib,
        date_naissance=date_naissance,
        decision=decision,
        donnees_brutes={},
    )
    db_session.add(resultat)
    await db_session.commit()
    await db_session.refresh(resultat)
    return resultat


async def _creer_profil(
    db_session: AsyncSession, *, numero_cnib: str, telephone: str
) -> ProfilCandidat:
    profil = ProfilCandidat(
        numero_cnib=numero_cnib,
        numero_cnib_hash=hash_deterministe(numero_cnib),
        nom_complet="Candidat Test",
        date_naissance=date(2001, 2, 15).isoformat(),
        telephone=telephone,
        telephone_hash=hash_deterministe(telephone),
        telephone_verifie=True,
        consentement_apdp_date=datetime.now(UTC),
        consentement_apdp_version="v1",
    )
    db_session.add(profil)
    await db_session.commit()
    await db_session.refresh(profil)
    return profil


async def _creer_candidature_en_attente(
    db_session: AsyncSession,
    profil: ProfilCandidat,
    administration: Administration,
    examen: Examen,
    numero_recepisse: str,
) -> Candidature:
    candidature = Candidature(
        profil_candidat_id=profil.id,
        administration_id=administration.id,
        examen_id=examen.id,
        numero_recepisse=numero_recepisse,
        statut_verification=StatutVerificationCandidature.EN_ATTENTE,
    )
    db_session.add(candidature)
    await db_session.commit()
    await db_session.refresh(candidature)
    return candidature


@pytest.mark.asyncio
async def test_publication_avec_candidature_correspondante_notifie(
    db_session: AsyncSession,
) -> None:
    administration = await _creer_administration(db_session, "agre")
    examen = await _creer_examen(db_session, administration, statut=StatutExamen.DRAFT)
    profil = await _creer_profil(db_session, numero_cnib="B00000010", telephone="+22670000010")
    candidature = await _creer_candidature_en_attente(
        db_session, profil, administration, examen, "000001"
    )

    examen.statut = StatutExamen.PUBLISHED
    resultat = await _publier_resultat(
        db_session,
        administration,
        examen,
        numero_recepisse="000001",
        numero_cnib="B00000010",
    )

    await MatchingService(db_session).traiter_publication_examen(examen)
    await db_session.commit()
    await db_session.refresh(candidature)

    assert candidature.statut_verification == StatutVerificationCandidature.VERIFIE_AUTO
    assert candidature.methode_verification == MethodeVerification.CNIB_MATCH_AUTO
    assert candidature.dernier_resultat_id == resultat.id
    assert candidature.dernier_resultat_statut == "ADMISSIBLE"
    assert candidature.derniere_notification_envoyee is not None


@pytest.mark.asyncio
async def test_publication_sans_candidature_ne_fait_rien(db_session: AsyncSession) -> None:
    administration = await _creer_administration(db_session, "ocecos")
    examen = await _creer_examen(db_session, administration, statut=StatutExamen.PUBLISHED)

    # Ne doit lever aucune exception même sans aucune candidature liée à cet examen.
    await MatchingService(db_session).traiter_publication_examen(examen)
    await db_session.commit()


@pytest.mark.asyncio
async def test_publication_avec_plusieurs_candidats_notifie_chacun(
    db_session: AsyncSession,
) -> None:
    administration = await _creer_administration(db_session, "bac")
    examen = await _creer_examen(db_session, administration, statut=StatutExamen.DRAFT)

    profil_a = await _creer_profil(db_session, numero_cnib="B00000020", telephone="+22670000020")
    profil_b = await _creer_profil(db_session, numero_cnib="B00000021", telephone="+22670000021")
    candidature_a = await _creer_candidature_en_attente(
        db_session, profil_a, administration, examen, "000010"
    )
    candidature_b = await _creer_candidature_en_attente(
        db_session, profil_b, administration, examen, "000011"
    )

    examen.statut = StatutExamen.PUBLISHED
    resultat_a = await _publier_resultat(
        db_session, administration, examen, numero_recepisse="000010", numero_cnib="B00000020"
    )
    resultat_b = await _publier_resultat(
        db_session, administration, examen, numero_recepisse="000011", numero_cnib="B00000021"
    )

    await MatchingService(db_session).traiter_publication_examen(examen)
    await db_session.commit()
    await db_session.refresh(candidature_a)
    await db_session.refresh(candidature_b)

    assert candidature_a.dernier_resultat_id == resultat_a.id
    assert candidature_a.derniere_notification_envoyee is not None
    assert candidature_b.dernier_resultat_id == resultat_b.id
    assert candidature_b.derniere_notification_envoyee is not None
    assert candidature_a.dernier_resultat_id != candidature_b.dernier_resultat_id


@pytest.mark.asyncio
async def test_publication_avec_recepisse_introuvable_reste_en_attente(
    db_session: AsyncSession,
) -> None:
    """Ce codebase n'a pas de statut "NON_TROUVE" : quand aucun résultat publié ne
    correspond au récépissé de la candidature, celle-ci reste simplement EN_ATTENTE et
    aucune notification n'est envoyée."""
    administration = await _creer_administration(db_session, "agre2")
    examen = await _creer_examen(db_session, administration, statut=StatutExamen.DRAFT)
    profil = await _creer_profil(db_session, numero_cnib="B00000030", telephone="+22670000030")
    candidature = await _creer_candidature_en_attente(
        db_session, profil, administration, examen, "999999"  # ne correspond à aucun résultat
    )

    examen.statut = StatutExamen.PUBLISHED
    await _publier_resultat(
        db_session, administration, examen, numero_recepisse="000001", numero_cnib="B00000099"
    )

    await MatchingService(db_session).traiter_publication_examen(examen)
    await db_session.commit()
    await db_session.refresh(candidature)

    assert candidature.statut_verification == StatutVerificationCandidature.EN_ATTENTE
    assert candidature.derniere_notification_envoyee is None


@pytest.mark.asyncio
async def test_publication_dune_administration_ne_touche_pas_lautre(
    db_session: AsyncSession,
) -> None:
    administration_a = await _creer_administration(db_session, "tenant-a")
    administration_b = await _creer_administration(db_session, "tenant-b")
    examen_a = await _creer_examen(db_session, administration_a, statut=StatutExamen.DRAFT)
    examen_b = await _creer_examen(db_session, administration_b, statut=StatutExamen.PUBLISHED)

    profil = await _creer_profil(db_session, numero_cnib="B00000040", telephone="+22670000040")
    candidature_b = await _creer_candidature_en_attente(
        db_session, profil, administration_b, examen_b, "000001"
    )

    # Publication de l'examen A : ne doit jamais toucher la candidature liée au tenant B.
    examen_a.statut = StatutExamen.PUBLISHED
    await db_session.commit()
    await MatchingService(db_session).traiter_publication_examen(examen_a)
    await db_session.commit()
    await db_session.refresh(candidature_b)

    assert candidature_b.statut_verification == StatutVerificationCandidature.EN_ATTENTE
    assert candidature_b.derniere_notification_envoyee is None
