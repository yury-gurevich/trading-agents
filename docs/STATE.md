# Project State

**Last updated:** 2026-09-15 19:05 AEST · **Version:** 0.98.04 · **🟩 S206 MERGED (`8c6f74a`) and DEPLOYED `s206` — 16/16 apps + dispatcher, packs unmoved, env and KEDA byte-identical. The referee stops being shown a `FAILED` for a check no agent performs; tonight's `sched-2026-09-15` at 22:30 UTC is the first live run that reads the corrected context.**

**How to read.** *Now* = active · *Next* = queued · *Recent* = last few shipped (older detail lives in
each `docs/sprints/sprint-NN-*.md` + [`state-archive/`](state-archive/INDEX.md) `STATE-01…08.md` + git). **LAW-02:** an item is "shipped" only when
its success factors are *proven* (tests, `make ci`, the named live check) — never restate intent as outcome.
**Size rules**, after this file reached 574 lines with a **112 KB header line**: keep it **under 200
lines**, and keep the header above to **three clauses — stamp, version, one headline**. Replace that
headline each session; never append a fourth. Oldest *Recent* entries split to the archive.

---

## Current focus

**The bar, set by the operator 2026-08-20.** The etalon is done when **the pack trades unattended
for a sustained stretch and the evidence discipline catches its own defects without the operator in
the loop.** Not "trading is finished" — but far above where it is. 🚨 **Consequence for ranking:**
whatever currently prevents unattended operation *is* etalon work, not a detour from it. **Until
2026-08-22 that was the 73 % veto rate** ([DL-119](design-log.md)). It is now one level up: the
referee cannot run at all until **2026-08-30**, so the pack trades unvetoed behind a gate that is red
nightly for a non-defect ([DL-125](design-log.md)). 🚨 **A discipline that cries wolf for six
straight nights fails the second half of the bar as surely as not trading fails the first** — which
is why work-queue **item 6** (a declared advisory posture) is now ranked first. 🪤 **Generality is a separate
unproven axis:** ADR-0012's platform/pack wall stays *de jure* until a second pack exists, and
clearing this bar does not close that.

Since P14 the project runs as **etalon-first continuous improvement** (DL-19).
**The platform is self-driving in paper mode**: the DEPLOYED, STANDING fleet (16 Container Apps +
`dispatcher-cron` job, KEDA scale-to-zero windows, idle ≈ $0) places a calendar-gated `RunRequest`
at 22:30 UTC daily, runs graph-pull + served-over-Service-Bus on the Neon Postgres spine (ADR-0014),
reconciles holdings against the broker (DL-44), debates vetoes under compiled prompts (DL-42), and
proves `ACCEPTANCE PASS`. Pausing = disable the job + zero the scale windows (`docs/deployment.md`).
Completed arcs live in their sprint docs + archives: fleet (DL-35), credentials (DL-36), Postgres
migration (DL-43), deliberation quality (DL-41/42). Layer-3 acceptance 🟩 at the full S&P-500;
Layer-2 choreography 🟩 on a distributed run (S102).

## Recent (most recent first — detail in each sprint doc)

🟩 **PROVEN RESULT — [S205](sprints/sprint-205-a-type-clause-names-the-fields-it-requires.md) MERGED
`af75079` (`0.98.03`), 2026-09-15 — work-queue **item 30** closed, and a clause family stopped being its own
oracle.** The twelve `TYP` clauses that said a payload *"matches `contracts/<agent>.py` exactly"* now **name the
fields they require**, each traceable to the clause that needs it; two new guard modules fail when a required
field is deleted, proven on three agents (Scanner `skipped_filters`, Master `capability_declaration`,
Researcher `backtest`). Zero `contracts/` edits — `git diff --stat -- contracts` empty.
🟩 **Verified independently on the merged SHA, not on the handback's word:**
`assert_gate_ran.py --sha af75079346a74f402408a6795ee881666f61b051` printed `GATE PROVEN` — image build, CI,
CodeQL, Security Findings and the dependency run all green; `main`'s later tip `8faf856` is `GATE PROVEN` too,
so no S205 commit rides above a gated one (the S186 hazard). 🟩 **Local `make ci`:** 2756 passed, 4 skipped,
100.00 %, pip-audit and detect-secrets clean. **No deploy, and checked rather than assumed:** the diff is laws,
test-plans, docs, two `tests/` modules and the version — nothing that ships in an image.
🪤 **Two forced decisions found and deliberately not built**, carried as open rows rather than as silent
residue: [DRIFT-060](laws/drift-register.md) — nothing requires `CONTRACT.version` to move when required fields
change; [DRIFT-061](laws/drift-register.md) — five execution output clauses name fields `contracts.execution`
does not carry.

