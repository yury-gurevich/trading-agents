# Drift register — the correction worklist

Every place where a **law (intent)** and **reality (PRD / mission / code)** disagree is recorded here
once, with a stable `DRIFT-NN` ID, so we can set them back on course later. Fed by each agent's local
**Divergence Register**. See conventions §9.

**Kinds** — `PRD-fork` (law vs PRD, needs a forced decision) · `stale-doc` (PRD/mission out of date
vs a later decision) · `code-drift` (code diverged from intent) · `gap` (intent not yet built).
**Status** — `OPEN` (awaiting forced decision) · `DECIDED` (resolution chosen) · `CORRECTED`.

## Provider (`PROV`)

| ID | Law | Intent says | Reality says | Kind | Status / decision |
| --- | --- | --- | --- | --- | --- |
| DRIFT-001 | PROV-STA-01 | The cache is a transparent perf optimisation; not load-bearing. | Mission/PRD: the provider **owns the price cache** (a first-class fact store). | PRD-fork | OPEN — forced decision D1 |
| DRIFT-002 | PROV-NEV-02 / IDN-01 | Provider serves *raw* news; sentiment scoring is downstream. | `mission.md` lists **finbert** as a provider client (sentiment in the provider). | stale-doc (vs ADR-0002, which put FinBERT in the forecaster) | OPEN — forced decision D2 |
| DRIFT-003 | PROV-IDN-01 / IN-01 | Fields = price, fundamentals, news, benchmark, regime. | `mission.md` also lists **FRED** (macro) and **EDGAR** (filings) sources. | gap / scope | OPEN — forced decision D3 |
| DRIFT-004 | PROV-OUT-02 | Regime response = classification + its inputs. | PRD/mission: provider emits the regime-derived **policy inputs** (stop/target/holding defaults) every downstream agent reads. | gap (enrich) | DECIDED — adopt PRD (strong guide); sharpen PROV-OUT-02 |
| DRIFT-005 | PROV-OUT-03 | Degradation = a quality record on the response (pull). | `mission.md`: provider also **emits** `market_data_degraded` (push event). | gap (enrich) | DECIDED — adopt both (record + event) |
| DRIFT-006 | PROV-OUT-01 | Benchmark is just another **requested field** of a market-data request. | Code (S38) fetches the benchmark via a **separate** request to dodge a degraded-quality trip. | code-drift | OPEN — reconcile code to law at test time |
| DRIFT-007 | PROV-SEC-07 | Only capability-matrix-authorised callers may invoke the provider. | Unverified that the matrix actually gates data requests. | code-drift (verify) | OPEN — confirm at reconciliation |

## Other agents

_Populated as each agent is authored and reconciled._
