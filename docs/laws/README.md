# The Law Book — operational source of truth

This is the **umbrella** that ties the agents together at the system level. It exists to do two
things and only two things:

1. **Arrest functionality drift** — each agent's behaviour is fixed as *law*, changed only by a
   deliberate, logged amendment, never by what the code happens to drift into.
2. **Document the system** — the law book *is* the documentation of what each component must and must
   not do.

## How it is organised

- **Umbrella (`docs/laws/`)** — system-level, the only place agents are connected:
  - [`conventions.md`](conventions.md) — ID scheme, stability rules, the gray→green definition, the
    lock mechanism, and the independence rule.
  - [`_TEMPLATE.md`](_TEMPLATE.md) — the law schema every agent obeys. **Locked first; copied to each
    agent.**
  - [`flow.md`](flow.md) — the agent flow diagram (the choreography). **Inter-agent knowledge lives
    only here.**
  - [`dependencies.md`](dependencies.md) — Layer-0 dependency charter; the "green bill of health" that
    must pass before any agent can be green.
  - [`drift-register.md`](drift-register.md) — the central worklist of every law-vs-reality drift, to
    set back on course later.
  - [`ledger.md`](ledger.md) — the gray→green rollup. "The landscape."
- **Per-agent shard (`agents/<name>/laws/`)** — sealed, travels with the agent:
  - `laws.md` — the **locked constitution**, every clause ID'd.
  - `test-plan.md` — the **living** plan + status; each line cites a law-ID and maps to a test.

> **ADR-0007 additions (2026-06-18).** Every `laws.md` must include two new sections:
>
> - **`CAPABILITY DECLARATION (CAP)`** — a JSON schema of what the agent needs at runtime
>   (message queue, graph, data API, broker). Interface-first; no product names. This becomes the
>   EHLO payload sent to the master agent at startup.
> - **`PARAMETERS (PARAM)`** — every constant in agent code documented with schema, rationale,
>   and marked `tunable` or `non-tunable`. Tunable = can be adjusted for experiments; non-tunable =
>   structural constant whose change would alter the agent's semantic contract.
>
> See `_TEMPLATE.md` for stub sections and `docs/decisions/0007-container-per-agent-master-bootstrap.md`
> for the rationale.

## The one rule that keeps agents independent

> An agent's `laws.md` describes **only itself** and the **message types** it accepts/emits — never
> another agent by name. "Where input comes from" is recorded as a *type + provenance role*, not a
> dependency. All "A → B" knowledge lives **only** in [`flow.md`](flow.md).

This makes a one-way DAG: the **umbrella knows all agents; agents know only the conventions and their
own contracts; agents never reference each other.** Any `agents/<name>/` can be lifted out whole and
its laws still make complete sense.

## On the PRD

The PRD (`docs/PRD.md`) was product **vision**, written before the foundation was solid; "make it
work" coding decisions may have pulled the system away from it. **The laws are not derived from the
PRD or the code** — they are authored from first-principles intent. Where a law diverges from the PRD
or a mission, it is recorded in that agent's **Divergence Register** as an explicit decision for the
owner. The intent: **the law book becomes the operational source of truth; the PRD is re-scoped to
product vision.** Nothing is inherited silently.

## Status

Bootstrapping. **Provider** is the first authored agent (the template stress-test). The pattern is
reviewed and locked, then copied to the remaining eleven. See [`ledger.md`](ledger.md).
