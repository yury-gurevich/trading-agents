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
| `PM`   | portfolio_manager | `OPER` | operator |
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
