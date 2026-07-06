import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.encrypted_str import EncryptedStr
from app.models.guid import GUID

if TYPE_CHECKING:
    from app.models.candidature import Candidature
    from app.models.journal_consultation_profil import JournalConsultationProfil


class StatutProfilCandidat(str, enum.Enum):
    ACTIF = "ACTIF"
    SUSPENDU = "SUSPENDU"
    SUPPRIME = "SUPPRIME"


class ProfilCandidat(TimestampMixin, Base):
    """Compte candidat unique au niveau plateforme, transversal à toutes les
    administrations (docs/PROFIL_CANDIDAT_UNIFIE.md § 2-3). Vit dans le schéma
    `plateforme`, distinct des schémas tenants : aucune administration ne peut lister
    ou interroger cette table.

    CNIB, téléphone et date de naissance sont chiffrés au repos (`EncryptedStr`) ; les
    colonnes `*_hash` (HMAC déterministe, voir `app.core.security.hash_deterministe`)
    permettent la recherche/unicité sans jamais indexer la valeur en clair."""

    __tablename__ = "profils_candidats"
    __table_args__ = {"schema": "plateforme"}

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)

    numero_cnib: Mapped[str] = mapped_column(EncryptedStr(255))
    numero_cnib_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    nom_complet: Mapped[str] = mapped_column(String(200))
    date_naissance: Mapped[str] = mapped_column(EncryptedStr(255))  # ISO 8601 (YYYY-MM-DD)
    lieu_naissance: Mapped[str | None] = mapped_column(String(200), nullable=True)
    sexe: Mapped[str | None] = mapped_column(String(1), nullable=True)

    telephone: Mapped[str] = mapped_column(EncryptedStr(255))
    telephone_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    telephone_verifie: Mapped[bool] = mapped_column(Boolean, default=False)
    operateur_telephone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    email_verifie: Mapped[bool] = mapped_column(Boolean, default=False)

    # Authentification : OTP SMS par défaut (§ 4.2), mot de passe optionnel.
    mot_de_passe_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    derniere_connexion: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    notifications_sms: Mapped[bool] = mapped_column(Boolean, default=True)
    notifications_push: Mapped[bool] = mapped_column(Boolean, default=False)
    notifications_email: Mapped[bool] = mapped_column(Boolean, default=False)

    statut: Mapped[StatutProfilCandidat] = mapped_column(
        Enum(StatutProfilCandidat, name="statut_profil_candidat"),
        default=StatutProfilCandidat.ACTIF,
    )
    consentement_apdp_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consentement_apdp_version: Mapped[str] = mapped_column(String(20))

    candidatures: Mapped[list["Candidature"]] = relationship(
        back_populates="profil", cascade="all, delete-orphan"
    )
    # Cascade ORM explicite (pas seulement l'ON DELETE CASCADE en base) : le droit à
    # l'oubli doit purger le journal de façon garantie, y compris sur un moteur qui
    # n'impose pas les contraintes FK (SQLite en test) — docs/PROFIL_CANDIDAT_UNIFIE.md § 7.
    journal: Mapped[list["JournalConsultationProfil"]] = relationship(cascade="all, delete-orphan")
