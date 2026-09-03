"""rendre unique ix_resultats_examen_pv_jury_phase

Revision ID: 8f2cc3339226
Revises: b3d4e5f6a7c8
Create Date: 2026-08-17 00:00:00.000000

Audit du 2026-08-17 : l'index sur (examen_id, numero_pv, jury, phase) n'a jamais été
unique alors que ce quadruplet doit identifier un résultat de façon univoque (le
`phase` distingue les lignes légitimement répétées d'un concours à publication
multi-phases). Sans contrainte, une double ingestion pouvait créer deux `Resultat`
contradictoires pour le même candidat — amplifie le risque de faux positif/négatif
lors du rapprochement candidat (docs `verification_service.py`).

Si cette migration échoue avec une violation d'unicité, des doublons existent déjà en
base : les identifier et les nettoyer manuellement avant de relancer `alembic upgrade`.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '8f2cc3339226'
down_revision: Union[str, None] = 'b3d4e5f6a7c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_resultats_examen_pv_jury_phase", table_name="resultats")
    op.create_index(
        "ix_resultats_examen_pv_jury_phase",
        "resultats",
        ["examen_id", "numero_pv", "jury", "phase"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_resultats_examen_pv_jury_phase", table_name="resultats")
    op.create_index(
        "ix_resultats_examen_pv_jury_phase",
        "resultats",
        ["examen_id", "numero_pv", "jury", "phase"],
    )
