import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.encrypted_str import EncryptedJSON
from app.models.guid import GUID
from app.models.resultat import PhasePublication

if TYPE_CHECKING:
    from app.models.examen import Examen
    from app.models.resultat import Resultat


class TypeFichier(str, enum.Enum):
    PDF = "PDF"
    EXCEL = "EXCEL"
    PDF_OCR = "PDF_OCR"


class StatutIngestion(str, enum.Enum):
    EN_ATTENTE = "EN_ATTENTE"
    PREVISUALISATION = "PREVISUALISATION"
    VALIDEE = "VALIDEE"
    PUBLIEE = "PUBLIEE"
    REJETEE = "REJETEE"


class Ingestion(TimestampMixin, Base):
    """Un import de fichier source. Chaque résultat créé y est rattaché pour la traçabilité."""

    __tablename__ = "ingestions"
    __table_args__ = (
        Index("ix_ingestions_administration_created", "administration_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    administration_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("administrations.id", ondelete="CASCADE"), nullable=False
    )
    examen_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("examens.id", ondelete="CASCADE"), nullable=False
    )
    admin_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("utilisateurs.id", ondelete="RESTRICT"), nullable=False
    )
    nom_fichier: Mapped[str] = mapped_column(String(255))
    chemin_fichier: Mapped[str] = mapped_column(String(500))
    type_fichier: Mapped[TypeFichier] = mapped_column(Enum(TypeFichier, name="type_fichier"))
    statut: Mapped[StatutIngestion] = mapped_column(
        Enum(StatutIngestion, name="statut_ingestion"), default=StatutIngestion.EN_ATTENTE
    )
    # Phase this list belongs to (chosen by the admin at upload for multi-phase exams);
    # every Resultat created from it carries the same phase.
    phase: Mapped[PhasePublication] = mapped_column(
        Enum(PhasePublication, name="phase_publication"),
        default=PhasePublication.RESULTAT_UNIQUE,
    )
    nombre_lignes_detectees: Mapped[int] = mapped_column(Integer, default=0)
    nombre_erreurs: Mapped[int] = mapped_column(Integer, default=0)
    publiee_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Aperçu des lignes extraites, en attente de correction/publication.
    # Chaque élément : {"ligne": int, "donnees": {...}, "brut": {...}, "erreurs": [...]}
    # Chiffré (CNIB, date de naissance des candidats). Toujours réassigné en entier,
    # jamais muté en place : EncryptedJSON ne suit pas les mutations.
    apercu_donnees: Mapped[list] = mapped_column(EncryptedJSON(), default=list)
    # Messages au niveau du fichier entier (pas d'une ligne précise), ex. colonnes non
    # reconnues ou fichier vide — pour que l'admin comprenne pourquoi peu/pas de lignes
    # ont été extraites sans avoir à nous solliciter.
    erreurs_fichier: Mapped[list] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), default=list
    )

    examen: Mapped["Examen"] = relationship(back_populates="ingestions")
    resultats: Mapped[list["Resultat"]] = relationship(back_populates="ingestion")
