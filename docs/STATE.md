# Project State

**Last updated:** 2026-08-04 11:25 AEST · **Version:** 0.86.01 · **🟢 `sched-2026-08-03` RAN CLEAN AND S154 IS NOW PROVEN IN PRODUCTION — the DL-80 test did not happen, and for once that is not a failure.** Traced 2026-08-04: **8/8 stages**, **zero `Fault`s** since 20:00 UTC, provider **100/100** with no degraded notes, `position_sync status=fresh`. A genuine **no-trade day** — all 10 analyst names returned `hold` (conf 0.60–0.68), PM `approved=0` (`hold_recommendation` ×10), execution `submitted=0`, monitor `closes=0`. **S154's terminal-status selector is proven on the live spine:** `BrokerOrderStatus` writes per run fell **203 (07-31) → 19**, and **19 is exactly the number of fills whose `broker_status` is still non-terminal** (`filled` 24 / `rejected` 16 / unset 19) — not merely "fewer", the *right* number, which is what makes it proof rather than an encouraging sign. **The deliberator's transport worked this time:** it consumed the `PMRun` and wrote its artifact at 22:39:36 with **no `EntityPath` fault** — independent corroboration of the correction below that the 08-02 trigger was the half-failed deploy, not bundle content. **But the debate still has not run.** The artifact reads `debates={}`, `verdicts={}`, `narrative='No PM-approved orders required deliberation.'`, and **`LLMCall` is still frozen at 25 calls, all `claude-sonnet-4-6`, newest 2026-07-15 — zero new model calls.** **DL-80 stays open:** a full-hold day gives the veto nothing to veto, so the plumbing got its first clean pass and the *debate* — the API key, the model call, the peer round trip — remains unproven. It needs a day on which the PM approves an order. 🟠 **`ACCEPTANCE FAIL`, and it is a deploy gap rather than a defect:** `deliberation.debate_coverage: MISSING` / `deliberation.failed_open_count: MISSING`, because the fleet is on `:s155` and last night's artifact carries the **pre-S158 property set**, so the S158 view reads `None` and reports MISSING. **Checked rather than assumed:** `_coverage` returns `1.0` when `reviewed == 0` (`orchestration/packs/trading_deliberation_view.py`), so this exact no-trade shape **passes** once S158 is deployed — but **every run FAILs the gate until the retag**, which is now the binding reason to do it. Retag packaged as [chore-deploy-s158](sprints/chore-deploy-s158.md); **images exist and are green** (`build-images` succeeded on the S158 merge `8be1570`, 2026-08-03 07:46 UTC), so this is shippable and not merely mergeable — the DL-84 lesson. · **🔴 THE LLM VETO RAN IN PRODUCTION FOR THE FIRST TIME AND NEVER REACHED A MODEL — AND THE GATE WENT GREEN.** Found 2026-08-03 while checking a routine calendar skip. On 2026-08-02 08:01 UTC the deliberator came up on `:s155` and **`DeliberationRun` went 0 → 23** — DL-80's headline number moved — but every one reads `verdict=uphold`, `turns=()`, `transcript=()`, `rationale='llm unavailable (fail-open)'`, and the `LLMCall` ledger is **unchanged at 25 calls, all `claude-sonnet-4-6`, newest 2026-07-15**. **Zero new model calls.** The `claude-opus-5` default was correctly in place; the call never happened. **Cause, from the one `Fault` written that minute:** `deliberator-manager` / `agents.deliberator.poll` / `review_pm_node` → `ValueError: The topic name provided does not match the EntityPath`. The manager must send to two peer topics; S133 gave each target an entity-scoped SAS string plus a per-topic bundle, and `connection_string_for_topic()` **silently returned the primary** when a topic was missing from that bundle. The namespace side is correct — both peer topics carry the `ta-deliberator-manager` rule and the bundle secret exists and is delivered — so this is bundle *content*, not provisioning. 🟠 **Worse than the original DL-80, and that is the lesson.** Before S153 deliberation was absent and the gate could not see it; now it is **present, green and inert** — the stage produces an artifact, so S153's declared-stage check passes, and the artifact's own contents record the failure. DL-57 one layer deeper. **The append-only store also permanently consumed all 23 `PMRun`s** — a silent failure spent the backlog, and they cannot be re-deliberated. **🟢 S158 IS SHIPPED (`v0.86.01`, merge `8be1570`)** — a configured bundle that does not cover a topic now raises `BusConfigError` instead of falling back; the manager **preflights both peer topics before consuming a `PMRun`** (inert and loud, never productive and wrong); `DeliberationRun` records **`real_debate_count` / `failed_open_count` / `failed_open_tickers`** as queryable facts instead of a rationale substring; and acceptance **FAILs** an all-fail-open or mixed run. **Fail-open policy is deliberately unchanged** (S147 item 2 — blocking a run on an LLM outage blocks *exits*). Deliberator law coverage **0 → 4 / 48**. Verified independently before merge: `make ci` **2097 passed / 5 skipped / 100.00 %**, four jobs green on tip `c145e5e` by `headSha`, and each shipped behaviour watched rejecting a hand-planted violation. 🟠 **Planning review found ADR-0021's own shape on the first sprint after the ADR:** `DLIB-OUT-01` requires one run per `PMRun` **linked by `DELIBERATED_BY`**; the summary dropped the linkage conjunct and the cited test asserted the count but never the edge — and **the S156 gate passed it**, because a citation gate cannot see whether a test covers the clause *as written*. Fixed rather than demoted (the edge is written). **Summary-vs-clause fidelity remains a human step.** **🟠 CORRECTION, 2026-08-03 — the Key Vault repair I named as owed does not exist; the transport is already correct.** Verified end-to-end against live Azure: the bundle in `trading-agents-kv` carries **all three** topics with matching `EntityPath`s (`deliberator-{manager.reply, proponent.requests, opponent.requests}`), was created **2026-08-02T05:13 UTC — three hours before the 08:01 fault**, and the value the **running app** holds is identical. Both peers hold their own requests topic plus the manager's reply topic, so the full round trip is wired. All three roles are granted `ANTHROPIC_API_KEY` in `trading_secrets.json`. **So the trigger was not bundle content — it was the half-failed first deploy run.** In that window the env/secret step had not completed (the same window that left `GRAPH_VOCABULARY_B64` absent), so `connection_strings_json` was `None`, `connection_string_for_topic` fell back to the entity-scoped primary, and the send raised the `EntityPath` mismatch. The second run closed it at 08:38. **The mechanism I diagnosed was right; the trigger was not.** **What this changed:** nothing was owed before that night, and the 22:30 UTC run was a genuine DL-80 test — correct transport, correct grants, on `:s155`. **✅ IT RAN AND THE TRANSPORT HELD** (lead entry): no `EntityPath` fault, the `PMRun` consumed cleanly. **But the test was inconclusive by luck of the calendar** — the PM approved zero orders, so there was nothing to debate. **Scope it honestly: configuration is verified, a working debate is not.** The API key's validity, the model call and the peer round trip are **still unproven**, and the ledger is **still frozen at 25 calls / newest 2026-07-15**. Watch the next run in which PM `approved>0` for a `DeliberationRun` with a **non-empty transcript** and a **`claude-opus-5` `LLMCall` dated after 2026-08-02**. **The retag is demoted, not cancelled:** S158 is insurance so the *next* transient config failure is loud and leaves the backlog unconsumed, rather than spending 23 `PMRun`s silently. 🚨 **When it happens, the deploy must re-inject and read back `GRAPH_VOCABULARY_B64`** — `DeliberationRun` is one of four property-enforced labels and S158 added three props to it, so a stale pack means `VocabularyError` fail-closed on the first write (S148 pattern). · **🟢 This morning's run was a correct no-op.** `dispatcher-cron` fired 2026-08-02 22:30 UTC and `Succeeded`; no `RunRequest` was written because the as-of was a **Sunday**. Live spine confirms it — 23 `RunRequest` nodes, newest still `sched-2026-07-31`. Calendar gate working. · **🟢 S156 IS SHIPPED (`v0.86.00`, merge `23ae35f`) — the law book's own proof is now checked by `make ci`, and the honest number is 252 / 653.** `conventions.md` §3 has always said a clause is green *iff a passing test cites its ID in its docstring*. **Nothing checked it.** `scripts/check_law_coverage.py` now does, as a tenth gate step, with a `gate_selftest` can-fail case so the gate has been **observed rejecting** rather than assumed to work. Of **284** rows marked 🟩, **10 cited a test function that exists nowhere** (several deleted when ADR-0017 retired `execute_close` and the monitor's exit authoring — the greens pointing at them simply stayed) and **19 cited a live test whose docstring never named the clause**. All 29 adjudicated in a per-row table with evidence: **7 kept, 22 demoted**. 🟠 **The planning review caught the sprint reintroducing its own defect, and that is the part worth remembering.** The derived counter used **rows**, so both roll-ups silently switched from counting clauses to counting bookkeeping — while the column headers still read *Clauses green / total*. The **101 clauses with no row were removed from the denominator instead of counted as unproven**, and several agents' ratios *improved* inside a change headlined "the green count fell honestly". Twelve of fourteen Status cells disclosed it in prose; `master` — the worst case in the book — did not. A second error rode along: **10 clauses carry more than one row** (PM 7, provider 3), so green *rows* let one clause count up to three times. Fixed: the counter is now **distinct clauses with ≥1 green row over clauses declared in `laws.md`**, pinned by two tests **observed failing** on the row-based derivation (DL-70). **Corrected: 260 / 562 (46 %) → 252 / 653 (39 %)** — `master` 56 % → **26 %**, provider 47 % → **27 %**, execution 64 % → **49 %**, PM 77 % → **57 %**. Against the pre-sprint claim, real coverage went **43 % → 39 %**. **Named limit, not smoothed over:** the check is mechanical (*does a docstring name the ID?*), so it cannot catch the S151 shape — a real citation on a test proving one third of its clause. **252 is a ceiling, not a floor**; the gate removes the three failure modes that *are* detectable. Verified independently before merge: `make ci` **2085 passed / 5 skipped / 100.00 %**, `make gate-selftest` **15/15**, all four jobs green on tip `a301ad9` by `headSha` (CI `30775862536`, Security Findings `30775862531`), and each hard-fail assertion watched rejecting violations planted by hand. **Hardening rows R and R² closed; O stays open** at **101 missing rows, warn-only** (DL-82 shadow-first) — **S157** writes them and flips the check to hard fail. **Nothing deployed; the fleet stays on `:s155`.** · **🟢 `chore-exec-fail-03-coverage` IS SHIPPED (`v0.85.06`) — `EXEC-FAIL-03` is proven in full, and the move that let it look proven is now forbidden.** S151 flipped the clause ⬜ → 🟩 on a test covering **one of its three conjuncts**, and — the part that matters — **reworded the clause summary in `test-plan.md` toward that test's scenario**, so `laws.md` and `test-plan.md` agreed and nothing disclosed the gap. Review reverted it; this closes it. Three tests in `agents/execution/tests/test_graph_write_failure_retry.py` cover the **submit** path — the spine failing between the broker accepting an order and the graph recording it: a fault is recorded with `submitted=0` and **zero `Fill` nodes while the order is already at the broker**; the retry sends **one stable idempotency key**, so the broker holds one order and the `Fill` finally lands; and a repeated write replays onto ordinal 0 while a *changed* one **appends** `…#1` with ordinal 0 preserved. **All three observed failing on planted defects first (DL-70)**, and the idempotency plant was measured, not inferred — an unstable key produced **two broker orders for one intent**, the oversell hazard `0.74.01` closed. 🟠 **One of my own assertions was wrong and was replaced, not explained away:** `PaperBroker.order_count` was proving “no re-submission”, and a planted broker that never de-dupes **still passed** — `PaperBroker._fills` is itself keyed by idempotency key, so the probe measured the fake's storage rather than the behaviour. Replaced with a broker that records what the caller actually sends. Execution **30 → 31 / 57** in `ledger.md` + `laws/INDEX.md`. The convention landed where it binds rather than in a return note: **[ADR-0021](decisions/0021-clause-summary-mirrors-the-law.md)** plus **[conventions §7a](laws/conventions.md)** — inserted as §7a rather than renumbered to §12, because `§3`/`§4`/`§7` are cited from sprint docs and test docstrings and renumbering breaks citations the way renumbering a clause ID does (§2). **⚠️ Found while reconciling, filed rather than fixed — [hardening row R](hardening-backlog.md):** `ledger.md` and `laws/INDEX.md` disagree with the test-plans they summarise for **8 of 14 agents** (`portfolio_manager` **33 / 24 / 24**, `monitor` **24 / 19 / 19**, `curator` **24 / 22 / 20**, and five more). **The larger number is not automatically the right one** — a 🟩 is only true if a passing test cites that ID — so adopting it would repeat the exact over-claim this chore exists to prevent; it wants the S152-style per-row pass, in one sweep with row O. [DL-87](design-log.md). Verified independently before merge: `make ci` **2067 passed / 5 skipped / 100.00 %** locally and **2066 / 6** on CI, with all four jobs green on tip `2ec79b8` by `headSha` (CI `30744754370`, Security Findings `30744754357`). Merge `0cd1583`; **`build-images` checked too and green** (`30744845393`) — a green CI proves mergeable, not shippable. **Nothing deployed — tests and documents only; the fleet stays on `:s155`.** · **🟢 S153 IS MERGED (`v0.85.00`, merge `f32581a`) — the deliberator exists, and DL-80 is still open.** One image with the role distributed: graph-pull Manager over unvetoed `PMRun`s plus served Proponent/Opponent peers; `kernel/deliberation.py` demoted to the shared reasoning core with debate behaviour unchanged. **Scope item 1 was observed failing** — removing the deliberation row from `trading_observatory_views.SPEC` gave `AssertionError: assert 'PASS' == 'FAIL'`, restoring it passed — which also satisfies DL-82's named precondition for revisiting DL-46 auto-deploy. **ADR-0020 implemented as decided, not merely satisfied:** `kernel/llm_ledger.py` writes `LLMCall` for any `calling_agent` and the dashboard attributes cost per agent, so the fragmentation argument that settled the ADR is honoured in code. New agent is **0 / 48 with a test-plan row for every clause** — no green claimed, and hardening row **O** deliberately not reproduced in a new bundle. Verified independently before merge: `make ci` **2030 passed / 6 skipped / 100.00%** on tip `7869dce`, and all four jobs green on that SHA by `headSha` (CI `30690470714`, Security Findings `30690470721`). **🔴 What this does NOT do: close [DL-80](design-log.md).** The veto has still never run in production — zero `DeliberationRun` nodes. Deploy, the live `DeliberationRun`, the post-deploy `claude-opus-5` `LLMCall` and the functionality check are operator sequencing, and are **blocked by DL-84**. · **🟢 S155 IS SHIPPED (`v0.85.01`, merge `4091d6c`) — the loop now backs off, and the untested half is finally tested.** `run_once` reports **progress**, not activity; `work_loop` sleeps on a no-progress pass exactly as on an empty one. Per-item backoff plus a **visible, append-safe** `WorkItemQuarantine` stop a poison item monopolising the loop, and identical faults collapse into a `FaultSuppression` summary that keeps the volume readable. **The `# pragma: no cover` is gone from `work_loop.py`** — 100 % branch coverage on the function whose failure mode cost two hours and 5,762 faults on 2026-07-30. That removal was most of the sprint's value. **Planted failures observed pre-fix (DL-70):** a no-progress loop ran **`attempts=25 sleeps=0`**, and one signature wrote 5 duplicate fault nodes; both bounded after. The **healthy path was proven unchanged first** — `test_work_loop_does_not_sleep_after_productive_pass` and the empty-pass test exist precisely because a backoff bug would stall eight agents at once. Collapse **shape 2 (first + summary)** chosen and justified: it preserves the exact first-fault timestamp/key contract, with the `flush()`-or-later-event trade-off named rather than hidden. **DRIFT-030** opened instead of amending a locked law (S152 convention). Verified independently before merge: `make ci` **2054 passed / 6 skipped / 100.00%** on tip `f0c237e`, all four jobs green on that SHA by `headSha`. Both new labels are declared in the vocabulary pack. **⚠️ The pack now carries THREE undeployed changes** — S154's `pnl_unresolved_at`, S153's `DeliberationRun` properties + `LLMCall.calling_agent`, and S155's two new labels. The next deploy **must** re-inject and read back `GRAPH_VOCABULARY_B64`, or the first write of any of them raises `VocabularyError` fail-closed (S148 stall pattern). · **🟢 THE FLEET IS ON `:s155` — 16 apps + dispatcher job, guard armed, verified per app ([DL-88](design-log.md)).** `DeployRecord deploy:2026-08-02T08:38:00Z:s155:1a17236` written **after** verification: 16/16 on tag, **16/16 carrying a byte-identical vocabulary pack** (`sha256 aec5ce55f789…`, checked per app rather than sampled), 16/16 `provisioningState=Succeeded`, every app `minReplicas=0` with 1 KEDA rule, job cron `30 22 * * *`. **Three new apps** (`deliberator-manager` / `-proponent` / `-opponent`), 13 → **16**. This carries **S153 + S154 + S155 + five chores**. **It took two runs, and the first fix was wrong.** Moving the pack to its own narrow `--set-env-vars` (`0.85.04`) still failed: `az` is **`az.cmd`**, so cmd's ~8,191-char ceiling applies to the *whole invocation* and the pack alone is **12,053** chars — measured, not inferred (`LASTEXITCODE: 1`, *The command line is too long.*, nothing else on the line). The fix could not be staying under the limit; it had to be **leaving the wrapper**: `python.exe -m azure.cli` goes through `CreateProcess` (32,767). Proven on one app before adopting (`0.85.05`). **⚠️ A window where the fleet was worse off than before:** between runs all 16 apps sat on `:s155` with `GRAPH_VOCABULARY_B64` **absent** — images updated, vocabulary step failed. An absent var is not the fail-closed stall the guard is designed around; it means the store is **unguarded**, so S144's protection was simply *off* on new code. Closed by the second run. **Follow-up filed as hardening row Q:** the second run reported `[XX]` for all 15 agents and the job while every target actually deployed correctly. `az` exits 0, so no stderr surfaces, and the state parsed out of a merged stdout/stderr stream is not the string `Succeeded`. The tool now **under**-reports rather than over-reports — the safe direction, and precisely why it will be tolerated — but a deploy whose report cannot be trusted either way is not finished. **Next: Monday 2026-08-03 22:30 UTC** is the first scheduled run on this fleet — first live test of the deliberator, the terminal-refresh fix and the bounded loop at once. Watch in order: (1) does a `DeliberationRun` appear, closing DL-80; (2) does acceptance still pass now that a declared stage must produce something; (3) `Fault` volume, which S155 should hold flat. · **🟢 DL-84 IS RESOLVED — the DHI base was rebuilt upstream and `build-images` went green on its own.** Recovery took ~6.5 h with **no repo change**: no `.trivyignore` entry, no digest pin. `30686057170` failed 05:33 and again on re-run at 05:48 (08-01); `30698986298` succeeded 12:05 (08-01); **`30730000621` on `4091d6c` succeeded 2026-08-02 03:05 UTC — 14/14 jobs, 0 failed.** R005's *“near zero, continuously rebuilt from source”* was load-bearing, not marketing, and **waiting turned out to be the cheap option**: accepting the 8 CVEs would have put the first-ever entries into a file empty since S130, for findings that fixed themselves six hours later. **🟢 THE DEPLOY IS UNBLOCKED.** Images exist for `4091d6c`, which carries **S153 + S154 + S155 + both chores** — the fleet is on `:s152` and four code merges behind. **⚠️ The single highest-risk step in that deploy is the vocabulary pack.** It now carries **three undeployed changes** — S154's `pnl_unresolved_at`, S153's `DeliberationRun` properties + `LLMCall.calling_agent`, and S155's `FaultSuppression` / `WorkItemQuarantine` labels. Each was declared correctly in isolation, which is exactly why it is easy to overlook: the deploy **must** re-inject `GRAPH_VOCABULARY_B64` and **verify it by reading the value back off a deployed app**, as was done for `:s152`. A stale pack means the first write of any of the three raises `VocabularyError` fail-closed inside a caller's fault boundary — the S148 stall pattern. **Timing:** next scheduled run is **Monday 2026-08-03 22:30 UTC**; Saturday and Sunday are non-session days, so the calendar gate correctly skips both. **The process finding is NOT resolved by this:** four merges were called green on CI + Security Findings without checking `build-images`. It recovered on its own, so nothing was lost — but that is luck, not process. **A green CI proves mergeable, not shippable.** · **🟢 S153 IS MERGED (`v0.85.00`, merge `f32581a`) — the deliberator exists, and DL-80 is still open.** One image with the role distributed: graph-pull Manager over unvetoed `PMRun`s plus served Proponent/Opponent peers; `kernel/deliberation.py` demoted to the shared reasoning core with debate behaviour unchanged. **Scope item 1 was observed failing** — removing the deliberation row from `trading_observatory_views.SPEC` gave `AssertionError: assert 'PASS' == 'FAIL'`, restoring it passed — which also satisfies DL-82's named precondition for revisiting DL-46 auto-deploy. **ADR-0020 implemented as decided, not merely satisfied:** `kernel/llm_ledger.py` writes `LLMCall` for any `calling_agent` and the dashboard attributes cost per agent, so the fragmentation argument that settled the ADR is honoured in code. New agent is **0 / 48 with a test-plan row for every clause** — no green claimed, and hardening row **O** deliberately not reproduced in a new bundle. Verified independently before merge: `make ci` **2030 passed / 6 skipped / 100.00%** on tip `7869dce`, and all four jobs green on that SHA by `headSha` (CI `30690470714`, Security Findings `30690470721`). **🔴 What this does NOT do: close [DL-80](design-log.md).** The veto has still never run in production — zero `DeliberationRun` nodes. Deploy, the live `DeliberationRun`, the post-deploy `claude-opus-5` `LLMCall` and the functionality check are operator sequencing, and are **blocked by DL-84**. · **🟢 S155 IS SHIPPED (`v0.85.01`, merge `4091d6c`) — the loop now backs off, and the untested half is finally tested.** `run_once` reports **progress**, not activity; `work_loop` sleeps on a no-progress pass exactly as on an empty one. Per-item backoff plus a **visible, append-safe** `WorkItemQuarantine` stop a poison item monopolising the loop, and identical faults collapse into a `FaultSuppression` summary that keeps the volume readable. **The `# pragma: no cover` is gone from `work_loop.py`** — 100 % branch coverage on the function whose failure mode cost two hours and 5,762 faults on 2026-07-30. That removal was most of the sprint's value. **Planted failures observed pre-fix (DL-70):** a no-progress loop ran **`attempts=25 sleeps=0`**, and one signature wrote 5 duplicate fault nodes; both bounded after. The **healthy path was proven unchanged first** — `test_work_loop_does_not_sleep_after_productive_pass` and the empty-pass test exist precisely because a backoff bug would stall eight agents at once. Collapse **shape 2 (first + summary)** chosen and justified: it preserves the exact first-fault timestamp/key contract, with the `flush()`-or-later-event trade-off named rather than hidden. **DRIFT-030** opened instead of amending a locked law (S152 convention). Verified independently before merge: `make ci` **2054 passed / 6 skipped / 100.00%** on tip `f0c237e`, all four jobs green on that SHA by `headSha`. Both new labels are declared in the vocabulary pack. **⚠️ The pack now carries THREE undeployed changes** — S154's `pnl_unresolved_at`, S153's `DeliberationRun` properties + `LLMCall.calling_agent`, and S155's two new labels. The next deploy **must** re-inject and read back `GRAPH_VOCABULARY_B64`, or the first write of any of them raises `VocabularyError` fail-closed (S148 stall pattern). · **🔴 NO DEPLOYABLE IMAGES — `build-images` has failed on every merge since 03:53 UTC today ([DL-84](design-log.md)).** Four consecutive failures (S154, DL-81 docs, S152, `chore-llmcall-substrate`); CI and Security Findings were green on all four, verified by `headSha`, so **the fleet is stuck on `:s152` while `main` is at 0.84.07** — three code merges behind. **Cause is upstream:** Trivy reports `Total: 8 (HIGH: 8, CRITICAL: 0)`, all `linux-libc-dev` kernel CVEs in the `dhi.io/python:3.13` base. The gate runs `ignore-unfixed: true`, so these fail *because* a patched `linux-libc-dev` exists and the base has not yet been rebuilt against it. **A plain re-run does not clear it** (run `30686057170`, re-run 05:48 UTC — identical 8 findings). **Ruled out: `.trivyignore`.** It would undo the reason [R005/S130](research/base-image/INDEX.md) migrated off `python:3.13-slim` — that move traded 22 HIGH/CRITICAL of permanent structural noise for a **near-zero baseline where the ignore-file stays empty and every finding is a real signal**. Spending the first entry on a class the base is designed to fix within hours trades a durable property for a few hours of waiting. **Decision: wait for the DHI rebuild, then re-run.** Next scheduled pipeline run is **Monday 2026-08-03 22:30 UTC** — Saturday and Sunday are non-session days, so the calendar gate correctly skips both — giving ~2.5 days of slack against a rebuild measured in hours. Escalation if not cleared by Monday AEST: pin a known-good DHI digest, or a **time-boxed** `.trivyignore` entry with an expiry and a hardening row so it cannot become permanent. **Process finding:** four merges were called green today on CI + Security Findings without checking `build-images` — the DL-46 shape again, **a green CI proves mergeable, not shippable**. **Otherwise healthy:** spine reachable, all 13 apps `minReplicas=0` with KEDA rules intact, `dispatcher-cron` `Succeeded` four nights running, last night 8/8. **Latent, for whenever the deploy happens:** S154 added `pnl_unresolved_at` to the vocabulary pack and the fleet's `GRAPH_VOCABULARY_B64` predates it — harmless on `:s152` code, but the deploy must re-inject and read back the pack or the first unresolvable sell fill raises `VocabularyError` fail-closed (S148 stall pattern). · **🟢 S153 IS UNBLOCKED — the delegated agent found a real law contradiction and stopped instead of coding around it ([DL-83](design-log.md)).** S153 hands the deliberator an `ANTHROPIC_API_KEY` and makes an `LLMCall` node a success factor, but `OPR-IDN-01` claimed the operator *"is the sole LLM boundary"* and `OPR-IDN-02` claimed single-writer ownership of `LLMCall`. **On verification the conflict was sharper than reported:** `OPR-IDN-02` is **🟩 green** (pinned by `test_operator_boundary_claims_graph_labels_once`), so S153 would have broken a *proven* clause; and `LLMCall` is already a **cost ledger with two consumers** — `surfaces/dashboard/llm_costs.py` and `/audit-costs` both enumerate it. **That second fact decided it.** The tempting fix, a deliberator-owned `DeliberationLLMCall`, breaks no law and passes every gate — and would have made the system's **largest** LLM spender invisible to the bill while the cost report still rendered a confident total. DL-57 landing on the instrument used to watch spend. **Also checked:** only `operator/store.py` writes `LLMCall` today, so there was **no code drift** — the law was honoured exactly, and this was a forward-looking conflict caught before implementation. Settled by **[ADR-0020](decisions/0020-llmcall-is-substrate-not-the-operators.md)** (`LLMCall` is substrate; any agent may call a model and writes its own audit node into the one ledger; operator keeps `CommandAudit`/`Intent` and stays the sole *operator-command* boundary) and shipped as `chore-llmcall-substrate` (**`v0.84.07`**, merge `b0e6b0e`, operator laws **v1 → v1.1**). **Why an ADR and not S152's convention:** that convention covers a *lacking declaration*; this was a **scope reduction on a locked, proven clause** — a different and bigger act, deliberately not absorbed by precedent. Kept in its **own chore** so no law amendment rides inside a feature. **`OPR-IDN-02` stays green** — the test was re-pointed to the amended wording and still proves it exactly, **not** loosened (the S151 failure mode); a second test pins the exclusion and was observed failing on a planted revert. Test module split at the 200-line hard block rather than bypassed. `make ci` **2002 passed / 100.00%**; gates verified by `headSha` on `71418b9`. **S153 brief updated** so the next attempt is not blocked, and scope item 6 now also owns the `LLMCall` shape question ADR-0020 left to it: whether it gains a declared property list, and how the calling agent is identified so spend stays attributable per agent. · **🟢 S152 IS SHIPPED — the law book caught up with its code, and the convention that let it fall behind is now written down.** Merge `4524da5`. `execution` LOCKED **v1 → v1.1** (+8 clauses: `IDN-03`, `TRG-07`, `OUT-07/08`, `STA-05/06`, `OBS-03`, `DEP-04`; 49 → **57**) and `analyst` **v1 → v1.1** (+3: `OUT-07/08`, `OBS-03`; 43 → **46**). **DRIFT-024/025/026/027/028/029 are all CORRECTED — zero open law-gap rows for the first time since S146.** **Greens deliberately did not move** (execution 30, analyst 26): the ratios got *worse* and that is the honest outcome — declaring a clause is not proving one, and every new clause starts ⬜ with `_tbd_`. **All IDs are new; nothing was renumbered and no existing clause was widened**, because extending a green clause silently extends what an already-passing test is claimed to prove. **The durable output is the convention, not the eleven clauses:** §4 forbids blessing *accidental* behaviour into law, it does not forbid declaring a capability an ADR already decided — the test is **provenance** (did a decision precede the code?), *decided → amend with a new ID naming the ADR*, *appeared → stays a code fix*. Six sprints deferred under the opposite reading; this precedent is what stops a seventh. **Stated honestly rather than smoothed over:** DRIFT-029 rests on a **weaker warrant** than the other five — its `pnl_unresolved_at` half has no ADR, only the S154 spec and DL-81 — and the row records that. **Still open inside DRIFT-029:** `broker_status="partial"` cannot upgrade to `filled` under the write-once property model, so that one case still refreshes indefinitely; **0 production fills are in it today**, and the fix is a current-status read model derived from `BrokerOrderStatus` facts — a design change, not a law edit. **A pre-existing gap found while reconciling:** the test-plans carry fewer rows than their laws have clauses (execution 44 vs 57, analyst 34 vs 46) — the counters agree, row-per-clause completeness does not. Worth its own pass. No production source changed; `make ci` **2001 passed / 6 skipped / 100.00%**; gates verified by `headSha` on `737f779` and tip `fcbfb1c`. **🟢 THE FOUR OWED DECISIONS ARE TAKEN** ([DL-82](design-log.md), operator delegated): **[ADR-0019](decisions/0019-risk-cap-binds-position-size-not-stop-distance.md)** — the 8 % risk cap binds **position size, never stop distance**, because raising a safety cap to make a challenger look better is fitting the guardrail to the strategy; closes DL-78 and means **S150 cannot be fairly promoted until the sizing change lands**. Property enforcement for the other 51 labels goes **warn-only shadow first** (fail-closed guard + 46 blind `add_edge` sites make a 49-label declaration an untested surface). DL-46 auto-deploy **stays deferred** behind S153's does-a-declared-stage-produce-anything check — DL-80 is the argument for keeping the human gate. ADR-0007's DockerHub wording gets a **proper amendment**, not a silent rewrite. · **🟢 S154 IS SHIPPED AND MERGED (`v0.84.05`, merge `676362a`) — the green run was also writing 2,742 copies of the same settled fact, and it has stopped.** Verified **independently before merge**, not taken on report: `make ci` re-run on tip `0649be0` at **2000 passed / 6 skipped / 100.00%**, and all four remote jobs confirmed green on both the implementation SHA `ae9e106` (CI `30682454551`, Security Findings `30682454545`) and the tip `0649be0` (CI `30682575369`, Security Findings `30682575384`) — SHAs checked against the runs, not just the run IDs quoted. The production change is **14 lines across two files**, inside the scale check the handover note set: a `_TERMINAL_BROKER_STATUSES = {"filled", "rejected"}` skip placed *before* `write_order_status`, and `pnl_unresolved_at` returned in place of `{}` with a matching `_needs_realized_pnl` guard. `partial` deliberately stays non-terminal. **Planted failures were observed in all three directions** (DL-70): pre-fix `5 failed / 5 passed`; adding `"partial"` to the terminal set failed the partial test `assert 0 == 1`; removing `pnl_unresolved_at` from the pack failed two tests naming the undeclared property. **DRIFT-029 opened** with the deferred `partial` read-model boundary recorded in it. **🟠 One finding from my review, and it is mine not the coding agent's — [DL-81](design-log.md), decision owed.** The terminal skip sits *before* the marker write, so a fill that is **already** terminal is skipped before `pnl_unresolved_at` can ever land. Verified live: 39 fills are already terminal and exactly **one** is a sell fill still needing a conclusion — `pm-run-927de0c7…:ABT:sell`, **the 98-share exit that motivated the whole sprint**. Its fault stops (the win) but it gets no marker, which is precisely the silent-skip shape the spec argued against. Marking is correct for every *future* unresolvable fill; the gap is bounded to history. Recommended fix is a **one-time marker write** on that single node (append-safe: the property is now declared and the node lacks it) — **not** a PnL backfill, because the key encodes no `position_ref` and inference on an append-only store cannot be withdrawn. **✅ RESOLVED 2026-08-01 — option 3 was approved and executed** ([DL-81](design-log.md)). The marker was written through an **armed `GuardedGraphStore`** (the pack base64-injected exactly as the fleet receives it), so the new declaration was validated on the real write path rather than assumed; **permanence was proven, not assumed** — a second write with a *different* value was refused (`ValueError: property 'pnl_unresolved_at' cannot be overwritten`); and **no PnL was asserted** (`realized_pnl_cents` stays `None`). Re-verified live 2026-08-04: `pnl_unresolved_at = 2026-08-01T04:03:39.898023+00:00`, and exactly one `Fill` carries it. Lifetime realized PnL stays understated by exactly one trade; AMD −$3,515.60 and MRVL −$1,330.12 are unaffected. **✅ Deployed and proven** — S154 reached the fleet with the `:s155` retag (2026-08-02) and its effect was measured on `sched-2026-08-03` (lead entry). ·  Found by tracing the clean `sched-2026-07-31`. `refresh_pending_fills` selects work with `if node.props.get("status") != "pending": continue` — but `Fill.status` is written **once**, at submit, as `"pending"`, and on the append-only spine (ADR-0014) it **can never become `"filled"`**. The terminal truth lives in a different property, `broker_status`, written once under `if "broker_status" not in node.props`. So the selector asks "is this fill unsettled?" using the one property that can never answer: **39 live fills carry a terminal `broker_status` (23 `filled`, 16 `rejected`) and are re-selected as pending work every single run.** `write_order_status` is then called *unconditionally*, before the `broker_fill.status == "pending"` early-return, and keys on a fresh timestamp — so each pass mints a genuinely new node plus a `REFRESHES` edge. Live count: **2,742 `BrokerOrderStatus` nodes across 59 distinct fills, up to 73 for one fill**; during the 07-29 retry storm one fill took 17 in 40 seconds. Growth is O(settled fills × runs), unbounded, on a paid spine. **Second symptom, same cause:** `realized_pnl_props` re-runs too, and one legacy ABT sell fill (`pm-run-927de0c7…:ABT:sell`, 98 sh filled $101.35 on 07-24) is keyed in the **pre-0.74.01 shape** that encodes no `position_ref` and has no `EXECUTES` order — so it can never resolve, and re-emits the identical `UnresolvedEntryBasis` fault every pass, forever. **Nothing overwrites, so nothing raised** — S151's guard holds and the loop is silent, which is why two sprints of live-fire debugging walked past it. **No gate could see it:** acceptance scores what a run *produced*, not what it *re-produced* — DL-57/DL-59 a third time. **Scoped honestly:** lifetime realized PnL is understated by exactly one trade (AMD −$3,515.60 and MRVL −$1,330.12 *are* attributed); the reporter is **not** broken (last night's `profit_factor=unavailable` is correct per-run scoping with 0 closes); broker↔graph state is correct. S154 ships a terminal-status selector, a durable `pnl_unresolved_at` marker so a conclusion is recorded once rather than retried forever, and the vocabulary declaration the **now-armed** guard requires. **Deliberately deferred and named:** `broker_status="partial"` can never upgrade to `"filled"`, so that one case keeps refreshing — 0 production fills are in it today; the right fix is a read-model change, not a bolt-on. · **🔴 FOUR CI RUNS WENT RED UNATTENDED — remote-green is now a blocking gate written into the sprint doc, not a handback footnote.** All four are the same Dependabot branch (`dependabot/uv/python-development-cc6c16f905`, `mcp` 1.28.1 → **2.0.0**, a breaking major): 8 mypy errors in `surfaces/mcp_server.py` — `Tool(inputSchema=…)` is no longer a valid keyword (5 sites) and `Server.list_tools` / `Server.call_tool` are no longer attributes, with the existing `type: ignore` comments now covering the wrong codes. Auto-merge is **correctly blocked**; `main` is not red from our code. **This needs its own chore branch** (`mcp` 2.0.0 API migration) — it is not S154's work and S154 says so explicitly. · **🔴 THE LLM VETO HAS NEVER RUN IN PRODUCTION — NOT ONCE ([DL-80](design-log.md), operator escalated).** A live-graph inventory taken during the S144 work shows **zero** `DeliberationRun`, `ForecasterRun`, `TrainingExample`, `Dataset`, `Predictor`, `ShadowPrediction`, `Experiment` and `Escalation` nodes. All **25** `LLMCall` nodes carry one edge shape — `CommandAudit -PRODUCED_BY-> LLMCall`, i.e. operator chat (S125) — and the newest is **2026-07-15**. `_drop_vetoed` is *documented* fail-open, so **every order this system has ever submitted went to the broker unvetoed**; the fail-open branch is the only one that has ever executed. **Two gaps, one symptom:** deliberation is not an agent at all — it lives in `orchestration/veto.py`, wired only into the *local* pipeline, with no image, no app and no graph-pull work source; and only **7 of 13** deployed apps have a work loop (provider/scanner/analyst/PM/execution/monitor/reporter), while forecaster, curator, operator, researcher and supervisor are **served** agents nothing ever sends a request to. **No gate could see it:** `trading_acceptance.py`, `trading_boundaries.py` and `trading_observatory.py` contain no reference to either capability, so every run scored `ACCEPTANCE PASS` with both absent — the DL-57/DL-59 pattern a third time. **Collateral:** DL-63's `claude-opus-5` default has therefore **never executed in production** (live calls are all `claude-sonnet-4-6`), and DL-41/DL-42's compiled judge and challenger are champions of a stage that does not run. **Not an outage** — the 7-agent pipeline works and scores honestly on what it covers; the missing thing is the risk-*review* layer the PRD and this file both describe as live. **Decision owed:** make deliberation a real fleet participant (own image + graph-pull source on unvetoed `PMRun`s, the shape every pipeline agent already uses) or retire it honestly from the architecture — and either way the acceptance gate must gain a check that **fails when a declared stage produces nothing**. · **🟢 S144 IS ENABLED ON THE FLEET — the write guard is finally armed, after three undeclared edge shapes were found and closed first.** Fleet retagged `:s151` → **`:s152`** (14/14 `Succeeded`, built from `d00904b`, `DeployRecord …:s152:d00904b` written after verification) and `GRAPH_VOCABULARY_B64` set on all 14 targets — **verified by reading the value back off a deployed app and decoding it byte-identical to the pack** (71 labels, 43 edge types, 43 signatures, 2 property lists). Config intact: `minReplicas=0`, `daily-agent-window`/`daily-master-window` KEDA rules, all 3 `secretRef`s per target, job cron `30 22 * * *`. **The pre-flight is what mattered.** Enabling was *not* the small step it looked: the signature dimension had the same hole the property dimension did — **46 `add_edge` sites have an endpoint the static scan cannot resolve** (a function parameter, or a label read off a descriptor table), so the declared signatures were whatever past runs happened to produce. Three shapes were undeclared and would have raised `VocabularyError`: `MonitorRun -LINKED_FROM-> MonitorRun`, `Snapshot -LINKED_FROM-> Snapshot` (both bite on a **late-stage resume — the recovery path**) and `PMRun -DELIBERATED_BY-> DeliberationRun`. All three now declared (0.84.04), with `resume_edge_signatures()` deriving the resume path's requirements from the same `ARTIFACTS` table `resume.py` walks so the gap cannot reopen; the new test was observed failing on a planted removal (DL-70). **Live proof before the run:** the vocabulary read back off the deployed `execution` app accepts **37/37 live labels, 36/36 live edge signatures and both enforced labels' live property sets** through kernel's own `check_node`/`check_edge` — every shape production has ever written passes. **Functionality check PROVEN on `sched-2026-07-31`** — the first guarded run scored **`RESULT 8/8 stages complete`** with **zero** `VocabularyError` faults in the graph, `position_sync status=fresh`, provider 100/100 with no degraded notes, and `audit_broker_graph.py` `totals failures=0` (9/9 positions qty-matched, 9/9 stop-protected). Scope it honestly: one order was submitted (BMY buy 153 @ limit $65.63) and **no new label, edge or property shape was written that the guard had not already seen** — so this proves the guard does not break the nightly path, not that it covers an unexercised one. Acceptance reads `UNPROVEN - completed; orders submitted but none filled yet` — the BMY `day` order was submitted 22:40 UTC Friday and rests until the **Monday 2026-08-03** open; re-run `accept.py --run-id sched-2026-07-31` after it. **Residual risk, unchanged:** the guard is fail-closed and a raise lands inside the caller's fault boundary (the S148 stall pattern), and 46 blind `add_edge` sites remain — so a *never-executed* path could still trip. Rollback is one command each way: retag to `:s151`, or unset the env var. · **🟢 THE S144 PREREQUISITE IS CLOSED — the guard's property dimension is now PROVEN, not assumed.** `chore-vocabulary-property-completeness` merged (`7f05829`, `v0.84.03`); gates green on tip `5edffd1` (CI `30612209568`, Security Findings `30612209553`), `make ci` **1987 passed / 6 skipped / 100.00%**. S149 taught `check_node` to reject undeclared node **properties**, but the completeness suite proved supersets for labels, edge types and signatures only — so an under-declared property read green and would have raised `VocabularyError` on the first real write once S144 is enabled. **The finding that mattered is why it looked fine:** `Fill` recovered **7 of its 45** declared properties while reporting **zero undeclared** ones, because `write_fills` and `_write_stop_fill` pass props through a frozen `FillAttempt` field — *didn't look* rendering identically to *looked and found nothing* (DL-57). Three resolver hops (parameter binding, the dataclass-field passthrough, the `dict()` rule) take `Fill` to **34 recovered, 0 undeclared, 0 blind sites**; `Recommendation` resolves fully at 21. **Both checks were observed FAILING on planted violations first** (DL-70): removing `drop_reason` from the pack failed the superset test naming it, and removing the `dict()` rule brought the blind sites back. **Named limits, recorded not hidden:** the guard enforces properties for **2 of 71 labels**, so 51 labels that write props are still unprotected (**49 of the 51 resolve totally**, so they could be generated — a separate decision, deliberately not taken); and `orchestration/resume.py` merges under `artifact.label`, so its clone properties are attributed to **no** label — latent until a resume-chain label becomes property-enforced. Report: [vocabulary-property-coverage](reports/vocabulary-property-coverage/README.md). **S144's dated fleet enablement is still open** and is now a smaller step. · **🟢 THE OUTAGE IS CLOSED — PROVEN IN PRODUCTION, NOT ASSUMED.** S151 deployed (fleet `:s148` → **`:s151`**, 14/14, `DeployRecord …:s151:410830f` written after tag verification) and the stalled `sched-2026-07-30` was **resumed on the live spine**: **2/8 → `RESULT 8/8 stages complete`**, **`ACCEPTANCE PASS`**. `position_sync` `status=fresh`, exactly one snapshot — the artifact whose absence stalled everything. **The collision is gone**: 11 `Fill` nodes now carry `drop_reason`/`dropped_at` with 11 matching append-only `BrokerOrderStatus` drop facts, and **every one still reads `broker_status=rejected`** — the reconciler's account preserved, not overwritten, which is the entire point. **Zero** `cannot be overwritten` faults against 5,762 the night before. 🚨 **All nine `gtc` stops survived** — 9 positions / 9 open orders / 9 resting stops at Alpaca with submit timestamps unchanged from 07-28/07-30 (never touched, not re-placed), and **0 non-stop open orders** left, so the sweep dropped exactly what it should. No orders placed (analyst 9 hold → PM `approved=0`), so it is a clean structural proof. Manual scale window closed and verified back to `minReplicas=0` with cron rules intact. Row in [functionality-checks.md](laws/functionality-checks.md). · **🟢 S151 MERGED** (`v0.84.01`, merge `8f57f5f`) — the outage fix. Drop evidence stays append-safe (`Fill.drop_reason` / `Fill.dropped_at` plus an append-only `BrokerOrderStatus` drop fact), the sweep has per-order and roll-up containment, and `sync_run_request` isolates cleanup from the run-start `BrokerPositionSnapshot` — **a cleanup step can no longer cost the run its foundation.** Gates green on tip `7e5c66b` (CI `30605541083`, Security Findings `30605541095`); `make ci` re-verified **independently** on that same tip at `1983 passed, 5 skipped, 100.00%`, pip-audit + detect-secrets clean. A **fifth consumer** surfaced during implementation — `orchestration/packs/trading_fill_outcomes.py` read `broker_status` to classify a dropped fill — and was re-pointed at `drop_reason` rather than restoring the removed write. **Planning review reverted one over-claim:** `EXEC-FAIL-03` had been flipped ⬜→🟩 on a test proving only its fault-recorded half, with the clause summary in `test-plan.md` **reworded toward that test**; summary restored to the locked wording, status back to ⬜ with the partial coverage named, execution back to **30 / 49** in `ledger.md` + `laws/INDEX.md`. The test is kept — good evidence for containment, not proof of that clause. (Reporter's 19 / 40 was checked and **stands**: those citations date from S148, so it was a stale-index backfill.) Coverage handed to **`chore-exec-fail-03-coverage`** (codex, `0.84.02`), which also adds the standing convention: *a clause summary mirrors `laws.md` and is never reworded to fit an available test.* **✅ DEPLOYED AND PROVEN 2026-07-31** — fleet `:s151`; the `:s147` contingency is moot and closed. · **🔴 THE OUTAGE ITSELF — `sched-2026-07-30` reached 2/8 stages and S148's own drop sweep is why.** S148's first night on the fleet. `record_drop` writes Alpaca's raw `reason` (`"canceled"`) into `broker_status`, which reconciliation had already filled with the normalised `BrokerStatus` (`"rejected"`) — two vocabularies in one property, and the append-only store refused (`ValueError: property 'broker_status' cannot be overwritten`). It raised **before** `reconcile_run_start` and **inside** its fault boundary, so no `BrokerPositionSnapshot` was written, `position_sync` never completed, and S147 correctly gates the analyst on that sync — stages 3–8 waited on a stage that could never finish. The work item stayed pending, so `work_loop` retried it every ~1.3 s: **5,762 identical `Fault` rows, 22:30:38 → 00:35:20 UTC**. **Everything else was healthy and does not need re-auditing** — cron `Succeeded`, all 13 apps up on `:s148` for the full window, zero `Escalation`s, provider 100/100 tickers. 🚨 **What held: nine positions, nine resting `gtc` stops, verified at Alpaca — none cancelled, none missing.** The ADR-0015 §3 floor survived a two-hour fault storm inside the agent that owns it, which is exactly why a lost session is survivable. **Fix packaged as [S151](sprints/sprint-151-drop-sweep-append-safe.md)** (`0.84.01`, PATCH — no new capability) and handed to codex; the class-level half matters more than the instance: *a cleanup of yesterday's leftovers may never outrank the foundation it runs beside* ([DL-79](design-log.md)). · **🟢 S150 MERGED** (`v0.84.00`) — the volatility-scaled **stop** challenger, shipping **off by default** (`stop_target_mode=flat`; challenger `k=2.0`, floor 2.5 %, ceiling 8 %). Gates green on tip `3dd2c44`; `make ci` re-verified independently at 1970 passed / 100.00%. **The RR trap was handled correctly and provably**: `scaled_target = flat_target × (scaled_stop / flat_stop)` makes `target/stop` algebraically invariant, and a test **plants stop-only scaling and requires MRVL to be rejected** with `reward_risk_below_min` — the trap demonstrated, not merely avoided. **DRIFT-028 opened — and this one is the *analyst's* constitution, not execution's**, so the declaration debt is systemic across the law book rather than one agent's problem (024/025/026/027 execution, 028 analyst). **Not deployed** — fleet stays `:s148`. · **🟠 MEASURED AFTER THE FACT — the 8 % risk cap, not the formula, is what now binds the volatile names.** The ceiling is correct (it must respect the PRD cap) but I measured what the shipped config delivers: BAC/USB/SCHW unchanged at 2.00× ATR, CSCO 6.1 % → 1.5 % touched, HPE 19.7 % → 6.1 %, AMD 36.4 % → 10.6 % — but **MRVL only halves, 39.4 % → 18.2 %, still 0.94 ATRs** because 2×ATR wants 17.1 % and the cap clamps it to 8 %. Read a promotion report knowing this: the scaling did not underperform, it hit a wall that is not its to move. Two ways past it, neither in S150 — **raise the cap** (a PRD/ADR decision about maximum risk per position, not a tuning knob) or **size positions by volatility** so a 17 % stop sits inside the dollar-risk budget. [DL-78](design-log.md). · · **🟢 S148 IS DEPLOYED — ADR-0018 is now live.** Fleet retagged `:s147` → **`:s148`** at 2026-07-30 05:08 UTC (14/14 `Succeeded`, 13 apps + `dispatcher-cron` verified on tag, env intact at `minReplicas=0`, `DeployRecord …:s148:e8bcca1` written after verification). Tonight's run is the first live test of bounded same-session orders and the drop sweep; check the drop rate and that all nine resting stops survived. · **🟢 S149 MERGED** (`v0.83.00`, tip `1b471c4`, CI `30512736642` + Security Findings `30512736663` green, `make ci` re-verified at 1949 passed / 100.00%). Challenger ships off; fleet intentionally stays `:s148` so S148's live drop rate is measured against one variable. · **🟢 THE EXIT-REPLAY OUTAGE IS FULLY CLOSED.** `sched-2026-07-27` now scores `ACCEPTANCE PASS`; `confirm-s146-20260728` is PASS; `sched-2026-07-28` ran 7/7 on `:s146`. ABT's missing stop was a broker wash-trade refusal, not a code bug; S146 fixed the silence by retrying and surfacing `UnprotectedPosition`. · **✅ RESOLVED 2026-07-30 — nine held, nine stops, zero unprotected.** The `:s147` head sync closed the stale-book ordering gap for stop placement. · **⬜ DRIFT-024 / ⬜ DRIFT-026 / ⬜ DRIFT-028 open** — law amendments remain for broker-stop state/fallback parameter, ADR-0018 bounded-order semantics, and S150 stop-scaling evidence. · **📁 Detail for the S128–S146 arc lives in [state-archive/STATE-06.md](state-archive/STATE-06.md)**.

