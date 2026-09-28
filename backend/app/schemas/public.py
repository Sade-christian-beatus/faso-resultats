import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models import PhasePublication, TypeExamen
from app.services.phases import SituationCandidat, StatutPhase


class AdministrationPublicOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    code: str
    nom_officiel: str
    sigle: str
    logo_url: str | None
    couleur_primaire: str | None


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
    # Concours à phases multiples (docs/CONTEXTE_METIER.md § 2.4) : présents sur le
    # modèle depuis la Phase 1 mais jamais exposés publiquement jusqu'ici — nécessaires
    # pour l'affichage "Rang / Phase / Prochaine étape" attendu côté clients (mobile).
    rang_numerique: int | None
    rang_affiche: str | None
    phase: PhasePublication
    phase_suivante_attendue: PhasePublication | None
    date_publication_phase: datetime | None


class EtapeParcoursOut(BaseModel):
    """One phase of the exam for one candidate (app/services/phases.py)."""

    phase: PhasePublication
    statut_phase: StatutPhase
    situation: SituationCandidat
    resultat: ResultatPublicOut | None


class ParcoursCandidatOut(BaseModel):
    numero_pv: str
    jury: str
    etapes: list[EtapeParcoursOut]


class DroitsCandidatOut(BaseModel):
    contact_dpo: str
    droits: list[str]
    delai_reponse_indicatif: str
