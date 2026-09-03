import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models import StatutApiKey, StatutPartenaire


class PartenaireCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=255)
    contact_nom: str = Field(min_length=1, max_length=255)
    contact_email: EmailStr


class PartenaireUpdate(BaseModel):
    nom: str | None = None
    contact_nom: str | None = None
    contact_email: EmailStr | None = None
    statut: StatutPartenaire | None = None


class PartenaireOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    nom: str
    contact_nom: str
    contact_email: str
    statut: StatutPartenaire
    created_at: datetime


class ApiKeyCreate(BaseModel):
    tier: str = Field(default="STANDARD", max_length=50)
    quota_quotidien: int = Field(default=1000, gt=0)


class ApiKeyOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    partenaire_id: uuid.UUID
    prefixe: str
    tier: str
    quota_quotidien: int
    statut: StatutApiKey
    derniere_utilisation: datetime | None
    created_at: datetime


class ApiKeyCreeeOut(ApiKeyOut):
    """Renvoyé une seule fois, à la création : la seule occasion où la clé en clair
    est visible — non récupérable ensuite, seul son hash est stocké en base."""

    cle: str
