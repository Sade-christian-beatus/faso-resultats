"""publication par phase : phase des ingestions, phases clôturées, action CLOSE_PHASE

Revision ID: 9c1d7e3a5f20
Revises: 5b8e2f41c9d7
Create Date: 2026-09-28 14:00:00.000000

Rend opérationnel le modèle de publication par phase des concours paramilitaires
(docs/CONTEXTE_METIER.md § 2.4, app/services/phases.py) :
- ingestions.phase : phase de la liste importée (les résultats la reprennent) ;
- examens.phases_cloturees : phases déclarées complètes par un admin ;
- action d'audit CLOSE_PHASE.
Les lignes existantes prennent RESULTAT_UNIQUE / [] : aucun import n'avait de phase.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9c1d7e3a5f20'
down_revision: Union[str, None] = '5b8e2f41c9d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'ingestions',
        sa.Column(
            'phase',
            postgresql.ENUM(name='phase_publication', create_type=False),
            nullable=False,
            server_default='RESULTAT_UNIQUE',
        ),
    )
    op.alter_column('ingestions', 'phase', server_default=None)

    op.add_column(
        'examens',
        sa.Column(
            'phases_cloturees',
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'),
            nullable=False,
            server_default='[]',
        ),
    )
    op.alter_column('examens', 'phases_cloturees', server_default=None)

    op.execute("ALTER TYPE action_audit_log ADD VALUE IF NOT EXISTS 'CLOSE_PHASE'")


def downgrade() -> None:
    op.drop_column('examens', 'phases_cloturees')
    op.drop_column('ingestions', 'phase')
    # Enum value CLOSE_PHASE left in place: Postgres cannot drop an enum value without
    # recreating the type (same no-op as the other enum additions in this project).
