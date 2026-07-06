import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.guid import GUID

if TYPE_CHECKING:
    from app.models.profil_candidat import ProfilCandidat


class StatutVerificationCandidature(str, enum.Enum):
    EN_ATTENTE = "EN_ATTENTE"
    VERIFIE_AUTO = "VERIFIE_AUTO"
    VERIFIE_MANUEL = "VERIFIE_MANUEL"
    REJETE = "REJETE"
    ADMINISTRATION_RESILIEE = "ADMINISTRATION_RESILIEE"


class MethodeVerification(str, enum.Enum):
    CNIB_MATCH_AUTO = "CNIB_MATCH_AUTO"
    DATE_NAISSANCE = "DATE_NAISSANCE"
    OTP_SMS = "OTP_SMS"
    VALIDATION_MANUELLE = "VALIDATION_MANUELLE"


class Candidature(TimestampMixin, Base):
    """Lien entre un `ProfilCandidat` (plateforme) et un examen d'une administration
    (tenant) — la seule table qui traverse la frontière plateforme/tenant
    (docs/PROFIL_CANDIDAT_UNIFIE.md § 3). `administration_id` et `examen_id` sont de
    simples références, volontairement sans FK cross-schéma : le schéma `plateforme`
    reste indépendant des schémas tenants."""

    __tablename__ = "candidatures"
    __table_args__ = (
        UniqueConstraint("administration_id", "numero_recepisse", name="uq_candidature_recepisse"),
        {"schema": "plateforme"},
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)

    profil_candidat_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("plateforme.profils_candidats.id", ondelete="CASCADE"),
        index=True,
    )
    administration_id: Mapped[uuid.UUID] = mapped_column(GUID())
    examen_id: Mapped[uuid.UUID] = mapped_column(GUID())
    numero_recepisse: Mapped[str] = mapped_column(String(20), index=True)

    statut_verification: Mapped[StatutVerificationCandidature] = mapped_column(
        Enum(StatutVerificationCandidature, name="statut_verification_candidature"),
        default=StatutVerificationCandidature.EN_ATTENTE,
    )
    date_verification: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    methode_verification: Mapped[MethodeVerification | None] = mapped_column(
        Enum(MethodeVerification, name="methode_verification"), nullable=True
    )

    notifications_activees: Mapped[bool] = mapped_column(Boolean, default=True)
    derniere_notification_envoyee: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Cache dénormalisé du dernier résultat connu, pour un dashboard rapide sans
    # jointure cross-schéma vers les tables tenant à chaque affichage.
    dernier_resultat_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True)
    dernier_resultat_phase: Mapped[str | None] = mapped_column(String(50), nullable=True)
    dernier_resultat_statut: Mapped[str | None] = mapped_column(String(50), nullable=True)
    dernier_resultat_publie_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    profil: Mapped["ProfilCandidat"] = relationship(back_populates="candidatures")
