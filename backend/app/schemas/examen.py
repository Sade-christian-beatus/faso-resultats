import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator

from app.models import (
    CategorieExamen,
    PhasePublication,
    SourceDonnees,
    StatutExamen,
    TypeExamen,
)


class ExamenCreate(BaseModel):
    type_examen: TypeExamen
    annee: int
    libelle: str
    categorie: CategorieExamen | None = None
    serie: str | None = None
    ministere_tutelle: str | None = None
    source_donnees: SourceDonnees = SourceDonnees.FILE_IMPORT
    partenariat_officiel: bool = False
    # Ordered phases (docs/CONTEXTE_METIER.md § 2.4), e.g. EPREUVES_SPORTIVES,
    # ADMISSIBILITE, ADMISSION_DEFINITIVE. Empty = single publication.
    phases_publication: list[PhasePublication] = []

    @field_validator("phases_publication")
    @classmethod
    def _phases_distinctes(cls, phases: list[PhasePublication]) -> list[PhasePublication]:
        if len(set(phases)) != len(phases):
            raise ValueError("Une même phase ne peut pas apparaître deux fois")
        return phases


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
    phases_cloturees: list[str] = []
    created_at: datetime
