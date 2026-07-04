import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Admin,
    Examen,
    Ingestion,
    PhasePublication,
    Resultat,
    StatutExamen,
    TypeExamen,
    TypeFichier,
)


@pytest.mark.asyncio
async def test_examen_default_statut_is_draft(db_session: AsyncSession) -> None:
    examen = Examen(type_examen=TypeExamen.BAC, annee=2026, libelle="BAC 2026 - Session normale")
    db_session.add(examen)
    await db_session.commit()

    assert examen.statut == StatutExamen.DRAFT


@pytest.mark.asyncio
async def test_resultat_requires_examen_id(db_session: AsyncSession) -> None:
    admin = Admin(email="admin@faso-resultats.bf", mot_de_passe_hash="hash", nom_complet="Admin")
    examen = Examen(type_examen=TypeExamen.BAC, annee=2026, libelle="BAC 2026")
    db_session.add_all([admin, examen])
    await db_session.commit()

    ingestion = Ingestion(
        examen_id=examen.id,
        admin_id=admin.id,
        nom_fichier="resultats.pdf",
        chemin_fichier="/app/uploads/resultats.pdf",
        type_fichier=TypeFichier.PDF,
    )
    db_session.add(ingestion)
    await db_session.commit()

    resultat_sans_examen = Resultat(
        examen_id=None,
        ingestion_id=ingestion.id,
        numero_pv="12345",
        jury="Ouagadougou 1",
        nom="Traore",
        prenom="Awa",
        decision="ADMIS",
        donnees_brutes={"numero_pv": "12345"},
    )
    db_session.add(resultat_sans_examen)

    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_resultat_traceable_to_source_ingestion(db_session: AsyncSession) -> None:
    admin = Admin(email="admin@faso-resultats.bf", mot_de_passe_hash="hash", nom_complet="Admin")
    examen = Examen(type_examen=TypeExamen.CEP, annee=2026, libelle="CEP 2026")
    db_session.add_all([admin, examen])
    await db_session.commit()

    ingestion = Ingestion(
        examen_id=examen.id,
        admin_id=admin.id,
        nom_fichier="cep_2026.xlsx",
        chemin_fichier="/app/uploads/cep_2026.xlsx",
        type_fichier=TypeFichier.EXCEL,
    )
    db_session.add(ingestion)
    await db_session.commit()

    resultat = Resultat(
        examen_id=examen.id,
        ingestion_id=ingestion.id,
        numero_pv="00042",
        jury="Bobo-Dioulasso",
        nom="Kabore",
        prenom="Issa",
        decision="ADMIS",
        donnees_brutes={"numero_pv": "00042", "nom": "Kabore"},
    )
    db_session.add(resultat)
    await db_session.commit()
    await db_session.refresh(resultat, attribute_names=["ingestion"])

    assert resultat.ingestion.nom_fichier == "cep_2026.xlsx"
    assert isinstance(resultat.id, uuid.UUID)


@pytest.mark.asyncio
async def test_resultat_defaut_phase_resultat_unique(db_session: AsyncSession) -> None:
    admin = Admin(email="admin@faso-resultats.bf", mot_de_passe_hash="hash", nom_complet="Admin")
    examen = Examen(type_examen=TypeExamen.BAC, annee=2026, libelle="BAC 2026")
    db_session.add_all([admin, examen])
    await db_session.commit()

    ingestion = Ingestion(
        examen_id=examen.id,
        admin_id=admin.id,
        nom_fichier="bac_2026.xlsx",
        chemin_fichier="/app/uploads/bac_2026.xlsx",
        type_fichier=TypeFichier.EXCEL,
    )
    db_session.add(ingestion)
    await db_session.commit()

    resultat = Resultat(
        examen_id=examen.id,
        ingestion_id=ingestion.id,
        numero_pv="00099",
        jury="Ouagadougou 1",
        nom="Sanou",
        prenom="Richard",
        decision="ADMIS",
        donnees_brutes={},
    )
    db_session.add(resultat)
    await db_session.commit()

    assert resultat.phase == PhasePublication.RESULTAT_UNIQUE
    assert resultat.phase_suivante_attendue is None


@pytest.mark.asyncio
async def test_resultat_plusieurs_phases_pour_le_meme_candidat(db_session: AsyncSession) -> None:
    """Modèle temporel des concours paramilitaires (docs/CONTEXTE_METIER.md § 2.4) :
    un même candidat peut avoir plusieurs Resultat pour le même examen, un par phase."""
    admin = Admin(email="admin@faso-resultats.bf", mot_de_passe_hash="hash", nom_complet="Admin")
    examen = Examen(
        type_examen=TypeExamen.ARMEE,
        annee=2026,
        libelle="Concours Armée 2026",
        phases_publication=["EPREUVES_SPORTIVES", "ADMISSIBILITE", "ADMISSION_DEFINITIVE"],
    )
    db_session.add_all([admin, examen])
    await db_session.commit()

    ingestion = Ingestion(
        examen_id=examen.id,
        admin_id=admin.id,
        nom_fichier="armee_2026.xlsx",
        chemin_fichier="/app/uploads/armee_2026.xlsx",
        type_fichier=TypeFichier.EXCEL,
    )
    db_session.add(ingestion)
    await db_session.commit()

    candidat = {
        "examen_id": examen.id,
        "ingestion_id": ingestion.id,
        "numero_pv": "000123",
        "jury": "Ouagadougou",
        "nom": "Kabore",
        "prenom": "Issa",
        "donnees_brutes": {},
    }
    db_session.add_all(
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
        ]
    )
    await db_session.commit()

    resultats = (
        (await db_session.execute(select(Resultat).where(Resultat.examen_id == examen.id)))
        .scalars()
        .all()
    )
    assert {r.phase for r in resultats} == {
        PhasePublication.EPREUVES_SPORTIVES,
        PhasePublication.ADMISSIBILITE,
    }
    assert {r.decision for r in resultats} == {"APTE", "ADMISSIBLE"}
