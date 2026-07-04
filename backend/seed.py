"""Peuple la base avec les données minimales pour démarrer en développement.

Idempotent : peut être relancé sans dupliquer l'admin ou les examens d'exemple.
Usage : python seed.py
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.database import AsyncSessionLocal
from app.models import (
    Admin,
    CategorieExamen,
    Examen,
    Ingestion,
    PhasePublication,
    Resultat,
    SourceDonnees,
    StatutIngestion,
    TypeExamen,
    TypeFichier,
)

DEFAULT_ADMIN_EMAIL = "admin@faso-resultats.bf"
DEFAULT_ADMIN_PASSWORD = "ChangeMe123!"


async def seed_admin(db: AsyncSession) -> Admin:
    result = await db.execute(select(Admin).where(Admin.email == DEFAULT_ADMIN_EMAIL))
    admin = result.scalar_one_or_none()
    if admin is not None:
        print(f"Admin {DEFAULT_ADMIN_EMAIL} existe déjà, rien à faire.")
        return admin

    admin = Admin(
        email=DEFAULT_ADMIN_EMAIL,
        mot_de_passe_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
        nom_complet="Administrateur par défaut",
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    print(f"Admin par défaut créé : {DEFAULT_ADMIN_EMAIL} / {DEFAULT_ADMIN_PASSWORD}")
    print("Pensez à changer ce mot de passe avant la mise en production.")
    return admin


async def seed_examens_exemple(db: AsyncSession, admin: Admin) -> None:
    """Un exemple par segment du positionnement concurrentiel (docs/CONTEXTE_METIER.md),
    pour visualiser categorie/source_donnees/phases_publication en conditions réelles."""
    if (await db.execute(select(Examen))).scalars().first() is not None:
        print("Des examens existent déjà, rien à faire pour les exemples.")
        return

    cep = Examen(
        type_examen=TypeExamen.CEP,
        annee=2026,
        libelle="CEP 2026",
        categorie=CategorieExamen.EXAMEN_SCOLAIRE,
        ministere_tutelle="MEBAPLN",
        # Couvert par SIGEC-CEP (resultats.examens.gov.bf) : partenariat potentiel, pas
        # encore conclu — voir docs/CONTEXTE_METIER.md § 1.
        source_donnees=SourceDonnees.SIGEC_API,
        partenariat_officiel=False,
    )
    bepc = Examen(
        type_examen=TypeExamen.BEPC,
        annee=2026,
        libelle="BEPC 2026",
        categorie=CategorieExamen.EXAMEN_SCOLAIRE,
        ministere_tutelle="DGEC",
        source_donnees=SourceDonnees.FILE_IMPORT,
    )
    bac = Examen(
        type_examen=TypeExamen.BAC_GENERAL,
        annee=2026,
        libelle="BAC 2026 - Série D",
        categorie=CategorieExamen.EXAMEN_SCOLAIRE,
        serie="D",
        ministere_tutelle="DGEC",
        source_donnees=SourceDonnees.FILE_IMPORT,
    )
    concours_direct_a = Examen(
        type_examen=TypeExamen.CD_CATEGORIE_A,
        annee=2026,
        libelle="Concours direct catégorie A 2026",
        categorie=CategorieExamen.CONCOURS_DIRECT,
        ministere_tutelle="Ministère de la Fonction Publique, du Travail et de la "
        "Protection sociale",
        source_donnees=SourceDonnees.FILE_IMPORT,
    )
    armee = Examen(
        type_examen=TypeExamen.ARMEE,
        annee=2026,
        libelle="Concours Armée 2026",
        categorie=CategorieExamen.CONCOURS_PARAMILITAIRE,
        ministere_tutelle="Ministère de la Défense",
        # Aucun canal en ligne : communiqués RTB/Sidwaya + affichage physique.
        source_donnees=SourceDonnees.PRESS_MONITORING,
        phases_publication=["EPREUVES_SPORTIVES", "ADMISSIBILITE", "ADMISSION_DEFINITIVE"],
    )
    police = Examen(
        type_examen=TypeExamen.POLICE,
        annee=2026,
        libelle="Concours Police 2026",
        categorie=CategorieExamen.CONCOURS_PARAMILITAIRE,
        ministere_tutelle="Ministère de la Sécurité",
        source_donnees=SourceDonnees.FACEBOOK_SCRAPING,
        phases_publication=["ADMISSIBILITE", "ADMISSION_DEFINITIVE"],
    )
    db.add_all([cep, bepc, bac, concours_direct_a, armee, police])
    await db.flush()

    # Un candidat au concours Armée sur ses 3 phases successives, pour donner un
    # exemple concret du modèle temporel (docs/CONTEXTE_METIER.md § 2.4).
    ingestion_armee = Ingestion(
        examen_id=armee.id,
        admin_id=admin.id,
        nom_fichier="seed-armee.xlsx",
        chemin_fichier="seed://armee",
        type_fichier=TypeFichier.EXCEL,
        statut=StatutIngestion.PUBLIEE,
        nombre_lignes_detectees=3,
        nombre_erreurs=0,
    )
    db.add(ingestion_armee)
    await db.flush()

    candidat = {
        "examen_id": armee.id,
        "ingestion_id": ingestion_armee.id,
        "numero_pv": "000123",
        "jury": "Ouagadougou",
        "nom": "KABORE",
        "prenom": "Issa",
        "donnees_brutes": {"source": "seed"},
    }
    db.add_all(
        [
            Resultat(
                **candidat,
                decision="APTE",
                phase=PhasePublication.EPREUVES_SPORTIVES,
                phase_suivante_attendue=PhasePublication.ADMISSIBILITE,
            ),
            Resultat(
                **candidat,
                decision="ADMISSIBLE",
                phase=PhasePublication.ADMISSIBILITE,
                phase_suivante_attendue=PhasePublication.ADMISSION_DEFINITIVE,
            ),
            Resultat(
                **candidat,
                decision="ADMIS",
                phase=PhasePublication.ADMISSION_DEFINITIVE,
                phase_suivante_attendue=None,
            ),
        ]
    )
    await db.commit()
    print(
        "Examens d'exemple créés : CEP, BEPC, BAC, concours direct catégorie A, "
        "Armée (3 phases), Police."
    )


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        admin = await seed_admin(db)
        await seed_examens_exemple(db, admin)


if __name__ == "__main__":
    asyncio.run(seed())
