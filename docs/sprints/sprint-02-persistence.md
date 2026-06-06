# Sprint 02 — Relational persistence adapter + migration harness

**Status:** active · **Branch:** `sprint-02-persistence` · **Build phase:** P1 (second slice)

## Goal

Give the kernel a **domain-pure relational persistence adapter** and a
**schema-migration harness**, proven against a local SQLite database with **no
external infrastructure**. This is the substrate every agent's future `store.py`
stands on: a shared declarative `Base`, a fault-wrapped session, and an Alembic
pipeline that CI can run. No agent tables are defined this sprint.

## Why (context)

- Sprint 01 shipped the runtime spine (in-process bus + `AgentBase`). The next P1
  layer agents need is somewhere to *own data*. P2 (`provider → scanner → analyst`)
  gives each agent a `store.py`; that work is blocked until this substrate exists.
- `docs/architecture.md` §"Data: two stores, two jobs": the relational store is
  ACID/append-only, **each agent owns its own tables — no shared schema**, and
  "schema migrations for the relational store are managed with a migration tool and
  validated in CI."
- The stack is already declared: `sqlalchemy>=2.0` + `alembic>=1.13` live in the
  `runtime` optional-dependency extra; `DATABASE_URL` is already stubbed (commented)
  in `.env.example` under "Runtime infrastructure (P1+)".
- Read first: `docs/architecture.md` (Data + Configuration sections),
  `kernel/config.py` (`AgentSettings`, `tunable`), `kernel/errors.py`
  (`fault_boundary`, `FaultSink`, `CollectingFaultSink`), and `kernel/__init__.py`
  (the docstring already reserves "persistence … adapters join later").

## Key design constraints (do not break)

- **Kernel stays domain-pure.** `kernel/` imports nothing from `contracts/` or
  `agents/`. The adapter defines the session machinery and **one shared declarative
  `Base`** — and **zero domain tables**. Tables are defined later by each agent's
  `store.py` against this `Base`. `import-linter` ("Kernel is pure plumbing") must
  stay KEPT.
- **No external infrastructure in the gate.** Tests run on **SQLite** (in-memory or
  a temp file). The adapter is engine-agnostic via the SQLAlchemy URL from config;
  Postgres is a later `integration`/`live` target, not a Sprint-02 dependency.
- **Synchronous**, to match the synchronous bus. Use `Session`/`sessionmaker`, not
  `AsyncSession`. (If a later sprint needs async, that is its decision to make.)
- **Faults, not silent failure.** A failing transaction rolls back, records an
  `AgentFault` with `module="kernel.persistence"`, and re-raises — persistence
  failures must surface, never be swallowed.
- **No magic numbers.** Any pool/engine constant that influences behaviour is a
  justified `kernel.tunable(..., why=...)`. The `DATABASE_URL` default is a local
  SQLite URL so the gate needs neither a service nor an env var.

## Deliverables

1. **`kernel/persistence.py`** (header + < 200 lines), pure plumbing:
   - `Base` — a SQLAlchemy 2.0 `DeclarativeBase`. Its `metadata` is what Alembic
     autogenerate and tests target. Defines no tables itself.
   - `PersistenceSettings(AgentSettings)` — `database_url: str` defaulting to a local
     SQLite URL (e.g. `"sqlite:///./trading.db"`), read from `DATABASE_URL` (no agent
     prefix — this is infrastructure). Any engine knob (e.g. `pool_pre_ping`) declared
     via `tunable(..., why=...)`.
   - `Database` — wraps engine + `sessionmaker` + a `FaultSink`
     (`__init__(self, settings: PersistenceSettings | None = None, sink: FaultSink |
     None = None)`; default settings + `CollectingFaultSink`).
     - `session()` — a context manager yielding a `Session`: **commit on clean exit;
       on exception roll back, record a fault via `fault_boundary(self.sink,
       agent="kernel", module="kernel.persistence", reraise=True)`, and re-raise.**
     - `create_all()` / `drop_all()` — thin helpers over `Base.metadata` for tests
       and local bootstrap. (Production schema is owned by migrations, not these.)
   - Keep it generic over any tables registered on `Base`. No domain logic.

