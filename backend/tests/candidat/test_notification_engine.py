"""Tests de NotificationEngine — respect de la plage silencieuse 22h-6h.

Note de fidélité au comportement réel (voir rapport BLOC B) : sans file de tâches (RQ,
Phase 2 — voir le docstring de NotificationEngine et docs/APDP_PROFIL_CANDIDAT.md § 6),
une notification tombant dans la plage silencieuse est abandonnée, pas mise en file pour
un envoi différé à 6h. Les tests ci-dessous vérifient ce comportement réel plutôt qu'un
report différé qui n'est pas implémenté."""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from app.services.candidat.notification_engine import NotificationEngine


@pytest.mark.parametrize(
    ("heure", "minute", "attendu"),
    [
        (14, 0, False),  # 14h — autorisé
        (23, 0, True),  # 23h — plage silencieuse
        (5, 30, True),  # 5h30 — plage silencieuse
        (6, 0, False),  # 6h pile — fin de la plage silencieuse, autorisé
        (21, 59, False),  # juste avant le début de la plage silencieuse
        (22, 0, True),  # 22h pile — début de la plage silencieuse
    ],
)
def test_dans_plage_silencieuse(heure: int, minute: int, attendu: bool) -> None:
    maintenant = datetime(2026, 7, 6, heure, minute, tzinfo=UTC)

    assert NotificationEngine._dans_plage_silencieuse(maintenant) == attendu


@pytest.mark.asyncio
async def test_envoyer_sms_a_14h_est_autorise() -> None:
    with patch("app.services.candidat.notification_engine.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2026, 7, 6, 14, 0, tzinfo=UTC)
        mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)

        envoye = await NotificationEngine.envoyer_sms("+22670000000", "Test")

    assert envoye is True


@pytest.mark.asyncio
async def test_envoyer_sms_a_23h_est_abandonne() -> None:
    """Comportement réel actuel : pas de mise en file, la notification est perdue."""
    with patch("app.services.candidat.notification_engine.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2026, 7, 6, 23, 0, tzinfo=UTC)

        envoye = await NotificationEngine.envoyer_sms("+22670000000", "Test")

    assert envoye is False


@pytest.mark.asyncio
async def test_envoyer_sms_a_5h30_est_abandonne() -> None:
    with patch("app.services.candidat.notification_engine.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2026, 7, 6, 5, 30, tzinfo=UTC)

        envoye = await NotificationEngine.envoyer_sms("+22670000000", "Test")

    assert envoye is False
