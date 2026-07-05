"""Peuple la base avec les données minimales pour démarrer en développement.

Idempotent : peut être relancé sans dupliquer les comptes ou administrations.
Usage : python seed.py

Modèle multi-tenant (docs/PIVOT_SAAS_B2G.md) : un super-admin plateforme, 3
administrations clientes pilotes (OCECOS, Office du BAC, AGRE), un utilisateur
ADMIN_ADMINISTRATION par tenant, un examen par tenant avec quelques résultats
fictifs. Le CEP est hors périmètre (couvert par SIGEC-CEP, voir docs/CONTEXTE_METIER.md).
"""

import asyncio
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_deterministe, hash_password
from app.database import AsyncSessionLocal
from app.models import (
    Administration,
    CategorieExamen,
    Examen,
    Ingestion,
    Resultat,
    RoleUtilisateur,
    SourceDonnees,
    StatutExamen,
    StatutIngestion,
    TypeExamen,
    TypeFichier,
    Utilisateur,
)
from app.models.candidature import Candidature, MethodeVerification, StatutVerificationCandidature
from app.models.profil_candidat import ProfilCandidat
from app.services.candidat.matching_service import MatchingService

DEFAULT_PASSWORD = "ChangeMe123!"
SUPER_ADMIN_EMAIL = "superadmin@faso-resultats.bf"

# code, nom_officiel, sigle, ministere_tutelle, email admin tenant
_ADMINISTRATIONS = [
    (
        "ocecos",
        "Office Central des Examens et Concours du Secondaire",
        "OCECOS",
        "Ministère de l'Éducation nationale",
        "admin@ocecos.bf",
    ),
    (
        "office-bac",
        "Office du Baccalauréat",
        "Office du BAC",
        "Ministère de l'Éducation nationale",
        "admin@office-bac.bf",
    ),
    (
        "agre",
        "Agence Générale de Recrutement de l'État",
        "AGRE",
        "Ministère de la Fonction Publique, du Travail et de la Protection sociale",
        "admin@agre.bf",
    ),
]


async def seed_super_admin(db: AsyncSession) -> None:
    result = await db.execute(select(Utilisateur).where(Utilisateur.email == SUPER_ADMIN_EMAIL))
    if result.scalar_one_or_none() is not None:
        print(f"Super-admin {SUPER_ADMIN_EMAIL} existe déjà, rien à faire.")
        return

    db.add(
        Utilisateur(
            administration_id=None,
            email=SUPER_ADMIN_EMAIL,
            mot_de_passe_hash=hash_password(DEFAULT_PASSWORD),
            nom_complet="Super-administrateur Faso Résultats",
            role=RoleUtilisateur.SUPER_ADMIN,
        )
    )
    await db.commit()
    print(f"Super-admin créé : {SUPER_ADMIN_EMAIL} / {DEFAULT_PASSWORD}")


async def seed_administrations_pilotes(db: AsyncSession) -> None:
    codes_pilotes = [code for code, *_ in _ADMINISTRATIONS]
    result = await db.execute(select(Administration).where(Administration.code.in_(codes_pilotes)))
    if result.scalars().first() is not None:
        print("Les administrations pilotes existent déjà, rien à faire.")
        return

    for code, nom_officiel, sigle, ministere_tutelle, email_admin in _ADMINISTRATIONS:
        administration = Administration(
            code=code,
            nom_officiel=nom_officiel,
            sigle=sigle,
            ministere_tutelle=ministere_tutelle,
            contact_referent_nom="À désigner",
            contact_referent_email=email_admin,
            contact_referent_telephone="+22600000000",
            convention_active=False,
        )
        db.add(administration)
        await db.flush()

        utilisateur = Utilisateur(
            administration_id=administration.id,
            email=email_admin,
            mot_de_passe_hash=hash_password(DEFAULT_PASSWORD),
            nom_complet=f"Administrateur {sigle}",
            role=RoleUtilisateur.ADMIN_ADMINISTRATION,
        )
        db.add(utilisateur)
        await db.flush()

        examen, candidats = _construire_examen_exemple(administration, sigle)
        db.add(examen)
        await db.flush()

        ingestion = Ingestion(
            administration_id=administration.id,
            examen_id=examen.id,
            admin_id=utilisateur.id,
            nom_fichier=f"seed-{code}.xlsx",
            chemin_fichier=f"seed://{code}",
            type_fichier=TypeFichier.EXCEL,
            statut=StatutIngestion.PUBLIEE,
            nombre_lignes_detectees=len(candidats),
            nombre_erreurs=0,
        )
        db.add(ingestion)
        await db.flush()

        for candidat in candidats:
            db.add(
                Resultat(
                    administration_id=administration.id,
                    examen_id=examen.id,
                    ingestion_id=ingestion.id,
                    donnees_brutes={"source": "seed"},
                    **candidat,
                )
            )

        print(f"Tenant pilote créé : {sigle} ({email_admin} / {DEFAULT_PASSWORD})")

    await db.commit()


