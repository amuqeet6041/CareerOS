"""phase1 job system

Revision ID: bf773dd3d573
Revises: 9032a41514cb
Create Date: 2026-09-20 20:44:17.353082

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bf773dd3d573'
down_revision: Union[str, None] = '9032a41514cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- jobs: phase 1 columns, renames, and the (source, external_id) key ---
    with op.batch_alter_table("jobs") as batch_op:
        batch_op.add_column(sa.Column("city", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("country", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("posted_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("expires_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("created_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("updated_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("is_active", sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column("minimum_experience_years", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("maximum_experience_years", sa.Float(), nullable=True))
        # Rename to the phase 1 canonical names while preserving any data.
        batch_op.alter_column("job_type", new_column_name="employment_type", existing_type=sa.String())
        batch_op.alter_column("apply_url", new_column_name="application_url", existing_type=sa.String())
        # Deduplication key for ingestion/re-ingestion.
        batch_op.create_unique_constraint("uq_jobs_source_external_id", ["source", "external_id"])

    # Existing rows predate the flag; treat them as active unless an expires_at
    # in the past says otherwise (queries also read expires_at directly).
    op.execute("UPDATE jobs SET is_active = 1 WHERE is_active IS NULL")

    # Query indexes (filters + default newest-first sorting).
    op.create_index("ix_jobs_is_active", "jobs", ["is_active"])
    op.create_index("ix_jobs_posted_at", "jobs", ["posted_at"])
    op.create_index("ix_jobs_city", "jobs", ["city"])
    op.create_index("ix_jobs_work_mode", "jobs", ["work_mode"])
    op.create_index("ix_jobs_employment_type", "jobs", ["employment_type"])
    op.create_index("ix_jobs_source", "jobs", ["source"])

    # --- job_skills ---
    op.create_table(
        "job_skills",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "job_id",
            sa.Integer(),
            sa.ForeignKey("jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("skill_name", sa.String(), nullable=False),
        sa.Column("normalized_name", sa.String(), nullable=False),
        sa.UniqueConstraint(
            "job_id", "normalized_name", name="uq_job_skills_job_skill"
        ),
    )
    op.create_index("ix_job_skills_job_id", "job_skills", ["job_id"])
    op.create_index("ix_job_skills_normalized_name", "job_skills", ["normalized_name"])

    # --- job_qualifications ---
    op.create_table(
        "job_qualifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "job_id",
            sa.Integer(),
            sa.ForeignKey("jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("qualification", sa.String(), nullable=False),
        sa.Column("normalized_qualification", sa.String(), nullable=False),
        sa.UniqueConstraint(
            "job_id",
            "normalized_qualification",
            name="uq_job_qualifications_job_qualification",
        ),
    )
    op.create_index(
        "ix_job_qualifications_job_id", "job_qualifications", ["job_id"]
    )
    op.create_index(
        "ix_job_qualifications_normalized_qualification",
        "job_qualifications",
        ["normalized_qualification"],
    )


def downgrade() -> None:
    op.drop_index("ix_job_qualifications_normalized_qualification", table_name="job_qualifications")
    op.drop_index("ix_job_qualifications_job_id", table_name="job_qualifications")
    op.drop_table("job_qualifications")

    op.drop_index("ix_job_skills_normalized_name", table_name="job_skills")
    op.drop_index("ix_job_skills_job_id", table_name="job_skills")
    op.drop_table("job_skills")

    op.drop_index("ix_jobs_source", table_name="jobs")
    op.drop_index("ix_jobs_employment_type", table_name="jobs")
    op.drop_index("ix_jobs_work_mode", table_name="jobs")
    op.drop_index("ix_jobs_city", table_name="jobs")
    op.drop_index("ix_jobs_posted_at", table_name="jobs")
    op.drop_index("ix_jobs_is_active", table_name="jobs")

    with op.batch_alter_table("jobs") as batch_op:
        batch_op.drop_constraint("uq_jobs_source_external_id", type_="unique")
        batch_op.alter_column("employment_type", new_column_name="job_type", existing_type=sa.String())
        batch_op.alter_column("application_url", new_column_name="apply_url", existing_type=sa.String())
        batch_op.drop_column("maximum_experience_years")
        batch_op.drop_column("minimum_experience_years")
        batch_op.drop_column("is_active")
        batch_op.drop_column("updated_at")
        batch_op.drop_column("created_at")
        batch_op.drop_column("expires_at")
        batch_op.drop_column("posted_at")
        batch_op.drop_column("country")
        batch_op.drop_column("city")