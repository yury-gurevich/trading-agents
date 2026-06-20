# Sprint 72 — ADR-0010 immediate close: `system_prompt` tunable

**Branch:** `sprint-72-system-prompt-tunable`
**Phase:** ADR-0010 immediate consequence
**Status:** shipped

## Goal

Close the "immediate" consequence of ADR-0010 (LLM interaction quality gate):
declare `system_prompt` as a justified `tunable` in each LLM-backed agent, wire it
into the operator's interpret path, and pre-declare it on the forecaster for P13.

## What shipped

### Code changes

| File | Change |
| --- | --- |
| `agents/operator/settings.py` | Added `system_prompt: str = tunable("")` |
| `agents/operator/agent.py` | `_interpret_command`: `system = self._settings.system_prompt or build_interpret_system()` |
| `agents/forecaster/settings.py` | Pre-declared `system_prompt: str = tunable("")` (no-op until P13) |

### Law updates

| File | Change |
| --- | --- |
| `agents/operator/laws/laws.md` | PARAM: added `system_prompt` row; Changelog: v1.1 |
| `agents/forecaster/laws/laws.md` | PARAM: added `system_prompt` row; Changelog: v1.1 |

### Docs updated

- `docs/STATE.md` — S72 shipped
- `docs/sprints/INDEX.md` — S72 complete; next S73
- `docs/sprints/README.md` — S72 row added

## Semantic of the champion slot

| `system_prompt` value | Runtime behaviour |
| --- | --- |
| `""` (default) | `build_interpret_system()` called dynamically (includes live `INTENT_FAMILIES`) |
| non-empty | DSPy-promoted static prompt used verbatim; families list is embedded in the compiled string |

The DSPy PromptOptimizer will compile a static prompt that captures the families
list in optimized form and write it back to this setting via the predictor registry
champion gate (ADR-0002 / P10 pattern).

## What is NOT here

- No DSPy code, PromptOptimizer port, golden eval set, or registry wiring.
  Those are deferred in ADR-0010 until eval data exists (from the operator LLM ledger).

## CI result

`make ci` passed locally (9/9 steps). GitHub CI confirmed green after push.
