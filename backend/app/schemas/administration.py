import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models import PlanAbonnement, RoleUtilisateur, StatutAdministration


class AdministrationCreate(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    nom_officiel: str = Field(min_length=1, max_length=255)
    sigle: str = Field(min_length=1, max_length=50)
    ministere_tutelle: str = Field(min_length=1, max_length=255)
    contact_referent_nom: str = Field(min_length=1, max_length=255)
    contact_referent_email: EmailStr
    contact_referent_telephone: str = Field(min_length=1, max_length=20)
    logo_url: str | None = None
    couleur_primaire: str | None = None
    domaine_personnalise: str | None = None
    plan_abonnement: PlanAbonnement = PlanAbonnement.STARTER
    quota_sms_mensuel: int = 0
    quota_examens_annuel: int = 0
    statut: StatutAdministration = StatutAdministration.PILOTE


class AdministrationUpdate(BaseModel):
    nom_officiel: str | None = None
    sigle: str | None = None
    ministere_tutelle: str | None = None
    contact_referent_nom: str | None = None
    contact_referent_email: EmailStr | None = None
    contact_referent_telephone: str | None = None
    logo_url: str | None = None
    couleur_primaire: str | None = None
    domaine_personnalise: str | None = None
    date_signature_convention: date | None = None
    convention_active: bool | None = None
    plan_abonnement: PlanAbonnement | None = None
    quota_sms_mensuel: int | None = None
    quota_examens_annuel: int | None = None
    statut: StatutAdministration | None = None


class AdministrationOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    code: str
    nom_officiel: str
    sigle: str
    ministere_tutelle: str
    logo_url: str | None
    couleur_primaire: str | None
    domaine_personnalise: str | None
    contact_referent_nom: str
    contact_referent_email: str
    contact_referent_telephone: str
    date_signature_convention: date | None
    convention_active: bool
    plan_abonnement: PlanAbonnement
    quota_sms_mensuel: int
    quota_examens_annuel: int
    statut: StatutAdministration
    created_at: datetime


_ROLES_TENANT = {
    RoleUtilisateur.ADMIN_ADMINISTRATION,
    RoleUtilisateur.OPERATEUR_INGESTION,
    RoleUtilisateur.OPERATEUR_PUBLICATION,
    RoleUtilisateur.LECTEUR,
}


class UtilisateurInitialCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=255)
    nom_complet: str = Field(min_length=1, max_length=255)
    role: RoleUtilisateur = RoleUtilisateur.ADMIN_ADMINISTRATION
    telephone: str | None = None

    @field_validator("role")
    @classmethod
    def _role_doit_etre_rattachee_a_un_tenant(cls, valeur: RoleUtilisateur) -> RoleUtilisateur:
        if valeur not in _ROLES_TENANT:
            raise ValueError(
                "Rôle invalide pour un utilisateur d'administration : SUPER_ADMIN et "
                "SUPPORT sont réservés aux comptes plateforme, sans administration_id."
            )
        return valeur
