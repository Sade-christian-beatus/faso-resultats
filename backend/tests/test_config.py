"""Garde-fou anti-déploiement dangereux : ENVIRONMENT=production ne doit jamais
démarrer avec un secret de développement resté par défaut (audit 2026-07-08)."""

import pytest
from pydantic import ValidationError

from app.config import Settings, _valider_secrets_production


def test_production_avec_secrets_par_defaut_leve_une_erreur() -> None:
    settings = Settings(environment="production")

    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        _valider_secrets_production(settings)


def test_production_avec_secrets_surcharges_ne_leve_rien() -> None:
    settings = Settings(
        environment="production",
        jwt_secret_key="une-vraie-cle-secrete-generee",
        candidat_hash_pepper="un-vrai-pepper-genere",
        api_key_pepper="un-autre-vrai-pepper-genere",
    )

    _valider_secrets_production(settings)


def test_production_avec_api_key_pepper_par_defaut_leve_une_erreur() -> None:
    settings = Settings(
        environment="production",
        jwt_secret_key="une-vraie-cle-secrete-generee",
        candidat_hash_pepper="un-vrai-pepper-genere",
    )

    with pytest.raises(RuntimeError, match="API_KEY_PEPPER"):
        _valider_secrets_production(settings)


def test_developpement_avec_secrets_par_defaut_ne_leve_rien() -> None:
    settings = Settings(environment="development")

    _valider_secrets_production(settings)


def test_environment_avec_variante_de_casse_est_rejete() -> None:
    """Une faute de frappe comme "Production" ne doit jamais contourner silencieusement
    _valider_secrets_production (comparaison littérale à "production") ni le masquage
    du code OTP de debug — Pydantic doit refuser toute valeur hors de l'énumération."""
    with pytest.raises(ValidationError):
        Settings(environment="Production")
