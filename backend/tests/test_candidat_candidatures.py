import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Examen, Ingestion, Resultat, StatutExamen, StatutIngestion, TypeFichier
from app.models.profil_candidat import ProfilCandidat


async def _publier_resultat(
    db_session: AsyncSession,
    *,
    administration_id,
    examen_id,
    admin_id,
    numero_recepisse: str,
    numero_cnib: str | None = None,
    date_naissance=None,
) -> None:
    examen = await db_session.get(Examen, examen_id)
    examen.statut = StatutExamen.PUBLISHED

    ingestion = Ingestion(
        administration_id=administration_id,
        examen_id=examen_id,
        admin_id=admin_id,
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
            numero_pv=numero_recepisse,
            numero_recepisse=numero_recepisse,
            jury="03",
            nom="TRAORE",
            prenom="Awa",
            numero_cnib=numero_cnib,
            date_naissance=date_naissance,
            decision="ADMISSIBLE",
            donnees_brutes={},
        )
    )
    await db_session.commit()


async def _creer_examen(
    client: AsyncClient, admin_headers: dict, db_session: AsyncSession
) -> tuple[str, str]:
    response = await client.post(
        "/api/v1/admin/exams",
        json={"type_examen": "CONCOURS_DIRECT", "annee": 2026, "libelle": "Concours"},
        headers=admin_headers,
    )
    examen_id = response.json()["id"]
    examen = await db_session.get(Examen, examen_id)
    return examen_id, str(examen.administration_id)


async def _utilisateur_id(db_session: AsyncSession, administration_id: str):
    from app.models import Utilisateur

    result = await db_session.execute(
        select(Utilisateur).where(Utilisateur.administration_id == administration_id)
    )
    return result.scalars().first().id


@pytest.mark.asyncio
async def test_ajout_candidature_verifiee_par_cnib(
    client: AsyncClient,
    admin_headers: dict,
    candidat_headers: dict,
    candidat_profil: ProfilCandidat,
    db_session: AsyncSession,
) -> None:
    examen_id, administration_id = await _creer_examen(client, admin_headers, db_session)
    admin_id = await _utilisateur_id(db_session, administration_id)
    await _publier_resultat(
        db_session,
        administration_id=administration_id,
        examen_id=examen_id,
        admin_id=admin_id,
        numero_recepisse="000001",
        numero_cnib=candidat_profil.numero_cnib,  # déchiffré à l'accès (EncryptedStr)
    )

    response = await client.post(
        "/api/v1/candidat/candidatures",
        json={
            "administration_id": administration_id,
            "examen_id": examen_id,
            "numero_recepisse": "000001",
        },
        headers=candidat_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["statut_verification"] == "VERIFIE_AUTO"
    assert body["methode_verification"] == "CNIB_MATCH_AUTO"


@pytest.mark.asyncio
async def test_ajout_candidature_verifiee_par_date_naissance(
    client: AsyncClient,
    admin_headers: dict,
    candidat_headers: dict,
    candidat_profil: ProfilCandidat,
    db_session: AsyncSession,
) -> None:
    import datetime as dt

    examen_id, administration_id = await _creer_examen(client, admin_headers, db_session)
    admin_id = await _utilisateur_id(db_session, administration_id)
    await _publier_resultat(
        db_session,
        administration_id=administration_id,
        examen_id=examen_id,
        admin_id=admin_id,
        numero_recepisse="000002",
        date_naissance=dt.date.fromisoformat(candidat_profil.date_naissance),
    )

    response = await client.post(
        "/api/v1/candidat/candidatures",
        json={
            "administration_id": administration_id,
            "examen_id": examen_id,
            "numero_recepisse": "000002",
        },
        headers=candidat_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["statut_verification"] == "VERIFIE_AUTO"
    assert body["methode_verification"] == "DATE_NAISSANCE"


@pytest.mark.asyncio
async def test_ajout_candidature_rejetee_si_cnib_different(
    client: AsyncClient,
    admin_headers: dict,
    candidat_headers: dict,
    db_session: AsyncSession,
) -> None:
    examen_id, administration_id = await _creer_examen(client, admin_headers, db_session)
    admin_id = await _utilisateur_id(db_session, administration_id)
    await _publier_resultat(
        db_session,
        administration_id=administration_id,
        examen_id=examen_id,
        admin_id=admin_id,
        numero_recepisse="000003",
        numero_cnib="B99999999",  # ne correspond pas au CNIB du candidat_profil fixture
    )

    response = await client.post(
        "/api/v1/candidat/candidatures",
        json={
            "administration_id": administration_id,
            "examen_id": examen_id,
            "numero_recepisse": "000003",
        },
        headers=candidat_headers,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ajout_candidature_sur_examen_non_publie_reste_en_attente(
    client: AsyncClient, admin_headers: dict, candidat_headers: dict, db_session: AsyncSession
) -> None:
    examen_id, administration_id = await _creer_examen(client, admin_headers, db_session)

    response = await client.post(
        "/api/v1/candidat/candidatures",
        json={
            "administration_id": administration_id,
            "examen_id": examen_id,
            "numero_recepisse": "000004",
        },
        headers=candidat_headers,
    )

    assert response.status_code == 201
    assert response.json()["statut_verification"] == "EN_ATTENTE"


@pytest.mark.asyncio
async def test_ajout_candidature_sans_donnee_de_verification_necessite_otp(
    client: AsyncClient,
    admin_headers: dict,
    candidat_headers: dict,
    db_session: AsyncSession,
) -> None:
    """Résultat publié mais sans CNIB ni date de naissance (examen scolaire léger) :
    fallback OTP (mécanisme 3, § 5)."""
    examen_id, administration_id = await _creer_examen(client, admin_headers, db_session)
    admin_id = await _utilisateur_id(db_session, administration_id)
    await _publier_resultat(
        db_session,
        administration_id=administration_id,
        examen_id=examen_id,
        admin_id=admin_id,
        numero_recepisse="000005",
    )

    response = await client.post(
        "/api/v1/candidat/candidatures",
        json={
            "administration_id": administration_id,
            "examen_id": examen_id,
            "numero_recepisse": "000005",
        },
        headers=candidat_headers,
    )

    assert response.status_code == 201
    assert response.json()["methode_verification"] == "OTP_SMS"


@pytest.mark.asyncio
async def test_meme_recepisse_ne_peut_pas_etre_lie_deux_fois(
    client: AsyncClient,
    admin_headers: dict,
    candidat_headers: dict,
    autre_candidat_headers: dict,
    db_session: AsyncSession,
) -> None:
    examen_id, administration_id = await _creer_examen(client, admin_headers, db_session)
    await client.post(
        "/api/v1/candidat/candidatures",
        json={
            "administration_id": administration_id,
            "examen_id": examen_id,
            "numero_recepisse": "000006",
        },
        headers=candidat_headers,
    )

    response = await client.post(
        "/api/v1/candidat/candidatures",
        json={
            "administration_id": administration_id,
            "examen_id": examen_id,
            "numero_recepisse": "000006",
        },
        headers=autre_candidat_headers,
    )

    assert response.status_code == 409