## Now

🟩 **PROVEN RESULT — [S206](sprints/sprint-206-a-rendered-verdict-names-the-check-that-produced-it.md)
BUILT (`0.98.04`), 2026-09-15 — work-queue item 59 narrowed.** The deliberator no longer renders
`stop_vs_regime_volatility gate:` or any `PASSED`/`FAILED` outcome for the unenforced stop/regime
comparison; the line is now a descriptive `stop_target_regime basis:` carrying mode, applied/flat/scaled
stop-target values and reward-risk ratios. The real confidence-floor verdict now names
`enforced_by=analyst`, PM gate outcomes are unchanged, and `contracts/` stayed untouched. 🟩 **Proven:**
T1 failed first on the old renderer naming `stop_vs_regime_volatility`; focused tests later reported
20 passed; local `make ci` exit 0 with **2758 passed, 6 skipped, 100.00 %**; branch `make gate-ran`
printed `GATE PROVEN` for `2807b446ca7789b0117c9548a88eb53f61e00aaa`. `DLIB-NEV-08` is green and the
deliberator rollup moved **20 / 55 -> 21 / 56** in both law rollups.
🟩 **Verified on handback rather than taken on trust, 2026-09-15:** `make gate-ran` re-run from the
S206 worktree proved the **branch tip** `5a192a960b366ccbab25c31d518dd934acf4d17c`, not just the
implementation commit the handback pasted (`2807b44`) — the S186 hazard, checked. T1 was **independently
reproduced red** at the branch base `823e5cf` in a throwaway worktree, failing on exactly the two lines
the handback claimed. `git diff --stat contracts/` empty, `context_pm.py` **129** lines, PATCH bump correct
(no agent gained a capability). 🟩 **MERGED `8c6f74a`** — the only difference between the gate-proven tip
and the merge commit is S207's three docs files, no code.
🟩 **DEPLOYED `s206`, 2026-09-15 19:02 AEST, by image-only retag — and the path was proven, not assumed.**
All **three** injected packs were diffed against the deployed `s203` commit `34eec3f` before choosing the
path (S202's near-miss, checked): `trading_graph_vocabulary` `58769995…`, `trading_credential_tests`
`f8f03950…`, `trading_issuer_map` `2ed1f41c…` — **byte-identical on both sides**, so a retag ships the whole
payload. 🎯 **The blast radius was read rather than assumed too:** the entire executable diff since `s203`
is S206's three deliberator modules; every other changed file under `agents/` is a `laws.md`/`test-plan.md`.
🟩 **Verified:** 15/15 image jobs green at `ea6a3b4`, **16/16 apps on `:s206`** plus `dispatcher-cron`,
**16/16 `Succeeded`**, cron `30 22 * * 1-5` intact, and scale/KEDA **and per-app env-var counts diffed
byte-identical to the pre-deploy baseline**. `DeployRecord deploy:2026-09-15T09:02:01…:s206:ea6a3b4…`.
🚨 **Caught mid-deploy and worth recording:** `deliberator-proponent` briefly showed **two** active
revisions (`0000107` on `:s203`, `0000108` on `:s206`); re-read after the transition it is Single-mode with
`0000108` sole active and ready. A one-shot read there would have reported a partial deploy.
🟩 **Spine, bus and cadence checked, not inferred:** `spine ok`; 8 Service Bus routes present, none
created; dispatcher `Succeeded` on every trading day back to 09-07.
🎯 **Pre-flight on the thing that actually decides whether tomorrow's test means anything:** the
**required** Anthropic activation probe — the exact `POST /v1/messages` body the pack injects — returned
**200** against the live key at 09:0X UTC. The nine blind nights were `400 credit balance is too low`, and
under S202 that now *halts* the deliberator rather than passing it, so a drained key would have produced
another unreviewed night. It is funded. 🟠 **Still owed:** the run itself.

🟩 **PROVEN RESULT — [S203](sprints/sprint-203-a-check-that-cannot-fail-says-so.md) MERGED `e890f93`
(`0.98.02`), 2026-09-14.** Work-queue items **53, 56 and
41** closed. The three pack `openai` probes and both `trading_vault_probes.py` LLM probes now POST a
real completion, so a key that cannot spend fails the DL-36 entry condition instead of passing it;
`compare_order_tolerances` ends every report with `comparison: FORCED | INFORMATIVE | NO DATA`;
`remediation_mode="automatic"` refuses to start a master that cannot remediate. 🪰 **The near-miss
that justifies the live-measurement rule:** the body this sprint's own spec prescribed — S202's
`max_tokens: 1` — returns **400 for a valid key** on `gpt-5.5`, a reasoning model that spends the
whole budget before emitting content; measured before the pack was edited, so three probes were never
broken ([DL-166](design-log.md)). 🟩 **Live proof:** through the parsed pack and the real
transport, `passed` for the live key and `credential_failure / http_401` for a bogus one; both
corrected vault probes likewise, both vendors, both arms. Cost **~US$0.0028** per full fleet
activation, from the vendor's `usage` block. 🟩 **Local proof:** `make ci` exit 0, **2742 passed,
6 skipped, 100.00 %**, pip-audit and detect-secrets clean. 🚨 **No `MST-*` clause written** — all
44 master clauses are silent on remediation, recorded as [DRIFT-059](laws/drift-register.md). 🟩 **Remote proof:** `make gate-ran` printed `GATE PROVEN` for the branch tip `ee2fe9b71df2f2edef60ee0dd9ed05ac1c53f4e4` (matching `git rev-parse HEAD` in that worktree) and again for the merge commit `e890f93521cc765231dbd8bcaf7d57bb207b44f3` on `main` — CI, CodeQL, Security Findings **and the image build** all `success`. 🟩 **DEPLOYED `s203`, 2026-09-14 20:40 AEST, by full `up` — never a retag, because the credential-tests pack moved.** 🚨 **The retag question looked at the wrong pack and the measurement caught it:** `trading_graph_vocabulary.json` and `trading_issuer_map.json` are **unchanged** since the deployed `e78e91ed`, so the vocabulary test alone said *retag* — while the deployed `MASTER_CREDENTIAL_TESTS_B64` decoded to **`b1496f71…`** against the repo's **`f8f03950…`**, still carrying the blind OpenAI probes this sprint exists to replace. That is S202's near-miss in the same place, and asking *"did any injected pack move?"* is what makes it visible. 🟩 **Verified:** 15/15 image jobs green at `34eec3f`, **16/16** apps on `:s203` plus `dispatcher-cron`, **16/16 `Succeeded`**, **`ENV PRESERVATION` 16/16**, alembic OK, cron `30 22 * * 1-5` intact, and scale/KEDA **diffed byte-identical to the pre-deploy baseline**. 🎯 **The check that matters here:** the deployed `MASTER_CREDENTIAL_TESTS_B64` now decodes byte-identical to the repo pack and its `openai` entry reads `POST /v1/chat/completions` with `max_completion_tokens: 256`. `DeployRecord` `deploy:2026-09-14T10:40:19…:s203:34eec3f…` written. 🟠 **Not yet proven live** — the first run under `s203` is the scheduled one, **Tuesday 2026-09-15 22:30 UTC**.

🟩 **PROVEN RESULT — work-queue item 47 CLOSED, 2026-09-13 (operator decision, [DL-165](design-log.md)).** The last of its four objections is decided: **`EXECUTION_ORDER_PRICE_TOLERANCE_MODE` flat → scaled**, promoting the S149 challenger that has shipped off-by-default since `0.83.00`. 🪤 **Promoted on DL-76's *external* measurement, not own-book evidence, and saying so is the point:** own-book evidence was **structurally uncollectable**. `compare_order_tolerances` reported flat and scaled **identical at 0.00 % drop over 170 orders** — *correctly*, because scaled is wider on **170 of 170** (75-250 bps against a fixed 50), so every order the flat band accepted the scaled band also accepts, and the orders flat **refused** never produce a `Fill` row to be counted at all. 🎯 **The flip is what makes the comparison informative for the first time:** with the wider band applied, an order that fills above the flat limit is precisely an order flat would have refused — DL-76's **35 % of buys** refusal rate, measured on our own book. Decision and instrument arrive together, which is why this beat waiting. ⚠️ **The weakness, stated:** DL-76's numbers are ~4 months old and external (60 sessions of overnight gaps: SCHW 25 % against **AMD 52 %** — one number encoding two policies), and ADR-0013 exists to prevent exactly this kind of promotion. Accepted because the alternative was not better evidence but **none** — the graph holds **4 filled orders in its entire history**. 🟠 **I recommended the opposite** (keep flat, close as decided-by-design) on two facts: S198 measured AMD and MRVL as the two worst names ever held, and S195's beta cap already drops AMD at the scanner. 🪤 **That case was weaker than it read — I could confirm the beta cap only for AMD, not MRVL or HPE.** Operator overrode; recorded as an override, not a consensus. 🟩 **Proven:** `make ci` exit 0 (**2706 passed, 4 skipped, 100.00 %**). 🟩 **DEPLOYED `s202a` 2026-09-13 by full `up`** (tunables are injected env vars, so only an `up` applies them; suffixed chore tag per [DL-106](design-log.md) rather than a second `s202`, which would put two commits under one name). **16/16 on `:s202a`**, **16/16 `Succeeded`**, cron intact, scale/KEDA **byte-identical to baseline, zero drift**, and `EXECUTION_ORDER_PRICE_TOLERANCE_MODE=scaled` present on `execution` — a **new** variable, so it could not have been inherited. S202's credential pack re-verified byte-identical after the re-`up`. `DeployRecord deploy:2026-09-13T13:05:11…:s202a:e78e91e…`. 🟠 **Opens item 56:** the report prints a confident `0.00` without saying it could not have differed — [DL-152](design-log.md)'s shape for the sixth time.

🟩 **PROVEN RESULT — [S202](sprints/sprint-202-a-probe-that-cannot-fail-is-not-an-entry-condition.md) BUILT (`0.98.00`), 2026-09-13 — the deliberator's credential probe can now fail, and a run whose veto never executed no longer reports green.** Closes work-queue **item 50**; implements [DL-163](design-log.md)'s operator decision as [DL-164](design-log.md); **CORRECTS new [DRIFT-058](laws/drift-register.md)**. 🚨 **The defect was not in the runner — it was in the question the pack asked.** `MST-NEV-06` promises a credential has *passed live* before handover, and the Anthropic probe's `credential_failure_statuses` already contained the **400** a drained account returns. It called `GET /v1/models`: free metadata, no tokens, not billed. A zero-credit key is a **valid** key, so the probe genuinely passed and all three deliberators activated clean for four nights while every debate died on `400 … credit balance is too low`. **The clause held literally and the guarantee it exists for did not.** 🪤 **DL-163 called this a one-line pack edit and measuring it proved otherwise:** `HttpProbeRequest` had no request body, and a bodyless `POST /v1/messages` returns **400 for a valid key** *[measured live]* — so the pack edit alone would have failed **all four required** Anthropic probes at once, trading a credit outage for a total activation outage. Probe bodies are a code change, which is why this is a **MINOR** and not a PATCH. 🎯 **Proven falsifiable against the live API through the real runner, which is the whole point:** funded key → `passed` (200, 7 in / 1 out, $0.00006); unusable key → `credential_failure http_401`; and `GET /v1/models` returned **200** for that same funded key in the same session. ⚠️ **Honest limit — the 400 path was not reproduced live** (that needs a genuinely drained account); it is carried by unit test and by the incident record. 🎯 **The gate half shipped with it rather than after it, and DL-163 had that backwards too:** a retired model name returns **404** *[measured]*, the runner maps every 4xx to a credential failure, so a stricter probe plus our own config drift would halt all three deliberators and let the run submit unreviewed buys on a **green** board — DL-36 halts the *agent*, not the run. So `advisory` + `proceeded_unvetoed` + an approved buy now breaches as `veto_never_ran`, which is the operator's **No** (2026-09-13). 🟩 **Not a new policy — the same policy applied consistently:** `not_required` with an approved buy was already red (`buy_veto_missing`, S191); `proceeded_unvetoed` is the identical fact more honestly labelled, and it was green, so the verdict depended on the wording. 🚨 **CORRECTED the same day, before merge, by `/audit-costs`:** the rule as first built keyed only on `proceeded_unvetoed` and I reported *"0 of 69 runs turn red"* as a **feature**. It is not — it means the tripwire is **inert**. Re-measured over the 40 linked `ExecutionRun` rows: `advisory` + `proceeded_unvetoed` **0**; `advisory` + `applied_failed_open` with `failed_open_count == reviewed` **4**; genuinely *partial* fail-open **0**. 🎯 **All four of the middle row carry `real_debate_count = 0` and a `400 … credit balance is too low` reason** — they are this sprint's own incident, and the first cut left every one green. **The line is partial-vs-total, not present-vs-absent.** 🪤 **I cited DL-125 as forbidding it and it says no such thing** — DL-125 argued against nightly red for a *declared, accepted, external* outage and proposed the advisory posture as the remedy; its own `sched-2026-08-21` entry treats that run failing acceptance as correct. Citing a document from memory instead of reading it, in the same sprint that priced a probe from memory. 🪤 **Three tests were passing for a reason their names did not describe**, each a 1-of-1 fixture that reads as partial and is total; all three are now explicitly one or the other. **The outage is nine nights, not four** (08-21/-24/-25/-26/-28, 09-08/-09/-10/-11). 🟩 **Proven:** `make ci` exit 0 (**2701 passed, 6 skipped, 100.00 %**), pip-audit and detect-secrets clean; `GATE PROVEN` for the pre-correction tip with the printed SHA checked against `HEAD`. 🟩 **DEPLOYED `s202` 2026-09-13 by full `up`, never a retag — and the path decision was itself a finding.** The deploy skill asks *did the vocabulary pack move?*; it did not (`58769995…` both sides), so the answer was **retag** — but this sprint's payload is the *credential* pack, injected as `MASTER_CREDENTIAL_TESTS_B64`, and `entrypoint.py:42` says **b64 wins** over the baked file. *[Measured before deploying]* the live master decoded to **`307e2a9a…`** against the repo's **`b1496f71…`**, still probing `GET /v1/models` on all four. **A retag would have shipped the fix inside the image and left it inert in config, with 16/16 on `s202` and every currency check passing** — DL-46 with the currency check looking one pack to the left. 🪤 **Three packs are injected at deploy time** — vocabulary, master credential tests, PM issuer map — **and a retag refreshes none of them**; the `deploy-fleet` skill's step 1 now asks about all three. 🟩 **Verified:** `ENV PRESERVATION` OK, alembic OK, 8 Service Bus routes, **16/16 on `:s202`**, **16/16 `Succeeded`**, dispatcher-cron on `:s202`, cron `30 22 * * 1-5` intact, scale/KEDA **byte-identical to the pre-deploy baseline, zero drift**. 🎯 **The check that mattered:** the deployed `MASTER_CREDENTIAL_TESTS_B64` now decodes **byte-identical to the repo** (`b1496f71…`) and all four required probes read `POST /v1/messages` `max_tokens=1` `model=claude-opus-5`. `DeployRecord deploy:2026-09-13T11:14:40…:s202:6df1c2df…`, `GATE PROVEN` for that SHA incl. CodeQL and the image build. 🟠 **Still open, deliberately: credit exhausted *mid-run*** — nothing re-probes between debates — and **new items 53 and 55** — four more probes that cannot fail (three `required: false` OpenAI entries and two vault probes, none of which gates a run), and the free unwatched outage signature: every call on all nine blind nights recorded `response_hash = e3b0c44298fc…`, **SHA-256 of the empty string**, at **~300 ms** against a working night's **~15,000 ms**. The ledger could have named this on **2026-08-21**, nineteen days before item 50 was filed.

🗄️ **Older shipped results — S199, S200, S201 and the item-6b posture decision are now in [state-archive/STATE-10.md](state-archive/STATE-10.md); S172, S173 Part A, S180, S191, S195–S198 and the CodeQL repair in [STATE-09.md](state-archive/STATE-09.md); everything earlier in [state-archive/INDEX.md](state-archive/INDEX.md).**

🟠 **FLIP CONDITION 1 of 3 on `sched-2026-08-31`** — the posture landed, but `real_debate_count` was **0** and
`failed_open_count == 0` only vacuously; PM approved nothing, so no debate ran. 🟩 **Its real purpose is now met
another way:** S188's in-fleet tests show all three deliberators passing `anthropic` through master's Key Vault, so
the credential path is proven and only **debate mechanics** still need item 3's K=4 run. Posture stays `advisory`.

🟩 **PROVEN LIVE — ADR-0023's PM half, unattended, first time.** GOOG sized at 0.998 %; GOOGL then **failed** at
1.67 % > 1 %. 🚨 Pre-S184 both passed, opening **two positions in one company** ([DL-122](design-log.md)).

🚨 **NOT PROVEN — ADR-0023's falsifiable test** (the 73 % veto rate falls materially). **73 % stands as the last
honest figure** ([DL-119](design-log.md) amendment). 🪤 `sched-2026-08-31` supplied **no** data — zero debates.

🚨 **NOT PROVEN — S182 live.** 2026-08-21's stops carry `stop_pct_source=position`, written eight minutes before
execution ran, so the fallback never fired. 🪤 **Do not re-check it that way** — run-start reconciliation closes it.

**Shipped and deployed, detail in the sprint docs and design log.** **S184** merged `18c41b1` (`0.91.00`), `GATE PROVEN` at `8613d72`, PM rows `PM-NEV-07/08/09` 🟩, DRIFT-042..046 `CORRECTED`, deployed `s184` with `ENV PRESERVATION` 16/16 and zero drift. Two defects the merge exposed are fixed on `chore-gate-outcome-refuses-ambiguity`: `GateOutcome.passed` re-collapsed the states S184 had just separated and now raises; CodeQL **#187** was `py/mismatched-multiple-assignment`, **the same rule and package as #177 four days earlier**, because `codeql.yml` runs only on `main` (queue item 31). 🟢 **That trap did not fire this time** — `main` at `19dc2b2` is `GATE PROVEN` on CI, Security Findings **and CodeQL**, with **0** open error-level alerts. **S182** merged `2fc0672` (`0.90.16`), deployed `s182`. 🪤 A `verify-2026-08-20-s184-a` teardown reported false success because `ScanRun` is uuid-keyed and the verification query reused the teardown's own filter ([DL-124](design-log.md)); a second pass removed 24 nodes + 25 edges and the pollers' own predicates now read **0 pending** at every stage, 22 positions intact.

🪤 **One live residue, not urgent:** **2 NFLX shares** from the S172 test harness, never vetoed (selling is a real trade). The `cancel_stop` `HTTP 422` half is **closed**.

## Next

**Ranked queue of record: [work-queue.md](work-queue.md)** — this section is the narrative around it, not a second ranking.

🎯 **Re-ranked 2026-09-15 against the live spine, then re-counted after S205 merged.**
**14 items open** against the operator's **Friday 2026-09-18** empty-by date. The review put **item 59**
first and displaced everything else for one reason: the referee **vetoes 100 % of what it reviews**, and every
order that has reached the broker since 2026-09-01 went through on a night it was blind — so the etalon bar
cannot be met while it stands ([DL-167](design-log.md)). It also filed **60, 61, 62** off the nine-gate PM
audit: `reward_risk` is 2.0 on 170 of 170 recommendations against a 1.5 threshold, the correlation gate has
never once failed, and sizing caps dollars rather than risk. S205 then closed **item 30**, so of the rows that
were "mostly not code" a week ago only **33** (57 PARAM/settings divergences), **22** (a sprint's built state
is not machine-checkable), **31** (CodeQL runs only on `main`), **7** (the duplicated LLM adapter) and **11**
(the delegated-agent sandbox default) remain. Item **42** is still the one live-behaviour defect open: one
spurious stop-liveness warning per run, every run. 📦 **[S206](sprints/sprint-206-a-rendered-verdict-names-the-check-that-produced-it.md)
is specced** (2026-09-15) against item 59 — a rendered verdict must name the check that produced it.

**Ahead of the numbered list — three questions raised and not yet answered.**

**The latency levers.** `effort` `max` → `high` is **done** (live 2026-08-12); `max_rounds` 2 → 1 is
🚨 **cutting the artefact under test to buy wall clock**, a recorded decision rather than a knob. The two are
**coupled** — more effort lengthens the peer-call tail into a fixed timeout — so measure them together or not
at all. Arithmetic and the full history in [DL-105](design-log.md)'s amendment.

**Undecided, recorded so they are not re-derived** — raised 2026-08-11. **(i)** amend S172 and **(ii)** collapse to one ranked queue are both **DONE 2026-08-19** (detail in the queue's own header). **(iii)** stop pinning version numbers in sprint specs (*"next available PATCH/MINOR at merge"*) — after three renumberings in one day — **still open**.

1. 🪤 **WITHDRAWN 2026-08-22 — retracted twice, on a raw-prop count both times.** `pending_human_flags`
   is **0**; `Flag.status` stays `pending` by design, like `Position.status` staying `open`. What pins
   `healthy=false` is `open_incidents`. The retracted-DL-73 class again — audit on the predicate.
2. 🪤 **Sweep the debate context for the same class — now FOUR instances, packaged as [S177](sprints/sprint-177-every-number-names-its-unit.md)** (2026-08-15). The fourth
   is `max_sector_pct`'s `deployed`: `SectorBook.__init__` seeds `_names` from held positions but
   **never seeds `_deployed`**, so `deployed` counts only *this batch* (GOOGL's `deployed=687.05` is
   exactly GOOG's `order_cost` moments earlier). `deployed=0.00` beside `existing_sector_names=2`
   is correct and unreadable, and it cost the AVGO overturn. 🚨 **Same code is also a latent gate
   defect** — the dollar sector cap never sees held positions, so across days sector exposure can
   pass 30 % unnoticed; masked today only because `max_names_per_sector=3` binds first. Every value rendered into the packet should be
   checkable against what the reader will assume it means: right unit, right period, right scope.
   **Not yet a spec.** This is the highest-value item once the divergence is settled.
3-5. **~~DL-104 (a) the invented ATR fragment · DL-104 (b) batch/portfolio absence · DL-112 sentiment
   units~~ — ALL DONE.** S175 `0.90.08` deployed `s176a` 2026-08-15, and `0.90.11` deployed `s176b`. The
   measured cost of each is in those sprint docs. 🚨 **(a) is the one S206 had to finish** — S175 deleted
   the ATR half of that rendered line and left its sibling, with no clause forbidding the class.
6. **DL-104 (c) — the analyst's hardcoded SMA-200 rationale.** The summary string always names
   SMA-200 while `indicators.sma_distance` returns `None` below its period. 🪤 **The bars gap
   underneath it is CLOSED** — S174 ships 203 bars, so SMA-200 now computes; what survives is the
   rationale asserting an input without checking it exists. Same class as item 5. 🚨 **Cited again 2026-08-19** — NEE vetoed because *"the cited technical support is contradicted by a 0.463 technical score with bearish MACD/EMA/golden-cross inputs and a bottom-tier scanner rank"*: the rationale reads as confirmation while the score underneath it is bearish.
7. **DL-104 (d) — a real advisory/binding switch**, so *advisory* is a declared posture rather than a
   grace that happens to expire. Every run writes a truthful but uninformative `error` fault, which
   trains the operator to read a real fault as noise.
8. **S170 — one LLM adapter in `kernel/`**
   ([sprint-170](sprints/sprint-170-one-llm-adapter-in-the-plumbing.md)). Capability, not repair, so
   it ranks below the fixes — but it gives the operator the same provider switch the deliberator has,
   while the Anthropic key is usage-limited to 2026-09-01.
9. **Remaining hardening rows: N, O, R.** **N** — delegated coding agents default to
   `danger-full-access` with no approval prompt; the protection is the operator remembering a CLI
   flag. **O** — S157's 101 missing law-clause test-plan rows, then flip assertion E in
   `scripts/check_law_coverage.py` to hard fail. **R** — three guards covered only by CI lacking the
   extras. 🪤 **Row P is closed** (S176, deployed); **row Q is closed** (the `s176a` full `up`
   returned `[OK]` on all 16 env-preservation checks after refusing once — see Recent).

## Pointers

Product `docs/PRD.md` · architecture `docs/architecture.md` · phases `docs/build-plan.md` · closed
decisions `docs/decisions/INDEX.md` · open threads `docs/design-log.md` · "does it work"
`docs/laws/{ledger,drift-register,functionality-checks}.md` · per-agent `agents/<name>/mission.md`.
