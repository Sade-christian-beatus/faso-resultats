import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.guid import GUID

if TYPE_CHECKING:
    from app.models.ingestion import Ingestion
    from app.models.notification_preinscription import NotificationPreinscription
    from app.models.resultat import Resultat


class TypeExamen(str, enum.Enum):
    CEP = "CEP"
    BEPC = "BEPC"
    BAC = "BAC"
    CONCOURS_DIRECT = "CONCOURS_DIRECT"


class StatutExamen(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Examen(TimestampMixin, Base):
    __tablename__ = "examens"
    __table_args__ = (Index("ix_examens_statut_annee", "statut", "annee"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    type_examen: Mapped[TypeExamen] = mapped_column(Enum(TypeExamen, name="type_examen"))
    annee: Mapped[int] = mapped_column(Integer)
    libelle: Mapped[str] = mapped_column(String(255))
    statut: Mapped[StatutExamen] = mapped_column(
        Enum(StatutExamen, name="statut_examen"), default=StatutExamen.DRAFT
    )

    resultats: Mapped[list["Resultat"]] = relationship(back_populates="examen")
    ingestions: Mapped[list["Ingestion"]] = relationship(back_populates="examen")
    notifications: Mapped[list["NotificationPreinscription"]] = relationship(
        back_populates="examen"
    )
