"""phase3 resume ai

Revision ID: c821c44ae290
Revises: bf773dd3d573
Create Date: 2026-09-20 21:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c821c44ae290'
down_revision: Union[str, None] = 'bf773dd3d573'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- resumes: AI analysis state + deterministic total experience ---
    with op.batch_alter_table("resumes") as batch_op:
        batch_op.add_column(sa.Column("total_experience_years", sa.Float(), nullable=True))
        batch_op.add_column(
            sa.Column("analysis_status", sa.String(), nullable=False, server_default="parsed")
        )

    # --- education: allow unknown/omitted institutions, add degree years ---
    with op.batch_alter_table("education") as batch_op:
        batch_op.alter_column("institution", existing_type=sa.String(), nullable=True)
        batch_op.add_column(sa.Column("start_year", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("end_year", sa.Integer(), nullable=True))

    # --- experience: employment dates drive the deterministic duration calc ---
    with op.batch_alter_table("experience") as batch_op:
        batch_op.add_column(sa.Column("location", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("start_date", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("end_date", sa.String(), nullable=True))
        batch_op.add_column(
            sa.Column("currently_employed", sa.Boolean(), nullable=False, server_default="0")
        )

    # --- certifications: issue/expiry years (display only, no guessing) ---
    with op.batch_alter_table("certifications") as batch_op:
        batch_op.add_column(sa.Column("issue_year", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("expiry_year", sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("certifications") as batch_op:
        batch_op.drop_column("expiry_year")
        batch_op.drop_column("issue_year")

    with op.batch_alter_table("experience") as batch_op:
        batch_op.drop_column("currently_employed")
        batch_op.drop_column("end_date")
        batch_op.drop_column("start_date")
        batch_op.drop_column("location")

    with op.batch_alter_table("education") as batch_op:
        batch_op.drop_column("end_year")
        batch_op.drop_column("start_year")
        batch_op.alter_column("institution", existing_type=sa.String(), nullable=False)

    with op.batch_alter_table("resumes") as batch_op:
        batch_op.drop_column("analysis_status")
        batch_op.drop_column("total_experience_years")