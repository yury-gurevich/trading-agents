# Sprint 127 live proof

Date: 2026-07-15 AEST. Live systems: Neon PostgreSQL spine, dashboard operator path with
Anthropic-backed interpret, Azure Container Apps read APIs, GitHub Actions read API, and Alpaca
paper account untouched. Secrets and connection strings were not printed.

## Row 11 approve routing

Live operator interpret was run against the production spine for the 2026-07-14 misrouted approve
phrases. Each returned a typed `approve` intent with confirmation required and the same target
`broker-position-divergence:14df92eb501d:critical`.

| Phrase | Result | Retained audit nodes |
| --- | --- | --- |
| `approve broker-position-divergence:14df92eb501d:critical` | `family=approve`, `target=broker-position-divergence:14df92eb501d:critical` | `audit:753f6487336dde4c`, `intent:753f6487336dde4c`, `llmcall:753f6487336dde4c` |
| `please approve broker-position-divergence:14df92eb501d:critical` | `family=approve`, `target=broker-position-divergence:14df92eb501d:critical` | `audit:d607b17e502c83f8`, `intent:d607b17e502c83f8`, `llmcall:d607b17e502c83f8` |
| `confirm approval for broker-position-divergence:14df92eb501d:critical` | `family=approve`, `target=broker-position-divergence:14df92eb501d:critical` | `audit:dd7ce80835223924`, `intent:dd7ce80835223924`, `llmcall:dd7ce80835223924` |

The unit regression table also pins the neighboring `resume`, `run`, and `status` phrasings in
`agents/operator/tests/test_operator_approve_routing.py`.

## Row 10 dashboard flag acknowledgement

The live dashboard initially showed one stale S126 confirm-intent warn flag and one critical
broker-divergence flag. This differed from the sprint handover's older "three critical flags"
snapshot; the check touched exactly one warn flag and left the critical broker-divergence flag
pending for the operator.

- Acknowledged warn subject: `15bb3e29df185949`.
- Before state: pending count `2`; screenshot `flag-ack-before.png`.
- Confirmation dialog rendered the typed intent verbatim: `family=approve`,
  `parameters.target=15bb3e29df185949`, `requires_confirmation=true`; screenshot
  `flag-ack-confirm-intent.png`.
- After state: pending count `1`; `flag:15bb3e29df185949:warn` renders `resolved`; screenshot
  `flag-ack-after.png`.
- Remaining pending flag, not touched:
  `flag:broker-position-divergence:broker-position-snapshot:pm-run-cf94a4e7dc7644a89c9b08bd9b5eeca6:2026-07-14T22:33:39.068670+00:00:critical`.

Retained graph provenance from the acknowledgement:

- `audit:a77b5cf18683b893`
- `intent:a77b5cf18683b893`
- `llmcall:a77b5cf18683b893`
- `a77b5cf18683b893:approve` (`Message`)
- `flag:a77b5cf18683b893:warn`
- `resolution:flag:a77b5cf18683b893:warn`
- `resolution:flag:15bb3e29df185949:warn`

## Row 12 deploy currency

Live Azure read-only evidence showed the dispatcher judged by job template, with the last execution
kept as history:

- Deploy judgement: `current`
- Running tags evidence: `["s126"]`
- Retained deploy record:
  `deploy:2026-07-15T05:49:41.389151+00:00:s126:0773ae83ecc032f56dcd2af7bfec6248ca6048fe`
- Latest main image build: run `29392150781`, SHA
  `0773ae83ecc032f56dcd2af7bfec6248ca6048fe`
- Dispatcher template tag: `s126`
- Dispatcher last execution tag: `s121`
- Last execution start: `2026-07-14T22:30:00+00:00`
- Next fire: `2026-07-15T22:30:00+00:00`
- Screenshot: `currency-template-current.png`

The live check ran before the 2026-07-15 22:30 UTC fire, so the last execution still read `s121`.
That is the expected distinction: template decides currency, last execution remains visible as
evidence. The behind and unreadable cases are proven by the unit truth table in
`surfaces/tests/test_dashboard_template_currency.py`.

## Row 4 warning links

The dashboard warning-link click landed on the Flags panel and highlighted the target evidence.
Screenshot: `warning-link-flags.png`. Static regression coverage confirms every S124-S126 warning
code is mapped: `pending_flags`, `degraded_feeds`, `acceptance_warning`, `deploy_behind`,
`deploy_unverified`, `bus_unverified`, `bus_unreachable`, and `untracked_spend`.

## Row 9 optional Azure extra

A throwaway clean virtual environment without Azure packages ran
`tests/test_bus_azure_receiver_integration.py` and skipped rather than failed:

```text
SKIPPED [1] tests\test_bus_azure_receiver_integration.py:97: could not import 'azure.servicebus': No module named 'azure'
1 skipped in 2.38s
```

The throwaway environment was created under the system temp directory and deleted after the check.

## Retained and torn down

Retained:

- The row-11 `CommandAudit`, `Intent`, and `LLMCall` nodes named above.
- The row-10 `CommandAudit`, `Intent`, `LLMCall`, `Message`, warning `Flag`, and two
  `FlagResolution` nodes named above.
- The existing `DeployRecord` named above, which remains production deploy provenance.

Torn down:

- The local dashboard server was stopped and port `8327` was released.
- The throwaway no-Azure virtual environment was deleted.
- No broker order, broker position, Azure control-plane resource, or graph production state was
  deleted or overwritten.
