"""PostgreSQL role provisioner SQL tests.

Agent: tooling
Role: prove per-agent role SQL generation without touching a live database.
External I/O: none.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from scripts import pg_role_plan as roles


def test_role_catalogue_contains_15_permanent_roles() -> None:
    assert roles.agent_role_names() == (
        "ta_scanner",
        "ta_analyst",
        "ta_portfolio_manager",
        "ta_execution",
        "ta_monitor",
        "ta_reporter",
        "ta_forecaster",
        "ta_operator",
        "ta_supervisor",
        "ta_curator",
        "ta_researcher",
        "ta_provider",
        "ta_master",
        "ta_dispatcher",
        "ta_ops",
    )


def test_fresh_role_plan_creates_login_and_restores_grants() -> None:
    plan = roles.role_plan("ta_scanner", "pw", exists=False, rotate=False)

    assert plan[0] == roles.SqlStatement(
        "CREATE ROLE \"ta_scanner\" LOGIN PASSWORD 'pw'"
    )
    assert roles.SqlStatement('GRANT USAGE ON SCHEMA public TO "ta_scanner"') in plan
    assert (
        roles.SqlStatement(
            'GRANT SELECT, INSERT, UPDATE ON TABLE public."nodes", public."edges" '
            'TO "ta_scanner"'
        )
        in plan
    )
    assert (
        roles.SqlStatement(
            "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE "
            'ON TABLES TO "ta_scanner"'
        )
        in plan
    )


def test_existing_role_without_rotation_only_restores_grants() -> None:
    plan = roles.role_plan("ta_analyst", "pw", exists=True, rotate=False)

    assert len(plan) == 5
    assert all("PASSWORD" not in statement.sql for statement in plan)
    assert all(statement.params == () for statement in plan)


def test_password_literals_are_escaped_in_generated_sql() -> None:
    plan = roles.role_plan("ta_monitor", "p'word", exists=False, rotate=False)

    assert plan[0] == roles.SqlStatement(
        "CREATE ROLE \"ta_monitor\" LOGIN PASSWORD 'p''word'"
    )


def test_rotate_existing_role_reissues_password_before_grants() -> None:
    plan = roles.role_plan("ta_provider", "pw", exists=True, rotate=True)

    assert plan[0] == roles.SqlStatement("ALTER ROLE \"ta_provider\" PASSWORD 'pw'")
    assert (
        roles.SqlStatement(
            "GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public "
            'TO "ta_provider"'
        )
        in plan
    )


def test_agent_argument_normalization_accepts_role_and_app_shapes() -> None:
    assert roles.normalize_agent("portfolio-manager") == "portfolio_manager"
    assert roles.normalize_agent("ta_portfolio_manager") == "portfolio_manager"
    assert roles.db_role("portfolio-manager") == "ta_portfolio_manager"
    assert roles.key_vault_secret_name("portfolio_manager") == (
        "postgres-dsn-portfolio-manager"
    )

    with pytest.raises(ValueError, match="unknown Postgres role target"):
        roles.normalize_agent("all")


def test_role_dsn_replaces_only_url_userinfo() -> None:
    admin_dsn = "".join(
        (
            "postgresql://admin:",
            "old@example.test:5432/neondb?sslmode=require",
        )
    )
    dsn = roles.build_role_dsn(
        admin_dsn,
        "ta_scanner",
        "rotated_pw",
    )
    expected_dsn = "".join(
        (
            "postgresql://ta_scanner:",
            "rotated_pw@example.test:5432/neondb?sslmode=require",
        )
    )

    assert dsn == expected_dsn


def test_provisioner_script_direct_execution_imports_helper() -> None:
    env = os.environ.copy()
    env.pop("POSTGRES_DSN", None)

    completed = subprocess.run(
        [sys.executable, "scripts/pg_provision_roles.py", "--database-only"],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "POSTGRES_DSN is required" in completed.stderr
    assert "ModuleNotFoundError" not in completed.stderr