**How to read.** *Now* = active · *Next* = queued · *Recent* = last few shipped (older detail lives in
each `docs/sprints/sprint-NN-*.md` + [`state-archive/`](state-archive/INDEX.md) `STATE-01…06.md` + git). **LAW-02:** an item is "shipped" only when
its success factors are *proven* (tests, `make ci`, the named live check) — never restate intent as outcome.

---

## Current focus

Since P14 the project runs as **etalon-first continuous improvement** (DL-19).
**The platform is self-driving in paper mode**: the DEPLOYED, STANDING fleet (13 Container Apps +
`dispatcher-cron` job, KEDA scale-to-zero windows, idle ≈ $0) places a calendar-gated `RunRequest`
at 22:30 UTC daily, runs graph-pull + served-over-Service-Bus on the Neon Postgres spine (ADR-0014),
reconciles holdings against the broker (DL-44), debates vetoes under compiled prompts (DL-42), and
proves `ACCEPTANCE PASS`. Pausing = disable the job + zero the scale windows (`docs/deployment.md`).
Completed arcs live in their sprint docs + archives: fleet (DL-35), credentials (DL-36), Postgres
migration (DL-43), deliberation quality (DL-41/42). Layer-3 acceptance 🟩 at the full S&P-500;
Layer-2 choreography 🟩 on a distributed run (S102).

