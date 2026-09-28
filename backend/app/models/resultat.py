import enum
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.core.security import hash_deterministe
from app.models.base import Base, TimestampMixin
from app.models.encrypted_str import EncryptedDate, EncryptedJSON, EncryptedStr
from app.models.guid import GUID

if TYPE_CHECKING:
    from app.models.administration import Administration
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
        Index(
            "ix_resultats_examen_pv_jury_phase",
            "examen_id",
            "numero_pv",
            "jury",
            "phase",
            unique=True,
        ),
        Index("ix_resultats_administration", "administration_id"),
        Index("ix_resultats_numero_cnib_hash", "numero_cnib_hash"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    administration_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("administrations.id", ondelete="CASCADE"), nullable=False
    )
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
    # Identity data encrypted at rest (audit 2026-08-17, same scheme as
    # `profils_candidats`): never shown publicly, only used to verify a candidate.
    date_naissance: Mapped[date | None] = mapped_column(EncryptedDate(), nullable=True)
    lieu_naissance: Mapped[str | None] = mapped_column(EncryptedStr(), nullable=True)
    etablissement: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Renseigné pour les concours directs (identification forte) ; vide pour CEP/BEPC/BAC.
    numero_cnib: Mapped[str | None] = mapped_column(EncryptedStr(255), nullable=True)
    # Deterministic hash of `numero_cnib` (same pepper as `profils_candidats`), set
    # automatically by `_hasher_cnib`: lets the candidate matching find results by CNIB
    # with an index instead of decrypting every row.
    numero_cnib_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

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

    # Ligne brute telle qu'extraite du fichier source, conservée pour audit. Chiffrée :
    # elle contient les mêmes CNIB/date de naissance que les colonnes ci-dessus.
    donnees_brutes: Mapped[dict] = mapped_column(EncryptedJSON())

    administration: Mapped["Administration"] = relationship()
    examen: Mapped["Examen"] = relationship(back_populates="resultats")
    ingestion: Mapped["Ingestion"] = relationship(back_populates="resultats")

    @validates("numero_cnib")
    def _hasher_cnib(self, _key: str, numero_cnib: str | None) -> str | None:
        self.numero_cnib_hash = hash_deterministe(numero_cnib) if numero_cnib else None
        return numero_cnib
