"""Verifies the Alembic migration chain produces the full application schema."""

import tempfile
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

BACKEND_DIR = Path(__file__).resolve().parents[1]

EXPECTED_TABLES = {
    "users",
    "resumes",
    "skills",
    "education",
    "experience",
    "certifications",
    "jobs",
    "saved_jobs",
    "applications",
    "user_preferences",
}


def _alembic_config(db_url: str) -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def test_alembic_upgrade_head_creates_all_tables():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "migration_test.db"
        url = f"sqlite:///{db_path.as_posix()}"

        command.upgrade(_alembic_config(url), "head")

        engine = create_engine(url)
        tables = set(inspect(engine).get_table_names())
        assert EXPECTED_TABLES.issubset(tables)
        engine.dispose()


def test_alembic_migration_adds_application_uniqueness():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "migration_test.db"
        url = f"sqlite:///{db_path.as_posix()}"

        command.upgrade(_alembic_config(url), "head")

        engine = create_engine(url)
        inspector = inspect(engine)
        constraints = {
            constraint["name"]
            for constraint in inspector.get_unique_constraints("applications")
        }
        assert "uq_applications_user_job" in constraints
        engine.dispose()


def test_alembic_migration_duplicate_application_row_rejected():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "migration_test.db"
        url = f"sqlite:///{db_path.as_posix()}"

        command.upgrade(_alembic_config(url), "head")

        engine = create_engine(url)
        with engine.begin() as connection:
            connection.execute(
                text("INSERT INTO users (name, email, hashed_password) "
                     "VALUES ('U', 'u@example.com', 'h')")
            )
            connection.execute(
                text("INSERT INTO jobs (title, company) VALUES ('J', 'C')")
            )
            connection.execute(
                text("INSERT INTO applications (user_id, job_id, status) VALUES (1, 1, 'applied')")
            )
            try:
                connection.execute(
                    text("INSERT INTO applications (user_id, job_id, status) VALUES (1, 1, 'applied')")
                )
            except Exception as exc:  # noqa: BLE001 - either IntegrityError or DB-level failure
                assert "UNIQUE constraint failed" in str(exc)
            else:
                raise AssertionError("Duplicate (user_id, job_id) application was allowed")
        engine.dispose()


def test_alembic_migration_idempotent_on_repeat_upgrade():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "migration_test.db"
        url = f"sqlite:///{db_path.as_posix()}"

        config = _alembic_config(url)
        command.upgrade(config, "head")
        command.upgrade(config, "head")  # no-op; must not raise

        engine = create_engine(url)
        tables = set(inspect(engine).get_table_names())
        assert EXPECTED_TABLES.issubset(tables)
        engine.dispose()