## Recent (most recent first — detail in each sprint doc)

- **The write guard was undeployable, and its pack was a trailing indicator (feat, 0.80.00,
  2026-07-27 — DL-68).** S143 shipped the vocabulary guard unset. Enabling it was two defects deep.
  **(1)** `GRAPH_VOCABULARY_PATH` names a file and **no image copies `orchestration/packs/`** —
  setting it would have raised `FileNotFoundError` at boot, not enabled a guard. Added
  `GRAPH_VOCABULARY_B64`, resolved first, path kept for local dev; injected for master, all 13
  agents and the dispatcher by `deploy-agents.ps1`. This is the shape the master already used for
  grants and the secret map (S86/DL-12) — S143 invented a weaker one instead of following the
  precedent in the same repo. **(2)** The pack came from **observed** writes, so it could not cover
  code that had never run. ADR-0015 §3 stops merged Friday having never placed one, and both its
  edges were undeclared — labels and edge types declared, **signatures** missing — so enabling the
  guard would have raised `VocabularyError` on tonight's first real stop and destroyed the pending
  proof. Now checked two ways because neither suffices alone: static recovery
  (`scripts/vocabulary_{coverage,signatures}.py`) reaches `Fill -STOPS_WITH-> BrokerStopOrder`;
  `Position -PROTECTED_BY-> BrokerStopOrder` resolves via a dict lookup and is reachable **only** by
  executing the path, so the e2e test now runs `place_stop` under a guarded store. Static also found
  `Experiment -PROPOSES-> ParamChange` undeclared. Invariant `graph-vocabulary-injected-at-deploy`
  added (self-test 14/14). Its own first run produced a **false positive** from flow-insensitive
  resolution (`Rejection -EMITTED_BY-> PMRun`; the PM rebinds `node`) — fixed by binding to the
  nearest assignment *above* the call. Worth recording because the tempting fix, unioning the
  bindings, would have pushed fiction into the pack to make the check pass. `make ci` **1851 passed
  / 100.00%**, four remote gates green before merge (`d215a76`). **Functionality check PROVEN** on
  the live Neon spine, base64 only: `GuardedGraphStore` over **`PostgresGraphStore`** (asserted),
  undeclared label rejected with **0 rows written**, both stop signatures accepted, live
  `BrokerStopOrder`=0 / Position=21. **Fleet deliberately NOT enabled** — `:s143` predates the code
  and tonight's run outranks the guard; enablement is a dated action and **S144 stays open** until
  it lands.
