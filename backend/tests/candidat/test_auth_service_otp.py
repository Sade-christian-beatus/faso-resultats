"""Tests d'AuthCandidatService — anti brute-force sur le code OTP.

Le verrouillage porte sur le numéro de téléphone (`candidat_otp_lockout_minutes`),
via une clé de cache distincte de l'OTP lui-même : demander un nouveau code pendant
la fenêtre de verrouillage ne le contourne plus (correctif de sécurité — voir
docs/ROADMAP.md, l'ancienne version ne verrouillait que le code courant)."""

import pytest

from app.config import get_settings
from app.services.candidat.auth_service import AuthCandidatService

settings = get_settings()


async def _epuiser_les_tentatives(telephone: str) -> None:
    """`candidat_otp_max_tentatives` échecs marquent le compteur au seuil ; il faut UN
    appel de plus pour que `verifier_otp` déclenche effectivement le verrouillage (le
    contrôle du seuil se fait en entrée de fonction, pas au moment de l'incrément)."""
    for _ in range(settings.candidat_otp_max_tentatives + 1):
        await AuthCandidatService.verifier_otp(telephone, "000000")


@pytest.mark.asyncio
async def test_trois_echecs_puis_quatrieme_tentative_echoue_aussi() -> None:
    telephone = "+22670000050"
    code = await AuthCandidatService.generer_otp(telephone)
    assert code

    await _epuiser_les_tentatives(telephone)

    # Même avec le bon code : le numéro est verrouillé.
    assert await AuthCandidatService.verifier_otp(telephone, code) is False


@pytest.mark.asyncio
async def test_otp_invalide_apres_usage_reussi() -> None:
    telephone = "+22670000051"
    code = await AuthCandidatService.generer_otp(telephone)

    assert await AuthCandidatService.verifier_otp(telephone, code) is True
    # Rejouer le même code (replay) doit échouer : l'entrée a été supprimée après succès.
    assert await AuthCandidatService.verifier_otp(telephone, code) is False


@pytest.mark.asyncio
async def test_compteur_de_tentatives_est_independant_par_telephone() -> None:
    telephone_a = "+22670000052"
    telephone_b = "+22670000053"
    await AuthCandidatService.generer_otp(telephone_a)
    code_b = await AuthCandidatService.generer_otp(telephone_b)

    await _epuiser_les_tentatives(telephone_a)

    # Le verrouillage du téléphone A ne doit pas affecter le téléphone B.
    assert await AuthCandidatService.verifier_otp(telephone_b, code_b) is True
    assert await AuthCandidatService.est_verrouille(telephone_a) is True


@pytest.mark.asyncio
async def test_verrouillage_est_reellement_temporise() -> None:
    """Générer un nouveau code pendant la fenêtre de verrouillage ne doit PAS
    débloquer le numéro — le correctif par rapport à l'ancien comportement."""
    telephone = "+22670000054"
    await AuthCandidatService.generer_otp(telephone)
    await _epuiser_les_tentatives(telephone)

    assert await AuthCandidatService.est_verrouille(telephone) is True

    # Demander un nouveau code pendant le verrouillage doit être refusé (None).
    nouveau_code = await AuthCandidatService.generer_otp(telephone)
    assert nouveau_code is None


@pytest.mark.asyncio
async def test_verrouillage_leve_apres_expiration(monkeypatch: pytest.MonkeyPatch) -> None:
    """Une fois la fenêtre de verrouillage expirée (simulée avec un TTL nul), le
    numéro redevient utilisable normalement."""
    monkeypatch.setattr(settings, "candidat_otp_lockout_minutes", 0)
    telephone = "+22670000055"
    await AuthCandidatService.generer_otp(telephone)
    await _epuiser_les_tentatives(telephone)

    # TTL de 0 seconde : la clé de verrouillage expire immédiatement (fallback mémoire,
    # voir app.core.cache) ou n'est jamais vue comme active selon le backend de cache.
    nouveau_code = await AuthCandidatService.generer_otp(telephone)
    assert nouveau_code is not None
    assert await AuthCandidatService.verifier_otp(telephone, nouveau_code) is True
