"""Command-line utilities for CareerOS.

Usage (from the ``backend`` directory, with the venv active):

    python -m app.cli seed-jobs

Seeding pulls jobs from an ingestion provider (the bundled demo provider by
default) and upserts them into the database configured by ``DATABASE_URL``.
It is idempotent: running it twice never duplicates jobs.
"""

import argparse
import sys

from app.core.database import SessionLocal
from app.services.job_ingestion import ingest_jobs
from app.services.providers import get_active_provider


def _run_seed_jobs() -> int:
    provider = get_active_provider()
    print(f"Ingesting jobs from provider: {provider.name}")

    db = SessionLocal()
    try:
        stats = ingest_jobs(db, provider)
    finally:
        db.close()

    print(
        f"Seed complete. fetched={stats.fetched} inserted={stats.inserted} "
        f"updated={stats.updated} skipped={stats.skipped} failed={stats.failed}"
    )
    for error in stats.errors:
        print(f"  - failed record: {error}", file=sys.stderr)
    return 0 if stats.failed == 0 else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="careeros", description="CareerOS admin commands")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "seed-jobs",
        help="Upsert demo jobs from the default provider into the database.",
    )

    args = parser.parse_args(argv)

    if args.command == "seed-jobs":
        return _run_seed_jobs()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())