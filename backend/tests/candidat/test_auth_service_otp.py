"""Tests d'AuthCandidatService — anti brute-force sur le code OTP.

Note de fidélité au comportement réel (voir rapport BLOC B) : ce service n'implémente
PAS un verrouillage de 15 minutes au niveau du numéro de téléphone. Le verrouillage
actuel invalide uniquement le code OTP courant après 3 échecs ; générer un nouveau code
(ré-appeler /login ou /inscription) réinitialise immédiatement le compteur, sans délai
d'attente forcé. Les tests ci-dessous documentent ce comportement réel."""

import pytest

from app.config import get_settings
from app.services.candidat.auth_service import AuthCandidatService

settings = get_settings()


@pytest.mark.asyncio
async def test_trois_echecs_puis_quatrieme_tentative_echoue_aussi() -> None:
    telephone = "+22670000050"
    code = await AuthCandidatService.generer_otp(telephone)
    assert code

    for _ in range(settings.candidat_otp_max_tentatives):
        assert await AuthCandidatService.verifier_otp(telephone, "000000") is False

    # 4ème tentative, même avec le bon code : le code a été invalidé par le verrouillage.
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
    code_a = await AuthCandidatService.generer_otp(telephone_a)
    code_b = await AuthCandidatService.generer_otp(telephone_b)

    for _ in range(settings.candidat_otp_max_tentatives):
        await AuthCandidatService.verifier_otp(telephone_a, "000000")

    # Le verrouillage du téléphone A ne doit pas affecter le téléphone B.
    assert await AuthCandidatService.verifier_otp(telephone_b, code_b) is True
    assert await AuthCandidatService.verifier_otp(telephone_a, code_a) is False


@pytest.mark.asyncio
async def test_verrouillage_nest_pas_temporise_a_ce_jour() -> None:
    """Documente un écart réel avec un verrouillage "15 minutes" attendu : générer un
    nouveau code immédiatement après un verrouillage suffit à débloquer le numéro, sans
    attente forcée. À traiter en amélioration post-démo si un vrai cool-down est requis."""
    telephone = "+22670000054"
    await AuthCandidatService.generer_otp(telephone)

    for _ in range(settings.candidat_otp_max_tentatives):
        await AuthCandidatService.verifier_otp(telephone, "000000")

    nouveau_code = await AuthCandidatService.generer_otp(telephone)

    assert await AuthCandidatService.verifier_otp(telephone, nouveau_code) is True
