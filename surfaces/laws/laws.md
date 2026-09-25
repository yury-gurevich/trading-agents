# `Surfaces` — Laws

**Prefix:** `SRF` · **status:** LOCKED v1 · **Owner:** Yury Gurevich

> Project graph-backed operating evidence to the human and route only bounded, audited operator intents.

Each clause below has a stable ID (`SRF-CAT-NN`). IDs are append-only (conventions §2). A clause is
green only when a functional test cites its ID (conventions §3). Tests + status live in
`test-plan.md`.

## Identity & purpose (`IDN`)

- **SRF-IDN-01** — Surfaces are the operator's product interface over stored evidence: CLI, MCP
  tools, dashboard routes, dashboard chat, and static dashboard assets. They explain and route
  bounded operator intent; they do not make trading decisions.
- **SRF-IDN-02** — Surfaces are read-only over trading facts except for named operator-intent write
  paths: dashboard hold answers, command audit/intents/LLM call audit, and supervisor-routed
  approvals, resumes, run commands, and stage promotions.

## Inputs (`IN`)

- **SRF-IN-01** — Run-scoped dashboard routes require an existing run id. Unknown runs return a clear
  404 instead of projecting another run.
- **SRF-IN-02** — Dashboard hold answers require POST, valid JSON object shape, a legal answer, and
  a live unanswered hold for the named run before appending a shared `RunHoldAnswer`.
- **SRF-IN-03** — Dashboard chat accepts only JSON requests with string message/run id fields and a
  boolean confirmation flag; unbound chat reports disconnection and malformed requests fail closed.
- **SRF-IN-04** — MCP tools accept only their declared tool names and argument shapes. Unknown tools
  and invalid argument types return plain errors rather than dispatching.

## Triggers (`TRG`)

- **SRF-TRG-01** — Dashboard GET routes and CLI read commands project evidence only on request.
  Dashboard POST routes are limited to chat and hold-answer handling.
- **SRF-TRG-02** — MCP requests are limited to the registered tool catalogue: `command`, `status`,
  `runs`, `incidents`, and `explain`.

## Outputs (`OUT`)

- **SRF-OUT-01** — The selected run scopes contextual dashboard panels and log windows. If a run is
  unknown, the route says so or falls back with an explicit `scope="latest"` marker where that is the
  documented log behaviour.
- **SRF-OUT-02** — "Open incidents" has one definition across surfaces and health: the same live
  incident predicate the supervisor health count uses.
- **SRF-OUT-03** — Dashboard chat answers are grounded in the selected run and record auditable
  `CommandAudit`, `LLMCall`, and `Intent` facts for priced/operator review.
- **SRF-OUT-04** — Operator-facing dashboard time labels are Melbourne local time in 24-hour format;
  the page receives `Australia/Melbourne` as its rendering zone.
- **SRF-OUT-05** — Operator-facing dashboard text and API display strings do not expose sprint ids,
  design-log ids, drift ids, or law ids as product language.
- **SRF-OUT-06** — The dashboard must not present an unwired control as active. Hold-answer controls
  appear only for active unanswered holds, and chat/resume assets carry the wired state expected by
  the route tests.

## Prohibitions (`NEV`)

- **SRF-NEV-01** — Any surface action with broker or run-placement consequences requires explicit
  confirmation before dispatch. Resume controls must spell out the broker consequence before the
  confirmed dispatch.
- **SRF-NEV-02** — Surfaces never use internal project vocabulary as a headline or operator action
  label. Raw tags may appear only as evidence data in detail views.
- **SRF-NEV-03** — Surfaces never dispatch an unknown or unbounded command tool.

## State & effects (`STA`)

- **SRF-STA-01** — Surface writes are audited operator-intent facts or shared answer facts: dashboard
  hold answers write `RunHoldAnswer`; chat writes audit/intent/LLM evidence; confirmed supervisor
  dispatches may write the downstream facts their bounded intent owns.
- **SRF-STA-02** — Repeated chat turns append fresh audit, LLM, and intent facts; they do not mutate
  prior operator evidence.

## Determinism & idempotency (`IDM`)

- **SRF-IDM-01** — Repeating the same chat message appends a new priced exchange with a distinct
  audit id, preserving an auditable sequence rather than overwriting history.

## Ordering & concurrency (`ORD`)

- **SRF-ORD-01** — Run lists render newest requested run first.
- **SRF-ORD-02** — Resolution views derive from matching `FlagResolution` facts, so append-only flag
  records do not remain pending after an approved answer.

## Failure, recovery & rollback (`FAIL`)

- **SRF-FAIL-01** — Optional Azure, log, cost, or image evidence failures degrade the relevant
  projection while keeping dashboard routes HTTP-successful and explicit about unavailable evidence.
- **SRF-FAIL-02** — Chat, MCP, and operator-tool errors reach the operator in plain words, not raw
  SDK JSON or traceback-shaped internals.

## Type alignment (`TYP`)

- **SRF-TYP-01** — MCP and dashboard chat tool families are bounded to the declared catalogue and
  return JSON-serialisable dictionaries.
- **SRF-TYP-02** — Dashboard API routes return JSON payloads for known routes, 404 for unknown
  routes/runs, and 405 for unsupported methods.

## Security & privilege (`SEC`)

- **SRF-SEC-01** — Surfaces hold no broker authority. Broker-affecting consequences can only be
  reached through the bounded operator/supervisor command path and its confirmation gate.
- **SRF-SEC-02** — Surface adapters sanitise external read errors before returning them to MCP,
  dashboard, or CLI callers.

## Dependencies (`DEP`)

