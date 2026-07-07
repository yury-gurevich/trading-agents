# `Researcher` — Laws

**Prefix:** `RES` · **status:** LOCKED v1 · **Owner:** Yury Gurevich

> Mine accumulated evidence for parameter and strategy improvements and propose bounded,
> measurable changes into the human-review queue — never apply them itself.

Each clause has a stable ID (`RES-CAT-NN`). IDs are append-only (conventions §2). A clause is
green only when a functional test cites its ID (conventions §3). Tests + status live in
`test-plan.md`.

## Identity & purpose (`IDN`)

- **RES-IDN-01** — The researcher's single job is evidence-to-proposal: collect run metrics from
  the graph over a configurable window, compute whether parameters should change, and submit at
  most `max_changes_per_proposal` bounded `ProposedChange` records into the human-review queue
  via the supervisor. It proposes; it never applies.
- **RES-IDN-02** — The researcher exclusively writes these graph labels (single-writer rule):
  `Experiment`, `ParamChange`.

## Inputs (`IN`)

- **RES-IN-01** — `propose` accepts `ResearchRequest { lookback_days=90,
  focus: str | None }`. Triggers an evidence collection and proposal build.
- **RES-IN-02** — `evidence` accepts `ResearchRequest`. Returns the raw evidence summary as
  an `Explanation`; no proposal or graph write.
- **RES-IN-03** — Malformed input → zero-change `ParameterChangeProposal` returned for `propose`;
  `Explanation(summary="...")` for `evidence`; fault recorded; never raises to bus.

## Triggers (`TRG`)

- **RES-TRG-01** — `propose` triggered by RPC request from the operator (via surfaces) or the
  dispatcher.
- **RES-TRG-02** — `evidence` triggered by RPC request only.
- **RES-TRG-03** — No event subscription; the researcher never self-triggers.

## Outputs (`OUT`)

- **RES-OUT-01** — `propose` returns `ParameterChangeProposal { proposal_id, changes,
  rationale, provenance }`. `changes` is a tuple of `ProposedChange`; may be empty.
- **RES-OUT-02** — When `changes` is non-empty, a `flag_for_human` RPC is sent to the supervisor
  so the proposal appears in the human-review queue.
- **RES-OUT-03** — `evidence` returns `Explanation` summarising available metrics; no graph write.
- **RES-OUT-04** — A `Experiment`/`ParamChange` graph node is written per successful proposal
  with changes.
- **RES-OUT-05** — When evidence is insufficient (fewer than `min_sample_runs` completed runs),
  `changes` is empty and `rationale` explains the gap; no flag is raised.
- **RES-OUT-06** — Zero-proposal (empty `changes`) result is a valid, non-degraded outcome.

## Prohibitions (`NEV`)

- **RES-NEV-01** — Never applies a parameter change itself. The researcher writes proposals into
  the review queue; only an approved operator-initiated intent can apply them.
- **RES-NEV-02** — Never bypasses the evidence-window requirement (`min_sample_runs`). Proposals
  without sufficient data always return zero changes.
- **RES-NEV-03** — Never proposes a forbidden parameter combination. Each `ProposedChange` is
  bounded by the settings schema (`confidence_low_water`/`high_water`, `confidence_step`).
- **RES-NEV-04** — Never imports from the analyst or PM agents. Parameter references are held
  as plain float tunables (`confidence_floor_reference`) without cross-agent coupling.

## State & effects (`STA`)

- **RES-STA-01** — Stateless between calls. Evidence is collected fresh from the graph on every
  invocation.
- **RES-STA-02** — Graph writes are append-only. `Experiment` and `ParamChange` nodes accumulate;
  none are overwritten.

## Determinism & idempotency (`IDM`)

- **RES-IDM-01** — Given the same graph state, `propose` produces the same `ParameterChangeProposal`
  structure. The proposal ID is a UUID hex; re-invoking generates a new proposal ID.
- **RES-IDM-02** — Not globally idempotent: each `propose` call writes a new `Experiment` node
  and sends a new `flag_for_human` if changes are found.
- **RES-IDM-03** — `evidence` is idempotent (read-only) given the same graph state.

## Ordering & concurrency (`ORD`)

- **RES-ORD-01** — No ordering dependency between `propose` calls.
- **RES-ORD-02** — Concurrent `propose` calls produce independent proposals; no deduplication
  at the researcher level.

## Failure, recovery & rollback (`FAIL`)

