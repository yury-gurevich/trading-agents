# Configuration & Constants Governance

**Principle:** no bare magic numbers. Every value that influences processing or a
forecast is a *justified, env-overridable tunable* — visible, bounded, and
controllable from one place. An operator (or auditor) can see every knob, its
default, why that default was chosen, and its safe range, without reading code.

## The modifiable environment

All configuration enters through the environment: a local `.env` file (see
`.env.example`) overlaid by the process environment. Nothing is hardcoded into a
deployment. Each agent namespaces its variables with an env prefix
(`SCANNER_`, `ANALYST_`, …) so there are no collisions and the source of any value
is obvious from its name.

## Declaring a tunable

Every configurable constant is declared with `kernel.tunable`, which makes the
justification mandatory and applies bounds:

```python
from kernel import AgentSettings, tunable
from pydantic_settings import SettingsConfigDict


class AnalystSettings(AgentSettings):
    model_config = SettingsConfigDict(env_prefix="ANALYST_", frozen=True)

    min_confidence: float = tunable(
        0.6,
        why="below 0.6 the blended score is indistinguishable from noise "
            "(2024 walk-forward study, docs/research/confidence-floor.md)",
        ge=0.0,
        le=1.0,
    )
```

This guarantees four things at once:

1. **Isolated & modifiable** — overridable via `ANALYST_MIN_CONFIDENCE` in `.env`.
2. **Justified in code** — `why` is required; a tunable cannot exist without a
   recorded reason for its value.
3. **Bounded** — `ge`/`gt`/`le` reject an override that would push it out of a safe
   range.
4. **Visible** — introspectable into the central catalogue (below).

A bare literal that influences a decision or forecast is a defect: convert it to a
tunable so its value is governed and its rationale is on the record.

## The constants catalogue

`kernel.describe(SettingsClass)` returns every tunable as a row — name, env var,
default, justification, and bounds. This is the single source of truth rendered
into:

- this documentation (regenerated as agents land),
- a dashboard panel where the operator sees and controls every knob,
- audit exports (acquisition-grade: every value that shaped a decision is on record).

## Secrets

Secrets (broker keys, model-provider keys, database passwords) are **not** tunables.
They are provided through the environment out-of-band, never committed, and never
echoed downstream — only the owning agent (provider, execution, operator) reads its
own credentials.
