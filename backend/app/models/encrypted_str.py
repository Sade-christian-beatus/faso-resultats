from cryptography.fernet import Fernet
from sqlalchemy import String
from sqlalchemy.types import TypeDecorator

from app.config import get_settings


class EncryptedStr(TypeDecorator):
    """Chiffrement au repos (Fernet/AES) pour les données sensibles du profil candidat
    (CNIB, téléphone, date de naissance — docs/PROFIL_CANDIDAT_UNIFIE.md § 8). Non
    recherchable en base : les colonnes qui doivent être filtrables (CNIB, téléphone)
    sont doublées d'une colonne `*_hash` (voir `app.core.security.hash_deterministe`)."""

    impl = String
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect) -> str | None:
        if value is None:
            return None
        fernet = Fernet(get_settings().candidat_encryption_key.encode())
        return fernet.encrypt(value.encode()).decode()

    def process_result_value(self, value: str | None, dialect) -> str | None:
        if value is None:
            return None
        fernet = Fernet(get_settings().candidat_encryption_key.encode())
        return fernet.decrypt(value.encode()).decode()
