# Project State

**Last updated:** 2026-09-18 21:10 AEST · **Version:** 0.98.10 · **🟩 S214 MERGED and DEPLOYED `s214` — `revise` is now a finding, `overturn` the only block; ADR-0029's five tests begin with tonight's `sched-2026-09-18`.**

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

## Now

🟩 **MERGED and DEPLOYED — [S214](sprints/sprint-214-a-revise-is-a-finding-an-overturn-is-a-block.md) (`0.98.10`, merge `1a6f342`, tag `s214`), 2026-09-18 — [ADR-0029](decisions/0029-a-revise-is-a-finding-an-overturn-is-a-block.md) decisions **1** and **5** are live; 2, 3 and 4 remain unshipped by design.** `vetoed_tickers` now carries `overturn` only (`review_batch.py`), and an empty/unparseable/stopped judge answer raises `UnreadableVerdictError` from the new `kernel/deliberation_verdicts.py` and routes to loud fail-open instead of borrowing `revise` — without which decision 1 would have flipped a fail-*closed* default to a silent fail-*open*. `kernel/deliberation.py` **198 → 180** by split, not by trimming. Deliberator laws **v1.7 → v1.8** (`DLIB-OUT-02` + `DLIB-OUT-04` amended), rollup **21/56 → 22/56**, `DRIFT-066` filed; `contracts/` and `agents/execution/` both **untouched**, confirming the spec's prediction that narrowing the veto upstream needs no execution edit. 🟩 **Gate proven twice, by me, not asserted:** `GATE PROVEN` for branch `3a95e53` (CI + Security Findings) and again for the **merged** `1a6f342` with CI, **CodeQL**, Security Findings, image build and dependency graph all `success` — so no commit rides above a gated one. 🟩 **DEPLOYED by image-only retag, path proven before taken:** all **three** injected packs byte-identical between the deployed `7d3ff51` and `HEAD` (vocab `40ac81be…`, creds `f8f03950…`, issuer `2ed1f41c…`) and re-read from the live fleet *after* the retag on the apps that actually carry them — the S202 trap checked, not assumed. **17/17 targets on `:s214`**, 16/16 `Succeeded`, dispatcher cron `30 22 * * 1-5`, KEDA/scale **diffed byte-identical to the pre-deploy baseline, zero drift**. 🟩 `DeployRecord deploy:2026-09-18T11:04:47…:s214:1a6f342…` **written** — the s211 gap (work-queue **72**) avoided by dispatching the build on `main` while `main` still equalled the merge commit. 🟠 **Owed — ADR-0029's five tests, starting with `sched-2026-09-18` tonight:** null check, first scheduled run, fail-closed on a non-answer, do fills resume, and 🪤 **the relabelling tripwire — `overturn` share must stay near 6.3 % over the first 10 real-debate sessions; above 20 % the judge swapped words and the ADR is revisited, not the prompt tightened.**


🟠 **BUILT — [S214](sprints/sprint-214-a-revise-is-a-finding-an-overturn-is-a-block.md) on branch
`sprint-214-revise-is-a-finding`, version `0.98.10`.** ADR-0029 decisions 1 and 5 are implemented:
`vetoed_tickers` now carries `overturn` verdicts only, `revise` remains recorded as a finding without
blocking, unreadable/empty/stopped judge non-answers take the loud fail-open path, and the operator
trace shows `revised=` so objections remain visible. Deliberator laws moved v1.7 -> v1.8 and roll up
22 / 56; `DRIFT-066` is filed/corrected; `contracts/` stayed untouched; execution source stayed
unchanged. 🟩 **Local proof:** red-first guard run failed 17 / passed 30 before implementation;
redirected `make ci` exited 0 with 2821 passed, 4 skipped, 100.00 % coverage, pip-audit clean and
secrets checks passed. 🟩 **Branch proof before handback commit:** `make gate-ran` matched
`e6b26b9030dda6d31a0dafaf2c58518004fbfe03` with CI and Security Findings success. No merge, deploy,
or live proof is done.
Note: memory mentions `docs/local/STATE.md`, but this checkout has no `docs/local/`; `docs/STATE.md` is
the live tracker named by `CLAUDE.md`.

