import enum
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Date, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.guid import GUID

if TYPE_CHECKING:
    from app.models.examen import Examen
    from app.models.ingestion import Ingestion


class PhasePublication(str, enum.Enum):
    """Étape de publication d'un résultat. Les concours paramilitaires se déroulent en
    plusieurs phases successives (docs/CONTEXTE_METIER.md § 2.4) : un même candidat peut
    avoir un `Resultat` par phase (admis à l'une, absent ou ajourné à la suivante)."""

    RESULTAT_UNIQUE = "RESULTAT_UNIQUE"  # Examens scolaires et concours simples
    EPREUVES_SPORTIVES = "EPREUVES_SPORTIVES"  # Phase 1 paramilitaires
    ADMISSIBILITE = "ADMISSIBILITE"  # Phase 2 (après écrit)
    ADMISSION_DEFINITIVE = "ADMISSION_DEFINITIVE"  # Phase 3 (finale)
    SECOND_TOUR = "SECOND_TOUR"  # BEPC/BAC uniquement


class Resultat(TimestampMixin, Base):
    __tablename__ = "resultats"
    __table_args__ = (
        Index("ix_resultats_examen_pv_jury_phase", "examen_id", "numero_pv", "jury", "phase"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    examen_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("examens.id", ondelete="CASCADE"), nullable=False
    )
    ingestion_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ingestions.id", ondelete="RESTRICT"), nullable=False
    )

    numero_pv: Mapped[str] = mapped_column(String(50))
    jury: Mapped[str] = mapped_column(String(255))

    nom: Mapped[str] = mapped_column(String(255))
    prenom: Mapped[str] = mapped_column(String(255))
    date_naissance: Mapped[date | None] = mapped_column(Date, nullable=True)
    lieu_naissance: Mapped[str | None] = mapped_column(String(255), nullable=True)
    etablissement: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Renseigné pour les concours directs (identification forte) ; vide pour CEP/BEPC/BAC.
    numero_cnib: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Champs spécifiques aux communiqués PDF scannés de la Fonction publique
    # (RECEPISSE-CODE-CENTRE, rang de mérite) — vides pour CEP/BEPC/BAC et les imports
    # Excel/PDF classiques. `numero_recepisse` duplique `numero_pv` (même valeur, nom
    # officiel du document) plutôt que de le remplacer, pour ne pas casser la recherche
    # publique existante par `numero_pv` sur les autres types d'examens.
    numero_recepisse: Mapped[str | None] = mapped_column(String(20), nullable=True)
    code_concours: Mapped[str | None] = mapped_column(String(10), nullable=True)
    code_centre: Mapped[str | None] = mapped_column(String(10), nullable=True)
    rang_numerique: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rang_affiche: Mapped[str | None] = mapped_column(String(10), nullable=True)

    decision: Mapped[str] = mapped_column(String(50))
    moyenne: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)

    # Modèle temporel des concours paramilitaires (docs/CONTEXTE_METIER.md § 2.4) :
    # défaut RESULTAT_UNIQUE pour les examens scolaires et concours à résultat unique.
    phase: Mapped[PhasePublication] = mapped_column(
        Enum(PhasePublication, name="phase_publication"), default=PhasePublication.RESULTAT_UNIQUE
    )
    date_publication_phase: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    phase_suivante_attendue: Mapped[PhasePublication | None] = mapped_column(
        Enum(PhasePublication, name="phase_publication"), nullable=True
    )

    # Ligne brute telle qu'extraite du fichier source, conservée pour audit.
    donnees_brutes: Mapped[dict] = mapped_column(JSON().with_variant(JSONB, "postgresql"))

    examen: Mapped["Examen"] = relationship(back_populates="resultats")
    ingestion: Mapped["Ingestion"] = relationship(back_populates="resultats")
