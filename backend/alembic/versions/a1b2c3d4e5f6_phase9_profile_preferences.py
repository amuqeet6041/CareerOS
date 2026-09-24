"""phase9_profile_preferences

Adds:
  * user_profiles table (1:1 with users)
  * New columns on user_preferences (Phase 9 preference fields)

Uses batch_alter_table for all ALTER TABLE operations so this migration runs
correctly on both SQLite (development / tests) and PostgreSQL (production).

Revision ID: a1b2c3d4e5f6
Revises: 313a54989d0d
Create Date: 2026-09-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '313a54989d0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(name: str) -> bool:
    return name in _inspector().get_table_names()


def _has_column(table: str, name: str) -> bool:
    return any(c["name"] == name for c in _inspector().get_columns(table))


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # 1. Create user_profiles table (skip if already exists — idempotent)
    # -----------------------------------------------------------------------
    if not _has_table("user_profiles"):
        op.create_table(
            "user_profiles",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("headline", sa.String(), nullable=True),
            sa.Column("bio", sa.Text(), nullable=True),
            sa.Column("location", sa.String(), nullable=True),
            sa.Column("country", sa.String(), nullable=True),
            sa.Column("profile_source", sa.String(), nullable=True, server_default="manual"),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", name="uq_user_profiles_user_id"),
        )
        op.create_index("ix_user_profiles_id", "user_profiles", ["id"])

    # -----------------------------------------------------------------------
    # 2. Add new Phase 9 columns to user_preferences
    #    (each guarded so re-running is safe)
    # -----------------------------------------------------------------------
    new_pref_columns = [
        ("preferred_roles", sa.String(), None),
        ("preferred_skills", sa.String(), None),
        ("preferred_work_modes", sa.String(), None),
        ("preferred_employment_types", sa.String(), None),
        ("preferred_industries", sa.String(), None),
        ("salary_min", sa.String(), None),
        ("salary_max", sa.String(), None),
        ("currency", sa.String(), "USD"),
        ("career_level", sa.String(), None),
        ("open_to_relocate", sa.String(), None),
    ]

    columns_to_add = [
        (col_name, col_type, default)
        for col_name, col_type, default in new_pref_columns
        if not _has_column("user_preferences", col_name)
    ]

    if columns_to_add:
        with op.batch_alter_table("user_preferences") as batch_op:
            for col_name, col_type, default in columns_to_add:
                batch_op.add_column(
                    sa.Column(col_name, col_type, nullable=True, server_default=default)
                )


def downgrade() -> None:
    # Remove Phase 9 preference columns
    pref_columns = [
        "preferred_roles",
        "preferred_skills",
        "preferred_work_modes",
        "preferred_employment_types",
        "preferred_industries",
        "salary_min",
        "salary_max",
        "currency",
        "career_level",
        "open_to_relocate",
    ]
    cols_to_drop = [c for c in pref_columns if _has_column("user_preferences", c)]
    if cols_to_drop:
        with op.batch_alter_table("user_preferences") as batch_op:
            for col_name in cols_to_drop:
                batch_op.drop_column(col_name)

    # Drop user_profiles table
    if _has_table("user_profiles"):
        op.drop_index("ix_user_profiles_id", table_name="user_profiles")
        op.drop_table("user_profiles")