🟩 **PROVEN RESULT — [S212](sprints/sprint-212-a-trace-says-why-nothing-was-submitted.md) MERGED, MAIN-GATED, and LIVE-CHECKED (`0.98.09`, main `b275d87`), 2026-09-18 — work-queue items 66/67 closed as operator-observability repairs.** `scripts/trace_run.py` now treats `complete == trace_stage_total()` as success, and `orchestration/batch_trace.py` prints a conservative `[deliberation]` block between PM and execution with reviewed/vetoed/status/tickers plus `withheld=N by deliberation veto` only when approved buys, vetoed tickers, and submitted count reconcile exactly. Law reading and DL-174 are recorded; A1-A8 were red-first, DL-70 break checks were restored, no `agents/` or `contracts/` diff exists, touched modules are under 200 lines, and redirected local `make ci` exited 0 with `2811 passed, 6 skipped`, 100.00 % coverage, pip-audit clean, detect-secrets clean. 🟩 **Gates:** final branch `make gate-ran` proved `b275d87ce243786bd609de0e67f2471c74794e1f`; after fast-forwarding and pushing `main`, post-merge `make gate-ran` proved the same SHA with CI, CodeQL, Security Findings, Dependency Graph, and image build success. 🟩 **LIVE CHECK DISCHARGED on `sched-2026-09-16`** from the main checkout with `.env`: `trace_run.py --run-id sched-2026-09-16` exited 0 and rendered `[deliberation] reviewed=4 vetoed=4 status=applied`, `tickers=USB,WFC,AMZN,MDLZ`, `withheld=4 by deliberation veto`, followed by `RESULT 8/8 stages complete OK batch processed`. No deploy was required or performed because S212 changes operator tooling only.

🟩 **DECIDED, NOT YET BUILT — [ADR-0029](decisions/0029-a-revise-is-a-finding-an-overturn-is-a-block.md), from [DL-173](design-log.md).** Four consecutive zero-fill sessions (09-14, 09-16 ×2, 09-17) traced to a code-level collapse, not a model fault: `revise` (164 all-time) and `overturn` (22) are reduced to one action at `agents/deliberator/review_batch.py:87`, so the referee's *systemic* critiques are spent rejecting *individual* trades. 🎯 **Three experiments show those critiques are correct and their fixes do not pay** — [EXP-011](research/experiments/EXP-011-regime-markov-and-barrier-calibration.md) (the ratio does not predict returns), [EXP-008](research/experiments/EXP-008-correlation-cutoff-replay.md) (no cutoff changes a trade), [EXP-012](research/experiments/EXP-012-volatility-sizing-ten-year-replay.md) (iso-risk costs $11,619/10 y). **Decision:** `overturn` blocks, `revise` records a deduplicated finding, a block must name an order-specific fact, the judge is told what its verdicts do, and 🚨 **a judge that cannot answer routes to `applied_failed_open`, never to `revise`** — without that the change would flip today's fail-*closed* parse default to a silent fail-*open*. Expected block rate **53 % → ~6 %**. 🪤 **Named tripwire:** if `overturn` share exceeds **20 %** over the first 10 real-debate sessions the judge has swapped words, and the ADR is revisited rather than the prompt tightened. 🟠 **Owed:** the implementing sprint (deliberator + execution law cycle) and tests 1-5 in the ADR.

