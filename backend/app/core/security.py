import hashlib
import hmac
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Deux audiences JWT distinctes (admin / candidat) : un token émis pour l'un ne peut
# jamais authentifier une route de l'autre, même si la clé de signature est partagée
# (docs/PROFIL_CANDIDAT_UNIFIE.md § 11, "deux middlewares d'authentification distincts").
_AUD_ADMIN = "admin"
_AUD_CANDIDAT = "candidat"


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return _pwd_context.verify(plain_password, password_hash)


def hash_deterministe(valeur: str) -> str:
    """Hash HMAC-SHA256 stable d'une donnée sensible (CNIB, téléphone), pour permettre
    une recherche/unicité en base sans jamais indexer la valeur en clair
    (docs/PROFIL_CANDIDAT_UNIFIE.md § 11, « indexer sur un hash déterministe »)."""
    return hmac.new(
        settings.candidat_hash_pepper.encode(), valeur.encode(), hashlib.sha256
    ).hexdigest()


def create_access_token(subject: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": subject, "exp": expire, "aud": _AUD_ADMIN}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str:
    """Retourne l'identifiant admin (sub) porté par le token. Lève JWTError si invalide,
    expiré, ou émis pour une autre audience (ex. token candidat)."""
    payload = jwt.decode(
        token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm], audience=_AUD_ADMIN
    )
    subject = payload.get("sub")
    if subject is None:
        raise JWTError("Token sans sujet")
    return subject


def create_candidat_access_token(subject: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.candidat_jwt_expire_minutes)
    payload = {"sub": subject, "exp": expire, "aud": _AUD_CANDIDAT}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_candidat_access_token(token: str) -> str:
    """Retourne l'identifiant candidat (sub) porté par le token. Lève JWTError si
    invalide, expiré, ou émis pour une autre audience (ex. token admin)."""
    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        audience=_AUD_CANDIDAT,
    )
    subject = payload.get("sub")
    if subject is None:
        raise JWTError("Token sans sujet")
    return subject
