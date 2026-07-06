"""pivot multi-tenant : administrations, utilisateurs, administration_id partout

Revision ID: f4a7c8e21b6d
Revises: d9b3f6a12c84
Create Date: 2026-07-05 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

import app.models.guid

# revision identifiers, used by Alembic.
revision: str = 'f4a7c8e21b6d'
down_revision: Union[str, None] = 'd9b3f6a12c84'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Administration placeholder pour les données déjà en base avant le pivot multi-tenant
# (dev/pilote uniquement — jamais de données de production réelles à ce stade). Le seed
# multi-tenant crée séparément les vraies administrations (OCECOS, Office BAC, AGRE) ;
# ce placeholder existe uniquement pour satisfaire la contrainte NOT NULL sur les lignes
# déjà existantes.
_ADMINISTRATION_HERITEE_ID = "00000000-0000-0000-0000-000000000001"

plan_abonnement = postgresql.ENUM("STARTER", "STANDARD", "PREMIUM", name="plan_abonnement")
statut_administration = postgresql.ENUM(
    "ACTIF", "SUSPENDU", "PILOTE", "RESILIE", name="statut_administration"
)
role_utilisateur = postgresql.ENUM(
    "SUPER_ADMIN",
    "SUPPORT",
    "ADMIN_ADMINISTRATION",
    "OPERATEUR_INGESTION",
    "OPERATEUR_PUBLICATION",
    "LECTEUR",
    name="role_utilisateur",
)


def upgrade() -> None:
    bind = op.get_bind()

    plan_abonnement.create(bind, checkfirst=True)
    statut_administration.create(bind, checkfirst=True)
    role_utilisateur.create(bind, checkfirst=True)

    op.create_table(
        "administrations",
        sa.Column("id", app.models.guid.GUID(), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("nom_officiel", sa.String(length=255), nullable=False),
        sa.Column("sigle", sa.String(length=50), nullable=False),
        sa.Column("ministere_tutelle", sa.String(length=255), nullable=False),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column("couleur_primaire", sa.String(length=20), nullable=True),
        sa.Column("domaine_personnalise", sa.String(length=255), nullable=True),
        sa.Column("contact_referent_nom", sa.String(length=255), nullable=False),
        sa.Column("contact_referent_email", sa.String(length=255), nullable=False),
        sa.Column("contact_referent_telephone", sa.String(length=20), nullable=False),
        sa.Column("date_signature_convention", sa.Date(), nullable=True),
        sa.Column("convention_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "plan_abonnement",
            postgresql.ENUM(name="plan_abonnement", create_type=False),
            nullable=False,
            server_default="STARTER",
        ),
        sa.Column("quota_sms_mensuel", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quota_examens_annuel", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "statut",
            postgresql.ENUM(name="statut_administration", create_type=False),
            nullable=False,
            server_default="PILOTE",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_administrations_code", "administrations", ["code"], unique=True)

    # Placeholder pour les lignes déjà existantes (voir commentaire en tête de fichier).
    op.execute(
        f"""
        INSERT INTO administrations (
            id, code, nom_officiel, sigle, ministere_tutelle,
            contact_referent_nom, contact_referent_email, contact_referent_telephone,
            convention_active, plan_abonnement, quota_sms_mensuel, quota_examens_annuel, statut
        ) VALUES (
            '{_ADMINISTRATION_HERITEE_ID}', 'heritee', 'Administration héritée (pré-multi-tenant)',
            'LEGACY', 'À déterminer', 'À déterminer', 'contact@exemple.bf', '+22600000000',
            false, 'STARTER', 0, 0, 'PILOTE'
        )
        """
    )

    # --- Renommage admins -> utilisateurs + nouveaux champs ---
    op.rename_table("admins", "utilisateurs")
    op.execute("ALTER INDEX ix_admins_email RENAME TO ix_utilisateurs_email")
    op.add_column(
        "utilisateurs",
        sa.Column(
            "administration_id",
            app.models.guid.GUID(),
            sa.ForeignKey("administrations.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.add_column("utilisateurs", sa.Column("telephone", sa.String(length=20), nullable=True))
    op.add_column(
        "utilisateurs",
        sa.Column(
            "role",
            postgresql.ENUM(name="role_utilisateur", create_type=False),
            nullable=False,
            server_default="SUPER_ADMIN",
        ),
    )
    op.alter_column("utilisateurs", "role", server_default=None)

    # --- administration_id sur les tables métier existantes ---
    for table in ("examens", "ingestions", "resultats", "notifications_preinscription"):
        op.add_column(
            table,
            sa.Column(
                "administration_id",
                app.models.guid.GUID(),
                sa.ForeignKey("administrations.id", ondelete="CASCADE"),
                nullable=True,
            ),
        )
        op.execute(
            f"UPDATE {table} SET administration_id = '{_ADMINISTRATION_HERITEE_ID}' "
            "WHERE administration_id IS NULL"
        )
        op.alter_column(table, "administration_id", nullable=False)

    op.create_index("ix_examens_administration_statut", "examens", ["administration_id", "statut"])
    op.create_index(
        "ix_ingestions_administration_created", "ingestions", ["administration_id", "created_at"]
    )
    op.create_index("ix_resultats_administration", "resultats", ["administration_id"])


def downgrade() -> None:
    op.drop_index("ix_resultats_administration", table_name="resultats")
    op.drop_index("ix_ingestions_administration_created", table_name="ingestions")
    op.drop_index("ix_examens_administration_statut", table_name="examens")

    for table in ("notifications_preinscription", "resultats", "ingestions", "examens"):
        op.drop_column(table, "administration_id")

    op.drop_column("utilisateurs", "role")
    op.drop_column("utilisateurs", "telephone")
    op.drop_column("utilisateurs", "administration_id")
    op.execute("ALTER INDEX ix_utilisateurs_email RENAME TO ix_admins_email")
    op.rename_table("utilisateurs", "admins")

    op.drop_index("ix_administrations_code", table_name="administrations")
    op.drop_table("administrations")

    bind = op.get_bind()
    role_utilisateur.drop(bind, checkfirst=True)
    statut_administration.drop(bind, checkfirst=True)
    plan_abonnement.drop(bind, checkfirst=True)
