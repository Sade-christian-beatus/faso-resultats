import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models import PhasePublication, StatutIngestion, TypeFichier


class LigneApercu(BaseModel):
    ligne: int
    donnees: dict[str, Any]
    brut: dict[str, Any]
    erreurs: list[str] = []


class IngestionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    examen_id: uuid.UUID
    admin_id: uuid.UUID
    nom_fichier: str
    type_fichier: TypeFichier
    statut: StatutIngestion
    phase: PhasePublication
    nombre_lignes_detectees: int
    nombre_erreurs: int
    erreurs_fichier: list[str] = []
    publiee_at: datetime | None
    created_at: datetime


class IngestionPreviewOut(IngestionOut):
    lignes: list[LigneApercu]


class CorrectionRequest(BaseModel):
    lignes: list[LigneApercu]