- **Opus 5 at max effort — the reasoning knob was inert (feat, 0.78.00, 2026-07-27 — DL-63).**
  Every Anthropic call sent `model`/`max_tokens` only, so `output_config` never left the process
  and reasoning depth sat at the API default. Wired through all three adapters — the operator's
  tool-use client, the deliberation debate, the remediation gate — with `max` as the default rung
  and `ANTHROPIC_EFFORT` as the script-side override. `effort` is a `Literal` over the API's own
  ladder, so a bad override fails on load rather than as a 400 mid-run. Two traps surfaced:
  `max_tokens=512` is a **truncation trap** once effort drives thinking (thinking and structured
  output share the ceiling → the parse returns `refused`), raised to 4096 (OPR-PERF-01); and
  **a container reads no `.env`** — it gets `os.environ` from the master's ACTIVATE payload, which
  `trading_secrets.json` fills with credentials only, so the **code default is the fleet's effective
  value** (DL-63, verified live on the operator app). Defaults moved `claude-sonnet-4-6` →
  `claude-opus-5` in code. `claude-opus-5` priced into `llm_pricing.json` ($5/$25 per MTok) — an
  unpriced model would silently distort the LLMCall ledger. `make ci` **1823 passed / 100.00%**,
  all four remote gate jobs green before merge, fleet retagged **14/14 → `:s143`** (`818e7a9`),
  `DeployRecord …:s143:818e7a9` written. **Functionality check PROVEN** (2026-07-27): a real debate
  ran on `claude-opus-5` — no 400 on `output_config`, substantive turns, `REVISE` verdict. Scope it
  honestly: that proves the *script-side* adapter; the operator agent's tool-use client is deployed
  but **not yet exercised live**.
