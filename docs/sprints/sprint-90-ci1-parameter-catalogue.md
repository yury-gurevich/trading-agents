# Sprint 90 — CI-1: unified parameter catalogue

**Branch:** `sprint-90-ci1-parameter-catalogue`
**Status:** queued · **Phase:** P16 (continuous improvement, ADR-0013) · **Effort: S**

## Goal

One call lists **every** `tunable()` in the system — across all agent settings classes — with env var,
default, justification, bounds, and unit. The menu of what can be tuned. (Layer 1 of ADR-0013.)

## Scope

**In:**
- `kernel/config.py`: `describe_all(*settings_classes) -> list[TunableDoc]` (or a registry that
  collects the known settings classes) building on the existing per-class `describe()`.
- A registry of every agent settings class (`provider`, `scanner`, `analyst`, `analyst_indicators`,
  `portfolio_manager`, `execution`, `monitor`, `reporter`, `forecaster`, `operator`, `curator`,
  `researcher`, `master`, plus kernel graph/bus configs).
- Tag each `TunableDoc` with its owning `process` (agent name) so later layers can key on it.
- A read surface: extend the existing tunables view / add a CLI query (`surfaces/queries`) that prints
  the catalogue grouped by process.

**Out:** no graph writes, no metrics, no experiments — pure introspection.

## Deliverables

- `describe_all()` + process-tagged `TunableDoc`.
- Settings-class registry (single import point).
- CLI/surface listing; test asserting ≥ the current ~145 params are catalogued and bounds round-trip.

## Acceptance

- `make ci` green; 100% coverage on new code.
- Catalogue lists every agent's tunables with correct env var (prefix-aware) and bounds.
- Adding a new `tunable()` to any registered settings class appears automatically.

## Dependencies

- None (foundation). Blocks CI-3 (ParameterSet validates against the catalogue's bounds).