def _construire_examen_exemple(
    administration: Administration, sigle: str
) -> tuple[Examen, list[dict]]:
    if sigle == "OCECOS":
        examen = Examen(
            administration_id=administration.id,
            type_examen=TypeExamen.BEPC,
            annee=2026,
            libelle="BEPC 2026",
            categorie=CategorieExamen.EXAMEN_SCOLAIRE,
            ministere_tutelle=administration.ministere_tutelle,
            source_donnees=SourceDonnees.FILE_IMPORT,
            statut=StatutExamen.PUBLISHED,
        )
        candidats = [
            {
                "numero_pv": "000101",
                "jury": "Ouagadougou 1",
                "nom": "TRAORE",
                "prenom": "Awa",
                "decision": "ADMIS",
                "moyenne": 13.45,
            },
            {
                "numero_pv": "000102",
                "jury": "Bobo-Dioulasso",
                "nom": "KABORE",
                "prenom": "Issa",
                "decision": "AJOURNE",
            },
        ]
    elif sigle == "Office du BAC":
        examen = Examen(
            administration_id=administration.id,
            type_examen=TypeExamen.BAC_GENERAL,
            annee=2026,
            libelle="BAC 2026 - Série D",
            categorie=CategorieExamen.EXAMEN_SCOLAIRE,
            serie="D",
            ministere_tutelle=administration.ministere_tutelle,
            source_donnees=SourceDonnees.FILE_IMPORT,
            statut=StatutExamen.PUBLISHED,
        )
        candidats = [
            {
                "numero_pv": "000201",
                "jury": "Ouagadougou 1",
                "nom": "SANOU",
                "prenom": "Richard",
                "decision": "ADMIS",
                "moyenne": 12.8,
            },
            {
                "numero_pv": "000202",
                "jury": "Koudougou",
                "nom": "OUEDRAOGO",
                "prenom": "Fatou",
                "decision": "AJOURNE",
            },
        ]
    else:  # AGRE — format concours direct Fonction publique (numero_recepisse/rang)
        examen = Examen(
            administration_id=administration.id,
            type_examen=TypeExamen.CD_CATEGORIE_A,
            annee=2026,
            libelle="Concours direct catégorie A 2026",
            categorie=CategorieExamen.CONCOURS_DIRECT,
            ministere_tutelle=administration.ministere_tutelle,
            source_donnees=SourceDonnees.FILE_IMPORT,
            statut=StatutExamen.PUBLISHED,
        )
        candidats = [
            {
                "numero_pv": "000015",
                "numero_recepisse": "000015",
                "code_concours": "120",
                "code_centre": "03",
                "rang_numerique": 1,
                "rang_affiche": "1°",
                "jury": "03",
                "nom": "BAYALA",
                "prenom": "Jean-Claude",
                "decision": "ADMISSIBLE",
            },
            {
                "numero_pv": "000042",
                "numero_recepisse": "000042",
                "code_concours": "120",
                "code_centre": "03",
                "rang_numerique": 2,
                "rang_affiche": "2°",
                "jury": "03",
                "nom": "TRAORE",
                "prenom": "Awa",
                "numero_cnib": "B00000001",  # démonstration du matching rétroactif par CNIB
                "decision": "ADMISSIBLE",
            },
        ]
    return examen, candidats


_PROFILS_CANDIDATS_DEMO = [
    ("B00000001", "TRAORE Awa", "2001-02-15", "+22670000001"),
    ("B00000002", "KABORE Issa", "2002-06-20", "+22670000002"),
    ("B00000003", "SANOU Richard", "2000-11-03", "+22670000003"),
]


