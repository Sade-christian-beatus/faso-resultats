"""export donnees candidat : nouvelle valeur EXPORT_DONNEES sur action_journal_consultation

Revision ID: b3d4e5f6a7c8
Revises: f0525fc88905
Create Date: 2026-07-07 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b3d4e5f6a7c8'
down_revision: Union[str, None] = 'f0525fc88905'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE action_journal_consultation ADD VALUE IF NOT EXISTS 'EXPORT_DONNEES'")


def downgrade() -> None:
    # Postgres ne permet pas de retirer une valeur d'un enum sans recréer le type
    # entier ; comme les autres migrations de ce projet ajoutant des valeurs d'enum
    # (voir d9b3f6a12c84), le downgrade est un no-op assumé.
    pass
