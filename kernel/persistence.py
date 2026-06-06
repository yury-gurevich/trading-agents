"""Relational persistence adapter: shared declarative base, settings, and session.

Agent: kernel
Role: provide a domain-pure SQLAlchemy 2.0 session factory with fault-wrapped
      transactions, a shared DeclarativeBase for all agent table definitions,
      and the infrastructure settings that wire them to a database URL.
External I/O: relational database (SQLite by default; Postgres in production).
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from kernel.config import AgentSettings, tunable
from kernel.errors import CollectingFaultSink, FaultSink, fault_boundary

if TYPE_CHECKING:
    from collections.abc import Iterator


# ── Shared declarative base ───────────────────────────────────────────────────


class Base(DeclarativeBase):
    """Shared SQLAlchemy declarative base.

    Every agent's ``store.py`` subclasses this to define its own tables.
    No tables are defined here — the kernel is domain-free.
    """


# ── Engine tunables ───────────────────────────────────────────────────────────

_POOL_PRE_PING: bool = tunable(
    True,
    why=(
        "Verify the connection is alive before using it from the pool. "
        "Prevents stale-connection errors after a DB restart, at the cost "
        "of one lightweight SELECT per checkout — acceptable for our load."
    ),
)


# ── Settings ──────────────────────────────────────────────────────────────────


class PersistenceSettings(AgentSettings):
    """Infrastructure settings for the relational adapter.

    Reads ``DATABASE_URL`` from the environment (or ``.env``).  The default is
    a local SQLite file so the gate never needs an external service.

    Note: there is intentionally no ``env_prefix`` — ``DATABASE_URL`` is a
    plain infrastructure variable shared across the stack, not agent-specific.
    """

    database_url: str = tunable(
        "sqlite:///./trading.db",
        why=(
            "SQLite is the zero-infrastructure default so CI and local runs "
            "need no external service. Override with a Postgres URL for "
            "production (e.g. postgresql+psycopg://user:pw@host/db)."
        ),
    )


# ── Database ──────────────────────────────────────────────────────────────────


class Database:
    """Wraps an SQLAlchemy engine and sessionmaker with fault-redirected sessions.

    Args:
        settings: persistence settings (URL + tunables).  Defaults to
                  ``PersistenceSettings()``, which reads from the environment.
        sink:     destination for faults.  Defaults to a
                  ``CollectingFaultSink`` so tests and local runs have
                  somewhere to capture failures without wiring the supervisor.
    """

    def __init__(
        self,
        settings: PersistenceSettings | None = None,
        sink: FaultSink | None = None,
    ) -> None:
        """Create engine + sessionmaker from settings."""
        self._settings = settings if settings is not None else PersistenceSettings()
        self.sink: FaultSink = sink if sink is not None else CollectingFaultSink()

        self._engine = create_engine(
            self._settings.database_url,
            pool_pre_ping=_POOL_PRE_PING,
        )
        self._factory = sessionmaker(bind=self._engine, expire_on_commit=False)

    # ── Session context manager ───────────────────────────────────────────────

    @contextmanager
    def session(self) -> Iterator[Session]:
        """Yield a transactional session; commit on success, rollback on error.

        On any exception the transaction is rolled back, an ``AgentFault`` is
        recorded via ``fault_boundary`` with ``module="kernel.persistence"``,
        and the exception is re-raised so the caller sees the failure.
        """
        sess: Session = self._factory()
        try:
            with fault_boundary(
                self.sink,
                agent="kernel",
                module="kernel.persistence",
                reraise=True,
            ):
                yield sess
                sess.commit()
        except Exception:
            sess.rollback()
            raise
        finally:
            sess.close()

    # ── Schema helpers ────────────────────────────────────────────────────────

    def create_all(self) -> None:
        """Create all tables registered on ``Base``.

        Convenience for tests and local bootstrap.  Production schemas are
        owned by Alembic migrations; this helper must never run in production.
        """
        Base.metadata.create_all(self._engine)

    def drop_all(self) -> None:
        """Drop all tables registered on ``Base``.

        Convenience for test teardown and local resets only.
        """
        Base.metadata.drop_all(self._engine)
