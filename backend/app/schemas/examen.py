import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models import CategorieExamen, SourceDonnees, StatutExamen, TypeExamen


class ExamenCreate(BaseModel):
    type_examen: TypeExamen
    annee: int
    libelle: str
    categorie: CategorieExamen | None = None
    serie: str | None = None
    ministere_tutelle: str | None = None
    source_donnees: SourceDonnees = SourceDonnees.FILE_IMPORT
    partenariat_officiel: bool = False
    phases_publication: list[str] = []


class ExamenOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    type_examen: TypeExamen
    annee: int
    libelle: str
    statut: StatutExamen
    categorie: CategorieExamen | None
    serie: str | None
    ministere_tutelle: str | None
    source_donnees: SourceDonnees
    partenariat_officiel: bool
    phases_publication: list[str]
    created_at: datetime
