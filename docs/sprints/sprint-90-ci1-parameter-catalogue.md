# Sprint 90 — CI-1: unified parameter catalogue

**Branch:** `sprint-90-ci1-parameter-catalogue`
**Status:** queued · **Phase:** P16 (continuous improvement, ADR-0013) · **Effort: S**

## Goal

One call lists **every** `tunable()` in the system — across all agent settings classes — with env var,
default, justification, bounds, and unit. The menu of what can be tuned. (Layer 1 of ADR-0013.)

## Scope

**In:**

- `kernel/config.py`: **auto-registration, not a hand list.** `AgentSettings.__init_subclass__`
  registers each settings subclass into a module-level registry the moment it is defined;
  `describe_all() -> list[TunableDoc]` reads that registry and folds in the existing per-class
  `describe()`. Declaring a `tunable()` on an `AgentSettings` subclass *is* cataloguing it — there is
  no list to remember to edit.
- **Completeness gate (closes the one hole in auto-registration).** A CI test statically scans the tree
  for `class *Settings(AgentSettings)` and asserts every one appears in the catalogue — so a settings
  class that is never imported (hence never registered) **fails CI** until it is wired in.
- Tag each `TunableDoc` with its owning `process` (agent name) so later layers can key on it.
- A read surface: extend the existing tunables view / add a CLI query (`surfaces/queries`) that prints
  the catalogue grouped by process.

**Note — two registration duties on new functionality (CI-2 enforces the second):** adding a dial is
automatic here (the parameter); making it *tunable* is not — its target/guardrail metric must be
registered (the `G-REG` gate, charter §OPS-GATE). So **catalogue ⊇ experiment-eligible**.

**Out:** no graph writes, no metrics, no experiments — pure introspection.

## Deliverables

- `describe_all()` + process-tagged `TunableDoc`.
- Settings-class registry (single import point).
- CLI/surface listing; test asserting ≥ the current ~145 params are catalogued and bounds round-trip.

## Acceptance

- `make ci` green; 100% coverage on new code.
- Catalogue lists every agent's tunables with correct env var (prefix-aware) and bounds.
- Adding a new `tunable()` to any settings subclass appears automatically (no list edit).
- The completeness test fails when a `*Settings(AgentSettings)` subclass is missing from the catalogue
  (proven by a fixture class that is defined-but-unregistered).

## Dependencies

- None (foundation). Blocks CI-3 (ParameterSet validates against the catalogue's bounds).
