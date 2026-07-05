import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.guid import GUID

if TYPE_CHECKING:
    from app.models.examen import Examen


class StatutNotification(str, enum.Enum):
    EN_ATTENTE = "EN_ATTENTE"
    ENVOYE = "ENVOYE"
    ECHEC = "ECHEC"


class NotificationPreinscription(TimestampMixin, Base):
    """Préinscription à la notification SMS (Phase 2). Table créée dès Phase 1 pour ne pas
    devoir réécrire le schéma plus tard."""

    __tablename__ = "notifications_preinscription"
    __table_args__ = (Index("ix_notifications_examen_statut", "examen_id", "statut"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    administration_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("administrations.id", ondelete="CASCADE"), nullable=False
    )
    examen_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("examens.id", ondelete="CASCADE"), nullable=False
    )
    telephone: Mapped[str] = mapped_column(String(20))
    numero_pv: Mapped[str] = mapped_column(String(50))
    consentement: Mapped[bool] = mapped_column(Boolean, default=False)
    statut: Mapped[StatutNotification] = mapped_column(
        Enum(StatutNotification, name="statut_notification"), default=StatutNotification.EN_ATTENTE
    )
    envoye_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    examen: Mapped["Examen"] = relationship(back_populates="notifications")
