import enum
import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.guid import GUID

if TYPE_CHECKING:
    from app.models.utilisateur import Utilisateur


class PlanAbonnement(str, enum.Enum):
    STARTER = "STARTER"
    STANDARD = "STANDARD"
    PREMIUM = "PREMIUM"


class StatutAdministration(str, enum.Enum):
    ACTIF = "ACTIF"
    SUSPENDU = "SUSPENDU"
    PILOTE = "PILOTE"
    RESILIE = "RESILIE"


class Administration(TimestampMixin, Base):
    """Un tenant du SaaS B2G = une administration publique cliente (OCECOS, Office du
    BAC, AGRE...). Voir docs/PIVOT_SAAS_B2G.md § 2.2."""

    __tablename__ = "administrations"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    nom_officiel: Mapped[str] = mapped_column(String(255))
    sigle: Mapped[str] = mapped_column(String(50))
    ministere_tutelle: Mapped[str] = mapped_column(String(255))
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    couleur_primaire: Mapped[str | None] = mapped_column(String(20), nullable=True)
    domaine_personnalise: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_referent_nom: Mapped[str] = mapped_column(String(255))
    contact_referent_email: Mapped[str] = mapped_column(String(255))
    contact_referent_telephone: Mapped[str] = mapped_column(String(20))
    date_signature_convention: Mapped[date | None] = mapped_column(Date, nullable=True)
    convention_active: Mapped[bool] = mapped_column(Boolean, default=False)
    plan_abonnement: Mapped[PlanAbonnement] = mapped_column(
        Enum(PlanAbonnement, name="plan_abonnement"), default=PlanAbonnement.STARTER
    )
    quota_sms_mensuel: Mapped[int] = mapped_column(Integer, default=0)
    quota_examens_annuel: Mapped[int] = mapped_column(Integer, default=0)
    statut: Mapped[StatutAdministration] = mapped_column(
        Enum(StatutAdministration, name="statut_administration"),
        default=StatutAdministration.PILOTE,
    )

    utilisateurs: Mapped[list["Utilisateur"]] = relationship(back_populates="administration")