- **SRF-DEP-01** — Surfaces depend on the graph store for operating evidence, optional Azure/GitHub
  readers for infrastructure/deploy evidence, the message bus for operator/supervisor/reporter
  requests, and an optional dashboard chat LLM client.
- **SRF-DEP-02** — The dashboard remains useful when optional Azure/GitHub readers or chat binding
  are absent: read routes degrade, and chat reports disconnected.

## Observability & audit (`OBS`)

- **SRF-OBS-01** — Confirmed surface actions are reconstructable through graph facts or supervisor
  dispatch results: hold answers, flag approvals, resumes, run commands, and chat turns carry durable
  evidence.
- **SRF-OBS-02** — The context bundle contains per-container logs and image evidence when available,
  and names unavailable or partial evidence without inventing it.

## Performance envelope (`PERF`)

- **SRF-PERF-01** — Log and bundle reads are bounded by dashboard settings (`log_tail_default`,
  `log_tail_max`, `bundle_log_tail`) and invalid tail inputs fall back to the documented default.
- **SRF-PERF-02** — Dashboard projection, fleet, cost, self-heal, GitHub, and Azure reads are bounded
  by their declared timeout/cache settings.

## Capability declaration (`CAP`)

```json
{
  "graph": {
    "operations": ["read", "append_write_for_operator_intent"],
    "access": "read-mostly"
  },
  "messaging": {
    "operations": ["request"],
    "targets": ["operator", "supervisor", "reporter"]
  },
  "external_reads": {
    "operations": ["read"],
    "systems": ["Azure Resource Manager", "Log Analytics", "GitHub Actions"]
  },
  "llm": {
    "operations": ["complete"],
    "scope": "dashboard chat only, optional"
  }
}
```

## Parameters (`PARAM`)

| Name | Value | Type | Tunable | Rationale |
| --- | --- | --- | --- | --- |
| `azure_subscription_id` | `""` | `str` | YES | ARM subscription containing the standing trading fleet. |
| `azure_resource_group` | `"trading-agents"` | `str` | YES | Resource group used as the bounded dashboard read scope. |
| `azure_workspace_id` | `""` | `str` | YES | Log Analytics workspace queried for per-container evidence. |
| `azure_environment_name` | `"trading-agents-env"` | `str` | YES | Container Apps environment label rendered in Section I. |
| `azure_job_name` | `"dispatcher-cron"` | `str` | YES | Scheduled dispatcher job that starts each graph-pull run. |
| `azure_timeout_seconds` | `20.0` | `float > 0 <= 60` | YES | Bound every Azure REST read so the dashboard still degrades promptly. |
| `azure_credential_mode` | `"auto"` | `Literal["auto","default","cli","service_principal"]` | YES | Allow a read-only local operator to select the Azure CLI credential when the existing service principal lacks dashboard Reader roles. |
| `fleet_cache_ttl_seconds` | `30.0` | `float >= 0 <= 300` | YES | Avoid repeating replica reads during one page refresh. |
| `cost_cache_ttl_seconds` | `300.0` | `float >= 0 <= 3600` | YES | Cost Management is slow and should not be hit on every panel refresh. |
| `projection_cache_ttl_seconds` | `5.0` | `float >= 0 <= 30` | YES | Collapse rapid repeated graph projections while keeping the verdict seconds-fresh. |
| `self_heal_refetch_seconds` | `90.0` | `float > 0 <= 600` | YES | Back off transient dashboard self-heal refetches to reduce repeated read egress. |
| `github_repository` | `"yury-gurevich/trading-agents"` | `str` | YES | Repository whose main image-build workflow defines deploy currency. |
| `github_image_workflow` | `"build-images.yml"` | `str` | YES | Workflow that publishes the main fleet images compared with DeployRecord. |
| `github_timeout_seconds` | `10.0` | `float > 0 <= 30` | YES | Bound the single read-only GitHub build lookup. |
| `log_tail_default` | `200` | `int >= 1 <= 1000` | YES | Match the operator-requested useful default log excerpt. |
| `log_tail_max` | `500` | `int >= 1 <= 5000` | YES | Keep interactive Log Analytics reads and responses bounded. |
| `bundle_log_tail` | `40` | `int >= 1 <= 500` | YES | Give the repair bundle useful evidence without multiplying its size. |
| `master_window_start_utc` | `"20:25"` | `str` | YES | Matches `$MasterScaleStart` in `infra/deploy-agents.ps1` and is test-pinned. |
| `agent_window_start_utc` | `"22:30"` | `str` | YES | Matches `$AgentScaleStart` in `infra/deploy-agents.ps1` and is test-pinned. |
| `window_end_utc` | `"00:30"` | `str` | YES | Matches `$ScaleEnd` in `infra/deploy-agents.ps1`. |
| `dispatcher_fire_utc` | `"22:30"` | `str` | YES | The dispatcher's first placing tick, `_ACTION_START`, and is test-pinned. |
| `operator_timezone` | `"Australia/Melbourne"` | `str` | YES | The operator reads their own local 24-hour time, never UTC. |
| `readiness_failure_max_age_minutes` | `1440` | `int >= 10 <= 2880` | YES | Keep a failed fleet check visible until the next one replaces it. |

## Divergence register

| ID | Law says | PRD / mission / code says | Decision needed |
| --- | --- | --- | --- |
| — | No new S229 surfaces divergence found. | DRIFT-022 is already corrected; S229 cites it as proof for selected-run scoping rather than reopening it. | Not applicable. |

## Changelog

- v1 — S229 authored surfaces law book for dashboard, CLI, MCP, chat, and operator-intent write
  boundaries. DRIFT-022 remains corrected and is cited by selected-run scoping clauses.
