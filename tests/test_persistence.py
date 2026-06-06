"""Tests for kernel.persistence: session, fault boundary, and migration smoke.

Covers round-trip persistence, commit boundary semantics, rollback + fault
recording, and (integration-marked) Alembic upgrade head + drift detection.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Mapped, mapped_column

from kernel.errors import CollectingFaultSink
from kernel.persistence import Base, Database, PersistenceSettings

# ── Test-only table (defined here, never in kernel or agents) ─────────────────


class _Widget(Base):
    """Minimal table used only by this test module."""

    __tablename__ = "test_widget"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column()


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_db(url: str = "sqlite:///:memory:") -> Database:
    """Return a fresh in-memory (or temp-file) Database with a collecting sink."""
    settings = PersistenceSettings(database_url=url)
    sink = CollectingFaultSink()
    db = Database(settings=settings, sink=sink)
    db.create_all()
    return db


# ── Round-trip ────────────────────────────────────────────────────────────────


def test_round_trip_insert_and_read() -> None:
    """Insert a row in one session; read it back in a fresh session."""
    db = _make_db()

    with db.session() as sess:
        sess.add(_Widget(name="sprocket"))

    with db.session() as sess:
        row = sess.get(_Widget, 1)
        assert row is not None
        assert row.name == "sprocket"


# ── Commit boundary ───────────────────────────────────────────────────────────


def test_commit_boundary_persists_on_clean_exit() -> None:
    """A clean session() block commits; the row is visible afterward."""
    db = _make_db()

    with db.session() as sess:
        sess.add(_Widget(name="gear"))

    with db.session() as sess:
        count = sess.query(_Widget).filter_by(name="gear").count()
    assert count == 1


# ── Rollback + fault ──────────────────────────────────────────────────────────


def _insert_then_raise(db: Database) -> None:
    """Insert a widget then raise inside a session (for rollback testing)."""
    with db.session() as sess:
        sess.add(_Widget(name="cog"))
        raise RuntimeError("boom")


def test_rollback_on_exception_and_fault_recorded() -> None:
    """Mid-write exception rolls back, records one fault, and re-raises."""
    db = _make_db()
    sink: CollectingFaultSink = db.sink  # type: ignore[assignment]

    with pytest.raises(RuntimeError, match="boom"):
        _insert_then_raise(db)

    # Table must be empty — the partial write was rolled back.
    with db.session() as sess:
        count = sess.query(_Widget).count()
    assert count == 0

    # Exactly one fault was recorded with the correct provenance.
    assert len(sink.faults) == 1
    fault = sink.faults[0]
    assert fault.source_module == "kernel.persistence"
    assert fault.error_type == "RuntimeError"


# ── Drop-all and default construction ────────────────────────────────────────


def test_drop_all_removes_tables() -> None:
    """drop_all() removes all tables so a subsequent query fails."""
    from sqlalchemy import inspect

    db = _make_db()
    db.drop_all()

    insp = inspect(db._engine)  # type: ignore[attr-defined]
    assert "test_widget" not in insp.get_table_names()


def test_database_default_construction() -> None:
    """Database() with no args uses PersistenceSettings defaults and collecting sink."""
    db = Database(settings=PersistenceSettings(database_url="sqlite:///:memory:"))
    assert isinstance(db.sink, CollectingFaultSink)


# ── Migration smoke (integration) ────────────────────────────────────────────


@pytest.mark.integration
def test_alembic_upgrade_head_and_no_drift(tmp_path: pytest.TempPathFactory) -> None:
    """Alembic upgrade head runs clean; autogenerate detects no drift.

    The drift comparison uses an *empty* MetaData — representing the production
    schema only — because _Widget is a test-only table that must not appear in
    migrations.  Sprint-02 defines zero production tables; head should leave the
    DB empty (aside from alembic_version) with no pending changes.
    """
    import os
    from pathlib import Path

    from alembic import command as alembic_cmd
    from alembic.autogenerate import compare_metadata
    from alembic.config import Config as AlembicConfig
    from alembic.runtime.migration import MigrationContext
    from sqlalchemy import MetaData, create_engine

    db_path = Path(str(tmp_path)) / "smoke.db"
    db_url = f"sqlite:///{db_path}"

    # Locate alembic.ini relative to this file's repo root.
    repo_root = Path(__file__).parent.parent
    ini_path = repo_root / "alembic.ini"

    alembic_cfg = AlembicConfig(str(ini_path))
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    # Run all migrations.
    alembic_cmd.upgrade(alembic_cfg, "head")

    # Compare against an empty production metadata (no production tables yet).
    # Test-only tables (e.g. _Widget) must not appear in migrations.
    production_metadata = MetaData()
    engine = create_engine(db_url)
    with engine.connect() as conn:
        migration_ctx = MigrationContext.configure(conn)
        diff = compare_metadata(migration_ctx, production_metadata)

    # No drift: the migrated schema matches the (empty) production metadata.
    assert diff == [], f"Unexpected schema drift detected: {diff}"

    # Ensure the DB file was actually created and clean up.
    assert db_path.exists()
    engine.dispose()
    os.unlink(db_path)
