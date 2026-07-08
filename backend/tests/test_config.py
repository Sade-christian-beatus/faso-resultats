"""Garde-fou anti-déploiement dangereux : ENVIRONMENT=production ne doit jamais
démarrer avec un secret de développement resté par défaut (audit 2026-07-08)."""

import pytest

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
    )

    _valider_secrets_production(settings)


def test_developpement_avec_secrets_par_defaut_ne_leve_rien() -> None:
    settings = Settings(environment="development")

    _valider_secrets_production(settings)
