"""Production bootstrap of the first super-admin (creer_super_admin.py)."""

import pytest
from httpx import AsyncClient

from creer_super_admin import ErreurCreation, creer_super_admin

MOT_DE_PASSE = "Un-mot-de-passe-long-2026"


@pytest.mark.asyncio
async def test_cree_un_super_admin_qui_peut_se_connecter(db_session, client: AsyncClient):
    utilisateur = await creer_super_admin(
        db_session, "  Directeur@FasoResultats.bf ", "Sadé Christian", MOT_DE_PASSE
    )

    assert utilisateur.email == "directeur@fasoresultats.bf"
    assert utilisateur.administration_id is None
    assert utilisateur.mot_de_passe_hash != MOT_DE_PASSE  # bcrypt hash only
    connexion = await client.post(
        "/api/v1/admin/login",
        json={"email": "directeur@fasoresultats.bf", "password": MOT_DE_PASSE},
    )
    assert connexion.status_code == 200, connexion.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("email", "nom", "mot_de_passe", "message"),
    [
        ("pas-un-email", "Nom", MOT_DE_PASSE, "e-mail"),
        ("a@b.bf", "  ", MOT_DE_PASSE, "nom complet"),
        ("a@b.bf", "Nom", "court", "12 caractères"),
    ],
)
async def test_refuse_les_saisies_invalides(db_session, email, nom, mot_de_passe, message):
    with pytest.raises(ErreurCreation, match=message):
        await creer_super_admin(db_session, email, nom, mot_de_passe)


@pytest.mark.asyncio
async def test_refuse_un_compte_deja_existant(db_session):
    await creer_super_admin(db_session, "a@b.bf", "Nom", MOT_DE_PASSE)
    with pytest.raises(ErreurCreation, match="existe déjà"):
        await creer_super_admin(db_session, "A@B.bf", "Autre", MOT_DE_PASSE)