async def seed_profils_candidats(db: AsyncSession) -> None:
    """3 profils candidat fictifs (docs/PROFIL_CANDIDAT_UNIFIE.md) : un utilise le
    matching rétroactif réel par CNIB (démonstration du scénario B, § 4.5), les autres
    illustrent des candidatures ajoutées manuellement à d'autres stades de vérification."""
    cnibs = [cnib for cnib, *_ in _PROFILS_CANDIDATS_DEMO]
    result = await db.execute(
        select(ProfilCandidat).where(
            ProfilCandidat.numero_cnib_hash.in_(hash_deterministe(c) for c in cnibs)
        )
    )
    if result.scalars().first() is not None:
        print("Les profils candidats de démonstration existent déjà, rien à faire.")
        return

    profils = {}
    for numero_cnib, nom_complet, date_naissance, telephone in _PROFILS_CANDIDATS_DEMO:
        profil = ProfilCandidat(
            numero_cnib=numero_cnib,
            numero_cnib_hash=hash_deterministe(numero_cnib),
            nom_complet=nom_complet,
            date_naissance=date_naissance,
            telephone=telephone,
            telephone_hash=hash_deterministe(telephone),
            telephone_verifie=True,
            consentement_apdp_date=datetime.now(UTC),
            consentement_apdp_version="v1",
        )
        db.add(profil)
        profils[nom_complet] = profil
    await db.flush()

    # Démonstration réelle du scénario B (§ 4.5) : TRAORE Awa a un CNIB qui matche le
    # résultat AGRE déjà publié (numero_recepisse 000042) — la candidature apparaît
    # automatiquement, sans action du candidat.
    await MatchingService(db).matcher_retroactif(profils["TRAORE Awa"])

    async def _get(code: str, numero: str) -> tuple[Administration, Examen, Resultat]:
        administration = (
            await db.execute(select(Administration).where(Administration.code == code))
        ).scalar_one()
        resultat = (
            await db.execute(
                select(Resultat).where(
                    Resultat.administration_id == administration.id,
                    Resultat.numero_pv == numero,
                )
            )
        ).scalar_one()
        examen = await db.get(Examen, resultat.examen_id)
        return administration, examen, resultat

    # Candidatures illustratives ajoutées manuellement, à différents stades (les
    # examens scolaires du seed ne portent pas de CNIB/date de naissance exploitables
    # automatiquement — cf. docs/PROFIL_CANDIDAT_UNIFIE.md § 5, cas des administrations
    # qui ne publient pas ces données).
    administration_ocecos, _, resultat_kabore = await _get("ocecos", "000102")
    db.add(
        Candidature(
            profil_candidat_id=profils["KABORE Issa"].id,
            administration_id=administration_ocecos.id,
            examen_id=resultat_kabore.examen_id,
            numero_recepisse=resultat_kabore.numero_pv,
            statut_verification=StatutVerificationCandidature.VERIFIE_MANUEL,
            methode_verification=MethodeVerification.VALIDATION_MANUELLE,
            date_verification=datetime.now(UTC),
            dernier_resultat_id=resultat_kabore.id,
            dernier_resultat_statut=resultat_kabore.decision,
            dernier_resultat_phase=resultat_kabore.phase.value,
        )
    )

    administration_bac, _, resultat_sanou = await _get("office-bac", "000201")
    db.add(
        Candidature(
            profil_candidat_id=profils["SANOU Richard"].id,
            administration_id=administration_bac.id,
            examen_id=resultat_sanou.examen_id,
            numero_recepisse=resultat_sanou.numero_pv,
            statut_verification=StatutVerificationCandidature.VERIFIE_AUTO,
            methode_verification=MethodeVerification.DATE_NAISSANCE,
            date_verification=datetime.now(UTC),
            dernier_resultat_id=resultat_sanou.id,
            dernier_resultat_statut=resultat_sanou.decision,
            dernier_resultat_phase=resultat_sanou.phase.value,
        )
    )

    _, examen_bac, _ = await _get("office-bac", "000201")
    db.add(
        Candidature(
            profil_candidat_id=profils["SANOU Richard"].id,
            administration_id=administration_bac.id,
            examen_id=examen_bac.id,
            numero_recepisse="000999",  # candidature à un futur résultat, pas encore publié
            statut_verification=StatutVerificationCandidature.EN_ATTENTE,
        )
    )

    await db.commit()
    print("3 profils candidat de démonstration créés (dont 1 auto-découvert par CNIB).")


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        await seed_super_admin(db)
        await seed_administrations_pilotes(db)
        await seed_profils_candidats(db)


if __name__ == "__main__":
    asyncio.run(seed())