- **Broker-native stops — the durable floor (feat, 0.77.00, 2026-07-25 — ADR-0015 §3 / DL-61).**
  The stop moves from the once-a-night analyst rail to a **resting `gtc` sell stop at the broker**
  for every held position — continuous, not re-decided daily. **Stop-only** (no take-profit leg —
  ADR-0017 retired `target`). The S137 analyst forced-stop **degrades to a gated fallback**: it
  fires only when a position has no live broker stop, so the two never double-sell. Append-only
  safe (`BrokerStopOrder` immutable fact + `cancelled_at` marker; broker is truth for liveness,
  DL-44); a stop fill rides the **existing** reconciliation + 0.75.00 realized-PnL — no new closure
  path. The one unproven §3 assumption — after-hours `gtc` stops rest — was **probed PASSED**
  (2026-07-25). Implemented by codex, verified independently: `make ci` **1809 passed / 100.00%**,
  all four remote gate jobs green, fleet retagged **14/14 → `:s142`** (`ca57fff`), `DeployRecord
  …:s142:ca57fff` written. **Functionality check PENDING** the next 22:30 UTC run — watch for a
  real `BrokerStopOrder` placed at Alpaca for a held name and the analyst deferring to it. *(A
  scripting error of mine emptied the 12 new files mid-verify; recovered via codex re-emit and
  re-verified. Root cause: a wrong "repo is CRLF" memory — the repo is **LF**; now corrected.)*
- **Exit authority: alpha proposes, risk disposes (feat, 0.76.00, 2026-07-24 — ADR-0017).** The
  question the closure work surfaced — *when the monitor's mechanical exit and the analyst's
  thesis disagree, which wins?* — is now settled and built. The analyst is the **sole
  discretionary exit author**; a **breached stop is forced onto the same rail regardless of
  confidence** (`decide(held=True)` short-circuits to a `sell` with `exit_trigger="stop"` before
  the thesis check — alpha cannot veto risk on the downside); the monitor **stops authoring exit
  decisions** and instead raises a `Fault` when a stop is breached-but-unsold (DL-57 visibility);
  `target`/`time` retire into deferred strategy; the dead `order_from_close`/`execute_close` path
  is removed (one rail, DL-60). Stop arithmetic moved to `contracts/stop_rule.py` (agents never
  import agents); `contracts/positions.open_position_stop_thresholds` does quantity-weighted-avg
  entry and **raises rather than guesses** if lots disagree on `stop_pct`. Built by codex
  (xhigh), verified independently: **`make ci` 1786 passed / 100.00%**, EOL churn on 4 files
  restored to CRLF, all four remote gate jobs green before merge, fleet retagged **14/14 → `:s141`**
  (`29a36f4`), `DeployRecord …:s141:29a36f4` written. **Functionality check PROVEN**
  (`sched-2026-07-24`): first-ever forced stop — `MRVL exit_trigger='stop'` at conf 0.637 >
  0.5 floor overrode a hold thesis; monitor silent (`closes=0`) and raised the breach Fault;
  sell reached the broker (`submitted=3`), fill queued for the open. Durable stop stays
  broker-native (ADR-0015 §3, still open).
- **Realized PnL belongs to a fill + the ledger repaired (fix, 0.74.03, 2026-07-24).** The monitor
  computed `pnl_cents` at **decision** time, so profit factor and expectancy rested on trades that
  never happened. The monitor no longer writes it; the reporter skips anything marked
  `pnl_invalidated_at`; and — the DL-57 lesson again — `collect_trade_outcomes` now **omits**
  `profit_factor`/`expectancy_cents` when there is no evidence instead of emitting a confident
  `0.0`. `scripts/repair_close_pnl.py` **appends** markers rather than rewriting history (the store
  is append-only, and the wrong number staying visible-but-marked is the better audit trail).
  **Applied to production:** 7 of 7 entries marked, `manual_review=0`, `pnl_cents` preserved, re-run
  a no-op (`skipped_invalidated=7`), reporter now returns `{closed_trades_with_pnl: 0.0}`.
  `make ci` 1762 passed / 100.00%. Fleet **`:s139`** (`9a8a88c`), `DeployRecord` written.
- **Live proof of evidence-based closure (2026-07-24, run `check-s138-unstrand` on `:s138`).** 7/7.
  Analyst **`scored=10`** — **AMD, CSCO, HPE, MRVL evaluated for the first time since 07-20**; PM
  `approved=1`, all 9 held names skipped `hold_recommendation`; execution `submitted=1 rejected=0`.
  **ABT closed by evidence** (`broker_absent=True`, sell Fill `broker_status=filled`), leaving graph
  holdings an exact match to Alpaca. **Three closes decided — nothing stranded.** Acceptance
  `UNPROVEN` (queued for the open). Windows restored and verified.

- **Evidence-based position closure — the stranding root cause (fix, 0.74.02, 2026-07-23).**
  `_is_open_position` removed a position from the book the moment a `CloseDecision` existed. A
  decision is **intent, not evidence** — and because the monitor's closes reach no broker, four
  positions still held at Alpaca (AMD, CSCO, HPE, MRVL) became invisible to every future run:
  unscoreable, unexitable, unreconcilable, with each run stranding more. The correct mechanism
  already sat beside it: `reconcile_positions_from_latest_snapshot` marks a Position
  `broker_absent` when its ticker leaves the broker holdings (DL-44 — the broker is truth for
  holdings). Decision-based exclusion **deleted**; `monitor/store.is_open_position`,
  `surfaces/queries/positions.py` and `execution/reconciliation_store.py` now share **one**
  closure predicate so they cannot drift. **PROVEN against the live graph:** held tickers read
  `ABT, AMD, BAC, CSCO, HPE, MRVL, PYPL, USB, WFC` — all nine, exactly matching Alpaca; the four
  stranded positions are back. `make ci` 9/9, **1755 passed, 100.00% coverage**, verified
  independently of the agent that wrote it; all four remote gate jobs green before merge.
  **ADR-0015 §2 corrected, not implemented:** "merge re-decisions into one position-keyed node
  carrying the latest `run_id`" is **not representable** — `kernel/graph_support.py` is
  append-only and refuses to overwrite a property. In an append-only store a re-decided exit is
  a new fact, so the `CloseDecision` key stays run-scoped. Also folds in the `status.ps1` fixes
  (replicas counted in PowerShell; a failed probe prints `?` not `0`; wake window with
  awake/asleep; named columns; all **14** deploy targets counted).
