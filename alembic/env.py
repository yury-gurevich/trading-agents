"""Alembic migration environment.

Wires the migration runner to kernel.persistence.Base.metadata so Alembic
can autogenerate and apply schema changes.  The database URL is always read
from PersistenceSettings (honouring DATABASE_URL from the environment or
.env) — it is never hardcoded here.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from kernel.persistence import Base, PersistenceSettings

# ── Alembic Config object ─────────────────────────────────────────────────────
config = context.config

# Interpret the config file for Python logging when Alembic runs from CLI.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Inject the URL from PersistenceSettings so it is never hardcoded.
_settings = PersistenceSettings()
config.set_main_option("sqlalchemy.url", _settings.database_url)

# The metadata Alembic autogenerates from.
target_metadata = Base.metadata


# ── Offline mode (generate SQL without connecting) ────────────────────────────


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (renders SQL to stdout)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online mode (apply migrations against a live connection) ──────────────────


def run_migrations_online() -> None:
    """Run migrations with a live DB connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
