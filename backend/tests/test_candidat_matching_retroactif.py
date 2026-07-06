"""Scénario B (docs/PROFIL_CANDIDAT_UNIFIE.md § 4.5) : un candidat qui s'inscrit après
la publication de son résultat le voit apparaître automatiquement dans son dashboard,
sans avoir à saisir son récépissé — le point différenciant du produit."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Examen,
    Ingestion,
    Resultat,
    StatutExamen,
    StatutIngestion,
    TypeFichier,
    Utilisateur,
)

_INSCRIPTION_PAYLOAD = {
    "numero_cnib": "B14863543",
    "nom_complet": "TRAORE Awa",
    "date_naissance": "2001-02-15",
    "telephone": "+22670000020",
    "consentement_apdp": True,
    "consentement_apdp_version": "v1",
}


@pytest.mark.asyncio
async def test_inscription_apres_publication_decouvre_automatiquement_le_resultat(
    client: AsyncClient, admin_headers: dict, db_session: AsyncSession
) -> None:
    examen_response = await client.post(
        "/api/v1/admin/exams",
        json={"type_examen": "CONCOURS_DIRECT", "annee": 2026, "libelle": "Concours"},
        headers=admin_headers,
    )
    examen_id = examen_response.json()["id"]
    examen = await db_session.get(Examen, examen_id)
    administration_id = examen.administration_id
    examen.statut = StatutExamen.PUBLISHED

    utilisateur = (
        (
            await db_session.execute(
                select(Utilisateur).where(Utilisateur.administration_id == administration_id)
            )
        )
        .scalars()
        .first()
    )

    ingestion = Ingestion(
        administration_id=administration_id,
        examen_id=examen_id,
        admin_id=utilisateur.id,
        nom_fichier="f.xlsx",
        chemin_fichier="x",
        type_fichier=TypeFichier.EXCEL,
        statut=StatutIngestion.PUBLIEE,
    )
    db_session.add(ingestion)
    await db_session.commit()
    await db_session.refresh(ingestion)

    db_session.add(
        Resultat(
            administration_id=administration_id,
            examen_id=examen_id,
            ingestion_id=ingestion.id,
            numero_pv="000099",
            numero_recepisse="000099",
            jury="03",
            nom="TRAORE",
            prenom="Awa",
            numero_cnib=_INSCRIPTION_PAYLOAD["numero_cnib"],
            decision="ADMISSIBLE",
            donnees_brutes={},
        )
    )
    await db_session.commit()

    # Le candidat ne connaît pas encore ce résultat : il s'inscrit simplement.
    inscription = await client.post("/api/v1/candidat/inscription", json=_INSCRIPTION_PAYLOAD)
    code = inscription.json()["code_otp_debug"]
    verif = await client.post(
        "/api/v1/candidat/otp/verify",
        json={"telephone": _INSCRIPTION_PAYLOAD["telephone"], "code": code},
    )
    headers = {"Authorization": f"Bearer {verif.json()['access_token']}"}

    response = await client.get("/api/v1/candidat/candidatures", headers=headers)

    assert response.status_code == 200
    candidatures = response.json()
    assert len(candidatures) == 1
    assert candidatures[0]["numero_recepisse"] == "000099"
    assert candidatures[0]["statut_verification"] == "VERIFIE_AUTO"
    assert candidatures[0]["methode_verification"] == "CNIB_MATCH_AUTO"