- **Exit orders keyed on the position, not the run (fix, 0.74.01, 2026-07-23).** With sells
  finally reaching the broker, `order_from_intent`'s run-scoped key was an **oversell hazard**:
  `run_id` is new every night and becomes Alpaca's `client_order_id`, so an unfilled sell would
  be re-submitted as a *second distinct order* the next night, and a third after that. Sells now
  key on `f"exit:{position_ref}:{ticker}:sell"`, a sha256 of the sorted open `Position` node
  keys — unchanged holding replays instead of duplicating, and a partial fill or re-entry
  changes the node keys and correctly re-attempts the remainder (ADR-0015 §5 falling out of the
  key). Buys keep their run-scoped key, asserted byte-for-byte. `make ci` 1752 passed, 100%.

- **S135 — one run, one evidence set, both directions (0.74.00, 2026-07-23) — THE SELL SIDE FINALLY
  EXECUTED.** Entries and exits were decided by two systems on two bodies of evidence: a buy passed
  provider facts + analyst scoring + PM gates + an LLM veto; a sell was three hardcoded numbers on
  prices alone. The book showed the cost — BAC 171→338→503, USB 160→320→478, WFC 116→233→348,
  re-bought nightly, never trimmed, until `regt_buying_power` hit 0. **Shipped (ADR-0016):** the
  analyst scores scanner survivors ∪ open held positions on the same snapshot/regime (held names
  bypass the scanner, whose filters are entry-selection criteria) and emits buy/hold/sell — the
  `held` branch returns *before* the buy path is reachable, so anti-pyramiding is **structural**;
  the PM sizes both directions into one `OrderIntentSet`; sells ride the **existing buy rail**, so
  **DL-60's missing close-dispatch became moot rather than built**. Held-position reading moved to
  `contracts/positions.py` with `monitor/position_book.py` delegating (no second copy to drift).
  Conservation became `analyst.scored <= scanner.survived + analyst.held`; older runs carry no
  `held_count` so the bound degrades and no history breaks. **PROVEN:** `make ci` 9/9 exit 0,
  **1748 passed, 100.00% coverage**, import-linter 4 kept/0 broken, live `pip-audit` clean —
  verified independently of the agent that wrote it; remote gate green on all four jobs before
  merge; fleet `:s136` from `1b858e7` with `DeployRecord` written after verification. **Live check
  (register 2026-07-23):** `check-s136-sell` 7/7 → **`ABT sell qty=98 type=market accepted
  id=fc7f075f`** — the first sell order in the system's history; `qty=98` matched the real held
  quantity, not the retired `close_quantity=1` fixture (DL-58); acceptance returned **`UNPROVEN`**,
  correctly refusing to call a queued order a pass (DL-59). `check-s136-clean` 7/7 proved the other
  half — all 7 held names `hold`, every one skipped `hold_recommendation`, only the genuine new
  candidate approved. **Teardown:** override removed (analyst env back to its 5 vars, secretRefs
  intact), KEDA windows restored to `22:30-00:30Z` and verified against backup, litter run torn
  down (9 edges/9 nodes); the two runs with real meaning retained — deleting the lineage of a live
  broker order would manufacture the exact DL-44 divergence we spent the day fixing. **NOT DONE:**
  ADR-0015 fill-keyed closure (stranded count now 4 and growing), realized-PnL repair where
  decision-time `pnl_cents` was booked without a fill, and exit strategy proper.
- **Status board fixed (chore, 2026-07-23) — A BROKEN PROBE READ AS A FACT.** `infra/status.ps1`
  showed `replicas=0` for the whole fleet while every app had a live replica: on Windows `az` is a
  `.cmd` shim, PowerShell strips the quotes, and `cmd` chokes on the parentheses in
  `--query 'length([])'` — exit 255 → `$null` → rendered `0`. Third instance of the DL-57 pattern in
  one day. Counting moved into PowerShell; a failed probe now prints **`?`**, never `0`; and the
  board gained the **wake window** with `awake`/`asleep`, so a legitimate scale-to-zero reads grey
  while `0 while awake` — the only genuinely broken case — reads red. Columns are now named and
  grouped: identity (`APP`) │ deployed (`DEPLOY`, `IMAGE`) │ running (`PODS`, `POWER`, `WAKE`).

- **Fleet on `s135` + the sell side proven still unbuilt (2026-07-23) — INTENT WAS NOT OUTCOME,
  AGAIN.** Deployed `s135` from `c7ccdb0` (all 14 targets, config intact, `DeployRecord` written),
  then widened the KEDA windows to fire a real run and **restored them, verified identical to
  backup** (master `25 22`, twelve agents `30 22`, all `end 30 00`). `sched-2026-07-23` ran
  **7/7** on the new images. **PROVEN WORKING:** the DL-58 `GraphFaultSink` — the first `Fault`
  nodes ever written (`provider returned no current price for HPE` / `MRVL`, so those two are
  silently skipped every run); and the DL-59 gate, which returned **`UNPROVEN`** on the live run
  instead of a false PASS. **PROVEN FAILING:** the monitor decided `CloseDecision CSCO close
  trigger=time` and the broker's lifetime sell count stayed at **0**, with **no fault recorded**
  — nothing was attempted. Root cause (DL-60): `dispatch_closes` exists only on the **bus RPC**
  path; the deployed **graph-pull** path writes the decision and stops, and execution's poll
  handles `PMRun` buys only. **There is no graph-pull consumer for close decisions anywhere — the
  sell side is unbuilt, not broken.** DL-58's fix was necessary but insufficient: it corrected the
  payload of a message nothing sends. Design note **DL-60** written (lifecycle: a position is
  closed by a **fill**, not a decision — decision-time `CLOSES` is what stranded AMD forever, and
  decision-time `pnl_cents` books realized PnL at a price nobody traded at). **Blocked on
  operator:** exit timing (a once-daily after-hours stop executes at the next open) and AMD
  recovery. 5 more unfillable buys cancelled; `regt_buying_power` still 0.

