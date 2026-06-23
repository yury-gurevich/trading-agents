# Sprint 92 — CI-3: ParameterSet (configurable, not settable)

**Branch:** `sprint-92-ci3-parameter-set`
**Status:** queued · **Phase:** P16 (continuous improvement, ADR-0013) · **Effort: M**

## Goal

A run loads a **named, versioned `ParameterSet`** from the graph instead of ad-hoc env vars. This is
the concrete "configurable, not settable" change. (Layer 3 of ADR-0013.)

## Scope

**In:**
- `ParameterSet` graph node: `{id, name, version, created_at, status (draft|champion|challenger|
  retired), overrides: {env_var → value}, note}`; values validated against the CI-1 catalogue bounds.
- Loader: resolve a `ParameterSet` → apply its overrides to the process env/settings at run start
  (same mechanism env uses today; env remains the local override of last resort).
- `run_local.py --parameter-set <id|name>`; the active set id is stamped onto the run's `RunMetrics`
  (closes the key from CI-2).
- Seed the first sets from DL-17: `ingest-champion` (chunk_size=12, delay=60, sigma=4) and a couple of
  challengers.

**Out:** no auto-sweep, no promotion (CI-5/CI-6); a human names sets for now.

## Deliverables

- `ParameterSet` node + loader + bounds validation against CI-1.
- `run_local --parameter-set`; RunMetrics now carries `parameter_set_id`.
- Tests (100% coverage), including a rejected out-of-bounds override.

## Acceptance

- Running with `--parameter-set ingest-champion` reproduces DL-17 run 2; RunMetrics links to the set.
- An override outside a tunable's `ge/le` is rejected with a clear error.
- `make ci` green.

## Dependencies

- CI-1 (bounds), CI-2 (RunMetrics key). Blocks CI-4/CI-5/CI-6.
