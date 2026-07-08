import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.candidature import MethodeVerification, StatutVerificationCandidature


class InscriptionRequest(BaseModel):
    numero_cnib: str = Field(min_length=1, max_length=20)
    nom_complet: str = Field(min_length=1, max_length=200)
    date_naissance: date
    telephone: str = Field(min_length=8, max_length=20)
    consentement_apdp: bool
    consentement_apdp_version: str = Field(min_length=1, max_length=20)

    @field_validator("consentement_apdp")
    @classmethod
    def _consentement_obligatoire(cls, valeur: bool) -> bool:
        if not valeur:
            raise ValueError("Le consentement APDP est obligatoire pour créer un compte")
        return valeur


class InscriptionResponse(BaseModel):
    message: str
    expire_dans_minutes: int
    code_otp_debug: str | None = None


class LoginRequest(BaseModel):
    telephone: str = Field(min_length=8, max_length=20)


class LoginResponse(BaseModel):
    message: str
    code_otp_debug: str | None = None


class OtpVerifyRequest(BaseModel):
    telephone: str = Field(min_length=8, max_length=20)
    code: str = Field(min_length=6, max_length=6)


class SessionResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    compte_cree: bool


class ProfilCandidatOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    nom_complet: str
    telephone_verifie: bool
    email: EmailStr | None
    email_verifie: bool
    notifications_sms: bool
    notifications_push: bool
    notifications_email: bool
    statut: str
    derniere_connexion: datetime | None


class ProfilCandidatUpdate(BaseModel):
    email: EmailStr | None = None
    notifications_sms: bool | None = None
    notifications_push: bool | None = None
    notifications_email: bool | None = None


class CandidatureCreate(BaseModel):
    administration_id: uuid.UUID
    examen_id: uuid.UUID
    numero_recepisse: str = Field(min_length=1, max_length=20)


class CandidatureOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    administration_id: uuid.UUID
    examen_id: uuid.UUID
    numero_recepisse: str
    statut_verification: StatutVerificationCandidature
    methode_verification: MethodeVerification | None
    notifications_activees: bool
    dernier_resultat_statut: str | None
    dernier_resultat_phase: str | None
    dernier_resultat_publie_at: datetime | None
    # Non persisté : présent uniquement sur la réponse de création quand le mécanisme 3
    # (fallback OTP) est déclenché, et seulement hors production — même logique que
    # InscriptionResponse.code_otp_debug.
    code_otp_debug: str | None = None


class CandidatureOtpConfirmRequest(BaseModel):
    code: str = Field(min_length=6, max_length=6)


class CandidatureExport(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    administration_id: uuid.UUID
    examen_id: uuid.UUID
    numero_recepisse: str
    statut_verification: StatutVerificationCandidature
    methode_verification: MethodeVerification | None
    date_verification: datetime | None
    dernier_resultat_statut: str | None
    dernier_resultat_phase: str | None
    dernier_resultat_publie_at: datetime | None
    created_at: datetime


class JournalEntreeExport(BaseModel):
    model_config = {"from_attributes": True}

    action: str
    ip: str | None
    timestamp: datetime


class ProfilCandidatExport(BaseModel):
    """Droit à la portabilité (docs/APDP_PROFIL_CANDIDAT.md § 8) : l'intégralité des
    données du profil connecté, dans un format structuré et exploitable — contrairement
    à `ProfilCandidatOut` (§ Droit d'accès), qui expose volontairement moins de champs
    pour l'usage courant du dashboard."""

    id: uuid.UUID
    numero_cnib: str
    nom_complet: str
    date_naissance: str
    telephone: str
    email: str | None
    statut: str
    consentement_apdp_date: datetime
    consentement_apdp_version: str
    created_at: datetime
    derniere_connexion: datetime | None
    candidatures: list[CandidatureExport]
    journal: list[JournalEntreeExport]
