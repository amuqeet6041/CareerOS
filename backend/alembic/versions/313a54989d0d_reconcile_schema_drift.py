"""reconcile schema drift

Reconciles the actual schema with the schema that the migration chain
already declares, without changing the authoritative final shape:

* databases created through ``alembic upgrade head`` already match this
  migration's target, so every operation below is guarded and becomes a
  no-op there (safe for fresh installs and CI);
* databases whose tables came from an early ``create_all`` (e.g. the local
  development DB) get the missing unique constraints / NOT NULL columns,
  drop the legacy ``jobs.job_type`` / ``jobs.apply_url`` columns that
  phase1 renamed, and gain the phase-1 query indexes now declared by the
  ``Job`` model.

No rows are deleted: legacy column data is copied to the new column names
before the old columns are dropped, and the unique constraints are added
without touching existing rows.

Revision ID: 313a54989d0d
Revises: c821c44ae290
Create Date: 2026-09-21 21:03:40.889427

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '313a54989d0d'
down_revision: Union[str, None] = 'c821c44ae290'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_index(table: str, name: str) -> bool:
    return any(i["name"] == name for i in _inspector().get_indexes(table))


def _has_column(table: str, name: str) -> bool:
    return any(c["name"] == name for c in _inspector().get_columns(table))


def _has_unique(table: str, name: str) -> bool:
    return any(u["name"] == name for u in _inspector().get_unique_constraints(table))


def _column_nullable(table: str, name: str) -> bool:
    for c in _inspector().get_columns(table):
        if c["name"] == name:
            return c["nullable"]
    return None


def upgrade() -> None:
    # --- 1. PK id indexes the phase-1 child tables were created without ---
    if not _has_index("job_skills", "ix_job_skills_id"):
        op.create_index("ix_job_skills_id", "job_skills", ["id"])
    if not _has_index("job_qualifications", "ix_job_qualifications_id"):
        op.create_index("ix_job_qualifications_id", "job_qualifications", ["id"])

    # --- 2. jobs: drop the legacy columns that phase1 renamed,
    #         copying any data into the new names first ---
    if _has_column("jobs", "job_type") or _has_column("jobs", "apply_url"):
        op.execute(
            "UPDATE jobs SET employment_type = job_type "
            "WHERE employment_type IS NULL AND job_type IS NOT NULL"
        )
        op.execute(
            "UPDATE jobs SET application_url = apply_url "
            "WHERE application_url IS NULL AND apply_url IS NOT NULL"
        )
        with op.batch_alter_table("jobs") as batch_op:
            if _has_column("jobs", "job_type"):
                batch_op.drop_column("job_type")
            if _has_column("jobs", "apply_url"):
                batch_op.drop_column("apply_url")

    # --- 3. jobs: the (source, external_id) dedup key ---
    if not _has_unique("jobs", "uq_jobs_source_external_id"):
        with op.batch_alter_table("jobs") as batch_op:
            batch_op.create_unique_constraint(
                "uq_jobs_source_external_id", ["source", "external_id"]
            )

    # --- 4. jobs: phase-1 query indexes now declared by the model ---
    for index_name, column_name in (
        ("ix_jobs_is_active", "is_active"),
        ("ix_jobs_posted_at", "posted_at"),
        ("ix_jobs_city", "city"),
        ("ix_jobs_work_mode", "work_mode"),
        ("ix_jobs_employment_type", "employment_type"),
        ("ix_jobs_source", "source"),
    ):
        if not _has_index("jobs", index_name):
            op.create_index(index_name, "jobs", [column_name])

    # --- 5. applications / saved_jobs: unique (user_id, job_id) ---
    if not _has_unique("applications", "uq_applications_user_job"):
        with op.batch_alter_table("applications") as batch_op:
            batch_op.create_unique_constraint("uq_applications_user_job", ["user_id", "job_id"])
    if not _has_unique("saved_jobs", "uq_saved_jobs_user_job"):
        with op.batch_alter_table("saved_jobs") as batch_op:
            batch_op.create_unique_constraint("uq_saved_jobs_user_job", ["user_id", "job_id"])

    # --- 6. nullability the phase-3 migration already declares ---
    if _column_nullable("education", "institution") is False:
        with op.batch_alter_table("education") as batch_op:
            batch_op.alter_column("institution", existing_type=sa.String(), nullable=True)

    if _column_nullable("experience", "currently_employed") is True:
        with op.batch_alter_table("experience") as batch_op:
            batch_op.alter_column(
                "currently_employed",
                existing_type=sa.Boolean(),
                nullable=False,
                server_default="0",
            )

    if _column_nullable("resumes", "analysis_status") is True:
        with op.batch_alter_table("resumes") as batch_op:
            batch_op.alter_column(
                "analysis_status",
                existing_type=sa.String(),
                nullable=False,
                server_default="parsed",
            )


def downgrade() -> None:
    """Reverse the only operations this migration adds on a compliant database.

    The constraint / NOT NULL / column-drop fixes bring a legacy database in
    line with the schema the existing chain already declares, so reversing
    them here would move the database *away* from the chain's own target. They
    are therefore intentionally left intact (matching what c821c44ae290 has
    always claimed).
    """
    if _has_index("job_skills", "ix_job_skills_id"):
        op.drop_index("ix_job_skills_id", table_name="job_skills")
    if _has_index("job_qualifications", "ix_job_qualifications_id"):
        op.drop_index("ix_job_qualifications_id", table_name="job_qualifications")