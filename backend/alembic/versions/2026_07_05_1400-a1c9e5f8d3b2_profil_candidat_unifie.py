"""profil candidat unifié : schéma plateforme, profils_candidats, candidatures,
journal_consultations_profil

Revision ID: a1c9e5f8d3b2
Revises: f4a7c8e21b6d
Create Date: 2026-07-05 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

import app.models.guid

# revision identifiers, used by Alembic.
revision: str = 'a1c9e5f8d3b2'
down_revision: Union[str, None] = 'f4a7c8e21b6d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

statut_profil_candidat = postgresql.ENUM(
    "ACTIF", "SUSPENDU", "SUPPRIME", name="statut_profil_candidat"
)
statut_verification_candidature = postgresql.ENUM(
    "EN_ATTENTE",
    "VERIFIE_AUTO",
    "VERIFIE_MANUEL",
    "REJETE",
    "ADMINISTRATION_RESILIEE",
    name="statut_verification_candidature",
)
methode_verification = postgresql.ENUM(
    "CNIB_MATCH_AUTO",
    "DATE_NAISSANCE",
    "OTP_SMS",
    "VALIDATION_MANUELLE",
    name="methode_verification",
)
action_journal_consultation = postgresql.ENUM(
    "INSCRIPTION",
    "LOGIN",
    "VIEW_DASHBOARD",
    "ADD_CANDIDATURE",
    "DELETE_CANDIDATURE",
    "UPDATE_PREFERENCES",
    "DELETE_ACCOUNT",
    name="action_journal_consultation",
)


def upgrade() -> None:
    bind = op.get_bind()

    # Schéma dédié, distinct des tables tenants (docs/PROFIL_CANDIDAT_UNIFIE.md § 2/3) :
    # aucune administration ne peut lister ou interroger le profil candidat.
    op.execute("CREATE SCHEMA IF NOT EXISTS plateforme")

    statut_profil_candidat.create(bind, checkfirst=True)
    statut_verification_candidature.create(bind, checkfirst=True)
    methode_verification.create(bind, checkfirst=True)
    action_journal_consultation.create(bind, checkfirst=True)

    op.create_table(
        "profils_candidats",
        sa.Column("id", app.models.guid.GUID(), primary_key=True),
        sa.Column("numero_cnib", sa.String(length=255), nullable=False),
        sa.Column("numero_cnib_hash", sa.String(length=64), nullable=False),
        sa.Column("nom_complet", sa.String(length=200), nullable=False),
        sa.Column("date_naissance", sa.String(length=255), nullable=False),
        sa.Column("lieu_naissance", sa.String(length=200), nullable=True),
        sa.Column("sexe", sa.String(length=1), nullable=True),
        sa.Column("telephone", sa.String(length=255), nullable=False),
        sa.Column("telephone_hash", sa.String(length=64), nullable=False),
        sa.Column("telephone_verifie", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("operateur_telephone", sa.String(length=20), nullable=True),
        sa.Column("email", sa.String(length=200), nullable=True),
        sa.Column("email_verifie", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("mot_de_passe_hash", sa.String(length=255), nullable=True),
        sa.Column("derniere_connexion", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notifications_sms", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notifications_push", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notifications_email", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "statut",
            postgresql.ENUM(name="statut_profil_candidat", create_type=False),
            nullable=False,
            server_default="ACTIF",
        ),
        sa.Column("consentement_apdp_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consentement_apdp_version", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema="plateforme",
    )
    op.create_index(
        "ix_plateforme_profils_candidats_numero_cnib_hash",
        "profils_candidats",
        ["numero_cnib_hash"],
        unique=True,
        schema="plateforme",
    )
    op.create_index(
        "ix_plateforme_profils_candidats_telephone_hash",
        "profils_candidats",
        ["telephone_hash"],
        unique=True,
        schema="plateforme",
    )
    op.create_index(
        "ix_plateforme_profils_candidats_email",
        "profils_candidats",
        ["email"],
        schema="plateforme",
    )

    op.create_table(
        "candidatures",
        sa.Column("id", app.models.guid.GUID(), primary_key=True),
        sa.Column(
            "profil_candidat_id",
            app.models.guid.GUID(),
            sa.ForeignKey("plateforme.profils_candidats.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("administration_id", app.models.guid.GUID(), nullable=False),
        sa.Column("examen_id", app.models.guid.GUID(), nullable=False),
        sa.Column("numero_recepisse", sa.String(length=20), nullable=False),
        sa.Column(
            "statut_verification",
            postgresql.ENUM(name="statut_verification_candidature", create_type=False),
            nullable=False,
            server_default="EN_ATTENTE",
        ),
        sa.Column("date_verification", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "methode_verification",
            postgresql.ENUM(name="methode_verification", create_type=False),
            nullable=True,
        ),
        sa.Column("notifications_activees", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("derniere_notification_envoyee", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dernier_resultat_id", app.models.guid.GUID(), nullable=True),
        sa.Column("dernier_resultat_phase", sa.String(length=50), nullable=True),
        sa.Column("dernier_resultat_statut", sa.String(length=50), nullable=True),
        sa.Column("dernier_resultat_publie_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint(
            "administration_id", "numero_recepisse", name="uq_candidature_recepisse"
        ),
        schema="plateforme",
    )
    op.create_index(
        "ix_plateforme_candidatures_profil_candidat_id",
        "candidatures",
        ["profil_candidat_id"],
        schema="plateforme",
    )
    op.create_index(
        "ix_plateforme_candidatures_numero_recepisse",
        "candidatures",
        ["numero_recepisse"],
        schema="plateforme",
    )

    op.create_table(
        "journal_consultations_profil",
        sa.Column("id", app.models.guid.GUID(), primary_key=True),
        sa.Column(
            "profil_candidat_id",
            app.models.guid.GUID(),
            sa.ForeignKey("plateforme.profils_candidats.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "action",
            postgresql.ENUM(name="action_journal_consultation", create_type=False),
            nullable=False,
        ),
        sa.Column("ip", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column(
            "timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        schema="plateforme",
    )
    op.create_index(
        "ix_plateforme_journal_consultations_profil_profil_candidat_id",
        "journal_consultations_profil",
        ["profil_candidat_id"],
        schema="plateforme",
    )


def downgrade() -> None:
    op.drop_table("journal_consultations_profil", schema="plateforme")
    op.drop_table("candidatures", schema="plateforme")
    op.drop_table("profils_candidats", schema="plateforme")

    bind = op.get_bind()
    action_journal_consultation.drop(bind, checkfirst=True)
    methode_verification.drop(bind, checkfirst=True)
    statut_verification_candidature.drop(bind, checkfirst=True)
    statut_profil_candidat.drop(bind, checkfirst=True)

    op.execute("DROP SCHEMA IF EXISTS plateforme")
