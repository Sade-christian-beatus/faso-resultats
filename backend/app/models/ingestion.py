import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.guid import GUID

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

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    examen_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("examens.id", ondelete="CASCADE"), nullable=False
    )
    admin_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("admins.id", ondelete="RESTRICT"), nullable=False
    )
    nom_fichier: Mapped[str] = mapped_column(String(255))
    chemin_fichier: Mapped[str] = mapped_column(String(500))
    type_fichier: Mapped[TypeFichier] = mapped_column(Enum(TypeFichier, name="type_fichier"))
    statut: Mapped[StatutIngestion] = mapped_column(
        Enum(StatutIngestion, name="statut_ingestion"), default=StatutIngestion.EN_ATTENTE
    )
    nombre_lignes_detectees: Mapped[int] = mapped_column(Integer, default=0)
    nombre_erreurs: Mapped[int] = mapped_column(Integer, default=0)
    publiee_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    examen: Mapped["Examen"] = relationship(back_populates="ingestions")
    resultats: Mapped[list["Resultat"]] = relationship(back_populates="ingestion")
