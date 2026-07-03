import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models import StatutExamen, TypeExamen


class ExamenCreate(BaseModel):
    type_examen: TypeExamen
    annee: int
    libelle: str


class ExamenOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    type_examen: TypeExamen
    annee: int
    libelle: str
    statut: StatutExamen
    created_at: datetime
