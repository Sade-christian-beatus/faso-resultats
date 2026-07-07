import uuid

from pydantic import BaseModel

from app.models import TypeExamen


class ExamenPublicOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    administration_id: uuid.UUID
    type_examen: TypeExamen
    annee: int
    libelle: str


class ResultatPublicOut(BaseModel):
    model_config = {"from_attributes": True}

    numero_pv: str
    jury: str
    nom: str
    prenom: str
    decision: str
    moyenne: float | None
    etablissement: str | None


class DroitsCandidatOut(BaseModel):
    contact_dpo: str
    droits: list[str]
    delai_reponse_indicatif: str