- **RES-FAIL-01** — Evidence collection failure: `fault_boundary` captures; zero-proposal
  returned with `rationale` explaining the failure; fault emitted.
- **RES-FAIL-02** — Proposal build failure: `fault_boundary` captures; zero-proposal returned;
  fault emitted.
- **RES-FAIL-03** — `flag_for_human` bus call failure: the proposal is still returned; the flag
  failure is a secondary fault; the proposal is not rolled back.
- **RES-FAIL-04** — Graph write failure for `Experiment`/`ParamChange`: fault emitted; the
  `ParameterChangeProposal` is still returned to the caller.

## Type alignment (`TYP`)

- **RES-TYP-01** — `ParameterChangeProposal` and `ProposedChange` match `contracts/researcher.py`
  exactly.
- **RES-TYP-02** — `ProposedChange.current_value` and `proposed_value` are floats; bounded by
  the settings schema constraints.
- **RES-TYP-03** — `evidence_window_days` on each `ProposedChange` reflects the actual evidence
  window used; never a literal default.

## Security & privilege (`SEC`)

- **RES-SEC-01** — Holds no credentials; no elevated privilege.
- **RES-SEC-02** — Cannot apply changes: all write paths go through the operator approval queue.
- **RES-SEC-03** — Proposal `parameters` dict contains only known parameter names from the
  settings schema; no arbitrary key injection from user input.
- **RES-SEC-04** — Revocable without breaking the system; if the researcher is down, trading
  continues and no proposals are generated until it restarts.

## Dependencies (`DEP`)

- **RES-DEP-01** — `DEP-POSTGRES` — reads `Snapshot`, `PMRun`, recommendation metrics for
  evidence; writes `Experiment`, `ParamChange`.
- **RES-DEP-02** — `DEP-BUS` — sends `flag_for_human` to supervisor when changes are found.

## Observability & audit (`OBS`)

- **RES-OBS-01** — `Experiment` and `ParamChange` nodes record every proposal with evidence
  window, proposed values, and rationale; auditable without the RPC response.
- **RES-OBS-02** — The `Flag` raised in the supervisor is the operational alert; `pending_human_flags`
  in `MasterReport` reflects pending proposals.
- **RES-OBS-03** — Zero-proposal results (insufficient data) are logged via `rationale`; never
  silent.

## Performance envelope (`PERF`)

- **RES-PERF-01** — `min_sample_runs=5` is the minimum evidence gate; evidence collection on
  5 runs is bounded and fast.
- **RES-PERF-02** — `max_changes_per_proposal=2` keeps proposals small and reviewer-friendly.

## Capability declaration (`CAP`)

```json
{
  "graph": {
    "operations": ["append_write", "read"],
    "labels_owned": ["Experiment", "ParamChange"],
    "labels_read": ["Snapshot", "PMRun", "Recommendation"]
  },
  "messaging": {
    "operations": ["request"],
    "peers": ["supervisor"]
  }
}
```

## Parameters (`PARAM`)

| Name | Value | Type | Tunable | Rationale |
| --- | --- | --- | --- | --- |
| `lookback_days` | `90` | `int ≥ 30 ≤ 365` | YES | Quarterly history for slow-changing signals |
| `min_sample_runs` | `5` | `int ≥ 3 ≤ 100` | YES | Multiple runs avoid one-day drift artefacts |
| `min_evidence_window_days` | `30` | `int ≥ 7 ≤ 365` | YES | Monthly window for parameter-change evidence |
| `max_changes_per_proposal` | `2` | `int ≥ 1 ≤ 5` | YES | Small proposals stay reviewable and reversible |
| `confidence_floor_reference` | `0.30` | `float ≥ 0.0 ≤ 1.0` | YES | Analyst confidence-floor baseline without importing analyst |
| `confidence_step` | `0.05` | `float ≥ 0.01 ≤ 0.20` | YES | Gradual threshold moves keep effects measurable |
| `confidence_low_water` | `0.40` | `float ≥ 0.0 ≤ 1.0` | YES | Below this average confidence, demand stronger signals |
| `confidence_high_water` | `0.70` | `float ≥ 0.0 ≤ 1.0` | YES | Above this average confidence, allow more candidates |

## Divergence register

| ID | Law says | Code / contract says | Decision |
| --- | --- | --- | --- |
| — | — | — | no known drift |

## Changelog

- v1 — authored S71 and locked immediately (full first-principles cycle).