- **Acceptance scores outcome, not intent (fix, 0.73.02, 2026-07-23) — THE GATE COULD NOT SEE
  TWO DEAD DAYS.** DL-58's named limit, closed. The gate's boundaries were all *conservation*
  checks, and `execution.submitted` is an **intent count** — it says orders reached the broker,
  never that the broker did anything with them. So 07-21 (all five orders rejected at the open,
  `regt_buying_power=0`) and 07-22 (five more against zero buying power) both scored
  `ACCEPTANCE PASS`. **Fix (DL-59):** `FillOutcomes` classifies a run's Fill nodes by real broker
  outcome (`broker_status` overrides submit-time `status`), and a fourth verdict **`UNPROVEN`**
  names the third state — filled → PASS, all resolved unfilled → **FAIL**, still queued →
  UNPROVEN (exit 0, never rendered as PASS). Counted from Fill nodes, **not**
  `ExecutionRun.submitted`: a broker refusing at submit time leaves `submitted=0`, so scoring
  intent would pass exactly that run. Dashboard: UNPROVEN stays **GREEN + warning row**
  (a nightly false RED trains the operator to ignore the light — DL-47), summary "N orders
  placed, none filled yet"; a real fault is still RED. **Proven:** `make ci` exit 0, 9/9,
  1737 passed, 100.00% coverage; end-to-end test drives a rejecting broker and asserts FAIL with
  `submitted=0, orders=2, unfilled=2` proving intent ≠ outcome; **replayed on the three real
  runs — 07-20 `PASS`, 07-21 `FAIL` ("0 of 5 submitted orders filled … the run traded
  nothing"), 07-22 `UNPROVEN`.** **Named limit:** proves *whether* orders filled, not *how well*
  (slippage/partials unscored); and a run stays UNPROVEN until acceptance is re-run after the
  open, which nothing yet does automatically.

- **Exit path made executable + faults made visible (fix, 0.73.01, 2026-07-23) — THE STACK
  COULD ONLY BUY.** A routine run review found `sched-2026-07-22` green (7/7, `ACCEPTANCE PASS`)
  while the system had been incapable of selling since inception: **zero sell orders in the
  broker's entire 33-order history.** The monitor stopped us out of AMD on 07-20
  (`CloseDecision`, `trigger=stop`, `pnl_cents=-153065`); no order ever reached Alpaca; we still
  held 55 shares. Two defects (DL-58): `CloseDecision` carried no quantity or price, so execution
  substituted `close_quantity=1` / `close_reference_price=$1.00` — tunables whose own `why=`
  admitted they were fixtures; and `dispatch_closes` swallowed failures into an in-process sink,
  so `surfaces/queries/faults.py` — the operator incident view — had been **empty by
  construction** and read as "no incidents". Buy-only execution then ratcheted the account to
  `regt_buying_power=0`; **all five orders on 07-21 were rejected at the open**, and 07-22
  submitted five more against zero buying power, both days scoring PASS. **Fix:** `CloseDecision`
  gains required `quantity` + `reference_price_cents` (contract 0.2.0 → 0.3.0), monitor
  populates both, `order_from_close` reads them, both fixture tunables **deleted**;
  `GraphFaultSink` appends a `Fault` node on all four graph-pull poll paths, keyed by
  origin+timestamp so recurrence appends. **Proven:** `make ci` exit 0, 9/9 steps, 1719 passed,
  100.00% coverage; a new test drives a 55-share stop end-to-end and asserts the broker saw
  55 shares at $94.00 (it saw 1 @ $1.00 before); a second asserts a swallowed dispatch failure
  lands as a queryable `Fault`. **Operator action taken:** the 5 unfillable 07-22 orders were
  cancelled at the broker (verified `canceled`, 0 open). **NOT fixed — named limit:** the
  acceptance gate still scores stage completion, not whether an order can fill, so it passed on
  two dead days; and **AMD (55 sh) is still held** against a 07-20 close decision — the code
  path is fixed, the stranded position is not yet resolved.

- **Gate self-test (chore, 0.73.00, 2026-07-22) — PROVING THE CHECKS CAN FAIL.** Three gates read
  green in one day while examining nothing: the security gate had run on **zero** sprint merges
  (DL-52), a STATE claim had no check able to contradict it (DL-54), and the secret sweep could not
  see new files (DL-55). Shared defect: *"didn't look"* rendered identical to *"looked and found
  nothing."* `scripts/gate_selftest.py` plants a violation per gate and requires a non-zero exit,
  and asserts the config facts whose loss silently disables a gate (the `push` triggers, the
  Makefile line wiring the untracked scan). Runs in CI `quality` on **every push** so it cannot rot.
  **Proven both directions at introduction:** 7/7 on a healthy tree; removing the `push` trigger —
  the exact DL-52 regression — made it exit 1 naming the invariant, and neutering a case to a
  command that always exits 0 made it exit 1 too. **Named limit:** it only tests failure modes
  someone imagined; it stops known blind spots regressing, it does not promise there are no new
  ones (DL-57).
- **Credential-delivery audit (chore, 0.72.00, 2026-07-22) — A CHECK THAT CAN CONTRADICT THE
  STATUS DOC.** Asked to apply the S131 Postgres flip, the audit-before-acting found it **already
  applied** — STATE had carried a false pending item for two days (DL-54). The real gap was that
  *no cheap check could disprove it*: a flip rewrites the secret's **value** while the env var name
  stays identical, so `preflight` and `az containerapp show` read the same before and after a flip
  **and after a rollback**. `scripts/cred_audit.py` reads the delivered value, reports the role it
  names, and connects as it — verdicts `scoped` / `scoped-degraded` / `shared` / `cross-wired` /
  `unreachable` / `missing`, `--strict` exits non-zero unless all 14 are scoped. **`cross-wired`
  (a target holding another agent's role) is a defect neither the flip script nor preflight could
  ever surface.** Live: **14/14 `scoped`**, `master` correctly `bus secretRef: none`; the negative
  run exited **1** — the check can fail, which is what makes the pass mean anything. 13 unit tests,
  `make ci` exit 0 @ 100 %. Runbook in `deployment.md`.
- **S133 — per-agent Service Bus SAS (0.71.07, 2026-07-22) — THE LAST SHARED CREDENTIAL IS
  CLOSED.** Every container held the same namespace-level `RootManage` connection string; now each
  of **13 bus targets** carries its own **entity-level topic SAS** with a Send/Listen split —
  **33 rules, `cap_violations={}`** (planner output reproduced independently at verify, matching
  the handback exactly). Azure's **12-rule cap** per namespace *and* per entity is what forced the
  per-topic model: 13 agents don't fit 12 namespace rules (DL-53). The grant matrix is **derived
  from source** (`scripts/sb_sas_plan.py` reads `serve_transport.py` + publish topics), not a
  hand-kept list that drifts. Delivery mirrors S131: per-target Key Vault secrets → Container Apps
  `secretRef`, `-UseSharedServiceBusDsn` rollback retained. **`master` was given no bus rights
  rather than an invented permission** — its Service Bus env is removed. Live proof: scoped
  Send/Listen served a request, an out-of-scope Send was **refused**, and revoking one rule locked
  out **only** that identity while the fleet stayed `Succeeded`; canary topics torn down to zero.
  **Backlog row I → Done, leaving no open hardening rows.** Verified at merge: `make ci` exit 0 @
  100 %, no key in the tree, and the credential-fallback path checked to **fail closed** (the
  per-target "primary" secret is itself a scoped grant, so a bundle miss cannot reach `RootManage`).
  *Honest limit:* proof used disposable canary topics, not a production container-origin run —
  that capture is an operator follow-up. Merged via PR #63 with the gate green (the PR requirement
  was reversed hours later — DL-56; the gate now runs on push to every branch).
- **Security-gate repair + backlog row L (chores on 0.71.06, 2026-07-22) — THE GATE THAT NEVER
  FIRED.** Investigating one red check on a Dependabot PR unwound five stacked defects: the
  `SECURITY_FINDINGS_TOKEN` was absent from the **Dependabot** secret store (separate from
  Actions, so it resolved empty); the replacement PAT lacked read access to the private toolset
  (403); the gate then flagged 6 error-level `py/undefined-export` alerts — all **false positives**
  from S131's PEP 562 lazy exports (CodeQL cannot follow `__getattr__`), dismissed with reason;
  **the gate is `pull_request`-triggered, so S131/S132/S134 — each merged directly with no PR —
  were never gated at all**; and `GITHUB_TOKEN` auto-merges fire no `push` workflows, so four
  dependency merges landed without rebuilding images (`:latest` stale and unscanned). Fixes: the
  gate was first made to fire by requiring PRs, **since replaced** by triggering it on push to every
  branch (DL-52 → **DL-56**: on a one-developer repo a PR buys no review, so the trigger was the
  only thing being bought); the whole investigation + named residual
  risk is **DL-52**, the 5-PR dependency backlog (frozen ~2.5 weeks) was drained, and setuptools
  was bumped for CVE-2026-59890 (not reachable — sdist/macOS-only — cleared for signal hygiene).
  **Row L Done:** the container entrypoint smoke went from provider-only to **all 12 agent
  images** — DRIFT-016/017/018 were the *same* defect three times ("unit gate hid it"). Verified
  by dispatch run `29904029290`: 14/14 jobs green and all 12 images printed the assertion,
  confirming the step *fired* rather than silently skipping. Merged `d54fd54` (PR #59).

- **S134 (assertion hardening, row K, 0.71.05→0.71.06) — ROW K CLOSED HONESTLY, IN THREE ROUNDS.**
  A planning verify gate ran between each round, and the first two did not pass it. R1 killed the
  alpaca money-parser bucket (39→7 named residuals) plus the PM gate/reward-risk/sector
  boundaries — but relabelled ~250 analyst math survivors "equivalent" using one template note
  repeated on all 274 rows, so it was **bounced**. R2 took the targeted analyst survivors
  **249→127** with a real per-module before/after table and honestly held row K at *Partial*
  rather than closing it. R3 forced **all 127** into an auditable per-mutant disposition —
  **107 killed, 12 individually justified equivalents, 8 named wording exclusions, 0 un-triaged**
  (`round-3-dispositions.csv`; the anti-template gate held — 20 non-killed rows, 20 *distinct*
  reasons). Scoped decision-engine kill-rate **79.87 % → 84.36 %** (5,678/6,731). Test+docs only:
  no production source, no `pragma` removed (81/81), mutmut stays manual. Planning re-ran
  `make ci` on the branch and on the merge result (1692 passed / 6 skipped / 100 %).
  **Merged `d831260`, tag `v0.71.06`** (GitHub CI + CodeQL + image build all green).

- **S132 (mutation testing, row G, 0.71.04→0.71.05) — TESTS THAT ASSERT, NOT JUST EXECUTE.**
  `mutmut` over the deterministic decision engines as a **manual periodic exercise, not a CI
  gate**: +94 mutants killed with cited tests, scoped kill-rate 78.47 % → 79.87 %. Survivors were
  dispositioned in a committed report rather than deleted. That report is what S134 then acted on —
  and the review of it found the "rainy day" parking had under-called ~130 genuinely killable
  survivors. Merged `15c23d6`, tag `v0.71.05`.

- **S131 (blast radius, rows I+J, 0.71.03→0.71.04) — 15 IDENTITIES INSTEAD OF ONE DSN.** Per-agent
  Postgres runtime identities: 15 `ta_<agent>` roles, per-role Key Vault DSNs, secret-backed
  Container Apps delivery, and a revocation canary; plus the dispatcher image slimmed to its
  measured 43/44-file import closure (row J). Live: role provisioning/flip/canary proven, a
  controlled `pg_stat_activity` audit saw all 15 roles. The Service Bus connection string remains
  the **last shared credential** → row I part 2 = S133. Merged `0ca7459`.

- **S130 (base image, row H / R005, 0.71.02→0.71.03) — ALL 14 IMAGES OFF DEBIAN.** Two-stage
  Docker Hardened Images (`dhi.io/python:3.13-dev` → `dhi.io/python:3.13`) with venv-carrying
  runtimes, and Trivy keeping HIGH/CRITICAL enforcement with `ignore-unfixed: true` while
  `.trivyignore` stays empty. Actionable findings dropped **22 → 0**; manual run `29681635979`
  built/pushed all 14 `s130-test` images through every Trivy gate. Merged `8aefe2a`.

- **S129 (fixpack + GitHub hardening, 0.71.01→0.71.02).** Quant-evidence persistence into
  Recommendation/veto context plus dashboard read-cache egress reduction; and the supply-chain
  lane: dependency review on PRs and Trivy container scanning, both SHA-pinned. Merged `3be1ee8`.

- **S128 (feed resilience, DRIFT-021, 0.71.00→0.71.01) — ONE 429 COSTS ONE TICKER, NOT THE FEED.**
  Per-request Finnhub pacing (55/min tunable budget) and per-ticker fault attribution across all
  four enrichment feeds, with durable attributed notes on the graph quality trace; the real rate
  limit was used as the fault injector. Live check PASSED (paced 99/99, zero degraded notes in
  7 min; unpaced runs showed per-ticker `:429` attribution with the majority kept). **This is the
  sprint that unblocked trading**: `sched-2026-07-20` then ran 7/7 ACCEPTANCE PASS with zero
  degraded feeds, flipping the chronic all-reject signature into 5 buys. Merged `09120b3`.

- **S127 (fixpack, 0.70.00→0.71.00) — FLAGS ARE ACTIONABLE; CURRENCY JUDGES THE TEMPLATE.**
  Backlog rows 4/9/10/11/12 in one sprint: per-flag "Acknowledge" through the audited operator
  `approve` command with the S125 confirm machinery (typed intent echoed verbatim; result is an
  appended `FlagResolution`); deterministic `approve <target>` routing normalizer + regression
  table (row 11); deploy currency judges the dispatcher by its *template* image with the last
  execution kept as evidence — a fresh retag now reads `current` immediately (row 12, proven
  live pre-fire: template `:s126`/execution `:s121` → `current`); verdict warnings deep-link to
  their evidence panels; the bus integration test skips without the azure extra. Live check
  acknowledged exactly one stale warn flag (`15bb3e29df185949`, pending 2→1); the one critical
  divergence flag remains for the operator. Evidence + 5 screenshots in
  `docs/reports/sprint-127-fixpack/`. **First sprint under the DL-48 contract — drift rule
  held (main unmoved at `a823763`), closeout + return notes arrived filled, nothing bounced.**
  Codex-built; planning review re-ran `make ci` (exit 0, 1584 passed / 5 skipped / 100%).
  Merged `32c73cc`.

Older sprints — **S102–S126 → [STATE-05.md](state-archive/STATE-05.md)** · S99–S118 + chores →
[STATE-04.md](state-archive/STATE-04.md) · S77–96 → [STATE-03.md](state-archive/STATE-03.md) · S37–76 →
[STATE-02.md](state-archive/STATE-02.md) · S36→P0 → [STATE-01.md](state-archive/STATE-01.md); full index
`docs/sprints/README.md`.

## Now

**🟢 S145 is SHIPPED, DEPLOYED, and PROVEN**
([sprint-145-exit-replay-append-safe](sprints/sprint-145-exit-replay-append-safe.md), 0.80.02,
`2c49f88`, [DL-71](design-log.md) option A): `make ci` **1856 passed / 100.00%**, remote CI +
Security Findings green on the merge tip, `Build and push agent images` green on `main`,
`v0.80.02` tagged, **fleet retagged `:s143` → `:s145`** (14/14 verified on tag, config intact,
`DeployRecord` written after verification), the **resumed run scored `7/7 stages complete`**
where it had crash-looped at 4/7, and a **full fresh cascade then scored `ACCEPTANCE PASS`**
(`confirm-s145-20260728`, 7/7). Execution wrote `submitted=2 rejected=0 skipped=1` on the resume
and `submitted=1 rejected=0` on the fresh run, adopted every existing order instead of duplicating
it, and created exactly **one** new broker order across both — SCHW's missing protective stop.
**The one item still open** is the realized outcome of `sched-2026-07-27` itself: its acceptance is
`UNPROVEN - completed` because AMD sell 55 and ABT buy 95 are queued for the 13:30 UTC open.
Re-run `accept.py --run-id sched-2026-07-27` after the open for the realized verdict.

**⬜ DL-73 — RETRACTED IN FULL the same day; the defect does not exist.** I audited `Position` nodes on `status == "open"`, which is **not** the active-position predicate. The real one is `contracts/positions.py::is_active_position_node`, which also excludes `broker_absent` **and `broker_superseded_by`** — and `reconcile.py` has always called `_mark_superseded` / `_mark_absent`. Re-audited correctly: **23 nodes, 9 active — exactly one per held ticker, every quantity matching the broker** (ABT 96/96, AMD 55/55, BAC 503/503, CSCO 177/177, HPE 229/229, PYPL 175/175, SCHW 196/196, USB 478/478, WFC 348/348). The 14 "phantoms" are a correct supersession chain (`BAC 171→338→503`, `USB 160→320→478`, `WFC 116→233→348`) plus two correctly `broker_absent`. The "unexplained mitigation" was my own measurement error: the PM sized AMD at 55 because the predicate filters superseded nodes, as designed. Two further claims from that audit are also withdrawn — the "3 fabricated rejections" are `rejected_broker_fill`'s documented `rejected:{key}` sentinel for pre-submit refusals (all three `HTTP Error 403: Forbidden`), and `canceled`→`rejected` is a deliberate four-value `BrokerStatus` contract that keeps the raw word in `reason`. **The lesson (kept, not deleted):** an audit that does not use the code's own predicates audits my assumptions, not the system. **What genuinely survived** is in [sprint-146](sprints/sprint-146-unprotected-position.md).

**🟢 S146 SHIPPED, DEPLOYED, PROVEN — and the cause is now known.** Merged `96dfa6f..7b06662` (0.80.03, `v0.80.03` tagged), fleet retagged **`:s145` → `:s146`** (14/14 `Succeeded`, 13 apps + `dispatcher-cron` verified on tag, env vars and `daily-agent-window` intact at `minReplicas=0`, `DeployRecord …:s146:7b06662` written after verification), and run `confirm-s146-20260728` scored **`RESULT 7/7 stages complete`** on the deployed code. **ABT's stop was never a code bug: Alpaca refuses it as a wash trade** — `code 40310000`, `"potential wash trade detected"`, `reject_reason: "opposite side market/stop order exists"`, `existing_order_id: fd1f1c2c…` — which is the **ABT buy 95 orphaned by the 07-27 crash**. S145's orphan and S146's unprotected position are the same event two hops apart. **What S146 actually fixed is the silence:** the refusal is now retried every run and re-surfaced as an `UnprotectedPosition` Fault — two exist, `08:05:23` (pre-deploy check) and **`09:45:02` (this run, on `:s146`)** — where previously the 403 was recorded once, days ago, and nothing ever retried. **No fabricated `BrokerStopOrder`** was written (still exactly 7, none ABT), and the PM's re-approved `AMD sell 55` **adopted the existing broker order rather than duplicating it** (AMD market sells at the broker: exactly 1). The **4 orphan PM-run fills are repaired** and present with real broker ids; the second `--apply` was idempotent. **DRIFT-024 opened** (law gap: execution's LOCKED constitution declares neither `BrokerStopOrder` state nor a fallback stop parameter, despite ADR-0015 §3 depending on both — the second sighting of S138's declaration debt after S144 caught the vocabulary half). **Still open, honestly:** ABT remains `held=96 stop_qty=0` and **stays that way while that buy order is open**. It should clear once the buy fills at the 13:30 UTC open and a subsequent run retries — that is the next thing to verify, not a claim.

**🟠 S147 IS PACKAGED — DL-71 option B, the last open half of the outage's root cause.**
[sprint-147-fresh-book-before-decision](sprints/sprint-147-fresh-book-before-decision.md) (feat →
**0.81.00**), handed to Codex under the [DL-74](design-log.md) law-first MUST RULE. **Every decision
this system makes is made against a book at least one full run old.** Broker truth arrives at stage
5 (`reconcile_run_start` writes a fresh `BrokerPositionSnapshot`), is adopted at stage 6
(`reconcile_positions_from_latest_snapshot` heals the `Position` book), and is consumed by the
analyst at stage 3 — *of the next run*. Across the 07-25/07-26 weekend skips that gap was **three
days**, which is why the analyst authored `MRVL sell` for a position that had already sold and
bricked the fleet. The fix is a **head-of-run position sync**, and its shape is decided by law
rather than preference: `MON-IDN-02` reserves `Position` writes to the monitor and `EXEC-IDN-01`
reserves the broker to execution, so it ships as **two agents in a new order** — execution refreshes
the snapshot, the monitor reconciles, and the analyst is simply not pending until both have
happened. Only the *triggers* move, so DL-71's ownership worry does not materialise. Carries a
**20-test plan** (each test named with the violation it must plant, DL-70) and the
`BROKER_RESUME_STAGES = frozenset(RESUME_STAGES[:5])` **index trap** — inserting a stage at the head
shifts every index, and getting it wrong stops the supervisor warning before a resume that really
does submit orders. **Complementary to ADR-0018, not an alternative:** ADR-0018 stops a stale
decision surviving the night; S147 stops it being made.

**PROVEN (LAW-02) — what the merge actually established.** One attempt = one immutable `Fill` node
with the broker `client_order_id` unchanged (the 0.74.01 oversell guard stands); a `filled` exit is
never re-issued and the skip is a visible `Fault`; a per-intent failure degrades to a per-intent
fault so one ticker cannot cost three stages (DRIFT-014 / S128 restated for order submission). Each
was observed **failing** on a planted violation first (DL-70), and all three were re-proven against
the live Neon spine with teardown to zero. Gate self-test 14/14.
**Those success factors are now all met** (2026-07-28): the fleet retag to `:s145`, the resumed run
at **7/7** with MRVL out of the book and SCHW carrying its stop, and both orphaned orders adopted
rather than fabricated. S144's dated vocabulary enablement remains sequenced after, and is still
open.

**🟢 S146 SHIPPED** — [sprint-146-unprotected-position](sprints/sprint-146-unprotected-position.md)
(0.80.03, merged `7b06662`, fleet `:s146`, `ACCEPTANCE PASS`). Its predecessor packet
(orphan-fill lineage, [DL-72](design-log.md)) was **superseded**: the two orphans it targeted healed
themselves on `:s145` exactly as DL-72 predicted, and the audit that followed found the real gap was
an unprotected position, not a lineage lie. It also ran the [DL-74](design-log.md) **law-first
trial** — the coding agent read the governing constitutions before writing code, recorded which
clauses bound each element, and surfaced **DRIFT-024** (a genuine law gap) *before* implementation.
Verdict recorded in the sprint doc: it changed the approach on 4 of 7 elements and found no
law/spec contradiction.

The hardening backlog has **no open rows** — S133 closed the last one. Other queued work is in
*Next*; the standing operator items below are the only other outstanding threads.

**Fleet:** standing on `:s145` (retagged and verified 2026-07-28 — all 13 apps + dispatcher on the
same tag, built from `fcd81a4`), self-driving in paper mode — the calendar-gated 22:30 UTC
`dispatcher-cron` fires nightly, KEDA scale-to-zero, idle ≈ $0. **It now fires into the fixed
execution agent; that the fix holds is unproven until the run completes.** **Both scoped-credential
flips are applied live** — Service Bus (S133) and Postgres (S131) — so the running fleet holds
per-agent identities on both. Verified end-to-end 2026-07-22: all 14 app-delivered DSNs connect as
their own `ta_*` role with the spine privileges, and all 13 bus targets carry scoped SAS
`secretRef`s. Shared credentials are retained, unused, for rollback only.

**Awaiting the operator (two standing items, none blocking):**

1. **Broker-divergence Flags (07-09 / 07-14 / 07-15)** still need acknowledgement — actionable
   from the dashboard since S127.
2. **Container-origin identity capture (S131 + S133, one errand)** — both sprints proved their
   scoped identities with controlled checks rather than by firing a production run out of hours
   (the honest, conservative call). During one live KEDA window, repeat the `pg_stat_activity`
   query *and* capture Service Bus sessions, to see both under real container origin.

**P12 sentiment scorecard-run** stays queued until roughly two weeks of clean-news nights
accumulate; the runway began 2026-07-20 and cannot be short-circuited.

**Standing principles (DL-19 etalon-first):** remaining gray law clauses go green with cited
tests; **every sprint ends with a real-environment functionality check**
([`laws/functionality-checks.md`](laws/functionality-checks.md)) plus teardown; each sprint or
chore lives in **its own worktree on its own branch**, and is **pushed and seen green on the
remote before it is merged locally** (DL-56 — no PR required; the `gate` now runs on push to every
branch, so pushing *is* the gate). Merge to `main` is the deploy trigger that rebuilds and pushes
agent images.

## Next

- **🟢 Tomorrow morning: read tonight's 22:30 UTC run — the first *scheduled* run on `:s151`.**
  Today's proof was a resumed run with `approved=0`, so it proved the **structure** (sweep completes,
  snapshot lands, 8/8, stops intact) and deliberately not the trading path. Tonight adds what it could
  not: a sweep running at the head of a *fresh* run, and the first chance for a real ADR-0018 drop
  rate. **Check in this order: (1)** the run reaches 8/8 without a `position_sync` stall; **(2)** the
  drop count — **now meaningful**, since today's run cleared the 07-22/07-23 backlog of 11, so
  anything tonight is a genuine per-session number; **(3)** the nine stops, again. Both challengers
  (S149 tolerance, S150 stops) stay off until that baseline exists.
- **🟠 `chore-exec-fail-03-coverage` is with codex** (`0.84.02`, branches off `main` post-S151).
  Closes the two untested halves of `EXEC-FAIL-03` — *the idempotency key prevents re-submission to
  the broker* (assert the broker receives exactly one order after a write failure + retry; the half
  that actually protects capital) and *a repeated graph write appends a new record*. Flip to 🟩 and
  move all three counters to 31 / 49 **only if both land**; untestable without production changes is
  a finding, not a widening. Also adds the standing convention: *a `test-plan.md` clause summary
  mirrors `laws.md` and is never reworded to fit an available test; partial coverage keeps the
  clause ⬜ and names what is missing.* **That convention is the durable fix** — summary drift is
  what let the over-claim through, and it will catch the next one regardless of who is working.
- **⚠️ The 11 drops on 2026-07-31 were the backlog clearing — do NOT read them as the drop rate.**
  Eleven `Fill` nodes from the 07-22/07-23 cancelled runs had been sitting in the colliding state
  (`broker_status=rejected`, `drop_reason=None`) since before ADR-0018 existed, and all cleared on
  the first sweep that completed. **ADR-0018's real per-session drop rate is still owed** and starts
  accruing tonight. **Both challengers (S149 tolerance, S150 stops) stay off until that baseline
  exists**; they are measured *against* the flat champion's live behaviour, so promoting before it
  exists would compare against nothing.
- **🟠 Filed, deliberately not in S151: fault de-duplication / retry backoff.** One deterministic
  defect wrote 5,762 identical rows because nothing between it and `work_loop` was contained. S151
  makes it impossible *on this path* by construction (a completed snapshot ends the loop), but the
  general version is a kernel/`work_loop` concern affecting every agent and needs its own sprint.
- **🟠 The law book is behind its code in five places, and it is no longer one agent's problem.**
  DRIFT-024/025/026/027 are execution (broker-stop state, `BrokerPositionSnapshot`, the tolerance
  tunable and drop semantics, S149's additions); **DRIFT-028 is the analyst**. Five consecutive
  sprints have each opened one. This wants **one law-amendment cycle** covering all five, not a
  sixth register row — and the fact that it now spans two agents means the gap is in how laws are
  maintained, not in any single constitution. **Now packaged as [S152](sprints/sprint-152-law-amendment-cycle.md)**, which names the cause: [conventions §4](laws/conventions.md) forbids amending a law *to match what the code does*, and every sprint doc tells its agent `laws.md` is read-only — so each sprint took the only sanctioned action and appended a row. The package carries the distinction that unblocks it: **decided in an ADR then built = a lacking declaration (amend); merely appeared = code drift (do not amend)**, applied and reported per clause.
- **🟢 DONE (0.84.03) — property completeness before S144 is enabled.** Shipped as
  `chore-vocabulary-property-completeness`: `Fill` and `Recommendation` are now proven supersets
  with zero blind sites, and a regression fails `make ci`. **What remains is a decision, not a
  gap:** whether to declare properties for the other **51** labels (49 resolve totally and could be
  generated from the scan; the pack currently enforces 2 of 71), and the `orchestration/resume.py`
  unattributed-label hole that must be closed *before* any resume-chain label is declared.
- **🟢 DONE (2026-07-31) — S144's fleet enablement.** Fleet `:s152`, `GRAPH_VOCABULARY_B64` set and
  read back verified on all 14 targets; three undeclared edge signatures found and closed first
  (0.84.04). **S144 is CLOSED**; what remains is the standing exposure it revealed: **46 `add_edge`
  sites the static scan cannot resolve**, so the signature dimension is proven only for the
  resolvable subset plus everything the live graph has exercised. Closing that wants the same
  parameter-binding treatment the property scan got — or a warn-only shadow mode, which would turn
  an open-ended static-analysis job into a bounded observation period.
- **`chore-wsl2-dev-env`** (packaged, branch pushed) — move the dev loop to WSL2 for
  native-ext4 `mutmut`/`pytest` and CI/prod parity; the 14 `.ps1` files stay and run under `pwsh`
  (verified on the operator's Ubuntu), so the real work is `.gitattributes` LF normalisation and
  a setup runbook. Must not overlap an in-flight sprint branch — the renormalise commit touches
  nearly every text file.
- **DL-50 — ADR-0007 amendment cycle:** the accepted ADR still names DockerHub while the pipeline
  ships to GHCR. Recorded as drift rather than silently rewritten; needs a proper amendment.
- **DL-46 option A** — a deploy step in CI remains the recorded end state, deferred not rejected
  (option C, the `DeployRecord` + currency judgement, shipped in S126).
- **Deliberation as a reasoning/competence source (DL-39, DIRECTION)** — the transcript's *why*,
  not the verdict, is the asset: grade whether the expert model reasons at senior-analyst level and
  learn which parameters carry the decision. Assembles DL-31 (`--score`) + DL-09 + ADR-0010/CI-2;
  needs a research item and a live runway before packaging. Companion **DL-40 (parked)**:
  literacy-tiered verdict explanations as a `surfaces/` renderer, ruling single-sourced.
- **Prompt-optimiser bake-off** — EvoPrompt / TextGrad behind the ADR-0010 `PromptOptimizer` port
  ([R003](research/textgrad/INDEX.md)), when prioritised. DL-42 shipped the compiled judge +
  challenger as live champions; defender stays hand-written.
- **Remaining DL-36 hardening** — destructive executors (`rotate-credential`,
  `recreate-instance`) stay human-manual until a provider-specific write path and an approval UI
  land.
- **Deferred behind a perfect etalon (DL-19):** CI-1..CI-6 (ADR-0013, S90–S95) · the bundle
  **generator** · the ADR-0010 reusable predictor registry/promotion (first instance landed in
  S107) · P13 cross-asset graph · the `contracts/` substrate/pack split.

## Pointers

Product `docs/PRD.md` · architecture `docs/architecture.md` · phases `docs/build-plan.md` · closed
decisions `docs/decisions/INDEX.md` · open threads `docs/design-log.md` · "does it work"
`docs/laws/{ledger,drift-register,functionality-checks}.md` · per-agent `agents/<name>/mission.md`.