🟩 **PROVEN RESULT — [S211](sprints/sprint-211-reward-risk-compares-two-measured-quantities.md) MERGED, DEPLOYED and LIVE-PROVEN (`0.98.08`, merge `7d3ff51`, tag `s211`), 2026-09-18 — work-queue item 60 closed.** Analyst targets use median trailing favourable-excursion evidence, `StopTargetEvidence` carries the estimate/window/sample count, PM `min_reward_risk_ratio` is `0` per ADR-0027 Correction 2 / EXP-011, and `reward_risk` records `comparison=DISCLOSURE_ONLY` by default while explicit positive floors still reject below-floor ratios. Analyst laws v1.4 → v1.5 (`ANLZ-OBS-06`), PM laws v1.6 → v1.7 (`PM-OBS-05`); rollups analyst **26 / 49**, PM **31 / 50**. 🟩 **Gate + deploy:** `make gate-ran` printed `GATE PROVEN` for `5dc9d1c`, merged `--no-ff` as `7d3ff51`, post-merge CodeQL success; build `35217747046` 15/15; `deploy-agents.ps1 up -Tag s211` exited 0 with **17/17 targets on `:s211`, all `Succeeded`**, `dispatcher-cron` `30 22 * * 1-5`. 🟩 **LIVE CHECK DISCHARGED on `sched-2026-09-17`** (8/8 stages, `ACCEPTANCE PASS`, provider quality `ok` 98/99, no `*_degraded`), recorded in [`laws/functionality-checks.md`](laws/functionality-checks.md): three **distinct** ratios (`AMZN 0.8136`, `USB 0.8479`, `WFC 0.9484`) where S208 saw a constant `2.0`; `comparison=DISCLOSURE_ONLY` at `threshold=0.0` throughout; **zero** `reward_risk_below_min` rejections; **zero** `STRUCTURALLY_DETERMINED`; evidence named as `target_basis=trailing_favorable_excursion`, horizon 10 d, sample 120. 🚨 **The proof arrived with its own finding:** every measured target landed *below* its stop (all ratios < 1), so the 0 floor admitted inverted payoff geometry and the deliberator vetoed **all three** (`verdicts` all `revise`) citing exactly that — a check *"structurally incapable of failing"*. Zero fills; book unchanged at 21 holdings. Whether the floor stays at 0 is reopened as a question, not a defect. 🟠 **Two gaps, both filed:** no `DeployRecord` for `s211` (`record_deploy.py` accepts only `main`-ref builds; this one was dispatched on `v0.98.08`), and the approved-vs-submitted accounting hole — **four consecutive zero-fill sessions, 20/26 buys vetoed (77 %)** — which [S212](sprints/sprint-212-a-trace-says-why-nothing-was-submitted.md) specs as work-queue **66**/**67**.

🟠 **BUILT and BRANCH-GATED — [S210](sprints/sprint-210-a-concentration-gate-divides-by-the-book-it-measures.md) on branch `sprint-210-concentration-divides-by-the-book`, worktree `C:\Users\yury_\Downloads\project\trading-agents-sprint-210-concentration-divides-by-book`, base `origin/main` @ `d4040f84a9b04bd9cd74f6656893433357468ece`.** `max_sector_pct` and `correlated_cluster_pct` now measure concentration against deployed capital while `sizing` keeps the equity denominator; below the derived deployment floor, those gates report explicit `NOT_EVALUATED`; PM laws/test-plan/rollups are amended to v1.6, `DRIFT-065` is filed, and `contracts/` stayed untouched. 🟩 **Local proof:** red-first S210 guards failed 7/9 before implementation, focused S210 tests **14 passed**, full PM tests **132 passed**, and redirected `make ci` exited 0 (**2780 passed, 6 skipped, 100.00 %**; pip-audit and secrets checks passed). 🟩 **Branch proof:** remote CI `35089424010` and Security Findings `35089424128` succeeded on `540415ff91fc312f05dcce3d79bc4c220d450b85`; `make gate-ran` from the S210 worktree printed `GATE PROVEN` for that same SHA. 🟠 **Not done:** merge, deploy, and next-run live denominator check. The evidence commit that records this note still requires its own final branch reproof.

🟩 **MERGED and DEPLOYED — [S209](sprints/sprint-209-a-stop-that-fired-is-not-a-mismatch.md) (`0.98.06`, deploy SHA `032cd8e`, tag `s209`), 2026-09-16 — work-queue item **42** is code-fixed and live-deployed, but not live-closed.** `_is_stop_order` now compares broker stop identity (`is_broker_stop_order`) with graph stop identity (`broker_stop_orders`) and no longer writes a permanent `BrokerStopIdentityMismatch` merely because a fired stop's graph refresh is 11-19 s behind the broker. `EXEC-OBS-05` stays 🟩 but is amended **v1.5 → v1.6**, rollup remains **35 / 61**, `DRIFT-064` is filed, and `DL-170` records the decision not to add a second liveness observer. 🟩 **Proven:** A1 red first, A4 red on intentional broken graph identity, focused 6 passed, local `make ci` exit 0 (**2768 passed, 4 skipped, 100.00 %**), `contracts/` diff empty, deploy-SHA `make gate-ran` on `032cd8ef6fa34f65099bf4ecb82af7d819888a1a` green for CI, CodeQL, Security Findings and image build. 🟩 **DEPLOYED `s209` by image-only retag:** all three injected packs were unchanged and re-read from live env after the retag — vocabulary `58769995…` on **17/17**, credential tests `f8f03950…`, issuer map `2ed1f41c…`; `35050880879` built `s209`; **17/17 targets on `:s209`**, 17/17 `Succeeded`, dispatcher cron `30 22 * * 1-5`, scale/env/cron shape drift **0**. `DeployRecord deploy:2026-09-16T08:45:36…:s209:032cd8e…`. 🟠 **Not done:** the only live closure that matters — a future scheduled run where a protective stop actually fired and zero same-date `BrokerStopIdentityMismatch` faults appear.

🟩 **MERGED and DEPLOYED — [S208](sprints/sprint-208-a-risk-gate-says-what-it-can-reject.md) (`0.98.05`, merge `d43280e`, tag `s208`), 2026-09-16 — work-queue item **61** closed, **60** narrowed.** `reward_risk` keeps its verdict and threshold but now names `base_take_profit_pct`, `base_stop_loss_pct`, `applied_mode`, `structural_basis` and `comparison=STRUCTURALLY_DETERMINED` when the ratio is fixed by the base pair — and a full gate report proves data-varying gates are **not** labelled structural, which is what stops the clause describing one site. `correlated_cluster_pct` now skips only the unusable pair, attributes it as `skipped_pair_issuers`, and still returns whole-gate `NOT_EVALUATED` when no usable pair remains, so `PM-NEV-09` comes out stronger. `PM-OBS-04` added and green; PM rollup **29 / 48 → 30 / 49** as the gate computed it; `DRIFT-063` filed and corrected. 🟩 **Proven:** T1/T2 red on `main` first; local `make ci` exit 0 (**2763 passed, 6 skipped, 100.00 %**); `contracts/` diff empty; `correlation.py` 153 → **115** lines; `make gate-ran` on the **merged** SHA — `main` @ `773c02e`, with CI, **CodeQL**, Security Findings and the image build all `success`, so no commit rides above a gated one (the S186 hazard). 🚨 **One handback defect no gate could catch, fixed on merge:** the `laws.md` v1.5 changelog cited `test_portfolio_manager_audit.py` for the T4 test, which lives in `test_gate_reachability.py`; the test-plan row the coverage gate reads was right, the prose was not.

🟩 **DEPLOYED `s208` by image-only retag, and the path was proven before it was taken.** All **three** injected packs were diffed against the deployed `ea6a3b4` *and* against what the live fleet decodes — vocabulary `58769995…`, credential tests `f8f03950…`, issuer map `2ed1f41c…`, identical on all three sides — so the retag ships nothing inert (the S202 trap). 🟩 **Verified:** 15/15 image jobs green at `773c02e`, **16/16 apps on `:s208`** plus `dispatcher-cron`, 16/16 `Succeeded`, cron `30 22 * * 1-5` intact, scale and KEDA **diffed byte-identical to the pre-deploy baseline, zero drift**, packs re-checked *after* the retag unchanged. `DeployRecord deploy:2026-09-15T14:55:48…:s208:773c02e…`. 🟩 **PROVEN RESULT — the live check is discharged, a day earlier than planned.** `sched-2026-09-15` dispatched at **22:32 UTC, after** the 14:55 UTC retag, so its `PMRun` `pm-run-ef4b658235c7491888338459fd5190b1` is the first written by `s208` — the run to read was last night's, not `sched-2026-09-16`. Read off the spine: every `reward_risk` detail carries `base_take_profit_pct=0.1000; base_stop_loss_pct=0.0500; applied_mode=scaled; structural_basis=base_take_profit_pct/base_stop_loss_pct; comparison=STRUCTURALLY_DETERMINED` with `outcome=passed value=2.0` unchanged, and `correlated_cluster_pct` renders `skipped_pairs=0; skipped_pair_issuers=none`. Recorded in [`laws/functionality-checks.md`](laws/functionality-checks.md). 🟠 **Half proven emitted, not exercised:** `skipped_pairs=0` on all three approvals, so the skip-only-the-unusable-pair path did **not** run live and still stands on its unit tests.

## Recent (most recent first — detail in each sprint doc)

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

🗄️ **Older shipped results — S202, S203 and the work-queue item 47 promotion are now in [state-archive/STATE-11.md](state-archive/STATE-11.md); S199, S200, S201 and the item-6b posture decision in [STATE-10.md](state-archive/STATE-10.md); S172, S173 Part A, S180, S191, S195–S198 and the CodeQL repair in [STATE-09.md](state-archive/STATE-09.md); everything earlier in [state-archive/INDEX.md](state-archive/INDEX.md).**

🗄️ **Older shipped results — the late-August deliberation/sizing residue (ADR-0023's PM half, the posture flip conditions, the 73 % veto figure, S182/S184 and the NFLX residue) are now in [state-archive/STATE-12.md](state-archive/STATE-12.md).** 🪤 The 73 % figure there is superseded by [DL-173](design-log.md) / [ADR-0029](decisions/0029-a-revise-is-a-finding-an-overturn-is-a-block.md).

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
spurious stop-liveness warning per run, every run. **S206 has since shipped and deployed** — see *Now*.

📦 **[S208](sprints/sprint-208-a-risk-gate-says-what-it-can-reject.md) is specced** (2026-09-15) against items **60** and **61**, from a live-spine audit recorded as [DL-169](design-log.md): two PM risk gates have **never rejected an order** — `reward_risk` has one distinct value across 256 recordings because the ratio cancels to two constants the regime label never touches, and `correlated_cluster_pct` abandons the whole gate on the first thin-overlap holding. Both appear **zero** times in 919 `Rejection` rows. 🪤 **The audit also corrected the queue's own denominators** — only **35** of 273 `OrderIntent` nodes carry gate outcomes, and the correlation abort path has **never fired**, so that half is repair before it bites. 🚨 **One decision is the operator's and is not in the sprint:** item **62**, position sizing by risk rather than dollars, is the referee's most-repeated nightly ground and the largest single lever on the veto rate — it is blocked on a policy call, not on engineering. New item **64** records that the regime label never modulates any risk number.

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
