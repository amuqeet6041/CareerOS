"""Shared in-memory SQLite test database.

Both test_auth.py and test_resume.py used to create their own engine and
overwrite ``app.dependency_overrides[get_db]`` at import time, so whichever
file was imported last silently replaced the other's database. Centralizing
the engine, session maker, and the single dependency override here keeps the
whole suite against one consistent test database and lets each test file seed
shared tables (e.g. jobs) predictably.
"""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  (register every table on Base.metadata)

from app.core.database import Base, get_db

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    """Enforce FK constraints like PostgreSQL does, so test data stays valid."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# One dependency override for the whole suite.
from app.main import app  # noqa: E402

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)