2. **`kernel/__init__.py`** — export `Base`, `Database`, `PersistenceSettings`.

3. **Alembic migration harness** (outside `kernel/`, so guards/coverage don't touch
   it — `check_module_size`/`check_module_header` and the coverage `source` already
   scope to `kernel contracts agents …`, not `alembic/`):
   - `alembic.ini` (script location `alembic/`).
   - `alembic/env.py` wired to `kernel.persistence.Base.metadata` and reading the URL
     from `PersistenceSettings` — **never a hardcoded URL**. Offline + online modes.
   - `alembic/versions/` — a baseline (may be an empty initial revision; there are no
     domain tables yet). The point this sprint is a *working pipeline*, not content.
   - Confirm `alembic/versions` stays in the ruff `extend-exclude` (it already is).

4. **Dependency wiring.** The gate must be able to import `sqlalchemy` + `alembic`.
   Decide and record: add both to the `dev` dependency group (they are now needed to
   test core kernel plumbing), **or** have `make ci`/CI install the `runtime` extra.
   Prefer the dev-group route unless you see a reason not to. SQLAlchemy 2.0 has
   native typing — use `Mapped[...]` / `mapped_column(...)`; no mypy plugin needed.

5. **`.env.example`** — uncomment / document `DATABASE_URL`, noting the SQLite
   default and that Postgres is the eventual target.

6. **`tests/test_persistence.py`** — define a **test-only** table (a `Base` subclass)
   *inside the test module*; add nothing to `agents/` or `contracts/`. Cover:
   - **round-trip**: `create_all()` on a temp/in-memory SQLite `Database`; insert a
     row inside `session()`; read it back in a fresh session.
   - **commit boundary**: a clean `session()` block persists; the row is visible
     afterward.
   - **rollback + fault**: a `session()` block that raises mid-write leaves the table
     unchanged, records exactly one fault on the sink (`source_module ==
     "kernel.persistence"`, right `error_type`), and re-raises.
   - **migration smoke** (mark `integration`): run Alembic to `upgrade head` against a
     temp SQLite DB via Alembic's Python API, then assert autogenerate detects **no
     drift** between `Base.metadata` and the migrated schema.

## Steps

1. Branch `sprint-02-persistence` off `main`.
2. Add the persistence deps to the gate (deliverable 4); `uv sync`.
3. Write `kernel/persistence.py` (header + < 200 lines); export from `__init__`.
4. Scaffold Alembic (`alembic.ini`, `alembic/env.py`, baseline revision) wired to
   `Base.metadata` + `PersistenceSettings`.
5. Update `.env.example`.
6. Write `tests/test_persistence.py` covering the cases above.
7. Run `make ci`; fix until green. If coverage climbs, raise the floor in
   `pyproject.toml` (`--cov-fail-under` and `[tool.coverage.report] fail_under`) to the
   new measured value — never lower it.
8. Push the branch and hand back the report (below). Do not merge to `main`.

## Acceptance criteria

- `kernel/persistence.py` exists with a coding-agent header, under 200 lines, and
  defines no domain tables.
- `import-linter` still reports "Kernel is pure plumbing" **KEPT**.
- `alembic upgrade head` runs clean against a temp SQLite DB and autogenerate reports
  **no drift** afterward.
- `tests/test_persistence.py` passes all cases (the migration smoke may be
  `integration`-marked but must pass in the default run).
- `make ci` fully green; coverage at or above the (possibly raised) floor.
- No changes under `agents/` or `contracts/`; the boundary meta-test still passes.

## Out of scope (do NOT build this sprint)

The Neo4j / graph adapter · the distributed (Celery) bus · the observability/metrics
adapter · MCP · any real agent's tables or `store.py` · Postgres-specific features or
a running Postgres dependency · async sessions. Each is its own later sprint — flag if
you think one is needed early.

## Handback report (paste into the PR / reply)

- Files added/changed and final line counts.
- New total coverage % and whether the floor was raised.
- The dependency-wiring decision (deliverable 4) and any other design decision worth
  recording (session/fault shape, baseline-revision approach, SQLite test strategy),
  or anything that felt out of scope.

The planning agent will review, merge to `main`, and update `docs/STATE.md` +
`docs/build-plan.md`.
