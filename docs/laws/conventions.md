# Law conventions

The rules that govern the law book itself. These are deliberately strict — the conventions are what
make the laws *durable* rather than another thing that drifts.

## 1. Identifiers

Every law clause has a stable ID: **`AGENT-CAT-NN`**.

- `AGENT` — the agent's prefix (see table below).
- `CAT` — the law category (the template sections):

  | Code | Category |
  | --- | --- |
  | `IDN` | Identity & purpose |
  | `IN` | Inputs |
  | `TRG` | Triggers |
  | `OUT` | Outputs |
  | `NEV` | Prohibitions (never) |
  | `STA` | State & effects |
  | `IDM` | Determinism & idempotency |
  | `ORD` | Ordering & concurrency |
  | `FAIL` | Failure, recovery & rollback |
  | `TYP` | Type alignment |
  | `SEC` | Security & privilege |
  | `DEP` | Dependencies |
  | `OBS` | Observability & audit |
  | `PERF` | Performance envelope |

- `NN` — a zero-padded sequence within the category (`01`, `02`, …).

Dependency (Layer-0) clauses use **`DEP-<COMPONENT>-NN`** (e.g. `DEP-NEO4J-01`).

Agent prefixes:

| Prefix | Agent | Prefix | Agent |
| --- | --- | --- | --- |
| `PROV` | provider | `MON` | monitor |
| `SCAN` | scanner | `REPT` | reporter |
| `ANLY` | analyst | `RSCH` | researcher |
| `FCST` | forecaster | `CURA` | curator |
| `PM` | portfolio_manager | `OPER` | operator |
| `EXEC` | execution | `SUPV` | supervisor |

## 2. ID stability (the most important rule)

IDs are **append-only and immutable**:

- **Never renumber, never reuse** an ID. Tests cite IDs; renumbering silently breaks traceability —
  the single costliest invisible mistake.
- To remove a law, mark it **`DEPRECATED`** in place (keep the ID, strike the text, add a changelog
  line). Do not delete.
- New laws always take the next free number in their category.

## 3. Gray → green (the only definition of "done")

- A clause is **GREEN** iff **≥ 1 passing functional test cites its ID** (in the test's docstring).
- A clause with no citing test, or a failing one, is **GRAY**.
- **Dependencies first:** an agent clause cannot be counted green while a `DEP-*` clause it relies on
  is gray. Layer-0 gets a green bill of health before Layer-1 agents.
- The rollup lives in [`ledger.md`](ledger.md); "the system is green" means *every* non-deprecated law
  is green.

## 4. Locking & amendment

Each `laws.md` carries a header: `status: LOCKED v<N>` and a **Changelog** at the foot.

- A LOCKED law is the fixed reference. It changes **only** by a deliberate amendment: bump `v<N>`,
  add a changelog line stating *what changed and why*. Every movement of truth is therefore visible.
- Amend a law only when functionality is genuinely *lacking* (discovered during reconciliation or
  testing) — not to match whatever the code currently does.

## 5. The independence rule

An agent's `laws.md` references **only** itself and the **message types** it accepts/emits. It must
**never** name another agent or describe another agent's behaviour. All choreography ("A sends B …")
lives **only** in [`flow.md`](flow.md). (See README.)

## 6. Authoring mode

Laws are authored in **ideal-design mode**: from first-principles intent ("this must exist *because*
it feeds X *so that* Y"), **not** transcribed from the implementation. Where the ideal diverges from
the PRD, a mission, or (at reconciliation) the code, it is logged in the agent's **Divergence
Register** for the owner to adjudicate — confirm the law (and amend the stale source) or correct the
law.

## 7. Test citation

Every functional test names the law-ID(s) it proves in its docstring, e.g.
`"""PROV-FAIL-02: partial feed outage degrades per-field, never crashes."""`. Discovering a needed
test that has no law → **add the law to `laws.md` first** (new ID), then write the test. The plan is
the master; tests are the proof.

## 8. The PRD relationship

The PRD (`docs/PRD.md`) is a **"wish-to-have"** document — recognise it as such. But it is also what
**holds wishes and reality together**, so it is used deliberately, not ignored:

- **Where the PRD states functionality *explicitly*, it is a STRONG guide** — treat it as
  near-authoritative; the law adopts it unless there is a compelling reason not to.
- **Where the PRD is wishful/aspirational/silent**, ideal-design intent leads.
- **Desired functionality is derived by *combining* ideal-design + PRD** — never one in isolation.
- **Every divergence is resolved by a FORCED decision *before* tests are designed.** The planning
  agent must surface each fork, **offer a recommended resolution and the alternative**, and make the
  owner choose — "PRD-first here, ideal-first there." You cannot write a test against undecided
  functionality.
- The PRD is re-scoped to **product vision**; the **law book is the operational source of truth.** The
  PRD remains the integrator of wish + reality and a strong guide where explicit.

## 9. Drift register (central)

Every functional drift — a place where the law (intent) and reality (PRD, mission, or code) disagree —
is recorded **once, centrally**, in [`drift-register.md`](drift-register.md) with a stable `DRIFT-NN`
ID. Per-agent **Divergence Registers** (in each `laws.md`) are the *local source*; the central
register is the **aggregated correction worklist** we use later to set drifts back on course. A drift
is `OPEN` (needs a forced decision), `DECIDED` (resolution chosen, not yet applied), or `CORRECTED`.

## 10. Tests are local to the agent

An agent's **entire** test surface lives with the agent (`agents/<name>/tests/`, indexed by its
`laws/test-plan.md`) — both the **functional** tests and the **directional boundary** tests, with the
other side always **synthetic** (the agent is proven in isolation):

- **Up** (callers/triggers) — accepts lawful inputs, rejects unlawful (`IN`, `TRG`).
- **Down** (consumers) — emits lawful, type-aligned outputs (`OUT`, `TYP`).
- **Left/Right** (dependencies & concurrency) — correct when each dependency is healthy *and* red, and
  under concurrent/duplicate/late messages (`DEP`, `FAIL`, `ORD`).

No shared/central suite owns an agent's behaviour. Cross-agent choreography (Layer 2) is proven
separately, but **every edge of every agent is proven locally** against its contract.

## 11. Lock only after a full cycle

The `_TEMPLATE` is **not** locked on authoring. One agent (the **provider**) runs the *entire* cycle
first — author → forced PRD reconciliation → tests designed → tests run & reconciled → green — so the
template is proven end-to-end. **Only then** is it locked and copied to the other eleven.
