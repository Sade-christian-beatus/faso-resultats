"""Durcissement sécurité candidat (docs/PROFIL_CANDIDAT_UNIFIE.md § 8) : détection
d'abus par taux de rejet et alerte de création de compte."""

from unittest.mock import patch

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
from app.models.profil_candidat import ProfilCandidat, StatutProfilCandidat


async def _creer_examen(client: AsyncClient, admin_headers: dict, db_session: AsyncSession):
    response = await client.post(
        "/api/v1/admin/exams",
        json={"type_examen": "BAC", "annee": 2026, "libelle": "BAC 2026"},
        headers=admin_headers,
    )
    examen_id = response.json()["id"]
    examen = await db_session.get(Examen, examen_id)
    return examen_id, str(examen.administration_id)


@pytest.mark.asyncio
async def test_suspension_apres_taux_de_rejet_eleve(
    client: AsyncClient,
    admin_headers: dict,
    candidat_headers: dict,
    candidat_profil: ProfilCandidat,
    db_session: AsyncSession,
) -> None:
    """Publie un résultat avec un CNIB qui ne correspond jamais au profil : chaque
    tentative est rejetée. Au-delà du seuil, le profil doit être suspendu."""
    examen_id, administration_id = await _creer_examen(client, admin_headers, db_session)

    for i in range(5):
        # Publie un résultat avec un CNIB étranger, pour forcer un rejet à chaque fois.
        examen = await db_session.get(Examen, examen_id)
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
                numero_pv=f"00{i}",
                jury="03",
                nom="AUTRE",
                prenom="Personne",
                numero_cnib="B99999999",  # jamais celui du candidat_profil
                decision="ADMIS",
                donnees_brutes={},
            )
        )
        await db_session.commit()

        response = await client.post(
            "/api/v1/candidat/candidatures",
            json={
                "administration_id": administration_id,
                "examen_id": examen_id,
                "numero_recepisse": f"00{i}",
            },
            headers=candidat_headers,
        )
        assert response.status_code in (422, 429)

    await db_session.refresh(candidat_profil)
    assert candidat_profil.statut == StatutProfilCandidat.SUSPENDU

    # Le profil suspendu ne peut plus s'authentifier (get_current_profil_candidat
    # exige ACTIF).
    response = await client.get("/api/v1/candidat/me", headers=candidat_headers)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_alerte_envoyee_a_la_creation_de_compte(client: AsyncClient) -> None:
    payload = {
        "numero_cnib": "B55555555",
        "nom_complet": "ALERTE Test",
        "date_naissance": "2000-01-01",
        "telephone": "+22670055555",
        "consentement_apdp": True,
        "consentement_apdp_version": "v1",
    }

    with patch(
        "app.services.candidat.notification_engine.NotificationEngine.envoyer_sms"
    ) as mock_envoyer_sms:
        mock_envoyer_sms.return_value = True
        inscription = await client.post("/api/v1/candidat/inscription", json=payload)
        code = inscription.json()["code_otp_debug"]

        await client.post(
            "/api/v1/candidat/otp/verify",
            json={"telephone": payload["telephone"], "code": code},
        )

    mock_envoyer_sms.assert_called_once()
    telephone_appele, message_appele = mock_envoyer_sms.call_args[0]
    assert telephone_appele == payload["telephone"]
    assert "compte" in message_appele.lower()
