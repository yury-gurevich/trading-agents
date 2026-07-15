# Sprint 126 live proof

Date: 2026-07-14 AEST. Live systems: Neon PostgreSQL spine, Azure Container Apps read APIs,
GitHub Actions read API, Anthropic operator path, and Alpaca paper account read API. Secrets and
connection strings were not printed.

## Resume from monitor

- Source: completed `sched-2026-07-13`.
- Dashboard command: `Resume from monitor`, posted to `/api/chat` with request ID
  `s126-law02-monitor-confirm`; first response `needs_confirmation`, second response
  `confirmed_dispatch`; both responses returned audit `audit:6a6c8832aa45ea2b`.
- The typed intent was `resume`, `from_stage=monitor`, `run_id=sched-2026-07-13`. The monitor
  confirmation correctly did not claim that broker orders would be submitted.
- Child: `sched-2026-07-13-resume-monitor`. `scripts.trace_run` reported **7/7 stages complete**:
  provider/scanner/analyst/PM/execution were linked upstream and only monitor/reporter were run.
- Monitor result: four existing paper positions checked, four holds, zero closes. Alpaca returned
  zero orders created from `2026-07-14T02:50:00Z` onward.
- Original source nodes were retained and unchanged. Resume is one child `RunRequest`, one
  child-to-source `RESUMES` edge, and `LINKED_FROM` provenance; no node or edge was deleted.

## Deploy currency and bus health

- The retained `DeployRecord`
  `deploy:2026-07-09T02:52:54.725871+00:00:s121:15e9688dd18fe4f7d9792bc9286dfa9cee61328d`
  records the historically verified `s121` deployment. It is backed by Azure revision/job evidence
  and successful build run `28990461295`; it does not pretend that the fleet is current.
- Live Azure CLI reads found one observed fleet tag, `s121`, matching that record.
- The newest successful main image build was run `29299680862`, SHA
  `9420b785c73f0bcd25991907781da720fc2bc2eb`. The projection returned `behind`, with
  `fleet_matches_record=true` and `main_matches_record=false`.
- With the Azure service-principal variables unset, `/api/infra` returned bus `unverified`, not
  `unreachable`. With authenticated Azure CLI reads, it returned `reachable`.

## Retained and torn down

All graph writes below are retained audit/provenance or real monitor observations. Nothing was
deleted or overwritten.

- Resume lineage: `run-request:sched-2026-07-13-resume-monitor`,
  `resume-link:sched-2026-07-13-resume-monitor:marketdata`,
  `resume-link:sched-2026-07-13-resume-monitor:scanrun`,
  `resume-link:sched-2026-07-13-resume-monitor:analystrun`,
  `resume-link:sched-2026-07-13-resume-monitor:pmrun`,
  `resume-link:sched-2026-07-13-resume-monitor:executionrun`, and
  `regime-context:sched-2026-07-13-resume-monitor`.
- Derived stages: `monitor-run-7dba17def52645e08988f2f512fc4e2c` and
  `snapshot:resume-link:sched-2026-07-13-resume-monitor:pmrun`.
- Monitor observations: four `PositionCheck` nodes below, all `hold`; no `Position`,
  `CloseDecision`, `OrderIntent`, `Fill`, or broker order was created:
  `monitor-run-7dba17def52645e08988f2f512fc4e2c:broker-reconciled:AMD:check`,
  `monitor-run-7dba17def52645e08988f2f512fc4e2c:broker:BAC:171:5850:check`,
  `monitor-run-7dba17def52645e08988f2f512fc4e2c:broker:CSCO:177:11241:check`, and
  `monitor-run-7dba17def52645e08988f2f512fc4e2c:broker:WFC:116:8603:check`.
- Accepted confirm ledger: `audit:6a6c8832aa45ea2b`, `llmcall:6a6c8832aa45ea2b`,
  `intent:6a6c8832aa45ea2b`, `flag:6a6c8832aa45ea2b:warn`,
  `resolution:flag:6a6c8832aa45ea2b:warn`, and `6a6c8832aa45ea2b:resume` (`Message`).
- Diagnostic attempts that exposed and verified the two fixed confirmation defects remain as audit
  history: `audit:`, `llmcall:`, and `intent:` nodes with each suffix
  `a9016edc279da8fd`, `bac715417452b584`, `1ae867b982a38b59`, and
  `48e97492b29644f6`; plus `48e97492b29644f6:resume` (`Message`). Pending diagnostic warnings
  `flag:a9016edc279da8fd:warn` and `flag:1ae867b982a38b59:warn` were append-resolved by
  `resolution:flag:a9016edc279da8fd:warn` and `resolution:flag:1ae867b982a38b59:warn`.
- The local dashboard processes are disposable and are stopped after capture. No Azure control-plane
  write occurred. The historical `DeployRecord`, resume lineage, operator ledger, and monitor
  observations are deliberately retained.

## Screenshot status

The exact API and graph evidence above is complete. Screenshot capture was completed by the
planning agent on 2026-07-15 (headless Chrome against a live local dashboard on ports 8321/8322,
servers stopped and ports verified released after capture); no substitute or fabricated image was
used.

- `resume-child-run.png` — run `sched-2026-07-13-resume-monitor` selected: **RUN PASSED / GREEN**,
  7/7 stage cards (upstream linked, monitor `checked=4`), a `Resume from <stage>` control on every
  stage card, the vitals line reading **`deploy behind · :s121`** and `spine reachable · bus
  reachable`, and the pending confirm flag carrying the broker-consequence wording verbatim
  ("re-running from portfolio manager will submit new orders at the broker").
- `bus-unverified.png` — served with `DASHBOARD_AZURE_CREDENTIAL_MODE=service_principal` and the
  `AZURE_SP_*` trio blanked: vitals read **`bus unverified`** and **`deploy unverified`**, the rail
  says "couldn't verify — retrying", and the master light stays GREEN — an unavailable Azure read
  never flips the light (decision 6).
- At capture time the newest successful main image build had advanced to run `29329555693`, SHA
  `a5bbb5ffd0a9fc47e192d228edc970cba5860f6f` (post-handback backlog merges); the judgement still
  read **behind** with `fleet_matches_record=true`, `main_matches_record=false` — the tripwire
  tracked main moving with no code change.
