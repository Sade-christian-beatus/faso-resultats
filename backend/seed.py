"""Peuple la base avec les données minimales pour démarrer en développement.

Idempotent : peut être relancé sans dupliquer les comptes ou administrations.
Usage : python seed.py

Modèle multi-tenant (docs/PIVOT_SAAS_B2G.md) : un super-admin plateforme, 3
administrations clientes pilotes (OCECOS, Office du BAC, AGRE), un utilisateur
ADMIN_ADMINISTRATION par tenant, un examen par tenant avec quelques résultats
fictifs. Le CEP est hors périmètre (couvert par SIGEC-CEP, voir docs/CONTEXTE_METIER.md).
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
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
                "decision": "ADMISSIBLE",
            },
        ]
    return examen, candidats


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        await seed_super_admin(db)
        await seed_administrations_pilotes(db)


if __name__ == "__main__":
    asyncio.run(seed())
