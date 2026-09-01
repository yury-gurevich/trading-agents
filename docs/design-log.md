# Design log — in-flight discussions, options, and what we ruled out

The home for design reasoning **before** it hardens into an ADR. Captures the question, the
options weighed (including the ones rejected and *why*), and the current status. This is the
LAW-05 ("every choice has a recorded why") and LAW-01 ("everything is a proposal") record for
threads that are discussed but not yet decided. When an entry resolves, it graduates to an ADR
and is marked CLOSED here.

---

## DL-141 - `not_required` is attributable only when the PM approved no buys - status: DECIDED (2026-09-01)

**The question.** [S191](sprints/sprint-191-a-quiet-night-gets-the-same-verdict-twice.md) found
that advisory acceptance can return opposite verdicts for identical quiet runs. If the empty
`DeliberationRun` lands before execution polls, execution records `deliberation_status="applied"`
and the stage passes. If it lands after execution polls, execution records
`deliberation_status="not_required"` and the same no-buy run fails
`deliberation.advisory_attribution: missing`.

**Decision 1 - `not_required` is attributable when the linked PMRun has zero approved buys.**
`not_required` is already part of the execution status vocabulary (`EXEC-OUT-09`) and ADR-0022 says
the veto gates buys, never exits. The acceptance reader therefore derives the missing fact from the
linked `PMRun.order_intent_set`: zero approved buys is attributable, including sells-only runs;
one or more approved buys is still a breach. The payload is readable without a graph-vocabulary
change: `orchestration.packs.trading_observatory_chain` already validates the same nested property
with `OrderIntentSet.model_validate(...)`.

**Rejected alternatives.** Adding `not_required` to the advisory status set globally was rejected
because it would also green-light a skipped veto on an exposure-opening buy. Conditioning on
`submitted == 0` or `approved_count == 0` was rejected because both misclassify sell-only runs.
Adding an `ExecutionRun` buy-count property was rejected because the fact is already derivable and a
new graph property would turn an image-only retag into a vocabulary deploy.

**Decision 2 - compute the buy count at the traversal boundary and keep attribution scalar.** The
view already walks `DeliberationRun <-DELIBERATED_BY- PMRun -EXECUTED_BY-> ExecutionRun`. It now
keeps the PMRun from that traversal, derives an approved-buy count, and passes that count into the
pure `_advisory_attribution(...)` helper. This keeps graph traversal out of the helper and avoids
any import from `agents.execution.deliberation_gate`.

**Rejected alternatives.** Putting the graph lookup inside `_advisory_attribution` was rejected
because it mixes traversal with a scalar policy check. Importing execution's `has_buy` was rejected
because orchestration can read contract-shaped graph facts directly and should not couple this
view to an agent implementation module.

**Decision 3 - the buy breach is named `buy_veto_missing`.** Existing unattributable cases keep the
`missing` token, while `not_required` beside an approved buy reports the sharper value. The check
shape stays the same (`oneof ("ok",)`), so downstream breach rendering still fails on any non-`ok`
value without a new acceptance primitive.

**Law-cycle answer.** No law cycle is owed. No `contracts/` file, graph vocabulary, env key, or
tunable changes. `EXEC-OUT-09` already declares `not_required`; `EXEC-OBS-04` states the
posture-severity rule and does not enumerate a status list that omits it. `DRIFT-056` was not filed.

---

## DL-140 - S172's K=4 concurrency measured at last, and it does not clear its own bar - status: MEASURED (2026-09-01)

**The question.** [S172](sprints/sprint-172-independent-debates-run-independently.md) has been
BUILT and gate-proven since 2026-08-20 and unmergeable ever since, because its success factors are
*measurements* and three attempts returned `real_debate_count=0` — twice on a dry vendor credit
balance, once on an OpenAI 429. Work-queue item 3 has carried it as "ready to prove, then merge".

**What was run.** Branch `sprint-172-k4-on-s190` (`fc36370`, `make ci` 2446 passed / 100.00 %,
`GATE PROVEN`) built as `s172b` and deployed to **the three deliberator apps only** — the other 13
stayed on `s190`, which is safe because the one shared-image file the branch touches,
`kernel/bus_azure_ready.py`, changes **type annotations only**. Peers at `maxReplicas=4`, manager
pinned at 1. Execution and PM were held at `minReplicas=0` so the synthetic orders could never reach
a broker. A 15-buy `PMRun` (`pm-run-s172k4-a`) was seeded into `sched-2026-08-31`'s **real** analyst
chain so `build_veto_context` rendered genuine analyst, scanner and market evidence rather than
`Lineage: no AnalystRun linked`. 🪤 **15 orders is synthetic on purpose** — real nights have produced
9, 9, 7, 5, 4, 4 and 3, so the 15-order breaking point has never occurred naturally and never will
on demand.

**The run is trustworthy, which is the part the previous three attempts could not establish.** All
**69** `LLMCall` rows are `claude-opus-5` with `stop_reason=end_turn`: no fallback, no throttle, no
truncation. 13 of 15 orders produced real debates.

**Measured 2026-09-01, `pm-run-s172k4-a`, seeded 05:53:34 UTC, complete 06:07:08 UTC.**

| Postcondition | Target | Measured | |
| --- | --- | --- | --- |
| span / sum-of-latency | **0.25** (1/K) | **0.67** (raw `sum/span` 1132.5 s / 760.9 s = 1.49) | red |
| 15 orders inside the 1800 s grace | 15 debates, no `DeliberationGraceExpired` | **815 s** end-to-end, 985 s headroom, no grace fault, but only **13** real debates | amber |
| `orphaned_reply_count == 0` | 0 | **6 orphaned peer replies dead-lettered** | red |
| Fault isolation | isolated | **2 of 15** lost their peer reply entirely (AAPL, BAC) | red |

🚨 **The success factor as written cannot be satisfied in the direction it names, and this is a spec
defect worth fixing before anyone re-runs it.** Success factor 1 says the ratio *drops* from the
0.95 measured on 2026-08-19 to about 0.25. But if 0.95 is the **serial** baseline, then
`sum-of-latency / span` must **rise** under parallelism, not fall — perfect K=4 would read ~4.0, not
0.25. The only orientation in which both numbers are coherent is **span / sum-of-latency**: serial
about 1.0, perfect K=4 about 0.25. Read that way the honest figures are **0.95 -> 0.67**, i.e.
**effective concurrency about 1.5x, not 4x**. Whoever re-runs this must state the orientation.

🚨 **The speed miss and the lost replies are very likely one defect, not two.** The manager
dead-lettered replies while waiting on *named* correlation keys — `SCHW:defender:r2`,
`INTC:challenger:r2`, `BAC:challenger:r1`, `NFLX:challenger:r1` (2) and `NFLX:challenger:r2` — so
replies are arriving for debates it is not currently waiting on, being discarded, and two orders
then time out with `RuntimeError: no deliberator peer reply received`. That is S171's correlation
guarantee **failing under concurrency**, which is the very thing S172 exists to establish; and a
manager that serialises on waits while throwing away replies it will later need is a sufficient
explanation for 1.5x instead of 4x.

**Consequence for item 3.** The branch is **not mergeable on this evidence**. It is no longer
blocked on an instrument, though — the instrument now exists and is repeatable, and the failure has
named correlation keys to work from. The K=1 determinism replay (success factor 3) was **not run**:
determinism is moot while 2 of 15 debates are lost.

**Ruled out, with reasons.**
- **Merging anyway because wall-clock improved.** Rejected: 815 s vs a projected 1,854 s is real, but
  success factor 4 is `orphaned_reply_count == 0` and it measured 6. Shipping a veto that silently
  discards peer replies is worse than a slow one.
- **Raising `debate_concurrency` above 4 to buy speed.** Rejected: the losses are correlation
  failures, so more concurrency would produce more of them.
- **Running K=1 for the determinism comparison anyway.** Rejected as premature, and it costs a second
  full Opus debate set.

**Teardown.** `pg_teardown --prefix s172k4 --contains` removed **67 edges / 71 nodes** (the PMRun,
its DeliberationRun and 69 LLMCall rows). `sched-2026-08-31` re-traced 8/8 and its AnalystRun is
intact. The fleet is back to **16/16 on `s190`** with scale config diffed identical to the
pre-measurement baseline.

---

## DL-139 - Execution's broker facts get one liveness predicate, derived not written - status: DECIDED (2026-08-31)

**The question.** [DL-131](design-log.md) closed with *"one predicate module for execution's broker
facts is the durable answer, and it is a sprint, not a patch"*, folding in [DL-129](design-log.md)
and [DL-130](design-log.md). Before packaging that as [S190](sprints/sprint-190-one-liveness-question-one-answer.md),
the three rows' numbers were re-measured against the live spine, because all of them were seven days
old and two had already been retracted once.

**Re-measured 2026-08-31, read-only `SELECT`s on the Neon spine** (main worktree, `.env` present;
nothing written, the fleet untouched):

| | 2026-08-24 | **2026-08-31** |
| --- | --- | --- |
| `BrokerStopOrder` nodes / reading live | 25 live | **46 total, 29 live** |
| Active `Position`s (`is_active_position_node`) | 24 | **28** |
| `BrokerStopIdentityMismatch` faults | 228 | **304** |
| …**distinct order keys behind them** | 13 | **17** |
| `Fill` nodes / genuinely open | 243 / 27 | **259 / 29** |

🚨 **Two carried claims are corrected.**

1. **DL-130's "13 objects, not a growing fault" is wrong.** It is **17** seven days later — AVGO,
   AMZN, MSFT, WFC, INTC, AMD and XOM joined the original ten, one per stop that died. The
   *repetition* count tracks how many sweeps ran; the *object* count tracks stop-outs, and it grows.
2. **DL-129's leftover — "24 open Fills carry no `submitted_at`" — is not a mystery, it is a naming
   collision.** **28 of the 29** open Fills are **resting stops**: `_write_stop_fill` never writes
   `submitted_at`, and a GTC stop that has not fired is `pending` by design, forever. Exactly **one**
   is a real order. So "open fill" needs two predicates, not one, and item 12's Fill half is a
   vocabulary defect rather than a backlog.

**The finding that decides the design: the graph already holds the answer.** *[measured]* **Every one
of the 46 `BrokerStopOrder` nodes has a `Fill` at the identical node key — 46/46, zero missing.** The
live specimen:

```text
BrokerStopOrder stop:87403939105c0a24:PYPL   cancelled_at absent  -> reads LIVE
Fill            stop:87403939105c0a24:PYPL   broker_status filled -> since 2026-08-28
                                             realized_pnl_cents -9758
Position        broker:PYPL:...              broker_absent true   -> correctly inactive
```

Three siblings, one truth, and only `Position` reads it correctly. **A further 7 stops carry
`cancelled_at` whose own `Fill` says `filled` — and in 7 of 7 the fill was recorded 1-3 days
*before* the cancel**, so this is not a fill/cancel race: `reconcile_broker_stops` eventually notices
the position is gone, cancels an order that already filled, and the graph records a stop-out as
*cancelled by us*. The lifecycle has one word for three endings.

**DECISION 1: liveness is derived from the sibling `Fill`, never written onto the stop.** The join is
by identical key with a `broker_order_id` fallback — the pairing `drop_sweep._tracked_as_stop` already
uses. When the sibling Fill is missing (0/46 today) the stop is treated as **live**, so the existing
`UnprotectedPosition` path speaks rather than a position silently losing protection.

**Rejected: add `filled_at` / `resolved_at` to `BrokerStopOrder` and write it when the stop fires.**
It is the obvious fix and it is the defect. The fact already exists at the identical key, so writing
it again denormalises lifecycle a third time — precisely what DL-131 named as the shape. R007 §5 is
explicit that a derived row is indistinguishable from an observed one at read time, and it needs a
new writer in the run path: more blast radius for less truth. 🎯 **[DRIFT-029](laws/drift-register.md)
had already reached the same end-state** — *"a current-status read model derived from
`BrokerOrderStatus` facts rather than a mutable Fill status"* — so this decision is that row being
honoured, not a new direction.

**Rejected: three separate patches, one per DL row.** DL-131's actual finding is that they are one
shape; three patches leave the fourth instance free to appear.

**Rejected: suppress or resolve the 304 faults.** DL-130's decision stands — the detector would keep
manufacturing the class for every stop that dies.

**Measured while looking, recorded so nobody re-derives it.** The mismatch fault carries **no context
at all** (0 of 304): the order key exists only inside the message string, which is why DL-130's
"13 distinct keys" needed a regex over free text. And **5,762 of the 6,393 `Fault` nodes** are a
single `execution/poll::position_sync` `ValueError` burst on 2026-07-30/31 — one dead incident, a
month old, that distorts every fault-population percentage anyone quotes. Neither is S190's job; both
change how its numbers should be read.

**S190 amendment (2026-08-31).**

**DECISION 2: use named broker-lifecycle vocabularies, and keep `partial` non-terminal.**
One status set cannot honestly serve every call site: broker order records use cancellation/expiry
terms, while `Fill.broker_status` settlement is the narrower `filled`/`rejected` boundary required by
`EXEC-STA-05`. S190 therefore keeps the vocabularies together in `contracts/broker_lifecycle.py`, but
as separate named sets. `partial` and `partially_filled` are not terminal for refresh/liveness, and
`agents/execution/run.py`'s `COMPLETED_EXIT_STATUSES` remains a different exit-completion policy.

**DECISION 3: a resting stop is identified by the semantic `stop_order_key` property.**
`key LIKE 'stop:%'` and `props ? 'stop_order_key'` match the same production population today, but
the property says what the fact is while the key format says how it happened to be named. The open
order predicate excludes resting-stop Fills by that property, so the next audit cannot read a GTC
protective stop as a broker order backlog.

**DECISION 4: the lifecycle module lives in `contracts/` and imports no agents.**
The predicates take a `GraphStore` and `Node`, matching `contracts/positions.py`, because both
execution and reporter need the same read model. Moving the vocabulary down avoids an import-linter
edge from contracts to agents and keeps the broker-lifecycle question available to readers without
sharing execution internals.

**Status.** The remaining design decisions — the terminal vocabulary (🪤 `partial` must stay
non-terminal or S176 is re-broken), the open-order/resting-stop discriminator, and the module's
import surface — are specified in S190 and are to be **appended to this entry**, not opened as a new
row.

---

## DL-138 - S189 temporarily baselines S188 main CodeQL alerts - status: DECIDED (2026-08-31)

**Context.** S189 pushed green on the regular CI workflow, then `Security Findings` failed because
the repo still had three open error-level CodeQL alerts on `main`: #189, #190 and #191,
`py/unsafe-cyclic-import`, all raised by S188's master credential-probe split. S189 now carries the
actual code repair: `HttpProbeRequest` moved to `credential_probe_support.py`, `credential_probes.py`
re-exports it deliberately, and `credential_probe_transports.py` type-checks against support rather
than importing back through `credential_probes.py`. That removes the cycle in the branch, but the
alerts themselves can only close after CodeQL analyzes the fix on `main`.

**Decision.** Add the three stable CodeQL finding keys to `security/findings-baseline.json` as a
temporary acceptance of already-open `main` alert state, while keeping `--fail-on-code-scanning-error`
enabled. This lets the branch gate prove there are no additional unbaselined error-level findings
before merge, without pretending the branch has closed alerts that only `main` can close.

**Rejected routes.** Rejected: disable the security ratchet or loosen the workflow, because that would
hide genuinely new findings. Rejected: merge a red branch and call it green, because S189 can use the
workflow's documented "re-baseline deliberately" exit instead. Rejected: dismiss the alerts in the UI
from this branch, because the code fix has not yet been analyzed on `main` and the intended cleanup is
to prune the baseline after post-merge CodeQL marks the alerts fixed.

## DL-137 - S189 LLM stop reasons are adapter facts and kernel policy - status: DECIDED (2026-08-30)

**Context.** S189 found 135 empty `LLMCall` completions, 11 of them judge calls, with no stored stop
reason. The direct `correlation_id` is an internal `pm-run-*`, so the DL-119 contamination question
has to be answered through graph lineage: one empty judge call, `pm-run-61025f7ffe254ae08b16f2adbaa456a7:AMZN:judge`,
descends from `verify-2026-08-19-clean`; the other three DL-119 binding runs have zero empty judge
calls.

**Decision 1 - adapters extract stop metadata; the kernel owns completion policy.** Anthropic and
OpenAI are the only code that can read `stop_reason` / `finish_reason` without guessing, so they set a
small `last_stop_reason` side channel and raise a shared sanitized exception for vendor-declared
truncation or refusal. `kernel.deliberation` still owns the semantic rule that an empty debate turn is
not a turn, and that a stopped judge response defaults to `revise`. Rejected: putting all checks only
in callers, because the vendor reason is already lost there. Rejected: putting all checks only in
adapters, because a normal `end_turn` with an empty string is a legitimate model answer at the port
level but not a valid debate turn. A future adapter must set `last_stop_reason` and raise the shared
exception when the vendor says the answer was cut off or declined.

**Decision 2 - the exception carries only sanitized stop metadata.** The shared exception carries
provider, stop reason, and an optional refusal category. It never carries prompt text, completion text,
API keys, or response payloads. Rejected: attaching the raw request/response for debugging, because
the fail-open reason is durable graph evidence and S188's credential evidence rule applies here too:
payload-rich errors turn observability into a leak path.

**Decision 3 - `max_tokens` keeps its default and gains an 8192 ceiling.** The default stays 4096; the
upper bound moves to 8192. That doubles emergency headroom for effort-heavy reasoning while remaining
bounded against runaway cost, and it is still far above the measured visible-answer median of 168 words
and max of 468 words. Rejected: 128K, because that needs streaming and is vendor-maximum thinking, not
etalon evidence discipline. Rejected: leaving `le=4096`, because a tunable pinned to its default cannot
be used to reproduce or mitigate truncation in live proof. Rejected: treating the bigger ceiling as the
fix, because visibility is the fix; more budget is only an operator lever.

**Decision 4 - `LLMCall.stop_reason` is compact vocabulary, not payload.** Every ledger write carries a
`stop_reason` string: the vendor value when available, or `unknown` for clients that do not expose it.
The property is declared in `trading_graph_vocabulary.json` in the same change. Rejected: separate raw
metadata blobs or provider-specific fields, because this sprint needs the shared answer to "why did the
call stop?" and adding payload-shaped audit props widens the privacy and vocabulary surface.

## DL-136 - S188 credential tests are pack data with response-classified failures - status: DECIDED (2026-08-30)

**Context.** Master already has the DL-36 substrate shape (`CredentialTest`, `PassCache`, remediation
entry), but production passes zero tests into it. S188 wires tests into the deployed master without
breaking ADR-0012: the master image remains substrate-only, and trading-specific probes arrive as
pack data.

**Decision 1 - declaration-as-data with two substrate probe kinds.** The declaration is JSON loaded by
`MASTER_CREDENTIAL_TESTS_B64` or a local path, parallel to grant policy and secret map. The substrate
implements `http_status` and `dsn_select_1`; the trading pack chooses URLs, headers, expected statuses,
agent types, and required/optional posture. Rejected: importing `orchestration.packs.trading_vault_probes`
or provider SDK classes from `agents/master`, because that crosses the ADR-0012 wall and the master image
does not contain those modules. Rejected too: widening `CredentialTest` to consume the seed-time
`ProbeResult`; the substrate already owns a smaller activation-test interface.

**Decision 2 - credential failure is classified by response, not by exception.** An HTTP 401/403, or any
declared credential-failure status, means the credential itself was rejected; a required test in that
state refuses activation. Timeout, DNS/connect/reset errors and 5xx statuses are transport failures:
they are faulted and observed, but they do not refuse activation and they never cache a pass. Rejected:
fail-closing every probe exception, because that would let a transient network fault halt the fleet.

**Decision 3 - required means "this agent cannot perform its granted role without this credential."**
Provider requires Tiingo, its primary OHLCV source. Provider Finnhub/FMP/Alpaca-data probes are optional:
their failures degrade enrichment or fallback capacity but should not keep the fleet dark. Execution
requires Alpaca broker credentials because broker submission is its role. Operator and the three
deliberator roles require Anthropic because the live pack selects Anthropic; their OpenAI fallback is
optional until the provider setting makes it primary again. Rejected: mark every configured credential
required, which would turn a degraded optional feed or inactive fallback into a fleet-start outage.

**Decision 4 - cache only costly passes, with a five-minute default TTL.** Auth endpoints such as
`/v1/models` and lightweight feed probes are cheap enough to run on activation; the default pack marks
them cheap. The tunable `credential_pass_cache_ttl_minutes` defaults to 5 for any future costly test,
matching the existing secret cache horizon and bounding repeated probes across a 16-app activation wave.
Rejected: cache all passes indefinitely, because a stale cached pass could hide a credential that failed
moments later; rejected also: no cache support, because a later costly probe would force the old choice
between cost and coverage.

**Decision 5 - activation records test evidence on `AgentInstance`, not a new label.** Successful
activation writes compact props for tested, passed, cached, optional-failed, and transport-failed
credential names. Required failures still write `Escalation` and no `AgentInstance`, preserving the
PRE_FLIGHT refusal shape. The graph vocabulary must declare the new `AgentInstance` props in the same
unit of work. Rejected: a new per-probe graph label, because this sprint needs activation-level
handover evidence and a new label would expand ownership/vocabulary blast radius without changing the
decision.

**Measured boundary note.** `postgres-dsn` is a seed-time credential probe today, but it is not currently
handed over by master in `ACTIVATE`; Container Apps injects `POSTGRES_DSN` as a secretRef outside
`MASTER_SECRET_MAP_B64`. `dsn_select_1` is still implemented and tested as substrate support, but the
S188 trading declaration is scoped to the credentials master actually hands over.

**AMENDMENT 2026-08-30, at merge review — decision 3's provider posture was inverted, and the reason
it gave is the superseded half of ADR-0006.** Decision 3 reads *"Provider requires Tiingo, its primary
OHLCV source"*, with `alpaca-data` optional. That is backwards.
[ADR-0006](decisions/0006-market-data-feed-strategy.md)'s **2026-07-04 amendment** — at the top of the
file, above the body it supersedes — routes runtime OHLCV to **Alpaca**
(`market_source_from_settings`, which batches many symbols per request) and makes **Tiingo the cheap
fallback and DL-37 lineage source**. The ADR's body still reads *"Primary live OHLCV (full universe):
Tiingo"*; that line is precisely what the amendment supersedes, and it is the line decision 3 was
built on. 🪤 **S111 recorded this same trap once already** — the law book had drifted ahead of the ADR,
and the fix was the amendment, not the body.

**Why it is not cosmetic.** As handed back, a dead `PROVIDER_ALPACA_*` credential would **not** refuse
provider activation: the nightly full-universe pull would silently fall back to Tiingo, whose
documented budget is **50 requests/hour and 500 unique symbols/month**
([`tiingo-usage-limits.md`](laws/tiingo-usage-limits.md)). One S&P-500 day exhausts the month, and 500
symbols at 50 req/hour cannot be pulled inside a night in any case. **So the fallback cannot absorb the
primary's loss** — and the credential the provider most needs gated was the one left optional. The
mirror error costs too: a dead Tiingo key, which harms offline lineage work rather than the nightly
run, would have refused provider activation outright. 🪤 **The two Alpaca probes do not cover each
other** — provider reads `PROVIDER_ALPACA_API_KEY`/`_SECRET`, execution reads
`EXECUTION_ALPACA_API_KEY`/`_SECRET_KEY`, so `alpaca-broker` being required on execution does not gate
the provider's data path.

**Corrected before merge:** `provider.alpaca-data` → `required: true`, `provider.tiingo` →
`required: false`, and the posture is now pinned by an assertion in
`test_trading_credential_tests_load_to_nonzero_count` rather than by a JSON field nobody diffs.
🟢 **Decision 3's rule is unchanged and was right** — *"required means this agent cannot perform its
granted role without this credential"*. Only its application to the provider was wrong, and only
because it was applied against a superseded sentence.

**Known wart, deliberately NOT fixed here: `credential_failure_statuses` is inert.** In `_http_runner`,
`if status in failure_statuses or 400 <= status < 500: return credential_failed(...)` is followed by an
identical unconditional `return credential_failed(...)`, so the declared list changes nothing — every
non-expected, non-5xx status is a credential failure either way, and all 12 pack declarations of it are
no-ops. 🟢 **The behaviour is correct and fail-closed**: the statuses that actually mattered in the
outage, Anthropic `400` and OpenAI `429`, are caught. So this is not a defect in what the system does —
but it is a declared knob that does nothing, inside the sprint about declarations that do nothing.
🪤 **Do not "fix" it by making the branches differ without choosing.** The two honest options are to
**delete the field** (12 pack declarations plus two code lines), or to **give it the one meaning it
could have** — let a declared status override the `>= 500` transport rule, so a vendor that returns
`503` for a revoked key can be declared as a credential failure. Left undecided on purpose; it is a
design choice, not a typo, and nothing depends on it today.

**What the flip's own test failure taught, kept because it is the load-bearing check.** Flipping
`alpaca-data` to required broke two `test_master_entrypoint` fixtures with
`ActivationRefused: ... ['alpaca-data']` even though their transport was stubbed to return `200`. The
cause is upstream of the transport: `_http_runner` renders headers from the resolved config first, and
a `KeyError` there becomes `credential_failed("missing_config:PROVIDER_ALPACA_API_KEY")`. 🟢 **A missing
credential is a credential failure — correct, and it is what made the flip worth verifying rather than
assuming.** Checked before keeping the change:
`orchestration/packs/trading_secrets.json` maps `alpaca-key-id → PROVIDER_ALPACA_API_KEY` and
`alpaca-secret-key → PROVIDER_ALPACA_API_SECRET` for `provider`, and **both secrets exist in
`trading-agents-kv`** (names listed, values never read). So master resolves and probes them at
activation, and required is safe. The fixtures now seed both.

🪤 **The accepted cost, stated plainly: a required probe turns a rotted probe URL into a fleet halt.**
If Alpaca moves `/v2/stocks/AAPL/trades/latest`, provider activation refuses on a `404` that is a
config error, not a credential one. 🟢 This is **not a new class of exposure** — `alpaca-broker`
(required, execution) and `anthropic` (required, on all three deliberators) already carry exactly it;
the flip makes the provider consistent with them instead of an exception. If that exposure is ever
judged too sharp, the fix is a third outcome for *"the probe itself is misconfigured"*, not a retreat
to optional.

---

## DL-135 - Monday's run goes first, and two measurements shrank what it has to prove - status: DECIDED (2026-08-30)

**Decision - `sched-2026-08-31` runs on `s187` untouched; S172's K=4 measurement happens after it,
not before.** Item 3 is unblocked and is the first buildable item, but its measurement needs `s172`
images and peer `maxReplicas=4` on the fleet - unmerged code, reversible by retag (**to `s187` now**,
not the `s182` the queue row still names). Deploying that before Monday would spend the only
instrument that can prove today's deploy *and* the credential path. The operator was offered the
inversion and took it.

**Ruled out - spend Monday on the K=4 measurement instead.** It would have moved the bigger item a
day earlier. Rejected because the credential path is the older unknown and the cheaper one to clear:
an unproven path makes the K=4 run return `real_debate_count=0` for the **third** time, and Monday
would no longer be a proof of `s187`. Sequencing costs a day; the alternative risks losing both.

**Two read-only measurements taken while deciding, both of which shrink Monday's unknown.**

1. 🟩 **The live fleet reads `anthropic`, not `openai`.** All three deliberator apps now carry
   `DELIBERATOR_LLM_PROVIDER=anthropic` (`az containerapp show`, 2026-08-30), with `EFFORT=high` and
   `REQUEST_TIMEOUT_SECONDS=120`. Today's `up -Tag s187` applied the switch that
   `orchestration/packs/trading_tunables.json` had carried as **staged but "NOT YET APPLIED LIVE"
   since 2026-08-20**. So Monday debates on **`claude-opus-5`** - the provider whose spend limit was
   actually raised - and **not** on the OpenAI fallback that carries item 35's silent-empty defect.
   🪤 That pack note is now stale in two ways ("not yet applied live", "both providers are currently
   non-functional") and is deliberately **left to be corrected inside S172's merge cycle**, which
   already touches that file, rather than editing production state for a comment.
2. 🟩 **The vault holds the key that works.** `anthropic-api-key` in `trading-agents-kv` is
   byte-identical to the `.env` value that returned `HTTP 200` today - compared by SHA-256, first 12
   hex `4f1e705379de`, values never printed and never written to disk.

**What is left for Monday to prove, stated narrowly.** Not *"is there a working provider"* and not
*"which one"* - both are now measured. Only **whether master resolves that vault secret and hands it
to the deliberator**: the one link in the chain with no test behind it, because
`credential_tests=()` ([DL-134](design-log.md)). Expect `real_debate_count > 0`,
`failed_open_count == 0`, and `deliberation_posture` on the `ExecutionRun`.

---

## DL-134 - The posture switch is not the decision DL-116 and DL-119 were arguing about - status: DECIDED (2026-08-30)

**Question.** Both providers returned to service on 2026-08-30 and the fleet is on `s187`, so
work-queue **item 6b** became a live decision for the first time rather than a no-op: flip
`deliberation_posture` from `advisory` to `binding` today, or not.

**Read the code before deciding, and it reframes the item.** `binding` bites in exactly one branch
and no other:

- `drop_vetoed` removes vetoed tickers **before** `apply_deliberation_posture` runs
  (`agents/execution/pm_execution.py:59`), so an **arrived veto is honoured identically under both
  postures** - asserted by `test_arrived_veto_is_honored_identically_under_both_postures`.
- `apply_deliberation_posture` returns the order set untouched unless the status is
  `proceeded_unvetoed`, i.e. **no `DeliberationRun` node exists at all** after the grace
  (`agents/execution/deliberation_posture.py:38`).
- `applied_failed_open` - a `DeliberationRun` *did* arrive but its reviews failed open - submits
  under **both** postures. Posture changes only the fault severity, warning -> error
  (`agents/execution/deliberation_faults.py:88`).
- Acceptance is where posture bites hardest: `binding` adds `debate_coverage >= 1.0` and
  `failed_open_count <= 0`; `advisory` asks only that the fail-open be attributed
  (`orchestration/packs/trading_deliberation_view.py:63-70`).

🚨 **Consequence.** Every degraded night of the outage was `applied_failed_open` - the deliberator
ran and its provider calls were refused, so the artifact existed. **`binding` would have blocked
zero orders on any of those nights.** What it would have done is turn each one into an acceptance
*error*. The veto binding at all is DL-116's grace change, in force since 2026-08-19 and untouched
by this switch; DL-119's 73 % is a rate over *arrived* verdicts and this switch does not move it by
one order. **So the switch is not "make the veto bind."** It is two narrower things: (a) halt buy
exposure when the referee is *entirely absent* after the grace, and (b) make acceptance strict about
coverage. Item 6b's framing - "that would leave the veto non-binding by default" - is wrong, and
this entry supersedes it.

**Decision - stay `advisory` through the 2026-08-31 run; flip on that run's evidence, not today.**
Two reasons, both about what is unmeasured rather than about posture:

1. 🚨 **The provider proof is from the wrong machine.** The 2026-08-30 `HTTP 200`s were direct API
   calls from the dev box. The deliberator receives credentials through master / Key Vault, and that
   path has not run since 2026-08-19. If it is still broken, `binding` makes acceptance red for a
   non-defect - **DL-125 repeated deliberately**, and that is the exact failure that ranked item 6
   first in the first place.
2. 🪤 **`proceeded_unvetoed` is the >=15-order branch, and its fix is unmerged.** Item 3 measured
   1,854 s against the 1800 s grace at 15 orders. Under `binding` the busiest nights are the ones
   that block every buy - and S172's `debate_concurrency=4`, the fix, is built and gate-proven at
   `5bf72c9` but not merged, pending its own K=4 measurement.

**Flip condition, so this is a check and not a second judgement call.** Flip when `sched-2026-08-31`
shows `deliberation_posture` present on its `ExecutionRun`, `real_debate_count > 0`, **and**
`failed_open_count == 0`. The third is what proves the Key Vault path; the first only proves the
fleet is on `s187`. If `failed_open_count > 0`, the credential path is the finding and the flip
waits on that, not on posture.

**Ruled out - flip today and let Monday prove it.** Tempting: the switch is one line, reversible,
and a binding referee is what DL-116 wanted. Rejected because it stakes the acceptance gate on an
untested credential path, and a red Tuesday would then be **indistinguishable** between "the referee
bound correctly" and "the fleet cannot reach a provider." Advisory records the same facts and keeps
that distinction readable. The flip costs one line whenever we want it; the ambiguity costs a day.

**Ruled out - make the flip wait on S172's merge as well.** Over-sequenced. Item 3 is already next
in the order and will most likely land before a 15-order night; making the flip a compound condition
produces a gate nobody checks. If S172 has not merged when the flip happens, the residual exposure
is one branch that no recorded run has approached - *[carried, not re-measured]* the approved-order
counts in items 3 and DL-119 are 9, 9, 7, 5, 4, 4 and 3 against a 15-order trigger. Named, bounded,
accepted.

🚨 **Discovered while writing this — there is no cheap probe, because DL-36 Piece A is not wired.**
`MasterAgent.__init__` takes `credential_tests: tuple[CredentialTest, ...] = ()`
(`agents/master/agent.py:57`) and the deployed entrypoint constructs it **without that argument**
(`agents/master/entrypoint.py:90-96`); no pack registers any. So the machinery that was built to
*"test every credential before handing it to an agent"* runs **zero tests** in the fleet, and
activation succeeding proves nothing about the provider path. 🪤 **That is exactly the check that
would have caught the 2026-08-19 outage at activation rather than at debate time** — six nights
earlier. It is also why the flip condition above has to be a whole scheduled run: **there is no
smaller instrument.** Not filed as its own row yet; it belongs with item 6b's evidence until the
2026-08-31 run says whether the path works at all.

**What this does not decide.** Whether `advisory` should ever be the *permanent* posture. It should
not: it is the setting that lets a referee outage pass acceptance, and living there indefinitely is
DL-104's back door by another name, which DL-119 refused. This entry buys one run's delay against a
named unknown, not a policy.

---

## DL-133 - S187 parameter declarations are checked against settings fields - status: DECIDED (2026-08-30)

**Question.** S187 closes the verified PARAM drift where law tables and settings fields disagree,
but the first all-agent reconciliation found broader pre-existing drift: 60 name-presence
differences before fixes, spread across provider 14/0, scanner 1/0, analyst 22/0, PM 0/1,
deliberator 1/0, execution 1/2, forecaster 7/0, researcher 3/0 and master 8/0. The check therefore
has to stop new drift without turning this small sprint into an accidental full law cleanup.

**Decision 1 - `provider.alpaca_data_feed` is `NO (mode selector)`.** The value chooses which Alpaca
market-data feed answers the request. That changes the vendor/entitlement route, not a value inside
one scoring or validation formula.

**Rejected alternatives.** Register it as a `tunable()` because SIP may be "better" - rejected
because feed choice changes the data source semantics and cost/entitlement boundary. Leave it as
undocumented config - rejected because it affects provider behaviour and must be visible in PARAM.

**Decision 2 - `provider.ingest_ohlcv_only` is `NO (mode selector)`.** It switches the provider into
the DL-29 OHLCV-only fast path and skips enrichment wholesale. That selects which ingestion workflow
runs; it is not a bounded experimental value inside one workflow.

**Rejected alternatives.** Treat it as a tunable because it can improve runtime - rejected because
an optimiser should not silently choose to remove fundamentals/news/sectors/earnings from the run.
Treat it as private config - rejected because the operator must see when enrichment is disabled.

**Decision 3 - make the CI check a baseline-backed hard gate, not a naive hard fail or warn-only
shadow.** The measured 60 differences prove a naive hard fail would block on work S187 is not doing.
The check will therefore carry an explicit legacy baseline for the current repo and fail only on
unbaselined drift; the legacy rows are still printed as warnings. Promotion trigger: retire the
baseline when the cross-agent PARAM backlog recorded from this measurement is corrected.

**Rejected alternatives.** Naive hard fail - rejected because it expands the sprint. Warn-only - rejected
because it would still allow the fifth drift to land green. Do nothing after fixing the four named
instances - rejected because DL-120 and S185 already proved manual audits are not enough.

**Decision 4 - compare name presence both ways plus the tunable-family declaration, but not default,
type or bound text.** Presence catches settings fields with no PARAM row and PARAM rows with no live
settings field. Family matching catches the scanner-shaped defect (`YES` rows must be registered via
the `tunable()` metadata, while `NO (...)` rows must not be), and it keeps deliberate mode selectors
green. Defaults, type strings and bounds are deferred because the law tables use human-readable units
and ranges; strict textual comparison would create false positives before the name/family contract is
stable.

**Rejected alternatives.** Name-only - rejected because it would miss `scanner.benchmark_ticker`.
Full default/type/bounds comparison - rejected for this sprint because it conflates declaration drift
with documentation-format drift.

## DL-132 - S186 sentiment de-duplication is batch-scoped and metric-visible - status: DECIDED (2026-08-24)

**Question.** [DL-127](design-log.md) already decided the policy: down-weight duplicated news
headlines by `1 / n_tickers` instead of dropping them. S186 has to decide the implementation shape
without moving the provider boundary, hiding the denominator, or changing the scanner composite
weights.

**Decision 1 - compute duplication weights in the analyst batch path, over the whole
`MarketData.news` batch.** `score_candidates` is the first analyst point that holds the whole news
batch and the scored candidate subset together, so it prepares a headline-weight map once and passes
it into candidate scoring. The denominator is every distinct ticker in `market.news` that carries the
exact headline, not just the tickers that survived to `CandidateSet`.

**Rejected alternatives.** Compute the count in `_parse_news` or the provider - rejected because the
parser sees one ticker at a time and the provider must serve raw news, not interpretation. Count only
candidate tickers - rejected because the committed `sched-2026-08-21` fixture proves that scope puts
`KO` at 0.600 instead of the measured 0.599.

**Decision 2 - exact headline string is the identity.** Re-measured on the committed fixture: exact,
whitespace-collapsed, casefolded, and mojibake-replaced+casefolded matching all produce the same
counts: 1,255 slots, 784 distinct headlines, 639 slots at `n >= 2`, 294 at `n >= 5`, 186 at
`n >= 10`, max `n = 19`.

**Rejected alternative.** Normalize on principle. It adds a hidden equivalence rule while changing
none of the measured counts on the evidence run. If vendor text drift later makes normalization
useful, that should arrive with a fresh measurement.

**Decision 3 - keep `sentiment_articles` as an unweighted scored-headline count and add
`sentiment_batch_weighted_articles` for the denominator actually used by the weighted mean.** The
old metric still tells the truth about article count. The new metric names both the weighted unit and
the batch scope, so DL-112's "same prefix, different units" failure is not repeated silently. Because
this adds a `sentiment_*` metric, the analyst law/test-plan cycle is owed in this sprint.

**Rejected alternatives.** Overload `sentiment_articles` to report weight - rejected because the name
would say articles while the value is fractional. Rename `sentiment_articles` - rejected because the
existing count is still meaningful and already consumed as an article count. Hide the weight - rejected
because the score would no longer be reconstructable from the visible metrics.

**Decision 4 - heavily duplicated all-news tickers keep a score.** The weighted mean remains
`sum(weight * sub_score) / sum(weight)`, so shrinking every headline's weight does not remove the
sentiment pillar as long as at least one headline has a lexicon word.

**Rejected alternative.** Treat highly duplicated headlines as absent sentiment. That is the dropped
headline policy under another name, and DL-127 rejected it because it silently changes the pillar mix.

---

## DL-128 - S185 deliberation posture is a mode selector and a recorded run fact - status: DECIDED (2026-08-22)

**Question.** The veto posture is currently inferred from timing: `deliberation_grace_seconds`
determines whether execution usually sees a `DeliberationRun` before it submits, while fail-open
reviews still submit and leave an error. S185 makes the posture explicit so the operator can choose
whether unavailable deliberation is advisory or binding.

**Measured before coding.** Reading the last ten live `ExecutionRun` nodes by their upstream
`PMRun.created_at` showed the newest scheduled runs as `applied_failed_open` with submissions:
`2026-08-20T22:42:21Z` submitted 3 and `2026-08-21T22:39:24Z` submitted 3. The same set also
contains one `proceeded_unvetoed` verification run on `2026-08-19T06:46:26Z`, submitted 9. So the
recorded graph proves why the evidence is noisy: unreviewed or failed-open orders can reach the
broker, but the posture that made that acceptable or unacceptable is not stored.

**Decision 1 - `deliberation_posture` is a mode selector, not a `tunable()`.** It chooses which
policy runs (`advisory` vs `binding`), not a value inside a formula. It is therefore a bare
`ExecutionSettings` field and a `PARAM` row with `NO (mode selector)`, following the existing
`order_price_tolerance_mode` and `stop_target_mode` precedent.

**Rejected alternative.** Register it with `tunable()`. That repeats the exact S183 trap in reverse:
a mode selector would enter the parameter optimiser as though it were a bounded numeric dial.

**Decision 2 - default/no-config is advisory; explicit binding drops buy exposure only when no
`DeliberationRun` exists after grace.** The live graph measurement showed the submit path is the
actual no-config behaviour: failed-open and one no-verdict verification run reached the broker. So
`ExecutionSettings` defaults to `advisory`, recording the posture and downgrading the expected
fail-open fault to warning. Under an explicit `binding`, a buy-carrying PMRun whose deliberation
never arrived is consumed with those buys removed, an error fault, and `deliberation_blocked_count`
on `ExecutionRun`. Sells in the same set still go through, because exits never wait. A linked
`DeliberationRun` with `failed_open_tickers` keeps the current S175 shape: it submits fail-open,
records `applied_failed_open`, and remains red unless the operator has declared advisory.

**Rejected alternatives.**

- Hold the whole PMRun for a later run - rejected because it reopens the DL-98 race and can strand
  exits beside buys.
- Block sells under binding - rejected by ADR-0017 and ADR-0022; delaying an exit costs control of
  the book.
- Treat failed-open reviews as clean under binding - rejected because the acceptance artifact would
  say the posture was honored while the review did not happen.

**Decision 3 - advisory acceptance asserts attribution, not debate coverage.** Under `binding`, the
existing `debate_coverage >= 1.0` and `failed_open_count <= 0` checks remain blocking. Under
`advisory`, fail-opens do not fail merely for being fail-open, but the stage must prove attribution:
the linked `ExecutionRun` records `deliberation_posture=advisory`, the failed-open reason is present
when failures exist, and the status is one of the known fail-open/no-verdict statuses rather than an
unexplained pass.

**Rejected alternative.** Make advisory pass everything. That would replace a gate that cries wolf
with a gate that cannot fail, which is a worse evidence artifact.

**Decision 4 - keep the five `deliberation_status` states and add posture as a separate axis.**
`deliberation_status` continues to answer what happened to the review (`applied`,
`applied_failed_open`, `not_required`, `waiting`, `proceeded_unvetoed`). `deliberation_posture`
answers what policy applied. The combination is the fact the operator needs.

**Rejected alternative.** Fold posture into new status strings such as `advisory_failed_open` or
`binding_blocked`. That recreates the original confusion by mixing the reason no verdict exists with
the policy that decided what to do about it.

---

## DL-131 - A stop that fires is never reconciled, because `cancelled_at` is the only lifecycle a stop has - status: DECIDED (2026-08-24)

**Found while proving item 27's protection coverage, not looked for.** *[measured 2026-08-24]* The
broker holds **24 positions and 24 open stop orders, 1:1, zero unprotected and zero orphans** - the
symptom that opened item 27 (22 positions, 19 stops, $2,147.76 unprotected on 2026-08-19) is gone.
But the graph holds **25** active `BrokerStopOrder` facts against the broker's 24.

**The extra one is `stop:9691904d478ed859:WFC`, and it did not fail - it worked.** The stop **fired**:
Alpaca reports `status=filled, filled_at=2026-08-21T17:00:44Z, qty=11`. WFC was stopped out. The graph
fact still reads `cancelled_at=None`, so `active_broker_stop_orders(graph)` returns it and will keep
returning it forever.

**The cause is that a stop has exactly one lifecycle marker and it is the wrong one.**
`contracts/broker_stops.py` defines active as `cancelled_at is None`. Cancellation is written; **a
fill is not**. So every stop-out from now on leaves a permanently "active" stop fact behind, and this
was simply the account's first one.

🪤 **The position side of the same event is correct**, which is what makes the gap precise rather
than general: graph active positions are **24**, matching the broker symbol-for-symbol, and WFC's
`Position` nodes still read `status: "open"` while `is_active_position_node` correctly returns
`False`. Positions have a predicate that encodes the real lifecycle; stops have a nullable timestamp.

**DECISION: record it as a defect now, fix it with the predicate it is missing.** A stop needs a
resolved/live distinction that covers *filled* as well as *cancelled* - the `is_active_position_node`
treatment, applied to `BrokerStopOrder`.

🚨 **This is the third instance of one pattern in a single sitting**, and the pattern is the finding:
**execution's graph facts each denormalise lifecycle differently, and only `Position` has a predicate
that hides it.** [DL-129](design-log.md) - `Fill.status` is immutable, truth is in `broker_status`,
and no `is_open_fill_node` exists, so an audit miscounted 202 open fills where 27 were open.
[DL-130](design-log.md) - `BrokerStopOrder` liveness is asked two different ways in one comparison,
producing 228 permanent faults. Here - a fired stop has no representation at all. 🪤 Do not fix these
one at a time without noticing they are one shape: **one predicate module for execution's broker
facts** is the durable answer, and it is a sprint, not a patch.

🟢 **No capital is at risk today** - protection is 1:1 and the stale fact belongs to a closed
position. The cost is that `active_broker_stop_orders` over-reports, and it will drift further with
every stop-out.

---

## DL-130 - The stop-identity check compares a type against a lifecycle - status: DECIDED (2026-08-24)

**The question (work-queue item 20).** `BrokerStopIdentityMismatch` has fired on every sweep for
12 days - 40 on 08-08, then ~10/run, then 24, 39, **52**, 13. The row asked whether the idempotency
key is reused across lots or the graph missed a status refresh, and said to decide that before
changing anything.

**Neither. The two sides of the comparison ask different questions** *[measured 2026-08-24]*:

| Side | `agents/execution/drop_sweep.py` | What it actually asks |
| --- | --- | --- |
| `broker_stop` | `order.order_type in {"stop", "stop_limit"}` | *is this order of type stop?* - **status is never consulted** |
| `graph_stop` | key in `active_broker_stop_orders(graph)` | *is this stop currently **active**?* - `cancelled_at is None` |

A cancelled stop is still **type** `stop`, so `broker_stop` stays `True` for the rest of the
account's life while `graph_stop` correctly goes `False`. **Every cancelled stop is therefore a
permanent, guaranteed mismatch**, and the population only grows.

**The numbers.** *[measured 2026-08-24]* The 228 faults are **13 distinct keys**, each re-raised
~20 times across 11 days, always in the same direction (`broker_stop=True graph_stop=False`). All 13
exist as `BrokerStopOrder` nodes and **all 13 carry `cancelled_at`, every one written on 2026-08-07
between 08:04:46 and 08:04:51** - a single cancel event. 🪤 **The graph and the broker agree
completely**: the same orders read `status=canceled` at Alpaca with the *same* timestamps. Nothing is
diverging.

**Why it recurs forever.** `AlpacaBroker._list_orders` queries `status=all&limit=500`
(`agents/execution/alpaca.py:155`). *[measured]* that returns **242 orders spanning 2026-06-16 to
2026-08-21, 136 of them `canceled`* - the entire account history, not a recent window. So the sweep
re-examines every dead order on every run, and re-raises a new `Fault` node for each of the 13.

🚨 **The row's own description was wrong on both halves.** It read *"the broker holds the stop open
(`broker_stop=True`) while the graph `Fill` for the same key reads `broker_status=rejected`"*. The
broker does **not** hold them open - they are `canceled` - and **no `Fill` is involved**: the
comparison is order-type versus `BrokerStopOrder.cancelled_at`. 🪤 The row also called the rate
unstable and suspected it tracked "how many stops the sweep saw". It does - the count is how many
sweeps ran, not how many stops mismatched. Only 13 objects have ever mismatched.

**DECISION: fix the predicate, not the data.** `broker_stop` must ask the same question as
`graph_stop` - a terminal order (`canceled`, `expired`, `filled`, `rejected`) is not a live stop.
Then the 13 stop matching, the exemption stops being granted on dead orders, and the fault becomes
capable of meaning something.

**Rejected: suppress or resolve the 13 faults.** `FaultSuppression` and `FaultResolution` exist and
would silence the noise, but the detector would keep manufacturing the same class for every stop
cancelled from now on. Suppressing a predicate that cannot be right is how a warning channel dies.

**Rejected: narrow the `status=all&limit=500` window.** It would reduce the rate and hide the defect
without fixing it, and the window has other consumers. 🪤 Worth knowing separately: at 242 orders the
500 cap is not yet binding, but it will be, and nothing watches for that.

🟢 **Severity is unchanged - `warning`, and no capital is at risk.** The exempted orders are already
dead. The cost is 228 unresolved fault records burying real ones, growing every run.

---

## DL-129 - `Fill.status` is a submit-time fact, so the "pending backlog" is not a backlog - status: DECIDED (2026-08-24)

**The question (work-queue item 12).** The item reads *"the pending backlog is growing, not
shrinking - 202 pending Fills, not ~122, of 211 total, and 121 carry `broker_status=rejected` while
still reading `status=pending`"*. Measured against the live spine 2026-08-24 the population is
larger again - **243 Fills, 138 `pending`/`rejected`, 67 `pending`/`filled`, 27 `pending`/unset** -
which reads as a backlog growing on two fronts.

**It is not a backlog. `Fill.status` is immutable by design.** `agents/execution/order_status_store.py`
states it in its own docstring: *"record broker order-status reads **without mutating existing Fill
facts**"*. `status` is what the broker said at submit; the refreshed truth is denormalised onto
`broker_status` and evidenced by append-only `BrokerOrderStatus` nodes linked `REFRESHES` - **3,725
of them** *[measured 2026-08-24]*. Both consumers agree: `refresh_pending_fills`
(`agents/execution/reconciliation_store.py:42`) selects `status == "pending"` and then **skips any
Fill whose `broker_status` is already terminal**, and `agents/execution/run.py:97` and
`filled_entry_stops.py:126` both read `broker_status` with `status` only as a fallback. A Fill
reading `pending`/`filled` is a correctly recorded, fully resolved fill.

**The real open set is 27 of 243** *[measured 2026-08-24]* - `status == "pending"` **and**
`broker_status` not terminal, which is exactly what the sweep retries. Three are from
`sched-2026-08-21`, i.e. the newest run's normal in-flight orders. 🪤 The other **24 carry no
`submitted_at` at all**, which is a separate and much smaller question than the one item 12 asks.

**So item 12's Fill half is corrected, not closed.** What survives is: why do 24 open Fills have no
submit timestamp, and does the sweep ever resolve them or do they age forever? That is a diagnosis,
not a sprint. The `pg_teardown` delete path, the item's other half, is untouched by this.

🚨 **This is the [DL-73](design-log.md) class, and the second time it has cost something.** That row
audited `Position.status` - which stays `"open"` by design - and raised a false red-severity defect;
the rule it produced was *never audit the graph on raw props, use the contracts predicate*. Item 12
did the same thing to `Fill.status`. 🪤 **`Fill` has no equivalent predicate** - `contracts/positions.py`
exports `is_active_position_node`, and `contracts/execution.py` only types the literal. The durable
fix is an `is_open_fill_node` predicate beside it, so the next audit cannot make this mistake a third
time. Recorded here rather than specced: it is one function and belongs to whichever sprint next
touches execution contracts.

---

## DL-127 - Contaminated news is down-weighted, not dropped - status: DECIDED (2026-08-22)

**The question ([DL-117](design-log.md), work-queue item 26).** Finnhub `/company-news?symbol=X`
returns market-wide content and `_parse_news` applies no relevance test, so a headline filed under
twenty tickers counts once, in full, for each of them. `score_sentiment` is an **unweighted mean**,
so contamination moves the number. The fix is cheap and vendor-independent - cross-ticker duplication
is computable from the batch at zero API cost - but the *shape* was undecided: **drop** headlines
filed under >= N tickers, or **down-weight** them.

The operator delegated the choice on the grounds that the downstream effect was not visible from the
question. It is now measured, so the choice is made on evidence rather than taste.

**Measured on `sched-2026-08-21`'s real news** - 98 tickers, 1,255 headline slots, 784 distinct
headlines. 🚨 **Two carried numbers in the work queue were wrong and are corrected here:**

| Claim | Carried | Measured 2026-08-22 |
| --- | --- | --- |
| slots filed under >= 5 tickers | 19 % | **23.4 %** |
| tickers left with no sentiment at all by a drop | "1 ticker" | **4** - `CMCSA`, `GD`, `PEP`, `TXN` |
| slots filed under >= 2 tickers | 48 % | **50.9 %** |
| slots filed under >= 10 tickers | - | **14.8 %** |

**The decisive comparison** ran both policies through the real pipeline - sub-score, mean, composite
(`tech 0.5 / fund 0.3 / senti 0.2`, renormalised over present pillars), `confidence = 0.3 +
composite x 0.6` - against the 0.600 regime floor. 🪤 The recomputed baseline reproduced **every**
stored confidence to three decimals, which is what makes the deltas trustworthy.

| | drop at N>=5 | down-weight 1/n |
| --- | --- | --- |
| tickers that lose sentiment entirely | **4** | **0** |
| headline slots discarded | **23.4 %** | none |
| raw sentiment moved > 10 pts | 10 tickers | 25 tickers |
| mean absolute sentiment shift | 3.98 pts | 6.87 pts |
| **max downstream confidence shift** | **0.0654** | **0.0338** |
| floor crossings at 0.600 | 1 (`CMCSA` 0.638 -> 0.573) | 1 (`KO` 0.605 -> 0.599) |

**DECISION: down-weight each headline by `1 / n_tickers`.** Five reasons, in order of weight:

1. **It costs no ticker its signal.** Drop silences four; down-weight silences none. The single
   stated objection to acting at all - *"leaves a ticker with no signal"* - disappears entirely, and
   it was **four times larger** than the carried number said.
2. **It uses all the evidence.** Drop discards 23.4 % of the slots the provider already paid for.
3. 🚨 **It is gentler on the decision boundary while being more informative.** Down-weight moves
   *more* tickers on raw sentiment (25 vs 10) yet its worst downstream confidence shift is **half**
   drop's (0.034 vs 0.065). It redistributes; drop lurches.
4. **Drop's one floor crossing is an artefact of information loss, not a correction.** `CMCSA` falls
   0.065 and crosses the floor **because it has no sentiment left**, so the composite renormalises
   onto technical+fundamental. The decision changes for a reason that has nothing to do with news
   quality. Down-weight's crossing is `KO` at **0.599 against a 0.600 floor** - a genuine borderline,
   moved by a hair.
5. **It has no threshold to tune.** `N=5` is arbitrary: 50.9 % of slots qualify at `>=2`, 37.5 % at
   `>=3`, 23.4 % at `>=5`. Any N is a magic number needing a `why` and an owner. `1/n` is
   parameter-free, so it cannot drift and cannot be quietly retuned.

**Rejected: drop at N>=5.** Reasons 1 and 4 above. It is also the option that *looks* more decisive
and measures worse - the pattern this log keeps recording.

**Rejected: leave it alone.** [DL-117](design-log.md) already retracted the alarming framing (*"mis-
attributed news is buying stocks"* was wrong - contamination is **bidirectional noise**, and every
approved order scores *higher* once it is removed). But bidirectional noise still mis-ranks, and the
scanner ranks on this. Zero API cost, no vendor dependency, and now a measured downstream bound.

**Recorded as a road not taken: `1/sqrt(n)`.** A softer discount, defensible if `1/n` proves too
aggressive on genuinely multi-name events (an index-wide selloff *is* news about each constituent).
Not chosen because nothing measured suggests `1/n` is too aggressive - its downstream shift is
already the smaller of the two - and adding an exponent reintroduces the tunable that reason 5
removes. Revisit only with evidence, not taste.

🪤 **The weight belongs in the mean, not in the parse.** `_parse_news` must keep returning every
headline: the duplication count is a property of the *batch*, not of a headline, and the parser sees
one ticker at a time. Computing it there would need cross-ticker state in a per-ticker function.

**Amended 2026-08-24 - the denominator's scope is part of the decision, and it was not stated.**
Preparing the S186 handover surfaced a constraint this entry left implicit: **`n` must be counted
over the whole `market.news` batch, not over the scored candidate set.** On `sched-2026-08-21` the
provider returned news for **98** tickers while the analyst scored **28**, and the two denominators
disagree on the result that decides the sprint - *[measured 2026-08-24]* `KO` lands on **0.599**
counted over 98 and on **0.600** counted over 28, so the single floor crossing this entry rests on
exists under one scope and vanishes under the other. Both are "1/n over this batch" in prose; only
one reproduces the measurement. The run's news and the analyst baseline it produced are now committed
as `agents/analyst/tests/data/news_sched_2026_08_21.json` so the claim is checkable without graph
access - on extraction the unweighted recompute reproduced **28/28** stored confidences to 3 dp.

---

## DL-126 - S183 skipped filters and stop basis are explicit - status: DECIDED (2026-08-20)

**Question.** The scanner and analyst both had values the deliberator had to infer around: a missing
scanner filter name could mean "passed" or "not evaluated", and a stop percentage did not name
whether it came from the flat champion or the ATR-scaled challenger.

**Decision 1 - carry "not evaluated" as a sibling field.** Add `skipped_filters` to `Candidate` and
`FilterVerdict`, preserving `survived_filters` as only the filters that actually evaluated and
passed. The debate packet renders both lists by name. `Candidate` has no property-enforced property
list in `orchestration/packs/trading_graph_vocabulary.json`; the durable scanner payload is the
typed `CandidateSet` stored on `ScanRun`, so no vocabulary-pack move is required.

**Rejected alternatives.**

- Encode suffixes such as `earnings_window:not_evaluated` inside `survived_filters` - rejected
  because it turns a list of names into a parse convention and violates DL-113's "value names its
  own meaning" rule.
- Add a new `FilterVerdict` graph label - rejected again under the S165 law reading:
  `SCAN-IDN-02` owns only `ScanRun` and `Candidate`, while `SCAN-OBS-01` already makes the
  persisted `CandidateSet.filter_trace.verdicts` the lawful audit carrier.

**Decision 2 - split no data from no upcoming/past earnings.** A missing earnings entry records
`earnings_window` in `skipped_filters`. A known date outside the exclusion window, including a known
past date represented by a negative `days_to_earnings`, records `earnings_window` in
`survived_filters`. Near future earnings still drop the ticker. This is additive for approvals:
unknown earnings no longer reads like a pass, but it still does not drop a candidate in S183.

**Rejected alternative.** Drop unknown-earnings tickers now. That would be a real trade-decision
change across the normal case, because the measured S183 run had earnings dates for only 10 of 98
tickers. S183 is an attestation fix, not an earnings-coverage promotion gate.

**Decision 3 - do not mark normal thin earnings coverage as provider degradation in S183.** Sparse
earnings coverage is normal for the current feed shape, while `quality.notes` is used for provider
health/degradation. The scanner now records the per-ticker truth the deliberator needs. A future
coverage score may be useful, but a batch-level `earnings_degraded` note here would conflate
"vendor has no date for this ticker" with a broken feed and could look like a whole-batch outage.

**Decision 4 - the stop attests from existing analyst evidence, with the selector unchanged.**
Leave `stop_target_mode` exactly as the locked analyst law declares it: a non-tunable mode selector
defaulting to `"flat"`. Render the already-durable `StopTargetEvidence` in the debate packet:
selected mode, ATR availability, ATR value, applied stop/target, and counterfactual mode. No new
`Recommendation` properties are needed; `stop_target_mode`, `stop_target_volatility_present`, and
`stop_target_volatility_fallback` are already in the graph vocabulary.

**Rejected alternatives.**

- Register `stop_target_mode` as `tunable()` - rejected by the corrected S183 spec and the locked
  analyst law. It selects which formula runs, not a value within one.
- File law drift against the selector row - rejected because `DL-120` established the law row is
  correct.
- Flip the default to `scaled` - rejected as out of scope. That is a champion-vs-challenger
  experiment that changes proposal values.
- Add a second stop-basis carrier outside `StopTargetEvidence` - rejected because it would duplicate
  the S150 evidence that is already persisted and vocabulary-declared.
## DL-125 - The falsifiable test was blocked by a billing failure, and the referee is down until 2026-08-30 - status: MEASURED (2026-08-22)

🚨 **ADR-0023's prediction could not be tested, and will not be testable for about six sessions.**

**What was supposed to happen.** S184 shipped issuer aggregation and a measured correlated-cluster
cap precisely so the deliberator's exposure objections - cited on four consecutive nights, 4 of the
6 vetoes on the clean run - would stop being true. The prediction was that the **73 % veto rate
falls materially** ([DL-119](design-log.md)). Only a live run can show it. `sched-2026-08-21` was
that run: unattended, on the production path, fleet verified on `s184`.

**What happened.** The run completed **8/8 stages** and failed acceptance:

```text
ACCEPTANCE  FAIL
  FAIL  deliberation.debate_coverage: 0.0 < floor 1.0
  FAIL  deliberation.failed_open_count: 3 > ceiling 0.0
```

`real_debate_count=0`. All three PM-approved orders (C, AMZN, GOOG) failed open and went to the
broker unreviewed. **The deliberator never spoke, so the veto rate for this run is not 0 % - it is
undefined.**

**The reason, read from `failed_open_reason` before the metrics** (the DL-116 lesson, applied):

```text
RuntimeError: Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error',
'message': 'Your credit balance is too low to access the Anthropic API. ...'}}
```

**Not a 429. Not a timeout.** A billing failure - the one cause in this class that no tunable, no
concurrency change and no adapter refactor can reach.

**Onset is 2026-08-20, not 08-21.** The prior scheduled run carries the identical 400 on 3 of its 5
orders (`NEE`, `XOM`, `INTC`) - so **two consecutive scheduled runs** were already degraded when
S184 was deployed. 🪤 The 2026-08-20 run's raw veto rate reads **40 %** (2 of 5), which looks like
the predicted fall and is not: 3 of those 5 were fail-opens. Of the orders actually debated, **2 of
2 were vetoed**. A veto rate computed over orders that were never reviewed is a diluted number, and
this is the fourth time a metric that *correlates* with the answer has been mistaken for it.

**Both providers have now run dry inside three days.** OpenAI on 2026-08-19 (`429 ... no credits
remaining`), Anthropic on 2026-08-20 (`400 ... credit balance is too low`).

**Operator constraint, stated 2026-08-22: not resolvable until 2026-08-30.**

**What this blocks.**

- ADR-0023's falsifiable test - parked until credit returns; nothing ships that changes this.
- [S172](sprints/sprint-172-independent-debates-run-independently.md)'s 15-order K=4 measurement.
  🪤 **Work-queue item 3's "UNBLOCKED 2026-08-20" is now false** and is corrected there.
- Item 9's verdict-quality gate (S173), which also needs the API.

**What it does NOT block, and this is the useful half.** ADR-0023 has **two** halves, and only the
referee's half needs an LLM. **The PM's half is measurable from the gate report alone, and it
fired** - see the DL-122 amendment. The next six sessions can still prove PM behaviour.

**Ruled out: item 7 (one LLM adapter in the kernel) is not a mitigation.** It carries this note
already for the 2026-08-19 outage and it holds harder now - a provider switch only helps if some
provider has credit, and none does. **Do not re-justify S170 on this evidence.**

🚨 **The real consequence is to the evidence discipline, not the trading.** For ~6 scheduled
sessions the gate goes **red every night for an external non-defect**, while the system trades
**unvetoed**. That is exactly the failure mode work-queue **item 6** (DL-104 d) was filed against -
*"trains the operator to read a real fault as noise"* - now firing nightly instead of theoretically.
**Item 6 stops being a nicety and becomes the thing that makes the next six nights honest:** a
declared `advisory` posture would make the unvetoed submissions a *stated* mode with a truthful
green, instead of six red nights that everyone learns to skip. It is promoted in the queue on this
evidence.

---

## DL-124 - Teardown by run-id misses every downstream artifact that is uuid-keyed - status: MEASURED (2026-08-21)

🚨 **A "zero residue" claim was wrong within two minutes of being made, and the standard teardown
idiom is why.**

**What happened.** The S184 deploy check placed `verify-2026-08-20-s184-a`, then abandoned it. At
**14:05:38** a direct query showed `MarketData=0` - nothing ingested - so it was recorded as safe to
drop: *"no scan, order or fill existed to strand."* `pg_teardown --prefix verify-2026-08-20-s184-a
--contains` deleted 3 nodes and 3 edges, a follow-up query returned **residue: none**, and the fleet
was scaled to zero.

**A background watcher, still running, contradicted all of it.** The provider was mid-ingest at
14:05 and finished afterwards:

```text
00:07:27  MarketData=0   <- immediately after teardown
00:09:30  MarketData=1   <- provider completed and wrote the node anyway
```

By 14:09:04 the **scanner had already consumed it** - `scanner-run-83d0562b…`, 99 evaluated,
**23 candidates** - and its `AnalystRun` was still missing. That `ScanRun` was live pending work: the
analyst polls `ScanRun` nodes with no downstream `AnalystRun`, so on the next wake it would have run
a **second full cascade alongside the scheduled run** - the exact outcome the teardown was performed
to prevent, displaced one stage down the pipeline.

**Root cause - the idiom cannot see the artifacts.** Teardown matches graph *keys*. Provider nodes
are keyed by run id (`market-data:<run_id>`, `regime-context:<run_id>`) and are caught. But
**`ScanRun` is keyed `scanner-run-<uuid>` and carries `run_id=None`**; `AnalystRun` and `PMRun` are
the same shape. So `--contains <run-id>` is **structurally incapable** of reaching anything past the
provider, and it reports success while doing so. Measured: the second teardown, aimed at the uuid,
removed **24 nodes and 25 edges** the first had left behind.

🪤 **Two compounding traps, both of which fired.**

- **A stage count of 0 is not "nothing happened", it is "nothing has happened *yet*".** A paced
  99-ticker ingest takes ~7 minutes; the check was made at ~6. Reading an in-flight pipeline as an
  idle one is the same absence-as-silence error `PM-NEV-09` and S183 exist to fix, made by hand.
- **The verification query used the same wrong filter as the teardown**, so it confirmed the teardown
  rather than testing it. `ScanRun` has no `run_id`, so filtering by run id found nothing and printed
  *"residue: none"* - a green that could not have gone red.

**The check that actually works.** Not "is the residue gone" but **"is any work pending for the next
wake"**, asked in the pollers' own terms - the same predicates the agents use:

```text
RunRequest  with no INGESTED_BY   -> provider will run
MarketData  with no SCANNED_BY    -> scanner will run
ScanRun     with no ANALYZED_BY   -> analyst will run
AnalystRun  with no EVALUATED_BY  -> pm will run
```

All four now read **0**, with 22 active positions intact. This predicate is key-agnostic, so it
cannot be defeated by a uuid, and it answers the question that actually matters.

**Rejected routes.**

- *Stamp a run id onto every downstream node* - the honest structural fix, deferred not rejected. It
  touches four agents' writers and their locked laws, and the pending-work predicate closes the
  operational hole today without any of that.
- *Wait out the pipeline before tearing down* - rejected as the general rule. It works only when
  someone is watching, and the point of this system is that nobody is.
- *Treat the watcher as noise* - it was very nearly dismissed as "no output yet". **It was the only
  thing in the session that caught this.** Long-running observers earn their keep precisely when the
  point measurement says everything is fine.

**Consequence.** The S184 deploy row in `functionality-checks.md` and the `STATE.md` entry both
carried the false "no scan existed / zero residue" claim and are corrected in the same commit that
records this.

---

## DL-123 - The same CodeQL rule landed twice in four days, and the branch gate structurally cannot catch it - status: MEASURED (2026-08-20)

**What happened.** Merging S184 raised CodeQL **#187**,
`py/mismatched-multiple-assignment`, at `agents/portfolio_manager/tests/test_correlation_edges.py:46`:

```python
(outcome,) = book.outcomes(...)     # outcomes() returns () OR a 1-tuple
```

`CorrelationBook.outcomes` returns `()` when there is nothing to assess and a 1-tuple otherwise, so
a fixed-arity unpack raises whenever the empty branch is taken. **This is the identical rule, in the
identical package, that produced #177 four days earlier** ([DL-110](design-log.md)) - where a PM test
unpacked `SectorBook.outcomes()` the same way, and that call also returns `()` with no sector.

**The structural part, and the reason it will happen again.** `codeql.yml` runs **only on `main`**.
S184's branch gate was genuinely green - CI, Security Findings and Build images all `success` at
`8613d72`, verified independently from a worktree at that SHA - because **the analysis that finds
this class had not run yet**. The alert appeared the moment the merge landed, and then failed the
*next* branch's Security Findings gate, which is how it surfaced.

🪤 **So "branch green" does not mean "CodeQL clean".** The gate proves CI and the findings baseline;
it cannot prove a scan that only main triggers. DL-110 recorded this as a trap and prescribed
merge-then-verify as the exit. That worked twice. **A trap that fires twice in four days is not a
trap, it is a missing check** - and both instances are the same one-line shape.

**Immediate fix.** Assert the length, then index:

```python
outcomes = book.outcomes(...)
assert len(outcomes) == 1
outcome = outcomes[0]
```

**Rejected routes.**

- *Make `outcomes()` always return exactly one outcome* - rejected. The empty return is meaningful:
  there is genuinely nothing to assess. Padding it with a filler outcome would reintroduce the
  absence-as-silence confusion `PM-NEV-09` exists to remove.
- *Wait for the next occurrence and fix it too* - rejected. That is the current policy by default,
  and it has now cost two red gates.
- *Move `codeql.yml` to run on branches* - **the obvious fix, deferred not rejected.** It would catch
  this before merge. Cost and blast radius are unmeasured (scan minutes per push, and the
  branch-vs-main alert-state semantics that DL-110 already found confusing). Queue item 31.
- *A local grep guard in `make ci` for fixed-arity unpacks of a variable-arity return* - deferred.
  Cheaper than CodeQL-on-branches and catches exactly this shape, but it is a new CI step and needs
  its own `gate_selftest` case so it cannot regress.

**Consequence for this merge.** A branch cannot clear an alert raised on `main`, so
`chore-gate-outcome-refuses-ambiguity` carries the fix but **cannot go green on its own gate** -
merge-then-verify on `main` is again the only exit, exactly as DL-110 prescribed. Recorded here so
the third occurrence is measured against a decision rather than rediscovered.

---

## DL-122 - S184 concentration gates: issuer, correlation, and not-evaluated evidence - status: DECIDED (2026-08-20)

**Context.** S184 implements ADR-0023 and PM laws v1.3. The sprint brief requires five design
decisions before code, with rejected alternatives recorded here rather than rediscovered inside the
implementation.

**Decision 1 - `GateOutcome` carries an outcome enum, not a boolean field.** Replace
`passed: bool` with `outcome = passed | failed | not_evaluated`. Historical payloads with a
`passed` key are accepted by a compatibility validator and normalized to `outcome`, but production
readers must branch on the three-state value. Rejected: adding `evaluated: bool` beside `passed`.
That is additive, but it permits `evaluated=false, passed=true`, exactly the impossible state
`PM-NEV-09` forbids.

> **Amendment, 2026-08-20 (post-merge review).** The shipped `GateOutcome` kept a `passed` property
> as a two-state convenience view, and it **re-collapsed the three states it had just separated**:
> `not_evaluated` read as `False`, i.e. *"the gate found a breach"* when the truth is *"the gate
> never ran"*. No production reader used it — all five were migrated — but it left the exact
> conflation this sprint removed reachable by the next one. **`passed` now raises on
> `NOT_EVALUATED`.** Rejected: deleting the property, which is equally safe but churns 31 test
> assertions in a just-verified sprint for no added protection. Rejected: leaving it, on the
> grounds that no caller uses it today — the defect class this whole thread is about
> ([DL-121](design-log.md)) is precisely *a hazard nothing currently trips over*. A boolean view of
> a tri-state fact is fine where the third state is impossible, and must refuse where it is not.

**Decision 2 - issuer identity is trading-pack data delivered to PM, not imported by PM.** The map
lives as `orchestration/packs/trading_issuer_map.json`; PM loads it from base64 env content in the
fleet or a path in local/dev, mirroring the master grant-pack pattern. A ticker absent from the map
is its own issuer and is an ordinary evaluable input. Rejected: hard-coding dual-class tickers in
the PM agent, which would move pack knowledge across the ADR-0012 wall; rejected also: making the
map a `tunable()`, because it is data identity, not a parameter to optimize.

**Decision 3 - one correlated cluster is recomputed against the running issuer book per candidate.**
Returns are close-to-close over the configured lookback window. The cluster is the candidate issuer
plus every held or tentatively approved issuer whose pairwise return correlation with the candidate
issuer is at least `correlation_threshold`. If the candidate issuer is already held, the candidate
adds dollars to that existing issuer exposure and does not consume a new issuer/name slot; the
cluster still evaluates against other correlated held issuers. Rejected: a static start-of-run book,
because `PM-STA-03` requires tentative approvals to affect later candidates; rejected: sector-label
proxies, because ADR-0023 exists precisely because labels miss the cross-label cluster.

**Decision 4 - correlation is computed in the PM domain from the run `MarketData`, cached for the run.**
The graph-pull path already supplies that node; the direct RPC path first looks up the full
`MarketData` by `RecommendationSet.run_id` and uses the existing short provider call only for
prices/regime when needed. The correlation helper caches close-to-close returns per issuer and pair
correlations inside one evaluation call. Measurement before implementation, using a synthetic
99-ticker x 202-bar book and 22 held pairs: 2000 candidate passes took 8.584242 s, or
4.2921 ms/pass, before any cache beyond return maps. That is below the latency budget dominated by
provider/LLM calls. Rejected: widening the PM provider call to fetch held-book bars; rejected:
reading `Bar` nodes, which are measured zero; rejected: persisting correlation facts this sprint.

**Decision 5 - not-evaluated outcomes name the missing input and block approval.** Missing sector
labels emit `outcome=not_evaluated` for sector concentration evidence with
`missing_input=sector_label`; too few overlapping returns emit `outcome=not_evaluated` for
`correlated_cluster_pct` with `missing_input=overlapping_return_bars`. The rejection reasons are
`sector_not_evaluated` and `correlation_not_evaluated`, and the gate report renders
`NOT-EVALUATED` as its own state. Rejected: returning `()` for unevaluable gates, because absence
and pass become indistinguishable; rejected: reporting not-evaluated as `FAILED`, because that hides
whether the gate found a breach or lacked the input to know.

**Guards already planted.** The first red run was
`uv run pytest agents\portfolio_manager\tests\test_issuer_correlation_concentration.py --no-cov`:
5 failed on the old code, covering `PM-NEV-07`, `PM-NEV-08`, `PM-NEV-09` and DRIFT-045.

**PROVEN LIVE 2026-08-22, unattended, on the production path.** `sched-2026-08-21` (fleet verified
on `s184`, all 16 apps) put GOOG and GOOGL in front of the PM in the same batch - the exact case
ADR-0023 was written for. Both gate reports, quoted verbatim from `OrderIntent.gate_report` and the
`PMRun` rejection set:

```text
GOOG  sizing  value=0.009975  threshold=0.01  outcome=passed
      issuer=alphabet; existing_issuer_value_usd=0.00;    position_value_usd=1025.19
GOOGL sizing  value=0.016684  threshold=0.01  outcome=failed
      issuer=alphabet; existing_issuer_value_usd=1025.19; position_value_usd=689.50
```

**GOOG's approved order counted against GOOGL as the same issuer**, taking Alphabet to 1.67 % of a
$102,771.73 book and breaching the 1 % sizing cap. 🚨 **Pre-S184 both would have passed** - sized
alone they are 1.00 % and 0.67 %, each under the cap - and the run would have opened **two positions
in one company**. One issuer, one bet, measured in production rather than in a fixture.

Three further S184 changes are visible in the same report, all previously only unit-proven:
`max_positions` counts `held_issuers=...,alphabet; is_new_issuer=false`; `max_sector_pct` now reads
`held_sector_value_usd=1092.36` beside `deployed_this_batch_usd=0.00`, so held dollars are counted
(the latent cross-day gate defect in work-queue item 2); and `correlated_cluster_pct` appears with a
three-state `outcome`.

🪤 **This proves the PM half of ADR-0023 only.** The ADR's falsifiable prediction is about the
*deliberator's* veto rate, and that half has no data at all - see [DL-125](design-log.md).

---

## DL-121 - The contracts leg of laws/contracts/tests was never load-bearing - status: DECIDED (2026-08-20)

**The question (operator, mid-amendment).** *"CONTRACTS should reflect LAWS and tested by TESTS, but
laws are central to my picture of it."* Raised while the PM law-amendment for ADR-0023 was being
drafted. It is right, and the measurement below shows which leg of that triangle is missing.

**Measured, 2026-08-20.**

- `laws -> test-plan -> tests` is real and CI-enforced. `scripts/check_law_coverage.py` fails the
  build when a green row cites a test that does not exist or whose docstring does not name the
  clause. 686 clauses across 14 books are bound this way.
- **Contracts are outside that loop.** `grep` for a clause ID across all 24 files in `contracts/`
  returns **zero**. The only link is prose running the other way: **16 clauses** say a variant of
  *"X matches `contracts/<agent>.py` exactly"*.
- **That phrasing is unfalsifiable.** `PM-TYP-03` asserts the payloads match
  `contracts/portfolio_manager.py` exactly; the test proving it imports that contract and round-trips
  it. **The contract is both the claim and the oracle** - change the contract and the test still
  passes. S156 half-caught this and demoted the wide row to gray, leaving a narrow deserialisation
  slice green.
- Contrast `PM-OUT-02`, which enumerates `ticker`, `action`, `quantity >= 1`, `est_price` Decimal,
  `stop_pct`, `target_pct`, `pm_run_id`, `provenance`. That clause **constrains** the contract.
  `PM-TYP-03` **delegates** to it.

**So the defect is not "contracts drift from laws". It is "the laws are vague enough that any
contract satisfies them".**

**The instance that proves it, found while drafting the amendment.** `PM-NEV-09` (new, this
amendment) requires that a concentration gate which cannot evaluate says so and never silently
passes. The contract that must carry that evidence is `contracts/portfolio_manager.py:18-23`:

```python
class GateOutcome(_Frozen):
    name: str
    value: float
    threshold: float
    passed: bool      # two states
    detail: str = ""
```

**A boolean has no third state.** The clause is *unexpressible* in the contract that carries its
evidence, and nothing in the repo says so: no test fails, no gate goes red. It was found only by
opening the file by hand.

🪤 **The scanner has the identical defect in a different encoding.** `FilterVerdict` carries
`filter_fired` plus a `passed` tuple, so *"the earnings gate did not run"* and *"the earnings gate
passed"* are the same bytes. **That is the bug S183 is out fixing right now** - the same
contract-expressiveness hole, in a second agent, that neither law book prevented.

**The sharpening.** A law is an assertion that can be **false** (`PM-NEV-06` claimed GICS level 1 and
was measurably wrong). A contract is a **definition**, and a definition cannot be falsified. So
"contracts reflect laws" cannot mean mechanical derivation. It means two checkable properties:

1. Every clause asserting a payload shape **enumerates the fields it requires** - never "matches the
   file exactly".
2. Every field in a contract is **traceable to a clause that requires it**. An unclaimed field is
   either dead, or an undocumented law.

**Decision - fold the first instance into work already in flight, do not open a programme.** The PM
amendment needs `GateOutcome` to gain a third state regardless. `PM-TYP-03` is therefore rewritten
from *"matches the file"* to an enumeration that names the required fields and requires
`GateOutcome` to be able to express *not evaluated*. One clause, one contract, real cost measured -
then decide whether to sweep the other 15.

**Cost, stated up front.** Rewriting a tautological `TYP` clause into an enumeration will demote
greens; apparent coverage drops. That is the trade conventions 7a already accepted: *"when the two
documents disagree, `laws.md` wins - even though that lowers apparent coverage."*

**Rejected routes.**

- *A fourth document layer mapping contracts to clauses* - rejected. The mapping belongs **inside**
  the clause text, where it is already read during every amendment. A separate map is one more
  surface to drift, and the operator has asked for less tracking surface, not more.
- *Sweep all 16 `TYP` clauses now* - rejected as sequencing, not as an idea. The cost of one honest
  enumeration is unmeasured; measuring it on PM first is cheap and the sweep is unblocked either way.
- *Generate contracts from the law text* - rejected. The law is prose written in ideal-design mode
  (conventions 6); generating types from it would invert the authoring direction and make the law
  answerable to what the generator can parse.
- *Leave it and rely on review* - rejected. Two agents already carry the same silent-pass defect,
  and review is what missed both.

**Follow-through.** Contract enumeration for the remaining 15 `TYP` clauses is a work-queue item, not
a sprint yet. Related: ADR-0023 (the amendment that surfaced it), S183 (the scanner half of the same
defect), conventions 7a (the coverage-vs-truth trade).

---

## DL-120 - Tunable sweep: the headline finding was wrong, and the law book said so - status: RETRACTED then CORRECTED (2026-08-20)

🚨 **RETRACTION, same day, before any code was written.** The original headline of this entry was
*"two agents, two sprints, the same mistake"* - `analyst.stop_target_mode` and
`execution.order_price_tolerance_mode` both left as bare defaults. **That is exactly backwards.**
Both are declared in their agents' locked laws, in identical deliberate wording:

```text
| stop_target_mode            | ... | NO (mode selector) | ADR-0013 champion-challenger selector;
                                      `flat` is the champion. Not a tunable - it selects which
                                      formula runs, not a value within one |
| order_price_tolerance_mode  | ... | NO (mode selector) | ...identical reasoning... |
```

It is **one convention, applied consistently twice**, recorded through the S149/S152 law-amendment
cycles and citing ADR-0013. A tunable is *a value within* a formula; a mode selector chooses *which
formula runs*. Both are documented in their PARAM tables with default, type and rationale, so
neither was ever "invisible to the operator" as I claimed. The law book carries a whole taxonomy for
this - `YES`, `NO`, `NO (config)`, `NO (mode selector)`, `NO (secret)`, 16 rows marked NO in some
form - and my audit was blind to all of it.

🪤 **Root cause of the error, and it is a process failure, not bad luck.** The sweep classified
fields by *code shape* (`tunable()` sets `description`; a bare default does not) and **never opened
`agents/<name>/laws/laws.md`, which is the specification.** CLAUDE.md requires exactly that check
when a law question is involved. Had I read the law first, there would have been no finding to
retract. **Fourth unmeasured direction claim in two days** - after DL-116's timeout, DL-117's
sentiment direction, and a veto-rate denominator that silently included synthetic fixtures.

**Corrected finding.** Of the ten suspects, **six are correct as they stand**:

| Field | Law says | Verdict |
| --- | --- | --- |
| `analyst.stop_target_mode` | `NO (mode selector)` | **correct as-is** |
| `execution.order_price_tolerance_mode` | `NO (mode selector)` | **correct as-is** |
| `curator.predictor_strategy` | `NO` - "training algorithm identity; structural" | **correct as-is** |
| `curator.schema_ref` | - | version identity, fine |
| `ProviderFeedSettings.*` (2) | - | duplicates of the provider rows below |

**What survives as real, and it is smaller and differently shaped:**

- 🚨 **`scanner.benchmark_ticker` is genuine law-vs-code drift.** The scanner law
  (`laws.md:219`) declares it **`YES`** - a tunable - and the code has it as a bare default. The
  analyst law says `YES` at line 251 and the analyst code *does* declare it. So one agent honours
  the law and the other does not, for the same parameter.
- **`provider.alpaca_data_feed` and `provider.ingest_ohlcv_only` appear in no law at all.** The
  provider `laws.md` is **LOCKED v1 (S69)**, so these were added after the lock and never declared.
  🪤 Fixing that needs a law cycle, not a code edit.
- **`execution.stage` is absent from the execution PARAM table**, appearing only inside `EXEC-OUT-01`
  as an output field. Possibly a genuine gap; **not verified** whether the law intends PARAM to
  cover it.

**The `execution.stage` severity note below stands** and was measured correctly.

---

**Why swept.** S183 found `stop_target_mode` written as a bare default rather than a `tunable()`,
hiding S150's fully-built volatility-scaled stop. The question was whether it was alone.

**Method.** `tunable()` always sets `description=why`, so a settings field with no description was
not declared through it. Imported every module under `agents/ kernel/ orchestration/ surfaces/
contracts/`, walked every `BaseSettings` subclass, and classified each field.

**Measured — 24 settings classes, 246 fields:**

| | count |
| --- | --- |
| declared via `tunable()` | **236** |
| bare, wiring-shaped (urls, keys, model refs) — legitimately not tunables | 32 |
| bare, **behavioural** — suspects | **10** |

**The ten, judged:**

| Field | Verdict |
| --- | --- |
| `analyst.stop_target_mode = "flat"` | **must be tunable** — already in S183 |
| `execution.order_price_tolerance_mode = "flat"` | **must be tunable** — the *same defect twice* |
| `scanner.benchmark_ticker = "SPY"` | **must be tunable** — sets every `relative_strength` and `beta` |
| `provider.alpaca_data_feed = "iex"` | **must be tunable** — IEX is a partial feed; SIP is the full one |
| `provider.ingest_ohlcv_only = False` | **must be tunable** — gates which feeds are ingested |
| `curator.predictor_strategy = "majority_class"` | **must be tunable** — selects the predictor |
| `execution.stage = "paper"` | **needs a `why` at minimum** — see below |
| `curator.schema_ref = "curator.training_example.v1"` | fine — a version identity, not a knob |
| `ProviderFeedSettings.alpaca_data_feed` / `.ingest_ohlcv_only` | duplicates of the two above |

🚨 **The headline is not the count, it is the pattern.** Two agents, two sprints, the same mistake:

- `analyst.settings:140` — `stop_target_mode` bare, surrounded by `scaled_stop_atr_multiplier`,
  `scaled_stop_floor_pct`, `scaled_stop_ceiling_pct`, **all properly tunable** (S150).
- `execution.settings:49` — `order_price_tolerance_mode` bare, surrounded by
  `scaled_order_price_tolerance_atr_multiplier`, `_floor_bps`, `_ceiling_bps`, **all properly
  tunable** (S149).

**Each sprint carefully registered the challenger's parameters and forgot the switch that selects
it.** The result is a fully built, fully parameterised challenger that no operator can reach through
the catalogue — twice. Whatever review caught the parameters did not think of the mode as one.

**`execution.stage` — severity corrected downward after checking.** It is
`Literal["paper", "broker_shadow", "live_manual", "live_autopilot"]`, so on its face the paper/live
switch and the most consequential value in the system. But: the graph is authoritative
(`current_stage_from_graph` prefers the latest `StageTransition`, falling back to the env value only
when none exists), and [`run.py:51`](../../agents/execution/run.py#L51) rejects outright —
`if stage not in ("paper", "broker_shadow"): return live_gate_rejected(...)`. **Both live stages
reject every order; the live submission path is not built.** So a stray `EXECUTION_STAGE` cannot
trade real money. 🪤 **The defect is that it carries no recorded `why` and is invisible to the
catalogue — not that it is dangerous today.** Saying otherwise would be the third unmeasured
direction claim in two days.

**Not swept: bare literals inside domain code**, the class S174 hit with
`_DEFAULT_LOOKBACK_DAYS = 60`. This sweep covers settings fields only. A module-level-constant sweep
is a separate, larger read and is **not** claimed here.

---

## DL-119 - The veto rejects 73% of approved orders, and it keeps citing one missing gate - status: MEASURED (2026-08-20)

**What changed.** DL-116 raised the grace so the veto actually binds. Four real runs later the
question is no longer *"does the veto work"* but *"can the system still trade"*.

**Measured across the four real binding runs** (Codex's synthetic S172 test runs are excluded - they
were 1-share fixtures, not trading decisions):

| Run | PM-approved | Vetoed | Submitted |
| --- | --- | --- | --- |
| `verify-2026-08-19-clean` | 9 | 6 | 3 (all fail-opens, never reviewed) |
| `verify-2026-08-19-clean-2` | 9 | 6 | 3 |
| `verify-2026-08-20-opus` | 4 | 3 | 1 |
| `verify-2026-08-20-s182-a` | 4 | **4** | **0** |
| **total** | **26** | **19** | **7** |

**73 % vetoed**, and 2026-08-20 produced the first run that approved four orders and traded none.
Only **2** of the 7 submitted ever filled (MO, CSCO).

**AMENDED 2026-08-22 - the 73 % cannot be re-measured, and the two runs since do not move it.**
Both scheduled runs after this entry was written were degraded by an API billing failure
([DL-125](design-log.md)), so neither is a binding run:

| Run | PM-approved | Really debated | Vetoed | Fail-open | Raw rate | Usable? |
| --- | --- | --- | --- | --- | --- | --- |
| `sched-2026-08-20` (pre-`s184` images) | 5 | 2 | 2 | 3 | 40 % | **no** - 2 of 2 debated were vetoed |
| `sched-2026-08-21` (first on `s184`) | 3 | **0** | 0 | 3 | 0 % | **no** - undefined, not zero |

🪤 **Neither 40 % nor 0 % is evidence that the veto rate fell.** Both are raw rates diluted by orders
the deliberator never saw. **The correct statement is that ADR-0023's prediction has zero
real-debate data on `s184` code** and will have none until credit returns on 2026-08-30. The 73 %
across the four binding runs stands as the last honest figure.


**The rejections are not noise, and they are not varied.** Across four consecutive nights the same
complaint dominates: the PM has no issuer or correlation dimension. On the clean run **4 of 6**
vetoes were this. On 2026-08-20, AMZN: *"the sector gates are label-based counts with no
name-correlation penalty, so 'Retail' lets AMZN pass at 1 name while the book already carries
correlated mega-cap tech beta (AAPL, NVDA, AMD, CSCO, NFLX, PYPL)"*.

**Reading.** 🚨 **The veto rate is a measurement of work-queue item 18's cost, not a veto problem.**
The PM keeps producing orders the deliberator keeps rejecting for a structural reason the PM cannot
see, because it has no correlation or issuer view of its own book. That reframes item 18 from
"highest-value open item" to **the binding constraint on the system trading at all**.

**Explicitly rejected: soften the veto.** Lowering the bar, or returning the grace to 900 so it
expires again, would restore throughput by making the objections stop binding rather than stop being
true. That is DL-104's advisory posture reintroduced by the back door, and every objection above
would still be correct. **Fix the PM, not the referee.**

🪤 **A number I published and had to scope down.** I first quoted this as 76 % from three runs; that
tally silently included Codex's synthetic 13-order S172 fixtures. Excluding them and adding the
fourth real run gives 73 % over 26 orders. Same conclusion, honest denominator.

**Not yet decided:** whether a 73 % veto rate is *correct behaviour for a book this concentrated* -
22 positions, heavily mega-cap tech - or evidence the deliberator over-weights correlation. Item 18
will answer it: once the PM aggregates exposure itself, the orders it emits should stop attracting
this objection, and any residue is the deliberator's own bias.

---

## DL-118 - S182 protects freshly filled entries from Fill lineage, not Position writes - status: DECIDED (2026-08-20)

**Question.** A broker holding can appear from a buy Fill before the monitor has written its
monitor-owned `Position`. Execution places broker stops one stage earlier than monitor adoption, so
`place_broker_stops` currently sees the holding but no position-derived stop plan and records
`UnprotectedPosition` instead of placing protection.

**Law reading record before implementation.** Read `agents/monitor/laws/laws.md`,
`agents/monitor/laws/test-plan.md`, `agents/execution/laws/laws.md`, and
`agents/execution/laws/test-plan.md`. `MON-IDN-02` declares `Position` as a monitor-owned label.
`EXEC-IDN-03` declares execution's broker-boundary evidence labels, including `BrokerStopOrder`.
`EXEC-OBS-03` requires a held position with no live broker stop to be loud and retried. Execution's
law has no `Position` ownership grant. Therefore S182 must not have execution create `Position`
unless it runs a law cycle; this sprint does not.

**Decision - execution may protect from filled-entry lineage, but may not create `Position`.** The
new stop plan is derived from execution-owned `Fill` nodes and their `OrderIntent` lineage only when
there is a fresh broker holding for the same ticker and no active `Position` plan yet. The
`position_ref` is the same deterministic reference the monitor will produce for the future
`Position` key, so after the monitor later writes `Position`, the existing `BrokerStopOrder` still
blocks duplicates. The stop fact remains execution-owned; the eventual `Position` remains
monitor-owned.

**Decision - wash-trade stop rejection stays loud and repeats.** A broker `403 potential wash trade`
on stop submission is recorded as the rejected stop `Fill` plus an `UnprotectedPosition` fault. S182
does not cancel the opposing buy automatically: the current broker port cannot identify the
conflicting order, and blindly cancelling entry orders would change trading intent to hide a
protection failure. The naked position must stay visible until the conflicting order is gone or a
future broker-order-discovery sprint can cancel the exact blocker and retry the stop.

**Decision - repeated unprotected faults are correct here.** S181's durable acknowledgement pattern
is rejected for this case. An untracked terminal test order was immutable residue; an unprotected
live holding is changing risk. Until an active broker stop exists, each run should keep emitting the
fault rather than remembering first sight and going quiet.

**Rejected routes.**

- *Move stop placement after monitor* - rejected for S182. It is semantically clean but requires a
  second execution pass or new orchestration edge, widening the stage contract.
- *Have monitor request stop placement* - rejected for S182. It preserves ownership, but adds a new
  cross-agent message and contract where existing Fill lineage already contains the needed facts.
- *Have execution create `Position`* - rejected. It violates `MON-IDN-02` and would require a law
  cycle before code.
- *Use a Fill-key-derived `position_ref`* - rejected. It would protect the first run but double-place
  after monitor adoption because the later `Position` reference would differ.
- *Automatically cancel any buy after a wash-trade 403* - rejected. Without broker-order discovery,
  execution cannot prove which order blocks the stop.

## DL-117 - The news feed is market-wide, and the sentiment score is an unweighted mean of it - status: MEASURED (2026-08-20)

**Question (work-queue item 26, filed diagnose-first).** The deliberator rejected sentiment as
evidence on three consecutive nights because the headlines behind it were not about the name. Was
the provider returning loose matches, or was the analyst failing to filter?

**Answer: the provider, and the analyst applies no filter of any kind.** Headlines come from
Finnhub `/company-news?symbol=X`, so the *vendor* asserts the association;
`fundamentals_parse.py:_parse_news` then takes every `headline` string in the payload, capped by
count, with **no relevance test**.

**Measured on `verify-2026-08-19-clean-2`, 99 tickers, 1,533 headline slots / 1,015 distinct.**
A headline filed under many tickers cannot be about any one of them, which measures contamination
without needing a company-name map:

| | |
| --- | --- |
| Slots whose headline is filed under **>=2** tickers | **736 = 48 %** |
| Slots whose headline is filed under **>=5** tickers | **287 = 19 %** |
| Slots containing their own ticker symbol | 154 = 10 % (lower bound; misses company names) |
| Worst single headline | *"Which dow jones stocks are moving on Tuesday?"* filed under **20** tickers |
| Worst ticker | **MRK, 60 %** of its 20 headlines are >=5-ticker generic |

**It moves the score, because the score is an unweighted mean.** `score_sentiment` averages
per-headline sub-scores, so a Dow Jones roundup counts exactly as much as an earnings report.
Re-scoring every ticker with the >=5-ticker headlines removed: **mean shift 4.8 points, max 75.0**
(TSLA **75.0 -> 0.0**), **15 tickers move more than 10 points**, and one ticker is left with no
scoreable headline at all.

**RETRACTION - my own framing in item 26 was wrong.** I filed it saying *"mis-attributed news is
buying stocks"*. The data says the opposite: **every** PM-approved order on that run scores *higher*
once contamination is removed (AMZN +2.3, GOOGL +6.0, INTC +5.0, CSCO **+14.3**, others 0.0). The
generic headlines were **suppressing** those scores. The deliberator's GOOGL objection was therefore
half right - the input is genuinely contaminated, but the approval survived the noise rather than
depending on it. 🪤 **This is bidirectional noise, not a bias toward buying**, and the risk is
mis-ranking and false rejection as much as false approval. Same error shape as DL-116: I asserted a
direction I had not measured.

**Candidate fix, cheap and vendor-independent.** The batch already contains every ticker's
headlines, so cross-ticker duplication is computable at zero API cost: drop, or down-weight, any
headline appearing under >= N tickers in the same run. **Not yet specced** - the threshold, and
whether to drop or weight, need a decision:

- *Drop at N=5* would remove 19 % of slots and leave 1 ticker with no signal at all, so the
  no-signal path must be a first-class outcome rather than an accident.
- *Down-weighting* keeps the signal but makes the score no longer a plain mean, which changes an
  artefact the deliberator reads.
- 🪤 **Do not filter on the ticker symbol appearing in the headline.** Only 10 % of slots would
  survive, because real company news says "ExxonMobil", not "XOM".

---

## DL-116 - The veto becomes binding by arithmetic, not by a switch - status: DECIDED (2026-08-19), AMENDED same day (half the diagnosis was wrong)

**Problem.** `sched-2026-08-19` submitted **all 9** PM-approved orders with
`deliberation_status=proceeded_unvetoed` at 07:02:17-22; the `DeliberationRun` landed **07:03:33**,
about **71 s** too late, and then returned **6 vetoes**. Acceptance failed on
`debate_coverage 0.778 < 1.0` and `failed_open_count 2 > 0`. Two independent causes, both measured:

- **Grace.** The debate spanned roughly **990 s** against `EXECUTION_DELIBERATION_GRACE_SECONDS=900`.
- **Per-call timeout.** 41 `LLMCall` rows in the window: median **15.0 s**, but the tail ran
  **65.3 / 59.3 / 58.2 s** against `DELIBERATOR_REQUEST_TIMEOUT_SECONDS=60`. One call exceeded the
  ceiling and two were within 2 s of it, producing the two
  `RuntimeError: no deliberator peer reply received` fail-opens (MO, CSCO). When this timeout was
  last measured (n=45) the max was **46.2 s**; the tail has grown since.

**Decision - grace 900 -> 1800, timeout 60 -> 120.** Both are `tunable()`s, no code and no image
rebuild. 1800 clears the observed 990 s span with 810 s of headroom; 120 is the declared ceiling
(`le=120.0`) and gives ~1.8x margin over the 65.3 s tail. Written to
`orchestration/packs/trading_tunables.json` as well as the live env, because a full `up` replaces
each app's env set and would silently revert an env-only change (DL-100 / S169).

**What this actually changes, named plainly.** 🚨 **The veto stops being advisory.** DL-104 returned
the grace 1800 -> 900 *deliberately*, because at the time the veto was "a good auditor and a bad
gate" and a grace that expires was recorded as **the sole no-code path** to keep it permissive. That
premise no longer holds: across `sched-2026-08-18` and `sched-2026-08-19` every verdict cited a real
structural gap (dual-class GOOG/GOOGL aggregation, absent sector-correlation penalty, market-order
sizing against an estimated price) and **none** was a DL-104-class defect. So this is a posture
change made by arithmetic rather than by the explicit switch that work-queue **item 6** still calls
for. Item 6 is not closed by this entry - the switch remains unbuilt, and the posture is now held in
place by two numbers that a busier night could overturn.

**The two levers are coupled.** Raising the per-call timeout lengthens the worst-case debate, which
pushes back against the grace: three slow calls at 120 s instead of failing at 60 s adds ~180 s.
9 orders would land near 1170 s, still inside 1800. 🪤 **At roughly 15 orders the two collide again**
(~1650 s), and `deliberation_grace_seconds` is capped `le=3600`, so this buys headroom - it does not
remove the constraint. **S172 is still the fix**; this is the mitigation that makes a clean run
possible today.

**AMENDMENT, 2026-08-19, after `verify-2026-08-19-clean`. The timeout half of the diagnosis above
is wrong.** Raising the grace worked exactly as predicted: the debate finished inside 1800 s and
`deliberation_status` came back **`applied_failed_open`**, not `proceeded_unvetoed` — the veto bound
for the first time, 6 of 9 orders blocked, **3 submitted instead of 9**.

But fail-opens went **up**, 2 -> 3, and coverage **down**, 0.778 -> 0.667. The real
`failed_open_reason` is not a timeout at all:

```text
RuntimeError: Error code: 429 - {'error': {'message': 'You have no credits remaining.
Add credits to continue using the API at https://platform.openai.com/...'}}
```

🪤 **The 60 s ceiling was a coincidence, and I read it as a cause.** The latency tail (65.3 / 59.3 /
58.2 s) sat right at the configured ceiling, which made timeout the obvious story; the calls were in
fact being *refused*. Probed directly: OpenAI **HTTP 429 no credits**, Anthropic **HTTP 400 usage
limit, access returns 2026-09-01**. **The deliberator has no working LLM provider**, so no tunable
produces a clean run and none of this was ever a latency problem.

**The timeout raise stays**, but on different evidence than it was made on: `verify-2026-08-19-clean`
logged calls at **75.4 s and 61.9 s**, so a 60 s ceiling would genuinely have cut two live calls. It
is defensible on its own; it simply was not the fix for this.

🚨 **Standing lesson, third instance of the same shape** (after the `record_deploy` SHA and the
module-size counts): a number that *correlates* with the failure boundary was taken as the cause
without reading the error text that was sitting in the graph the whole time. Read the reason field
first, then the metrics.

**Rejected routes.**

- *`max_rounds` 2 -> 1* - rejected. Worth ~40 % of the wall clock, but S172's own `why` requires the
  debate to show more than one round in live proof. Cutting the artefact under test to buy time is a
  decision to record, not a knob to turn, and it would contaminate S172's before/after measurement.
- *Lower `effort` back from `high`* - rejected. It shortens the tail, but `effort` reaching the wire
  at all was the `0.90.02` fix, and reverting it re-opens the inert-knob question DL-63 already cost
  us once.
- *Leave the grace at 900 and accept fail-opens* - rejected. It is precisely the state where an
  unreviewed order is indistinguishable in outcome from an approved one, and the whole point of the
  veto is to bind.
- *Raise the grace only* - rejected as insufficient. `failed_open_count > 0` fails acceptance on its
  own, so the timeout had to move too or the run could not come back clean.

---

## DL-115 - Untracked broker orders report once via broker-status ack - status: DECIDED (2026-08-19)

**Problem.** S181 found one canceled S164 Alpaca probe (`stop:probe-s164:T#1`) with no `Fill`
chain. The drop sweep has no durable memory for the no-Fill branch: it records an
`UntrackedOpenOrder` error and returns `False`, so the same terminal broker order re-emits a fresh
error on every run. S179 made one unresolved current-day error enough to turn `healthy=false`.

**Decision - remember first sight durably.** The sweep records an append-only acknowledgement for a
pipeline-owned broker order whose `Fill` is still missing after a successful cancel attempt or after
the broker already reports a terminal canceled/expired status. First sight remains an `error`
because a missing `Fill` for a broker order shaped like pipeline output is a real lineage defect.
Later sightings of that exact broker order are skipped before a new fault is emitted.

**Decision - use `BrokerOrderStatus`, without an edge.** The ack is a `BrokerOrderStatus` node keyed
from the broker idempotency key and broker order id, with explicit properties naming it as
`lineage_status="missing_fill_ack"`. It has no `REFRESHES` edge because there is no `Fill` to point
at, and the existing vocabulary only declares `BrokerOrderStatus -REFRESHES-> Fill`. This keeps the
evidence inside execution-owned broker-boundary status facts and avoids a vocabulary-pack move.

**Decision - revocation is by precedence, not deletion.** The sweep looks for a `Fill` first and
consults the ack only when no `Fill` exists. If a later repair creates the `Fill`, normal drop
evidence can be recorded and the old ack remains as history rather than being removed.

**Rejected routes.**

- *Demote `UntrackedOpenOrder` to warning* - rejected. It would make health green while silencing
  every future missing-Fill lineage hole.
- *Skip terminal orders after an age cutoff* - rejected. The same defect would disappear based on
  time or order volume, not based on corrected evidence.
- *Exclude no-Fill orders from `_pipeline_owned`* - rejected. That deletes the check instead of
  giving it memory.
- *Add a new `UntrackedOrderAck` label* - rejected for this sprint. It is self-describing, but it
  would require a trading graph vocabulary pack change, deployment coupling, and an execution law
  ownership follow-up for one acknowledgement bit.
- *Reuse `BrokerOrderStatus` with a fake `REFRESHES` edge* - rejected. A reader should not see a
  fabricated Fill relationship. The absence of the edge is the point.

---

## DL-114 - Fault incidents are live-scoped, not the immutable Fault log - status: DECIDED (2026-08-18)

**Problem.** S178 cleared `pending_human_flags`, but `healthy` still reads false because
`open_incidents` counts every `Fault` whose status is not `resolved`. Live re-check on 2026-08-18:
Postgres spine, 6119 `Fault` nodes, 0 `FaultResolution`, 0 pending human flags, every Fault
`status=pending`. The largest contributor is closed history: 5762 nodes from the July
`property 'broker_status' cannot be overwritten` incident.

**Decision - separate incident health from the Fault log.** `Fault` remains an immutable
per-occurrence audit log; `fault_node_key` stays timestamp-keyed so recurrence appends. A live
incident is an unresolved `Fault` with severity `error` or `critical` in the latest graph-run day.
The day is derived from graph evidence, not wall clock: latest `BrokerPositionSnapshot.created_at`,
falling back to the latest Fault occurrence date when no snapshot exists. `warning` Faults remain
queryable evidence, but they do not pin `healthy` false.

**Decision - explicit retirement is append-only.** A `FaultResolution` node joined to the Fault by
`RESOLVES` is the retirement evidence. The health predicate treats either a matching
`FaultResolution` or legacy `status="resolved"` as resolved, but S179 writes new resolutions rather
than mutating the Fault. The initial live sweep may retire current `error`/`critical` incidents after
operator inspection; older closed history stops counting by scope without being deleted.

**Decision - one predicate implementation.** The supervisor `MasterReport` path and the dashboard
`system_health()` path both call the same helper. Their names may remain `open_incidents` /
`open_faults` for compatibility, but the value is the shared live-incident count.

**Stop-identity faults.** The recurring `stop identity mismatch ... broker_stop=True
graph_stop=False` rows are real warning-level Fault evidence from `drop_unfilled_orders`, recurring
across 2026-08-08, 08-10 through 08-14, 08-17, and 08-18. They are not silenced or fixed here. The
question is deferred as a separate execution/drop-sweep evidence defect because S179 changes health
reporting only; the fault log and incident surface still expose them.

**Rejected routes.**

- *Set `Fault.status="resolved"`* - rejected. It mutates append-only evidence and would trip the
  same `_append_props` overwrite guard that produced most of the backlog.
- *Delete old Faults* - rejected. The log exists precisely so old failures remain auditable.
- *Keep counting every unresolved Fault forever* - rejected. It makes `healthy` a statement that the
  system once had trouble, not a live health signal.
- *Use wall-clock age* - rejected. `system_status` must be deterministic for the same graph state;
  the scoping anchor is graph evidence instead.
- *Count warnings as health incidents* - rejected for the same reason S178 made first-sight
  divergence a warn: warning evidence can be important without demanding `healthy=false`.

---

## DL-113 - Debate-packet numbers name their unit and scope - status: DECIDED (2026-08-15)

**Question.** S177 sweeps the values rendered into the deliberator debate packet after four real
vetoes were traced to correct numbers under unreadable labels. The immediate defect is PM
`max_sector_pct` detail rendering `deployed=0.00`, where the value means "deployed by earlier
approved orders in this PM batch", not portfolio-wide sector exposure.

**Decision - producer-owned names carry the unit and scope.** PM gate `detail=` strings and the
deliberator's own shell labels must name the unit/scope in the key: examples are
`deployed_this_batch_usd`, `order_cost_usd`, `quantity_shares`, `requested_tickers`, and
`provider_sentiment_score`. Generic `GateOutcome.value` / `threshold` render as gate-specific
labels such as `value_batch_sector_ratio` and `threshold_sector_ratio`.

**Decision - source-owned dictionaries get an explicit boundary.** `market.fundamentals`,
`candidate.metrics`, `verdict.features`, and analyst `quant_metrics` are open-name dictionaries
whose keys are producer/vendor owned. The deliberator must not invent units for those keys. It
renders them with a source-owned units/scope boundary; a value whose key does not name a unit is
explicitly unknown to the deliberator rather than inferred.

**Decision - labels only for S177.** `SectorBook._deployed` stays batch-scoped. Seeding it from held
positions would change approval behaviour, not just packet wording. That dollar-cap behaviour
question is filed separately: decide whether `max_sector_pct` should include held portfolio sector
dollars instead of only prior approvals in the current PM run.

**Rejected routes.**

- *Teach the prompt how to read `deployed` and other values* - rejected for the DL-112 reason: every
  future reader would need the same prompt text to avoid the same wrong conclusion.
- *Seed `SectorBook._deployed` from held positions in S177* - rejected. That changes which orders the
  PM approves and needs its own ADR-backed behaviour change.
- *Infer units for vendor/scanner dictionaries at the deliberator render site* - rejected. A renderer
  cannot know whether `pe`, `beta`, or a future vendor key is a ratio, currency, count, or score.
- *Drop ambiguous dictionaries from the packet* - rejected. The values are still useful evidence;
  the correct boundary is "source owned / unknown here", not silence.

---

## DL-112 - Two counts, two units, one prefix: the veto read word counts as article counts - status: DECIDED (2026-08-15)

**What happened.** The `sched-2026-08-14` run put 9 PM-approved buys to the deliberator and 8 came
back vetoed; 1 order reached the broker. Reading the verdicts, **XOM was vetoed for a defect that
does not exist**: *"the sentiment feed is internally inconsistent (10 articles but 11 positive and 3
negative classifications)"*. AMZN's `revise` cites the same shape.

The feed was fine. `score_sentiment` returned three metrics under one prefix and **two different
units**:

| Metric | Counted | Unit |
| --- | --- | --- |
| `sentiment_articles` | headlines that carried >= 1 lexicon word | articles |
| `sentiment_positive` | positive lexicon **word occurrences**, summed | words |
| `sentiment_negative` | negative lexicon **word occurrences**, summed | words |

`Recommendation.quant_metrics` carries these verbatim into the debate context
(`context_pm._quant_metrics` renders `name=value`), so the judge saw
`sentiment_articles=9, sentiment_positive=11, sentiment_negative=2` and concluded 11 > 9 was
impossible. One headline routinely carries several lexicon words, so word counts exceeding the
article count is the **normal** case, not a corrupt one.

**Decision - the names carry the unit.** `sentiment_positive` -> `sentiment_positive_words`,
`sentiment_negative` -> `sentiment_negative_words`. No computed value changes; nothing is removed
from the context. Shipped `0.90.11`, guard planted (old names -> `KeyError`) and restored.

**Rejected routes.**

- *Drop the counts from the veto context* - rejected. Volume and tone strength are real evidence for
  the debate; the trap was the label, not the data.
- *Rename the `SentimentReading.positive` / `.negative` fields and their graph props too* - rejected
  for this change. Those are not LLM-facing, and renaming them splits 433 existing
  `SentimentReading` nodes across two prop vocabularies for no gain. The fields now carry a comment
  naming the unit instead.
- *Teach the deliberator prompt that the units differ* - rejected as the primary fix: it makes every
  future reader of `quant_metrics` depend on prompt text to avoid a wrong conclusion. The metric
  name is the durable place for a unit.

🪤 **This is DL-104's disease, third instance.** DL-104a was an ATR fragment the context invented;
DL-104b was portfolio/batch absence read as zero exposure; this is a unit read from a name. All
three cost real orders, and all three are the veto context asserting something it could not prove.
The class is *"the context said something the reader could only misread"* - worth a sweep of every
value rendered into the debate, not three more point fixes.

**Measured, not assumed:** `analyst-run-f38452d1...:XOM` carries
`sentiment_articles=9, sentiment_positive=11, sentiment_negative=2` in `quant_metrics` - read from
the production spine on 2026-08-15, and the shape the judge quoted.

---

## DL-111 - The audit-clause sweep: nine green rows read, five demoted, two clauses false - status: MEASURED (2026-08-14)

S165 closed asking for this: `SCAN-OBS-01` had been green while its clause was false, because the
cited test proved *provenance links* rather than *FilterTrace reconstructability*. The work queue
carried the follow-up as **"17 audit-type rows"**. **Measured: there are 9 `audit` rows and 4
`observable` rows, 13 in total** - and 4 were already gray from the S156 citation check, so **9
green rows** were actually in scope. The 17 was a carried, unmeasured number.

**Read one at a time, clause against cited test. Five demoted, four stand.**

| Row | Verdict |
| --- | --- |
| `ANLZ-OBS-01` | ⬜ cited test asserts a pub/sub node exists with a `recommendations` key |
| `EXEC-OBS-01` | ⬜ proves one `Fill`; `Reconciliation` is asserted in no test at all |
| `EXEC-OBS-02` | ⬜ proves broker rejection; timeouts and stage-gate faults untested |
| `PM-OBS-01` (the "gate outcomes and portfolio snapshot" row) | ⬜ weaker than the two sibling rows S156 already demoted |
| `PROV-OUT-04` | ⬜ proves `graph_node_id` resolves, not source or transformation |
| `PM-OBS-01` (rejection `gate_report`), `PM-OBS-02`, `SCAN-OBS-01`, `SCAN-OBS-02` | 🟩 clause and cited test match |

**Two of the five are worse than a citation gap - the clause is false in code**, and both are now in
the drift register rather than the test plans. **DRIFT-039:** `portfolio_state_snapshot` appears
**nowhere in the codebase**; `OrderIntentSet` has no snapshot field and `PMRun` carries
`order_intent_set` alone. **DRIFT-040:** `Provenance` has no source or transformation field, and
`MarketSnapshot` records `created_at` plus a boolean `used_fallback` - so under ADR-0006's
three-vendor OHLCV arrangement, *which feed produced this bar* is unanswerable from the graph.

**The pattern under the pattern, worth more than the five rows.** Four of the five demoted rows cite
a test on the **pub/sub path**, which production does not use - `test_analyst_pubsub`,
`test_pm_pubsub`, `test_execution_pubsub`. That is the S174 shape (a parameter that travelled
correctly on the request/response path while the graph-pull path took a bare default) showing up in
the *ledger* rather than in the code. A row proven only on the pub/sub path says nothing about the
fleet. Not swept for here; **candidate for the next sweep** - and a cheaper filter than reading
clauses, because it is greppable.

🪤 **A green row can also be green for the wrong reason and still be true.** `ANLZ-OBS-01`'s
clause **is** satisfied in production - the graph-pull path persists the whole `RecommendationSet`
as `AnalystRun.recommendation_set` - it is the *test* that proves none of it. Demoting the row is
correct; concluding the analyst loses its scores would have been a false red (the DL-73 lesson).

**Not decided:** DRIFT-039 and DRIFT-040 each need a forced choice - build the thing, or narrow the
law to what the code actually carries. Both are law amendments, not test-citation fixes.

## DL-110 - A manual dispatch consumes that night's scheduled run id - status: MEASURED (2026-08-14)

**The scheduled run for 2026-08-14 does not exist, and nothing failed.** `dispatcher-cron` fired at
`2026-08-13T22:30:00Z` and **Succeeded**, logging `placed sched-2026-08-13 reason=NYSE trading
session`. No `sched-2026-08-14` `RunRequest` was ever created, and the newest graph write of any
kind is **2026-08-13T02:48:54Z** - no `LLMCall`, `DeliberationRun` or `Fault` after it. `master` was
up 22:25-22:30:40 and went quiet; on 08-12, a night that did work, it stayed up to 23:37.

**Mechanism.** `as_of` is *today's UTC date* (`scripts/dispatch_scheduled_run.py`) and
`place_run_request` is a `merge_node` on `run-request:sched-<date>` (`orchestration/start.py:79`).
Yesterday's manual S174 proof fire ran at **02:28 UTC on 08-13** - the same UTC day as the 22:30
scheduled fire - so it had already taken the key. The scheduled fire re-merged onto a complete 8/8
node, and the graph-pull fleet found nothing unconsumed to pull. Day-keyed dedupe worked exactly as
designed; the collision is that a manual fire and the scheduled fire **share one key per UTC day**.

**Consequence.** The 60 s `request_timeout_seconds` readout (`failed_open_count 0` /
`debate_coverage 1.0`, predicted in STATE) is **untested**, not failed. Tonight's 22:30 UTC fire
takes `sched-2026-08-14` uncontested and produces it.

**Ruled out: firing manually to recover the day.** Every agent's KEDA rule is a cron window
`22:30 -> 00:30 UTC`; at the time of the decision **27 minutes remained**, against **~21 minutes**
end to end for the comparable run (dispatcher 02:28 -> last write 02:48:54 on 08-13). A run cut off
mid-cascade at 00:30 would still burn the key, destroying the only clean single-variable comparison
available. Extending the window across 16 apps to buy ~22 hours was rejected as a live config write
for no proportionate gain - the [DL-100](#dl-100) shape.

**Open, not decided:** whether the run id should key off the *session* date rather than the UTC
date, which would let a pre-open manual run and the post-close scheduled run coexist. Not urgent -
the collision only bites on a day with a manual fire - and it moves a key format the whole graph is
keyed on. Filed here so it is not re-derived.

## DL-108 - S175 makes the veto say only what it can prove - status: DECIDED (2026-08-13)

**Decision.** S175 repairs DL-104 classes (a), (b), and (d) without changing the fail-open posture
or the `DeliberationRun` vocabulary. The four choices:

1. **Delete the ATR fragment.** The PM packet no longer renders `stop_pct vs ATR% -> PASSED/FAILED`
   inside `stop_vs_regime_volatility gate:` because no PM gate performs that comparison. The live
   AMD replay from `market-data:sched-2026-08-13` changed from
   `stop_pct=5.00% vs ATR%=4.07% -> PASSED` to no ATR clause at all.
2. **Fail-open remains permissive, but no longer clean.** Execution reads the existing
   `failed_open_tickers` field, stamps `ExecutionRun.deliberation_status="applied_failed_open"`,
   and emits `DeliberationFailedOpenSubmit`. It still submits the order, preserving S147.
3. **The posture is declared in ADR-0022, not as a tunable.** `applied_failed_open` is an evidence
   status under the existing fail-open policy; turning the veto advisory/binding as a mode remains
   an operator posture decision for a later ADR.
4. **Do not supply portfolio/batch context in this sprint.** The packet now states that holdings,
   open positions, sibling orders, and dual-class exposure facts are unavailable and must not be
   inferred beyond explicit PM gate outcomes.

**Rejected routes.**

- *Relabel the ATR fragment honestly* - rejected because a non-gate ATR number remains an extra
  prompt input that can move with unrelated data-window changes. Deleting it leaves only performed
  gate outcomes in a gate line.
- *Add failed-open tickers to `vetoed_tickers`* - rejected because that makes the fail-open path
  block like a veto, reversing S147 as an implementation side effect.
- *Add a new `DeliberationRun` property* - rejected because `failed_open_tickers` already exists and
  is pack-declared; a new property would force a full deploy while S169's env-wipe gap is open.
- *Add a tunable advisory/binding switch* - rejected because this is safety posture, not an
  experiment parameter.
- *Supply full portfolio and batch context now* - rejected on blast radius and latency. It requires
  a broader packet contract and more tokens; S175 only makes the current packet honest.

**Consequences.** Fewer veto objections after S175 are expected, not a regression: the largest
self-manufactured objection class is gone. S173's self-agreement baseline must be remeasured after
this lands because verdicts before and after S175 are not comparable.

---

## DL-01 · Primary organizing lens for `ops/`  ·  status: OPEN

**Question.** A filesystem is one tree, so the `ops/` realm can show only one organizing lens
as folders. Which is primary?

| Lens | Organizes by | Residency appears as |
| --- | --- | --- |
| Departmental | who owns / escalation | a GRC concern |
| DataCentre | kind of resource (compute/network/storage) | an attribute (region property) |
| **Lifecycle** | when in the process (build→deploy→operate→recover→retire) | a gate in the flow |

**Key insight (keep regardless of choice).** These are **views, not rival taxonomies.** The
*atoms* (the OIDC app, the Aura instance, a gate) are lens-independent; only the grouping
changes. Pick one lens for the folder tree; express the others as view-indexes now and **Neo4j
queries later** (one graph, project any view). This is a strong argument for modelling `ops/`
in the graph.

**Ruled out.** Committing the tree to one lens *permanently* (violates LAW-01). The current
`departments/` layout is provisional.

**Status.** Operator leaned **Lifecycle** (interrupted before confirming). Not final. Decide
before filling the remaining charters, so they're filed under the right primary lens.

---

## DL-02 · Data-residency: governing gate vs infrastructure attribute  ·  status: OPEN

**Question.** Is residency a **gate** that can block any operation, or an **attribute** of the
infra layer?

- **Option A — governance gate (GRC owns it).** Every deploy/data-move passes a residency check
  first. ✅ provable to a regulator (LAW-05); wrong-region move is structurally impossible.
  ❌ extra ceremony per region-touching action.
- **Option B — infra attribute (region property).** ✅ simpler, fewer gates, matches the
  DataCentre lens. ❌ residency becomes implicit/scattered; nothing *stops* a non-compliant
  move; "prove why here?" is manual and audit-risky.

**Recommendation on record.** **Option A** — financial data with tax-jurisdiction exposure; the
cost of an undefendable region is high. Note the lens choice (DL-01) tugs this: DataCentre→B,
Departmental/Lifecycle-with-GRC→A.

**Status.** Operator leaned **Option A** (interrupted before confirming). Not final.

---

## DL-03 · Multi-tenant residency model — the three-plane decomposition  ·  status: DRAFT (not decided)

The most important architectural idea from the 2026-06-21 platform discussion. Captured so it
is not lost; **not committed** — there are no real clients yet.

**The unlock — classify data by *who it is about*:**

| Tier | Examples | About | Residency? |
| --- | --- | --- | --- |
| Operational | master registry, identity, grants, sessions | the system | none — central |
| Reference/market | OHLCV, news, fundamentals, the universe | instruments | none — global |
| Signal/model | scores, forecasts, regime, model artifacts | instruments | none — global |
| Client-personal | KYC, PII, identity | the client | **strictly zoned** |
| Client-financial | positions, orders, fills, P&L, broker links | the client | **zoned + retention** |

Only the bottom two rows carry a jurisdiction. Everything that makes it a *trading* system is
about stocks, not people.

**Falls onto the 12 agents as three planes:**

- **Signal plane** (scanner · analyst · forecaster · provider) — market signals about
  instruments → **global, shared, one instance, cheap.**
- **Client plane** (portfolio_manager · execution · monitor · reporter) — applies signals to a
  *client's* portfolio → **the only part that gets zoned**, deployed per residency zone.
- **Control plane** (master · operator · supervisor · curator · researcher) — orchestration →
  **central "home" region.**

**Consequences / sub-points:**

- "Spin up an EU zone" = the `ta` deploy framework run with `--region=eu` against an EU graph.
  The multi-region topology *is* the ops framework parameterised by zone.
- **Compute follows data:** processing is itself a transfer (GDPR), so client-plane agents must
  *run* in the zone of the data they touch — not just store there.
- **Aggregation:** zones report anonymized aggregates upward; the centre sees money, never people.
- **Residency is 3 strands** that can point to different countries for one person:
  data-protection (where privacy law applies — extraterritorial, e.g. GDPR follows EU residents),
  tax (CRS/FATCA reporting + retention), regulatory (which financial regulator governs the
  service). The onboarding "interview" must capture them separately; the data domicile is
  derived to satisfy the **strictest intersection**; if none lawful → **decline the client.**

**Ruled out (implicitly).** One global graph for all clients (fails residency); full
stack-per-zone for the *entire* fleet (needless cost — only the client plane needs zoning).

**Status.** DRAFT model, deferred until real clients. **The constraint to protect now:** do not
build a single-tenant data model that can't partition by residency zone later. Graduate to an
ADR ("tenant-partitioned by residency zone; domicile policy-derived at onboarding") when the
data model is next touched.

---

## DL-08 · Agent work loop — "graph as queue" pull model  ·  status: DECIDED (2026-06-21)

**Question.** How do deployed agents get triggered to do their work? (DL-07c concrete design.)

**Decision (operator, 2026-06-21).** **Graph-as-queue / DB-mediated pull model:**

- **Provider** is the sole data-ingestor — one container, runs on its own cadence (market-close
  cron or manual trigger), fetches OHLCV + news + fundamentals, writes everything to the graph,
  then exits or sleeps until the next cycle. Other agents do not need provider alive to work.
- **All other agents** poll the graph: "Is there data with my name on it that I haven't processed
  yet?" If yes → process → write results → loop. If no → sleep(N) → loop.
- **The graph IS the queue.** No Azure Service Bus dependency in the work loop. The P14 pub/sub
  bus becomes an **optional fast-path notification** layer ("doorbell" — hint to wake up early
  instead of waiting for the poll interval). The graph is the source of truth; the bus is additive.

**Work-loop pattern per agent:**

```python
payload = activate_agent(...)          # EHLO → ACTIVATE → config injected to env
graph   = build_graph_from_env()       # reads NEO4J_URI + creds from env (_apply_config set them)
agent   = ScannerAgent(settings, graph=graph)
while True:
    pending = find_unprocessed_scan_windows(graph)   # Cypher: no ScanResult downstream
    for window in pending:
        agent.run(window)
    time.sleep(POLL_INTERVAL)          # default 60s; tunable per SCAN_POLL_INTERVAL env var
```

**Why this model over pure pub/sub:**

| Question | Graph-pull (this decision) | P14 pub/sub only |
| --- | --- | --- |
| Provider down → analyst broken? | No — analyst reads existing DB rows | Yes — event never arrives |
| Test one agent in isolation? | Yes — feed DB, start agent | Hard — upstream must be publishing |
| Azure Service Bus required? | No | Yes |
| Debug state? | `ta graph` at every stage | Log correlation across agents |
| Latency (EOD data) | ~poll interval (60s fine) | Sub-second (overkill) |

**Ruled out.** Pure pub/sub-only work loop (too coupled; agent failure cascades upstream; bus
is a hard runtime dependency for every run; hard to test agents in isolation).

**Consequences:**

- Provider entrypoint gets a `--ingest` mode (or always runs its ingest loop).
- Each agent needs a `find_unprocessed_{agent}_work(graph)` graph-query function.
- Neo4j credentials must reach every agent via ACTIVATE.config (not just master).
  Means adding `neo4j-uri` / `neo4j-user` / `neo4j-password` to `AGENT_SECRETS` for all agents,
  OR deploying them as plain env vars on the Container App (no KV, acceptable — they're connection
  strings, not secrets in the same sense as API keys). **Decision needed (DL-08a, open).**
- `idle_loop()` is replaced by the agent's work loop once this is wired.
- P14 pub/sub bus remains in the codebase as the speed-path; agents can optionally subscribe
  for faster wake-up. The bus subscription is additive, never required for correctness.

**Status.** DECIDED. Graduate to an ADR ("graph-as-queue work loop") when the first agent
(`provider → graph`) implementation lands.

---

## DL-08b · Agents fetch market data over the bus, not the graph — S79 scope correction  ·  status: DECIDED (2026-06-22)

**Constraint discovered (S79 kickoff).** DL-08 assumes every agent reads its inputs from the
graph. The code does not work that way yet:

- **Scanner** (`_run_scan`) and **analyst** (`_analyze`) acquire OHLCV/regime via **live bus RPC
  to the provider** — `request_market_data(self.bus, …)` → `bus.request(recipient="provider")`.
  The graph claim-check only carries the *handoff artifact* (candidates, recommendations) between
  adjacent agents — **not** the underlying market data.
- **S78's ingest writes a summary, not data.** `write_market_snapshot` persists
  `bar_count`/`requested`/`returned` — *not the bars themselves*. There is nothing in the graph
  for a downstream agent to read market data **from**.
- **Per-container `InProcessBus` can't do cross-container RPC.** Each agent container builds its
  own local bus (as the S78 provider entrypoint does). A scanner's `bus.request(recipient=
  "provider")` hits its *own* empty bus — the provider is in a different container. This coupling
  is exactly what DL-08 chose graph-as-queue to eliminate.

**Consequence.** S79 implemented literally (add `poll.py` + `work_loop()`, swap `idle_loop()`)
would pass CI but the agents would still **fail at `request_market_data`** — green, but not
actually standalone. The sprint's headline goal would be unmet.

**Decision (operator + Claude, 2026-06-22).** **Reshape S79 to a vertical slice (provider→scanner)
rather than the full six-agent rewrite.** Smallest surface that proves DL-08 is real:

1. **Provider ingest persists the full market payload** to the graph (bars + earnings + …), not
   just a summary node — so a downstream agent has something to read.
2. **Scanner reads market data from the graph** (a graph-backed market source) instead of bus RPC,
   ending the provider→scanner bus coupling for this handoff.
3. **Ship the reusable `work_loop()` kernel helper** (find_pending → process → sleep).

**Ruled out (this sprint):**

- *Full six-agent rewrite* — multiplies the speculative-Cypher / schema-discovery risk per agent;
  no shippable checkpoint if quota runs out mid-pipeline.
- *Triggers-only (poll claim-check artifacts, keep market-data RPC)* — passes CI but agents still
  die at `request_market_data`; buys the appearance of standalone agents without the substance.

**Pattern established for S80+.** The graph-backed market source built here is the template the
analyst / PM / execution / monitor / reporter reuse when their data paths move graph-first.

**S80 (2026-06-22) — extended the slice to scanner→analyst.** Provider now also persists the full
`RegimeContext` (`ingest._write_regime_context`, keyed by window-end date); scanner persists the
full `CandidateSet` on its `ScanRun` node; analyst reads all three from the graph
(`agents/analyst/poll.py`: `find_pending` over `ScanRun` lacking an `ANALYZED_BY` descendant +
`analyze_scan_node`, which pulls the `CandidateSet` from props, the `MarketData` via the ScanRun's
`DERIVED_FROM` descendant, and the same-day `RegimeContext` by date). The scoring core was extracted
to `agents/analyst/run.py` (`run_analysis`) so the bus path (`_analyze`) and the graph path share one
implementation. **Bug caught by the coverage gap:** the lineage edge is `(scan)-[:DERIVED_FROM]->(market)`,
so market is the ScanRun's *descendant*, not ancestor — the first cut walked `ancestors` and would have
returned empty results forever. **Still deferred to S81:** PM, execution, monitor, reporter.

**S81 (2026-06-22) — extended the slice to analyst→PM, PM ONLY.** Analyst now persists the full
`RecommendationSet` on its `AnalystRun` (S80 left it `{}`, counts only); PM reads it plus the
`MarketData` (via the AnalystRun's `ANALYZED_BY` ancestor = ScanRun, then its `DERIVED_FROM`
descendant) and the same-day `RegimeContext` (`agents/portfolio_manager/poll.py`). Sizing/risk core
extracted to `agents/portfolio_manager/run.py` (`run_evaluation`), shared by the bus path
(`_evaluate_orders`) and the graph path — the `_provider_rejection`/`_record_fault`/`_empty_result`
helpers moved out of `agent.py`, so the degraded-fault `source_module` is now
`agents.portfolio_manager.run` (one existing test assertion updated). **Scope decision (operator,
2026-06-22):** keep the one-handoff-per-sprint discipline — PM only, execution/monitor/reporter →
**S82**, rather than landing all four at once. **Ruled out:** doing all four in S81 (rejected — same
reason S79/S80 each took one hop: smaller diff, each handoff's lineage gap surfaces in isolation).
**Known limitation:** graph-pull PM builds a fresh `default_portfolio` each poll, not live
position/cash state (that needs execution/monitor running graph-pull first).

**S82 (2026-06-22) — closed the chain: execution + monitor + reporter (all three).** PM now
persists the full `OrderIntentSet` on its `PMRun`. Execution: submit core extracted to
`agents/execution/run.py` (`run_submit`, shared by `_submit` and the new poll path); `poll.py`
finds `PMRun` lacking `EXECUTED_BY`, submits via the injected broker, and writes a new
**`ExecutionRun` anchor** (`PMRun ─[EXECUTED_BY]→ ExecutionRun`) — execution previously wrote only
`Fill` nodes, leaving monitor nothing to poll. Monitor: dropped the live `latest_close_cents`
provider bus RPC (the second cross-container call) and reads current prices from the same-cycle
`MarketData` reached by walking the PM lineage (`EVALUATED_BY→ANALYZED_BY→DERIVED_FROM`); evaluate
core extracted to `agents/monitor/run.py`; `poll.py` finds `ExecutionRun` lacking `MONITORED_BY`.
Reporter: `build_snapshot` was already fully graph-native, so `poll.py` only adds the trigger
(`MonitorRun` lacking `REPORTED_BY`) and links the edge to the existing `Snapshot` node (no new
`ReporterRun` concept). **Scope decision (operator, 2026-06-22):** all three in one sprint (reporter
trivial; Aura deadline favours finishing the pipeline). **Ruled out:** writing S82 against a real
store first — operator chose code-first, store as a separate follow-on, accepting the Aura-lapse
risk. **Known limitations:** monitor prices = the same ingest snapshot the position was sized from
(fine for one daily cycle); PM portfolio state still fresh-`default_portfolio` per poll.

**Status.** DECIDED + COMPLETE. The graph-pull pull model now spans
provider→scanner→analyst→PM→execution→monitor→reporter end-to-end. S79 = provider→scanner;
S80 = scanner→analyst; S81 = analyst→PM; S82 = execution+monitor+reporter. The remaining blocker is
operational, not architectural: a permanent reachable graph store (see DL-05 / the permanent-store
follow-on) before the Aura trial lapses ~2026-06-29.

**S83 (2026-06-22) — the explicit start: dispatcher trigger + provider becomes graph-pull.**
Before S83 nothing "started a run" in the graph-pull world: the provider self-triggered on a
timer (`ingest_loop`, S78) and the only `Dispatcher` was the P14 **pub/sub** one, which can't
drive containers (no shared in-process bus). **Operator model (2026-06-22):** the dispatcher
places ONE "message on the queue" to trigger run #1; everything downstream is woken by
"completing the prerequisite gate". **Decision:** realise the "message on the queue" as a
`RunRequest` **graph node** (DL-08's graph-as-queue), and make the **provider graph-pull on it**
(`agents/provider/poll.py`: `find_pending` over `RunRequest` lacking `INGESTED_BY` +
`ingest_run_node`; entrypoint swaps `ingest_loop`→`work_loop`). So the dispatcher's RunRequest is
the *single* trigger source and **every** agent (provider included) is uniform graph-pull.
`orchestration/start.py` adds pre-flight checks + `place_run_request`; `orchestration/
local_pipeline.py`'s `cascade_once` runs one poll pass per agent (the fleet does this
continuously, one container each); `scripts/run_local.py` is the runnable demonstrator and
`test_graph_pull_e2e.py` is the first end-to-end proof. **Ruled out:** (a) keeping the provider
timer-self-triggering (rejected — no explicit "start", and two trigger sources); (b) reusing the
pub/sub `Dispatcher` for the fleet (can't — needs one in-process bus across containers). The P14
`Dispatcher` is left intact as the in-process dev path. **Deferred:** a **dispatcher cron** to
place the daily RunRequest on a schedule (operator deferred) — today it's placed by hand / the
demonstrator.

**Status.** DECIDED + COMPLETE (orchestration trigger). The pipeline now has an explicit
single-trigger start and a uniform graph-pull model end to end, proven in one process. Real-fleet
run still gated on the permanent graph store.

---

## DL-08a · Neo4j credentials distribution — KV secret vs plain env var  ·  status: OPEN

**Question.** Do non-master agents receive their Neo4j connection string + credentials via
`ACTIVATE.config` (i.e., in `AGENT_SECRETS` / Key Vault), or as plain Container App env vars
set at deploy time?

- **Option A — KV-distributed (ACTIVATE.config path).** Add `neo4j-uri`, `neo4j-user`,
  `neo4j-password` to `AGENT_SECRETS` for all 12 trading agents; master resolves from KV and
  injects. ✅ Single source of truth; changing the URI requires only a KV update. ❌ Every
  agent appears in `AGENT_SECRETS`; bootstrap failure blocks DB access.
- **Option B — Plain env vars (deploy-time).** Set `NEO4J_URI`, `NEO4J_USER`,
  `NEO4J_PASSWORD` as Container App env vars in `deploy-agents.ps1`. ✅ Simple, zero bootstrap
  coupling; `NEO4J_PASSWORD` is a connection credential, not an API key — acceptable as a
  deploy-time secret. ❌ Changing the URI requires redeploying all agents.

**Recommendation.** Option B for now. Neo4j URI + user are non-sensitive config; password can
be a Container Apps secret (stored in the app, not KV, which is the same security model as other
Container App–managed secrets). KV path is for externally-issued API keys (Tiingo, Alpaca, etc.).
Revisit if agent count or rotation frequency makes deploy-time updates burdensome.

**Decision (operator, 2026-06-21).** **Option B — plain Container App env vars.** Neo4j URI +
user are non-sensitive config; password is stored as a Container Apps secret (in-app, not KV).
KV path reserved for externally-issued API keys (Tiingo, Alpaca, Anthropic, etc.).

**Status.** CLOSED.

---

## DL-07 · Key Vault secret-name + missing-secret reconciliation  ·  status: PARTLY OPEN

Surfaced while wiring Key Vault (B). Two issues found and how they're handled:

**1. The config-consumption bridge is MISSING (the real issue, discovered 2026-06-21).** Nothing
reads `ACTIVATE.config` — a grep for consumers is empty. Agents read credentials via
pydantic-settings with an `env_prefix` (e.g. `ProviderSettings` → `env_prefix="PROVIDER_"` →
`PROVIDER_TIINGO_API_KEY`), **not** from the injected config. So the master→KV→`ACTIVATE.config`
path (S75 + B, proven live) is **plumbing that works but is unconsumed**: no code applies the
returned config to the agent's environment/settings. The injected secrets currently go nowhere.

This couples three things into one piece of work:
  (a) a **config→env bridge** — the agent applies `payload["config"]` to `os.environ` *before* its
      settings/work loop reads them;
  (b) a **canonical credential-naming scheme** — `secret_map` output keys must match the settings
      env-var names (incl. the `PROVIDER_`/etc. prefixes), reconciled with `.env` + the KV secret
      names. Current mismatch: `.env` uses provider-prefixed names (finnhub, fred) plus an `FNP_`
      typo for fmp and *unprefixed* tiingo/alpaca, while `secret_map` emits unprefixed UPPER_SNAKE
      keys with no `PROVIDER_` prefix and a different alpaca spelling. One scheme must align all four;
  (c) the **event/work loop** — agents currently `EHLO → idle_loop()`; they don't run their jobs, so
      nothing accrues data (the "live run for news" is inert until this is wired).
All three are the same next piece: **"agents actually do work"** (the bridge from deployed+idle to
operating). It touches the credential scheme system-wide and handles money — scope it as a
deliberate sprint, not a tail-end patch.

**2. Missing-secret behaviour (FIXED).** `AzureKeyVaultSecretStore.get_secret` *threw* on a
not-found secret, but `Null`/`EnvVar` stores return `""` (and `resolve_config` skips empties). So an
agent entitled to an unseeded secret would fail to activate. Fixed: catch `ResourceNotFoundError` →
return `""`. Lets us seed only the secrets that exist (tiingo, anthropic) without breaking the rest.

**3. Alpaca seeding deferred (safety).** `.env` has both live (`ALPACA_API_KEY`) and paper
(`ALPACA_PAPER_API_KEY`). Seeding *live* trading creds into the pipeline is a money-risk; deferred
until the operator makes the paper-vs-live call. KV currently holds only `tiingo-api-key` +
`anthropic-api-key`.

---

## DL-04 · Model `ops/` in Neo4j as a multi-view engine  ·  status: IDEA (later)

Per DL-01: tag each operational atom once (`Subsystem`/`Gate`/`Runbook`, `DEPENDS_ON`/`AFFECTS`),
then query any lens (departmental / datacentre / lifecycle) and run change-impact ("what breaks
if I touch X?"). Seed from the markdown charters first; graduate to the graph when they stabilise.

---

## DL-05 · Cloud graph store hosting  ·  status: DECIDED (refined 2026-06-21)

**Question.** Where does the graph live for the cloud fleet, given we can't afford paid Aura?

**Decision (refined — operator).** **While the Aura trial lasts: use the real Aura** and stay "as
close to reality as possible" (real managed graph, real persistence/backups). **Pause smartly** —
pause the instance whenever the fleet isn't actively being tested (`aura.ps1 pause`,
`deploy-agents.ps1 down`) to stretch the trial credit and keep PAYG low. **When the trial ends:**
fall back to **in-memory** (`MASTER_GRAPH=memory`, shipped v0.14.0 — registry rebuilds on boot, $0)
until trading needs durable provenance, **then** a small **Azure VM (~$15/mo)**.

So the order of preference is: **real Aura (trial, smart-paused) → in-memory (post-trial) → VM (when
durable data matters).** The in-memory toggle is the *fallback*, not the everyday default.

**Ruled out.**

- *Paid Aura* — cost (operator can't afford it).
- *Aura Free* — auto-pauses after 3 days idle; operator said "no Aura".
- *Tunnel to the operator's machine* — worst of both: needs the laptop always-on (= fleet
  availability) and a DB-over-tunnel security surface, with *none* of a VM's reliability, to solve
  a persistence problem we don't have yet. Actively steered away from.

**Trade-off accepted.** In-memory loses persistence across master *restarts* (a restart empties the
registry; running agents then differ from the master's view). Tolerable at the test-rig stage; the
trigger to move to a VM is "real graph data worth keeping."

## DL-06 · Neo4j edition — Community baseline, but backup is a real deferred cost  ·  status: DECIDED (for now)

**Risk.** The local Neo4j **Enterprise** eval expires at 30 days; a Neo4j **Developer license** was
requested and may not be granted.

**Correction (operator caught this).** Enterprise was **not** a cosmetic choice — ADR-0008 chose it
deliberately for **automated online/differential backup + point-in-time restore**, specifically to
avoid hand-rolling backup management and to make **region moves** clean (a `scenarios.md` case). An
earlier note here glibly said "Community loses nothing you use" — wrong.

**What Community actually costs.** It loses **online/hot backup + PITR**. It does **not** force custom
tooling: `neo4j-admin database dump`/`load` and APOC export (`apoc.export.cypher`) are built-in and
cover region-move backups — but **with downtime and no restore-to-timestamp**. So: Enterprise =
zero-downtime + fine-grained recovery; Community = coarse, downtime-y, but built-in. Early stage
(small graph, brief downtime OK) → Community is adequate. The Enterprise advantage earns its keep at
scale / for true DR.

**Decision.** **Community is the assumed baseline** (free, forever); Enterprise (dev license *or*
managed Aura) is a **documented optional ops upgrade, never an app dependency** — exactly ADR-0008's
own rule ("app logic must not depend on an Enterprise-only feature; ops/backup layer may"). Also:
`NEO4J_DATABASE=neo4j` if no license; APOC Core + GDS still work; affects **local dev only** (cloud is
in-memory per DL-05, CI skips the Neo4j test).

**Open, deferred to "trading has durable data + does region moves":** pick the backup strategy —
Enterprise (license/self-host), managed Aura (backups included, ~$260/mo, currently unaffordable), or
Community dump/load + APOC export on a schedule. Not urgent now (nothing persisted). Tied to the same
horizon as the VM decision (DL-05).

**Small follow-up (when WSL2 returns post-trial):** verify no code/test hard-depends on the named db.

---

## DL-09 · Filter decisions as a labeled training source — measure to improve  ·  status: DRAFT (2026-06-22)

**Question.** The scanner filters drop tickers (`min_price`, `min_average_volume`,
`min_relative_strength`, `max_beta`, `earnings_window`). How do we *prove* a filter is right, and
turn its decisions into labeled data for LLM/predictor training? "I need deterministic methods to
prove the filter is right … We need to be able to measure it in order to improve it." This is to be
**one source among several** feeding a training set.

**The gap.** A dropped ticker vanishes — we never learn what it would have done, so there is no
label and no way to score the filter. `FilterTrace.dropped_by_filter` only *counts* drops
(`{min_relative_strength: 1}`); it carries neither the per-ticker features judged nor the outcome.

**Direction (two mechanisms + a measurement):**

1. **Per-ticker verdict record.** Persist a `FilterVerdict(ticker, decision, filter_fired, features)`
   on each `ScanRun` — every evaluated ticker, survived or dropped, with the exact metrics the filter
   judged (price, avg_volume, relative_strength, beta, days_to_earnings). This is the example's
   *input*; today only aggregate counts survive.
2. **Global `bypass_scanner_filter` flag (default off).** When on, all evaluated tickers become
   survivors (tagged `bypassed=True`) but the verdict still records what the filter *would* have
   decided. Dropped-but-bypassed tickers flow analyst→PM→execution→monitor, so their realized
   outcome becomes the **label**. This is the only way to get the counterfactual — a ticker the
   filter would have dropped, allowed to prove the drop right or wrong.
3. **Confusion matrix per filter** (the evidence, computed deterministically from recorded verdicts +
   realized returns): dropped×down = good drop, dropped×up = missed winner, kept×up = good keep,
   kept×down = wrong keep. Yields per-filter precision and miss-rate → which filters earn their place
   and which throw away winners. Reproducible from stored records, so it is provable, not anecdotal.

**Label decision (operator, 2026-06-22): record BOTH labels side by side.** Each verdict carries
(a) **raw forward return** over a fixed horizon from the bypassed bars — the filter measured *in
isolation*, deterministic, independent of PM behavior; and (b) the **full-pipeline trade outcome**
(close trigger after bypass runs PM→execution→monitor) — the filter *as actually traded*. Two
columns let us separate "the filter dropped a name that rose" from "the filter dropped a name the PM
would have rejected anyway" — i.e. attribute misses to the filter vs to downstream gates.

**Plugs into existing machinery — not a parallel path.** The curator already turns
`ExampleRecord(content, label, source_ref, metadata)` → `DatasetManifest` (train/val/test) →
advisory `Predictor`; its sole source today is `TradeNarrative` lineage labeled by close trigger.
Filter verdicts become a **second assembler** (`assemble_filter_examples`) feeding the same pipeline.

**Platform/pack reading.** The collect→measure→improve *loop* (verdict record, bypass, outcome
labeling, confusion matrix, curator dataset/predictor) is **substrate** — it is the "text-defined
business" self-improvement mechanism. The specific filter *features* are **trading-pack**. So this is
a pack-specific assembler feeding the substrate curator — a clean test case for the platform/pack wall
work queued next.

**Ruled out.** (a) Logging only the aggregate `dropped_by_filter` counts — no per-ticker features and
no outcome, so unmeasurable. (b) Recording verdicts *without* bypass — gives the filter's decision but
never the counterfactual label, so drops can never be scored, only keeps. (c) A bespoke training-data
store outside the curator — duplicates the existing ExampleRecord/Manifest/Predictor loop.

**Status.** COLLECTION SIDE SHIPPED (S88, 2026-06-22, 0.24.00). `contracts/scanner.py::FilterVerdict`
`(ticker, decision, filter_fired, features, bypassed)` rides `FilterTrace.verdicts` (additive, scanner
CONTRACT 0.1.0→0.2.0) and persists on `ScanRun` for free; `ScannerSettings.bypass_scanner_filter` (bool,
default off) emits would-be-dropped tickers as survivors tagged `bypassed` so their downstream outcome
can be observed, while the verdict records the real drop. `filters.apply_filters` reworked to emit a
verdict per ticker (features + first-failing-filter); survivor output unchanged. **Verdict schema +
bypass semantics are now fixed in code** — ready to graduate to an ADR.
**MEASUREMENT ENGINE SHIPPED (S89, 2026-06-23, 0.25.00).** `agents/curator/domain/filter_quality.py`:
`score_filters(verdicts, outcomes) -> FilterScorecard` (pure) computes the per-filter confusion matrix —
`good_drops` (dropped×fell), `missed_winners` (dropped×rose), `precision` per filter — plus overall keep
quality (`good_keeps`/`wrong_keeps`/`keep_precision`); `collect_verdicts(graph)` reads recorded verdicts
off `ScanRun` nodes. Outcomes are **injected** (fixed-horizon forward return per ticker), same discipline
as the forecaster scorecards. Bypassed drops carry a real outcome, so a drop that rose is finally counted
as a missed winner — the counterfactual made measurable.
**REMAINING — wire real outcomes (DL-09 part B.2):** (1) forward-return outcomes from the reference
Postgres (price_cache OHLCV) over a fixed horizon from each scan date; (2) expose a curator capability +
`assemble_filter_examples` → ExampleRecord/Manifest/Predictor; (3) optional surface/CLI to print + persist
the scorecard. The pure measurement core is done and unit-tested.

---

## DL-10 · Staleness gate counts calendar days, not trading sessions  ·  status: CORRECTED (S87, 2026-06-23)

**Resolution (S87).** Chose **option (a)** — count **trading sessions**, with the dependency-free twist of
option (b): `agents/provider/domain/market_calendar.py` (`trading_sessions_between`, a static NYSE holiday
set 2024–2027, weekend-aware) measures session distance; `integrity.py::_stale_tickers` now flags a ticker
only when `trading_sessions_between(latest_bar, window.end) > max_staleness_days`. The setting's `why` was
corrected to read *"three TRADING SESSIONS."* A holiday weekend no longer kills a run. Proven by
`test_market_calendar.py` (4 cases). *Bookkeeping: this status was left OPEN until the DL-19 session
(2026-06-25) verified the fix and closed it.* The EXP-006 `calendar-staleness` Class-1 case (an LLM that
*doesn't* know this fix) remains a useful grounding probe — the firewall's answer key, not a live bug.

---

## DL-10 (original, OPEN 2026-06-22)

**How it surfaced.** First live Aura run (3 tickers, 2026-06-22). The batch trace showed
`analyst: scored=0 rejected=2`, both rejected `provider market data degraded` — i.e. the analyst
bailed at `run.py:39` (`market.quality.used_fallback`) before scoring anything. Tracing upstream:
`MarketData.quality` = `{used_fallback: True, stale_tickers: (AAPL, GOOGL, MSFT), notes:
(stale_or_missing_tickers,)}`. The latest bar for every ticker was **2026-06-18, only 4 calendar
days before the window-end** — fresh data, yet condemned as stale.

**Root cause.** `agents/provider/domain/integrity.py::_stale_tickers` measures
`(window.end - latest_bar).days > max_staleness_days` in **calendar days**, with the default
`max_staleness_days = 3`. But the setting's own `why` says *"older than three **sessions**"* — the
intent is **trading sessions**, the implementation is **calendar days**. They diverge across any
market closure:

- Thu Jun 18 = last real session · Fri Jun 19 = Juneteenth (NYSE closed) · Sat–Sun = weekend ·
  Mon Jun 22 = run date. Jun 18's close is the **freshest data that can exist** — zero sessions stale
  — but **4 calendar days** old → `4 > 3` → whole batch flagged degraded → entire pipeline produces
  nothing. One ordinary holiday weekend silently kills every run.

**Why it matters.** A calendar-day staleness gate conflates *"the data is genuinely old"* with
*"the market was closed."* Every Monday after a holiday Friday (and any Tuesday after a Mon holiday)
trips it. The trade side of the pipeline goes dark precisely when nothing is actually wrong. This is
a correctness flaw in the degraded-data guard, not a tuning nit.

**Options (not yet decided):**

- **(a) Count trading sessions** between `latest_bar` and `window.end` using a market calendar
  (exchange holiday + weekend aware). Correct, but introduces a calendar dependency/source.
- **(b) Skip weekends + a static holiday set** in the day-count. Cheaper, no live dependency, but the
  holiday list must be maintained and is exchange-specific.
- **(c) Widen the default** (e.g. `max_staleness_days = 5`) as a stopgap. Trivial, but a band-aid: a
  4-day holiday stretch (e.g. Thanksgiving, year-end) can still exceed any fixed calendar bound while
  the data is current. Masks rather than fixes.

**Ruled out.** Leaving it calendar-day with the default 3 — demonstrably breaks on a normal holiday
weekend (this run). Also note the `--real` demo path used the default 3 while the in-memory demo
passes `max_staleness_days=7`, so the in-memory tests **never exercised the degraded path** — the
gap was invisible until live data hit it.

**Status.** RESOLVED (S87, 2026-06-22, 0.23.04) — shipped **option (b): trading-session count via a
static NYSE holiday set + weekend exclusion**, dependency-free, over option (a)'s market-calendar
library. `agents/provider/domain/market_calendar.py::trading_sessions_between` counts NYSE sessions in
`(latest_bar, window_end]`; `integrity._stale_tickers` flags `> max_staleness_days` sessions instead of
calendar days. The Jun-18→Jun-22 case is now **1 session** (was 4 days), so fresh data across a holiday
weekend no longer kills the batch; a genuinely old bar still flags. Holiday set covers 2024–2027 (a date
past the window falls back to weekday counting); upgrade path = `exchange_calendars` /
`pandas-market-calendars` when the window needs extending or per-exchange precision. This is a pack-level
(trading) calendar living in the provider agent, not substrate.

---

## DL-11 · Aura backup/restore — API surface vs console-only ops  ·  status: NOTED (2026-06-22)

**From the Neo4j testing track (2026-06-22), verified against the live Aura Professional instance:**

- **Snapshot create + list work over the management API** (`POST`/`GET /v1/instances/{id}/snapshots`).
  `infra/aura.ps1 snapshot|snapshots` drive them. Note the create response carries **only**
  `snapshot_id` (not `status`/`timestamp`) — those appear in the list once the backup completes;
  the script was fixed to stop dereferencing the absent fields.
- **In-place restore is NOT available over the API.** `POST /v1/instances/{id}/restore` returns
  **`403 {"error": "Requested endpoint is forbidden"}`** for this key/tier. Restore is a **console-only**
  action (console.neo4j.io → instance → Snapshots → ↺). `infra/aura.ps1 restore` therefore cannot
  drive it; kept for the day the endpoint is permitted, but treat restore as a manual console step.
- **No byte-size in the API.** Snapshot objects expose `{snapshot_id, status, timestamp, profile,
  exportable}` — no size. On-disk store size is observable only from inside the DB via Browser
  `:sysinfo`; the serialized property payload of one batch run measured ~27.7 KB (MarketData node
  dominates at ~24 KB).
- **Console timestamps are local (AEST/+10); the API reports UTC** — a 05:30:11 UTC snapshot shows as
  15:30:11 in the console. Worth remembering when matching a CLI-triggered snapshot to a console row.

**Restore proven, end to end.** Planted a `RestoreProbe` sentinel node *after* a snapshot, restored
from that snapshot via the console, and confirmed the sentinel's label no longer exists — the DB rolled
back exactly to the snapshot point while all pre-snapshot pipeline data survived. Backup/restore is
trustworthy; the only constraint is that restore is a manual console operation, not scriptable here.

**Status.** NOTED — operational finding, no open decision. Revisit `aura.ps1 restore` if Neo4j later
exposes the restore endpoint to API keys.

---

## DL-12 · Platform/pack separation — master grant policy is the first leak  ·  status: IN PROGRESS (2026-06-22)

**Frame (ADR-0012).** The master is **substrate** (fleet bootstrap mechanism); it must not encode
trading-pack knowledge. `agents/master/grants.py::DEFAULT_GRANTS` violated this — it hardcoded all 12
trading agent types and domain capabilities (`broker`, `data_feeds`, `ohlcv`, …) inside the substrate.
First named leak to close in the platform/pack split.

**Step 1 shipped (2026-06-22): the injection seam.** `MasterAgent.__init__` now takes
`grant_policy: GrantPolicy | None` (`GrantPolicy = Mapping[str, dict[str, object]]`); `activate()`
reads the injected policy, not the module global. Default still falls back to `DEFAULT_GRANTS` so
behavior is unchanged and all callers keep working. Proven by a test that injects a custom policy: a
`widget` type (absent from `DEFAULT_GRANTS`) activates while `scanner` (present in `DEFAULT_GRANTS`,
absent from the injected policy) is rejected — i.e. the master genuinely consults the injected policy.
This is the load-bearing seam; nothing else in the split can proceed without it.

**The hard decision still open — WHERE the trading policy lives + HOW the master receives it.** The
import boundary (`kernel ← contracts ← agents ← orchestration/surfaces`) blocks the obvious move:

- The trading grant policy is pack config → it belongs in a pack module (e.g. `orchestration/packs/`).
- But `agents/master/entrypoint.py` (the master's container bootstrap) is in the **agents** layer and
  **cannot import** `orchestration/packs/` — agents may not import orchestration. So the production
  composition point for the master cannot pull a orchestration-located policy by import.

**Options (not yet decided):**

- **(a) Policy as data the master loads from config** (a JSON/YAML grant-policy file, path via
  `MasterSettings`; the trading pack ships the file). Substrate gains a generic "load a grant policy"
  mechanism; the pack supplies content as *data*, never as a Python import → no boundary violation.
  Matches the container-per-agent "agents start braindead, configured by data" model. Most correct.
- **(b) A top-level `packs/` package importable by `agents`** — inverts the dependency (substrate
  importing pack); contradicts ADR-0012. Rejected.
- **(c) Leave `DEFAULT_GRANTS` in `agents/master` as the default, relocate only the *type knowledge*
  later** — defers the real cut; the substrate still ships trading data. Stopgap only.

**Ruled out.** Importing pack grants into the master entrypoint (option b's boundary inversion).

**Status.** GRANT LEAK CLOSED (S84, 2026-06-22) — **option (a) chosen and shipped.** The 12-agent
grant table now lives in `orchestration/packs/trading_grants.json`, loaded by path via
`MasterSettings.grant_policy_path` (`load_grant_policy` in `agents/master/grants.py`) and injected by
the master entrypoint — never imported, so the `agents↛orchestration` boundary holds. `DEFAULT_GRANTS`
is deleted; with no injected policy the substrate knows no agent types. Deployed behavior unchanged
(loaded policy == old table, asserted). 0.23.01 (PATCH).

**BOTH MASTER LEAKS CLOSED (S85, 2026-06-22, 0.23.02).** The second leak,
`agents/master/secret_map.py::AGENT_SECRETS`, got the identical treatment: the per-agent
`(kv_name, env_name)` entitlement table moved to `orchestration/packs/trading_secrets.json`, loaded
via `MasterSettings.secret_map_path` (`load_secret_map`) and injected into `MasterAgent`;
`resolve_config(agent_type, store, secret_map)` now takes the map as a parameter. `AGENT_SECRETS`
deleted. **The master substrate now names zero trading concepts** — grants and secrets are both
pack-supplied data.

**DEPLOY WIRING DONE (S86, 2026-06-22, 0.23.03) — and the master *image* stays pack-agnostic.** Rather
than bake the pack JSONs into the substrate image (which would re-couple them), the pack policy travels
as **deploy-time config**: `_resolve_pack` in the entrypoint resolves each policy **base64 env content
(cloud) → file path (local) → None**. `deploy-agents.ps1` base64-encodes the two pack JSONs into
`MASTER_GRANT_POLICY_B64` / `MASTER_SECRET_MAP_B64` (like `MASTER_PRIVATE_KEY_PEM_B64`);
`docker-compose.yml` mounts `orchestration/packs/` read-only and sets the `MASTER_*_PATH` vars. The
master `Dockerfile` is **unchanged** — the same image runs any pack. `parse_grant_policy`/
`parse_secret_map` (JSON-string core) added; `load_*` delegate. The b64-content path is unit-tested; the
ps1/compose lines are inspection-verified (not CI-run). **DL-12 is now complete** for the master; the
only remaining ADR-0012 item is the `contracts/` substrate/pack split, deferred to a 2nd pack.

---

## DL-13 · Message-layer schema enforcement — bus IS bilaterally validated  ·  status: NOTED (2026-06-22)

**Trigger.** A flow audit (2026-06-22) of the two message paths (P14 bus RPC vs DL-08 graph-pull)
concluded the bus path was a schema gap: *"the bus does not validate the payload against
`Capability.request`; the handler is expected to call `model_validate` itself."* **Verified against the
code — that conclusion is wrong.** Recording the corrected reality so the audit's table is not trusted as-is.

**What the code actually does.** Every capability handler is registered through
`kernel/agent.py::AgentBase._bus_handler`, which wraps it:

```python
def wrapped(payload):
    request_model  = capability.request.model_validate(payload)    # validates IN
    result         = handler(request_model)                        # handler gets a MODEL, not a dict
    response_model = capability.response.model_validate(result)     # validates OUT
    return response_model.model_dump(mode="json")
```

`AgentBase.bind` (agent.py:37) and even the supervisor's hand-rolled `bind`
(`agents/supervisor/agent.py:69`) both route through `_bus_handler`. So **request and response are
schema-validated against the declared `Capability` types on every bus call**, by the framework, not by
handler discretion. The raw `InProcessBus.request` is schema-agnostic (it routes dicts + enforces
envelope + capability-exists + `caller_authorized`), but no agent registers a raw handler — they all go
through `_bus_handler`. Handlers' own `XRequest.model_validate(request)` calls are redundant
belt-and-suspenders. **The bus path is a typed, bilateral boundary, symmetric with graph-pull.**

**The one genuine residual gap — pub/sub events.** The `subscribe()` path has **no** `_event_handler`
wrapper analogous to `_bus_handler`; a topic carries no declared schema. Event subscribers validate by
convention (e.g. `provider._on_market_data_request` calls `DataRequest.model_validate(event)`), but
nothing in the framework enforces it. Events are fire-and-forget triggers, so the stakes are lower than
request/response, but this is the real "by the handler's discretion" case. **Optional hardening
(backlog, low priority):** an `_event_handler` wrapper + per-topic typing to make the event path
framework-enforced too.

**Accuracy nits in the audit.** (1) `model_dump(mode="json")` does not validate — it serializes an
already-constructed (hence already-validated) model; the producer's guarantee is from model
*construction*. (2) The graph-pull strength is real: producer constructs (validated) → `model_dump` →
consumer `model_validate`, both importing the *same* contract class.

**Status.** NOTED — no action required; request/response is bilaterally enforced on both transports.
Event-path validation is the only open hardening item, deferred.

---

## DL-14 · Operational path map — spine is live, the rest is aspirational or a gap  ·  status: NOTED (2026-06-22)

**Trigger.** Same flow audit (DL-13) drew 13 source→sink edges, raising the concern that the agent
chain has many concurrent live paths. **Verified: it does not.** The diagram conflates *contract
capabilities* with *what is actually running*. Classified by operational status:

- **Class A — the live spine (7 agents on `work_loop`).** RunRequest → provider → scanner → analyst →
  PM → execution → monitor → reporter (audit edges 1-7, 9). This is the only concurrent live flow — a
  linear graph-pull chain, one writer per stage, exactly what `scripts/run_local.py` /
  `test_graph_pull_e2e.py` exercise.
- **Class B — graph re-read, not a separate message** (edge 10). PM/monitor re-read the same
  `MarketData` node by walking lineage; no new path.
- **Class C — NOT wired (the 5 `idle_loop` agents).** forecaster, operator, supervisor, curator,
  researcher are still braindead. So audit edges 11 (forecaster `ShadowPrediction` — advisory, never
  gates even when wired), 12 (operator→supervisor), 13 (→supervisor faults) are aspirational, not running.
- **Class D — contract capability, unwired in graph-pull (a real gap).** Audit edge 8 (monitor
  `CloseDecisionSet` → execution `execute_close`): the monitor *decides* closes (writes `CloseDecision`
  nodes with `pnl_cents`), but `agents/execution/poll.py` has no close-handler and `monitor_pm_node`
  takes no broker — so **positions are opened (execution submits buys via the broker) but closes are
  decided and never executed** against a broker in the current operational path. Acceptable for
  paper/graph-tracked positions; an honest incompleteness vs the diagram. Wire the close-execution loop
  before live broker trading.

**Status.** NOTED. Reassurance: the live system is the linear spine (A), not a many-path tangle. Open
items: activate the 5 control-plane/advisory agents (C) and wire the close-execution loop (D) — both
out of scope until needed; flagged so they are not mistaken for already-working.

---

## DL-15 · DB placement — substrate registry should not use Neo4j  ·  status: SUPERSEDED (2026-08-05) by [ADR-0014](decisions/0014-postgresql-system-of-record.md) — the premise is gone: there is no Neo4j runtime to move the registry off. Verified 2026-08-05: zero `neo4j` references in `kernel/`, `agents/`, `orchestration/`; the single survivor is a stale capability declaration in `contracts/master.py:99` (DRIFT-033), not a live dependency.

**Trigger.** ADR-0012 platform/pack wall + DL-12 (S84–S86) separated master grant/secret policy
from the trading pack. The next step in the split: the substrate registry (AgentInstance, Session,
CapabilityGrant, CapabilityRoute nodes currently stored via `GraphStore`) is backed by Neo4j —
a choice inherited from the trading pack's provenance graph, not from a substrate need.
**Operator direction:** "substrate (plumbing) should have its own DB. Neo4j belongs to the trading
system because it is the requirement that came from trading demands."

**Two distinct workloads, currently sharing one store:**

1. **Substrate registry** — Session, AgentInstance, CapabilityGrant nodes written by the master.
2. **Trading-pack provenance graph** — RunRequest → provider → scanner → analyst → PM → execution →
   monitor → reporter lineage, graph-traversal-heavy. Cypher queries throughout `kernel/graph_cypher.py`.
   Grows ~55 nodes / ~60 rels per run. Neo4j is genuinely the right fit here.

**Research complete — see [docs/research/db-placement/db-placement.md](research/db-placement/db-placement.md) for full
capability mapping against AuraDB Free, Azure free-tier options, and self-host alternatives.**

**KEY FINDING (2026-06-23): the substrate registry writes are audit-only. Code inspection of
`agents/master/agent.py` and `agents/master/store.py` shows:**

- `activate()` computes grants entirely from `self._grant_policy` (in-memory dict loaded from JSON)
  and returns them in `ACTIVATEMessage`. The `write_agent_instance()` + `write_capability_grant()`
  calls are **write-only audit records** — nothing reads them back to route work or make decisions.
- `drain()` does one `get_node("AgentInstance", ...)` to verify existence before stamping
  drain_reason/drain_at. A consistency guard inside the master itself, not external lookup.
- No agent outside the master, no Cypher pipeline query, no orchestration code reads Session /
  AgentInstance / CapabilityGrant. `grep -rn "Session\|AgentInstance\|CapabilityGrant"` across
  `agents/ orchestration/ kernel/` finds only `agents/master/`.

**The substrate is already effectively in-memory.** Running the master with `InMemoryGraphStore`
(which all tests use — and they pass) is functionally identical to Neo4j for anything that matters.
The Neo4j writes are a pure audit trail. **Option (c) is already the de-facto reality.**

**Direction — RECOMMENDED: drop the graph writes from the substrate master; make InMemoryGraphStore
the only backed store for the substrate.** If an audit trail is wanted later, add it as a
separate lightweight concern (Azure Table Storage append log, or a JSON file). Do not keep a
Neo4j dependency in the substrate just for writes nobody reads.

**Trading pack stays on Neo4j regardless.** All Cypher queries and `kernel/graph_cypher.py` /
`kernel/graph_support.py` / `kernel/graph_neo4j.py` are unchanged. AuraDB Free covers years of
daily single-batch runs (~55 nodes/run → 200K node ceiling hit after ~3,600 runs). Self-hosting
Neo4j Community Edition in the existing Azure Container Apps environment is the zero-cost escape
hatch if Aura Free limits bind or the service becomes unavailable.

**AuraDB Free limits — note inconsistency in official sources:** FAQ states 200K nodes / 400K rels;
product page may show 50K / 175K. **Verify in console before planning against either number.**
No automated backups on Free tier; restore is console-only (DL-11). Auto-pauses on inactivity.

**Ruled out.** (b) Separate Neo4j instances — substrate still depends on trading-pack DB choice.
Cosmos DB Gremlin API for the trading pack — free and Azure-native but requires rewriting every
Cypher query as Gremlin; high migration cost for a working system.

**Status.** OPEN — analysis complete; decision and sprint pending. Recommended sprint: remove
`graph` parameter from `MasterAgent.__init__` and `store.py` writes; master becomes graph-free.
One remaining question: (1) verify AuraDB Free actual node limit in console (planning only).

## DL-16 · Alpaca is the primary OHLCV feed; Tiingo retained but demoted  ·  status: DECIDED (2026-06-24)

**Trigger.** A 100-ticker live populate run (`run_local.py --real --universe scripts/universe_sp100.txt`)
returned `0/100` bars with quality `source_unavailable`. Direct probing showed **Tiingo returns
HTTP 429 (Too Many Requests)** — its free tier (~50 req/hr) cannot serve a 100-symbol batch, because
`TiingoDataSource.fetch_ohlcv` issues **one HTTPS call per ticker** (`/tiingo/daily/{ticker}/prices`).
Even a 2-symbol fetch 429'd once throttled for the hour. ADR-0006 had made Tiingo the primary
full-universe feed; that assumption does not survive a real S&P-100-sized run.

**Decision (operator: "we can use Alpaca finance after all").** Make **Alpaca the primary OHLCV
source.** Alpaca's market-data bars endpoint (`/v2/stocks/bars`) accepts **up to ~100 symbols in a
single request**, so one call covers the whole universe and structurally avoids the per-symbol rate
limit. Free `iex` feed returns complete daily bars for liquid large-caps (probe-verified). Existing
`ALPACA_*` credentials already in `.env`; the `.env` header had long noted "Tiingo (primary) +
Alpaca (failover) cover the OHLCV need" — this realises that failover intent, but promotes Alpaca to
primary rather than fallback.

**Build.** New `agents/provider/alpaca_data.py` (`AlpacaDataSource`) implements the price-source side
of the `DataSource` port: batch `fetch_ohlcv` with internal `next_page_token` pagination (network in
`_download*`, `# pragma: no cover`; parsing in `_parse_bars`/`_bar`, 100% covered). `ProviderSettings`
gains `alpaca_data_base_url`, `alpaca_api_key`, `alpaca_api_secret`, `alpaca_data_feed` (default
`iex`), `alpaca_data_timeout`. `market_source_from_settings` now wires Alpaca as `price_source`.

**Ruled out.** *Tiingo→Alpaca failover wrapper* — more resilient and matches the original `.env` note,
but needs a failover-source abstraction + error taxonomy; deferred (operator chose "Alpaca primary"
for the simplest clean populate). *Configurable price source (setting-selected)* — flexible but adds a
knob with no immediate consumer. *Stooq* — already in-repo and free, but single-symbol CSV fetches
share Tiingo's per-symbol shape. Tiingo code is retained (still tested) and can become the failover.

**Follow-ups (later).** (1) Optional Tiingo→Alpaca failover wrapper if Alpaca `iex` coverage proves
thin for any name. (2) Decide `adjustment` policy (raw vs split/dividend-adjusted) for momentum
inputs — currently raw. (3) Supersede note on ADR-0006's "Tiingo primary" line.

## DL-17 · Chunked ingest — paced sub-batches reassembled into one batch  ·  status: DECIDED (2026-06-24)

**Trigger.** With Alpaca solving OHLCV (DL-16), a 100-ticker run was still `DEGRADED`. Measured
cause: `validate_bars` sets `used_fallback = bool(notes)`, and the **optional fields are all
Finnhub, fetched one HTTPS call per ticker** — 100 tickers × 4 fields (fundamentals, news, sectors,
earnings) = **~400 calls fired in a burst**, far over Finnhub free's ~60/min, so all four pillars
fault and taint the batch. (Sentiment/AV is not requested by ingest, so its 25/day cap is moot.)

**Operator framing.** "Put the batch back together: first 25 are asked for and downloaded, marked
as batch B part one, and so on until the last ticker, then we put the batch together and send it off
down the chain. From the point of view of model training the batch is the best breakdown of
information — it needs regular intervals. Test it at various times of day, measure, re-run with other
parameters until we improve." → **continuous improvement: guess, run, measure, re-run.**

**Decision.** Add a chunked ingest path: split the universe into `ingest_chunk_size` sub-batches,
fetch each through the provider's normal `_get_market_data` (its own fault boundary + a per-chunk
`MarketSnapshot` "part"), `sleep(ingest_chunk_delay_seconds)` between chunks so the aggregate
per-minute call rate stays under the free-tier ceiling, then **reassemble one `MarketData` batch over
the full universe** (concatenated bars, merged field dicts, folded quality) and write it as the single
downstream work item the scanner consumes. `ingest_once` dispatches to the chunked path when
`ingest_chunk_size > 0`; default 0 preserves single-shot behaviour. New module
`agents/provider/ingest_chunked.py`; tunables `ingest_chunk_size`, `ingest_chunk_delay_seconds`;
`run_local.py --chunk-size/--chunk-delay`.

**What it fixes vs not.** Chunking clears the **Finnhub rate-limit** degradation (the 4 optional
pillars). It does **not** fix two independent OHLCV-side taints seen on the 100-run: BK returned only
19 bars on Alpaca `iex` (thin coverage → `stale_or_missing_tickers`) and one name had a >4σ daily
move (`daily_move_sigma_anomaly`). Those are separate follow-ups (drop/relax universe, or revisit
`max_daily_move_sigma`), not rate-limit problems.

**Educated first guess (to be tuned empirically).** `chunk_size=12` (48 Finnhub calls/chunk),
`delay=65s` → ~48 calls/min, ~9 chunks ≈ 9 min for 100 names. The right values depend on the live
per-minute cap and time-of-day latency — exactly the measure-then-tune loop the operator described.

**Ruled out.** *Make the optional pillars non-tainting* (taint=False) — would let trades flow on
price-only data, but silently drops the quality signal the analyst is meant to honour; a real policy
question deferred. *Parallel fetch with backoff* — more throughput but harder to keep under a hard
per-minute cap and to reason about deterministically.

**Measurement log (guess → run → measure → re-run).**

| # | Params | Result | Read-off |
| --- | --- | --- | --- |
| 1 | single-shot (100 at once) | notes: `daily_move_sigma_anomaly`, `stale_or_missing_tickers`, **`fundamentals_/news_/sectors_/earnings_degraded`** | Finnhub 429s on the ~400-call burst → all 4 optional pillars fault |
| 2 | `chunk_size=12`, `delay=60s` (~9 min, ~04:05–04:14 AEST) | notes: `daily_move_sigma_anomaly`, `stale_or_missing_tickers` only — **all 4 Finnhub pillars cleared**; news populated (1810 headlines) | ✅ pacing fixes the rate-limit degradation; the 2 remaining taints are OHLCV-side, not rate-limit |
| 3 | 99 tickers (BK dropped), `chunk_size=12`, `delay=60s`, `max_daily_move_sigma=8.0` (~14 min, 04:22–04:36 AEST) | notes: `daily_move_sigma_anomaly`, **`news_degraded`** | ✅ BK drop killed staleness; ✗ sigma still trips and ✗ news re-faulted — see read-offs below |

**Diagnostics behind run 3.** BK on Alpaca `iex`: 18 bars, latest 2026-05-20 (~5 weeks stale);
`sip` feed is 403 on the free plan → BK genuinely unservable, dropped. The sigma outlier is **INTC
+11.7 % intraday on 2026-05-08** (a real earnings move), global z = 6.6 across the 99-name pool.

**Key architectural read-off (run 3).** `sigma=8.0 > 6.6` yet the anomaly *still* fired — because the
chunked path calls `_get_market_data` **per chunk**, so `validate_bars` computes sigma over each
12-ticker chunk, not the full universe. INTC's z *within its chunk* exceeds 8.0, and `_combine_quality`
unions the per-chunk notes. **Per-chunk validation is the wrong altitude: quality must be assessed on
the reassembled batch, once.** Separately, `news_degraded` reappeared (clean in run 2) — chunk=12/
delay=60 is borderline for Finnhub; one chunk 429'd this run. Time-of-day variance, as predicted.

**Next iterations (open).** (a) **Validate the reassembled batch once** (separate fetch from
validate in the chunked path) so sigma/staleness see the full universe — then `sigma=8.0` clears
INTC. (b) **More conservative pacing** (smaller chunk and/or longer delay) to make Finnhub reliably
clean, not borderline. (c) Whether `max_daily_move_sigma=4.0`→`8.0` should be the committed default
(the check should catch corrupt ~30σ prints, not legit 6.6σ earnings moves). (d) Only after a clean
batch do trades actually flow — chunking was necessary but not sufficient.

## DL-18 · Continuous-improvement system — map, measure, tune, gate  ·  status: PROMOTED → ADR-0013 + S90–S95 (2026-06-24)

> Promoted to **[ADR-0013](decisions/0013-continuous-improvement-system.md)** (storage: all on the
> graph) with sprint specs **S90–S95** (phase P16). This entry is the originating map/design.

**Trigger.** DL-17's pacing work was hand-tuned: guess → run → measure → re-run, with the operator
reading flags off a trace and editing env vars. That loop must become a **system**. Operator
direction: *"PROVIDER_INGEST_CHUNK_SIZE / _DELAY should be **configurable, not settable** parameters.
Create the whole continuous-improvement system — map what processes we have, measure them, tweak
parameters, improve."*

**Configurable vs settable — the distinction that drives this.**

- *Settable* (today): a human edits `PROVIDER_INGEST_CHUNK_SIZE=12` in `.env`; one value, no memory
  of what it scored, no comparison, no promotion gate.
- *Configurable* (target): a parameter lives in a **named, versioned ParameterSet** the run loads;
  the system measures the run, attributes the metrics to that set, sweeps alternatives, and
  **promotes** the winner via the existing ACTIVATE channel. Env stays only as the local-dev override.

**What already exists (do not rebuild).**

- **Parameter catalogue** — `kernel/config.py` `tunable()` + `describe()` already expose ~145
  justified, bounded params across 13 agents (name, env var, default, why, ge/le, unit).
- **Measurement prototypes** — forecaster IC/return scorecard (`forecaster/domain/return_scorecard.py`),
  curator filter confusion matrix (`curator/domain/filter_quality.py`), sentiment
  champion–challenger + eval-gate (ADR-0010). Siloed; each proves one slice of the loop.
- **Delivery channel** — master → agent ACTIVATE config injection (entrypoints `_apply_config`).
- **Measurement substrate** — the provenance graph already records every run's lineage.

**The map — processes → key tunables → candidate metrics.**

| Process | Example tunables | Metric to optimise |
| --- | --- | --- |
| provider / **ingest** | `ingest_chunk_size`, `ingest_chunk_delay_seconds`, `max_daily_move_sigma`, `max_staleness_days` | degradation rate (pillars clean / total), total fetch time, returned/requested |
| scanner | `min_average_volume`, `min_relative_strength`, beta/volume gates | survivors/universe, downstream realised-return of survivors |
| analyst | indicator weights (`settings_indicators.py`, 21 knobs), confidence floor | scored/eligible, hit-rate, calibration |
| portfolio_manager | sizing, sector/RR gates | approved/scored, realised PnL per decision |
| execution | broker/slippage params | fill rate, slippage vs expected |
| monitor | exit thresholds, holding window | premature-exit rate, captured vs left-on-table |
| reporter | — (metrics sink) | profit_factor, expectancy |
| forecaster | booster/IC params (existing scorecard) | information coefficient |
| operator LLM | `system_prompt`, model, reasoning effort | eval-set score (ADR-0010 gate) |

**The loop — four layers.**

1. **Catalogue** — aggregate `describe()` across *every* agent settings class into one registry
   (today it runs per-class; nothing unifies them). This is the menu of what is tunable + its bounds.
2. **Measure** — write a per-run `RunMetrics` record keyed by `(process, parameter_set_id, run_id,
   as_of)`; start with ingest (degradation rate, fetch seconds, returned/requested), reuse the
   forecaster/curator scorecards for their slices.
3. **Experiment** — load a named `ParameterSet` instead of ad-hoc env; run champion vs challenger;
   record both sets' metrics against the same as-of so they are comparable.
4. **Gate** — promote a challenger only when its metric ≥ champion with no regression on the
   guardrails (generalises ADR-0010's eval-gate from prompts to *any* parameter set). Promotion
   updates the active set delivered via ACTIVATE; provenance records who/why.

**First concrete target (closes the DL-17 loop).** Make `chunk_size`/`delay`/`max_daily_move_sigma`
a ParameterSet; metric = (Finnhub degradation rate, fetch time) measured across N runs at different
times of day; sweep a small grid within the tunables' bounds; promote the fastest set that holds 0
degradation. This is the manual DL-17 loop, automated and recorded.

**Phased build (proposed sprints).**

- **CI-1 Catalogue** — `describe_all()` over every agent settings class → one registry + a read
  surface (extend the existing tunables view).
- **CI-2 RunMetrics** — graph node + writer; populate from the ingest trace first.
- **CI-3 ParameterSet** — named/versioned set loaded by a run (replaces ad-hoc env for experiments);
  `run_local --parameter-set <id>`.
- **CI-4 Experiment + compare** — run two sets on one as-of; tabulate metric deltas.
- **CI-5 Gate + promote** — no-regression promotion + ACTIVATE delivery; generalise the eval-gate.
- **CI-6 Optimiser** — sweep within bounds (grid first, smarter later); start on the ingest target.

**Open questions.** (a) Where does ParameterSet live — graph node, JSON in repo, or Cosmos (DL-15)?
(b) Metric storage — RunMetrics on the provenance graph vs the metrics/Prometheus plane already wired.
(c) How much overlaps the curator's existing "filter decisions as training source" (DL-09) — likely
CI-2/CI-4 should subsume it rather than duplicate. (d) Relationship to ADR-0010 — the gate should be
one mechanism, not two.

## DL-19 · Etalon-first, and laws as a creative space (not a solution)  ·  status: DIRECTION (2026-06-24)

**Trigger.** After wiring the `tuner`/`librarian` bindings and writing the etalon
(`ops/agent-genesis.md`), the AI leapt toward a bundle *generator*. Operator correction:
**"Too early. Create the ETALON first — the bundle becomes the first etalon v0.1; we need to show
perfection in a finished trading-agent bundle. I want to cover creativity as well. The overall
solution will be owned by agents; the solution will have to be discovered within the space boundaries
which laws define."**

**Two directional locks.**

1. **Etalon-first sequencing.** The generator is the far endgame, **deferred**. The immediate work is
   to bring the trading-agents bundle to *demonstrated perfection* — and that finished bundle **is**
   etalon v0.1. You cannot reproduce a reference that is not yet a reference; a copier would only
   reproduce gaps. Gate to start the generator = etalon v0.1 proven complete.
2. **Laws define a space, not a solution — creativity is first-class.** Laws/charters/gates/NEVERs
   draw the **boundaries of a solution space**; the **solution is owned and creatively discovered by
   the agents** inside it. Constraints say *where the walls are*, never *what to find in the room*. A
   bundle that is only gates is a **cage**, and a cage discovers nothing — every charter must leave
   **deliberate room for discovery**. Test of a good boundary: it rules out the unsafe/incoherent
   without prescribing the answer; if a law forces a single outcome it has become the solution — suspect
   it. This extends LAW-01 from "tune the dials" to "search the lawful space for a better solution."

**Recorded in** `ops/agent-genesis.md` (Sequence note + "Laws define a space, not a solution" section - deferred-generator endgame) and memory [[etalon-bundle-genesis]].

**Implication for the work.** The near-term backlog is *perfecting the bundle*, not building meta-
machinery: finish the laws (green clauses), the pipeline that actually trades (DL-17 line), the
recorded decisions, and — newly — audit each charter for whether it leaves room for creative discovery
rather than over-constraining. The CI-1…CI-6 experimentation machinery and the generator both wait
behind a perfect etalon.

## DL-20 · Discovery is research-driven, feasibility-gated, and deliberated  ·  status: DIRECTION (2026-06-24)

**Trigger.** DL-19 established that laws define a *space* and agents discover the solution within it,
but left the **discovery mechanism** abstract. Operator fills it in: creativity + a *solution field* +
a mandatory research/feasibility front-end, run autonomously by the AI.

**The principle.**

1. **Solution field, not an answer.** A problem can be designed "this way or that", each with
   different implications. The solution is **created on-the-fly**, not retrieved — there is rarely one
   right answer, there is a field of viable ones to be weighed.
2. **Research precedes any offered solution.** Inputs: **legislative / governance**, **typical
   scenarios**, **best industry practice**, and the **constraining factors** of the specific case —
   time, money, physical placement, CPU/compute, other resources. You cannot reason about a solution
   without first finding the facts.
3. **Feasibility gates** — the questions any sane engineer asks *before committing*, answerable only by
   research:
   - **FEAS-POSSIBLE** — is the solution possible at all?
   - **FEAS-READY** — are we scientifically / technically ready to solve what is being asked? (is it
     tractable with current knowledge and tools?)
   - **FEAS-BUDGET** — is it possible within the money / time / compute / physical-resource envelope?
   A red feasibility gate stops the build before it starts — and is itself a *finding*, recorded.
4. **Creative, deliberated research.** Develop **several candidate solutions** and **argue them** — a
   **group of three agents** deliberating (generate → critique → converge), not a single guess. The
   exact council roles are themselves a solution-field, left open (do not prescribe — DL-19).
5. **Autonomy — on the AI's side of the screen.** The operator cannot help with technical detail and
   should not have to. The AI runs the research and the deliberation and brings back a **reasoned
   recommendation with its trade-offs and feasibility verdict** — the decision, not the derivation
   (LAW-04 legibility: surface the choice, hide the weeds unless asked).

**Relationship to existing parts.** This is the front-end that precedes `tunable()` tuning
(Experimentation tunes *within* a chosen design; this *chooses the design*). It generalises
champion–challenger from parameters to whole solutions. It reuses the platform's `researcher` agent
seed (P7) but is larger: a research/feasibility/solution-design discipline.

**Identified bundle (charter pending — record now, build while perfecting the etalon).**
A **Research & Solution-Design** bundle: a deliberative (≈tri-agent) council that, given a problem,
gathers facts (law/scenarios/practice/constraints), runs the feasibility gates, develops and argues
candidate solutions, and returns a recommendation. Not built now (etalon-first, DL-19); named so the
boundary is on record.

## DL-21 · DSPy steers the deliberation — compile the role prompts, don't hand-write them  ·  status: DIRECTION (2026-06-24)

**Trigger.** Ran the same debate ("Buy AAPL", momentum +0.6 / RSI 55 / earnings in 4 days) twice on
live OpenAI. The **conclusion was stable** (both OVERTURN — the decision is genuinely weak) but the
**conversation wandered**: different arguments, framings, and kill-shots each run. The role prompts
(`DEFENDER_SYSTEM` / `CHALLENGER_SYSTEM` / `JUDGE_SYSTEM`) are hand-written statics, so the model
improvises — quality and steering are uncontrolled. On a *harder* decision that variance would flip
verdicts. Operator: **"DSPy is needed here to steer the conversation."**

**Direction.** The three role prompts are **not hand-tuned strings; they are DSPy-compiled predictors**
(ADR-0010, adopted). DSPy optimizes each role's prompt + few-shot demonstrations **against a
deliberation eval**, so the debate is consistently useful: the **Challenger** reliably surfaces
*material* flaws (not sycophancy), the **Judge** verdict **calibrates to outcomes**. The conversation
is steered by the **metric**, not by prose.

**The eval ("a better debate" = ?).** The one the Deliberation charter already names: **do upheld
decisions out-perform overturned ones?** Plus, does the Challenger find flaws a reviewer agrees are
material? Champion–challenger over compiled role prompts, gated by ADR-0010.

**Sequencing.** This is the **P12/P13 DSPy harness applied to its first concrete target**. Etalon-first
(DL-19) keeps the harness queued behind a perfect bundle, but deliberation is a high-value, well-
bounded place for DSPy to land — and it needs a labelled eval set (decisions with known outcomes),
which the pipeline must first *produce* (the real-trade blocker). So: real trades → outcome-labelled
decisions → DSPy-compiled debate roles. The Deliberation charter OPS-TUNE now names DSPy explicitly.

## DL-22 · The LLM assumes guardrails we don't have — DSPy must teach actual coverage  ·  status: DIRECTION (2026-06-24)

**Trigger.** Asked the deliberation model (gpt-5.4) to interpret 86 decision parameters *cold* (only
`name = default`, our `why` withheld). It read ~90% correctly on general finance — but the errors were
revealing (full critique: `docs/research/quant-methods/llm-interpretation-deltas.md`).

**The three delta classes.** (1) *Implementation misreads* — e.g. it read `max_daily_move_sigma` as a
per-stock vol filter; it is actually a **pooled cross-sectional z-score** data gate (the DL-17 bug).
(2) *Dangerous assumptions* — it read `max_sector_pct=0.30` as "limits concentration from correlated
holdings", which is the textbook intent **but false for us**: we have a sector cap, **not a
name-correlation penalty**, and the pipeline just opened 4 semis. A Defender would falsely claim
concentration is controlled; a Challenger would fail to attack it. (3) *Honest UNSURE* on the genuinely
obscure (Nadaraya-Watson, Alpha158) — low risk.

**The insight (extends DL-21).** The model does **not** need to be taught finance — it needs to be
taught **this system's actual behaviour and its limits**. DSPy's job for the deliberation roles is less
"make it smarter" and more **"stop it assuming we are smarter than we are."** Concretely, the compiled
role context must carry: (a) per-parameter implementation notes where our code ≠ textbook (the
withheld `why` fields), and (b) the **coverage gaps** (quant-methods Part 2) as explicit *"the system
does NOT do X"* facts — otherwise a fluent debate is *falsely reassuring*, which is worse than none.
The eval (do upheld decisions outperform?) still gates; understanding is necessary, not sufficient.

## DL-23 · Manufacture the eval set — don't wait for outcomes  ·  status: DIRECTION (2026-06-24)

**Trigger.** "DSPy needs outcome-labelled decisions we don't have yet" was framed as a wall (the live
trades haven't resolved). Operator: *don't give up — be creative.*

**The reframe.** Eval data need not come from the *future*. Two sources are available **now**:

- **Path A — backtest replay (history has the outcomes).** The pipeline already runs `as_of`-dated; run
  it on *historical* dates → the forward return is **already known** → instant, large, outcome-labelled
  decision set. This is not just DSPy's eval — it is the eval set for the **whole** continuous-improvement
  loop (RunMetrics, forecaster IC, the debate), and backtesting the bundle is part of *perfecting* it.
- **Path B — the known-gap rubric (our own docs are the answer key).** quant-methods Part 2 + EXP-001
  already wrote down the failure modes the debate *should* catch. Score any debate deterministically:
  *did the Challenger raise known flaw X?* Construct **adversarial decisions** where the right verdict is
  known *by construction*. Zero trade outcomes needed.

**Proven (EXP-002).** Same "Buy NVDA" decision, debated blind vs **grounded** with EXP-001's context: the
blind Challenger missed the correlated-semiconductor concentration; the grounded one caught it precisely.
**The caught-vs-missed delta is a binary training signal, generated today.** Path B works.

**Bootstrapping ladder (each stronger; start now, don't wait):** Path B (gap-rubric / adversarial,
*immediate*) → Path A (backtest, *ground-truth profit calibration*) → live outcomes (*gold standard*, as
the 5 positions resolve). DSPy's prerequisite is unblocked at step 1.

**Bonus + follow-up.** Path A unblocks the *entire* loop, not just DSPy — high leverage beyond this goal.
Follow-up bug (EXP-002): the Judge sometimes returns unparseable JSON → defaults to `revise`; harden the
judge output contract (tool-use / stricter parse / retry).

## DL-24 · DSPy's first job is a model-drift firewall — a model change is a *gated* change  ·  status: DIRECTION (2026-06-24)

**Trigger.** gpt-5.5 is the flagship — capable but expensive; we will likely downgrade/side-grade the
model later (cost, or a new provider). Operator foresight: the danger isn't the swap, it's that the swap
makes *"reports come out slightly different, deep in the code"* — **silently**. *"If we can foresee
something at design time we need to cater for it."*

**Reframe of DSPy's value (extends ADR-0010, DL-21/22).** DSPy is **not primarily a quality booster**
for the deliberation — EXP-003 showed a strong model already catches textbook flaws. Its **first job
here is portability / regression protection across model change.** DSPy compiles the role prompts
**per-model** (ADR-0010's "per-(task×model) compiled artifact"), so swapping the model swaps to *its*
compiled prompts, and the **eval (EXP-003 harness) proves the outputs did not regress.**

**Cater for it at design time (the catering, not just the worry):**

1. **The model is a GATED parameter, never silent.** Changing `OPENAI_MODEL` / `operator.model` is an
   *experiment*: run the eval harness on the new model, compare to the champion baseline; a regression
   (pass-rate down, or verdicts flipped on the golden set) **blocks the swap** / escalates to the
   operator gate. No silent drift.
2. **Per-model compiled artifacts.** Each model gets its own compiled role prompts; the `model` field
   selects the artifact, so outputs stay consistent because the prompt is re-fit to the model.
3. **A golden verdict regression set.** A frozen set of decisions whose verdicts must stay stable across
   model swaps — the EXP-003 harness is the substrate; freeze a baseline once the Class-1 cases +
   sharper scorer (DL-22/EXP-003) land.

**Status.** DSPy + the per-model gate are still gated on the harness maturing (Class-1 cases, LLM-judge
scorer) and eval data — but the **design now caters for it**: a model change *cannot* silently drift the
deliberation's outputs, because it must pass the eval. Recorded in the Deliberation charter (model = a
gated parameter; OPS-NEV: no swap without the eval gate). This widens ADR-0010 from "guard prompt drift"
to **"guard model-swap drift."**

---

## DL-25 · Translate the firewall's findings into code — close the name-correlation gap  ·  status: DECIDED (2026-06-25)

**Trigger.** The deliberation firewall (EXP-004..006) was built on DL-23's premise: *our documented gaps
are the answer key.* So the Class-1 cases are a **catalogue of real holes in our trading logic** — not
just test fixtures. The operator's directive: *"bake experiment results into code; translate our findings
into code."* A finding the firewall keeps surfacing — and that gpt-5.4 regressed on, and that the live
book exposed (it opened 4 correlated semis) — is **name-correlation concentration**.

**The gap (made concrete).** The PM had a `max_sector_pct` *dollar* cap (30 %). But five small correlated
names at 5 % each clear a 30 % cap while being **one bet**. The dollar cap bounds weight, not *count* —
there was no name-correlation penalty. (This is the `name-correlation` Class-1 case verbatim.)

**Decision.** Add **PM-NEV-06**: a per-sector **name-count** cap (`max_names_per_sector`, default 3, 0
disables; already-held names count). A new `SectorBook` (`domain/concentration.py`) owns both the dollar
and the count gate. The count cap is the name-correlation penalty in **deterministic, interpretable**
form — consistent with the etalon's "facts + interpretable quant params" style.

**Road not taken.** A **return-correlation matrix** (pairwise correlation from OHLCV, reject a candidate
too correlated with the book) is more powerful but heavier — needs price history at the PM and a
correlation computation, and it is *opaque* (a number, not a reason). Deferred: the count cap is the
honest first cut; a correlation penalty is a future *tunable* the experimentation process can A/B against
it. Also **not** fixed here: the cap is silent when `market.sectors` is empty (a provider data-completeness
gap) — logged as a separate follow-up, not a risk-logic change.

**Why this matters.** It is the first loop closed end-to-end: *firewall surfaces a gap → recorded as a
Class-1 case → translated into a law clause + code + cited test.* The machinery doesn't just measure
quality; it now **feeds fixes back into the bundle.** This is how the bundle moves from *trades cleanly*
to *trades wisely* (DL-19). The remaining Class-1 findings (calendar-day staleness DL-10; fixed-fraction
sizing; Alpha158 weight=0; LightGBM shadow) are the queued backlog of the same loop.

---

## DL-26 · The cage test is role-relative; cages aren't the bundle's problem — implicit discovery is  ·  status: DECIDED (2026-06-25)

**Trigger.** Tackling DL-19 lock #2 ("laws define a space, not a solution") via the **no-cages audit**
(`docs/laws/cage-audit.md`) — surveying all ~67 prohibitions across the 13 agents against the cage test.

**Finding 1 — the test is role-relative (a sharpening of DL-19).** The genesis test ("a law that forces a
single outcome is a cage") is **incomplete as stated**: removing discovery is only a *cage* where discovery
is the agent's *job*. A **faithful executor** (provider fetches faithfully, execution submits the intent
exactly, monitor applies stops) is *meant* to be deterministic — its lack of a discovery surface is correct
scoping, not over-constraint. So the test must first classify the agent: **discoverer** (scanner, analyst,
forecaster, researcher, curator, operator) vs **faithful-executor / integrity-keeper** (provider, execution,
monitor, reporter, supervisor, master; PM mechanics). Apply "is this a cage?" only to discoverers.

**Finding 2 — no prohibition is a cage.** Every NEV is a role boundary or a safety/integrity rule; none
prescribes *what to find*. The bundle's constraint surface is healthy — positive evidence for etalon v0.1.

**Finding 3 — the real DL-19 gap is positive, not corrective.** Discovery surfaces are **implicit**. The
laws declare the walls (NEV), the capabilities (CAP), and the dials (PARAM/`tunable`) — but **no agent
names the space it owns and may creatively search.** The room exists; it is undeclared, so the etalon
can't show, per agent, *"what is this agent free to discover?"* Two sequenced follow-ups: (a) **DONE at the
legibility layer** — the **discovery-surface register** (`docs/laws/discovery-surfaces.md`) names every
discoverer's space (Owns / Walls / Search / admitting gate); promoting a per-charter "Discovery surface"
section into the LOCKED `_TEMPLATE.md` stays deferred to its own law cycle; (b) give **lawful-space search**
a mechanism (DL-19's extension of LAW-01 beyond dial-tuning to re-composition) — gated behind the deferred
CI-6 optimiser + the DL-20 discovery discipline.

**Decision.** The "No cages" success factor is **satisfied** (audited; none found). DL-19's remaining work
is to make the rooms explicit, not to knock down walls. Also reconciled a drift the audit surfaced: PM
`laws.md` footer said "v0, not yet locked" while it is LOCKED v1 (S70) — fixed (DRIFT-010).

---

## DL-27 · Pipeline observatory — a human-legible *checker that prints* for the trade flow  ·  status: DECIDED (2026-06-25)

**Trigger.** Operator wants a **visibility utility**: see what each agent receives (from whom, what
triggered it) and produces, across the whole pipeline; lock **what must be there**; check **floor/ceiling**
on the values. *"A print statement for a human to see something is not right."*

**Insight.** This is the **deliberation firewall pattern (golden baseline + floor/ceiling) applied to the
data pipeline.** It has three separable layers: (1) the **trace/print** (per-stage I/O), (2) the
**structural lock** — what *must* be present (partly the Pydantic contracts already), (3) the **value
floor/ceiling** invariants (the new part). The risk: a print-everything firehose becomes noise a human
stops reading — so build a **checker that prints** (flags only breaches), not a printer that occasionally
checks.

**Decision (v1 — graph post-hoc; chosen over live bus-tap and gate-first).**

- **Substrate** `orchestration/observatory.py`: `Check` (required/floor/ceiling/oneof), `StageView`,
  `breaches`, `render`. Domain-agnostic; evaluates + renders only.
- **Pack** `orchestration/packs/trading_observatory.py`: per-stage extractors (provider→pm) + the trading
  invariants (`returned ≥ 1`, `return_ratio ≥ 0.9`, `universe/evaluated/scored/evaluated ≥ 1`) — the "what
  must be there" + floor/ceiling locks. Reuses `batch_trace.walk_chain`; reads the graph (DL-08 — the data
  is already all there).
- **Passive WARN**, never blocks, in v1. The committed invariant set *is* the baseline.
- **Platform/pack wall (ADR-0012):** the mechanism is substrate; the specific invariants are the trading
  pack. CLI: `scripts/observatory.py --run-id <id>`.

**Road not taken.** *Live bus-tap* (richer "watch it move" feel; needs a kernel bus-observer hook) —
later. *Invariant-as-hard-gate* (a "pipeline firewall" sibling to `deliberation_gate`, WARN→FAIL) — later,
once baselines settle. *Per-field schema re-validation* — already the contracts' job; the observatory
surfaces, doesn't duplicate.

**Next.** Extend to execution/monitor/reporter; freeze a golden run + diff; then promote WARN→FAIL as the
gate. Same arc the deliberation took: print → baseline → gate.

**Shipped + validated (2026-06-25).** Full `provider→reporter` spine (0.34.02); `run_local.py --observe`
runs a test and monitors it in one command (0.34.03). **Validated live against the free Aura (`c3ce91d0`)
with real Tiingo data** — a 3-ticker run pulled 41 bars/name, opened `AAPL qty=34 est=$293.32`, reported
`OBSERVATORY OK`. Usage doc: `docs/observability.md` §2a. Remaining: golden-run diff + the WARN→FAIL gate.

---

## DL-28 · Layer-3 acceptance gate — the observatory promoted to PASS/FAIL with conservation  ·  status: DECIDED (2026-06-25)

**Trigger.** The law ledger's **Layer-3** row — *"one full paper-trading day on real S&P 500 data,
persisted, with each agent's **job + boundaries asserted**"* — is the ledger's own *definition of "the
system works,"* and it is ⬜. The observatory (DL-27) already proves "each agent's **job**" (per-stage
outputs + invariants) on a real run; it is the instrument for Layer 3. The missing half is "**boundaries
asserted**" and a hard PASS/FAIL.

**Decision.** Promote the observatory to an acceptance **verdict** (the DL-27 WARN→FAIL gate), and supply
the missing half as **cross-stage conservation**: each agent's output count is bounded by its input — *no
fabrication, no overreach*. `scanner.survived ≤ provider.returned` · `analyst.scored ≤ scanner.survived` ·
`pm.approved ≤ analyst.scored` · `execution.submitted ≤ pm.approved` (**EXEC-NEV-01** "never decides what
to trade"). Substrate `observatory.accept(stages, cross_checks) → AcceptanceResult{passed, breaches}`
(per-stage + cross-stage); pack `packs/trading_acceptance.py` (the conservation invariants + `accept_run` +
`render_acceptance`); `scripts/accept.py` exits non-zero on FAIL — a real gate.

**Two flavors (same as the firewall).** A deterministic **CI guard** (a full cascade must PASS — proves the
wiring + boundaries every commit) + the **live acceptance run** (real S&P data → Aura, recorded as
evidence). The **Layer-3 ledger row goes 🟩 when both exist**.

**Road not taken.** A *full golden-run diff* (freeze every value, exact-match) — deferred; conservation +
floor/ceiling is the high-signal first cut (catches fabrication/overreach without brittle exact-match that
breaks on every legitimate data change).

**Next.** Run the live acceptance on a real S&P-100/500 universe against Aura; record it; turn the Layer-3
row 🟩 (or 🟨 if partial). Then the golden-run diff for value-level regression.

**Live run (2026-06-25) — gate works; found a real bug.** `accept.py` ran **live against the free Aura** and
returned `ACCEPTANCE PASS` on a real 3-ticker run — the gate is proven end-to-end on real infra. The
**full S&P-100 run surfaced [DRIFT-011](laws/drift-register.md)**: a same-day re-ingest collides on the
immutable `snapshot` property in Neo4j (the in-memory store hid it) — exactly the integration bug
100%-coverage unit tests miss, and *the reason Layer 3 exists*. Layer-3 row → 🟨 (gate live-verified; 🟩
pending the DRIFT-011 fix + one clean full-universe run).

**Re-run after the DRIFT-011 fix (0.35.01).** The full **S&P-100 → Aura run now completes** (99/99 × 41
real bars, no collision) — DRIFT-011 **CORRECTED, proven live**. The acceptance gate still **FAILed**, now
on *data quality* ([DRIFT-012](laws/drift-register.md)): clean OHLCV but `used_fallback=True` from a
`daily_move_sigma_anomaly` (too-tight default sigma vs a real big-mover) **and** optional-field faults
(`fundamentals/news/sectors/earnings_degraded` — Finnhub rate-limited at 99 per-ticker calls) → the analyst
rejected all 5 candidates → zero trades. The gate did its job again: it caught **over-taint** — optional
*enrichment* failure blocks trading on otherwise-good OHLCV. The 🟩 is now one over-taint fix (optional
faults record a note but don't set `used_fallback`, à la DRIFT-006's `taint=False`) + sigma review away.

**🟩 Layer-3 GREEN — "the system works" (0.35.02, 2026-06-25).** After the [DRIFT-012](laws/drift-register.md)
fix (optional faults never taint; sigma 4.0→8.0), the **clean full S&P-100 → Aura run PASSES**:
provider→reporter over all 99 names × 41 real bars, **5 positions opened**, `OBSERVATORY OK` + **`ACCEPTANCE
PASS`**. Three live-only bugs the 100%-coverage in-memory suite hid (DRIFT-011 keying, DRIFT-012 over-taint
×2) fell out of *one* acceptance push — the thesis of Layer 3, vindicated. **Caveat (not blocking,
[DRIFT-013](laws/drift-register.md)):** the 5 names are correlated and PM-NEV-06 was silently inactive
(empty `sectors` from a Finnhub rate-limit) — the concentration guard is data-dependent. Trades cleanly,
not yet wisely. Remaining stretch: the same path at S&P-500 scale.

## DL-29 · Per-ticker OHLCV quality — a partial degradation excludes a ticker, never taints the batch  ·  status: DECIDED (2026-06-25)

**Trigger.** The live S&P-500 acceptance ([DRIFT-014](laws/drift-register.md)) `FAIL`ed where S&P-100
passed: Alpaca pulled **503/503** OHLCV (the data layer scales), but the analyst `scored=0`. Root cause —
`daily_move_sigma_anomaly` is a **pooled cross-sectional** check whose taint is **batch-level**: one name's
>8σ intraday move among 503 set `used_fallback=True`, and the analyst's `ANLZ-FAIL-02` gate bails the
*whole* batch. As N→503 the probability of ≥1 outlier → 1, so the batch is ~always "degraded" → zero trades.
The per-batch quality model doesn't scale.

**Decision.** `used_fallback` means *"the whole delivery is untrustworthy"* — a per-ticker problem must not
trip it. So the outlier is **attributed to its own ticker and excluded** (`validate_bars` drops its bars;
new `DataQualityTrace.anomalous_tickers` field records it), exactly parallel to `stale_tickers`. The clean
remainder is delivered and `used_fallback` is set **only** by a genuine whole-batch failure — a tainting
note (validity/staleness) or `returned == 0` (nothing survived). The analyst then scores the survivors.

**What did NOT change (deliberate).** The **detector stays pooled cross-sectional** — a >Nσ move *vs the
whole batch* is the documented data-integrity/event gate (`quant-methods.md`; a Class-1 case the LLMs
misread as a per-stock vol filter). Only the **consequence** changed (batch note → per-ticker exclusion).
Mechanically, a pooled outlier among *k* near-identical clean returns has z = √k, so the gate still fires
for any k ≥ ⌈Nσ²⌉ — detection power preserved, blast radius reduced to the offending name.

**Observability (the DRIFT-013 lesson).** The exclusion is **never silent**: the observatory prints
`anomalous <tickers>  (>sigma excluded, DRIFT-014)` and the batch reads `quality ok`, so a reader sees *what*
was dropped and that the delivery was *not* whole-batch degraded.

**Road not taken.** (1) A **per-ticker time-series** detector (judge each name against its *own* return
history) — rejected: a single unadjusted-split glitch inflates that ticker's *own* σ and **masks itself**;
the pooled comparison is strictly better at catching glitches, which is the point. (2) **Relaxing σ further**
or dropping the check — rejected: that blinds a real integrity gate; the bug was the *taint scope*, not the
threshold. (3) Excluding only the **anomalous bars** but keeping the ticker — rejected: a glitchy name's
remaining bars are suspect too; excluding the whole ticker (like stale) is the conservative, consistent move.

**Proven.** Unit (`test_domain.py::test_integrity_excludes_anomalous_ticker_keeps_clean_remainder`) +
observatory (`test_anomalous_ticker_is_excluded_and_shown_not_degraded`); `make ci` green, 100% coverage,
0.37.01.

**PROVEN LIVE (2026-06-26) — Layer-3 🟩 at the full S&P-500.** A live S&P-500 → Aura acceptance run returned
**`ACCEPTANCE PASS`**: the provider flagged `anomalous SMCI  (>sigma excluded, DRIFT-014)` and the batch
stayed `quality ok  returned=502/503` — the single outlier excluded, the clean remainder delivered and
scored (scanner 503→5, analyst HPE/MRVL, **2 positions opened**). The same path that `FAIL`ed pre-fix now
passes at the literal S&P-500. The run also **validated the OHLCV-only fast mode**: requesting only the
`ohlcv` field skipped the ~2000 Finnhub enrichment calls (`collect_optional_fields` gates each pillar by
`field in fields`), so the whole cascade took **9.4s** vs the ~33 min a fully-enriched single-shot would
spend rate-limited. The only WARN was the expected DRIFT-013 sector-coverage advisory (enrichment skipped).

**Toggle shipped (0.38.00).** The fast mode is now first-class, not a monkeypatch: `provider.ingest_ohlcv_only`
(`PROVIDER_INGEST_OHLCV_ONLY`) + a `--ohlcv-only` flag on `run_local.py`. `_ingest_fields(settings)` returns
`("ohlcv",)` when set (else `MARKET_FIELDS`), threaded through both the single-shot and chunked ingest paths;
`collect_optional_fields` already gates each pillar by `field in fields`, so no enrichment call is made. The
acceptance gate needs nothing more — sectors come from the warmed cache, the rest is advisory.

## DL-30 · Activate the forecaster as an orchestrated advisory side branch (RPC, never gates)  ·  status: DECIDED (2026-06-26)

**Trigger.** The forecaster is a *fully built* agent (FinBERT sentiment + LightGBM return models,
scorecards, graph writes) that **nothing ever called** — it bootstrapped and `idle_loop()`d. The 5
control-plane agents (forecaster/operator/supervisor/curator/researcher) are the last stubs; the forecaster
is the natural first because it slots into the proven trading path as the locked champion–challenger's
FinBERT advisory leg.

**Decision.** Activate it as an **orchestrator-triggered cascade stage**, not a change to the analyst and
not a graph-pull self-trigger. After the analyst writes its `RecommendationSet`, a new `forecaster` stage in
`cascade_once` calls the forecaster over the bus (`forecast` + `forecast_return`) for each recommendation;
the forecaster persists a `ShadowPrediction` per leg and the stage writes a `ForecasterRun` marker linked
`AnalystRun-[:FORECAST_BY]->ForecasterRun` for idempotency. The provider and forecaster are bound to a
**shared bus** (the forecaster's `get_market_data` calls reach the provider — it is in the provider's
allowed-callers). `subject_ref` is the **ticker** (so news/price fetch *and* the by-ticker scorecard line
up; the `ADVISES` edge to the `{run_id}:{ticker}` Recommendation node simply doesn't form — acceptable, the
scorecard matches by ticker). Predictions are `shadow=True` and the stage is a **side branch**: it never
touches the conservation/PM/execution path. Version 0.39.00, `make ci` green (1143 tests, 100%).

**Why this shape.** It respects `FORE-TRG-01/02` (RPC-triggered, never self-triggers — the orchestrator is
the caller), keeps the **LOCKED analyst** untouched, and matches the locked champion–challenger direction:
the forecaster lays down a shadow track record per run that the already-built scorecard/comparison evaluates
offline. The immediate job is to *produce and persist* shadow predictions, not to have the analyst consume
them — so an orchestrated side stage is exactly right.

**Road not taken.** (1) The analyst calls the forecaster synchronously — rejected: more invasive, touches
locked laws, couples the trade decision to an advisory agent. (2) A forecaster graph-pull `work_loop` — it
*looks* like the provider→reporter pattern but **violates FORE-TRG-02** (self-trigger). (3) Linking by the
`{run_id}:{ticker}` Recommendation key — rejected because the forecaster also uses `subject_ref` as the
news/price ticker; ticker wins (the scorecard is by-ticker).

**Finding (cross-cutting, not faked).** There is **no distributed RPC-serve transport** in the kernel —
only `idle_loop` (sleep) and `work_loop` (graph-pull, which self-triggers). So an RPC agent's *standalone
container* cannot truly "serve" yet; the forecaster is activated **in the in-process cascade demonstrator**,
not as a live container service. This gap blocks the full-fleet activation of **all 5 RPC control-plane
agents** and is the real prerequisite for them — a `serve_loop`/bus-consume primitive (Service Bus
queue → dispatch to bound handlers). Logged as the next infra unblock for the control-plane.

**Deferred (small, noted).** An observatory advisory `[forecaster]` line (shadow-prediction count per run);
deferred to avoid entangling the trade-spine conservation view — a clean follow-up.

## Discussion agenda — opened 2026-06-26 (4 topics; status: OPEN / in discussion)

Captured per LAW-06 so they are not lost; each resolves into its own DL entry or ADR.

1. **Control flow — whole process vs. financial decision-making.** Is the trading control flow
   (orchestration *and* the buy/sell/size/reject decision logic) fully pre-determined at code time, or
   does an LLM make a *runtime* decision that mutates the graph / changes the flow? If it is fully
   deterministic, what justifies the agent/graph machinery over a hardcoded function — for the *trading
   pack specifically* (platform dataflow set aside)? **CONCLUDED 2026-06-26 → DL-31.** Verified: the
   trading path is fully deterministic (zero LLM calls in provider→reporter); the 3-analyst deliberation
   exists but is *offline-only* (scripts), not wired into the live decision. The agent/graph machinery is
   justified by isolation / audit / resumability, not flow-dynamism. Direction: put the LLM in the loop as
   an **asymmetric challenger-veto** (DL-31).
2. **Rigor about Laws — review + continuous-improvement cycle.** How do we make the law book
   (~300 gray clauses) rigorous and self-improving, not just a one-time citation pass? Cadence, ownership,
   and the gray→green ledger as a living instrument. Relates to ADR-0013 (continuous improvement) and the
   ledger.
3. **Do LLMs actually understand the parameters we ask them to prioritise/decide on?** When the
   deliberation/operator LLM weighs `max_daily_move_sigma`, `base_min_confidence`, regime floors, etc., does
   it grasp our *implementation* meaning (e.g. sigma is pooled cross-sectional, not per-stock)? How to
   interpret and **test** that understanding. Continues EXP-001 / EXP-003 and
   `docs/research/quant-methods/llm-interpretation-deltas.md`. **Partly folded into DL-31** (define-then-
   justify + score the definitions against the answer key); the broader "test understanding" method stays
   open here.
4. **Insert an LLM into every agent + a pre-defined command set.** Give each agent an LLM and a standard
   command vocabulary (start, show-all-parameters, explain, etc.). Relates to topic 1's "where may an LLM
   make runtime decisions" and to the operator command surface.

## DL-31 · LLM in the loop as an asymmetric challenger-veto, with define-then-justify + scored understanding  ·  status: PROPOSED (2026-06-26)

**Trigger.** Topic-1 discussion. The operator's instinct: the 3-analyst deliberation (defend / challenge /
judge, `kernel/deliberation.py`) is *expert-LLM input that should influence the purchase decision* — and we
should make the LLM **explain what each parameter means and justify its verdict** to earn confidence.

**Finding (rigor).** The trading path is **fully deterministic** — zero LLM calls in
provider→scanner→analyst→PM→execution→monitor→reporter (verified). The deliberation harness is real and
works, but is called **only from scripts** (`deliberate.py` / `deliberation_eval.py` / `deliberation_gate.py`)
— it is **not wired into the cascade or any poll/run path**. So today it is a *design-time / offline* tool;
it does **not** currently let a ticker through or hold one back in a live run. The operator's "in principle"
was exactly right.

**The core principle.** *Asking the LLM to explain ≠ confidence.* EXP-001/EXP-003 +
`docs/research/quant-methods/llm-interpretation-deltas.md` already **proved** the model confidently misreads
our parameters (it calls `max_daily_move_sigma` a per-stock vol filter; it is a **pooled cross-sectional**
gate). A fluent justification can be confidently wrong. **Confidence comes from measurement, not eloquence.**

**Proposal (three parts).**

1. **Wire the deliberation into the loop as an asymmetric challenger-veto.** Run defend/challenge/judge on
   each PM-approved candidate (a new orchestration stage, like the forecaster side branch). The judge may
   **block** a trade (verdict `revise`/`reject`) but may **never originate or resize** one — the
   deterministic core stays authoritative. This is the LLM analogue of `FORE-NEV-02` (advise/veto, never
   gate-up). The transcript + verdict persist as graph nodes (provenance, auditability). A missing/slow
   deliberation must **fail safe** (default = do not block, or block-and-flag — to decide).
2. **Define-then-justify prompt.** Each role must, for every parameter it invokes, first **state its meaning
   in THIS system**, then justify the verdict against those definitions. Edit `DEFENDER_SYSTEM` /
   `CHALLENGER_SYSTEM` / the judge prompt in `kernel/deliberation.py`. Output: a transcript that names and
   defines `base_min_confidence`, the regime floor, `max_daily_move_sigma`, etc., then reasons from them.
3. **Score the definitions against ground truth.** Grade the model's parameter-definitions against the
   answer key (`llm-interpretation-deltas.md`) using the existing scorer (`kernel/deliberation_eval.py` +
   the frozen golden). A regression in *understanding* trips the gate (DL-24: model/prompt are gated
   parameters). This converts "it explained itself, I feel better" into "it defined our N parameters
   correctly, measured, and we block on drift."

**Why this shape.** Transparency (part 2) is for humans/audit; verification (part 3) is for trust; the
asymmetric veto (part 1) is the only safe way to put a non-deterministic judge in a capital path —
reproducibility and testability survive because the LLM can subtract but never add. Parts 2+3 are also the
concrete method for Discussion-topic 3 ("does the LLM understand the parameters, and how do we test it").

**Road not taken.** (a) LLM as **originator/sizer** — rejected: injects hallucination into capital
allocation, breaks reproducibility + the acceptance gate. (b) **Explain-only, no scoring** — rejected: the
project already proved self-explanation is confidently wrong; it is false comfort. (c) Leave deliberation
offline-only — viable as a governance tool, but then it never influences a live decision (the operator's
goal), so it does not satisfy the trigger.

**Open questions to settle before building.** Where in the cascade the veto sits (after PM-approve, before
execution); per-candidate LLM cost/latency (one debate per approved trade) and whether to batch; fail-safe
default on deliberation outage; veto scope (hard block vs. revise-size-down — the latter edges toward
origination, so likely hard-block only); how the `llm-interpretation-deltas.md` answer key is owned and kept
current as parameters evolve.

## v1.0 milestone — DRAFT (provisional, NOT final)  ·  status: DRAFT (2026-06-27)

Captured per LAW-06 so it is not lost; the operator is deliberately **not** finalising this yet (more
criteria in mind). Do **not** treat as a committed milestone — `/roadmap`'s "path to v1.0" stays
*approximate* until this is closed.

**Provisional v1.0 = the bundle is trustworthy enough to run for real:**

1. **Soak performance** — a ~2-week paper soak producing **~20 trades** that return **+2 to 5%** overall.
2. **Dashboard** — a working operator dashboard (surfaces over the graph).
3. **Continuous improvement, live + automatic** — the model-training / curation pipelines are fully
   functional and **automatic** (datasets assembled → trained → scorecarded → promoted through the
   registry with no manual steps).

**OPEN:** the operator has further criteria to add before this is final. Revisit and promote to a
build-plan milestone (or an ADR) when ready.

## DL-32 · P12 sentiment — closed as SHIPPED; scorecard-run + promotion deferred  ·  status: DECIDED (2026-06-27)

**Trigger.** Roadmap cleanup of "abandoned" P12/P13/P15. Investigation showed P12 is **not abandoned** —
it is ~shipped and live: the LM-lexicon **champion is binding** (`analyst.sentiment_weight=0.20`, applied
in `analyst/domain/scoring.py`); the news feed is wired through the provider (`fetch_news`, Finnhub
`/company-news`); the provider-sentiment challenger (`av_sentiment.py`) is advisory; and the FinBERT
forecaster was **re-activated this session** (DL-30 advisory shadow stage).

**Decision.** **Close P12 as SHIPPED.** The only open piece is the final *operational* step — run the
3-scorer scorecard (`forecaster.sentiment_scorecard`, a callable-but-never-triggered RPC) on forward
returns and promote a challenger via the P10 registry gate. That is **DEFERRED, not abandoned**: it needs
a live **news-accrual runway** that was never accumulated and is not being pursued under the etalon-first
pivot (DL-19). **No code removed** — every P12 piece is in the live decision path; ripping out the
sentiment pillar would be a 20%-of-score regression.

**Road not taken.** (a) Delete the sentiment pillar / scorecard machinery — rejected: regressive (champion
is binding) and discards the working promotion mechanism. (b) Keep P12 listed as "active / pending
remainder" — rejected: misleading; nobody is accruing the news runway, so it is a deferred step, not
in-flight work.

**Effect.** build-plan P12 row → SHIPPED; STATE "Next" carries only the deferred scorecard-run step (P13 is
downstream of it). The `sentiment_scorecard` harness stays as cold-but-tested machinery, ready if a news
runway is ever accrued. Next in the roadmap cleanup: P13, then P15.

## DL-33 · P13 cross-asset/macro graph — deferred, not started (honest reclassification)  ·  status: DECIDED (2026-06-27)

**Trigger.** Roadmap cleanup, after P12 (DL-32). Investigation: **P13 has zero code** — no `Sector`
propagation graph (`PEER_OF`/`IN_SECTOR`/`EXPOSED_TO`/`Event-[:AFFECTS]`), no signed-propagation logic, no
sprint doc; only forward-reference mentions in ADR-0002 and a few sentiment/sector sprint docs. (The
`Sector` nodes that *do* exist are the DRIFT-013 sector-label cache for the PM concentration cap — a
different thing.)

**Decision.** Reclassify P13 from "planned" to **DEFERRED — not started.** It is gated on three things,
none active: P12's deferred news runway (DL-32), **premium relationship data** (supplier/exposure edges —
the hard, expensive part), and the etalon-first pivot (DL-19). It is the plan's highest-ambition phase and
stays **intact as a future direction** — not killed, just honestly out of any current queue. No code to
touch (none exists).

**Effect.** build-plan P13 row → DEFERRED/not-started; STATE already carries it only as downstream of P12's
runway (DL-32 edit). Next in the cleanup: P15 (the partially-shipped one).

## DL-34 · P15 container split — in progress, paused (not abandoned); deploy facts reconciled  ·  status: DECIDED (2026-06-27)

**Trigger.** Final roadmap cleanup (after P12 DL-32, P13 DL-33). Investigation: P15 is **heavily built**,
the opposite of abandoned — master bootstrap (`agents/master/`: grants/key_vault/secret_map/http_server),
`kernel/crypto.py` + `bootstrap.py`, 13 Dockerfiles, **live GHCR image build/push** (`build-images.yml`),
and full Container Apps IaC (`infra/container-apps.bicep`, `deploy-agents.ps1`, `main.bicep`).

**Stale fact corrected.** The plan's S76 item said "DockerHub push"; reality is **GHCR** (ADR-0011,
`build-images.yml`). Fixed in the phase description.

**Decision.** Reclassify P15 from a bare "in progress" to **IN PROGRESS — paused under the etalon-first
pivot (DL-19), not abandoned.** It is not a running fleet yet; three concrete gaps remain (all already in
STATE.md "Next"): (1) **S86 deploy wiring** — grants/secrets JSON into the master image + the
`MASTER_*_PATH` env, else a deployed master rejects every agent; (2) the **DL-30 distributed RPC-serve
transport** — control-plane agents can't serve as live containers without it; (3) a full **fleet
run-through** on the permanent store. No infra removed; the `infra/*.local.json` files are gitignored
local config, not cruft.

**Effect.** build-plan P15 row + S76 item reconciled; STATE already carries the three gaps as discrete Next
items. **Roadmap cleanup complete** — P12 shipped/deferred (DL-32), P13 deferred/not-started (DL-33), P15
in-progress/paused (DL-34). None were "abandoned" in the delete sense; all are now honestly classified.

---

## DL-35 · Activate the distributed fleet now — the Fleet Activation arc (S97–S103), reversing the etalon-first pause  ·  status: DIRECTION (2026-07-01)

**Trigger.** A code-level readiness audit (2026-07-01) of "is the platform ready, communication and all?"
found the trading *product* works in-process (Layer-3 acceptance 🟩) but the *distributed platform* does
not run. Three verified findings: (1) [`AzureServiceBusBus`](../kernel/bus_azure.py) is **send-only** —
`publish` can push but there is **no receiver**, and `request` is an in-process shim; (2) the 5
control-plane agents (operator/supervisor/curator/researcher/forecaster) `idle_loop()` because there is no
serve/consume primitive (the DL-30 gap); (3) the fleet has never run as containers (only scanner EHLO was
proven, S76). Also corrected: **DL-34 gap (1) is stale** — S86 deploy wiring *is* done
([`infra/deploy-agents.ps1`](../infra/deploy-agents.ps1) L155 passes `MASTER_GRANT_POLICY_B64` /
`MASTER_SECRET_MAP_B64`; `agents/master/entrypoint.py` `_resolve_pack` consumes them).

**Decision (operator, 2026-07-01).** Take the **full** activation arc — build the distributed fleet now,
**reversing the DL-19 etalon-first pause** for this workstream. Sequenced as **S97–S103**, in-process
before distributed (mirrors the P14 method):

1. **S97** — kernel `serve_loop` + `RequestConsumer` Protocol (the missing primitive; the twin of
   `work_loop`). In-process, CI-provable.
2. **S98** — supervisor + operator served in-process over `serve_loop` (idle_loop retired for the two).
3. **S99** — forecaster + curator + researcher served; **zero `idle_loop()` remains**; fleet serviceable
   in-process. *Forecaster stays RPC-triggered, not graph-pull (`FORE-TRG-02`, DL-30).*
4. **S100** — Azure Service Bus **receiver** behind the same Protocol + claim-check read + a both-backends
   parity test (mirrors S67). **← etalon-first cut line: S97–S100 are CI/parity-provable, no live spend.**
5. **S101** — permanent Neo4j (durable store) + fleet store wiring (live infra; cost).
6. **S102** — full 13-container run-through → distributed `ACCEPTANCE PASS`; control plane proven serving.
7. **S103** — dispatcher cron: hands-off scheduled daily runs (closes the S83-deferred item).

**Why this shape.** The trade spine already communicates via graph-as-queue (DL-08, working); the gap is
purely the *control-plane serve transport* + *live fleet*. `serve_loop` (S97) is the one primitive DL-30
named; everything else hangs off it. Proving S97–S100 in-process/at-parity means the risky live steps
(S101–S103) run on a communication layer already verified — the same discipline that made P14 safe.

**Road not taken.** (1) *Make the control-plane agents graph-pull* — rejected: violates `FORE-TRG-02` for
the forecaster (self-trigger) and mis-models operator/supervisor, which are genuinely request/response.
(2) *Skip in-process serving, go straight to Service Bus* — rejected: breaks "in-process before
distributed"; a live-only transport is un-unit-testable and hides bugs (every prior live-first step cost
a DRIFT). (3) *Stay etalon-first, defer the fleet* — the option DL-19 implies; **explicitly overridden
here** for this arc by operator choice, accepting the live-infra spend of S101–S103. The etalon-first
principle still governs the *bundle-generator* meta-work (unchanged); only the fleet-activation timing
moved.

**Effect.** Seven sprint handovers written (`docs/sprints/sprint-97…103-*.md`); sprints README + INDEX +
STATE updated to carry the arc. Success is proven per LAW-02 at each step (unit/parity for S97–S100; a
captured `ACCEPTANCE PASS` + activation log for S102). Supersedes the DL-19 pause **for the fleet
workstream only**.

---

## DL-36 · Credentials tested before handover; a failed test enters bounded self-healing (master→LLM→human), one automatic shot  ·  status: DIRECTION (2026-07-01)

**Trigger.** The master login-frenzy aftermath (DL-35 / 2026-07-01). The master was handed *untested*
Neo4j credentials, failed to connect, and crash-looped until Aura locked the account. The operator's
directive generalizes that fix into a system-wide policy.

**The policy (operator, 2026-07-01).**

1. **Test-before-handover.** Every credential the master would distribute in `ACTIVATE.config`
   (`agents/master/secret_map.resolve_config`) is **tested first**. Handover happens *only* on a pass.
2. **Fail → stop.** A failed test means *there is no point continuing the next step* — do not activate the
   agent with a broken credential; **escalate to the master**.
3. **Master devises a plan.** The master **converses with an LLM** to diagnose the failure and devise a
   remediation plan to implement.
4. **Escalate to human.** The plan goes to a human for **approval** — or the operator has pre-set
   **automatic mode**.
5. **Remediate.** test → execute → production → documentation.
6. **One automatic shot.** Automatic mode gets **exactly one** attempt. If it fails, **everything goes to
   a human** — no second automatic attempt, ever.

**Why this shape — it is the frenzy-fix principle, generalized.** DL-35's guard was "test the connection;
on failure halt, never crash-loop." This makes it a policy: *test before you trust, fail safe to a human,
never loop.* The **one automatic shot** is the crash-loop bound promoted to governance. It echoes the
challenger-veto asymmetry (DL-31 — the LLM proposes within rails, never originates the final action) and
the stage-gate ladder (P8: paper→shadow→manual→autopilot — "automatic mode" is an autopilot stage).

**Builds on.** `agents/master` activation (`resolve_config`/`activate`); the **probe pattern**
(`probes/checks.py` — the credential *tests* already exist); `supervisor.flag_for_human` (human
escalation); `kernel/deliberation.py` (LLM plan-devising); `kernel/startup.ensure_reachable_or_halt`
(the fail-safe primitive from the frenzy fix). Related: P8 stage gates, DL-09.

**Proposed decomposition (planning).**

- **A — Test-before-handover (near-term, concrete, low risk).** `resolve_config` → a `resolve_and_test`
  step: fetch each secret, run its per-credential **test** (reusing the probe library), include it only on
  pass; a *required* failure blocks activation and records an `Escalation`. Directly prevents another
  bad-credential distribution — the highest-value, lowest-risk start.
- **B — Escalation record + human gate.** On failure, write an `Escalation`/`Incident` node, flag for
  human (`supervisor.flag_for_human`), and STOP. A decision surface: approve a remediation, or enable
  automatic mode. The **one-shot** counter lives here.
- **C — LLM remediation planning.** The master uses the deliberation LLM to propose a plan **from a
  bounded remediation catalogue** (rotate credential, re-fetch from Key Vault, recreate instance, pause)
  — each with a known test + rollback — **not free-form**. (Safety fork; bounded recommended.)
- **D — Remediation pipeline.** test → execute → production → documentation, with the one-automatic-shot
  bound; a failed auto attempt escalates to human.

**Open questions (operator's to settle).**

- **Test cost:** live credential tests cost real calls (Anthropic $, broker submits an order, feed quota).
  Test everything live every activation, or cache a recent pass / gate the expensive ones behind a flag?
- **LLM safety model:** bounded remediation catalogue (recommended) vs. free-form plan?
- **"Automatic mode" + "one shot" scope:** global operator toggle vs. per-incident; one shot per-incident,
  per-credential, or per-run?
- **"Production" + "documentation":** promote the remediation to the live fleet + auto-write an incident
  record / ADR — what exactly?
- **Reuse the P8 stage-gate machinery** for automatic vs. manual modes?

**Status.** DIRECTION — firm invariants (test-before-handover; a failed test halts; fail safe to a human;
one automatic shot then always human). The self-healing mechanism (C/D) needs the open questions settled
before build; **Piece A can start now**. Graduates to an ADR once the escalation FSM is designed.

**Resolution — ARC COMPLETE: A/B/C/D shipped (S104–S107).** C/D decisions (operator, 2026-07-01).

- **A/B/C/D shipped** (S104 credential-tested activation + `Escalation`, S105 KV secret cache, S106
  remediation planner, S107 eval-gated auto-execution — all live GPT-5.5-checked). A required
  credential failure refuses handover + writes an `Escalation` with the mode/one-shot structure.
- **LLM safety model = bounded catalogue** (confirmed) — the LLM selects from a vetted remediation list,
  never free-form (S106 Piece C).
- **Auto-boundary = a configurable parameter** (both options, dialable): `auto_remediation_scope ∈
  {safe_only, all}` (default `safe_only`), combined with a per-remediation `destructive` tag →
  `auto_eligible = (mode==automatic) and (scope=="all" or not destructive)`. Documented on the setting.
- **Sequencing:** C shipped (S106, planner + record + human gate), **D shipped** (S107, eval-gated
  execute → production → documentation; one automatic shot then human; DSPy behind ADR-0010's
  `PromptOptimizer` port — the harness's first instance).
- **"Production"/"documentation"** (for D): production = resume the blocked activation once the
  re-run credential test passes; documentation = a `RemediationRun` record + resolve the `Escalation`.
- **Upstream (S108, 0.50.00):** the `.env`→Key Vault seeder tests every credential *before it enters the
  vault* (fail-**closed** — a failing/empty/unverifiable secret is rejected, never written), so only
  working credentials ever exist to be handed out. DL-36 at the source; the master's handover-time test
  (S104) becomes defence-in-depth. Also fixed a latent secret-map bug (provider Alpaca-secret env var).

---

## DL-37 · Reference Postgres (`price_cache`) is decommissioned — raw-history needs re-point to Tiingo  ·  status: DIRECTION (2026-07-04)

**Trigger.** The S110 functionality check tried to export the `price_cache` CSV and could not: the
sibling project's `.env` host `trades-database.postgres.database.azure.com` **does not resolve** (DNS
`No such host is known`), and a sweep of **all three enabled Azure subscriptions** lists **zero**
PostgreSQL flexible servers. Verified twice (coding agent + planning agent), 2026-07-04. The server is
gone, not misconfigured.

**What this invalidates.**

- The standing assumption that the reference Postgres is available as a **raw OHLCV** source
  (629,823 rows / 507 tickers, 2021-04 → 2026-05). Any doc or plan that says "export `price_cache`"
  is now dead text: the S59 training-CLI docstring's `\copy` recipe, R001's Q2 prerequisite note,
  and the original S110 check procedure.
- The P12 sentiment-scorecard runway idea "news+returns from the reference Postgres" — that harness
  must source returns elsewhere when it is planned (it was already flagged "verify before planning").

**Decision (planning, within ADR-0006 — no reversal involved).** Raw daily history for training and
evaluation now comes from **Tiingo**, the ADR-0006 primary OHLCV feed (free tier covers the full
S&P-500; client already in-tree at `agents/provider/tiingo.py`); Alpaca data remains the failover.
Historical depth changes from ~5y (price_cache) to whatever Tiingo serves (typically ≥5y daily) —
acceptable for training/evaluation. The LightGBM booster is retrained from Tiingo-sourced bars; the
artifact was never committed, so nothing is orphaned, but **the original v1-Postgres training data is
no longer reproducible** — record the data source in every future `functionality-checks.md` row.

**Ruled out.** Recreating the Azure Postgres server just to keep the old recipe (cost for no new
information — the same raw bars are available from the primary feed); treating this as an ADR-0006
change (it is not: Tiingo was already primary; Postgres was only a *backtest convenience* source).

**Consequences applied.** S110's functionality check re-scoped to a Tiingo export (sprint doc
amended, same evidence bar); S59 trainer docstring recipe is stale (fix opportunistically next time
that file is touched, not worth a sprint).

**S111 operational note.** The rolling-retrain evidence check still uses Tiingo when it is proving
DL-37 lineage, but this is a lineage/cheap-fallback choice, not a runtime-source reversal. Alpaca
remains the primary OHLCV path for repeated broad backfills because it batches many symbols per
request; a provider-selectable exporter is the queued cleanup once the Tiingo-specific sprint evidence
is closed.

**Resolved (same day).** The deletion was **deliberate** — operator removed the server on
**2026-06-19** (no backup taken; raw price cache only, fully replaceable by the live Tiingo feed).
The real defect was **documentation lag**: the S59 docstring recipe, R001's prerequisite note, and
the S110 handover all still pointed at a server that had been gone for two weeks. This entry kills
that dead text; Tiingo is the raw-history source going forward.

---

## DL-38 · Agent memory belongs to the agent definition; the spine stays shared and shrinks  ·  status: DIRECTION (2026-07-04)

**Trigger.** Operator frustration with Aura Free limits reopened the DB question ("do I regret
Neo4j?"), then produced the real insight: *"what if the memory graph should be handled as part of
the agent definition? — this is at the heart of the process."* Captured because it re-frames both
the store decision (R002/DL-15) and the eventual RAG question.

**The observation — one graph, three conflated workloads:**

1. **Substrate registry** (master's `AgentInstance`/`Session`/`CapabilityGrant`) — DL-15 already
   found these writes are audit-only; effectively in-memory; no Neo4j need.
2. **The shared spine** — cross-agent lineage (`RunRequest` → provider → … → reporter) and the
   graph-pull work loop (DL-08). *Coordination state*: shared by definition. Neo4j-shaped
   (traversal-heavy), but **small and stable** once fat artifacts leave it.
3. **Agent memory** — each agent's own artifacts (forecaster `ShadowPrediction`/`Model`, analyst
   pillar outputs, curator datasets …). Ownership is **already declared per agent**: every
   contract's `owns_graph` tuple, enforced by the boundary meta-test. The logical partition
   exists; only the physical co-location makes it look like one big DB decision.

**Direction.** Make **memory a first-class part of the agent definition** — a **MEMORY
declaration** in the bundle alongside CAPABILITY DECLARATION: owned labels, retention, engine
class. Consequences:

- **Engine choice becomes bundle-local.** An agent that needs a different memory engine (first
  real candidate: **RAG** — a vector store for researcher/curator document retrieval) declares it
  in *its* bundle; nothing else migrates, no other agent's laws/tests are touched. Memory stops
  being the odd one out next to per-agent deps, laws, and containers.
- **The blast radius of any store decision is sliced per agent.** Today an engine question is one
  big decision about one big store; under this model it is N small, independent, deferrable ones.
- **The spine shrinks** to lineage edges + work-state + IDs, with fat artifacts referenced by ID
  (the claim-check pattern, already in-tree). A small spine is cheap to host anywhere — the Aura
  Free node-cap pressure comes precisely from the fat per-agent artifacts (ShadowPredictions at
  S&P-500 scale; RunMetrics when CI-2 lands), which this moves out.
- **S101 reframes** from "provision the permanent graph" to "provision the permanent **spine**" —
  a smaller, better-scoped sprint. Fold into the S101 handover refresh (it needed one anyway).
- **Etalon/bundle-genesis fit:** the MEMORY section enriches the agent-definition template — the
  memory *port* is a substrate primitive, the declared memories are pack/agent content, per
  ADR-0012's "substrate or pack?" test.

**Constraint (firm).** **The spine cannot be privatized.** Graph-pull coordination, supervisor
lineage traversal, and cross-agent evidence queries need one shared store; fragmenting it means
hand-built distributed joins — strictly worse than any free-tier limit. Private memory: yes.
Private spine: no.

**Sequencing — painless by construction.**

1. **Conceptual first (near-zero cost):** add MEMORY to the agent-definition template and treat
   `owns_graph` as its first implementation. Docs/template work; no code moves.
2. **Physical split only on demand:** an agent's memory leaves the shared store only when its
   workload demands a different engine. First expected instance: the RAG research item (R00x —
   **this entry is its anchor**). No date; needs a concrete retrieval use case first.

**Ruled out.** Fragmenting the spine across per-agent stores (above). A wholesale Neo4j→Postgres
migration driven by free-tier pain (measured blast radius 2026-07-04: `neo4j` driver imported in
4 files, Cypher in 8 — all kernel-adapter/scripts/tests; contained, but pointless when the spine
can simply be re-hosted). Requiring RAG and provenance to share one engine — different workloads,
joined by IDs, not one store.

**Builds on.** DL-15 (registry ≠ pack provenance — this extends the same cut: pack provenance ≠
agent memory), DL-08 (graph-pull spine), ADR-0012 (substrate/pack wall), R002 (db-placement
research), the `GraphStore` port + `owns_graph` boundary meta-test.

**Status.** DIRECTION — operator-confirmed capture (2026-07-04). Graduates to an ADR with the
S101 (spine) handover refresh; the RAG research item cites this entry when created.

---

## DL-39 · Deliberation's primary product is the graded *rationale* — expert reasoning captured as a training source  ·  status: DIRECTION (2026-07-05)

**Trigger.** After the GPT-5/Opus/Fable bake-off, the operator reframed the point of a deliberation
round: *"one reason is the decision to buy or not, BUT THE MOST IMPORTANT ONE IS WHY THIS DECISION
WAS MADE — is an expert model performing at the level of a senior stock analyst. We collect this and
use it to train a model to see what parameters carry the biggest load and why."* Captured because it
re-frames what the harness is *for*.

**The shift.** Today `kernel.deliberate` returns a `Verdict` (uphold/overturn/revise) — the *decision*.
The reframe says the verdict is the by-product; the **transcript is the asset**. The recorded WHY —
Defender's grounded case, Challenger's strongest objection, the Judge's weighing — is a labelled
corpus of *reasoning quality*, not just outcomes.

**Two questions it must answer:**

1. **Competence** — does the expert model reason at senior-analyst level? Not "did it pick buy," but
   "did it cite the right parameters, define them correctly, weigh reward:risk, catch the event-window
   gap." The bake-off already showed this discriminates: an un-truncated challenger flipped GPT-5's
   verdict, and the three models argued in distinct registers (economic / procedural / parameter-enumeration).
2. **Parameter load** — across many graded deliberations, *which parameters carry the decision* and
   *why*. Feature-importance over the reasoning, not the price series.

**Builds on existing pieces (this is assembly, not green-field):**

- **DL-31 / `score_understanding`** (the `--score` flag) already grades a transcript's parameter
  *definitions* against `TRADING_PARAMETER_TRUTHS` (define-then-justify). That is the seed of a
  "senior-analyst competence" score — extend from "defined correctly" toward "weighted correctly."
- **DL-09** (filter verdicts as a training source) — same pattern: decisions → labels → a second
  training signal for the curator. Deliberation rationale is a *richer* label than a filter bit.
- **ADR-0010** (LLM quality gate) + **ADR-0013 CI-2** (RunMetrics on the graph) — the storage and
  champion-challenger machinery a rationale corpus would feed.

**Open questions (for a research item, not yet decided):** the answer-key for "senior-analyst level"
(a rubric? a human-graded gold set? an LLM-judge with a competence scorecard distinct from EXP-004?);
how a transcript becomes a training row (per-parameter citation → load label?); whether "parameter
load" is learned from reasoning text or correlated against realised outcomes (DL-09 dual-label style).

**Status.** DIRECTION — operator capture (2026-07-05). Next concretisation: a research item
("deliberation rationale as a training/competence source") that unifies DL-31, DL-09 and this entry;
sequence behind a live runway (needs graded deliberations at volume). [[sentiment-champion-challenger]]
and the curator's second-source appetite are the consumers.

---

## DL-40 · The verdict needs literacy-tiered explanations — low / mid / high financial literacy  ·  status: PARKED-IDEA (2026-07-05)

**Trigger.** Operator, immediately after DL-39: *"Opinion is great but we need to explain it to any
Karen. There must be versions of what the judge delivered for people with low, mid and high financial
literacy. Just a thought."* Flagged explicitly as ideation.

**The idea.** The Judge's rationale is written in expert register (reward:risk, ATR multiples,
expectancy). A non-expert reader can't act on it. Render the *same* verdict at (at least) three
literacy tiers — plain-language ("this looks okay but there's no clear plan for taking profit, so
we'd wait"), intermediate, and full expert — without changing the underlying ruling.

**Where it fits.** This is a **surface/presentation** concern, not a substrate one (ADR-0012 test):
the deliberation produces one grounded verdict; a renderer projects it to an audience. Natural home
is `surfaces/` (the same layer as the MCP surface and the A2A front-door adapter from R004), behind a
literacy-tier parameter. Must **not** leak into `kernel.deliberate` — the ruling is single-sourced;
only its *explanation* is multi-voiced (else the tiers could disagree, which would be a bug).

**Ties to DL-39.** If DL-39 grades *whether* the reasoning is expert-level, DL-40 is the inverse
projection — *translating* expert reasoning down. Same rationale object, two directions.

**Status.** PARKED-IDEA — captured so it isn't lost; not scheduled. Revisit when there's a
human-facing surface for verdicts (operator report or A2A front-door). No sprint yet.

---

## DL-41 · Deliberation evidence must be complete: explicit gate OUTCOMES + PM risk-gate results — PRIORITY  ·  status: DIRECTION (2026-07-05)

**Trigger.** Operator, reading Fable's live-bake-off challenger ("nothing in the evidence shows
base_min_confidence was met or even computed"): *"We need to fix it to perfection. Past that process
the money is spent on the decision this process produces. If it's not the best it can be, let's get
there — sooner rather than later."* Elevated to priority: this is on the critical path of every real
trade's quality.

**Finding (not what the wording implies).** The values *are* computed and enforced — `base_min_confidence`
gates the analyst rec (`agents/analyst/domain/recommend.py:45`); `max_sector_pct` gates the PM
(`agents/portfolio_manager/domain/concentration.py:59`). And the **live** veto context
(`orchestration/veto_context.py`) is already rich: it renders analyst `confidence`, a Regime line with
`base_min_confidence`/stop/target/holding, scanner filter verdicts, market quality, fundamentals,
sentiment, earnings, news. The starved one-line context in the GPT/Opus/Fable bake-off was a **test
artifact** (hand-typed `Proposition.context`), not the system.

**The two real gaps (money-critical):**

1. **Gate outcomes are implicit.** Context prints `confidence=0.62` and `base_min_confidence=0.30` but
   never states the *result* ("0.62 ≥ 0.30 → PASSED"). The LLM must infer every comparison; a rigorous
   challenger can still attack an unstated check. Render each gate's **explicit pass/fail** beside its
   values.
2. **PM risk gates are absent from the evidence.** `max_sector_pct` concentration, position-sizing
   basis, and existing-position/portfolio context are computed in the PM but **not rendered** into the
   veto context. So the challenger's "no `max_sector_pct` check cited, could be doubling into
   concentrated exposure blind" is a **valid live finding**. This is the substantive hole.

**Fix scope (to perfection).**

- Render every computed gate in `build_veto_context` as **value + explicit outcome** (passed/failed,
  by how much).
- Thread the **PM risk-gate results** into the evidence — sector exposure vs `max_sector_pct`, sizing
  basis, held positions. Likely needs the PM to **emit its gate outcomes** as a small additive contract
  field on the `OrderIntentSet`/PMRun (computed today, not persisted for the debate to read).
- Add the stop-vs-ATR relationship explicitly (the recurring challenger point across all three models).
- `veto_context.py` is at **195/200 lines** — split before adding (e.g. `veto_context_pm.py`).
- A completeness test: for a decision, assert every enforced gate appears in the rendered context with
  an outcome (guard against silent evidence regressions).

**Why priority over S113.** S113 (Q5 factor proposal) improves what we *propose*; DL-41 improves what
we *decide and spend on*. The veto is the last gate before real orders (`agents/execution/poll.py`
drops vetoed tickers). A debate over incomplete evidence produces a lower-quality veto — and, per
DL-39, poisons the graded-rationale training signal at the source (garbage-in). Fix the evidence before
mining more of it. **Sequence: DL-41 (S114) before S113 execution.**

**Builds on.** S96/DL-31 (challenger-veto + define-then-justify), the live `veto`/`veto_context`
stage, PM concentration/risk domain. Consumer of the completed evidence: [[project-filter-training-source]]
and DL-39.

**Status.** DIRECTION — operator priority (2026-07-05). Package as **S114** next session; execute before
handing S113 to Codex.

---

## DL-42 · DSPy compiles deliberation reasoning quality/consistency — the layer ABOVE DL-41, not a substitute  ·  status: DIRECTION (2026-07-05)

**Trigger.** Operator, on the deliberation quality problem: *"maybe we impose DSPy there — it promises
to fix quality and consistency."*

**The distinction that matters.** Deliberation has two orthogonal quality holes:

1. **Evidence completeness (DL-41)** — deterministic: is every computed gate (value + pass/fail) and
   the PM risk gates in the context? DSPy **cannot** fix this; compiling over incomplete evidence just
   makes the model argue the wrong case *consistently*. **DL-41 first, and not a DSPy task.**
2. **Reasoning quality + consistency, given complete evidence** — does the debate reliably
   define-then-justify, weigh the right parameters, and return stable verdicts? **This is DSPy's job.**

**Why DSPy fits layer 2 well here.** The role prompts are hand-written strings today
(`kernel/deliberation.py`: `_DEFINE_THEN_JUSTIFY`, `DEFENDER_SYSTEM`, `CHALLENGER_SYSTEM`,
`JUDGE_SYSTEM`) — prime compile targets. And unusually, the **metric + eval scaffolding already
exists**: `score_understanding` (DL-31 define-then-justify grader), the EXP-004 `LLMJudgeScorer`, the
Class-1 grounded eval set (`deliberation_eval`), and the `deliberation_golden` drift firewall
(EXP-004..006). Most DSPy adoptions start with no metric; this one has one. `system_prompt`-as-tunable
(ADR-0010) is already live on operator/forecaster — extend the pattern to the deliberation roles.

**This is the first real deliberation instance of the ADR-0010 `PromptOptimizer` port** (first instance
overall landed in S107's remediation selector). Needs: a metric combining understanding-rate + verdict
stability/consistency; a golden eval set for deliberation *reasoning* (distinct from the pass/fail
firewall); the compile pipeline behind the port. Substantial — a sprint after DL-41, and it honours
ADR-0010's "plumbing complete first" caveat. EvoPrompt/TextGrad (R003) remain the later bake-off
candidates behind the same port.

**Sequence.** DL-41 (S114, complete the evidence) → DSPy-compile the deliberation roles against the
understanding+consistency metric (S11x). Feeds DL-39 (a consistent, complete debate is the clean
training signal). Builds on ADR-0010, DL-31, EXP-004..006, R003.

**Status.** DIRECTION — operator capture (2026-07-05). Package after DL-41 ships.
**Update 2026-07-08:** packaged as **S119** (`docs/sprints/sprint-119-dspy-deliberation-roles.md`)
after the fleet arc closed (DL-41 shipped in S114, so the sequencing condition is met).

---

## DL-43 · PostgreSQL becomes the system of record; Neo4j demoted to an ad-hoc analysis workbench  ·  status: DIRECTION (2026-07-06)

**Trigger.** Operator: *"think deep and see how we can move from Neo4j to PostgreSQL as soon as
possible"*, refined in the same session: *"we will still use Neo4j but for investigations and graph
analysis, ad-hoc and out of bounds."*

**Direction.** PostgreSQL becomes the runtime system of record (the DL-38 spine: lineage, work-state,
provenance — plus pgvector for the RAG/agent-memory candidate and a home for CI-2 RunMetrics). Neo4j
leaves the runtime entirely: local-Docker analysis workbench only, loaded on demand from a PG
snapshot, zero runtime/CI/law/cloud dependency. Full analysis + sprint sequence (S116 adapter+parity
→ S117 provision+swap, absorbs S101 → S118 rip-out):
`docs/research/db-placement/postgres-migration-plan.md` (R002).

**Why now (measured):** GraphStore port is 6 methods; the whole Neo4j surface is ~480 adapter lines +
4 driver import sites; production graph data is ZERO (every check tears down to baseline 0; fleet not
distributed); S101 ("provision the permanent spine") has not run — swap the provisioning target and
no migration ever happens. Parity rig (`test_graph_backend_rigor.py`) already exists.

**Reverses (surfaced, not buried):** DL-38's ruled-out note against wholesale migration — reversed by
operator directive with changed facts (RAG/pgvector, zero-data window, S101 queued, Aura economics).
ADR-0001 (Neo4j primary store) to be formally superseded at S117; ADR-0008 amended to analysis-only
scope. DL-38's architecture itself is unchanged — Postgres is simply where the spine lives.

**Status.** DIRECTION — plan complete, awaiting operator go to package S116 (after S115 lands).

---

## DL-45 · Service Bus receive path completes the served-agent transport  ·  status: DECIDED (2026-07-07)

*(Renumbered 2026-07-09 from a duplicate DL-44 — that number belongs to broker reconciliation below,
which every external reference already cites.)*

**Trigger.** S100 implemented the receive half of the Azure Service Bus backend behind the S97
`RequestConsumer` protocol, closing the DL-35 communication gap between the in-process served agents
and the distributed fleet transport.

**Decision.** The distributed served-agent path uses **Service Bus topics plus subscriptions**, not
queues: the publisher chooses the capability/request topic, and each served agent consumes through its
own subscription. The operator sync-RPC and master EHLO/ACTIVATE handshake stay HTTP. The forecaster is
triggered by the orchestrator/dispatcher publishing the `forecast` request, so it remains request-driven
and never self-triggers from analyst graph nodes (`FORE-TRG-02`).

**Reply semantics.** A request and response are both claim-checked `AgentMessage` envelopes: the bus
message is a small ready event, the graph holds the envelope payload, and the response ready event is
published to the requester's reply topic. Correlation is the original envelope id. This keeps
`serve_once(consumer, bus)` unchanged while swapping `LocalRequestConsumer` for
`AzureServiceBusRequestConsumer`.

**Ack semantics.** The receiver completes a source Service Bus message only after the response ready
event is published. Decode/claim-check failures and reply-publish failures abandon for redelivery until
`max_delivery_count`, then dead-letter. All Azure SDK send/receive I/O remains optional and outside the
unit coverage path; in-memory and Celery behavior stay unchanged.

**Status.** DECIDED and implemented on `sprint-100-servicebus-receiver`; live namespace smoke passed on
`trading-agents-bus` with disposable topics torn down.

---

## DL-44 · Broker is truth for holdings; the graph must reconcile — teardown discipline meets the production era  ·  status: DIRECTION → S120 (2026-07-08)

**Trigger.** Operator, after the first fully unattended scheduled run (2026-07-07 22:30 UTC fire):
*"capture it and take care of it straight away after the coding agent hands over the previous work."*
The observed defect: the unattended run **re-bought CSCO (89 sh) on top of the manual S103 check's
88 sh** because the live-check teardowns had deleted the `Position`/`Fill` nodes for trades the
Alpaca paper account still holds. Graph state and broker state diverged; the fleet started its solo
run blind to real holdings. Also observed: the 22:34 UTC after-hours order sits `pending` in its
`Fill` node forever — nothing ever refreshes broker order status after run end.

**The distinction that matters.** Teardown-to-zero was the *right* discipline while every live run
was a disposable proof (S99→S118 pattern: stamp, verify, delete). S103 changed the regime: scheduled
runs are **production**, and the broker account is a *standing* stateful system the graph merely
mirrors. Two truths now coexist and must be reconciled, not assumed equal:

- **Broker = source of truth for holdings** (positions, fills, cash) — it executes reality.
- **Graph = source of truth for lineage** (why each position exists: the DL-41 gate evidence,
  provenance chain, decisions). Lineage can never be recovered from the broker; holdings can never
  be trusted from the graph.

**Direction (S120).** (1) Additive read-only `positions()` on the Broker port (Alpaca GET
/v2/positions; PaperBroker returns its book). (2) An execution-owned reconciliation step at run
start: fetch broker positions + refresh any `pending` `Fill` statuses, write a
`BrokerPositionSnapshot`; divergence vs graph `Position` nodes → **loud** (`Flag`, supervisor path)
— adopt broker truth with provenance `reconciled-from-broker` (never silently fabricate entry
lineage). Monitor reconciles its `Position` nodes from the snapshot (islands: execution touches
broker + its own artifacts; monitor owns `Position`). (3) Teardown discipline amended: checks that
trade must reconcile after teardown; `Position`/`Fill` rows mirroring real broker holdings are
production state, not test artifacts. The first live run of the reconciliation **is** the repair of
the current divergence (AMD/CSCO/HPE/MRVL exist at the broker; graph holds zero).

**Ruled out:** flattening the paper account to re-zero reality (destroys the first real
accumulating dataset — the P12/DL-09 runway); graph-as-truth for holdings (broker executes; the
graph can only lag); folding this into monitor-pnl-from-broker (S43's queued re-point — related,
separate; reconciliation is about *existence* of positions, S43 about *valuation*).

**Status.** DIRECTION — packaged as **S120** (`docs/sprints/sprint-120-broker-reconciliation.md`),
queued immediately after S119's handback (operator: "straight away after the previous work").

---

## DL-46 · Merge-to-main rebuilds images but does not redeploy the fleet — the deploy gap  ·  status: DECIDED (2026-07-14)

**Trigger.** The 2026-07-08 22:30 UTC scheduled run — the first STATE.md expected to run with broker
reconciliation (S120) + compiled deliberation prompts (S119/S121) live — ran entirely on **`:s103`
images**. All three merges had rebuilt and pushed images successfully (`build-images.yml` green), but
the 13 Container Apps + `dispatcher-cron` job are **pinned to a named tag**, so none of the merged code
reached the running fleet. Observed consequences: no `BrokerPositionSnapshot`/divergence `Flag` from the
run, and the PM — blind to held positions without S120's seeding — bought another 87 CSCO on top of the
88 held + 89 pending (the pending 89 filled at the 2026-07-08 open, making broker CSCO 177 vs graph 88).
Repaired by hand 2026-07-09: 87-share order cancelled at the broker; fleet + job updated to `:s121`
(manual `workflow_dispatch` build off main, then `az containerapp update --image` per app — env vars,
secrets, and KEDA scale rules survive an image-only update).

**The gap.** "Merge to `main` is the deploy trigger" currently holds for image *builds* only. Named-tag
pinning (`:s103`, `:s121`) is deliberate — immutable, human-readable, rollback-friendly — but nothing
moves the running apps to a new tag after merge, and nothing *tells* the operator the fleet is behind.
The failure mode is silent: CI green, images pushed, acceptance PASS — on last sprint's code.

**Options (none decided).**

- **A — Deploy step in CI:** after `build-images.yml` on main, a job runs `az containerapp update
  --image` for all 14 targets (needs an Azure service principal secret in GitHub; turns merge into a
  true deploy trigger; loses the human pause between merge and fleet swap).
- **B — Pin to `:latest`:** scale-from-zero pulls fresh on each window, so merges self-deploy at the
  next cold start. Zero new machinery, but mutable-tag drift: a run's code version is no longer
  provable from the app config, and a bad merge auto-ships to the standing fleet.
- **C — Keep manual, add a tripwire:** stay tag-pinned; add a check (in the observatory/acceptance
  path or `infra/status.ps1`) that compares the fleet's running tag against the latest main image and
  fails/flags loudly when the fleet is behind. Preserves the human gate; kills the silence.
- Leaning: **C now** (cheap, keeps LAW-02's "proven, never assumed" spirit — the gap was invisible
  precisely because nothing measured it), with **A** as the end state once the build-on-merge pipeline
  discussion (memory: branch-per-sprint-merge-deploys) is settled properly.

**Decision (S126). C shipped in S126; A remains the end state.** The dashboard now judges
`current / behind / unverified` from append-only `DeployRecord` facts, the observed fleet tags, and
the newest successful main image build. No dashboard control-plane write was added.
**Ruled out.** B remains ruled out because a mutable `:latest` tag weakens per-run provenance and
rollback clarity. A is deferred, not rejected.

---

## DL-47 · The operations dashboard — the PRD's product surface #1 gets built  ·  status: DIRECTION → S122 (2026-07-10)

**Trigger.** Operator, 2026-07-10, after two nights of scheduled runs verified by hand: *"we cannot
have it running under your supervision forever. WE NEED DASHBOARD."* The nightly loop is self-driving
but not self-explaining — every "how did we go last night" costs a manual trace/accept/flag audit.

**Operator requirements (verbatim spirit, all binding).**

1. **All and every signal**, including **per-container logs**.
2. Look & feel: **ChatGPT / early Anthropic** — calm, minimal, warm paper, serif headers.
3. **Three sections**: (I) hardware/infrastructure health & performance; (II) process & life flow of
   the containers **as logical stages**; (III) the trading process **as a logical unit** — *"I want a
   logic there, not hardware flow"*: did each agent do its job, and what is the result of it.
4. **Animated**, reflecting stages/health/logical outcomes; an overall how-did-the-system-perform view.
5. A **run selector at the top**: pick a run and *all contextual information switches to that run and
   only that run*.
6. Compliant with the **self-recovery** (DL-36 ladder) and **consistent-delivery** principles — every
   red state must show where it sits on the ladder (self-healed / escalated / operator-held).
7. **Talk to an LLM** in the dashboard: ask questions beyond the tiles ("state is green but something
   smells"), have it run communication tests, find why something wasn't flagged, and fix it.
8. **Functional, not read-only**: able to **restart a run from the point of failure onwards**.
9. **Accumulated costs visible** (added 2026-07-10): month-to-date **hardware** spend (Azure Cost
   Management API over the resource group) and **LLM** spend (price the append-only model-call
   ledger via a per-model pricing table — a tunable catalogue, so a price change is a config
   change, not code). Status-line vital + Section-I breakdown cards.
10. **Layout** (redlined 2026-07-10 on mockup r1): a **right flyout rail** holds the three
    categories; selecting one shows that section in the middle — one section at a time, not a
    scrolling stack. The **status line carries the vitals**: pending flags, broker↔graph sync,
    degraded feeds, spine/bus health, fleet-images-vs-main currency (the DL-46 tripwire, surfaced),
    month-to-date cost, next fire.
11. **The LLM must be able to repair, not just explain** (added 2026-07-10): it has **access to
    the repo**, uses the dashboard's information to investigate, and the information must be
    **useful enough to prepare a fix if one is needed and rebuild container(s)**. This is the
    operator directive to productize what the planning agent did by hand on 07-09/07-10
    (investigate scheduled runs → diagnose the deploy gap → fix → retag the fleet).

**The chat is therefore two-tier (amends the architecture direction above).**

- **Tier 1 — operator agent (always on):** bounded Q&A grounded in stored evidence + the bounded
  command set (ack a flag, resume a run, deploy tag N). Unchanged.
- **Tier 2 — repair agent (escalation):** a Claude Code / Agent SDK session launched from the
  dashboard with (a) a **repo checkout** and (b) the run's **context bundle** as input. It
  investigates, and when a code fix is warranted it prepares one **on a branch + PR — never a
  direct push to main** (branch-per-sprint law holds; merge stays the operator's deploy trigger).
  "Rebuild container(s)" reuses the DL-46 machinery (tagged `workflow_dispatch` image build +
  `az containerapp update --image`) as one bounded, logged command — no bespoke deploy path. The
  DL-36 ladder still governs: one automatic shot at a vetted remediation, then human.
- **The keystone is the context bundle** — "information useful enough" is a deliverable, not a
  hope: one endpoint (`/api/runs/{id}/bundle`, added to S122) aggregating verdict + per-stage
  observations/checks + flags with reasons + positions + escalations/remediations + image tags +
  (from S123) per-container log excerpts and degraded-feed detail, as one JSON document an LLM can
  ingest whole. The manual equivalent today is five scripts and four az calls; the bundle is that,
  machine-shaped.

**12. Pre-defined investigation skills (added 2026-07-10).** The repair LLM investigates through a
**catalogue of pre-defined, versioned skills** — the DL-36 bounded-catalogue pattern applied to
diagnosis; it composes vetted procedures rather than improvising raw access. Because the repair
agent is a Claude Code session with a repo checkout, the skills ship **in the repo** at
`.claude/skills/` and work in any session **today**, before S125 exists. Operator asked for "why
did a run not complete" and delegated the rest of the set; catalogue as shipped (distilled from
the 07-09/07-10 live debugging):

| Skill | Answers |
| --- | --- |
| `/diagnose-run` | why a run stopped / what a verdict means — the flagship; stage-by-stage procedure + known-signature table |
| `/diagnose-feeds` | why enrichment feeds ran degraded (stale vault secret vs entitlement vs 429s vs vendor) |
| `/check-fleet` | fleet health + deploy currency (the DL-46 tripwire, manual) — healthy-idle vs broken |
| `/deploy-fleet` | the bounded rebuild/retag procedure (proven 07-09); operator approval required |
| `/reconcile-broker` | broker↔graph divergence readings + safe broker-side actions (DL-44 semantics) |
| `/resume-run` | resume a stalled run (graph-pull makes it natural); redo-a-completed-stage explicitly deferred to S124 |
| `/audit-costs` | hardware $ (Cost Management) + LLM $ (priced `LLMCall` ledger, coverage caveats named) |

Each skill ends with a mandatory report format and cites LAW-02 (no cause without evidence).
Growing the catalogue = adding a folder + PR, reviewable like any code. Later candidates:
`/diagnose-deliberation` (veto transcripts, prompt artifact versions), `/diagnose-activation`
(DL-36 escalation deep-dive) — add when a real incident demands them, not speculatively.

**Prior art (operator asked to draw on similar products).** Airflow's run view + *clear task &
downstream* re-execution; Dagster's *re-execute from failure*; GitHub Actions' *re-run failed jobs*;
Temporal's replay-from-history; Grafana for the infra panels (we already run Managed Grafana — it
covers metrics, **not** logical verdicts, which is why section III cannot live there). The section-III
model is closest to Dagster: a run-scoped DAG where every node carries a *logical* verdict, not an
exit code.

**Why restart-from-stage is cheap here.** The graph-pull architecture already persists every stage's
full artifact (RunRequest → MarketData → CandidateSet → RecommendationSet → OrderIntentSet →
ExecutionRun → MonitorRun → Snapshot) and agents poll for unconsumed predecessors. Resume = clear (or
mark-stale) artifacts from the chosen stage **downstream**, wake the fleet, and the cascade re-runs
from the last good artifact — Airflow's clear+downstream semantics for free. Idempotency guards exist
(day-keyed merge-deduped RunRequests; `client_order_id` dedup at the broker). The resume primitive
lives in `orchestration/`, exposed to the dashboard as one bounded command.

**Architecture direction.**

- `surfaces/dashboard/` — a FastAPI read-model service + a static, build-toolchain-free frontend
  (vanilla JS/CSS; repo stays Python-first). Local-first (`uv run python -m surfaces.dashboard`),
  then a 14th scale-to-zero Container App.
- **Reads**: the Postgres spine (observatory + acceptance verdicts, flags, positions, escalations,
  remediation plans — sections II/III, run-scoped); Azure APIs (Container Apps state, job executions —
  section I); **Log Analytics** for per-container logs (section I/II drawer).
- **Writes**: none directly. Every action (ack a flag, resume a run, ask-and-fix) routes through the
  **operator agent's bounded command set** (PRD: surfaces never drive agents except through the
  operator). The chat panel *is* the operator agent with its evidence-grounded explain path; "fix it"
  is bounded by DL-36 remediation scope — anything beyond it escalates to the human (or to a Claude
  Code session), it does not free-lance.
- **Design system**: `docs/design/dashboard-mockup.html` (committed) — interactive mockup built from
  the real sched-2026-07-08/09 runs; status palette validated (dataviz six-checks: light trio full
  pass; dark trio passes contrast/CVD/chroma; status never rides color alone — icon + label always).

**Sprint slices (dependency order).** S122: read-model API + section III (run selector, logical
verdicts, acceptance banner, flags/positions) served locally — kills the manual morning audit.
S123: section II lifecycle + section I infra + per-container logs (Log Analytics query) + the
**cost meters** (Azure Cost Management for hardware; ledger × pricing-table tunable for LLM).
S124: the resume-from-stage primitive + restart affordance (+ the DL-46 fleet-behind tripwire lands
on the dashboard naturally — it is already a status-line vital in the mockup). S125: the
operator-agent chat panel. Order is by operational value; the mockup
is the design spec for all four.

**Ruled out.** Building section III in Grafana (verdicts are graph-native logic, not metrics);
a React/toolchain frontend (repo is Python-first, CI has no node step); dashboard writing to the
graph or bus directly (operator-agent boundary, PRD §non-negotiable); LLM chat with unbounded
write access (DL-36 one-shot ladder governs).

**Operator redline r2 (2026-07-11, after first real use of the shipped slices — all binding).**

**13. Glance verdict first.** Opening the dashboard must answer "is everything right?" with **zero
reading**: one dominant master indicator — RED or GREEN — backed by pre-attentive signals
(color, motion/animated borders, arrows). Operator verbatim spirit: *"you have an immediate
indicator that things are right or wrong AT A GLANCE."* Today the page opens with prose ledes,
section headers, and tables — reading-first, which inverts how dashboards work. **Dashboards do
not explain at the beginning — they explain on demand**: the existing detail (stages, tables,
logs) stays, but as drill-down beneath the verdict, not as the landing view.

**14. No internal project vocabulary on the operator surface.** Sprint ids (S123…), design-log ids
(the DL-36/DL-47 chips currently in Section II/III headers), and other repo bookkeeping are
build-time language, not operator language. The surface says what a thing *is* ("self-recovery
ladder", "deploy currency"), never which internal artifact defined it. Raw image tags remain
fine as *data* inside detail views; they must not be the headline.

**15. The dashboard must stand alone — the coding environment is not the operations console.**
Operator verbatim spirit: *"we will have to leave the coding environment one time and never
come back."* The req-12 skills catalogue (`.claude/skills/`) is reachable only inside Claude
Code, so every "how did we go last night" still drags the operator back into the IDE. This
makes the chat tier (reqs 7/11/12) **the mechanism by which the skills become reachable from
the dashboard**, not a nice-to-have — it weighs on the S124 vs S125 ordering (decision open,
operator's call at next packaging). Corollary: the mockup's canned chat dock read as broken
("LLM dialog box is not connected") — a dead control erodes trust; until wired, the production
dashboard must not show an unwired chat input (hide it or mark it explicitly as not yet live).

**Status.** DIRECTION — S122 shipped (0.66.00, run view); S123 shipped (0.67.00, fleet/infra/logs/
costs). **Resequenced 2026-07-11 per redline r2:** S124 = glance-first master verdict + `NO_TRADE`
acceptance verdict + operator-language sweep (reqs 13–14; **shipped 0.68.00, merged `b9ed20e`,
2026-07-11** — live flip proven: `sched-2026-07-10` NO_TRADE/GREEN) — the light shipped with the
gate fix that makes it honest on no-trade days; S125 = operator chat (req 15 pulls it ahead — it is how the skills
catalogue becomes reachable outside the IDE); S126 = resume-from-stage + the DL-46 tripwire
judgement (was S124).

---

## DL-48 · Three-actor parallelism outgrew the coordination model — process gaps + remedies  ·  status: DECIDED (2026-07-15)

**Trigger.** The S126 closeout week: three actors now work in parallel (operator fixpack chores on
main, Codex on sprint branches, planning agent on closeout/merge), and three near-misses surfaced in
one session — all caught by gates, none reaching production.

**The three gaps and the decided remedies.**

1. **Branch drift is structural.** S126 was cut at 0.69.00; main reached 0.69.05 (12 commits, same
   dashboard files) before handback. The visible cost was six merge conflicts; the invisible one:
   the branch had moved `_apps`/`_jobs` into a new module, so main's CodeQL fix (`public_message`,
   0.69.01) auto-merge-vanished and was restored only by hand during conflict resolution — a
   semantic conflict no auto-merge catches. **Remedy (standing):** every sprint kickoff includes
   "if main has moved when you finish: merge main into the branch, resolve, re-run `make ci`, and
   say so in the return notes" — drift reconciliation is the coding agent's step, not a merge-time
   surprise. While a sprint is in flight, fixpack chores avoid the sprint's contested files when
   practical.
2. **Handback contract must be bounced, not absorbed.** S126 arrived with the closeout placeholder
   unfilled and return notes empty (both explicitly mandatory); the planning agent completed the
   evidence instead of returning it. Right for that day's velocity, wrong as precedent. **Remedy:**
   the kickoff's final instruction is the closeout/return-notes fill, and an incomplete handback is
   returned to the coding agent, not repaired.
3. **Secrets never through the worktree.** A rotated PAT arrived as a repo-root scratch file and
   was staged by `git add -A` during conflict resolution; only detect-secrets stopped it. **Remedy:**
   new hard rule in CLAUDE.md ("Secrets — never through the worktree"): chat or gitignored
   `.env`/`*.local.json` only; a secret found in a tree file is deleted, purged from the index, and
   verified never-committed before work continues.

**Context, not a gap.** The dispatcher tag semantics (backlog row 12) and the operator `approve`
misroute (row 11) are first-contact findings, not process failures — DL-19's loop working as
designed. Read: not a quality decline; a coordination model catching up with parallelism.

**Ruled out.** Freezing main during sprints (kills the fixpack loop's same-day value); giving the
planning agent standing authority to finish handbacks (hides coding-agent regressions and erodes
the closeout contract).

---

## DL-50 · ADR-0007 registry wording lags the shipped GHCR deploy path  ·  status: DECIDED (2026-07-19)

**Trigger.** S129 hardening-backlog reconciliation found row F had effectively landed, but not in
the exact form ADR-0007 originally described. The accepted ADR says per-agent images are pushed to
DockerHub; the shipped workflow (`.github/workflows/build-images.yml`) builds all 14 agent images
and pushes them to GHCR, and the DL-46 deploy-currency path records `DeployRecord` evidence against
that GHCR reality.

**Decision.** Do not silently amend ADR-0007 inside a fixpack. Treat GHCR as the current operational
truth, keep the backlog/docs honest, and queue a formal ADR amendment cycle that updates the
registry choice plus the related supply-chain mitigations (signing, pull credentials, accepted image
scan findings) in one reviewed change.

**Why.** The sprint's job is to fix evidence loss, reduce read egress, and add bounded hardening
gates. Rewriting an accepted platform ADR as a side effect would hide architectural drift instead of
making it governable.

---

## DL-49 · Stored procedures for dashboard reads — ruled out  ·  status: DECIDED (2026-07-19)

Operator asked why the dashboard does not use Postgres stored procedures. Answer recorded so the
question stays closed.

**Decision.** Dashboard read logic stays in Python projections behind the `GraphStore` port;
no logic moves into database procedures.

**Why.** (1) Postgres is one adapter of the port — the same projections run against the
in-memory store, which is what keeps the suite fast and the 100 % floor holdable; a stored
procedure has no in-memory twin. (2) Procedures escape the whole CI gate (ruff, mypy, coverage,
module-size, import-linter) and would be versioned via alembic instead of reviewable code.
(3) ADR-0012: the substrate stays domain-agnostic — trading-shaped read logic does not belong in
the storage layer.

**The legitimate pro (egress) and its adopted alternative.** Server-side computation returning
small results is the real benefit stored procedures would offer. Adopted instead: push heavy
traversals into adapter SQL (`kernel/graph_postgres_queries.py` already does recursive walks
server-side) and reduce read volume with the S129 TTL cache. Escalation path if read patterns
outgrow this: smarter adapter SQL — still code, still gated — never database-resident logic.

---

## DL-51 · Per-agent Postgres identities before RLS or ACTIVATE delivery  ·  status: DECIDED (2026-07-20)

**Trigger.** S131 split the shared `POSTGRES_DSN` blast radius. The graph spine still uses two
shared tables (`nodes`, `edges`) and agents need the spine before the master can issue ACTIVATE
payloads, so credential scoping had two tempting-but-wrong expansions.

**Decision.** Ship same-grant, distinct-login roles first: `ta_<agent>` identities for every
fleet target, plus `ta_ops`, delivered as per-target Container Apps secret-backed
`POSTGRES_DSN` values. This buys attribution (`pg_stat_activity.current_user`) and revocability
now without changing the graph schema.

**Deferred.** Row/label-level least privilege through RLS is a later design. It needs an explicit
label write/read matrix, policy tests, migration ownership rules, and a plan for cross-stage
lineage reads. S131 must not improvise RLS over the append-only graph.

**Ruled out for this sprint.** Delivering `POSTGRES_DSN` through DL-36 ACTIVATE grants. Agents use
the graph spine to discover work and participate in activation-era recovery, so the DSN is a
bootstrap credential, not an after-activation secret. Reworking that order is a bootstrap redesign,
not a hardening patch.

## DL-52 · Sprints merge through a PR — a direct merge bypasses the enforcing security gate  ·  status: DECIDED (2026-07-22)

**Trigger.** A Dependabot PR's red `gate` check was investigated and unwound three stacked
defects. (1) `secrets.SECURITY_FINDINGS_TOKEN` was absent from the **Dependabot** secret store —
Dependabot-triggered runs read a separate store, so the token resolved empty and `uvx` could not
fetch the private toolset (symptom: "Can't add secret mask for empty string", then
`could not read Password`). All 7 Dependabot runs failed; all 5 normal-branch runs passed — a
clean split that proved the cause. (2) Once the secret existed, the PAT lacked read access to
`security-findings-toolset` (403 "Write access to repository not granted"). (3) With the gate
finally *running*, it flagged 6 error-level `py/undefined-export` alerts. The deepest finding was
structural: `security-findings.yml` triggers on `pull_request` **only**, and S131/S132/S134 were
each merged straight into `main` with **no PR** — so the gate that has been "enforcing since
2026-07-04" never ran on any of them. The alerts it would have caught were introduced by S131 and
sat unexamined because nothing evaluated them; the Dependabot PRs were the only traffic still
hitting the gate, and their token failure masked the whole thing.

**Decision.** Sprint and chore branches merge to `main` **through a pull request**, never a local
`git merge` + push. The PR event is what makes the enforcing gate (plus `quality`/`test`/`security`)
actually execute on the code it exists to guard; branch protection already lists `gate` as a
required context, but that binds PR merges only. Recorded as a hard rule in `CLAUDE.md`.

**Also decided.** The 6 `py/undefined-export` alerts are dismissed as **false positives**: they are
the PEP 562 lazy-export pattern S131 introduced for the dispatcher image slim (row J) — `__all__`
declares the name, module `__getattr__` resolves it at runtime, and CodeQL cannot follow
`__getattr__`. Runtime behaviour is covered by the suite at 100 %. Dismiss-with-reason is this
repo's accepted-finding path; the baseline file was left untouched.

**Ruled out.** Adding `push: branches: [main]` to the workflow as the fix. It would evaluate direct
merges *after* they land, which reports rather than gates — a safety net, not enforcement. Kept as a
possible addition, not a substitute. Also ruled out: refactoring away the lazy exports to satisfy the
query (they are load-bearing for the S131 image slim), and growing `security/findings-baseline.json`
instead of dismissing (the baseline records accepted *keys*, and inflating it hides the reason).

**Residual risk (named, not fixed).** Repo-admin pushes can still bypass branch protection, so the
rule is currently binding on process rather than mechanically enforced. Tightening protection to
disallow bypass is an operator decision, deferred because it would also route routine docs/STATE
commits through PRs.

**Addendum (same day) — the second silent-gate of the same class.** Draining the 5 unblocked
Dependabot PRs exposed a sibling defect: **a push made with `GITHUB_TOKEN` does not trigger `push`
workflows** (GitHub's recursion guard). The Dependabot auto-merge workflow merges with
`GITHUB_TOKEN`, so #52/#54/#56/#57 landed on `main` firing **nothing** — no `CI` on the merge
result and, critically, no `build-images`, even though its `paths:` filter explicitly lists
`pyproject.toml` and `uv.lock`. The consequence was invisible: `main` read green while the
published `:latest` images were stale at `15c81ae`, predating every dependency bump, with Trivy
never having scanned the new dependency set. Corrected by dispatching `build-images` manually at
`image_tag=latest` (run green on `88bb8fb`; all 14 images rebuilt, Trivy gates passed). **Standing
rule:** after any Dependabot auto-merge that touches `pyproject.toml`/`uv.lock`, confirm
`build-images` actually ran for that SHA — a green `main` does not imply fresh images. The general
lesson matching this entry's theme: a gate can be configured, required, and *still never fire*;
verify the run exists for the commit, not just that the check is green.

---

## DL-53 · Service Bus blast radius uses topic-level SAS, not namespace rules  ·  status: DECIDED (2026-07-22)

**Trigger.** S131 removed the shared Postgres runtime identity, leaving the Azure Service Bus
namespace connection string as the last shared credential across the standing fleet. The bus carries
claim-check refs and RPC envelopes rather than graph data, so the severity is lower than the
Postgres half; the remaining value is attribution, revocation, and reducing spoofed bus access.

**Azure limit that forces the shape.** The current Service Bus quota remains **12 shared-access
authorization rules per namespace, queue, or topic**. The fleet has more than 12 runtime identities,
so a per-agent namespace-rule model cannot fit honestly. S133 therefore uses entity-level topic
authorization rules with measured Send/Listen rights. The live plan produced 13 bus targets and 33
topic rules with no topic over the cap.

**Decision.** Service Bus runtime credentials are delivered as per-target Key Vault secrets:
`AZURE_SERVICEBUS_CONNECTION_STRING` remains the compatibility primary, and
`AZURE_SERVICEBUS_CONNECTION_STRINGS_JSON` carries the measured topic bundle. The runtime resolves
the connection string by topic before sending or receiving; topic names, subscriptions, claim-check
payloads, and RPC envelopes are unchanged. `master` has no measured bus topic rights, so scoped
delivery removes its Service Bus env rather than inventing a permission.

**Rollback.** The shared namespace string is retained only as an operator rollback credential:
`pwsh -NoProfile -File infra/deploy-agents.ps1 servicebus-flip -UseSharedServiceBusDsn`.

**Proof.** S133 provisioned the 33 entity rules, wrote 26 Service Bus Key Vault secret names, flipped
12 agent apps plus `dispatcher-cron` to secretRefs, removed `master`'s Service Bus env, and proved a
controlled canary request/reply with separate Send/Listen identities. Wrong-topic Send was refused,
revocation locked out only the revoked requester rule, canary topics were deleted to zero, and all
Container Apps/job stayed `Succeeded`.

## DL-54 · A scoped observation drifted into an unscoped status claim  ·  status: RESOLVED (2026-07-22)

**Trigger.** The operator asked to apply the S131 per-role `POSTGRES_DSN` flip, which `STATE.md`
had listed as a pending operator item. Auditing before acting showed the flip was **already
applied**: all 14 targets carried distinct per-role DSNs and every one connected as its own
`ta_*` role with the correct spine privileges. Nothing needed applying.

**How the false entry formed.** On 07-21 STATE recorded, accurately, that *one run* had used the
shared DSN: "S131 per-role DSN flip not yet applied (**this run** used the shared DSN)". The
scope qualifier was then dropped in later edits and the sentence became a claim about current
infrastructure state. The 07-22 Now/Next rewrite (#62) carried it forward unexamined, and the
S133 STATE update leaned on it a second time ("unlike the still-pending S131 Postgres flip").
A statement that was true about a past *event* had been promoted to a false statement about
present *state*, and each subsequent edit reinforced it.

**Why nothing caught it.** The flip is invisible to the obvious check. `postgres-flip` rewrites
the **value** of the `postgres-dsn` secret while leaving the env var name identical, so
`az containerapp show` returns `POSTGRES_DSN=secretref:postgres-dsn` before *and* after. Every
cheap read-only verification looks the same in both worlds; only reading the delivered secret
value — or observing which role actually connects — distinguishes them.

**Decision.** Do not re-run the flip. It is idempotent, but executing it would have created 14
new revisions to reach a state already held, and "run it again to be sure" is how an unverified
claim becomes an unnecessary production change. The audit is recorded in
`docs/laws/functionality-checks.md` (2026-07-22) as the proof instead.

*Ruled out:* re-running `postgres-flip` as a no-op confirmation (revision churn, no information
gained — the audit answers the question directly); adding a preflight check that greps env-var
names (it cannot see the value, so it would have reported the same thing in both worlds).

**Standing correction to how status is written (LAW-02).** An operator item asserting that
infrastructure is in some state must name the check that would prove it, and a claim about a
*run* must keep its scope marker when it is restated. Where a claim's cheap check cannot
distinguish the two states — as here — that fact belongs in the item itself, so the next reader
knows not to trust the cheap check.

**Follow-up shipped (2026-07-22, 0.72.00).** The gap DL-54 exposed was not the wrong status line —
it was that no cheap check could contradict it. `scripts/cred_audit.py` now closes that: it reads
each target's *delivered* secret value, reports the role it names, and connects as it, classifying
every target as `scoped`, `scoped-degraded`, `shared`, `cross-wired`, `unreachable`, or `missing`.
`--strict` exits non-zero unless all 14 are scoped. `cross-wired` — a target holding *another*
agent's role — is a defect neither the flip script nor preflight could ever have surfaced. First
live run: 14/14 `scoped`, and a negative run against a bogus resource group correctly exited 1.
Runbook: `docs/deployment.md` → "Verifying which credential the fleet actually holds".

## DL-55 · The local secret sweep could not see new files  ·  status: RESOLVED (2026-07-22)

**Trigger.** While landing the credential audit (0.72.00), `make ci` reported a clean
detect-secrets sweep; the commit two minutes later was blocked by detect-secrets on two findings
in the very files `make ci` had just "scanned".

**Cause.** `pre-commit run detect-secrets --all-files` resolves "all files" through git, so it
covers **tracked files only**. A module that has been written but never `git add`ed is invisible
to it. Every new file a sprint adds is therefore unscanned locally until the moment it is staged,
which is exactly when it is too late for the local gate to be useful.

**Why this is worse than an inconvenience.** The gate's whole purpose is to fail before the
commit, and its blind spot was aimed precisely at new code — the code most likely to carry a
pasted credential. A green `make ci` was not evidence that a sprint's new modules were
secret-clean, and nothing in the output said so.

**Fix.** `scripts/check_untracked_secrets.py` scans exactly the set `--all-files` skips
(`git ls-files --others --exclude-standard`), wired into both the `ci` and `check` Make targets.
Proven both directions: with a fake basic-auth URL planted in an untracked file the existing
sweep still reported **Passed** while the new check exited **1**; with the tree clean it exits 0.

*Ruled out:* telling the operator to remember the gap (a human check that cannot fail is not a
check — the same reasoning as DL-54, which is what prompted this being fixed rather than
documented); passing tracked+untracked as one giant `--files` list (the argument list would
approach the Windows command-line limit on this repo).

**Standing note.** GitHub CI is unaffected — it checks out a clean tree, so there are no
untracked files there. This was a local-gate-only blind spot, which is why nothing upstream
ever caught it.

## DL-56 · PR requirement reversed — the gate, not the PR, was the point  ·  status: DECIDED (2026-07-22)

**Reverses the same-day DL-52 decision to merge through pull requests.** Operator directive: *"I
do not like a PR process for a single developer — it is meaningless. I prefer worktrees."*

**Why the reversal is right.** A PR buys two things: review, and a `pull_request` trigger. On a
one-developer repo the review is self-review, which is worth approximately nothing — so the
entire value being purchased was the trigger. DL-52 correctly identified that S131/S132/S134
merged ungated, then reached for PRs because that was the only mechanism that made the gate fire.
That confused the requirement (the gate must run on the code) with one implementation of it.

**What replaces it.** `security-findings.yml` now triggers on `push` to every branch, matching
`ci.yml`. The job reads repo-level code-scanning alerts against a committed baseline and uses no
`pull_request` context, so push and PR runs are equivalent — verified by inspection before the
change. This gates the branch *before* a local merge, which is strictly earlier than a PR would.

**Working agreement now.** Worktree per sprint/chore → `make ci` locally → push the branch →
confirm `quality`/`test`/`security`/`gate` green on that branch → merge locally. The binding rule
is **never merge a branch not seen green on the remote**; that, not the PR, is what closes the
S131/S132/S134 hole.

*Ruled out:* keeping `enforce_admins: true` (enabled and then reverted the same hour — it forced
even one-line STATE edits through PRs, and its only real function was compelling a PR flow the
operator does not want); leaving the gate `pull_request`-only and relying on discipline to open
PRs (that is the human-check-that-cannot-fail pattern DL-55 rejects).

**Process note on how DL-52 over-reached.** The operator chose "the real fix" between two options
during a gate repair; that was rendered into a CLAUDE.md hard rule worded "never a local
`git merge` into `main`", which was never shown back for confirmation, and was then cited as
settled policy in later work. A scoped choice became a standing rule through restatement — the
same drift shape as DL-54, applied to a rule about how the operator works rather than to
infrastructure status. Decisions that constrain the operator's own workflow get read back
verbatim before they land in CLAUDE.md.

## DL-57 · Gates must be observed failing, not assumed working  ·  status: DECIDED (2026-07-22)

**Trigger.** Three checks read green on one day while examining nothing or the wrong thing: the
security gate had run on **zero** sprint merges (DL-52), a STATE claim had no check able to
contradict it (DL-54), and the secret sweep could not see new files (DL-55). All three were found
by accident — a red Dependabot check, an operator asking to apply an already-applied flip, and a
commit that failed two minutes after a clean `make ci`.

**The shared defect.** In each case *"didn't look"* was rendered identical to *"looked and found
nothing."* Absence of evidence was displayed as evidence of absence. That is mechanizable: a check
that has never been observed rejecting anything is not known to work.

**Decision.** `scripts/gate_selftest.py` plants a known violation per gate and requires a non-zero
exit, plus asserts the config facts whose loss would silently disable a gate (the `push` triggers,
the Makefile line wiring the untracked-secret scan). It runs in the CI `quality` job on **every
push**, so it cannot rot, and `make gate-selftest` runs it locally.

**Proven at introduction, both directions.** 7/7 pass on a healthy tree. Removing the `push`
trigger from `security-findings.yml` — simulating the exact DL-52 regression — made it exit 1 and
name the invariant; neutering a case's command to one that always exits 0 made it exit 1 with
"gate exited 0 on a planted violation". A self-test never seen failing would have been the same
sin it exists to catch.

**Named limit (do not oversell this).** It cannot catch a blind spot nobody imagined; it only
tests failure modes someone thought of. The guarantee is narrower than "never again": known blind
spots cannot regress, and every new gate ships with a demonstration it can fail. The case table is
the standing record of blind spots found the hard way — each entry cites the incident that put it
there.

*Ruled out:* running it inside `make ci` (it writes probe files into the worktree; CI runners are
disposable, a developer's tree is not — `make gate-selftest` stays opt-in locally); a
documentation-only blind-spot register (a human check that cannot fail, rejected for the same
reason as DL-55).

---

## DL-58 · The exit path never executed — a green run that could only buy · status: CLOSED

**How it surfaced.** A routine "how did the run go" on `sched-2026-07-22`: 7/7 stages,
`ACCEPTANCE PASS`, five buys submitted. The only anomaly was a recurring `critical`
broker-divergence Flag naming AMD, which the runbook's own signature table invites you to read
as *"reconciliation working."* It was not. It was the single visible symptom of two defects.

**What was actually true.** On 2026-07-20 the monitor stopped us out of AMD — a `CloseDecision`
node with `trigger=stop`, `pnl_cents=-153065`, booked in the graph. The broker's entire
33-order history contains **zero sell orders**. We still held 55 AMD. The graph believed it had
exited a position it had never exited, and the divergence Flag had been correctly reporting
that fact, unread, on every run since.

**Defect 1 — the contract could not describe an exit.** `CloseDecision` carried ticker,
position, trigger, rationale and PnL, but neither **quantity** nor **price**. Execution filled
the hole with two `tunable()` settings whose own `why=` text admitted they were fixtures:
`close_quantity=1` (one share) and `close_reference_price=$1.00`. So even a close that *did*
dispatch would have offered 1 share at a $1 limit. The monitor had both real values in hand at
decision time and threw them away at the contract boundary.

**Defect 2 — the failure could not be seen.** `dispatch_closes` wraps its send in
`fault_boundary(..., reraise=False)` so a dispatch failure cannot kill the run. The default
sink is `CollectingFaultSink` — an in-process list. Nothing ever wrote a `Fault` node, while
`surfaces/queries/faults.py` had been reading `Fault` nodes for the operator incident view the
whole time. **That view was empty by construction, and its emptiness read as "no incidents."**
The existing regression test asserted `len(sink.faults) == 1` — it proved the fault was
recorded, never that it survived the process.

**Why it stayed green for days.** Buy-only execution ratchets: positions accumulate, cash goes
negative, and on 07-21 `regt_buying_power` hit **0** and all five orders were rejected at the
open. The 07-22 run then submitted five more against zero buying power. The acceptance gate
passed every one of these days, because it scores *stage completion*, not whether an order can
execute. Compare DL-57: "didn't look" rendering identical to "looked and found nothing" —
here, *"decided to sell"* rendered identical to *"sold."*

**Decision.** `CloseDecision` gains required `quantity` and `reference_price_cents` (contract
`0.2.0` → `0.3.0`); the monitor populates both from position state and the decision price;
`order_from_close` reads them off the decision; both fixture tunables are **deleted** rather
than re-defaulted, so the fallback that hid this cannot come back. `GraphFaultSink` wraps the
sink in all four graph-pull poll paths and appends a `Fault` node — keyed by origin *plus
timestamp*, so a fault recurring every run appends rather than overwrites, because recurrence
is itself the signal.

*Ruled out:* making the new fields optional with defaults (identical failure, relocated);
"fixing" the graph to mark AMD closed (DL-44 — broker is truth for holdings, never edit the
graph to agree with a story); flattening AMD at the broker to re-zero (destroys the
accumulating dataset, ruled out in DL-44); persisting faults only for monitor (the same blind
spot exists on every `reraise=False` boundary).

**Named limit.** This makes exits *executable* and failures *visible*. It does **not** make the
acceptance gate aware of buying power — a run whose orders cannot fill still scores PASS. That
gap is open, and it is the reason two dead days looked healthy.

---

## DL-59 · The gate scored intent, not outcome — UNPROVEN as a verdict · status: CLOSED

**Question.** DL-58 left a named limit: acceptance passed `sched-2026-07-21` and
`sched-2026-07-22` while the account had **zero Reg-T buying power** and not one order could
fill. Two dead days scored `ACCEPTANCE PASS`. What invariant was missing?

**The defect.** The gate's boundaries were all *conservation* checks — each stage's output
count bounded by its input (no agent fabricates). Every one held: execution submitted 5, PM
approved 5. But `submitted` is an **intent count**. It says orders were handed to the broker,
never that the broker did anything with them. The gate could not distinguish *tried* from
*traded*, which is the same failure shape as DL-57 ("didn't look" vs "looked and found
nothing") and DL-58 ("decided to sell" vs "sold").

**Why not simply fail any run with no fills.** An after-hours run legitimately has no outcome
yet: at 22:30 UTC the orders queue for the next open, and the answer arrives hours later. A
gate that failed those would be wrong every single night, and one that passed them would be
asserting a success nobody had observed. **The distinction is three-way, not binary** — filled,
resolved-unfilled, and not-yet-known — and the third state needed a name.

**Decision.** `FillOutcomes` classifies a run's Fill nodes by their real broker outcome
(`broker_status` overriding the submit-time `status`), and acceptance gains a fourth verdict:

| Outcome | Verdict | Exit |
| --- | --- | --- |
| ≥1 order filled | `PASS` | 0 |
| every order resolved unfilled (rejected/canceled/expired) | `FAIL` | 1 |
| orders still queued, none filled | `UNPROVEN` | 0 |
| no orders submitted, rejections explained | `NO_TRADE` | 0 |

`UNPROVEN` is pass-equivalent — queued orders are not a fault and must not block a deploy — but
it can **never** render as PASS. That is the whole point: LAW-02 says success is proven, not
assumed, and the old gate was asserting proof it did not have.

**Counted from Fill nodes, not `ExecutionRun.submitted`.** A broker that refuses an order *at
submit time* leaves `submitted=0` with rejected Fills on the graph; scoring the intent field
would let exactly that run pass. The end-to-end test drives a `PaperBroker(reject_tickers=...)`
cascade and asserts FAIL — with `submitted=0, orders=2, unfilled=2` proving the two differ.

**Dashboard.** `UNPROVEN` keeps the master light **GREEN** with a warning row
(`orders_unresolved`) and the summary "N orders placed, none filled yet". A nightly false RED
would train the operator to ignore the light (DL-47 is glance-first); silence would repeat the
sin. A real fault still turns it RED regardless.

*Ruled out:* reading live broker buying power in the gate (the acceptance pack is graph-only by
design — ADR-0012; the rejected Fills are the graph-visible proxy and are sufficient); making
UNPROVEN exit non-zero (blocks deploys nightly for a non-fault); treating UNPROVEN as GREEN with
no warning (invisible = the original defect); a time-based rule such as "fail if unresolved
after N hours" (invents a clock the gate does not have — re-running accept after the open gives
the real verdict for free).

**Verified on the three real runs it was built from:** 07-20 → `PASS` (5 filled), 07-21 →
`FAIL` naming "0 of 5 submitted orders filled … the run traded nothing", 07-22 → `UNPROVEN`.
The gate now separates the exact days it previously conflated.

**Named limit.** This proves *whether orders filled*, not whether they filled *well* — slippage,
partial fills, and price quality are unscored. And it is retrospective: a run is UNPROVEN until
someone re-runs acceptance after the open, which nothing yet does automatically.

---

## DL-60 · Exit lifecycle: a position is closed by a fill, not by a decision · status: CLOSED → ADR-0015

**Why this is open.** DL-58 fixed what a close order *contains*; it is live on `s135` and still
produces **zero sell orders**, because nothing sends one. The `sched-2026-07-23` re-run decided
`CloseDecision CSCO close trigger=time` and the broker's lifetime sell count stayed at **0**,
with **no fault recorded** — nothing was attempted. Before writing that dispatch, the lifecycle
it plugs into has to be decided, because the current one converts a delivery failure into
permanent capital loss.

### The three defects, in dependency order

**1 · Nothing carries a close to execution.** `dispatch_closes` is called only from
`agents/monitor/agent.py` — the **bus RPC** path. The deployed runtime is **graph-pull**, where
`monitor_pm_node` evaluates, writes the CloseDecision, links the MonitorRun, and stops. Execution's
`find_pending` polls `PMRun` nodes for *buy* intents; **no graph-pull consumer for close decisions
exists anywhere**. The sell side is not broken, it is unbuilt. Every unit test that "covers" it
drives the bus path — the one path production never takes.

**2 · The decision closes the position, so a failure strands it forever.**
`write_close_decision` writes the `CLOSES` edge at *decision* time, and
`is_open_position` excludes any Position with one. So the instant the monitor decides, the graph
stops tracking the position — whether or not a single share was sold. AMD is the proof: decided
2026-07-20, never sold, 55 shares still held, and **no future run will ever look at it again**.
One dropped message = one position held forever, silently. This is the defect that turns a
transient fault into an unrecoverable one, which is why it is worth settling before #1.

**3 · Realized PnL is booked from a price nobody traded at.** The same call writes
`pnl_cents` computed from the *current* price at decision time — AMD booked **−$1,530.65**
realized against an exit that never happened (the position is now +$1,277 unrealized). Every
downstream reporter metric — profit factor, expectancy — is therefore built on fills that do
not exist. A close is the only moment the system learns a *real* price, and it is currently
discarded in favour of a hypothetical one.

### Options for the lifecycle (the actual question)

| | Approach | Position stays open until | Verdict |
| --- | --- | --- | --- |
| **A** | Add a `close_state` (`decided`/`submitted`/`filled`) to CloseDecision; `is_open_position` excludes only `filled` | the sell fills | Works, but adds a state machine the graph must keep consistent with the broker — two truths again |
| **B** | Write CloseDecision without `CLOSES`; **execution** adds the edge when the sell fill lands | the sell fills | Lineage stays append-only and the edge means what it says: *this fill closed this position* |
| **C** | Never infer closure from our own records — the next run's broker snapshot shows the holding gone | the broker says it is gone | Most aligned with DL-44 (**broker = truth for holdings**), and needs no new state |

**Leaning: B as the mechanism, C as the backstop.** B gives the lineage (which decision caused
which fill), C gives the truth (we hold it or we do not), and they disagree only when something
is wrong — which is exactly when you want two independent readings. A is rejected: it invents a
third bookkeeping of a fact the broker already answers.

**Consequence worth stating plainly:** under B/C a close that fails to execute is simply
**re-decided next run**. Retry becomes the default behaviour rather than a feature to build, and
AMD would have exited itself on 07-21.

### The idempotency key has to change with it

`order_from_close` currently keys on `f"{close_set.run_id}:{ticker}:sell:{position_id}"`, and
`run_id` is the **monitor run**, which is new every run. Under a re-decide-until-filled
lifecycle that key would place a *fresh sell every night* — turning the fix into repeated
oversells. A whole-position exit happens once, so the key must be stable across runs and derived
from the position: `f"close:{position_id}"`. CloseDecision's own node key
(`{monitor_run_id}:{position_id}:close`) has the same problem and needs the same treatment if it
is to represent "the exit of this position" rather than "one run's opinion".

### Open questions (not yet answered — do not code past these)

- **Partial fills.** A 55-share sell filling 30 leaves a 25-share position. Does the remainder
  stay open with its original stop, or is it a new position?
- **Rejected sells.** A sell can be refused (locked shares, halted symbol). Retry silently, or
  escalate after N attempts? This is the one place where retry-forever is dangerous.
- **Timing.** Every exit is decided after the close and executes at the next open, hours later,
  at an unknown price — a stop is not a stop. Does the exit path need an intraday trigger, or is
  a once-daily exit an accepted property of the strategy? **This is a strategy question, not an
  engineering one, and it belongs to the operator.**
- **AMD recovery.** Once closure is fill-keyed, does AMD re-enter the machinery automatically
  (superseding its stale decision), or is it a one-off manual exit first? Under C it self-heals;
  under B its existing `CLOSES` edge must be neutralised deliberately.
- **PnL.** Confirm realized PnL moves to fill time. Ruled out already: keeping the
  decision-time estimate "for continuity" — it is a fabricated number in a ledger.

### Ruled out

- **Monitor calling execution over the bus from the poll path** — reintroduces a synchronous
  dependency into a graph-pull cascade (DL-08), and it is precisely the swallowed-RPC shape that
  hid this for a month.
- **Marking AMD closed in the graph to clear the divergence flag** — DL-44: never edit the graph
  to agree with a story. The flag is correct; the position is real.
- **Flattening the account to re-zero** — destroys the accumulating dataset (ruled out in DL-44).
- **Fixing #1 first (wiring dispatch before the lifecycle)** — a working dispatch on top of
  decision-time closure still strands a position on every delivery failure; it would just strand
  them faster.

**Status.** CLOSED — graduated to **ADR-0015** (2026-07-23). The operator answered all four:
fill-keyed closure, **broker-native stops** (`bracket` at entry, `oco` retrofitted onto the 9 existing
positions — Alpaca's `oco` class exists precisely for already-held positions), bounded retry (3 runs)
then escalate, and a partial fill reduces the position rather than creating a new one. AMD self-heals
under fill-keyed closure; no manual trade. One assumption remains unproven and is named in the ADR:
bracket/OCO submission **outside regular hours** queues for the next open — needs a live probe before
the implementation is trusted.

---

## DL-61 · Broker-native stops (ADR-0015 §3): stop-only, on the same rail, reconciled with ADR-0017 · status: CLOSED (shipped S138; ADR-0015 §3 amendment finally recorded 2026-08-05)

**Question.** ADR-0015 §3 accepted "the broker enforces stops and targets" but never shipped. ADR-0017
then made the analyst the sole exit decider and forced a breached stop onto the daily rail as the
**interim** floor — explicitly naming §3 as the *durable* home. Two things must now be worked out before
§3 can be built: (1) §3 as written assumed a **take-profit + stop bracket**, but ADR-0017 **retired
`target`** — so what does a broker order without a take-profit look like? and (2) if the broker holds a
resting stop *and* the analyst still force-sells at 22:30, do we **double-sell**?

### Context — what changed under §3's feet

- §3's table: new entry → `bracket` (entry + take-profit + stop-loss); held position → `oco`
  (a take-profit / stop-loss pair). Both legs assume a **target**.
- ADR-0017 §4 retired `target`/`time` as mechanics ("let winners run; exit on thesis"). A fixed +10%
  take-profit leg would **re-introduce** the mechanical profit-taking ADR-0017 deleted — a direct
  contradiction.
- S137 shipped `contracts/positions.open_position_stop_thresholds` (quantity-weighted entry × `stop_pct`,
  raises on lot disagreement) and `contracts/stop_rule.check_stop`. **The stop *price* is already
  computable** from what we built last sprint. Reuse it.
- The broker port (`agents/execution/broker.py::Broker`) does **market orders only**:
  `submit(key, ticker, side, qty, limit_price)`. It already has `cancel(broker_order_id)`
  (`alpaca.py`). Idempotency is `client_order_id` (422 → GET-by-client → replay).

### Decision 1 — **stop-only, no take-profit leg**

The broker order is a **resting sell stop**, not a bracket/OCO pair. Rationale: ADR-0017 owns the upside
(thesis, discretionary) — the broker owns only the **downside floor**. Concretely:

- **Held position** → a standalone **sell stop** at `weighted_opened_price_cents × (1 − stop_pct)`,
  full held quantity (whole shares), `time_in_force = gtc` so it *rests* until triggered or cancelled.
  (Not `oco` — OCO requires a limit take-profit leg we no longer want.)
- **New entry** → the entry is a market buy today; once it fills and shows as a position, the *same
  per-position pass* attaches its sell stop. So there is **one mechanism** — "every active position gets
  a resting sell stop" — covering both the 8 currently-held names and every future entry. (Not a
  `bracket` at submit time, because bracket also needs a take-profit leg.)

This **amends ADR-0015 §3** (bracket/oco → stop-only) and will be recorded there under "what shipped"
when it ships, the same way §1/§2 were corrected.

### Decision 2 — the broker stop rides the state we already have; the analyst **defers** to it

To avoid a double-sell, the ADR-0017 interim forced-stop (§2) becomes a **fallback**, not a peer:

- The analyst force-sells a held name on a breached stop **only when that position has no confirmed
  resting broker stop**. When a broker stop *is* resting, the analyst defers — the broker owns the floor.
- This is safe by construction: the only names the analyst force-sells are those **without** a broker
  order to collide with. And it is *robust*: if a broker stop ever fails to place, the daily forced-stop
  still fires as the safety net — we never silently lose the floor (the exact risk-control gap we keep
  fighting). ADR-0017 §5 called §3 "the durable home"; this makes the interim degrade to a backstop
  rather than be deleted.
- The monitor's S137 stop-breach `Fault` stays as the third layer: if a position is through its stop but
  still held (broker stop present but un-triggered, or placement failed), it is **visible** (DL-57).

Three layers, no collision: **broker stop (continuous)** → **analyst forced-stop (daily fallback when no
broker stop)** → **monitor Fault (visibility)**.

### Decision 3 — liveness comes from the broker, not a mutable graph status (append-only)

`kernel/graph_support.py` is append-only; a `status: placed→filled→cancelled` property is **not
representable** (the same wall that broke ADR-0015 §2's position-keyed node). So:

- A `BrokerStopOrder` node keyed `stop:{position_ref}:{ticker}` records the **immutable placement fact**
  (stop_price_cents, broker_order_id, placed_at) and is the **idempotency guard** — if it exists, don't
  re-place. The same string is the broker `client_order_id`, so a re-submit *also* replays broker-side
  (double idempotency, like the S135 exit key).
- **"Is a broker stop active?"** is answered by the **broker** (DL-44 — broker is truth for order/holding
  state): a resting stop shows as an open order; a triggered one shows as a fill and the position leaves
  the book. Closure + realized PnL then flow through the **existing** reconciliation (DL-44) and
  fill-price PnL (0.75.00) with **no new closure path** — a stop fill is just a sell fill.
- Re-basis (partial fill / re-entry) changes `position_ref` → a new `stop:{new_ref}` is placed and the
  stale one is `cancel()`-ed by its recorded `broker_order_id`. Bounded lifecycle, reusing the existing
  cancel.

### Decision 4 — the one assumption that must be **probed** before coding

Runs fire **22:30 UTC — after the US close**. The entire design rests on: *does Alpaca paper accept a
`type=stop, tif=gtc, sell` order submitted after hours and let it rest for the next session?* ADR-0015 §3
already flagged this as "the one assumption not yet proven against the API." **It is a hard gate:** if
after-hours gtc stops are rejected, stop-only-at-22:30 does not work and the design pivots (e.g. an
intraday placement window — which ADR-0015 rejected for other reasons). **Probe before Codex builds:**
submit one gtc sell stop far below market on a held name against the paper account, confirm it rests
(`new`/`held`), then `cancel()` it. Operator-authorized, controlled, self-cleaning.
**PROVEN 2026-07-25** (market closed, ~03:00 UTC — the same after-hours condition as a 22:30 run): an
`AMD` gtc sell stop 30% below market returned `status=accepted, type=stop, tif=gtc` (resting, not
rejected) and cancelled clean. The gate is cleared; the mechanism stands.

### Options weighed

| Option | Verdict |
| --- | --- |
| Full `bracket`/`oco` with a take-profit leg (§3 as written) | **Ruled out** — reintroduces the mechanical target ADR-0017 retired. |
| Stop-only resting sell stop, one per active position | **Chosen** — floor without touching the upside. |
| Remove the ADR-0017 interim forced-stop entirely once §3 ships | **Ruled out (for v1)** — a placement failure would then leave a position with *no* stop, silently. Keep it as the gated fallback. |
| Mutable `status` on a stop node | **Ruled out** — append-only forbids it; broker is truth for liveness anyway (DL-44). |
| Intraday KEDA window to place stops during RTH | **Ruled out** — ADR-0015 already rejected: still polling, adds market-hours compute; gtc resting removes the need if the probe passes. |
| A second order rail for stops | **Ruled out** — DL-60; the stop is submitted by execution on the one rail. |

### Open questions (do not code past these)

1. ~~**The after-hours probe (Decision 4)** — must pass first.~~ **CLEARED 2026-07-25** (see Decision 4).
2. **Where the per-position stop pass runs** — most likely execution's existing poll, right after
   reconciliation each run, iterating active positions. Confirm it does not fight the buy/sell submission
   ordering.
3. **Interaction with a same-run thesis sell** — if the analyst sells a name on thesis *and* that name has
   a resting broker stop, the market sell will fill and the stop must be `cancel()`-ed (or it dangles as a
   naked sell stop with no position). Cancel-on-exit is part of the lifecycle.

**Status.** Design settled; the after-hours probe **PASSED 2026-07-25**. Reuses S137's `open_position_stop_thresholds` for the stop
price and the existing reconciliation/PnL for closure. Graduates to an ADR-0015 §3 "what shipped"
amendment on merge. **feat** → 0.76.00 → 0.77.00.

---

## DL-62 · Unify stop exits through the broker; retire the interim forced-stop · status: OPEN (recommended: A)

**Question.** S138 gave every *un-breached* held position a resting broker `gtc` stop (ADR-0015 §3).
But a position that is **already through its stop** never gets one: `place_broker_stops` skips tickers
being sold this run, and the S137 analyst forced-stop (a market sell) is what exits it. So stop-driven
exits are now split across two mechanisms by breached-vs-not. What is the durable single mechanism?

### Evidence that surfaced it (MRVL, 2026-07-24 → 2026-07-27)

MRVL breached its 5% stop (entry $226.21, now $194.23, **−$1,407**). The S137 forced-stop fired
correctly and submitted `sell 44 market tif=day` at **Fri 22:40 UTC** — but the market was closed, so
it sat `accepted`/unfilled all weekend and fills at **Monday's open**, at whatever price that is
(≈ **14% loss**, not the 5% the stop implies). Three flaws the interim can't escape:

1. **Uncontrolled fill** — a market sell placed after close fills at the *next open*, gap-exposed. The
   "stop" triggers an exit; it does not cap the loss near the stop level.
2. **No intraday/weekend protection** — the position bleeds for days with a dead order on it. (A broker
   stop is no better *over a closed market* — nothing trades — but during the week it triggers intraday.)
3. **Idempotency-key-reuse risk** — the sell is keyed `exit:{position_ref}:{ticker}:sell` (0.74.01). If
   the `day` order **expires** unfilled over a weekend, the key is consumed: the idempotent replay
   returns the dead order and the position may never be re-submitted. **Must be watched.**

### Why S138 does not already cover it

`agents/execution/broker_stops.py::place_broker_stops` skips `sold_tickers` (names with a sell
`OrderIntent` this run). A breached name is force-sold by the analyst → it is in `sold_tickers` → no
broker stop is placed. So the broker stop only ever protects names **above** their stop; breached names
fall through to the after-hours analyst market sell. Complementary, but two paths and a gap.

### Options

| Option | What | Trade-off |
| --- | --- | --- |
| **A (recommended)** | A broker stop for **every** held name: resting `gtc` for un-breached; a **marketable** broker exit for already-breached. Retire the S137 analyst forced-stop; keep the monitor breach-`Fault` as the visible safety net (DL-57). | One continuous mechanism, no dual path, no after-hours analyst market sell. Removes S138 §C's analyst fallback — the monitor Fault must carry the "stop failed to place" visibility. |
| **B** | Keep the split; make the forced-stop a **stop-limit** to bound the gap-down fill. | A limit can **miss** on a hard gap → the position does *not* exit. Worse risk control; rejected. |
| **C** | Leave as-is. | MRVL exits Monday and the design is coherent, but flaws 1–3 persist. Rejected as the end-state; acceptable only as the interim it already is. |

### Recommendation

**A.** The broker becomes the *sole* home of the stop for all held names — the natural completion of
S138 and ADR-0017 §5 ("§3 is the durable home"). The analyst forced-stop retires; the monitor's
stop-breach Fault stays as the safety net for a placement failure. Graduates to an **ADR-0015 §3
amendment** when built.

**Open sub-questions for the sprint:** (a) exact Alpaca order for the marketable exit of a breached
name (market vs stop with a trigger already crossed) and its after-hours/next-open behaviour — **probe
like DL-61**; (b) the idempotency-key-reuse case (flaw 3) — detect an expired/dead exit order and re-key
rather than replay it.

**Status.** OPEN, recommended **A**, pending operator go for a sprint. Immediate MRVL action: none (can't
trade over a weekend) — verify the Monday fill + booked realized PnL; if the `day` order expired, cancel
and re-key.

---

## DL-63 · Non-secret runtime config has no delivery channel to the fleet · status: OPEN (recommended: B)

**Question.** Where should a *non-secret* runtime parameter — the LLM model id, the reasoning
effort level — live, so that changing it changes what the deployed fleet actually runs?

### The constraint, discovered while moving the operator to Opus 5 at max effort

Editing `.env` looks like the answer and is not. A deployed container **never reads `.env`**.
`kernel/bootstrap.py::_apply_config` writes into `os.environ` exactly what the master returns in
`ACTIVATE.config`, and what the master returns is driven by `orchestration/packs/trading_secrets.json`
— a map of **Key Vault secret name → env var name**. The operator's entire grant is one row:
`["anthropic-api-key", "ANTHROPIC_API_KEY"]`.

Verified live on the deployed operator app (2026-07-27): its container env is `MASTER_URL`,
`MASTER_PUBLIC_KEY_PEM_B64`, `POSTGRES_DSN`, `AZURE_SERVICEBUS_CONNECTION_STRING`,
`AZURE_SERVICEBUS_CONNECTION_STRINGS_JSON`. No model, no effort, no `.env`.

**Therefore the `tunable()` literal in code is the fleet's effective value.** That is why 0.78.00
moved the defaults (`claude-sonnet-4-6` → `claude-opus-5`) rather than relying on the operator's
local file — an `.env`-only change would have been a silent no-op in production while appearing to
work locally.

### Delivery options

- **A · Status quo — code default + redeploy.** Honest and versioned; every change is a commit, a
  CI run, and a fleet retag. Cost: a model swap is a deploy, not a config edit.
- **B · Extend the pack with a non-secret `config` section** (recommended). ACTIVATE already writes
  arbitrary key/values into `os.environ`; only the *pack schema* is secret-only. Keeps one delivery
  path, keeps the graph as the record of what was delivered.
- **C · Set Container App env vars directly** (`az containerapp update --set-env-vars`). Works today,
  no code change — but bypasses the pack, leaves no trace in the graph, and drifts from the IaC.

### Options ruled out

- **Key Vault for the model id.** A model name is not a secret. It buys nothing and *loses* the
  `tunable()` catalogue, the bounds validation (the `Literal` that rejects a bad effort level at load
  instead of as a 400 mid-run), and the `laws.md` PARAM documentation — in exchange for a vault
  round-trip on every boot. Vault is for credentials.

---

## DL-64 · Dependabot: batch monthly, isolate only production majors · status: CLOSED (implemented)

**Question.** The dependency-surveillance config promised "MAJOR bumps open their own PR so a
breaking change is reviewed in isolation." In practice those solo PRs were **closed unread**
(#69 setup-uv 8→9, #70 setup-python 6→7, #72 dev-minor group, all closed 2026-07-27 without
review). A review rule that reliably produces non-review is worse than no rule. What cadence and
grouping actually gets looked at?

### What was actually happening

Grouping already worked — #72 was a proper grouped PR. The leak was that every group covered only
`["minor", "patch"]`, so **majors fell out and opened solo**, weekly, across three ecosystems.

### Decision

Monthly, and fold majors into the group **except** for Python *production* dependencies:

| Ecosystem | Majors | Why |
| --- | --- | --- |
| uv · production | **solo PR** | The only class that reaches the running fleet |
| uv · development | grouped | A break costs a red build, nothing else |
| github-actions | grouped | Ditto; also SHA-pinned, so tag-hijack is already blocked |
| docker | grouped | Python major already pinned out by the existing `ignore` |

Expect ≤3 PRs in a typical month.

### Constraint discovered while deciding

**This was never the CVE net, and `dependabot_security_updates` is `disabled` on the repo.** The
actual net is `pip-audit` inside `make ci` — no `-` prefix on the Makefile recipe, so a known
Python vulnerability **fails the build** (hardening row L is closed) — plus the Trivy HIGH/CRITICAL
image scan in `build-images.yml`. So slowing *version* updates does not slow *vulnerability*
response. Enabling Dependabot alerts would add a net for GitHub Actions and the base image, which
neither pip-audit nor Trivy covers as advisories; that remains **open and unclaimed**.

### Resolved (2026-07-27, same day)

**Dependabot alerts + security updates: ENABLED.** The open item above is closed. Repo went
`disabled` → `enabled` with **zero open alerts** at the time, so nothing was hiding and no
backlog surfaced. Security PRs bypass both the monthly schedule and `open-pull-requests-limit`,
so a vulnerability still arrives the day its advisory drops — routine noise stays batched,
genuine ones jump the queue. That closes the gap this entry named: advisories against pinned
GitHub Actions and the base image, which `pip-audit` (Python packages only) and Trivy (image
contents, not action versions) both miss.

**Interaction found while reconciling the docs.** `dependabot/fetch-metadata` reports a
**group's** `update-type` as the *highest* semver change among its members, and
`dependabot-auto-merge.yml` only auto-merges when that is not `semver-major`. So folding
majors into a group means **one major makes the whole monthly batch wait for a human**,
routine members included. That is the intended trade — and it is a second, unplanned reason
the production-majors carve-out was right: `python-production` stays minor/patch-only, so
production dependency updates keep auto-merging untouched.

### Approaches ruled out

- **Batch everything including production majors.** A hard ceiling of 3 PRs/month is tempting, but
  a grouped red build gives no signal about *which* member broke it, and for a runtime dependency
  that is the moment isolation is worth most.
- **Monthly cadence alone, grouping untouched.** Fixes frequency, not the trickle — #69 and #70
  would still have arrived as separate PRs, just less often. It treats the symptom.

---

## DL-65 · The root Dockerfile was dead, and the guard watching it was wrong · status: CLOSED

**Trigger.** The first monthly Dependabot batch (DL-64) auto-merged `#73`:
`FROM python:3.13-slim` → `python:3.14-slim`, on a repo whose `requires-python` is `>=3.13` and
whose ruff/mypy both target py313.

### Two separate defects, one symptom

**1 · The ignore rule did not do what its comment said.** It blocked
`version-update:semver-major` while claiming to "pin to 3.13.x". `3.13 → 3.14` is semver-**minor**,
so it walked straight through. The guard was wrong, not unlucky — a real runtime migration would
have auto-merged the same way. Fixed: block minor *and* major.

**2 · The file it changed was dead.** Nothing built the root `Dockerfile`. Verified exhaustively
before deleting, because "unused" is the kind of claim that is cheap to assert and expensive to get
wrong:

| Candidate consumer | Reality |
| --- | --- |
| `build-images.yml` | Builds 14 images from `agents/*/Dockerfile` + `orchestration/Dockerfile` |
| `docker-compose.yml` | Every service pins `dockerfile: agents/<name>/Dockerfile` |
| `infra/`, `Makefile` | No reference |
| `docs/architecture.md`, `docs/deployment.md` | Referenced it — **both stale**, describing a monolith superseded by ADR-0007 |

It was the pre-P15 monolith image. Deleted, and both doc references corrected rather than left to
describe a deployment shape that has not existed since S74.

### Consequence for the docker ecosystem

Dependabot's `docker` entry was `directory: "/"` — so it watched **only the dead file**, and had
never watched the 14 images actually shipped. Repointed at `/agents/*` and `/orchestration`.

**Named uncertainty:** those Dockerfiles use `dhi.io/python` (Docker Hardened Images), and whether
Dependabot can resolve that registry is **unverified**. If it cannot, this entry produces nothing —
which is precisely the silent-no-op trap this entry exists to close, so it is written down rather
than assumed. Trivy HIGH/CRITICAL at image build stays the real CVE net (backlog E/H); this is
freshness signal only.

### The general lesson, matching DL-52 and row L

A guard can be present, documented, and still not guard: `-uv run pip-audit` could not fail, this
rule blocked the wrong semver level, and a `directory` pointed at a file nothing built. In all
three the *config existed* — reading it was enough to believe it worked. Only tracing what actually
consumes it settles the question.

---

## DL-66 · Graph vocabulary: constraints wired, inference still refused · status: CLOSED (0.79.00)

Builds the constraint half R007 recommended. `kernel/graph_vocabulary.py` declares a closed set of
labels, edge types, and edge shapes; `kernel/graph_guarded.py` wraps any `GraphStore` and rejects a
non-conforming write **before it reaches the store**. Reads pass straight through. Nothing derives
or writes a fact — the refusal of inference in R007 §5 stands.

**ADR-0012 split.** Mechanism is substrate (`kernel/`, names no trading concept); the vocabulary is
pack data (`orchestration/packs/trading_graph_vocabulary.json`), loaded via `GRAPH_VOCABULARY_PATH`
at the one composition root, `build_graph_from_env`. Unset ⇒ unguarded, so nothing changes for a
caller that has not opted in.

### The vocabulary was derived from evidence, not written by hand

Union of three sources: the **live Neon graph** (36 labels, 25 edge types, 31 observed
`parent -> edge -> child` triples), **code literals and constants**, and the `labels_owned` /
`labels_read` blocks in the agent law files. Result: 71 labels, 42 edge types, 34 signatures.

### The guard immediately found something, which is the point

Running the real cascade under the guard failed with:

```text
VocabularyError: edge 'FORECAST_BY' is not declared to run AnalystRun -> ForecasterRun
```

`ForecasterRun` is **not among the 36 labels in the live graph** — that code path exists and has
never written to production. A vocabulary built from live observation alone would have been
complete-looking and wrong. Fixed by recording what the cascade actually writes and merging it in
(31 → 34 signatures).

### Proof that the gate can fail

The first proof attempt was worthless and is worth recording as such: running the existing e2e
tests with `GRAPH_VOCABULARY_PATH` set passed 6/6 — but those tests construct `InMemoryGraphStore()`
**directly**, bypassing `build_graph_from_env`, so the guard never engaged. A passing test proved
nothing, which is exactly the DL-65 pattern one layer up.

`orchestration/tests/test_graph_vocabulary_e2e.py` replaces it with three tests, and the
load-bearing one is negative — drop `RunRequest` from the declaration and the cascade must raise.
Same principle as `pip-audit-cve` in `gate_selftest_cases.py`: a gate that cannot be shown to fail
is not a gate.

### Ownership is deliberately NOT enabled, and why

`Vocabulary.check_node(writer=)` is built and tested, but the pack ships `owners: {}`. The eight
law declarations are **not accurate enough to enforce**: `reporter` lists a read-set (13 labels it
mostly does not write), and `supervisor` declares the literal string `"all"`. Enforcing them today
would break agents on bad data.

**Named, not dormant:** the next step is reconciling those declarations against what each agent
actually writes — measurable now by running each agent under a recording store. That is the
remaining half of R007's item 1.

---

## DL-67 · CodeQL is the wrong tool for "guards that don't guard" - gate_selftest is · status: CLOSED

**Question.** Can CodeQL detect the class of defect that dominated 2026-07-27 - a check that is
present, documented, and examines nothing?

**Answer: mostly no, and the right tool was already in the repo.** CodeQL queries a database built
by a *language extractor* over source code. Of the seven gaps found that day, five were not in code
at all:

| Gap | Where it lived | CodeQL |
| --- | --- | --- |
| `-uv run pip-audit` ignoring exit status | Makefile recipe | no extractor |
| ignore rule blocked major, not minor | dependabot.yml semantics | no |
| `directory: "/"` -> a Dockerfile nothing builds | config <-> filesystem <-> workflow | no |
| `labels_owned` declared, never read | Markdown <-> Python | no |
| `ANTHROPIC_MODEL` never reaches the operator | env name <-> pydantic `env_prefix` | no |
| e2e tests bypass the guarded factory | Python | plausible |
| `output_config` never sent | Python | plausible |

These are **correspondence failures between artifacts**. CodeQL models one artifact. The fitting
tool is `scripts/gate_selftest_cases.py` - a bespoke conformance harness that runs inside `make ci`
and reads whatever file it is pointed at. Three cases added: `dependabot-pins-python-to-3-13`,
`graph-vocabulary-guard-wired`, `codeql-custom-query-referenced`. Each was **proven able to fail**
by removing the asserted string and re-running, not merely observed passing.

### What the investigation found on the way

**The custom CodeQL pack never ran.** `codeql.yml` requested only `security-and-quality`; nothing
referenced `codeql/python-security/`. Latest report: 2026-06-23. A fifth instance of the pattern -
and the one that makes the point, because it is the *security* tooling that was reading as coverage
while examining nothing.

The two queries got opposite treatment, because they are not alike:

- **`TaintTracking.ql` - WIRED IN.** Project-specific and genuinely uncovered by the standard suite:
  it tracks MCP tool args, `os.environ`, `sys.argv` and argparse namespaces into
  `urllib.request.urlopen`, which this codebase calls with env-derived URLs in the provider,
  execution and probe paths. Now referenced from `.github/codeql-config.yml`.
- **`AgentCrossImport.ql` - DELETED.** Its own docstring conceded it duplicates the `.importlinter`
  independence contract, which fails `make ci` on every commit. It was also absent from its own
  pack's `.qls` suite - an orphan twice over. Kept, it would be a second implementation of an
  already-enforced rule, and 263 lines of README documenting it.

**A latent bug surfaced while removing it.** `run_codeql_agent_boundary.ps1` is a *generic* runner
(`-Query`, `-OutputDir`), and `reports/taint-tracking/INDEX.md` documents using it for
TaintTracking - but line 148 hardcoded
`results\local\python-security\AgentCrossImport.bqrs`. Every non-default `-Query` looked for the
wrong result file. So the documented TaintTracking invocation could never have worked. Renamed to
`run_codeql_query.ps1` and the result name derived from the query.

### The general rule

CodeQL answers *"does untrusted data reach a dangerous sink?"*. It does not answer *"did the thing
I wired actually get wired?"*. The second question is the one this repo keeps losing, and it is an
assertion, not a dataflow query.

### Addendum — the fix for this entry was itself a dormant guard, for one commit

Wiring `TaintTracking.ql` into `codeql-config.yml` **did nothing**. A dispatched CodeQL run went
green having evaluated **172 queries, none of them ours** — found only by grepping the run log for
the query name instead of accepting the green tick.

Cause: `queries:` on the `codeql-action/init` step **replaces** the config-file list unless it is
prefixed with `+`. The workflow said `queries: security-and-quality`, so the config's `queries:`
block was ignored entirely. Fixed to `+security-and-quality`; re-dispatched and verified from the
log — `Compiling query plan for .../TaintTracking.ql`, and the query-source tally moved from
`172 codeql` to `172 codeql / 1 local`.

Invariant added: `codeql-config-queries-not-overridden`, asserting the plus.

**This is the entry's own thesis landing on the entry.** Writing the config was not the same as the
query running, exactly as declaring `labels_owned` was not the same as enforcing it, and a `.ql`
file existing was not the same as it being referenced. Three layers of the same mistake in one
afternoon, and only the last one was caught by *checking the artifact rather than the status*.

---

## DL-68 - The vocabulary guard was undeployable, and its pack was a trailing indicator · status: CLOSED (0.80.00)

S143 shipped the write-time vocabulary guard and closed honestly: `GRAPH_VOCABULARY_PATH` was unset
everywhere, so the guard guarded nothing. Turning it on was supposed to be a one-line change. It was
two defects deep, and the second one nearly cost a live capital-protection proof.

### Defect 1 - a path interface, and no image has the file

`GRAPH_VOCABULARY_PATH` names a file. **None of the 14 images contains one.** Every agent Dockerfile
copies exactly `kernel/`, `contracts/`, and its own `agents/<name>/`; `orchestration/packs/` is in
none of them. Setting the variable to the pack path would not have enabled the guard - it would have
raised `FileNotFoundError` inside `build_graph_from_env` and taken the agent down at boot.

The repo had already solved this. The master receives its trading pack as **base64 env content**,
path as the local-dev fallback (S86 / DL-12, `_resolve_pack`). S143 invented a weaker mechanism
instead of following the one in the same repository. Fixed: `GRAPH_VOCABULARY_B64` resolved first,
`GRAPH_VOCABULARY_PATH` retained for local dev, injected for every agent by `deploy-agents.ps1`.

### Defect 2 - a vocabulary derived from history cannot cover code that has not run

The pack was built from the live graph (31 observed triples) plus code literals. **Observed** edges
only. So any path that had never executed in production was missing by construction.

ADR-0015 section 3 broker-native stops merged Friday and had never placed a stop. Both its write
edges were undeclared:

```text
('Fill',     'STOPS_WITH',   'BrokerStopOrder')  -> declared: False
('Position', 'PROTECTED_BY', 'BrokerStopOrder')  -> declared: False
```

Both *labels* and both *edge types* were declared; only the signatures were missing - the last thing
`check_edge` tests. **Enabling the guard would have raised `VocabularyError` at the moment execution
placed the first real stop**, destroying the ADR-0015 proof pending since Friday, in the name of a
guard built to prevent damage. A guard whose declaration lags the code is not a safety net; it is a
scheduled outage.

### The fix: prove the pack is a superset, two ways

Neither check alone is sufficient, which is the point.

- **Static** (`scripts/vocabulary_coverage.py`, `scripts/vocabulary_signatures.py`) - every label,
  edge type, and *recoverable* signature in shipped code must be declared. Signature recovery
  follows Node-valued locals back to the `merge_node` that produced them, one hop through helpers
  that return one directly. It recovers `Fill -STOPS_WITH-> BrokerStopOrder`, so this check would
  have caught the defect that nearly landed tonight.
- **Dynamic** (`test_graph_vocabulary_e2e.py`) - the broker-stop path executed under a guarded
  store. `Position -PROTECTED_BY-> BrokerStopOrder` resolves its parent through a dict lookup, so
  **no static scan can recover it**; only running the code proves it.

The static pass also found a third genuine gap neither the live graph nor manual reading had:
`Experiment -PROPOSES-> ParamChange` in the researcher.

### The check's own false positive - worth recording

The first signature run reported `Rejection -EMITTED_BY-> PMRun`, which no call site writes. Cause:
resolution was flow-insensitive, and `agents/portfolio_manager/store.py` rebinds `node` from
`OrderIntent` to `Rejection` inside one function, so the later binding answered for the earlier
call. Fixed by resolving to the nearest assignment **above** the call site. Unioning the bindings
would have been worse than the bug: it would have invented edges and pushed them into the pack,
permanently weakening the guard to make a check pass. **A completeness check that over-reports gets
"fixed" by declaring fiction.**

### Ruled out

- **Enable in the same change that makes it enablable.** Rejected on sequencing: tonight is the
  first session-day run since the broker-stops deploy, nine positions hold no protective stop, and
  a fail-closed write path is the wrong thing to introduce into that run. Fixes before features -
  the stop proof outranks the guard. Enablement is a dated action, not an indefinite deferral.
- **Warn-only / observe-then-enforce mode.** This is precisely the "guard that doesn't guard"
  pattern (DL-65) with a flag on it. If it cannot reject, it is not a guard.
- **Copy `orchestration/packs/` into all 13 images.** Larger blast radius than a deploy-time env
  var, and it bakes pack data into substrate images - the coupling ADR-0012 exists to prevent.
- **Drop `edge_signatures` and check only labels plus edge types.** Would have made enabling safe
  today by deleting the dimension that actually catches misattached edges.

### The standing rule

A declaration derived from observation is a trailing indicator. It must be mechanically checked
against what the code *can* do, or it silently rots into a trap that fires on the first novel path -
which is, by definition, the path nobody has tested.

---

## DL-69 - ruff 0.16 wanted to reformat 36 docs; a dependency bump is not the place · status: CLOSED (0.80.01)

The first monthly batched Dependabot PR under DL-64 (#75: ruff 0.15.22 -> 0.16.0,
prometheus-client 0.20 -> 0.26.0) failed `quality`. Neither cause was a defect in the bump; both
were ruff behaviour changes, and only the second needed a decision.

### 1 - S310 narrowed, so two suppressions went dead

`S310` (unvalidated URL open) no longer fires on a `Request(...)` built from a literal `https://`
f-string, so `RUF100` rejected the now-unused directives at `scripts/sb_sas_kv.py:29` and
`surfaces/dashboard/github_builds.py:71`. Removed them, kept the rationale as plain comments.

**Checked per site rather than blanket-stripping:** the `urlopen(...)` suppression at
`sb_sas_kv.py:38` *still* fires and stays. The rule narrowed for one call shape, not for the file.
No runtime change - both URLs remain fixed-scheme HTTPS with `quote()`-escaped interpolation.

### 2 - ruff format now formats Python inside Markdown

Scanned files went 800 -> 1105. **36 doc files would be rewritten.** The snippets in `docs/` are
read, not run: they carry deliberate alignment, elided bodies and pseudo-signatures. The first diff
ruff offered stripped the aligned `Callable` parameters in `sprint-79-agent-work-loops.md` - the
alignment that made the example legible.

Set `extend-exclude = ["*.md"]`, which is exactly behaviour-preserving: ruff never linted or
formatted Markdown before 0.16.

### Ruled out

- **Accept the 36-file reformat.** Unreviewable scope creep riding a version bump. It silently
  edits example code that **no test covers**, so nothing would catch a snippet made wrong - and it
  buries a docs-style decision inside a dependency chore where no one would look for it.
- **Pin ruff below 0.16.** Freezes the linter to dodge one formatting opinion, and every later
  security or rule improvement pays for it. The exclusion is narrower and reversible.
- **A numbered sprint for this.** Dependency policy already lives in the design log (DL-64); the
  code change is three lines. A sprint doc would be ceremony around a chore.

### Worth noting for next month

The group is labelled `deps-dev`, but `prometheus-client` sits in the **runtime** extra too, so a
"dev" batch moved a production dependency. It is a MINOR, so DL-64's config grouped it correctly -
the *label* undersells the blast radius, not the rule. Read the diff, not the title.

### The standing rule

**A dependency bump may change the tool; it must not carry an unrelated repo-wide rewrite.** When a
new tool version wants to touch files outside its previous scope, the default is to hold the old
scope and let the expansion be argued on its own. If Markdown snippets should be formatted, that is
its own chore with its own diff - not a side effect of upgrading a linter.

---

## DL-70 - Arresting artifact/claim drift: stop asserting presence, start planting violations · status: DECIDED (standing practice; `scripts/gate_selftest.py` 19/19 as of 2026-08-05)

Six entries this month record the same failure (DL-52/54/55, DL-65, DL-66, DL-67, DL-68). It is not
six accidents. It is one structural weakness, and it follows from a deliberate choice.

### Why it is endemic here

The platform is assembled from **declarations** - law files, pack JSON, workflow YAML, env vars,
`labels_owned`. That is ADR-0012 working as intended. But a declaration is **not self-executing**,
and **a dead declaration is indistinguishable from a live one**. Dead imperative code shows up as
unreachable or uncovered; a dead declaration just sits there looking enforced.

| Artifact that existed | Claim it was taken to prove | What was missing |
| --- | --- | --- |
| `labels_owned` in 8 law files | ownership enforced | zero lines of Python read it |
| `TaintTracking.ql` | the query runs | unreferenced; then `queries:` replaced instead of appending |
| `-uv run pip-audit` | CI fails on a CVE | the leading dash swallowed the exit code |
| `GRAPH_VOCABULARY_PATH` | the guard is enablable | no image copies `orchestration/packs/` |
| 34 edge signatures | the pack covers writes | derived from history; unrun code invisible |

The shape is always: **an artifact is necessary, is mistaken for sufficient, and nothing tests the
path between it and the effect.**

### The instrument exists; we reach for the weaker half

`gate_selftest.py` holds two kinds of case, and they are not equal:

- **can-fail** - plant the real violation, assert rejection. Tests the *claim*. **5 cases.**
- **invariant** - assert a string is present in a file. Tests the *artifact*. **9 cases.**

The invariants are the same class of thing that keeps failing: `must_contain=("GRAPH_VOCABULARY_B64",
"_guarded(")` passes happily if the guard is unreachable. **Every `must_contain` is an IOU.** S144
made the ratio worse - it added one invariant and no can-fail twin.

`pip-audit` is the only gate carrying **both** (`pip-audit-cve` proves it can fail;
`pip-audit-not-ignored-by-ci` blocks the dash returning). That pairing is the template.

### Three rules

1. **A guard ships with the violation it exists to catch** - plant the specific bad input and assert
   rejection, in the same commit. Positive-only tests are why S143's "6/6 passing" proved nothing.
2. **One test per guard must traverse the composition root.** The recurring mechanism is *bypass*:
   tests construct `InMemoryGraphStore()` directly, proving the class while saying nothing about
   whether the wiring is reached. The guard lives in the wiring.
3. **Ask reachability, not presence.** For the fleet the sharp form is: **the image is the boundary
   of truth - not COPY'd means it does not exist at runtime.** That one question would have caught
   DL-68 defect 1 before it shipped.

### Moving the existing debt back

Audit the 9 invariants; for each, name the claim and ask whether it can be executed. Convert what
converts, and **mark the rest explicitly as artifact-only** so they stop reading as proof. Then
track the ratio: if invariants outgrow can-fail cases, the IOUs are accumulating again.

Two convert cheaply, both added by S144:

- `graph-vocabulary-injected-at-deploy` asserts a string in a `.ps1`. The claim is *a container
  receives a usable vocabulary* - executable by running `Get-VocabularyEnv` and asserting the output
  base64-decodes into a valid `Vocabulary`.
- An **image-reachability check**: every path a runtime default can reference must be either COPY'd
  into the image that reads it or delivered by env.

### Honest limits

Not all of it mechanises. DL-69 - reasoning that existed but was recorded only in a commit message -
was not a guard failure; LAW-06 already covered it and the discipline simply was not applied. The
cheap mechanical half is asserting that every `DL-NN` cited in code exists in this file.

**Sequenced after the ADR-0015 section 3 stop proof.** It is a fix, but nothing is bleeding from it,
and capital protection outranks it.

---

## DL-71 - The exit replay was a rewrite in an append-only store · status: PARTLY RESOLVED (A shipped and proven as S145; B still deferred; the fan-out lesson unfiled)

**Trigger.** `sched-2026-07-27` reached 4/7 stages and scored `ACCEPTANCE FAIL`. Execution crashed
with `ValueError: property 'price_cents' cannot be overwritten` in `write_fills`, restarted, and
crash-looped from 22:40:31 until the KEDA window closed at 00:33. Monitor and reporter never ran.
The same run placed the **first six broker-native stops** (ADR-0015 section 3, proof pending since
Friday) and booked the **first realized forced-stop exit** (MRVL 44 @ $195.98, -$1,330.12), because
`place_broker_stops` runs before `run_submit` in `poll.py`.

**The defect.** 0.74.01 keyed exit orders on the position rather than the run, so an unfilled sell
would *"replay instead of duplicating"*. That one string does two jobs: at the broker it is the
`client_order_id` (the oversell guard - it worked), and in the graph it is the `Fill` node key. The
graph is append-only. A replay is byte-identical only if the reference price never moves, and it
always moves (`19451` -> `18928`). **The replay path had never actually replayed before**; its first
real execution killed the cascade. The oversell guard was right; treating a replay as a *rewrite*
was not.

**Why a replay happened at all - the upstream cause.** The MRVL exit had filled at Monday's open,
nine hours earlier. Nothing removed the position from the book: the broker snapshot is written by
execution at stage 5, but the book is only healed by the monitor at stage 6 - one full run later -
and 07-25/07-26 were weekend skips. So the analyst scored a stale book, re-decided `MRVL sell`, the
PM approved a full exit of a position that no longer existed, and execution rebuilt the dead
position's exit key.

**Two options, both real.**

- **A - make attempts append-safe (shipping, S145).** One attempt = one immutable node; the broker
  key stays stable, the graph key gains an attempt ordinal; a completed exit is never re-issued; a
  per-intent failure degrades to a per-intent `Fault` instead of taking three stages down. Bounded,
  testable, and it unbricks production.
- **B - reconcile the book before the analyst decides (deferred).** Heals the actual cause: no stale
  book, no phantom exit intent. Deferred because it reorders the cascade and moves position truth
  across DL-44's ownership line, and that is not a change to make on top of a live outage. **Not
  rejected** - the natural successor sprint.

**Ruled out.** *Making `price_cents` mutable* - it would fix the crash by discarding the property
the store exists to provide; the wrong number staying visible-but-superseded is the better audit
trail (the `repair_close_pnl.py` precedent, 0.74.03). *Reverting to a run-scoped exit key* - that
restores the 0.74.01 oversell hazard, where an unfilled sell is re-submitted as a second distinct
order every night. *Catching the `ValueError` in the work loop and continuing* - it would keep the
fleet alive while writing nothing, which is DL-57's failure mode with extra steps.

**The general lesson.** Execution is a **fan-out** stage, and it had no per-item containment: one
ticker's write failure cost three stages, a night's trading, and the reconciliation that would have
prevented it. This is DRIFT-014 / S128 (*one 429 costs one ticker, not the feed*) restated for
order submission. Worth auditing every other fan-out stage for the same shape.

**Named limit.** Both live orders from the crashed run (AMD sell 55, ABT buy 95) carry no `Fill`
node, so a naive retry records `rejected` for orders that are actually live - a fabricated outcome
of exactly the DL-57/DL-59 class. Adopting broker state on a duplicate-key refusal is part of A.

**Where this stands, 2026-07-29 (updated — B is now packaged as S147).** **A is done and proven**
(S145, 0.80.02, merged `2c49f88`, fleet
`:s145`): `sched-2026-07-27` — the run that crash-looped for two hours — was resumed and scored
`ACCEPTANCE PASS` at 7/7, and the completed-exit skip later fired on a live scheduled run for real
(`CompletedExitReplaySkipped … AMD position_ref=22d71d0d3acc0586`), containing the exact defect that
bricked the fleet. The named limit held: no fabricated `rejected` was written, and both crash
orphans adopted broker state as designed. **B is packaged as
[S147](sprints/sprint-147-fresh-book-before-decision.md)** — a head-of-run position sync, kept
lawful by leaving both jobs with their owners: execution refreshes the `BrokerPositionSnapshot`
(`EXEC-IDN-01`, sole broker interface) and the monitor reconciles the book (`MON-IDN-02`, sole
`Position` writer), with the analyst simply not pending until that has happened. Two agents in a new
order rather than one agent doing both jobs — the ownership line DL-71 worried about is not crossed,
because only the *triggers* move. B is also smaller than it looked:
[ADR-0018](decisions/0018-decision-validity-same-session-or-dropped.md) drops unfilled orders at
session end, removing the *carried* phantom intent — but not the *authored* one, which is what B
fixes and why the two are complementary rather than alternatives.
**The fan-out lesson was never acted on** — S145 gave *execution*
per-item containment, but the audit this entry called for ("worth auditing every other fan-out stage
for the same shape") was never scheduled. Parked in [ideas.md](ideas.md) 2026-07-29 so it stops
living only inside this paragraph.

---

## DL-72 - Self-healing that only works once is not a repair path · status: RESOLVED (S146 — repair script shipped, applied to production, proven idempotent)

**Trigger.** Probing production on 2026-07-28, after S145 merged (`2c49f88`), to find out what the
AMD/ABT orphans actually need. The probe found something the S145 spec did not: **no `ExecutionRun`
exists for `pm-run-df925eea017a4a7e94cd4365bf20c25a`**. `find_pending` returns `PMRun`s with no
downstream `ExecutionRun`, so the crashed run is *still pending*, and the next execution pass will
re-process all three intents through the S145 code - skipping MRVL as a completed exit and adopting
AMD and ABT through the `422 duplicate` -> `by_client_order_id` path.

**So the orphans will probably heal by themselves.** That is the finding, and it is also the
problem.

**The insight.** The self-heal is **single-shot and unrepeatable**. The same pass that adopts the
orphans also writes the missing `ExecutionRun`, and that write is what removes the `PMRun` from
`find_pending` forever. If adoption succeeds for ABT and fails for AMD - a 404 on the by-client
lookup, a timeout caught by S145's new per-intent fault boundary, an order aged out at the broker -
the window still closes. The failure is *silent by construction*: the node that proves the crash
happened is the same node whose absence keeps the repair possible. A repair path whose availability
is destroyed by its own execution is not a repair path; it is a coincidence with good timing.

**Decision.** Ship a bounded one-shot repair script (S146) that finds orphaned broker orders by
empty `fill_attempt_chain` and adopts broker state through the *same* `write_fills` path the agent
uses, so both routes converge on one key and either can run second as a no-op. Explicitly **do not**
let the script write an `ExecutionRun`: forging the node whose absence is the evidence of the crash
would destroy the record to tidy the record.

**Ruled out.** *Doing nothing and letting the nightly run adopt them* - probably sufficient, but
single-shot, unprovable in advance, and it leaves the next crash-orphan with no path at all;
"probably worked" fails LAW-02. *Extending the monitor to adopt orphans during reconciliation* -
the right long-term home, and it would fix the position book too, but it moves order truth into the
reconciliation pass, which is the cascade-ordering change DL-71 option B already defers; do not
reorder the cascade while cleaning up after an outage. *Hardcoding the observed `accepted` status
into the repair* - the orders are queued market orders that fill at the next open, so the document
would be stale before the code ran; the script must read broker state at execution time.

**Found alongside, not fixed (worse than the orphans).** ⛔ **RETRACTED 2026-07-28 — every claim in
this paragraph is false.** It audited `Position` nodes on the raw `status` property instead of
`contracts.positions.is_active_position_node`, so it counted superseded and broker-absent nodes as
live. The correct audit found **one active node per held ticker, every quantity matching the
broker**. Kept verbatim because the retraction is the lesson; see DL-73 below for the full account.
The false text follows. ~~The position book has diverged badly from
the broker: AMD carries three `open` Position nodes totalling **111 shares against 55 held**
(`broker-reconciled:AMD` 19, `broker:AMD:37:53978` 37, `broker:AMD:55:53127` 55); MRVL is **held
nowhere at the broker** yet has two `open` Positions of 44; ABT 98 vs 96; SCHW 98 vs 196. And
`exit:e67227ec57fa1e46:MRVL:sell` still reads `status='pending'` while `broker_status='filled'` and
its realized PnL is booked. These are monitor-reconciliation defects and they strengthen the case
for DL-71 option B rather than for widening S146.~~

**Unrelated bug found while probing.** `orchestration/packs/trading_vault_probes.py`
`_alpaca_account_request` falls back to `ALPACA_ENDPOINT` and then appends `/v2/account`. The
documented value in `.env.example` (and the live `.env`) already ends in `/v2`, so the Alpaca
credential probe requests `/v2/v2/account` and 404s whenever `EXECUTION_ALPACA_BASE_URL` is unset.
The execution agent is unaffected - it reads `EXECUTION_ALPACA_BASE_URL` with its own default. This
is a DL-36 credential-probe defect; file it, do not fold it into S146.

**Resolved 2026-07-29 (S146, 0.80.03, merged `7b06662`).** `scripts/repair_orphan_fills.py` shipped
dry-run-by-default, `--since`-bounded, writing through the agent's own `write_fills` path, and
**never** forging an `ExecutionRun`. Proven on production in three passes: dry-run
`would_record=4`, apply `recorded=4`, second apply `recorded=0 already_recorded=48` — idempotence
demonstrated rather than argued. `scripts/audit_broker_graph.py` shipped alongside it, so the
condition is now *detectable on demand*, which is the part that actually answers this entry's
title: the repair is repeatable and its precondition is observable, so it no longer depends on the
crash evidence surviving. The AMD/ABT orphans this entry was written about **did** self-heal on
`:s145` exactly as predicted — they are absent from the post-S145 audit. The four orphans the
script actually repaired were older ones nobody knew about (CSCO 88, AMD 19, HPE 229, MRVL 44),
which is the vindication of not relying on the single-shot window. The `/v2/v2/account` probe
defect was fixed in the same sprint: `_alpaca_broker_api_base_url` appends `/v2` only when absent.

---

## DL-73 - Broker reconciliation mints a new Position per (qty, basis) and never closes the old · status: RETRACTED (2026-07-28 — the defect does not exist; see the retraction at the end of this entry)

**Trigger.** The 2026-07-28 resumed run on fleet `:s145` - fired to prove the S145 exit-replay fix.
It did prove it (7/7 stages, see DL-71), and in passing it made the position book **worse**:
`Position` node count went **21 -> 23 in a single reconciliation**.

**Mechanism.** `agents/monitor/reconcile.py:108` keys the node
`broker:{ticker}:{quantity}:{avg_entry_cents}`, and `_matching_position` (lines 91-99) requires
**both** `quantity` and `opened_price_cents` to match a holding exactly. Any change - a fill, a
partial sell, a second buy moving the average - fails the match and mints a **new** `Position`,
while the previous node stays `status="open"`. **Nothing ever closes it.**

**Observed this run.** SCHW went 98 -> 196 at the broker, producing `broker:SCHW:196:10222`
alongside the still-open `broker:SCHW:98:10177` - **294 graph shares against 196 held**. ABT went
98 -> 96, producing `broker:ABT:96:10437` alongside `broker:ABT:98:10078` - **194 against 96**.
Standing damage from earlier runs: AMD carries **three** open Positions (19 + 37 + 55 = **111
against 55 held**); MRVL carries **two** open 44s while the broker holds **none at all**.

**Why it matters.** ADR-0016 has the analyst score scanner survivors **union open held positions**.
Phantom positions are `open`, so the analyst scores them, the PM can size a full exit against one,
and execution builds an exit key from it. That is precisely the chain that produced DL-71 - an exit
authored for a position that did not exist. This is not a divergence to be reconciled once; it is a
**generator** of divergence, and it grows by construction every time a holding changes. S146's
orphan-Fill repair does not touch it.

**Ruled out.** *Deleting the stale nodes* - append-only store (LAW-02); supersession/closure is the
shape here, following the S126 `RESUMES` precedent, not deletion. *Keying on ticker alone* - throws
away the entry basis that realized PnL resolves against (S136), which would trade a visible defect
for a silent one. *Treating it as stale data to be hand-corrected* - the correction would be undone
by the next holding change.

**Consequence for sequencing.** This makes DL-71 option B **non-optional rather than the natural
successor**: reconciling the book before the analyst decides is worth little while reconciliation
is itself the thing manufacturing the phantoms. Option B should absorb this, or precede it.

---

### CORRECTION - the consequence claim was inferred, then tested, and is weaker than written (2026-07-28)

The entry above asserted that the phantom positions "get scored, sized, and turned into exit keys -
the exact chain that produced DL-71". That was **inference from the node counts, not observation**.
A full fresh cascade (`confirm-s145-20260728`, fleet `:s145`, 7/7 stages) was then run specifically
to confirm it, and it did **not** reproduce that consequence:

- The analyst scored **9 tickers, one per ticker** - not one per `Position` node. AMD has three open
  nodes (19 / 37 / 55) and was scored **once**.
- The PM approved `AMD sell qty=55` - the **true broker holding**, not the 111 the three nodes sum
  to. Sizing was correct.
- MRVL was excluded from scoring entirely, so no exit was authored against the stock the broker no
  longer holds.
- Execution submitted 1 order and created **no duplicate**: AMD still shows exactly one live sell
  (`d040c762…`, qty 55). No oversell.

**What stands.** The accumulation is real and confirmed: **23 `Position` nodes for 8 actual broker
holdings** - BAC open at 171 *and* 338 *and* 503, USB at 160/320/478, WFC at 116/233/348, AMD at
19/37/55, plus SCHW, ABT and MRVL doubled. Nothing closes the superseded nodes. The `broker_absent`
marking that ought to isolate them is applied **inconsistently**: `broker-reconciled:MRVL` and
`broker:ABT:98:10078` carry `broker_absent=True`, but `broker:MRVL:44:22621` - 44 shares of a stock
held **nowhere** at the broker - does not.

**What does not stand.** That the phantoms currently drive sizing or exit-key construction. Some
per-ticker selection upstream is picking one position per ticker and picking the right one. That
path was not identified, and **that is the actual open question** - the correctness is currently
unexplained, therefore unguarded, and nothing tests it.

**Revised severity.** Not "DL-71's chain, live" - DL-71 happened, but this run did not reproduce it.
It is an **unbounded junk-accumulation defect with an unexplained mitigation**, which is a different
and lower-urgency problem. DL-71 option B remains the right owner; the correction is that it is not
firefighting. **Also worth noting the opposite result:** the same reconciliation *fixed* something -
`broker:SCHW:196:10222` matched the real holding, so `_broker_quantity_matches` finally passed and
execution placed SCHW's missing protective stop (`stop:b56b2d2f124326d3:SCHW`, sell stop qty=196,
2026-07-28T06:55:22Z), closing the item S145 left as "verify, do not fix".

**Method note (LAW-02).** The original entry was written from a node-count delta and a code read,
and stated a consequence it had not observed. The run cost ~15 minutes and refuted half of it. A
count plus a plausible mechanism is a hypothesis, not a finding - this is DL-70's thesis landing on
the design log itself.

---

### RETRACTED IN FULL - the defect does not exist (2026-07-28, same day)

**DL-73 is wrong. Both the mechanism and the consequence. It should not have been written.**

I audited `Position` nodes by filtering on `status == "open"` and concluded that reconciliation
mints nodes and never closes them. `status` is **not** the active-position predicate. The real one
is `contracts/positions.py::is_active_position_node`, which excludes any node carrying
`broker_absent` **or `broker_superseded_by`** - and
`agents/monitor/reconcile.py::reconcile_positions_from_latest_snapshot` already calls
`_mark_superseded` for every non-matching candidate (line 48-50) and `_mark_absent` for every
ticker absent from the snapshot (line 51-54). Supersession was built all along; `status` stays
`"open"` deliberately, because this is an append-only store and closure is recorded as a **separate
fact**, not by mutating the original node.

Re-audited with the correct predicate:

```text
total Position nodes = 23      ACTIVE by is_active_position_node = 9
OK ABT  1 node  96 vs 96       OK MRVL  (absent, correctly)
OK AMD  1 node  55 vs 55       OK PYPL  1 node 175 vs 175
OK BAC  1 node 503 vs 503      OK SCHW  1 node 196 vs 196
OK CSCO 1 node 177 vs 177      OK USB   1 node 478 vs 478
OK HPE  1 node 229 vs 229      OK WFC   1 node 348 vs 348
```

**One active position per held ticker, every quantity matching the broker exactly.** The 14
"phantoms" are a correct supersession chain - `BAC 171 -> 338 -> 503`, `USB 160 -> 320 -> 478`,
`WFC 116 -> 233 -> 348`, `AMD broker-reconciled -> 37 -> 55` - plus two correctly `broker_absent`
(MRVL, `ABT:98`). That is the history the append-only store exists to keep.

**This also answers the "unexplained mitigation".** There was no mystery: the PM sized `AMD sell
qty=55` correctly because `is_active_position_node` filters superseded nodes, exactly as designed
and tested. I invented a puzzle out of my own measurement error and then proposed a sprint to solve
it.

**Two further claims from the same audit, also withdrawn.** *"3 fabricated rejections"* -
`agents/execution/domain/orders.py::rejected_broker_fill` sets `broker_order_id="rejected:{key}"`
**by design**, as the durable record of a submission refused before it reached the broker, with
`reason` carrying the cause (all three read `HTTP Error 403: Forbidden`). That is DL-57 working, not
a lie. *"`canceled` recorded as `rejected`"* - `BrokerStatus` is a deliberate four-value contract
(`filled|partial|rejected|pending`) and `fill_from_order` preserves the broker's raw word in
`reason`; the information is modelled coarsely, not lost.

**What actually survived the audit** (carried into the S146 packet):

1. **ABT holds 96 shares (~$10k) with no protective stop.** Its last stop attempt was refused
   `HTTP Error 403: Forbidden`; no `BrokerStopOrder` node was written, so retry is *not* blocked -
   yet the 2026-07-28 run placed SCHW's stop and still skipped ABT. **Cause not established.** This
   is real, it is capital, and it is the one item worth a sprint.
2. **4 filled broker orders carry no `Fill` node** - `pm-run-f1f38e5c…` AMD 19 / HPE 229 / MRVL 44
   and `pm-run-6f34914d…` CSCO 88, all `status=filled`. A genuine lineage gap, and the reason those
   four `broker-reconciled:*` Positions had to be invented from a snapshot.
3. **`orchestration/packs/trading_vault_probes.py:154`** builds `/v2/v2/account` whenever
   `EXECUTION_ALPACA_BASE_URL` is unset and `ALPACA_ENDPOINT` holds its documented `.env.example`
   value. Code-verified, unaffected by the audit error.
4. **46 `Flag` nodes, 0 acknowledged** - operator action from the dashboard, not code.

**The lesson, which is the point of keeping this retraction rather than deleting the entry.** I
wrote a red-severity defect into `STATE.md` and the design log from a node count and a code read,
without running the system's own predicate over the data. DL-70's thesis is *stop asserting
presence, start planting violations* - and the check I should have planted was trivial: assert that
`is_active_position_node` returns one node per held ticker. It would have failed in seconds and
DL-73 would never have existed. **An audit that does not use the code's own definitions is not an
audit of the system; it is an audit of my assumptions about it.** Any future graph-vs-broker audit
must import the predicates from `contracts/` rather than re-deriving them from raw props.

---

## DL-74 - Trial: make the coding agent read the governing laws before writing code · status: DECIDED (trial concluded on S146; rule RETAINED on evidence and standard in every sprint handover since S147)

**Question.** The law book is authored, locked, and cited by tests - but nothing makes the coding
agent *read* it before implementing. Does law-first reading change what gets built, or is the law
book only a review artefact?

**The trial.** S146's handover (revision 2) opens with a **MUST RULE**: before any code, read
`agents/<name>/laws/laws.md` for every element to be modified, plus the cross-cutting umbrella laws
(`dependencies.md` for `DEP-BROKER`, `conventions.md`, `drift-register.md`), and fill a **Law
reading record** table *in the handover* before the first edit. One row per element: which clauses
bind, and **did reading them change the intended approach - yes and what, or no and why the
approach already complied.** An empty or retrospectively-written record makes the handback
incomplete by definition (DL-48).

**Why S146 is the right first subject.** It touches the execution agent's stop-placement path -
governed by `EXEC-NEV-*`, `EXEC-IDM-*`, `EXEC-FAIL-*` and `EXEC-PARAM-*` - plus a read-only
dependency on monitor's `Position` state (`MON-STA-*`). It also has a **known correct answer to a
tempting wrong move**: the DL-73 retraction proves reconciliation is lawful and must not be
"fixed". If law-first reading is worth anything, an agent that reads `MON-STA-*` should reach that
conclusion independently rather than on the sprint doc's say-so.

**What counts as a result.** Three outcomes are all informative and all must be reported honestly:
the record shows laws **changed** a decision (the rule earns its cost); the record shows **no
change** everywhere (the sprint spec was already law-compliant - cheap insurance, keep or drop on
cost); or the agent surfaces a **contradiction between a law and the spec**, which is the highest
value outcome available, because the spec is one sprint's opinion and the law is the constitution.

**Deliberately not measured yet.** Whether the rule slows the agent down materially, and whether it
scales to sprints touching six agents rather than two. One trial does not settle either.

**Ruled out.** *Making it a CI gate* - unenforceable, since reading is not observable in a diff;
the observable artefact is the record, and a record can be faked, which is why the rule demands
clause IDs and a yes/no-with-reason rather than a tick. *Quoting the relevant clauses into the
sprint doc instead* - that is what the planning agent already does implicitly, and it is exactly
the failure mode under test: it keeps the law book as a thing the planner has read and the coder
has not. *Applying it to every sprint immediately* - this is a trial; adopt or drop it on evidence.

---

## DL-75 - S146 diagnosis: unprotected ABT is a broker refusal, not a graph skip · status: ACCEPTED

**Question.** The S146 handover suspected ABT was skipped because a broker-reconciled `Position`
could fail threshold discovery or active-position filtering. Is the exposed position caused by graph
state, or by the broker refusing the stop?

**Decision.** Treat ABT as an active position that reaches the stop-submission rail. The production
pre-audit found `Position key=broker:ABT:96:10437`, `stop_pct=0.05`, one active node, graph quantity
96 matching the broker, and `open_position_stop_thresholds` returning the ABT threshold. The live
retry submitted the same stop idempotency key and Alpaca rejected it with HTTP 403
`potential wash trade detected. use complex orders` because an opposite-side order already exists.
The fix therefore makes the refusal durable and retryable instead of rewriting reconciliation.

**Implementation consequence.** Execution owns a broker-stop threshold planner that reuses
`contracts.positions` predicates, applies a bounded execution fallback only when an active position
is missing `stop_pct`, and records `UnprotectedPosition` faults when protection is absent or refused.
Repeated stop refusals append a new `Fill` attempt while preserving the broker idempotency key.

**Ruled out.** *Changing `contracts.positions` active semantics* - DL-73 proved the predicate is the
source of truth and the ABT node already passes it. *Retiring or replacing broker-reconciled
positions* - that would reintroduce the invisibility ADR-0015 exists to prevent. *Recording a
`BrokerStopOrder` for a refused submission* - ADR-0015 makes the stop order a fact about broker
state, and a 403 refusal never creates a live broker stop.

---

## DL-76 - A flat price tolerance is not a neutral parameter; it silently picks winners · status: PARTLY (challenger SHIPPED S149 `eee68d1`/0.83.00, off by default; promotion still pending)

**Trigger.** S148 shipped ADR-0018's order-price tolerance as a flat **50 bps**. Before merging, I
measured that number against 60 sessions of real overnight gaps (Alpaca daily bars, 2026-05-01
onward) for the nine held names plus AMD and MRVL, computing **directional** refusal - a buy only
fails if the price gaps *up* through the band, so a two-sided rate would overstate it by roughly
double.

**What the measurement says.** Blended, 50 bps refuses **35 % of buys and 23 % of sells**. That part
is ADR-0018 working as designed. The finding is the **distribution**:

| Ticker | Median overnight gap | Buys refused @ 50 bps |
| --- | --- | --- |
| SCHW | 42 bps | 25 % |
| USB | 47 bps | 30 % |
| WFC | 47 bps | 37 % |
| HPE | 132 bps | 45 % |
| AMD | 251 bps | 52 % |
| MRVL | 318 bps | 48 % |

Tolerance sweep, blended buy/sell: 25 bps -> 40 %, **50 bps -> 29 %**, 100 bps -> 18 %,
200 bps -> 9 %, 500 bps -> 2 %.

**The insight.** 50 bps is *one* median gap for SCHW and *one fifth* of one for MRVL. A single
number therefore encodes two completely different policies depending on which ticker it lands on -
and nobody chose that. The flat band quietly decides that the system trades the low-volatility book
roughly normally and goes nearly silent on AMD/MRVL/HPE.

**Why scaling is about edge, not volatility.** A tolerance says *how far from my decided price I
will still trade*. On a name whose typical move is 3 %, refusing a 0.5 % adverse gap discards trades
whose edge dwarfs the slippage; on a name whose typical move is 0.5 %, the same gap eats the entire
edge. Volatility is the available proxy for edge size, so the band should scale with it. `atr_pct`
already exists per ticker and already crosses the analyst -> PM boundary inside
`Recommendation.quant_metrics`, so the input is free; only PM -> execution needs a field.

**Decision: make it a measured challenger, not a correction (ADR-0013).** Packaged as
[S149](sprints/sprint-149-volatility-scaled-tolerance.md), shipping **off by default**, with the
counterfactual tolerance recorded on every order so the comparison is judged on evidence rather than
argued. Promotion is an operator config flip, never automatic.

**Ruled out.** *Widening the flat band to ~150 bps* - one number, no plumbing, drops fall to ~11 %;
rejected as the primary answer because it does not fix the **shape** (SCHW would get three median
gaps, MRVL half of one), but retained as the baseline the challenger must beat. *Keeping the flat
band and simply not trading high-gap names after close* - genuinely defensible, and what the flat
band already does implicitly; rejected only as an **unexamined default**, and if the measurement
says the flat band wins, that is a real result. *Scaling by realized overnight gap instead of ATR* -
more directly on target, deferred because nothing computes that statistic today. *Letting the PM
decide the tolerance* - rejected on the `EXEC-IDN-01` line: the PM carries the input, execution owns
the band. *Auto-promotion on N winning runs* - rejected; ADR-0013 requires gated promotion.

**Found alongside, not fixed (arguably larger).** `suggested_stop_pct` is **not per-ticker at all**:
`agents/analyst/domain/recommend.py:172` sets it to `regime.base_stop_loss_pct` for every buy. So
every position carries an identically-sized stop regardless of volatility - SCHW at a 42 bps median
gap and MRVL at 318 bps get the same floor. That is the same flat-band defect one layer over, and it
governs **risk** rather than execution price, which makes it the more consequential of the two.
Recorded here deliberately rather than folded into S149.

---

## DL-77 - The same 5 % stop is 2.4 ATRs for BAC and 0.6 for MRVL · status: PARTLY (challenger SHIPPED S150 `ca97797`/0.84.00, off by default; promotion still pending)

**Trigger.** DL-76 recorded, as a finding left unfixed, that `suggested_stop_pct` is
`regime.base_stop_loss_pct` for every buy - one global number, currently 5 %, for the whole book. I
measured what that actually means before packaging anything.

**The measurement** (Alpaca daily bars, ~65 sessions from 2026-04-01; 14-day ATR as a percent of
price; "touched" = the day's low fell more than the stop width below the prior close):

| Ticker | ATR % | Flat 5 % stop touched | 2 x ATR stop touched | 2 x ATR width |
| --- | --- | --- | --- | --- |
| BAC | 2.1 % | 0.0 % | 0.0 % | 4.1 % |
| USB | 2.1 % | 0.0 % | 0.0 % | 4.1 % |
| SCHW | 2.5 % | 1.5 % | 1.5 % | 4.9 % |
| CSCO | 3.2 % | 6.1 % | 1.5 % | 6.4 % |
| HPE | 5.5 % | **19.7 %** | 0.0 % | 11.0 % |
| AMD | 6.4 % | **36.4 %** | 1.5 % | 12.8 % |
| MRVL | 8.5 % | **39.4 %** | 1.5 % | 17.1 % |

**The insight.** A 5 % stop on MRVL is **0.6 ATRs - inside a single day's normal range** - and is
touched on ~39 % of days by ordinary noise. That is not a protective floor; it is a near-certainty
that the position exits within days regardless of thesis. The same 5 % on BAC is **2.4 ATRs** and is
touched on 0 % of days. So "5 % stop" is not one policy at all: it is a different risk appetite per
ticker, chosen by accident rather than decided. A 2 x ATR stop equalises the touch rate across the
book at 0-3 %, with the *width* ranging 4.1 % -> 17.1 %, which is what holding risk constant actually
looks like.

**This is DL-76's defect one layer over, and it governs risk rather than execution price.** DL-76
was about how far from a decided price we will still trade; this is about how far a position may
fall before it is closed. The second is the more consequential of the two.

**An honest check that did not support the story.** The tempting narrative is that MRVL's 07-27
forced stop (-$1,330.12, the ADR-0018 trigger) was a noise stop-out caused by exactly this defect.
**It was not.** MRVL closed 189.28 / 174.36 / 163.39 on 07-27/28/29 - **16.6 % below the $195.98
exit**. That stop was correct and it saved money. The statistical finding stands without the
anecdote; recording the failed check because a convenient story that survives testing is worth more
than one never tested.

**The coupling that makes this dangerous to fix naively.** `gate_report.py:125` computes
`ratio = target_pct / stop_pct` and gates approval on it, while `suggested_target_pct` is *also* the
flat `regime.base_take_profit_pct`. Widen the stop for volatile names without widening the target and
the ratio collapses exactly where the stop widened most - **AMD, MRVL and HPE silently stop passing
the reward-risk gate and stop being traded at all**, with no error, no fault and no dropped decision.
Stop and target must scale together, and the RR verdict must be provably mode-invariant.

**Decision: a measured challenger, off by default (ADR-0013).** Packaged as
[S150](sprints/sprint-150-volatility-scaled-stops.md), consistent with S149's shape - mode selector,
counterfactual recorded, promotion an operator config flip on evidence. Being off by default matters
more here than for the tolerance: this is a **risk** parameter, and a stop that changes width without
evidence is not an improvement, it is a different bet.

**Ruled out.** *Raising the flat stop to 8 %* (the current `le` bound) - makes BAC's stop 3.8 ATRs,
decorative, while MRVL's is still under 1 ATR; moves the problem without changing the shape and
raises the risk cap for names that never needed it. *Scaling by realized downside gap rather than
ATR* - more directly on target, deferred because nothing computes it. *Putting the scaling in the PM
rather than the analyst* - defensible on "risk disposes", left as a live question for the law-first
pass to settle rather than assumed. *Letting the monitor re-price stops as volatility drifts* -
mutating live risk instruments on a schedule is a much larger safety question than choosing a stop at
entry. *Doing nothing* - no measured loss is yet attributable to the flat band, and MRVL's stop was
correct; rejected because the exposure is structural and measurable **in advance**, and waiting for
it to cost money is how the ADR-0018 gap went unnoticed for months.

---

## DL-78 - After S150, the risk cap binds the volatile names, not the stop formula · status: CLOSED by [ADR-0019](decisions/0019-risk-cap-binds-position-size-not-stop-distance.md) (2026-08-01) — the cap holds; position size gives

**Trigger.** Verifying S150 at handback. The sprint shipped exactly as specified - `k=2.0`, floor
2.5 %, ceiling **8 %**, with the ceiling bounded `le=0.08` so a scaled stop can never exceed the
declared PRD/regime maximum risk. That is the correct behaviour. I then measured what the shipped
configuration actually delivers, rather than what the formula wants.

| Ticker | ATR % | 2 x ATR wants | Shipped (capped) | ATRs | Flat 5 % touched | Shipped touched |
| --- | --- | --- | --- | --- | --- | --- |
| BAC / USB | 2.1 % | 4.1 % | 4.1 % | 2.00x | 0.0 % | 0.0 % |
| SCHW | 2.5 % | 4.9 % | 4.9 % | 2.00x | 1.5 % | 1.5 % |
| CSCO | 3.2 % | 6.4 % | 6.4 % | 2.00x | 6.1 % | **1.5 %** |
| HPE | 5.5 % | 11.0 % | 7.7 % | 1.40x | 19.7 % | **6.1 %** |
| AMD | 6.4 % | 12.8 % | 8.0 % | 1.25x | 36.4 % | **10.6 %** |
| MRVL | 8.5 % | 17.1 % | **8.0 %** | **0.94x** | 39.4 % | **18.2 %** |

**The finding.** The challenger delivers most of what DL-77 promised - CSCO, HPE and AMD improve
sharply - but **MRVL only halves, from 39 % to 18 %, and remains under one ATR**. For the most
volatile names the binding constraint is no longer the scaling formula; it is the **8 % risk cap**.
2 x ATR wants 17.1 % for MRVL and the ceiling clamps it to 8 %.

**Why this matters at promotion time.** A comparison report will show the challenger failing to fix
the very name that motivated the work. That reads as "the scaling underperformed", and it would be
the wrong conclusion: the scaling hit a wall that is not its to move. Recording it here so the
promotion decision is made against the complete picture rather than the report alone.

**Two ways past it, neither belonging to S150.**

- **Raise the cap.** `base_stop_loss_pct` is bounded `le=0.08` today. Widening it is a decision about
  the maximum risk the system may take per position - a PRD/ADR question, not a tuning knob, and it
  should not be made by an experiment.
- **Size positions by volatility instead (the more promising).** If MRVL needs a ~17 % stop to sit
  outside ordinary noise, the answer may be to hold proportionally *less* MRVL so that a 17 % move is
  within the same dollar-risk budget as a 4 % move on BAC. That keeps the cap intact and attacks the
  problem from the other side: constant *dollar* risk rather than constant *percentage* risk. It is
  the classic volatility-scaled sizing argument and it is the natural successor to S149/S150.

**Not yet decided.** Which of the two (or neither) is right depends on evidence S150 has not produced
yet, because the challenger ships off. Sequence: let the flat champion and the recorded counterfactual
accumulate, then choose. **Do not raise the risk cap to make an experiment look better.**

**Ruled out already.** *Removing the ceiling so the formula runs free* - it would let a scaled stop
exceed the declared risk cap silently, which is exactly the safety rail the sprint was right to build.
*Treating 18.2 % as good enough for MRVL* - it is a halving and real progress, but a stop under one
ATR is still inside the noise band, so the structural problem is reduced, not solved.

---

## DL-79 - A cleanup step outranked the run's foundation: the drop sweep stalled the fleet · status: ACCEPTED (fix packaged as S151)

**Trigger.** `sched-2026-07-30` - S148's first night on the fleet - reached **2/8 stages** and
stopped. `ACCEPTANCE FAIL`, six stages `NOT REACHED`. Diagnosed 2026-07-31.

**Everything that normally explains a stall was healthy**, and it is worth recording so the next
diagnosis does not re-walk it: `dispatcher-cron-29757510` `Succeeded` 22:30:00-22:30:25 UTC and wrote
`run-request:sched-2026-07-30`; all 13 Container Apps KEDA-activated at 22:30:21, pulled `:s148`, ran
the full window and deactivated cleanly at 00:34:50; master fetched every Key Vault secret at HTTP
200 with **zero** `Escalation` nodes; provider served 100/100 tickers, 4,200 bars, 1,920 headlines,
no `*_degraded` notes. The fleet was fine. The code was not.

**Root cause - two vocabularies in one property.** `BrokerStatus` is a four-value Literal
(`filled|partial|rejected|pending`, `agents/execution/alpaca_orders.py:22`); Alpaca's raw `canceled`
is normalised to `status="rejected"` with the raw string kept in `reason`. Reconciliation writes the
**normalised** value (`reconciliation_store.py:70` -> `broker_status="rejected"`). S148's drop sweep
writes the **raw reason** into the same property (`drop_sweep_records.py:42` -> `"canceled"`). The
append-only store permits re-writing the same value and refuses a different one
(`kernel/graph_support.py:70`), so it refused - correctly.

```text
ValueError: property 'broker_status' cannot be overwritten
  agents/execution/drop_sweep.py:43 -> drop_sweep_records.py:38 -> kernel/graph_support.py:71
```

Ten `Fill` nodes from the 07-22 and 07-23 cancelled runs sit in exactly that state
(`broker_status=rejected`, `drop_reason=None`) and each is a landmine the sweep steps on.

**The store is not the bug - it is the only component that behaved well.** This is the second time a
caller has fought it (S145: `property 'price_cents' cannot be overwritten`) and both times the caller
was wrong. Recorded here because the tempting fix - an overwrite escape hatch for "status-like"
properties - would destroy the guarantee that what we believed at each moment stays recoverable.

**Why the blast radius was 5,762 faults and not one.** The sweep runs *inside* the same fault
boundary as `reconcile_run_start` and *before* it (`agents/execution/poll.py:142-145`). So the
exception cost the `BrokerPositionSnapshot`; the missing snapshot left `position_sync` incomplete;
S147 correctly gates the analyst on the sync, so stages 3-8 waited on a stage that could never
finish. The work item stayed pending, `work_loop` retried it every ~1.3 s from 22:30:38 to 00:35:20
UTC, and each attempt appended an identical `Fault` - **5,762 rows, one cause**. Only the *cancel*
path inside `sweep_unfilled_orders` has per-order containment; the resolved-drop path (line 43) and
`mark_execution_runs` (line 62) have none.

**The lesson, which outlives the specific defect.** *A cleanup of yesterday's leftovers may never
outrank the foundation it runs beside.* Nothing downstream depends on the sweep; everything depends
on the snapshot. A failed sweep should cost a `Fault` and a night of stale resting orders - the
pre-S148 world the system ran in for months - never a stalled fleet. This is DL-71's per-item
containment lesson, which S145 already paid for once, arriving in a new module.

**Why the tests missed it.** Every drop-sweep fixture builds a fresh `Fill` with no prior
`broker_status`, so the first write always succeeds. The collision needs *history*. That is the
S143/S144 trailing-indicator lesson one level down: a check built only from what the code has been
observed to do cannot cover state the code has never been run against. Two tests
(`test_drop_sweep.py:41`, `test_drop_sweep_edges.py:47-48`) actively assert the defective behaviour -
correct tests of a wrong spec.

**What held.** Nine positions, nine resting `gtc` broker stops, verified at Alpaca after the outage:
**none cancelled, none missing.** The ADR-0015 §3 floor survived a two-hour fault storm inside the
agent that owns it. That is the reason a lost session is survivable rather than dangerous, and it is
the strongest available evidence for the broker-native stop decision.

**Cost.** One session: no analyst, PM, execution or monitor evaluation. Modest in practice - the
07-29 run approved 0 (nine `hold_recommendation` skips), so the book was static anyway.

**Decided.** Fix packaged as [S151](sprints/sprint-151-drop-sweep-append-safe.md): drop evidence stops
writing `broker_status` entirely and lives on `drop_reason`/`dropped_at` plus the append-only
`BrokerOrderStatus` node that the sweep *already* writes correctly on the next line; per-order
containment in the sweep; and the sweep gets its own fault boundary so a failure can never cost the
snapshot. Version is a PATCH (`0.84.01`) - no new capability, the sweep already exists.

**Ruled out.** *Relax the append-only guard* - destroys the evidence model (above). *Write
`broker_status` only when absent*, copying the `reconciliation_store.py:68` precedent - fixes the
crash but leaves two vocabularies in one property, the same broker fact under two names decided by
timing; kept as the fallback if the primary shape proves unworkable. *Widen the `BrokerStatus`
Literal to include `canceled`/`expired`* - arguably the right model, but a contract change rippling
through the adapter, reconciler and every consumer: MINOR-sized redesign inside a PATCH-sized outage
fix, worth reconsidering in a law-amendment cycle. *Only reorder the sweep after the snapshot* -
the run would survive but the sweep would be permanently broken and silently drop nothing, a green
run that does not do its job; kept as additional hardening, not as the fix. *Roll back to `:s147`
and abandon the sweep* - valid as a one-night contingency, rejected as a fix: ADR-0018 addresses the
largest measured cost in the system (≈ -$2,850 across two exits).

**Left open, deliberately not in S151.** General **fault de-duplication / retry backoff** for a
work item that fails deterministically. 5,762 rows for one cause is a real problem, but it is a
kernel/`work_loop` concern affecting every agent; S151 makes it impossible *on this path* by
construction (a completed snapshot ends the loop) and the general version needs its own sprint.

**First measurement warning.** The ten legacy fills will all be recorded on the first corrected
sweep, so expect **~10 drops, not ~3**. That number is not the ADR-0018 drop rate; the real
per-session rate is only measurable from the second clean run onward.

---

## DL-80 · Five deployed agents have never run, and the LLM veto has never vetoed · status: OPEN (operator escalated 2026-07-31)

**The finding.** A live-graph inventory taken while enabling S144 shows **zero** nodes for
`DeliberationRun`, `ForecasterRun`, `TrainingExample`, `Dataset`, `Predictor`,
`ShadowPrediction`, `PredictorPromotion`, `Experiment`, `Escalation` and `RemediationPlan`.
The core pipeline is healthy — 22 each of `RunRequest` → `MarketData` → `ScanRun` → `AnalystRun`
→ `PMRun` → `ExecutionRun`, 44 `MonitorRun`, 22 `Snapshot` — so this is not an outage. It is a
capability that was built, deployed, described as live, and never wired to anything.

**The LLM veto has never run in production. Not once.** All 25 `LLMCall` nodes carry a single
edge shape, `CommandAudit -PRODUCED_BY-> LLMCall`: they are operator-chat calls (S125), and the
newest is **2026-07-15**, sixteen days before this was found. `agents/execution/poll.py::_drop_vetoed`
is *documented* fail-open — "No DeliberationRun (the veto stage did not run) → the full set
executes, so an absent or failed review never blocks trading." That design is defensible; what is
not is that **the fail-open branch is the only branch that has ever executed.** Every order this
system has submitted went to the broker unvetoed.

**Root cause — two different gaps wearing one symptom.**

1. *Deliberation is not an agent.* It lives in `orchestration/veto.py` and is wired only into
   `orchestration/local_pipeline.py`, the local/manual runner. The deployed fleet runs per-agent
   graph-pull entrypoints, and **no entrypoint calls `veto.find_pending`**. There is no image, no
   app, and no work source for it.
2. *Five agents are served, not pulled.* Only **seven** of the thirteen deployed apps have a
   graph-pull work loop (provider, scanner, analyst, portfolio_manager, execution, monitor,
   reporter). `forecaster`, `curator`, `operator`, `researcher` and `supervisor` have entrypoints
   with **no `find_pending` loop** — they serve Service Bus request/reply (proven in S102). Nothing
   in the nightly pipeline ever sends them a request, so they wake, idle, and scale back to zero.

**Why no gate caught it.** `trading_acceptance.py`, `trading_boundaries.py` and
`trading_observatory.py` contain **no reference to deliberation or the forecaster**. Every run has
scored `ACCEPTANCE PASS` with both absent. This is the DL-57 / DL-59 pattern a third time: a gate
reports green on what it does not examine, and "the stage did not run" is indistinguishable from
"the stage ran and found nothing". The S144 lesson generalises past the vocabulary guard — *a
capability with no check that can fail is not a capability, it is an intention.*

**Collateral.** DL-63 (0.78.00) moved the default model to `claude-opus-5` and priced it into the
ledger; since no fleet LLM call has happened since 07-15, **that upgrade has never executed in
production** — the live calls are all `claude-sonnet-4-6`. STATE's caveat that DL-63 proved only
the script-side adapter was true but understated: the deployed path is not merely unproven, it is
unreached. Likewise DL-41/DL-42's compiled judge and challenger are live champions of a stage that
does not run, and the DL-09/curator training loop has no source data because the curator has never
been invoked.

**The decision this forces (not yet made).** Deliberation must either become a real fleet
participant — its own image and graph-pull work source keyed on unvetoed `PMRun` nodes, which is
the shape every other pipeline agent already uses — or be honestly retired from the architecture
and from STATE. The same question applies to the forecaster: an advisory input nothing requests is
not advisory, it is dead code with a container bill. **Whichever way it goes, the acceptance gate
must gain a check that fails when a declared stage produces nothing**, or the next capability will
rot the same way with the same green verdict.

**Do not read this as "the trading path is broken."** It is not: the seven-agent pipeline works,
reconciles, places stops and scores acceptance honestly on what it does cover. The exposure is that
the risk *review* layer described in the PRD and STATE is absent, and nothing said so.

**Operator correction, 2026-07-31 — the design was right; the implementation shape is what stranded
it.** The intended design, confirmed by the operator and recorded at the time in
[sprint-109](sprints/sprint-109-heterogeneous-deliberation-models.md), is that the Manager activates
**three copies of the researcher agent** — Manager, Proponent, Opponent — which receive *identical*
evidence (external feeds plus the quant research done inside the app), deliberate over rounds,
narrow to the major points of influence, and return recommendations the Manager rules on with its
own verdict. The narrative of that conversation is a first-class output: the point of exposure for
what was actually argued.

Almost all of that **is** built, and faithfully: `kernel/deliberation.py` runs bounded rounds
(`max_rounds=3`, Defender argues then Challenger rebuts, each seeing the running transcript), the
Judge rules afterwards with a verdict plus rationale, `build_veto_context` renders the full
provider→scanner→analyst→PM lineage including quant evidence, and every `Turn` (role, round, text)
is persisted on the `DeliberationRun` node. S109 additionally made the model per-role.

The single divergence is the one that matters: the roles were built as **system prompts inside a
kernel harness**, called from `orchestration/veto.py`, rather than as **three researcher-agent
instances**. Three agent instances would have been fleet-native by construction — agents get
images, identities, work sources and scheduling, and the master already activates them. A kernel
harness only runs where something calls it, and the only caller is the local pipeline. **The
shortcut is the root cause**: had the roles been agents, the stage would have been scheduled like
every other. This reframes the fix — it is not "wire deliberation into the fleet somehow", it is
"build the three researcher instances the design always called for", and the harness becomes the
reasoning core they share rather than the thing that runs.

**LAW-06 finding, same session — the embodiment decision was never recorded.** The operator
recalls deciding "ages ago" that, because the three debate roles are so similar, they would ship as
**one image with the role distributed**, and that **one researcher instance activates the other
two**. A search of `design-log.md`, every ADR, every sprint doc, both state archives, the
researcher's `mission.md` and its LOCKED `laws.md` finds **no trace of it**. What *is* recorded is
the debate's *structure* (S109: Defender/Challenger/Judge, per-role models) — never its
embodiment. Per LAW-06 a decision discussed but unrecorded is treated as not-yet-made, so this is
the second time in one investigation that the gap was not the thinking but the capture.

**And the name collides with a different agent.** The `researcher` that exists is the
parameter-improvement researcher — *"mine accumulated evidence for parameter and strategy
improvements and propose bounded, measurable changes into the human-review queue — never apply
them"* — owning `Experiment` and `ParamChange`, with LOCKED v1 laws. Debating a PM order is not
that mission. So "three copies of the researcher agent" resolves to one of two materially different
designs, and the choice is the operator's:

- **(a) Broaden the researcher.** One image, one agent identity, a `role` parameter selecting
  manager/proponent/opponent, and its mission + LOCKED laws amended to cover adversarial review of a
  proposed order. Cheapest in infrastructure, but it makes one agent responsible for two unrelated
  jobs and requires a law amendment on top of the five already owed (see S152).
- **(b) A new `deliberator` agent that reuses the pattern.** One image, three instances, role by
  parameter — exactly the shape the operator described — but its own identity, mission and laws,
  leaving the researcher's mission intact. Costs a new agent bundle; keeps both missions honest and
  is the better fit for `ops/agent-genesis.md`.

Either way the debate roles stay one image with a distributed role, and one instance activates the
other two, because that part is settled — it simply had never been written down.

---

## DL-81 · The marker never lands on the fills that motivated it: skip-before-mark on pre-existing state · status: RESOLVED (option 3 approved and executed 2026-08-01)

**Found in review of S154, after merge-quality was already established.** The sprint shipped exactly
what it specified and the gates are green; this is a consequence of *my* spec's ordering that is only
visible against production state, not a defect in the implementation.

S154 ships two things deliberately: **item 1** stops selecting fills whose `broker_status` is
terminal, and **item 2** records an unresolvable realized-PnL conclusion once via
`Fill.pnl_unresolved_at`. The spec argued for both on the grounds that item 1 alone would stop the
ABT fault *by accident of scheduling* while item 2 stops it *because the system recorded what it
concluded* — and that a silent skip is the DL-57 failure mode.

**The ordering defeats that argument for every fill that is already terminal.** The new guard sits
before the broker lookup and before `realized_pnl_props`, so a fill that already carries
`broker_status="filled"` is skipped before the marker can ever be written. Verified against the live
spine: **39 fills are already terminal**, and exactly **one** of them is a sell fill still needing a
PnL conclusion — `pm-run-927de0c7…:ABT:sell`, the 98-share exit filled at $101.35 on 2026-07-24 that
motivated the whole sprint. It will now be silently skipped forever: no fault (the win), and no
marker (the DL-57 shape, preserved in the one instance the marker existed for).

Marking is correct for every *future* unresolvable fill. The gap is bounded to the historical set.

**The road not taken, and why the decision is owed rather than taken.**

1. **Reorder so the marker is evaluated before the terminal skip** — rejected. It would re-open the
   full scan over all 39 settled fills on every run to serve one historical row, which is the exact
   cost the sprint exists to remove.
2. **Backfill the real PnL** by reconstructing which `Position` that exit closed — rejected for now.
   The key encodes no `position_ref` and there is no `EXECUTES` order; any reconstruction is
   inference, and on an append-only store a wrong number can never be withdrawn. Fabricating lineage
   to make a metric appear is the worst available outcome (S154 non-goals).
3. **One-time marker write** on that single node — **recommended.** `pnl_unresolved_at` is now a
   declared `Fill` property, the node does not carry it, so the write is append-safe by construction
   and idempotent thereafter. It converts a silent historical skip into a queryable known gap without
   asserting any PnL figure.

**Owed:** operator sign-off on option 3, because it is a write to the production graph and the
append-only spine makes it irreversible. Until then the state is recorded here and in `STATE.md`:
lifetime realized PnL is understated by exactly one trade, and the two attributed exits
(AMD −$3,515.60, MRVL −$1,330.12) are unaffected.

---

**RESOLVED 2026-08-01 — option 3 executed with operator approval, and proven.** The one-time marker
was written to `pm-run-927de0c7…:ABT:sell` **through an armed `GuardedGraphStore`** (the pack
base64-injected exactly as the fleet receives it), so the new declaration was validated on the real
write path rather than assumed: `pnl_unresolved_at = 2026-08-01T04:03:39.898023+00:00`.

**No PnL was asserted.** `realized_pnl_cents` remains `None`, `broker_status` remains `filled`, and
`quantity` remains 98 — the write added exactly one property and touched nothing else.

**Permanence proven, not assumed:** a second write with a *different* value was refused by the
append-only store — `ValueError: property 'pnl_unresolved_at' cannot be overwritten` — so the marker
cannot drift and the conclusion is now durable. Exactly **one** `Fill` carries the marker.

**One thing the audit surfaced and it is not a gap:** 12 further `side="sell"` fills carry no PnL,
but every one is a `stop:*` resting broker stop that has **not filled** (`broker_status` unset). No
realized PnL is due until they do, and `_needs_realized_pnl` correctly requires a broker status of
`filled`/`partial`. They are live protection, not unresolved history.

Lifetime realized PnL remains understated by exactly one trade, now **queryable** rather than silent.

---

## DL-82 · The four decisions owed were taken, under delegated authority · status: DECIDED (2026-08-01)

The operator reviewed the outstanding-debt survey, said of the *Decisions owed* section *"I do not
understand it enough to comment — do what is appropriate to the spirit and letter of this project"*,
and prioritised S152. Recording the four calls here so none is treated as not-yet-made (LAW-06), and
so a later reader can see the reasoning rather than only the outcome.

**1 · The 8 % risk cap vs. volatility-scaled stops → [ADR-0019](decisions/0019-risk-cap-binds-position-size-not-stop-distance.md).**
The cap is a capital-safety bound and does not move; **position size** shrinks so a correct stop fits
inside it. Raising the cap is the change that makes the challenger look better, which is exactly why
it is the wrong instrument — the repo already holds that safety/capital caps are ADR-only and never
experiments. Closes DL-78. **Consequence worth flagging: the S150 stop challenger cannot be fairly
promoted until the sizing change lands**, because any promotion report before then compares the
scaled stop against the clamp rather than against the flat champion.

**2 · Property enforcement for the other 51 labels → shadow first, declare second.** The guard
currently enforces properties for 2 of 71 labels; 49 of the remaining 51 resolve totally under the
static scan, so a pack *could* be generated today. Declining to, for now, on the project's own
evidence: S143/S144 established that a pack built from observed writes is a **trailing indicator**,
the guard is **fail-closed** and a raise lands inside the caller's fault boundary (the S148 stall
pattern), and **46 `add_edge` sites** remain unresolvable to the scan. Generating 49 more enforced
labels multiplies the surface on which a never-executed path can raise at 22:30 UTC, to protect
against a class of defect that has not yet occurred. **The sanctioned path is warn-only shadow mode**
— log what *would* have raised, observe for a bounded period, then promote the labels that came back
clean. That converts an open-ended static-analysis job into a bounded observation, and it is the same
instrument already recommended for the 46 blind edge sites, so the two should ship as one sprint.
*Ruled out:* declaring all 49 now (untested fail-closed surface); declaring none ever (leaves the
guard at 3 % of its labels indefinitely).

**3 · DL-46 option A, a deploy step in CI → stays deferred, and now with a named precondition.**
Auto-deploy on merge would remove the operator-approval gate that the deploy procedure deliberately
encodes. [DL-80](design-log.md) is the argument against removing it: five deployed agents and the LLM
veto rotted undetected precisely because *deployment succeeding* was never the same thing as *the
thing working*. **Precondition for revisiting: an acceptance check that fails when a declared stage
produces nothing** — already scoped as item 1 of S153. Until that exists, automating deploy would
automate the propagation of green-but-inert releases. Not rejected; sequenced behind S153.

**4 · DL-50, ADR-0007 still names DockerHub → amend, do not silently rewrite.** The pipeline has
shipped to GHCR since the container split. The fix is a proper amendment cycle with the supersession
recorded, exactly as S152 is establishing for agent laws — not an edit that makes the old text
disappear. Queued as a small chore; deliberately **not** folded into S152, whose scope table is
exhaustive by design and covers agent constitutions rather than ADRs.

**Sequencing note:** `chore-wsl2-dev-env` stays behind S152. Its `.gitattributes` LF renormalisation
touches nearly every text file, and S152 is a docs-heavy sprint — running them concurrently would
manufacture conflicts across the whole law book.

---

## DL-83 · The delegated agent stopped and reported a law contradiction instead of coding around it · status: RESOLVED (ADR-0020 + chore merged, 2026-08-01)

**The process worked, and that is the record worth keeping.** S153's delegated prompt said *"if a
law, an ADR, or the brief itself contradicts what you find, STOP and report it — a contradiction you
surface is a success, not a delay."* The coding agent did exactly that, **before editing a single
file**, and its recommendation (decide the ownership question first, then implement) was the right
sequencing. Worth noting because the cheap failure mode was available and not taken: it could have
invented `DeliberationLLMCall`, satisfied every gate, and shipped a silent hole.

**The contradiction.** S153 hands the deliberator an `ANTHROPIC_API_KEY` and makes an `LLMCall` node
a success factor. `OPR-IDN-01` said the operator *"is the sole LLM boundary"*; `OPR-IDN-02` said it
exclusively writes `CommandAudit`, `Intent`, `LLMCall`, and `contracts/operator.py` encoded it.

**On verification the conflict was sharper than reported** — two things the agent had not surfaced:

1. **`OPR-IDN-02` is 🟩 green**, pinned by `test_operator_boundary_claims_graph_labels_once`. S153
   would have broken a *proven* clause, not merely an asserted one.
2. **`LLMCall` is already a cost ledger with two consumers** — `surfaces/dashboard/llm_costs.py` and
   the `/audit-costs` skill both enumerate it, and the skill names `agents/operator/store.py` as
   *the* writer. The deliberator is about to become the system's **largest** LLM consumer.

That second fact is what decided it. The tempting fix — a deliberator-owned label — breaks no law and
passes every gate, and would have made the biggest spender **invisible to the bill while the cost
report still rendered a confident total**: DL-57 landing on the instrument used to watch spend.

**Also checked, and it mattered:** only `operator/store.py` writes `LLMCall` today, so there was
**no code drift**. The law was being honoured exactly. This was a genuine forward-looking conflict,
caught before implementation rather than rationalised after it.

**Resolved** by [ADR-0020](decisions/0020-llmcall-is-substrate-not-the-operators.md) — `LLMCall` is
substrate; any agent may call a model and writes its own audit node into the one ledger; the operator
keeps `CommandAudit` and `Intent` and remains the sole *operator-command* LLM boundary — then
`chore-llmcall-substrate` (`v0.84.07`, operator laws **v1 → v1.1**).

**Why an ADR and not the S152 convention.** S152's standing convention covers a *lacking declaration*
of a decided capability. This was a **scope reduction on a locked, proven clause** — a different act,
and a bigger one. Recording the distinction so the convention is not stretched to cover narrowings
by precedent.

**Two process notes for next time.** The chore was kept **separate from S153** so no law amendment
rides inside a feature implementation. And `OPR-IDN-02` **stays green**: the test was re-pointed to
the amended wording and still proves it exactly — it was *not* loosened to accommodate the change,
which is the failure mode S151 taught. A second test pins the exclusion and was observed failing on
a planted revert (DL-70).

---

## DL-84 · The DHI gate fired for the first time, and waiting is the designed response · status: RESOLVED (upstream rebuild landed 2026-08-01, confirmed 2026-08-02)

**`Build and push agent images` has failed on every merge since 03:53 UTC today** — S154, the DL-81
docs commit, S152 and `chore-llmcall-substrate`, four consecutive runs. **No new images exist, so the
fleet cannot be deployed off `:s152` at all.** Everything else was green: CI and Security Findings
passed on each merge, verified by `headSha`.

**Cause is upstream, not ours.** Trivy reports `Total: 8 (HIGH: 8, CRITICAL: 0)`, every one a
`linux-libc-dev` kernel CVE in the `dhi.io/python:3.13` base (CVE-2026-63970, -64287, -64364, -64375,
-64434, -64534, -64552, -64558). The gate is `exit-code: 1`, `severity: HIGH,CRITICAL`,
`ignore-unfixed: true` — so these are **fixable upstream**, which is exactly why they now fail: a
patched `linux-libc-dev` was published and the base has not yet been rebuilt against it.

**A plain re-run does not fix it** (run `30686057170`, re-run 05:48 UTC — identical 8 findings), so
the refreshed DHI image had not landed at that point. Recorded so the next reader does not repeat the
experiment.

**The ruled-out option, and why it is ruled out.** Adding the eight CVEs to `.trivyignore` is the
obvious unblock and it is **wrong here** — it would undo the reason [R005/S130](research/base-image/INDEX.md)
migrated off `python:3.13-slim` in the first place. That migration's whole point was to move from a
base where 22 HIGH/CRITICAL findings were *permanent structural noise* to one where the gate enforces
against a **near-zero baseline and `.trivyignore` stays empty** — so that any finding is a real
signal. The file's own header says entries need a sprint/design-log link, scope, owner and expiry.
Spending the first entry on a class of CVE the base is *designed to fix within hours* trades a
durable property for a few hours of waiting.

**Also worth naming: `linux-libc-dev` is kernel *headers*.** A container runs the host kernel, so
this class is usually non-exploitable inside the image — the standard argument for ignoring it. It is
still not the right call, because the point of the DHI baseline is that we *never need to make that
argument*; the upstream rebuild removes the finding rather than us reasoning past it.

**Decision: wait for the DHI rebuild, then re-run.** R005 records DHI as *"near zero, continuously
rebuilt from source"*. The next scheduled pipeline run is Monday 2026-08-03 22:30 UTC, so there is
roughly two and a half days of slack against a rebuild measured in hours.

**Escalation path if it has not cleared by Monday morning AEST** — in preference order: pin a
known-good DHI digest for the base; or a time-boxed `.trivyignore` entry with an expiry date and this
entry as its evidence link, opened as a hardening row so it cannot become permanent.

**Process finding, separately.** Four merges were declared green today on CI + Security Findings
without anyone checking `build-images`. That is the DL-46 shape in a new costume: **a green CI proves
mergeable, not shippable.** The merge routine should assert the image build too before a change is
called done.

---

## DL-85 · LLMCall attribution is a node property, not only an edge · status: DECIDED (S153, 2026-08-01)

**Question.** S153 is the first non-operator writer of the shared `LLMCall` ledger after ADR-0020.
How should cost consumers identify who made a call?

**Decision.** Add a declared `calling_agent` property to every `LLMCall` write, while keeping
producer edges as lineage. `kernel.llm_ledger.write_llm_call` owns the shared shape; operator and
deliberator callers pass their identity into that substrate helper.

**Ruled out.** Edge-only attribution. It is audit-useful, but it forces `/audit-costs` and
`surfaces/dashboard/llm_costs.py` to infer spend through graph shapes that differ by caller and can
be absent during partial/fail-open writes. A direct property keeps the cost ledger complete and
cheap to group while preserving edges for provenance.

**Status.** Implemented in S153 with `LLMCall` property declarations and dashboard per-agent spend
breakdown.

---

**RESOLVED — the base was rebuilt and the gate went green on its own, exactly as R005 predicted.**

| Run | Commit | Time (UTC) | Result |
| --- | --- | --- | --- |
| `30686057170` | `b0e6b0e` | 2026-08-01 05:33 | ✗ 8 HIGH `linux-libc-dev` |
| `30686057170` (re-run) | `b0e6b0e` | 2026-08-01 05:48 | ✗ identical 8 |
| `30698986298` | `f32581a` | 2026-08-01 12:05 | ✓ success |
| `30730000621` | `4091d6c` | 2026-08-02 03:05 | ✓ **14/14 jobs, 0 failed** |

**Recovery took roughly six and a half hours**, entirely upstream — no repo change, no `.trivyignore`
entry, no digest pin. R005's claim that DHI is *"near zero, continuously rebuilt from source"* was
load-bearing rather than marketing copy, and the decision to wait rather than accept the CVEs is the
one that turned out cheap.

**What would have happened under the rejected option.** Adding the eight CVEs to `.trivyignore` would
have unblocked the build at 05:48 — and left eight permanent entries in a file that has been empty
since S130, for findings that fixed themselves six hours later. The first entry in that file would
have been pure noise, and the next reader would have inherited both the entries and the precedent.

**The process finding stands and is not resolved by this.** Four merges were declared green on CI +
Security Findings without anyone checking `build-images`. The image build recovered on its own, so
nothing was lost this time — but *nothing was lost* is luck, not process. **A green CI proves
mergeable, not shippable**, and the merge routine should assert the image build before a change is
called done. Tracked separately from this entry's resolution.

**Images now exist for `4091d6c`**, which carries S153, S154, S155 and both chores — so the deploy
that has been blocked since 2026-08-01 03:53 UTC is unblocked.

---

## DL-88 · The deploy failed on all 15 agents, reported success, and exited 0 · status: RESOLVED (fleet on :s155, 2026-08-02) — one follow-up open

> **Renumbered 2026-08-03.** This entry was written as DL-85, which [DL-85](#dl-85--llmcall-attribution-is-a-node-property-not-only-an-edge--status-decided-s153-2026-08-01) already held. IDs are append-only and never reused (the `conventions.md` §2 rule, applied to the design log), so the **later** claimant moved. References in `STATE.md` and hardening row Q were updated with it.

**The `:s155` deploy did not happen.** Every agent printed `[XX]`, the script then printed
`Fleet deployed with cron scale windows and dispatcher job.` and returned exit code **0**. The fleet
was left untouched on `:s152` — a clean failure — but nothing in the output said so, and an automated
caller would have recorded a successful deploy.

**The error was suppressed.** `az @agentArgs 2>$null` (`infra/deploy-agents.ps1` ~line 466) hid it
fifteen times. Recovered by running a copy of the script with the redirect removed:
`The command line is too long.`

**The measurement.** `az` resolves to `az.cmd`, a cmd.exe batch wrapper, so every invocation inherits
cmd's line ceiling. `GRAPH_VOCABULARY_B64` alone is **12,032 characters** — and `up` splices it into a
`containerapp create` that also carries every Container App secret, the GHCR PAT,
`MASTER_PUBLIC_KEY_PEM_B64` and the cron scale args.

**Why `:s152` worked on 2026-07-31 and this did not.** That was an image *retag* plus a narrow
`--set-env-vars` call — short commands. This is full `create`. The pack growing 11,228 → 12,032 across
S153/S154/S155 was not the cause on its own; the wider command was. The fix is therefore not to
shrink the pack but to stop carrying it on that line — **and the precedent is already in the same
file**: `Set-AppPostgresDsn` does `secret set` then `update --set-env-vars`. Vocabulary injection
never adopted that shape.

**Two defects, and the second is the one that will bite again.** The length limit is a bounded
infrastructure problem. **A deploy tool that cannot report its own failure is the DL-57 pattern
living inside the thing we use to verify everything else** — `Check` only prints, nothing
accumulates, and the success banner is unconditional. That is what turned a five-minute fix into a
diagnosis cycle, and what would have let a half-deploy pass as done.

**Ruled out:** minifying the pack (8,128 chars leaves no headroom, and it grew twice in one week);
moving it to a Container App secret (`--secrets name=value` is inline too, same line); trimming
declarations to fit (trades the guard's correctness for a shell limit). **Deferred, recorded as a
decision not an oversight:** migrating the script to `az containerapp create --yaml`, which removes
the limit class entirely but is a rewrite of every create/update path.

**Found on the way, all fixed before this point:** the deliberator was absent from
`build-images.yml` so its image was never built (`0.85.02`); its Dockerfile was off the S130
hardened pattern — `python:3.13-slim`, single-stage, `uv run` as CMD against a shell-less runtime
(`0.85.03`); and it lacked `--extra llm`, so the agent would have deployed, activated, polled and
produced **no `DeliberationRun`** — DL-80's exact shape inside the agent built to end it. **None of
these could surface earlier because the image was never built**, and none were caught in review:
S153 was checked for laws, clause counts, ADR conformance and its acceptance gate, and nobody asked
whether the image builds and runs.

**Provisioning done on 2026-08-02 and safe to keep:** three deliberator Postgres roles + DSNs, three
SAS identities, six rules, three topics/subscriptions; `alembic upgrade head` was a no-op (no new
migrations). Existing agents' SAS keys were **not** rotated — verified by comparing the Key Vault
connection string against the live rule key, because the running fleet holds those values baked in
at deploy time and a rotation would have broken the bus at the next run.

Chore: [chore-deploy-pack-off-the-command-line](sprints/chore-deploy-pack-off-the-command-line.md).

---

**RESOLVED — fleet deployed at `:s155`, and the first fix was not enough.**

**The two-step was necessary but insufficient.** Moving the pack into its own narrow
`--set-env-vars` call (`0.85.04`) still failed: **`az` is `az.cmd`, so cmd's ~8,191-character
ceiling applies to the *whole invocation*, and the pack alone is 12,053 characters.** Measured
directly rather than inferred: `LASTEXITCODE: 1`, `The command line is too long.`, with nothing
else on the line. The fix therefore could not be *staying under* the limit — it had to be *leaving
the wrapper*.

**What actually works:** invoking the CLI's own interpreter, `python.exe -m azure.cli`, which goes
through `CreateProcess` (32,767) instead of cmd. Verified live before adopting it: the identical
call that failed via `az.cmd` returned `0`, and the pack read back off the deployed `execution`
app decoded **byte-identical** to the repo pack. Shipped `0.85.05`, with a fallback to bare `az`
where the interpreter is absent — safe, because non-Windows paths have no such ceiling.

**A window where the fleet was worse off than before.** Between the two runs, all 16 apps were on
`:s155` **with `GRAPH_VOCABULARY_B64` absent entirely** — image updates had succeeded while the
vocabulary step failed. That is not the fail-closed stall the guard is designed around; an absent
variable means `build_graph_from_env` returns an *unguarded* store, so S144's protection was simply
**off** on new code. Less dangerous than a stale pack, and strictly worse than `:s152`. Worth naming
because "the deploy half-worked" had a specific safety meaning that neither the script nor the
operator would have inferred from the tag alone.

**Verified after the second run**, not assumed: 16/16 apps on `:s155`; **16/16 carrying a
byte-identical pack** (`sha256 aec5ce55f789…`, checked per app rather than sampled); 16/16
`provisioningState=Succeeded`; every app `minReplicas=0` with 1 KEDA rule; `dispatcher-cron` on
`:s155` with cron `30 22 * * *` and the pack present. `DeployRecord
deploy:2026-08-02T08:38:00Z:s155:1a17236` written only after all of that.

**The follow-up, and it is the same class in the opposite direction.** The second run reported
`[XX]` for all 15 agents and the job while *actually succeeding* — `az` exited 0, so no stderr was
surfaced, but the value read back from `--query properties.provisioningState` was not the string
`Succeeded`. So the tool now under-reports instead of over-reporting. That is the **safe** direction
— a false negative costs a verification pass; the false positive it replaced would have shipped a
broken fleet as done — but a deploy whose report cannot be trusted either way is still not finished.
`Invoke-Az`'s success detection needs a proper look, probably reading the state from a separate
`show` rather than parsing a merged stdout/stderr stream.

---

## DL-86 · Ceremony proportional to blast radius, not applied uniformly · status: DECIDED (2026-08-02, operator)

**Operator challenge, twice in one exchange:** *"this is not a bump and it does not warrant a version
bump if you are doing it just for the .ps1 file"*, then *"why do we need a CI??"* — both on a change
that widened a column in `infra/status.ps1` because `deliberator-proponent` (21 chars) overran a
hardcoded width of 19.

**The challenge was right, and the reason is worth keeping.** `make ci` runs ruff, mypy, pytest,
import-linter and coverage. **None of them read PowerShell.** Running the full gate on a `.ps1`-only
change proves nothing about that change — it *looks* like diligence while verifying nothing. The run
was green only because of a Python test added alongside; the actual verification that mattered was
rendering the table and looking at the columns.

Same for the version: `0.85.06` for a column width would sit in the history beside `0.85.05`, which
was the fix that made the fleet deployable at all. **Bumping for cosmetics makes a real fix
indistinguishable from a rendering tweak.**

**Decided, now in CLAUDE.md:** docs and **read-only** tooling take the light path — straight to
`main`, no branch, no remote gate, no version bump — verified the way the artifact is actually
verified (render it, parse-check it).

**The line is blast radius, not file extension**, and that distinction is the whole decision.
`infra/deploy-agents.ps1` is also PowerShell and also invisible to `make ci`, but it **changes
production** — it keeps the full cycle. So does anything adding or editing a Python file, because
then CI genuinely is testing something. Unsure → full cycle.

**The road not taken.** The tempting rule was *"non-Python changes skip the gate"*, which is simpler
and wrong: it would have exempted the five deploy-script chores shipped earlier the same day, one of
which briefly left the fleet running new code with the write guard **off**. A file-extension rule
optimises for the wrong property.

**Honest accounting of what this costs.** The light path removes the remote gate from changes CI
never covered, so nothing real is lost — but it does remove the *habit* of pushing before merging,
and habits are what caught the S131/S132/S134 ungated merges. Mitigated by keeping the carve-out
narrow and the default ("unsure → full cycle") biased toward the gate.

---

## DL-87 · A partial test is not a smaller clause · status: CLOSED (2026-08-02, [ADR-0021](decisions/0021-clause-summary-mirrors-the-law.md))

**The finding, restated.** S151 flipped `EXEC-FAIL-03` green on a test proving one of its three
conjuncts, and — the move that matters — **reworded the clause summary in `test-plan.md` toward that
test's scenario**. Both documents then agreed, so nothing disclosed the gap. Reverted in review;
closed properly by `chore-exec-fail-03-coverage`, which proves all three conjuncts and takes
execution to 31 / 57.

**Why it deserved an ADR rather than a return note.** S152's convention was a *reading* of an
existing rule, so a sprint doc held it. This one changes what `conventions.md` requires, and that
file's own INDEX row says *"amend only via a new ADR or RFC"* — there is no RFC mechanism in the
repo, so ADR is the only compliant route. DL-86's *ceremony proportional to blast radius* cuts
*toward* the ADR here, not away from it: the blast radius is every future coverage claim.

**Inserted as §7a, not §12.** Section numbers in `conventions.md` are cited from sprint docs and test
docstrings (`conventions §3`, `§4`, `§7`, "sections 3 and 7"). Renumbering §8–§11 to append a §12
would break those citations the same way renumbering a clause ID breaks traceability (§2). Appending
out of position was the cheaper wrong answer; a lettered insert keeps both properties.

**The road not taken: split the clause into three IDs.** It maps cleanly onto three tests and is the
same narrowing in better clothes — two of the three would sit ⬜ indefinitely while the ledger showed
a green for the easy one. `EXEC-FAIL-03` describes one behaviour: a failed graph write is survivable.
Splitting stays available for a law that genuinely conflates two behaviours; "a test only covers part
of it" is not that.

**A probe that measured the fake instead of the property.** The first draft proved "the idempotency
key prevents re-submission" with `PaperBroker.order_count`. Planting a broker that never de-dupes
left the test **passing** — `PaperBroker._fills` is itself a dict keyed by idempotency key, so the
count could not move whatever the broker did. The assertion was true and worthless. Replaced by
recording what the caller actually sends, and re-planted at the real source (an unstable key), where
it failed and the measured consequence was **two broker orders for one intent**. Worth keeping
because the failure mode is generic: *asserting against a fake's internals rather than the behaviour
under test*, and DL-70's planted-failure rule is the only thing that catches it.

**Found, not fixed.** Counting execution's greens meant counting everyone's: `ledger.md` and
`laws/INDEX.md` disagree with the test-plans they summarise for **8 of 14 agents**
([hardening row R](hardening-backlog.md)). Not corrected here, because the larger number is not
automatically the right one — a 🟩 is only true if a passing test cites the ID, so adopting the
bigger figure would repeat the exact over-claim this entry is about.

---

## DL-89 · Pytest must never transact with production Service Bus · status: DECIDED (2026-08-05)

**Question answered.** Hardening row T's open question resolved to the worse answer: the
deliberator peer tests did not merely resolve a live endpoint, they published to the production
Service Bus namespace. The operator-observed evidence was 40 dead-lettered messages on
`deliberator-proponent.requests/agent`, all carrying the fixture `run_id` value `"turn-1"`, and the
`S100ReceiverFailure` reason proves the live consumer received and retried them.

**Decision.** Local pytest may not cross the Azure Service Bus send boundary. Tests that need the
Service Bus-shaped peer client must inject offline settings
`AzureServiceBusSettings(connection_string=None, connection_strings_json=None)`, and the root pytest
configuration unconditionally patches `AzureServiceBusBus._azure_send` to raise if any test reaches
that boundary. The guard sits at the send boundary because that is the last point where the defect
is observable without relying on SDK internals or the presence of the Azure extra.

**The `.env` trap.** Removing only the direct `env_file=".env"` declaration would not have been
enough while `conftest.py` loads `.env` into `os.environ`; a no-argument settings object would still
resolve the credential from process env. S159 therefore does both: the peer tests construct offline
settings explicitly, and the send-boundary guard rejects the next accidental resolved credential.
`AzureServiceBusSettings` also overrides inherited `.env` loading with `env_file=None` so ordinary
env-clearing isolation works for this boundary. The base `AgentSettings` and dashboard settings
still load `.env`; changing those was rejected as the broad test-harness refactor this sprint
explicitly avoided.

**Roads not taken.** Rejected: stopping root `conftest.py` from loading `.env` (too much blast
radius for tests that legitimately read local config), adding the Azure extra to the default install
(would make accidental production sends more reliable), guarding the vendor SDK import path (fails
when the SDK is absent), or adding an opt-out marker for future live tests. Existing live Service
Bus pytest entry points are skipped by default; live Service Bus proof belongs in explicit operator
scripts, not in `make ci`.

**Verification instrument.** The 40 messages were purged with operator approval before S159 so the
dead-letter baseline could become zero. A final local gate in a tree with `.env` present must leave
`deliberator-proponent.requests/agent` at dead: 0; that production-side count is stronger evidence
than a unit assertion because it observes the namespace directly.

---

## DL-90 · S159's residue: a swallowable guard, and a suite doing DDL on production · status: DECIDED (2026-08-05)

Three items surfaced at S159's handback rather than in its spec. [[DL-89]] stands; this entry
corrects its blast-radius statement and closes the residue in one chore instead of three backlog
rows.

**1. The guard could be swallowed.** `PytestAzureServiceBusSendError` derived from `RuntimeError`,
and `kernel.errors.fault_boundary` catches bare `Exception`; with `reraise=False` it converts the
error into a `Fault` and continues. Measured with a throwaway probe: the guard error became a
`Fault` of type `PytestAzureServiceBusSendError` and the probe reported `1 passed`. The *protection*
held either way — the raise happens before any Azure I/O — but the *loudness* did not: a test
exercising an agent path that publishes inside a degraded-but-continue boundary passes green, the
author never learns the test tried to transact, and the code under test silently takes a fault path
it would never take in production, so the assertions may be measuring the wrong thing. This is
S158's own lesson (*fail-open must be loud*) recurring inside the fix for a different problem.
**Decided:** the guard derives from `BaseException`, for the same reason `KeyboardInterrupt` does.
Pinned by `test_pytest_guard_is_not_swallowed_by_a_fault_boundary`, which was watched failing on the
planted `RuntimeError` (`DID NOT RAISE`) before being trusted.

**2. The blast radius included topic DDL, not only published messages.** DL-89 and hardening row T
both describe messages reaching the namespace. Measured 2026-08-05:
`tests/test_bus_azure_receiver_integration.py` gated on `_CONNECTION`, which reads **both**
`AZURE_SERVICEBUS_CONNECTION_STRING` **and** `SERVICEBUS_CONNECTION_STRING`; `.env` supplies the
second name, so its `skipif` never fired, `integration` is not deselected (`addopts` carries no
`-m "not integration"`), and the credential has Manage rights (`list_topics` returned 22 topics).
That test creates two topics and two subscriptions per run via `ServiceBusAdministrationClient`,
sends, receives, and deletes them. A green `make ci` therefore implies it ran to completion — the
suite was performing create/delete DDL against the production namespace on every local gate, not
merely publishing. No leftovers exist (`s100-*` topics: none), so its cleanup worked.
**Correction to DL-89:** its sentence *"existing live Service Bus pytest entry points are skipped by
default"* became true only when S159 added an unconditional `@pytest.mark.skip`; it was not true
before.

**3. Two live entry points deleted rather than left skipped.** `test_bus_azure.py`'s parity test was
skipping **by accident**: its `skipif` checks only the `AZURE_`-prefixed name while `.env` supplies
the un-prefixed alias, so a single env-var rename would have started it publishing to a
`parity.topic` that does not exist in the namespace. **Decided:** delete both it and the live
receiver test. A permanently-skipped test is worse than no test — it reads as coverage while proving
nothing, which is the DL-57/DL-59 shape at test level. **To restore either one, the precondition is
a dedicated non-production Service Bus namespace**; until that exists, live-bus proof belongs in an
explicit operator script, never in `make ci`. The provider integration tests
(`test_sources.py`, `test_stooq.py`) are deliberately **kept**: they gate on purpose-named opt-in
variables (`FINNHUB_TEST_NETWORK=1`, `STOOQ_TEST_NETWORK=1`) that nothing sets by accident, and they
read public data rather than touching owned infrastructure. That difference is the rule — an opt-in
named for its own purpose is safe; a gate that keys off *the production credential being present* is
not, because the credential is always present.

**Stated boundary, not a new open row.** `kernel/config.py`'s `AgentSettings` base declares
`env_file=".env"`, so every settings class in the repo still reads the file directly;
`surfaces/dashboard/settings.py` declares it too. S159 overrode only `AzureServiceBusSettings`.
Changing the base changes local config resolution for every agent and deserves its own decision, so
it is **deliberately out of scope and recorded here as a known boundary** rather than filed as debt.
The send-boundary guard, not the settings change, is what makes the dangerous half safe.

**Road not taken.** Making `fault_boundary` refuse to catch the guard type (couples kernel error
handling to a test fixture); a pytest plugin instead of a conftest fixture (more machinery, same
guarantee); keeping the live tests behind a `RUN_LIVE_INTEGRATION=1` opt-in (rejected — the opt-in
would still point at the production namespace, so it moves the risk without removing it).

---

## DL-91 · "No workflow runs appeared" had a mundane candidate cause all along · status: DECIDED (2026-08-05)

Hardening row M recorded that on 2026-07-23 a pushed branch produced **no runs at all**
(`total_count: 0`, confirmed twice a minute apart), that `workflow_dispatch` resolved it, and that
the **cause was never established**. It was carried as an infrastructure miss that could silently
defeat the branch-is-the-gate rule.

**Measured 2026-08-05.** The GitHub API's `head_sha` filter matches only the full 40-character SHA.
Handed an abbreviated one it returns zero — no error, no warning, no hint the query was malformed:

```text
head_sha=c145e5e79a3a3aa7435897d5ec80800167884892  ->  total_count: 2   (both green)
head_sha=c145e5e                                   ->  total_count: 0
```

That reproduces row M's exact symptom on demand with no platform fault involved, and the row's own
detail — *"confirmed twice a minute apart"* — fits a deterministic query bug better than a transient
infrastructure miss, which would more likely have cleared on the second look.

**Stated honestly: this is a strong candidate, not a finding.** Which SHA form the 2026-07-23 query
used cannot be recovered, so the row is closed on its *fix trigger* being satisfied, not on the cause
being proven. Row M's Done entry says so explicitly rather than quietly upgrading a hypothesis into
a conclusion — the same discipline hardening row S needed when its stated diagnosis turned out to be
wrong.

**Decided:** the check becomes a command, not a glance. `make gate-ran`
(`scripts/assert_gate_ran.py`) resolves the full SHA itself via `git rev-parse`, **refuses an
abbreviated SHA outright** rather than querying with it, and fails unless both `CI` and
`Security Findings` exist for the commit and both concluded `success`. `CLAUDE.md`'s merge sequence
now names it as a required step.

**The fix had to not inherit the bug it catches.** A wrapper that simply re-ran the same query would
report "no run exists" with total confidence for a short SHA — converting a silent wrong answer into
a loud wrong answer, which is worse. Refusing the abbreviated input is the whole point.

**Proven able to fail (DL-70).** Two `gate_selftest` cases: `gate-ran-rejects-abbreviated-sha`
(plants `--sha c145e5e`) and `gate-ran-rejects-zero-runs` (plants a `{"total_count": 0}` payload
through the script's `--runs-json` seam, so the zero-runs branch is provable without network).
Two invariants stop the procedure drifting back: `CLAUDE.md` must contain `make gate-ran`, and the
`Makefile` must define it. Self-test 15/15 → **19/19**.

**A wait window, because an assertion that cries wolf gets ignored.** Found while using the tool on its own push: a query issued immediately after `git push` returns zero, then `total_count: 2` by t+15s — GitHub creates runs a few seconds after the push, not synchronously with it. Without a wait the assertion would fail on every ordinary merge and be trained away within a week, which is the DL-52 failure mode in a new costume. It now polls for up to 120 s (`--wait-seconds`). **The wait is also what gives the assertion its meaning**: *never created* only becomes distinguishable from *not created yet* once you have waited, which is precisely the distinction row M could not make by eye.

**Road not taken.** Asserting inside `make ci` (wrong lane — `make ci` runs before the push, when no
run can exist yet); polling until runs appear (turns a missing run into a long wait rather than a
failure); requiring a PR again to get the checks UI (DL-52's reversal stands — the gate runs on push
to every branch, so pushing *is* the gate).

---

## DL-92 · The deploy report was wrong about ordering, not about content · status: DECIDED (2026-08-05)

Hardening row Q: after DL-88 stopped the deploy script *over*-reporting, it began **under**-reporting
— the `:s155` run printed `[XX]` for all 15 agents and the job while every target had actually
deployed, and it happened again 2026-08-05 with *"Deploy FAILED for 17 target(s)"*, exit 1, entirely
wrong. The row recorded the symptom precisely and guessed at the cause: *"the value parsed from
`--query properties.provisioningState` out of a merged stdout/stderr stream simply is not the string
`Succeeded`."*

**The guess was right about where and wrong about why.** `Invoke-Az` merged the streams with `2>&1`
and returned *"the last non-empty line that does not start with `WARNING:`"*. My first hypothesis was
that the extension emits a **non-WARNING** stderr line the filter misses — measured, and that alone
is harmless: with the notice emitted *before* the value, the heuristic still returns `Succeeded`.
The defect is **ordering**. Any stderr line arriving **after** the tsv value becomes the answer,
whatever it says. The old code's own comment admitted the weakness — *"pick the last non-empty line
rather than trusting order"* — and taking the last line is precisely what makes trailing stderr
fatal. All four `Invoke-Az` call sites parse `provisioningState` (master, each agent,
`Set-AppVocabulary`, `Set-JobVocabulary`), which is why *every* target flipped to `[XX]` at once
rather than a random few.

**Measured 2026-08-05** against a stub `az.cmd` — a real external process, because a PowerShell
function writing through `[Console]::Error` bypasses stream redirection and silently invalidates the
test (that mistake was made first and caught):

```text
stub emits: WARNING banner (stderr) -> "Succeeded" (stdout) -> deprecation notice (stderr)
  old heuristic -> 'Deprecation: containerapp update will change default behavior...'  Succeeded? False
  new Invoke-Az -> 'Succeeded'                                                          Succeeded? True
stub exits 1 with "ERROR: The command line is too long." on stderr
  new Invoke-Az -> $null, stderr printed   (DL-85 stays fixed)
```

**Decided.** (1) `Invoke-Az` sends stderr to a temp file instead of merging, so the returned value is
stdout and needs no filtering heuristic at all; stderr is still printed on non-zero exit, because the
old `2>$null` hid *"The command line is too long."* fifteen times over (DL-85) and that must not come
back. (2) Success detection reads `properties.provisioningState` from a **separate
`az containerapp show`** (`Get-AppState` / `Get-JobState`) rather than from the output of the call
that changed the resource — row Q's own recommendation. A deploy is the one operation with no cheap
undo, so its report is worth a second round trip.

**Stated boundary, not discovered residue.** The remaining raw `az ... 2>$null` call sites
(`Deploy-DispatcherJob`, the secret-set helpers) discard stderr and do not check `$LASTEXITCODE`. They
were deliberately left alone: a failed call there yields an empty `$state`, so the comparison is false
and the target reports `[XX]`. They **fail closed** and cannot produce a false green, which is a
different and much lower severity than what this entry fixes.

**Not proven, and it should not be claimed.** The exact stderr line the containerapp extension emits
*after* the value in production was **not** captured — doing so requires a real deploy, which is
operator-gated. The trailing notice above is synthesised to reproduce the *class*. What is proven is
the mechanism: trailing stderr defeats the old parser, and the new one is immune to it regardless of
what the line says. **The end-to-end confirmation is owed at the next deploy** — expect `[OK]` for
all 17 targets, and if any `[XX]` appears it should now be a real failure with its stderr printed
above it.

**Road not taken.** Filtering more stderr patterns (an arms race against a vendor's output);
`--output json` and parsing (same stream problem, more parsing); checking only `$LASTEXITCODE` and
dropping the state read (loses the DL-85 lesson that exit codes alone were what made a broken deploy
look done).

---

## DL-93 · Sizing, the 10-slot cap, and "sell what is losing" · status: OPEN (operator raised 2026-08-06; decision deferred pending the sizing/margin question)

**Operator framing, recorded because it reframes what the pipeline is currently for.** *"We are not
at the trading stage. Far from it. We are still in development."* The object under test is the
**selection process** - can the system predict? - not profit. Therefore **position size is not a
variable we care about right now**: *"I do not care HOW MANY SHARES I PURCHASED... even 1 share of a
profitable stock is better than 10 fully exhausted purchase power."* Profit is the ultimate goal but
not the current measurement; the current measurement is whether the picks are right. This entry
records the discussion, the measurements taken, and the one question that is genuinely an ADR
reversal rather than a parameter change.

### Measured 2026-08-06 (Alpaca paper, read-only)

Eight of ten held parcels are profitable; total unrealized **+$8,832.76**.

| Ticker | Qty | Avg entry | Last | Unrealized $ | Unrealized % |
| --- | --- | --- | --- | --- | --- |
| BMY | 153 | 65.63 | 63.76 | **-286.11** | **-2.85%** |
| MDT | 233 | 86.59 | 85.99 | **-139.02** | **-0.69%** |
| ABT | 191 | 105.52 | 105.71 | +37.12 | +0.18% |
| USB | 478 | 62.60 | 64.21 | +767.87 | +2.57% |
| WFC | 348 | 86.39 | 89.50 | +1,080.99 | +3.60% |
| PYPL | 175 | 56.65 | 58.70 | +358.89 | +3.62% |
| SCHW | 196 | 102.22 | 108.02 | +1,136.10 | +5.67% |
| BAC | 503 | 59.64 | 63.40 | +1,892.63 | +6.31% |
| CSCO | 177 | 112.41 | 122.70 | +1,820.52 | +9.15% |
| HPE | 229 | 43.55 | 53.00 | +2,163.77 | +21.70% |

The two losers total **-$425** against **+$9,258** of winners.

### The finding that outranks the cap: the book is on ~2x margin

```text
equity        104,042.69
cash         -104,966.77   <- negative
market value  209,009.46   <- 2.01x equity
```

`cash_buffer_pct = tunable(0.05, why="Hold back cash so sizing does not consume the full paper
account.")` **is not achieving its stated purpose** - the account did not merely spend its cash, it
borrowed roughly the same amount again. **This is a defect, not a tuning question, and it must be
understood before any resize**: resizing on top of it would produce a hundred small wrongly-sized
positions instead of ten large ones. No change was made pending that investigation.

### Where the 10-slot cap came from, and why it is not a decision anyone made

`agents/portfolio_manager/settings.py:35` -
`max_positions = tunable(10, why="Keep portfolio concentration bounded before sector caps exist.")`.
**Sector caps now exist** (`max_sector_pct`, `settings.py:73`, shipped S52 - whose sprint doc quotes
this exact `why` as its own motivation). The cap is therefore being enforced by a justification that
lapsed eight sprints ago. Nobody chose to keep 10; it was never revisited.

**Consequence, measured on `sched-2026-08-04/05` (corrected 2026-08-06 — this entry first said three nights; `sched-2026-08-03` produced **zero** buys, so there were **2** `blocked_capacity` dispositions, not 3, as the S160 shadow book then confirmed):** the analyst's single `buy` is rejected `SKIP max_positions`, PM approves **0** on all three nights, and therefore the deliberator
has **nothing to debate** - `debates: 0, verdicts: {}`. **The cap is what is starving
[[DL-80]]**, which cannot close until the PM approves an order.

**S162 caveat for the shadow book (recorded 2026-08-07):** S160's `blocked_capacity` disposition is
read from the single rejected-order `reason`, so a buy that fails both `max_positions` and
`cash_available` is labelled as capacity-blocked even though it was unaffordable too. The two
measured `sched-2026-08-04/05` dispositions remain clean: they ran on `:s158`, where the PM still
used the fictional cash book and `cash_available` genuinely passed. From `sched-2026-08-06`
onward, after S161 deployed account-backed sizing, the cut must be read with this caveat. S162 adds
the rejected-order gate report so future runs show when the `reason` was not the only blocker; it
does **not** reclassify old dispositions or change the S160 scorecard.

### Why nothing is sold today (this part is working as designed)

Not a missing feature - a deliberately removed one. [ADR-0017](decisions/0017-exit-authority-alpha-proposes-risk-disposes.md)
§4 retired `target`/`time` as mechanics ("let winners run; exit on thesis"), leaving the **stop** as
the only mechanical exit. Measured 2026-08-06: every position carries `opened_price_cents` and
`stop_pct=0.05`, so a stop threshold **is** computable for all ten, and **none is breached** - the
closest is BMY at 63.76 against a 62.35 stop (2.3% of headroom). The analyst returned `hold` on all
eleven names. So: no breach, no mechanical exit, no discretionary exit, nothing closes.

> **A correction worth keeping.** The investigation was first reported as *"every active Position
> carries `entry_price_cents=None`, so exits cannot be measured."* **That property does not exist.**
> The entry price is stored as `opened_price_cents` and is populated on all ten. The `None` was a
> query against a guessed name, not missing data - the same shape as the retracted [[DL-73]] audit.
> The real gap is narrower and is stated below.

### The real measurement gap: realized PnL is never derived

`pnl_cents` **is** genuinely `None`, and [ADR-0015](decisions/0015-exit-lifecycle-and-stop-ownership.md)
§1's amendment already names it: *"the monitor stopped writing `pnl_cents` altogether... Nothing yet
computes PnL at fill time"*, and *"that blocker is now gone - ABT 98 @ $101.35 filled on 2026-07-23 -
so the derivation is unblocked and outstanding."* Meanwhile **unrealized** PnL is fully available at
the broker (+$8,832.76 above), so the reporter prints `open=0.0` while the account is up $8.8k. It
reads a graph property nobody writes.

### The open question - an ADR reversal, not a parameter

Operator's proposed rule: **"If it is profitable keep, if not sell."** That is a *mechanical* exit
rule, and it reverses ADR-0017 §4, which deleted mechanical exits on purpose. It is therefore an
**ADR amendment with evidence**, not a tunable change, and it is deliberately **not** actioned here.

**Two candidate directions, both recorded rather than chosen:**

- **A - resize for observation (no policy change).** Cut `max_position_pct` 0.10 -> ~0.005 (~$500 a
  pick) and raise `max_positions` 10 -> 50-100. Serves the operator's stated goal directly: many
  small parcels keep the selection process sampled, the account stops being exhausted, and the veto
  is un-starved. **Requires the margin defect to be understood first.** Touches only parameters
  whose justification has already lapsed.
- **B - reintroduce a mechanical loss exit** ("sell what is losing"). Frees slots and matches the
  operator's instinct, but reverses an accepted ADR and re-introduces exactly the mechanical
  decision-making ADR-0017 removed. Needs an ADR amendment stating what changed in the evidence
  since 2026-07-24.

**Road not taken (so far):** selling the two losers by hand to free slots - rejected as a *mechanism*
because `EXEC-IDN-01` makes execution the sole broker interface and a hand-fired order writes no
lineage, which is precisely the evidence this testing phase exists to produce. If the positions
should go, they should go through the pipeline.

**Status is OPEN on purpose.** The sequence agreed with the operator: understand the sizing/margin
defect first, then decide A vs B. Nothing was changed on the account, the parameters, or the ADRs.

---

## DL-94 · `pg_teardown.py --run-id` leaves orphans, because its label list predates half the graph · status: CLOSED (2026-08-08, `chore-teardown-leaves-no-orphans`, 0.89.04)

**Found while tearing down the S162 end-to-end check** (`sched-2026-07-17`, a synthetic backdated
run fired to exercise the deployed `:s162` fleet). `--run-id` reported `deleted_edges=50
deleted_nodes=21` and read as complete. It was not: **41 further nodes survived**, all stamped with
the same run's identifiers.

**Why.** `_RUN_ARTIFACT_LABELS` enumerates 16 labels and is the filter on the recursive neighbour
walk. Four labels the pipeline now writes are absent from it, so the walk refuses to traverse into
them:

| Label | Orphans left behind | Written by |
| --- | --- | --- |
| `Rejection` | 11 | PM `store.write_order_decision` |
| `SentimentReading` | 11 | analyst |
| `PositionCheck` | 10 | monitor |
| `DeliberationRun` | 1 | deliberator |
| `BrokerPositionSnapshot` (PM-keyed) | 1 | execution at submit |

Plus **6 `Recommendation` nodes**: those *are* in the list, but the only path the walk had into them
was via `Candidate`, and the run scored 11 recommendations against 5 scanner survivors. The five
reachable ones were deleted and the other six were not — **a partially-deleted lineage, which is
worse than an untouched one**, because the surviving rows look like real history.

**The failure mode is the point.** The script prints a count and exits 0. Nothing about
`deleted_nodes=21` says "and 41 more matched your stamp and were left". Teardown is the step that
makes a functionality check honest (`functionality-checks.md`: *"Return stamped rows to zero after
each check"*), so a teardown that silently under-deletes quietly corrupts the register's central
claim. Cleared here only because the residue was **verified by stamp afterwards rather than
inferred from the exit code** — three further `--prefix … --contains` sweeps, then a re-count to
zero across all five of the run's identifiers.

**Decision: fix the script, do not fix it inline.** `scripts/pg_teardown.py` is Python, so
CLAUDE.md puts it on the **full cycle** (branch, `make ci`, remote gate, merge) — not the docs light
path. Doing it as an untested edit during a functionality check would be the same class of mistake
the entry describes. Filed for its own chore.

**What the fix should be, and what it must not be.** Add the four missing labels and give
`Recommendation` a path that does not depend on `Candidate` (walk from `AnalystRun`, or match the
analyst-run stamp directly). 🪤 **The label list cannot simply become "every label":**
`_RUN_ARTIFACT_LABELS` already contains `Position` and `Fill`, which the standing broker-state note
(DL-44 / S120) calls **production state, not disposable proof artifacts**. The dry run for this
teardown was checked precisely for that — it reached neither, but it reached them only by luck of
the edge topology, not by design. The real fix should make that safety explicit rather than
incidental.

**Road not taken.** Deleting by raw SQL against the run id without the label filter — rejected for
exactly the reason above: it would have taken the 27 live `Position` rows mirroring the Alpaca book
with it, manufacturing the broker↔graph divergence DL-44 exists to prevent.

### Resolved 2026-08-08 — and the fix above was **not** the fix that worked

Measured against the live spine before writing any code. Three of this entry's own claims were wrong,
and the third is the one that would have caused harm.

**1. `PositionCheck` cannot be fixed by adding the label.** Its *only* edge type in the entire graph is
`PositionCheck -> Position` (191 of them). `Position` is production state, so no walk that respects
DL-44 may traverse it — which means **no walk can ever reach a `PositionCheck`.** Measured: widening the
label list exactly as this entry proposed reaches **0** of them. The fix is a second enumerator — the key
convention `<owning-run-key>:<suffix>`, e.g. `monitor-run-<id>:broker:WFC:348:8639:check` — which
collects them by prefix without traversing anything. `CloseDecision` has the same single-edge shape and
was equally unreachable while sitting in the list looking covered.

**2. `Recommendation` is not reached via `Candidate`.** Its inbound edges are `Rejection -> Recommendation`
(129) and `OrderIntent -> Recommendation` (56); there is no `Candidate -> Recommendation` edge at all. That
sharpens the diagnosis rather than changing it: the S162 run approved **zero** orders, so it had no
`OrderIntent`s, and with `Rejection` missing from the list the recommendations were orphaned *transitively*.
Adding `Rejection` closes it.

**3. 🚨 The label list was a load-bearing traversal barrier and nothing said so.** This entry warned the
list "cannot simply become every label". The real hazard is sharper: `Position`'s only bridge from the
reached set is `Fill -> BrokerStopOrder -> Position`, and it held **solely because `BrokerStopOrder`
happened to be absent**. `BrokerStopOrder` reads exactly like a run artifact — it is created during a run —
so the obvious next edit to that tuple would have deleted the 27 live `Position` rows mirroring the Alpaca
book. The one tuple was answering two different questions.

**The shipped shape.** `scripts/pg_teardown_targets.py` splits them: `PROTECTED_LABELS`
(`Position`, `Fill`, `BrokerStopOrder`, `BrokerOrderStatus`) is broker-mirroring production state, never
deleted and never traversed *through*; `RUN_ARTIFACT_LABELS` is disposable proof, and can now grow safely.
`--run-id` **verifies itself**: it re-reads the run's stamps after deleting and **exits 1** naming every
survivor, so the defect this entry records — a count printed, exit 0, 41 rows still stamped — cannot
recur silently.

**Proven read-only on `sched-2026-08-07`:** 23 former orphans now collected (11 `SentimentReading`,
**10 `PositionCheck`**, 1 `DeliberationRun`, 1 `Rejection`), and **10 `Fill` rows no longer deleted** —
`exit:…:sell`, the ten live flatten exits. The old code would have deleted the graph's record of ten
orders open at the broker. `protected_kept` reports **20** (10 `Fill` + 10 `Position`); a stamp-based
count reported **0**, because a spared `Fill` keyed `exit:<ref>:WFC:sell` carries no run stamp — so the
count was changed to mean *what the walk stopped at*, not *what matched the stamp*.

**Road not taken (this time).** Removing the allowlist so the walk traverses everything except protected
labels — rejected: it inverts a silent under-delete into a possible over-delete across runs through hub
nodes, and the measurement that mattered (widening adds only 13 rows, no cross-run escape) was taken on
*one* run and is not a guarantee.

🪤 **The live check earned its place.** All 12 unit tests passed while the SQL was invalid: `ESCAPE` is a
syntax error on the `LIKE ANY(...)` form, and a fake cursor does not parse SQL. Unit-green really is not
"works".

---

## DL-99 · The debate is inert until 2026-09-01, and my audit said zero faults while 18 were being written · status: CODE FIXED (S167; account limit remains until 2026-09-01)

**Two findings from one investigation.**

### 1. The Anthropic API usage limit is exhausted

The `:s166` veto-gate run recorded `real_debate_count=0, failed_open_count=18` with the rationale
*"llm unavailable (fail-open)"*. That rationale is **almost right for the wrong reason**: 58
`LLMCall`s were logged across all three roles in the window (proponent 28, opponent 20, manager 10),
so the peers *were* reachable. The 18 Faults say what actually happened:

```
Error code: 400 - invalid_request_error
"You have reached your specified API usage limits.
 You will regain access on 2026-09-01 at 00:00 UTC."
```

`_review_one` pre-seeds `fail_open_review()` and runs the debate inside
`fault_boundary(reraise=False)`, so any exception leaves the fail-open verdict standing. That is the
designed behaviour (S147) and it worked — but it means **the veto is inert until 2026-09-01**, on
every run including Monday's.

🟢 **S166 handles this correctly, and that is worth stating.** The gate waits for a
`DeliberationRun`, not for a *good* one. The fail-open run is written within ~2 minutes, execution
applies it and submits. No deadlock, no stall — exactly the S147 constraint the ADR was built around.
**What is lost is the review, not the trading.**

The comparison that isolates it: the `:s165` run 80 minutes earlier reached the model for real
(`real_debate_count=18`, 73 calls). The limit was crossed between the two runs — plausibly *by* the
first run, which spent 139 Opus calls.

### 2. 🚨 My own audit reported "Faults today = 0" while 18 were being written

`Fault` nodes stamp **`occurred_at`**, not `created_at`. My pre-Monday audit queried
`props->>'created_at' > '2026-08-08'`, which is `NULL` on every Fault node, so it returned **0** —
three times, and I reported it as a PASS each time. Measured after the correction:
`occurred_at > 06:50` → **18**, `created_at > 06:50` → **0**.

**This is the same defect class this session has been finding all day** — DL-94's teardown counting
the wrong rows, my own watcher blind to `ScanRun` keys — and it is worse here, because it was the
instrument being used to certify the system clean for Monday. A green that comes from querying a
field that does not exist is indistinguishable from a real green.

**Owed:** a fault-count helper that asserts the field it reads exists, rather than every caller
hand-rolling the property name. Until then, no audit should report a Fault count without showing a
non-zero control.

### Code-shaped fix packaged in S167

S167 adds `kernel.fault_query` as the single Fault timestamp read path; it reads
`occurred_at`, counts `FaultSuppression` volume, and raises if the timestamp property is missing
instead of returning zero. The deliberator fail-open path still upholds the affected order, but
`DeliberationRun.failed_open_reason` now records the captured exception class plus message, and the
new property is declared in the vocabulary pack. This does **not** change the fail-open policy, the
S166 buy gate, or the Anthropic account usage limit.

---

## DL-98 · The LLM veto finally ran — eleven minutes after the orders were already at the broker · status: FIXED (2026-08-08, S166 / [ADR-0022](decisions/0022-the-veto-gates-buys-never-exits.md), 0.89.07)

**The first production run in which the PM approved orders AND the deliberator reached a model.**
[DL-80](#) is **closed** by it: `LLMCall` went **25 → 164**, the 139 new calls all `claude-opus-5`
from `deliberator-proponent`/`-opponent`, and the `DeliberationRun` records
**`real_debate_count=18`, `failed_open_count=0`** with a real narrative (*"ABT: revise — both sides
argue figures absent from this packet…"*). The debate works.

🚨 **And it could not have vetoed anything.** Measured timestamps from the run's own lineage:

| | time (UTC) |
| --- | --- |
| `PMRun` written, 18 approved | 05:35:56 |
| **execution submitted 18 orders to the broker** | **05:36:22–05:36:32** |
| `DeliberationRun` written | **05:47:32** |
| last `LLMCall` of the debate | 05:51:53 |

The orders were accepted at Alpaca **~11 minutes before the deliberator finished**, and ~15 before
its last model call. The `DeliberationRun` that says *revise* refers to orders that were already
live.

**Why, and it is by design rather than by accident.** `_drop_vetoed`
([`agents/execution/poll.py:51-69`](../agents/execution/poll.py#L51)) drops `vetoed_tickers` when a
`DeliberationRun` is linked to the `PMRun`, and its own docstring states the fallback: *"No
DeliberationRun (the veto stage did not run) → the full set."* **Fail-open on absence.** In
graph-pull both agents poll independently, so "the veto has not run **yet**" and "the veto is not
deployed" are indistinguishable to execution — DL-57's shape, on the control path. The deliberator
is slow precisely because it is doing real work: 18 debates × multi-turn Opus.

**Why this was never seen before.** The fail-open policy is deliberate (S147 item 2: blocking a run
on an LLM outage blocks *exits*). It has been invisible because the PM approved **zero** orders on
every scheduled run since 07-31 — no orders to submit, nothing to debate, no race to lose. The
deadlock was hiding it.

**Not fixed here, and the fix is not obvious.** Making execution wait re-introduces exactly what
S147 rejected: an LLM outage stalling exits. Candidate directions, none chosen: a bounded wait that
applies to **buys only** (exits proceed, matching ADR-0017's asymmetry); the deliberator writing an
*intent-to-deliberate* marker at PMRun time so absence and not-yet become distinguishable; or moving
the veto ahead of the PM. Wants an ADR, not an inline patch.


### Fixed 2026-08-08 — the veto gates buys, never exits

[ADR-0022](decisions/0022-the-veto-gates-buys-never-exits.md) settles the policy; S166 implements it.
A PMRun carrying a `buy` is **left unconsumed** while its grace window is open, so the next poll
retries — no new state, and a restart resumes because the window is measured from the PMRun's own
`created_at`. A **sell-only** run never waits, which keeps S147's constraint exactly: an LLM outage
must never block an exit. Bound is `deliberation_grace_seconds` (default **900**, `0–3600`); at `0`
the old race is restored deliberately.

Fail-open survives — the grace expires and the run submits — but no longer silently: the
`ExecutionRun` carries `deliberation_status` (`applied`/`not_required`/`waiting`/`proceeded_unvetoed`)
as a queryable fact, and `proceeded_unvetoed` raises a `DeliberationGraceExpired` fault.

**Both plants observed failing first (DL-70):** restoring the race failed 3 tests; making exits wait
too — the S147 violation — failed 2, one of them a broker-stops test, so the exit path is guarded
from more than one direction.

🚨 **The in-process cascade needed an explicit opt-out, and finding that was the useful part.**
`orchestration/local_pipeline.py` runs the deliberation stage only when an LLM is configured, so with
none the harness would have waited for a veto that never comes — 18 tests failed until it was made
explicit. That is harness-only: production runs the deliberator as three container apps polling
independently, always deployed, which is exactly why the race was real rather than theoretical.

**No pack coupling:** `ExecutionRun` is **not** one of the five property-enforced labels
(`DeliberationRun`, `BrokerPositionSnapshot`, `Fill`, `LLMCall`, `Recommendation`), so
`deliberation_status` cannot trigger the S148 fail-closed stall and a deploy is an image-only retag.

---

## DL-97 · A second copy of the sector reason strings, kept alive only by the test that called it · status: FIXED (2026-08-08, `chore-one-sector-rejection`, 0.89.06)

**Found while splitting `risk.py`** ([DL-96](#)), reported then rather than folded in silently, and
fixed here on the operator's call.

`SectorBook.rejection` mapped a failing sector gate to `sector_name_count` /
`sector_concentration` — **an exact duplicate** of the mapping `risk.py` used via its own
`_sector_rejection` (now `position_gates.sector_rejection`). Two copies of the same reason strings,
either of which could be changed without the other.

🚨 **Nothing in production ever called it.** The only three call sites were in
`test_sector_cap.py`, which invoked it directly. So it was dead production code, and the coverage
gate could not tell: the method was **100 % covered** and had a passing test named after it. A
100 % floor measures whether a line ran, not whether anything but a test made it run — the DL-57
shape again (*didn't look* and *looked and found nothing* render identically).

**Why the duplicate existed rather than the caller using the method.** `risk.py` needs the sector
`GateOutcome`s *separately*, because an **approved** order carries them in its additive gate report.
`SectorBook.rejection` computed the outcomes internally and returned only the rejection, so the
caller could not reuse them — it called `book.outcomes(...)` and mapped the result itself. The
method was structurally unusable by its only real would-be caller.

**Fixed** by deleting it. The mapping now exists once, in `position_gates.sector_rejection`, and
`SectorBook` reports outcomes only — stated in its module docstring so the split does not re-merge.
`concentration.py` **174 → 144**, out of the 150-line warn band as a side effect.

**The test was re-pointed, not deleted.** `test_sector_rejection_maps_each_failing_outcome_to_its_reason`
keeps every prior assertion but runs them through `sector_rejection(book.outcomes(...))` — the
composition the PM actually executes. Proven live: swapping one reason string in `sector_rejection`
fails **5 tests**, where the same swap in the deleted method would have failed only its own.

**Road not taken.** Keeping the method and having `sector_rejection` delegate to it — rejected: it
would recompute `outcomes` a second time per order purely to preserve an API nothing uses.

---

## DL-96 · The PM's rejection precedence was unpinned, and a refactor is exactly when that changes · status: FIXED (2026-08-08, `chore-split-modules-before-the-block`, 0.89.05)

**Found while splitting `risk.py`** to clear the 200-line hard block. The split moved the
per-recommendation decision into `order_decision.py` unchanged, and the whole PM suite stayed green
— which proves less than it looks.

🚨 **A planted reorder — evaluating `reward_risk` *before* the sizing gates — passed all 86 PM
tests.** Under that reorder a recommendation failing both `max_positions` and `reward_risk` is
rejected as `reward_risk_below_min` instead of `max_positions`. Nothing objected.

**Why it matters more here than it would elsewhere.** The reason string is the operator-visible
output: it is the word on every `SKIP` line in the batch trace, and it is what S161 and S162 were
*about* — `max_positions` shadowing `cash_available` is the reason S161's sizing gate could not be
shown to have fired, and S162 exists to attach the rest of the evidence. The precedence is load-
bearing, and it was held only by the order two statements happened to appear in.

**The existing test that looked like coverage.** `test_2026_08_07_max_positions_rejection_keeps_cash_gate_failure`
pins `max_positions` over `cash_available` — but both live *inside* `position_rejection`'s own loop,
so it constrains that function's internal ordering and says nothing about the ordering of the
*stages* around it. A gate test one level too low reads exactly like one at the right level.

**Fixed** by `agents/portfolio_manager/tests/test_rejection_precedence.py`: sizing gates outrank
reward-risk, reward-risk outranks the sector cap, and the reason names one gate while the report
stays additive. The same planted reorder now fails 2 of 89.

**Road not taken.** Encoding the precedence as data (an ordered tuple of stages) — rejected for now:
it would make the order explicit but is a behaviour-shaped change to the decision path, and this
chore was scoped to move code without changing it. The tests pin the order either way, so the
refactor can be done later against a guard that already exists.

---

## DL-95 · The book cannot be sold: every share is reserved by its own resting stop · status: OPEN (found 2026-08-07 while executing the flatten chore)

**Found at the baseline step of [chore-flatten-and-resize](sprints/chore-flatten-and-resize.md), before
anything was changed.** The chore was packaged to flatten the book by raising
`exit_confidence_floor` above the highest held confidence. Measured against the live Alpaca paper
account first — and the flatten cannot execute.

### Measured 2026-08-07 04:45 UTC (read-only)

Ten positions, and **ten resting `gtc` sell stops, one per position, each for the full quantity**:

| | qty | `qty_available` | resting stop |
| --- | --- | --- | --- |
| ABT | 191 | **0** | sell 191 @ 100.24 |
| BAC | 503 | **0** | sell 503 @ 56.65 |
| BMY | 153 | **0** | sell 153 @ 62.34 |
| CSCO | 177 | **0** | sell 177 @ 106.78 |
| HPE | 229 | **0** | sell 229 @ 41.37 |
| MDT | 233 | **0** | sell 233 @ 82.26 |
| PYPL | 175 | **0** | sell 175 @ 53.81 |
| SCHW | 196 | **0** | sell 196 @ 97.10 |
| USB | 478 | **0** | sell 478 @ 59.47 |
| WFC | 348 | **0** | sell 348 @ 82.07 |

**`qty_available = 0` on all ten.** Alpaca reserves shares against open sell orders, so a full-exit
sell has no shares to sell. `shorting_enabled: True`, which is why this matters twice over.

### Why the pipeline does not handle it

`execute_pm_node` ([`poll.py:169-180`](../agents/execution/poll.py#L169)) runs in this order:

1. `reconcile_run_start` — snapshot
2. `reconcile_broker_stops` — **cancels only stops whose `position_ref` is no longer active**. The
   positions being sold are still active at this moment, so nothing is cancelled.
3. `place_broker_stops` — computes `sold_tickers` and **skips placing new** stops for them. It never
   cancels the existing one.
4. `run_submit` — submits the exits into a position with zero available shares.

**The gap is precise: `place_broker_stops` already knows exactly which tickers are being sold, and
uses that knowledge only to decline placing a stop — never to cancel the stop already resting.**

### This is not hypothetical, and it is not only about the flatten

The graph already carries the failure signature. Five `Fill` rows are `status=rejected` with
`HTTP Error 403`, three of them explicit:

```text
{"code":40310000,
 "existing_order_id":"fd1f1c2c-4911-4df5-b7a1-e2e9929a7341",
 "message":"potential wash trade detected. use complex orders",
 "reject_reason":"opposite side market/stop order exists"}
```

That instance is a *stop placement* colliding with an opposite-side order, not an exit — a different
path to the same root cause: **the system places resting stops and then does not account for them
when it next wants to trade the same name.** Two SCHW **buy** fills were rejected 403 the same way.

**Scope it honestly:** the exit-blocked-by-`qty_available` case is an inference from
`qty_available = 0`, not yet an observed rejection — no exit has been attempted since the stops were
placed (2026-07-28 → 08-04), because the analyst has returned `hold` throughout. The wash-trade
rejections above are observed. Both follow from the same unaccounted resting stop.

### Consequence: the pipeline is blocked in *both* directions

[DL-93](design-log.md)/S162 established it cannot **buy** — `available_for_buys = -105,748.50`, so
`cash_available` fails on every order. This entry establishes it cannot **sell** either: every share
is reserved. The deadlock is therefore not merely "the book is full"; it is **closed at both ends**,
and the flatten that was supposed to open it runs straight into the second wall.

### Decision

**The chore is blocked on a code fix; do not hand-cancel the stops.** Cancelling the ten stops
directly against the broker would clear `qty_available`, but the graph's `BrokerStopOrder` facts stay
active, and `place_broker_stops` skips any ticker in `active_broker_stop_refs(graph)` — so the
positions would be **unprotected while the graph believes they are protected**, which is worse than
the blockage. If the flatten then partly failed, we would hold unstopped positions and not know it.

**Fix shape (its own sprint, full cycle — this is Python):** in `execute_pm_node`, cancel the resting
stop for each `sold_ticker` *before* `run_submit`, recording the cancellation fact the way
`cancel_stop` already does, so broker and graph move together. `place_broker_stops` already computes
`sold_tickers`; the change is to act on it in both directions rather than one.

### Road not taken

- **`DELETE /v2/positions?cancel_orders=true`** — Alpaca will flatten and cancel related orders in one
  call. Rejected: it writes no lineage and bypasses `EXEC-IDN-01`, which is exactly the mechanism
  DL-93 already ruled out for hand-fired exits.
- **Hand-cancel the stops, then run the flatten through the pipeline.** Rejected above — it
  manufactures a graph/broker divergence in the *protection* layer, the one place where a silent
  divergence can cost real money.
- **Lower the stop thresholds out of the way instead of cancelling.** Rejected: it neither frees
  `qty_available` nor removes the opposite-side conflict, and it quietly disarms risk control.

---

## DL-95b · I cited Fill keys as broker keys, and the real risk was the one I skipped · status: DECIDED (2026-08-07)

**The S164 spec claimed production evidence it did not have.** It argued the attempt-chained stop key was safe because *“the rejected ABT stops are keyed `stop:5244d9de63d93691:ABT`, `#1`, `#2`”*. Those are **`Fill` node keys**. Measured on the graph, every one of them carries `broker_idempotency_key = stop:5244d9de63d93691:ABT` — the **base** key, no `#`. The graph-side attempt chain never reached Alpaca. **Alpaca had never seen a `#`-suffixed `client_order_id`.**

That mattered, because S164's `_place_stop` passes the chained key straight into `broker.submit_stop(key, ...)` as the `client_order_id`. Had Alpaca rejected the format, the replacement would have failed silently and the position stayed unprotected — exactly the defect S164 exists to fix, reintroduced one layer down.

**Resolved by measurement, not by watching.** The operator refused a “wait for it to break” plan: *“I do not know how to manage a KNOWN BUG.”* A bounded probe against the live paper account submitted a 1-share limit buy far from market with `client_order_id = stop:probe-s164:T#1` on a symbol outside the book (avoiding the wash-trade rule): **HTTP 200, `client_order_id` echoed verbatim, cancelled 204, zero residue.** The format is accepted. Precedent for a broker probe: the S97 functionality check.

**The lesson is narrower than “check your evidence”.** Both keys are called *the key* in conversation, and `broker_stop_order_key`’s own docstring says *“the shared graph key **and** broker client_order_id”* — which is true for stops and **false for the `Fill` attempt chain beside it**. Two identifiers, one name, one of them not what it appears. When a spec cites production evidence, cite the **field** that carries it, not the node key that resembles it.

---

## DL-100 · A provider switch that is four switches, and a deploy that silently unsets them · status: CLOSED by S169 (code-proven 2026-08-14; live proof owed at the next full `up`)

Both halves found by hand while executing `chore-openai-cutover` on 2026-08-08. Same defect class:
**configuration that silently does not do what the operator believes it does.** Neither raises.

**A — the switch is four switches.** `DELIBERATOR_LLM_PROVIDER=openai` alone is not a working
switch. `entrypoint.py:76` passes `model=settings.model_for_role(...)` explicitly, and
`defender_model` / `challenger_model` / `judge_model` each default to **`claude-opus-5`** — so
flipping only the provider sends an Anthropic model name to OpenAI. The cutover needed **four** env
vars on each of three containers. Worse than inconvenient: `role_models` is written onto the
`DeliberationRun` from those same tunables, so left unset the audit record would claim the order was
reviewed by `claude-opus-5` while the call went to OpenAI — the provenance claim DL-99 exists to
protect, quietly false.

**B — a full `up` discards operator-set configuration.** `deploy-agents.ps1` passes `--env-vars` on
`containerapp create`, which **replaces** the env set. Measured across one deploy, with a green
`[OK]` on every target:

| Setting | Before `up -Tag s169` | After | Default if unset |
| --- | --- | --- | --- |
| `SCANNER_CANDIDATE_CAP` | 25 | wiped | 5 |
| `PORTFOLIO_MANAGER_MAX_POSITION_PCT` | 0.01 | wiped | 0.10 |
| `PORTFOLIO_MANAGER_MAX_POSITIONS` | 60 | wiped | 10 |
| dispatcher cron | `30 22 * * 1-5` | `30 22 * * *` | script default |

The cron is the same bug twice: `$DispatcherCron` defaults to the daily literal, so S166's
weekday-only schedule silently reverted and would have fired an unintended weekend run that night.

**Why it is dangerous rather than annoying.** A run with defaults restored still *succeeds* — it
scans 5 candidates instead of 25 and sizes 10 % across 10 slots instead of 1 % across 60. A
materially different trading system, reporting `ACCEPTANCE PASS`. The only thing that caught it was
snapshotting the env by hand before deploying, because S161's closeout happened to mention a manual
restore. **Ruled out:** "remember to restore afterwards" — that is the process that already failed.

**Resolved by S169 (`0.90.10`, 2026-08-14).** **A** — the three model tunables now default to an
empty sentinel and resolve from `DEFAULT_MODEL` in `llm_factory.py`, next to `KEY_ENV`, so the
provider owns its own default and `DELIBERATOR_LLM_PROVIDER` is the whole switch; an explicit model
still wins. `role_models` reads through `model_for_role`, so the audit record names the **resolved**
model and can never be the sentinel — asserted on the written `DeliberationRun`, not on settings,
because a green settings object is what let this ship. **B** — operator tunables and the dispatcher
cron move into `orchestration/packs/trading_tunables.json`; `up` reads the live env of all 15 agents
and the job **before its first create** and refuses, naming every key it would drop, unless
`-DropEnv` acknowledges the removal. The `$DispatcherCron` literal is gone.

🪤 **What this does not establish.** No `up` has run. The refusal, the pack values and the
resolution are proven by unit tests and a parse-level harness against the committed pack — the live
half (tunables surviving a real `up`, re-read off the app rather than believed from the deploy's own
report — hardening row Q) is owed at the next full deploy. The three temporary
`DELIBERATOR_*_MODEL=gpt-5.5` overrides on the live deliberators must be dropped in that same deploy
(`-DropEnv`), or the fleet keeps proving the old path.

---

## DL-101 · The LLM layer is half in the substrate · status: OPEN (S170 packaged)

The **port and the ledger** are kernel: `kernel/llm.py` (the `LLMClient` protocol) and
`kernel/llm_ledger.py` (the append-only `LLMCall` node). Both model-calling agents genuinely route
through the ledger, so the *audit* path is already plumbing.

The **vendor adapters and provider selection are not**, and they are duplicated:
`agents/deliberator/llm_anthropic.py`, `llm_openai.py`, `llm_factory.py`, and a second
`AnthropicLLMClient` in `agents/operator/llm_anthropic.py`. The two Anthropic clients share a name,
a `ConfigurationError`, a constructor, the `importlib` SDK load and the empty-key guard, and differ
in **one method**: `complete()` is free-text for the deliberator, tool-use for the operator.

**The consequence that makes it a defect rather than untidiness.** S168 added the OpenAI fallback to
`llm_factory`, which only the deliberator has. The operator has no factory, no `llm_provider` and no
OpenAI client, so it can call Anthropic and nothing else — while the Anthropic key is usage-limited
until **2026-09-01**. "We have a vendor fallback" is true for one of two model-calling agents. And
`surfaces/dashboard/chat_binding.py:13` imports `agents.operator.llm_anthropic` directly, so a
surface is wired to a specific agent's vendor adapter and inherits the same single-vendor exposure.

**Not a pure file move:** free-text vs tool-use is a real difference in what the caller needs back.
Collapsing both under one name without preserving it would silently change what the operator
receives.

---

## DL-102 · The veto pairs a request with whatever reply is at the head of the queue · status: FIXED (S171, `0.90.01`, 2026-08-08 — correlation shipped and proven on cold peers)

**Measured on the deployed fleet**, `check-s169-openai-cutover`, 2026-08-08. The OpenAI cutover was
working — the proponent made **18 real `gpt-5.5` completions** and `role_models` correctly recorded
`gpt-5.5` for all three roles — yet the `DeliberationRun` came out `real_debate_count=0,
failed_open_count=18`, with a **Anthropic** usage-limit error as the fail-open reason.

The manager never read the proponent's answers. `peer_client.py:143` resolves a peer reply as:

```python
messages = receiver.receive_messages(max_message_count=1, ...)
raw = messages[0]
receiver.complete_message(raw)
```

**There is no `request_id` correlation.** It takes the head of the `deliberator-manager.reply`
subscription and treats it as the answer to the request it just sent. The subscription held **84
active messages**, oldest enqueued **05:51 UTC** (the earlier `check-s166` run, which failed all 18
orders on the Anthropic limit), newest **11:20 UTC** — this run's own proponent replies, which went
in and were never consumed. So the manager drained 5.5-hour-old error replies, one per ticker, ~2 s
apart, and failed open on every order while the live debate succeeded beside it.

🚨 **The error case is the benign one.** It raises and fails open. A stale *success* reply takes the
other branch — `DebateTurnReply.model_validate(reply.payload)` — and is accepted as a debate turn
**for a different ticker's order**. That is precisely the provenance guarantee the veto exists to
provide: "which model reviewed this order, and about what". A queue backlog turns it into a lie
without a fault, an error, or a failing gate.

**Mitigated, not fixed:** the 84 stale replies were drained after inspection (all were answers to
long-dead requests; the manager is the only consumer). With an empty queue a strictly sequential
manager pairs correctly *by accident*. The bug reopens the moment a backlog exists again — a timeout,
a crash mid-debate, a restart, or two managers.

**Ruled out:** raising `request_timeout_seconds` *as the fix*. In the poisoned run the manager was
not timing out; it was reading promptly and reading the wrong thing.

**The second half, found on the clean re-run — and it is what manufactures the backlog.** With the
queue empty (`check-s169-debate-2`), the first turn faulted at **11:50:07** with `no deliberator peer
reply received`. An idle peer blocks **5 s** in `receive` (`receive_timeout_seconds`) and then sleeps
**60 s** (`serve_loop.py:23`), while the manager waits **30 s** (`request_timeout_seconds`) — so a
**cold peer cannot answer inside the manager's window**. Once the peers were warm the debate ran
normally through all three roles, judge included (`deliberator-manager`, 11:51:20, `gpt-5.5`).

So the two defects feed each other: **every timed-out turn leaves the peer's late reply in the
subscription as an orphan**, and the missing correlation converts that orphan into the answer to a
later request. The 84 stale messages were not a historical accident — they were being produced
continuously, one per timeout. Fixing correlation alone yields a manager that correctly dead-letters
orphans and **still fails open on every cold start**, which is precisely the case the scheduled
22:30 UTC run hits, because the fleet sits at `minReplicas=0` until 22:25.

Both halves are packaged as [S171](sprints/sprint-171-a-reply-must-answer-its-own-request.md).

---

## DL-103 · The veto now works, and finishing takes longer than it is allowed · status: MITIGATED (grace 900 → 1800 s, 2026-08-08); the scaling problem is open

**Measured on `:s171`, run `check-s171-cold-start`, cold peers.** [S171](sprints/sprint-171-a-reply-must-answer-its-own-request.md)
did what it promised: `real_debate_count=**18**`, `failed_open_count=**0**`, `failed_open_reason`
empty, **zero deliberator faults, zero orphans dead-lettered** — against peers scaled from
`minReplicas=0`, the case that produced two fail-opens on `:s169` and the case the scheduled run
hits. The reply subscription ended at **0 active / 0 dead-letter**: the backlog no longer
regenerates.

🚨 **And the verdicts were still not applied.** `ExecutionRun.deliberation_status =
**proceeded_unvetoed**`, `submitted=18` — including the **15 tickers the veto had just decided to
veto**. The debate ran **15:13:34 → 15:29:17 = 943 s** against
`execution.deliberation_grace_seconds = **900 s**`. It overran by 43 s, `DeliberationGraceExpired`
fired, and execution proceeded. The gate behaved exactly as S166 designed it; the debate is simply
slower than its allowance.

**The cost is linear and now measurable:** 90 `LLMCall`s for 18 orders — `max_rounds=2` × 2 peers +
1 judge = **5 calls per order** — at a mean **10.6 s** per call, so **~53 s per approved order**.

**Why the earlier runs never showed this.** The poisoned run answered every turn instantly from the
stale backlog, so it "finished" in seconds; the `:s169` run reached only 16 real debates. Correct
correlation is what made the debate take its true duration. **Fixing the veto is what exposed that
the veto does not fit.**

**Mitigated, not fixed:** `deliberation_grace_seconds` raised **900 → 1800** on the `execution` app
(`le=3600`, so no code change), read back and verified. That buys ~2× headroom at 18 orders.

🚨 **It does not scale, and the numbers say so.** `PORTFOLIO_MANAGER_MAX_POSITIONS=60`, so a
run may approve far more than 18. At ~53 s per order the grace ceiling of **3600 s** is exhausted at
about **68 orders**, and 60 approvals would need **~3180 s** — inside the ceiling but only just, with
no margin for a slow vendor. Raising the grace also delays every buy by that long. The real options
are **parallelising peer turns** (they are issued strictly sequentially today), **cutting
`max_rounds` 2 → 1** (halves peer calls to 3 per order), or **deliberating only a bounded subset**.
Not chosen here — each changes what the veto *is*, so it wants its own sprint.

🟠 **Second thing the operator should know: the veto is aggressive.** It vetoed **15 of 18**
(`revise`) on this run and **10 of 18** on the previous one. Had the grace held, this run would have
placed **3 orders, not 18**. That is the veto working as designed, but it is a large behavioural
change and nobody has yet judged whether those `revise` verdicts are *right* — only that they are
real and attributable.

---

## DL-104 · The veto's verdicts were read for the first time: it is a good auditor and a bad gate · status: DECIDED (2026-08-10 — grace returned to 900 s for `sched-2026-08-10`)

[DL-103](#dl-103--the-veto-now-works-and-finishing-takes-longer-than-it-is-allowed) closed noting
that the veto's *quality* was unassessed — "only that they are real and attributable". This entry
assesses it, before the first run on which the veto could actually bind.

**The dataset is larger than STATE recorded.** Four `DeliberationRun`s carry real verdicts, not two.
Read directly off the live spine, read-only:

| Run | Vendor | Real debates | `revise` |
| --- | --- | --- | --- |
| `pm-run-3388c4f6…` 2026-08-08 05:47 | `claude-opus-5` | 18 | 15 |
| `pm-run-0c3c9324…` 2026-08-08 12:03 | `gpt-5.5` | 16 (+2 fail-open) | 10 |
| `pm-run-cbd26639…` 2026-08-08 15:29 | `gpt-5.5` | 18 | 15 |
| `pm-run-9b2a931e…` 2026-08-07 22:39 | `claude-opus-5` | 6 (+4 fail-open) | 5 |

**45 `revise` of 58 real debates — 78 %.** 🪤 The raw counts overstate agreement: a fail-open is
stored with `verdict: "uphold"` (`review_record.fail_open_review`), so the two contaminated runs
must have their fail-open tickers excluded before any rate is computed. Run D is 5 of **6**, not
5 of 10.

🚨 **The veto does not agree with itself.** `pm-run-0c3c9324` and `pm-run-cbd26639` are the **same
model, same prompt, same eighteen tickers, 3.5 hours apart**. They agree on **9 of 16** comparable
verdicts — **56 %**, on a binary verdict, so barely distinguishable from chance. Cross-vendor
agreement is *better* than same-vendor self-agreement: `claude-opus-5` vs `gpt-5.5` agree on
**12 of 17** shared tickers (**71 %**). Stated as measured-vs-assumed: the two `gpt-5.5` runs are
distinct PM runs, so their inputs are near-identical rather than provably identical.

**The grounds were checked against the code, not taken at face value. Three classes:**

🚨 **(1) The most-repeated objection is manufactured by the deliberator's own context builder.**
Six vetoes across *both* vendors cite an ATR contradiction — AMZN `3.07` vs `3.603`, BMY `2.50` vs
`2.939`, MSFT `2.74` vs `3.466`, T `2.91` vs `3.27`, KHC `2.93` vs `3.349`. There is no
contradiction. The analyst's `atr_pct` is a **14-period** ATR (`analyst/settings_indicators.py`,
`atr_period=14`); the figure in the gate line is computed by
`deliberator/context_pm.py::_atr_pct` over **every bar it was handed** — 42 bars, a 41-period ATR.
Two windows of the same series; they can never agree. Worse, `_atr_fragment` prints
`stop_pct vs ATR% -> PASSED/FAILED` **inside the `stop_vs_regime_volatility gate:` line**, while
the real gate is only `stop_pct <= base_stop_loss_pct` and `target_pct >= base_take_profit_pct`.
**The veto is shown a pass/fail no gate ever computed, on an input no gate ever used**, and reads
it as proof the risk check is unsound. The inversion is exact: it accuses the system of validating
stops against an understated volatility, using its own understated figure.

🚨 **(2) The sector-state objection is false.** SCHW: *"Financial Services deployed=0 and
existing_sector_names=0 even though the book already holds USB and WFC."* The book was **flat** —
USB and WFC were later approvals in the *same batch*, and `risk.py` does call
`book.record(item, cost)`, so the running `SectorBook` works as designed. `names=0` is correct for
whichever name is evaluated first. The deliberator receives one order's packet with no batch
context and **cannot distinguish "first in the deterministic order" from "the book is broken"**.
The related BAC/AVGO objection — *"the gates apply no name-correlation penalty"* — is a design
disagreement, not a defect: `max_names_per_sector` is exactly that penalty, and
`concentration.py`'s own docstring says so. The veto is arguing the cap should be tighter.

✅ **(3) One class is correct, and our gates cannot see it.** Both vendors, on ~7 tickers: *the
rationale cites SMA-200 distance while `history_bars=42`*. Verified — the summary string in
`analyst/domain/recommend.py` is **hardcoded** and always names SMA-200, while
`indicators.sma_distance` returns `None` below its period, so the leg is silently skipped. The
*scoring* is correct; the *stated rationale asserts an input that could not exist*. Underneath it
sits a real data gap: `lookback_days=260` exists explicitly *"so SMA200 can compute"*, we are
getting 42 bars, and `min_history_bars=2` waves that through without a murmur. USB's `$1.84`
sizing-headroom point (a market order clearing the 1 % cap only at the estimated price) is likewise
specific and fair.

**Conclusion: the veto is a genuinely useful auditor and a bad gate.** Roughly 2 of 15 grounds
survive checking, one whole class is self-inflicted by its own context builder, and it disagrees
with itself on 44 % of verdicts. Letting it bind would have cut ~18 orders to ~3 on mostly unsound
reasoning, and cost another night of the selection data [DL-93](#dl-93) names as the object under
test.

**DECISION (operator, 2026-08-10): `EXECUTION_DELIBERATION_GRACE_SECONDS` returned 1800 → 900** on
the `execution` app. At a measured 943 s the debate overruns, `DeliberationGraceExpired` fires, and
buys proceed — the veto stays advisory for `sched-2026-08-10` while its grounds are repaired.
**Verified, not assumed:** grace read back at `900`; **7/7 env vars survived** the update
(diffed before/after — the DL-100 trap); image still `:s171`; `minReplicas=0` with 1 KEDA rule;
`execution--0000069` the sole active revision, `Healthy`, Single revision mode; and the tunables
DL-100 previously wiped re-checked untouched on their own apps — `SCANNER_CANDIDATE_CAP=25`,
`MAX_POSITION_PCT=0.01`, `MAX_POSITIONS=60`, `dispatcher-cron` `30 22 * * 1-5` on `:s171`.

🟠 **The road not taken, and why.** *Let it bind for one more sample* — rejected: it spends a
night of selection data to re-measure grounds already measured unsound. *Add a real advisory
switch* — the honest fix, but it is code in `execution`, the highest-risk agent, hours before a
run; `deliberation_grace_seconds` is the **only** lever that exists today
(`execution/settings.py`), so a grace that expires is the sole no-code path. 🚨 **Name the cost
plainly: this uses a fault as a feature.** Every run in this state writes a
`DeliberationGraceExpired` fault that is truthful but not *informative* — it says the debate was
slow, not that we chose to ignore it. That is acceptable for one run and corrosive as a standing
posture, because it trains the operator to read a real fault as noise.

**Owed, in priority order:** (a) delete the invented ATR fragment from the deliberator's context,
or label it honestly as the deliberator's own long-window figure and stop rendering a `PASSED`;
(b) give the veto batch context, or stop it reasoning about portfolio state it cannot see;
(c) fix the analyst's hardcoded SMA-200 rationale and decide whether 42 bars is acceptable when
`lookback_days=260` promises ~180; (d) a real advisory/binding switch, so *advisory* is a declared
posture rather than a grace that happens to expire; (e) reproducibility is the open question a
verdict-quality gate would have to answer — 56 % self-agreement is the number to beat.

---

## DL-105 · The deliberation system does not scale, and the constraint is wall clock, not cost · status: OPEN (S172/S173 packaged; the advisory-vs-binding fork deferred to an ADR)

Opened 2026-08-11 by the operator, asking whether two Anthropic APIs — a multi-agent conversation
surface and the Message Batches API — address the deliberator's scaling problem. Answering it first
required establishing *which* resource the system is actually short of.

**The constraint was measured, not assumed.** Read off the `LLMCall` ledger for `sched-2026-08-10`:

| | |
| --- | --- |
| Calls | **90** — 18 manager + 36 proponent + 36 opponent, i.e. 5 per order × 18 orders |
| Tokens | **91,201 in / 14,820 out** |
| Per-call latency | mean **11.4 s**, p90 **16.4 s**, max **23.0 s** |
| Span, first call → last | **1,136 s** (22:41:00 → 22:59:56 UTC) |
| Sum of per-call latency | **1,022 s** |

🚨 **Sum-of-latency ÷ span = 0.90.** For ninety per cent of the wall clock there is exactly one call
in flight. The debate is serial end to end and the remaining ~114 s is bus round-trip plus graph
writes. Three independent serializations, each confirmed against the code or the live fleet rather
than inferred:

1. [`agents/deliberator/poll.py:64`](../agents/deliberator/poll.py#L64) is a plain synchronous
   `for intent in order_set.approved:`.
2. Rounds within one order are inherently sequential (proponent → opponent → … → judge).
3. All three deliberator apps run `minReplicas=0, maxReplicas=1` — so even a concurrent manager
   could not fan out.

🟠 **Cost is not the constraint, by two orders of magnitude.** 91 k in / 15 k out priced at Claude
Opus 5 list rates is **$0.83 per run**, ~$216/yr at 260 sessions. The Batch API's 50 % discount would
save **$0.41 a run**. Any argument for batching that rests on price is arguing about $107 a year.

**The fork this exposes.** The two candidate answers are not competing implementations of one plan;
they follow from opposite decisions about what the veto *is*:

| If the veto is… | The answer is | Because |
| --- | --- | --- |
| **an auditor, permanently** ([DL-104](#dl-104)'s own finding) | the **Batch API** | An auditor never has to finish before orders go out. Submitting the day's debates as one batch does not optimise the scaling table — it **deletes it**: no grace window, no `le=3600` ceiling, no `DeliberationGraceExpired` fault-used-as-a-feature, and identical behaviour at 18 orders or 500 |
| **something that may bind** | **concurrency** (S172) | A batch cannot gate what has already been submitted. Fan-out across independent orders is the only path to a veto that finishes inside a grace |

🪤 **The fork cannot be decided today, and deciding it early is the trap.** DL-104 (a)–(c) established
that the veto's grounds are partly manufactured by its own context builder, so a decision to make it
advisory *forever* would be taken on a contaminated sample. Sequence: repair the grounds → measure
reproducibility (S173) → then write the ADR. Recorded here so the fork is not silently resolved by
whichever sprint lands first.

**Where each API actually lands.**

- **Message Batches** — the right tool for a *different* problem than the one it was proposed for.
  Up to 100 k requests per batch, results keyed by `custom_id`, most complete inside an hour, 50 %
  off. That is a precise fit for the **verdict-quality gate** DL-104 (e) leaves open: thousands of
  replayed debates, no latency budget at all, and the same machinery serves the ADR-0010 prompt eval
  set. Packaged as **S173**. It is *not* a fix for the live path unless the fork above resolves to
  auditor-forever.
- **Multi-agent conversation (Managed Agents)** — a genuine architectural option and an **ADR, not a
  sprint**. The mapping is clean (coordinator = manager, roster = proponent/opponent, threads run
  parallel in one session with caching and compaction built in), but Anthropic hosts the agent loop
  and the container, which collides with three locked decisions: container-per-agent (LOCKED
  2026-06-18), [ADR-0012](decisions/0012-platform-domain-separation.md)'s
  platform/pack wall, and DL-36's master-as-sole-Key-Vault-accessor. The parallelism it buys is
  available in-process for a fraction of the change.
- 🪤 **Both are Anthropic-only, and the deliberator is deliberately on `gpt-5.5` until 2026-09-01**
  ([DL-99](#dl-99)). Either path is gated on that date or on resolving the key limit — the same
  date S170 already carries.

**Three adapter findings, discovered while checking the above.** None were being looked for; all
three change the lever list.

1. 🚨 **`effort` is inert on the deployed fleet.**
   [`llm_openai.py:43`](../agents/deliberator/llm_openai.py#L43) assigns `self.effort` and
   `complete()` never sends it. The tunable is registered, is visible to the operator, reads as live,
   and does nothing on `gpt-5.5`. Same class as DL-63's inert reasoning knob.
2. 🚨 **`effort="max"` with `max_tokens=4096` is a documented misconfiguration on Claude Opus 5.**
   Thinking and answer share that one budget, and Anthropic's guidance at `max` effort is to start at
   **64 K**. The tunable is hard-capped `le=4096`, so it cannot be raised without a code change.
   **Stated as a candidate, not a finding:** a verdict truncated or rushed under that cap is a
   plausible contributor to the **56 %** self-agreement DL-104 (e) wants explained — S173 is what
   would settle it.
3. 🟠 **No prompt caching and no structured outputs.** Every one of the 5 calls per order re-sends the
   full prefix at full price, and both adapters do `del tool_schema` — the verdict is parsed out of
   free text rather than schema-guaranteed.

**Amendment, same day — the lever order, once `effort` was made to exist.** Wiring the tunable
(`0.90.02`) made the two free levers measurable for the first time, which changes the ranking. Try
them in ascending order of what they cost, and stop at the first that fits:

| Lever | What it costs | 100 orders, serial |
| --- | --- | --- |
| **`effort` down from `max`** | nothing — no semantic change, tunable only | unmeasurable until `0.90.02`; **this is the open question** |
| **`max_rounds` 2 → 1** | 🚨 **the second round of the debate** | ~3,420 s — fits the 3,600 s ceiling with 5 % headroom, too tight to rely on |
| **S172 concurrency** | a sprint, a new tunable, a thread pool, deterministic reassembly, a replica bump, a deploy | ≈ N/K |

🚨 **`max_rounds` is not the free lever it looks like.** Its own `why` reads *"Manager-driven debate
must show more than one round in live proof"* (DL-42/S166). One round is one assertion, one rebuttal,
one verdict — **cutting the artefact under test to buy wall clock.** Defensible while the veto is
advisory and its grounds are unsound; it is a recorded decision, not a knob.

🟠 **S172 should therefore be specced-and-unstarted, not queued.** Its trigger, written down: *build
it when the measured serial cost at the target funnel width still exceeds the grace after the two
tunables have been swept.* Building it first buys concurrency machinery for the *"may bind"* branch
of a fork this entry deliberately defers — see the fork table above. 🪤 The sweep needs the fleet
retagged off `:s171` to pick up `0.90.02`, and a full `up` still discards operator env until S169
lands ([DL-100](#dl-100)).

🟠 **The road not taken.**

- *Batch the live debate for the cost saving* — rejected on the measurement: $0.41 a run, while
  trading away the only resource that is actually scarce. If batching is adopted it must be for the
  architectural reason (the veto is declared advisory), never the price.
- *Adopt Managed Agents multiagent to get parallelism* — rejected as the **first** move, not on
  merit. It buys concurrency we can have with `asyncio.gather` plus a replica bump, and pays for it
  by reopening three locked architectural decisions. Revisit as an ADR if the deliberator ever needs
  hosted orchestration for its own sake.
- *A single batched verdict — one call scoring all orders at once* — previously ruled out and still
  ruled out: 5 calls total, but it stops being a debate, and the debate is the artefact under test.
- *Deliberate only marginal orders* — ruled out: the veto's one genuinely sound catch (the SMA-200
  rationale, DL-104 class 3) landed on an ordinary order, not a marginal one.

---

## DL-106 · The image tag left the `sNNN` scheme, and a name stopped identifying a commit · status: DECIDED (2026-08-12)

**What happened.** The 2026-08-12 deploy of `0.90.02` was tagged **`v0.90.02`** rather than `sNNN`,
because the change was a **chore** with no sprint number of its own and `s172` is packaged but
unbuilt. The cost showed up within the hour: `v0.90.02` names **two different commits** — the git
tag `v0.90.02` points at `de3c071`, while the image was built from `ffdbaf1`, two docs commits
later. `sNNN` had never been able to collide that way, because it was only ever an image tag.

**Decision — image tags stay sprint-shaped.** A deploy that carries no sprint of its own
**suffixes the sprint it follows**: `s171a`, `s171b`. That sorts after its parent, cannot be
misread as a sprint that has not shipped, and shares no namespace with git tags. Never a version
string, never `latest`. Redeployed the same day as **`s171a`** from `e49349c` — 17 targets
verified, `DeployRecord deploy:2026-08-12T07:52:49…:s171a:e49349cb`.

**Why the `DeployRecord` SHA is not a sufficient answer.** It carries the full SHA and stays
authoritative, so traceability was never actually lost — that is exactly why this is easy to wave
through. But the *name* is what a human reads on the status board and in `az` output, and a name
that needs a graph lookup to disambiguate is [DL-46](#dl-46)'s currency failure in slow motion:
the entire point of the tag is that *being behind* is visible **at a glance**.

🟠 **The road not taken.**

- *Keep version-shaped tags and lean on the SHA* — rejected on the glance test above. It shipped
  for one afternoon and worked; it also put two different objects under one name across two
  systems that are read side by side.
- *Use the next sprint number (`s172`)* — rejected as a traceability lie. S172 is packaged and
  unbuilt; naming an image after it makes the board assert a sprint has shipped.
- *Tag by commit SHA* — rejected: unambiguous and unreadable. The board is the artefact, and
  `s171a` tells an operator where they are without a lookup.

---

## DL-107 - S174 carries declared indicator history on the RunRequest - status: DECIDED (2026-08-12)

**Decision.** The dispatcher stamps `RunRequest.lookback_days` from the analyst's declared
indicator settings, plus `RunRequest.required_history_bars` from the same declarations. The
calendar window is derived from the NYSE session calendar for the run date, plus the provider's
existing `max_staleness_days` session buffer, so the value is large enough to contain the declared
bar count even when today's daily bar is not yet published. It is not a copy of the old 260-day
analyst lookback. The provider graph-pull path refuses to ingest a run request whose stamped
lookback cannot cover the stamped bar requirement.

This keeps the cross-agent contract on the existing typed queue item: the dispatcher already chooses
the run universe, the provider already reads the run request, and the analyst's settings remain the
single source that declares the indicator windows. The route is still the recommended RunRequest
carrier; the self-maintaining calculation is local to the dispatcher so the provider does not import
analyst policy.

Short-history evidence rides inside the existing `Recommendation.quant_metrics` map as
`*_missing_bars` entries. `Recommendation.quant_metrics` is already in the vocabulary pack's
property allow-list, so S174 does not add a new top-level `Recommendation` property and does not
move the pack.

**Image follow-up.** The RunRequest carrier means the scheduled dispatcher image must carry the
same minimal analyst/provider settings modules used by `orchestration.start` to derive the stamped
window. Copying those settings modules into the slim dispatcher image was chosen over moving the
history calculation into provider-owned defaults: the latter would reintroduce duplicated indicator
policy, while the former keeps the Dockerfile aligned with the chosen contract. The follow-up also
copies `orchestration/history_window.py`, because `start.py` imports the new calendar conversion
helper and the dispatcher image deliberately does not copy the full orchestration package. It also
keeps `agents.analyst` package exports lazy so importing `agents.analyst.history_requirements` does
not load the full boundary agent tree in the dispatcher image. The lazy initializer deliberately has
no `__all__`; CodeQL treats a lazy `__all__ = ["AnalystAgent"]` as `py/undefined-export`, while
explicit `from agents.analyst import AnalystAgent` still resolves through `__getattr__`.

**Security follow-up.** The first pushed S174 follow-up failed the remote Security Findings gate
because CodeQL reported `py/unsafe-cyclic-import` across `history_requirements.py` and
`settings.py`. Replacing the `TYPE_CHECKING` import of `AnalystSettings` with a local structural
protocol preserves type precision without creating an analyzer-visible cycle.

**Rejected routes.**

- *Put required history in the pack* - rejected because it creates a second durable place for the
  same number. The pack should validate graph shape, not become a copy of analyst indicator policy.
- *Add a provider `tunable()` set to 260* - rejected because it duplicates the analyst value by
  construction. It would fix today's SMA-200 miss while preserving the drift mechanism that caused
  the bug.
- *Have the provider derive lookback from the largest indicator period* - rejected because the
  provider does not own indicator policy. The dispatcher can perform the session-calendar
  calculation before the run crosses the agent boundary; provider-side derivation would either
  import analyst code or recreate analyst policy in provider.
- *Add a new top-level `Recommendation` property for missing indicators* - rejected because
  `Recommendation` is property-enforced. That would move
  `orchestration/packs/trading_graph_vocabulary.json` and force a full deploy path still blocked by
  the S169 operator-env gap.

---

## DL-109 - S176 lets only partial broker fills complete - status: DECIDED (2026-08-13)

**Decision.** A broker-observed `Fill.broker_status` may advance only from `partial` to `filled`.
That single transition also lets the broker completion replace the tied `broker_price_cents`,
`broker_status_refreshed_at`, and `realized_pnl_cents` values, because the first two describe the
current broker fact and the PnL conclusion for a completed-after-partial sell must be based on the
final completed price. The ordinary graph merge rule remains append-only; the exception is a
property conflict allowlist gated by `existing.broker_status == "partial"` and
`incoming.broker_status == "filled"`.

This keeps S154's terminal-refresh boundary intact: `filled` and `rejected` fills are still skipped
before a broker read can append another status fact or rewrite the `Fill`. The completion still
appends a `BrokerOrderStatus` observation, so the observation history remains reconstructable while
the current `Fill` fields stop lying.

**Rejected routes.**

- *Terminal-status guard* - rejected as the implementation rule because it is broader than the
  measured defect. It says every non-terminal state can update; S176 needs exactly
  `partial -> filled`, and an explicit transition set is easier to plant against.
- *Append a new node per observation and derive a read model* - rejected for this sprint because it
  changes every downstream reader that currently consumes `Fill.broker_status` and
  `Fill.broker_price_cents`. It remains the purer long-term model if more broker-state transitions
  need to become current-state projections.
- *Remove the write-once guard wholesale* - rejected because `Fill` is protected production broker
  evidence. Terminal rewrites (`filled -> partial`, `rejected -> filled`) must stay refused.

---

## DL-110 - A code-scanning alert raised on `main` cannot be cleared from a branch - status: DECIDED (2026-08-17)

**The failure.** Four consecutive `Security Findings` runs on `main` failed (`31874097513`,
`31874121784`, `31874756644`, `31874771431`), all on the gate step, all for one alert: CodeQL
`py/mismatched-multiple-assignment` #177, error severity, raised on `main` at 07:38 UTC on
2026-08-15 against `agents/portfolio_manager/tests/test_sector_evidence_labels.py:87`. Error-level
is exactly what `--fail-on-code-scanning-error` blocks, and it was not in the baseline, so every
push after S177 merged failed - including four docs-only commits that touched no Python at all.

**Why it fired.** `SectorBook.outcomes()` returns `()` when the ticker has no sector, so its return
type spans lengths 0 and 2. The test unpacked the call directly into two names, and CodeQL reports
the empty-tuple branch as a runtime unpack error. The test is not actually reachable on that branch
(its `SectorBook` knows `AVGO`), but the analyzer cannot see that, and the shape it objects to is
genuinely fragile.

**Decision.** Fix the test: bind the call to `outcomes`, assert `len(outcomes) == 2`, then take the
two elements by index. The length is now proven in the test rather than assumed by its syntax, and
the analyzer sees a two-element right-hand side. Test-only, so **no version bump** - it ships no
package behaviour (precedent: `74bdd7c`).

**The discovered constraint that matters.** `codeql.yml` runs on push to `main` and on PRs to
`main`; `security-findings.yml` runs on push to **every** branch. So an alert raised on `main` stays
open, and fails the gate on every branch, until the fix is analysed **on `main`**. A branch cannot
turn it green - the fix branch's own gate run fails on the same stale alert. The rule "never merge a
branch you have not seen go green" has no path through this: the only exits are merge-then-verify or
dismissing the alert. Merge-then-verify was chosen, with the proof deferred to `main`: CodeQL
re-analyses `main`, alert #177 closes, and a `Security Findings` run on `main` is confirmed green
afterwards. The green claim belongs to that run, not to the merge.

**Why it took two days to name.** The gate step writes its report to the job summary and prints
**nothing** to stdout, so all four failed runs showed a bare `Process completed with exit code 1`.
The alert was identified by running the toolset locally against the live alert list, which printed
`New policy violations: 1` and the offending row. A failure that names nothing in its own log is
why a red gate can sit unexplained; worth a follow-up step that echoes the violating rows.

**Proven, not assumed.** `make ci` exit 0 (2302 passed / 6 skipped / 100.00 %); remote CI green on
the branch; alert #177 state `fixed` after CodeQL ran on `main`; `Security Findings` re-run green on
`21a5e81`; `make gate-ran` `GATE PROVEN` for `21a5e81`, matching `git rev-parse HEAD`.

**Rejected routes.**

- *Dismiss alert #177 with a reason* - rejected. It is the sanctioned acceptance path, but this
  finding points at a real fragility in the test, and accepting it would have left the pattern in
  place for the next unpack of a variable-length return.
- *Re-baseline* - rejected for the same reason, and because the baseline exists for accepted
  standing findings, not for clearing today's inbox.
- *Make `outcomes()` always return two outcomes* - rejected. The empty return is the meaningful
  "this ticker has no sector, there is nothing to gate" answer; widening it to satisfy an analyzer
  would put a fake gate outcome into production evidence.
- *Give `collect` a `--ref` so the gate measures the pushed branch* - rejected here, and noted as a
  real option for later. It would have let this branch go green on its own, but CodeQL does not run
  on branches at all, so a ref-scoped query would find no alerts and the gate would pass by absence
  of data - a weaker gate, not an earlier one.

---

---

## DL-111 - Divergence-flag severity follows persistence, not the adoption outcome - status: DECIDED (2026-08-18)

**The problem.** `healthy` had been `false` continuously since 2026-07-08. Measured 2026-08-18 on
the live spine: 46 unresolved `critical` Flags, 45 of them `Broker position divergence at run
start`. The flag is written at run start, *before* reconciliation adopts broker truth, so it
describes an operation that is about to succeed and then demands human attention for it. A signal
that cannot change carries no information.

**What S178 recommended, and why it does not work.** The spec's decision 1 was **severity follows
the adoption outcome**: adopted -> `info`/`warn`, unadopted -> `critical`. Measured while
implementing: **the outcome is not knowable where the flag is written.** Run-start reconciliation
lives in the execution agent (`agents/execution/reconciliation.py`); adoption of broker truth into
`Position` nodes happens in the **monitor** (`agents/monitor/reconcile.py:117`), a different agent
and a later stage. Agents never import agents, so execution cannot ask whether adoption succeeded
at the moment it writes the flag. The recommendation was unimplementable as written.

**Decision. Persistence is the observable proxy for the outcome.** A divergence seen for the first
time is a `warn` - reconciliation is about to adopt it, and it must not pin `healthy` to false. The
**same divergence still present at the next run start** was demonstrably not adopted, and is
escalated to `critical`. A divergence that has gone is retired by appending a `FlagResolution`. All
of it is decidable inside the execution agent, from graph state alone.

This requires the `subject_ref` to identify the *divergence*, not the snapshot. It was
`broker-position-divergence:{snapshot.key}` - and `snapshot.key` embeds a per-run ISO timestamp, so
the dedupe guard never fired across runs and each day minted a unique unresolvable flag. It is now
`broker-position-divergence:{kind}:{ticker}`, stable across runs, which is what makes both the
dedupe and the persistence check possible.

**Ruled out.**

- *Auto-resolve after adoption* (raise `critical`, clear it on the next clean run) - built first,
  then discarded. It is S178's own rejected option and the rejection is right: an adopted
  divergence still reads `critical` for a full day, so `healthy` stays false for normal operation.
- *Severity follows the adoption outcome* - S178's recommendation. Ruled out as **unimplementable**
  at the flag's write site, per the measurement above. Moving the flag write into the monitor was
  considered and rejected: DL-44 lineage belongs with the broker boundary, which is execution's
  (EXEC-IDN-03).
- *Stop raising the flag* - destroys the DL-44 lineage record, which is the point of having it.

**The legacy backlog is swept separately, not by a run.** Pre-S178 flags carry snapshot-keyed
subjects that can never match a live divergence. `_retire_absent` deliberately skips them, and
`scripts/sweep_divergence_flags.py` retires them as one audited, append-only action with
before/after counts. Letting a run silently clear 45 historical flags as a side effect would have
been the same "fix it by editing the graph" move DL-44 prohibits, one level removed.
