import json
from datetime import date

from cryptography.fernet import Fernet
from sqlalchemy import String, Text
from sqlalchemy.types import TypeDecorator

from app.config import get_settings


def _fernet() -> Fernet:
    return Fernet(get_settings().candidat_encryption_key.encode())


class EncryptedStr(TypeDecorator):
    """Chiffrement au repos (Fernet/AES) des données sensibles : profil candidat (CNIB,
    téléphone, date de naissance — docs/PROFIL_CANDIDAT_UNIFIE.md § 8) et identité des
    candidats dans `resultats` (CNIB, lieu de naissance). Non recherchable en base : les
    colonnes qui doivent être filtrables (CNIB, téléphone) sont doublées d'une colonne
    `*_hash` (voir `app.core.security.hash_deterministe`)."""

    impl = String
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect) -> str | None:
        if value is None:
            return None
        return _fernet().encrypt(value.encode()).decode()

    def process_result_value(self, value: str | None, dialect) -> str | None:
        if value is None:
            return None
        return _fernet().decrypt(value.encode()).decode()


class EncryptedDate(TypeDecorator):
    """Same as `EncryptedStr` for a date: stored as an encrypted ISO string, exposed to
    Python as a `datetime.date` so callers keep comparing/formatting dates as before."""

    impl = String(255)
    cache_ok = True

    def process_bind_param(self, value: date | None, dialect) -> str | None:
        if value is None:
            return None
        return _fernet().encrypt(value.isoformat().encode()).decode()

    def process_result_value(self, value: str | None, dialect) -> date | None:
        if value is None:
            return None
        return date.fromisoformat(_fernet().decrypt(value.encode()).decode())


class EncryptedJSON(TypeDecorator):
    """Encrypted JSON document, for raw source rows kept for audit (`donnees_brutes`,
    `apercu_donnees`): they hold the same CNIB/birth date as the encrypted columns, so
    leaving them in clear would defeat the column encryption. Not queryable in SQL —
    nothing filters on these documents. Only reassignment is detected (no in-place
    mutation tracking), which is how the ingestion code already updates them."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect) -> str | None:
        if value is None:
            return None
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        return _fernet().encrypt(payload.encode()).decode()

    def process_result_value(self, value: str | None, dialect):
        if value is None:
            return None
        return json.loads(_fernet().decrypt(value.encode()).decode())
