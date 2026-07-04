import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Date, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.guid import GUID

if TYPE_CHECKING:
    from app.models.examen import Examen
    from app.models.ingestion import Ingestion


class Resultat(TimestampMixin, Base):
    __tablename__ = "resultats"
    __table_args__ = (Index("ix_resultats_examen_pv_jury", "examen_id", "numero_pv", "jury"),)

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

    # Ligne brute telle qu'extraite du fichier source, conservée pour audit.
    donnees_brutes: Mapped[dict] = mapped_column(JSON().with_variant(JSONB, "postgresql"))

    examen: Mapped["Examen"] = relationship(back_populates="resultats")
    ingestion: Mapped["Ingestion"] = relationship(back_populates="resultats")
