import uuid

from pydantic import BaseModel, EmailStr

from app.models import RoleUtilisateur


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UtilisateurOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    administration_id: uuid.UUID | None
    email: EmailStr
    nom_complet: str
    role: RoleUtilisateur
    actif: bool
