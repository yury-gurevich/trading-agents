# Project State

**Last updated:** 2026-07-22 18:54 AEST · **Version:** 0.71.06 · **🟢 THE STACK IS VALIDATED IN PRODUCTION.** `sched-2026-07-20` (dispatcher `dispatcher-cron-29743110`, fleet on `:s130`) ran **7/7 → ACCEPTANCE PASS** with **ZERO `*_degraded` notes** — the first fully-fed scheduled run since 07-07, and the proof S128 mattered: all four enrichment feeds populated (1867 headlines; the earnings-window filter actually fired), sentiment restored, the analyst scoring on **full signal**, and the chronic all-reject no-trade signature flipped into **5 buys** (USB/BAC/PYPL/WFC/ABT, conf 0.61–0.68 lifted over the 0.600 floor by sentiment). S130's hardened DHI runtimes booted and ran the whole chain; 0 Escalations. Fleet standing on `:s130` (built `d0b0d3a`); **P12 clean-news runway accumulating since 2026-07-20**. **Now:** S133 (Service Bus SAS, backlog row I — the last shared credential) is executing on `sprint-133-servicebus-sas` → 0.71.07, and will be the **first sprint to merge through a PR** under the DL-52 rule, so the security gate finally runs on sprint code. **Pending operator:** the standing broker-divergence Flags (07-09 / 07-14 / 07-15) still await ack; the S131 per-role DSN flip is **not yet applied** (runs still use the shared DSN).

**How to read.** *Now* = active · *Next* = queued · *Recent* = last few shipped (older detail lives in
each `docs/sprints/sprint-NN-*.md` + `STATE-01…05.md` + git). **LAW-02:** an item is "shipped" only when
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

- **Security-gate repair + backlog row L (chores on 0.71.06, 2026-07-22) — THE GATE THAT NEVER
  FIRED.** Investigating one red check on a Dependabot PR unwound five stacked defects: the
  `SECURITY_FINDINGS_TOKEN` was absent from the **Dependabot** secret store (separate from
  Actions, so it resolved empty); the replacement PAT lacked read access to the private toolset
  (403); the gate then flagged 6 error-level `py/undefined-export` alerts — all **false positives**
  from S131's PEP 562 lazy exports (CodeQL cannot follow `__getattr__`), dismissed with reason;
  **the gate is `pull_request`-triggered, so S131/S132/S134 — each merged directly with no PR —
  were never gated at all**; and `GITHUB_TOKEN` auto-merges fire no `push` workflows, so four
  dependency merges landed without rebuilding images (`:latest` stale and unscanned). Fixes:
  PR-based merges are now a hard rule in `CLAUDE.md`, the whole investigation + named residual
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

**🟢 DRIFT-023 RESOLVED (2026-07-19).** The operator fixed the Neon quota issue; verified live
before use — `DEP-POSTGRES-01 GREEN` on `SELECT 1`, same Sydney endpoint — then **S128's live
check ran the same day and PASSED** (see below). Egress-reduction hardening (dashboard read
caching/backoff, leaner nightly polling) stays queued as a worthwhile chore regardless of the
plan state.
**S128 LIVE CHECK COMPLETE (2026-07-19, planning agent).** Paced full-universe ingest: 99/99,
all four feeds populated, **zero degraded notes**, 7 min 09 s — inside the fleet window.
Unpaced ingest (live 60/min limit as injector, no mocks): all four feeds attributed exactly the
39 rate-limited tickers (`<feed>_degraded:39:MET,META,MMM,MO,MRK:429`), kept the other 60, and
left `used_fallback=False` (DRIFT-012 held). Durability: attributed notes read back off Neon
over a fresh SQL connection after the writer exited. Teardown: 12 nodes + 4 edges swept,
0 remaining. **DRIFT-021 → CORRECTED.** Evidence:
`docs/reports/sprint-128-feed-resilience/live-check.md` + functionality-checks row 2026-07-19.
**FLEET RETAGGED `:s128` same day** (operator-approved): images built at `0030243`
(run `29678020292`), 13 apps + `dispatcher-cron` all `Succeeded`, env + KEDA scale rules
verified intact, `DeployRecord` appended after verification — the resilience fix is live for
tonight's 22:30 UTC fire.

On `main` at 0.71.04 (S131 latest). **S128 SHIPPED (merged `09120b3`, tag `v0.71.01`; local `make ci` exit 0
at 1590 passed / 100 %, GitHub CI + image build + CodeQL all green; 0.71.01 images pushed).**
Codex code handback 2026-07-16; planning-agent live check + merge 2026-07-19
(`docs/sprints/sprint-128-feed-resilience.md`). S127 fixpack before it (merged `32c73cc`) on
top of the completed DL-47 arc (S122–S126).
**THE FLEET IS DEPLOYED AT `:s126`** (operator-directed retag, 2026-07-15 ~15:50 AEST): images
built at `0773ae8` (run `29392150781`, all 14 pushed), all 13 apps + `dispatcher-cron` updated
`Succeeded`, env + KEDA scale rules verified intact, and
`DeployRecord deploy:2026-07-15T05:49:41…:s126:0773ae8…` appended after verification. The retag
also **live-proved the rotated GHCR pull PAT** — every new revision pulled its `:s126` image
with the new credential. S127 then fixed the dispatcher-tag semantics (template decides, last
execution is evidence — backlog row 12), so currency judged `current` even before tonight's
first `:s126` execution.
Same session: the `trading-agents-ghcr-pull` PAT was rotated — tested first (GHCR manifest pull
200 + Actions read 200), then placed in `.env` (`GITHUB_TOKEN`, read by the deploy-currency
judgement), `infra/ghcr.local.json`, the `GHCR_PAT` repo secret, and the registry credentials on
all 13 Container Apps + `dispatcher-cron`; the live pull proof is tonight's 22:30 UTC scale-up.
Pending operator attention in the graph: 3 critical broker-divergence flags (the 07-14 run-start
flag was reconciled by monitor but awaits ack) + stale inert confirm-intent warn flags from the
S126 live check (partly resolution-view artifacts — see the sprint doc's Return notes).
**S127 SHIPPED same day** (merged `32c73cc`, 0.71.00) — see Recent. The DL-48 contract worked
on its first run: drift rule held, closeout arrived filled, planning review verified rather
than repaired.
Note: images for `32c73cc` build on merge, so the currency judgement will read **behind** again
(fleet `:s126`, record `0773ae8` vs newest main build `32c73cc`) — correct and intended; retag
via `/deploy-fleet` when the S127 dashboard fixes should reach the deployed fleet.
Pending in the graph: **1 critical broker-divergence flag** (operator's ack — now doable from
the dashboard); tonight's 22:30 UTC fire is the rotated-PAT + `:s126` first scheduled run.
The 07-10 feed diagnosis is closed: DRIFT-021 CORRECTED (S128, live-proven 2026-07-19) and
deployed to the fleet at `:s128` the same day.
**S129 (fixpack) SHIPPED 2026-07-19** (merged `3be1ee8`, 0.71.02, tag `v0.71.02`; Codex-built
same-day from packaging, planning review re-ran `make ci` — exit 0, 1597 passed / 5 skipped /
100 %). Fixes-first directive delivered: S127 backlog row 3 FIXED (bounded `QuantMetric` tuple
on Recommendation, rendered to all three deliberation roles; live transcript cited
`composite_score`); egress reduction live-proven (TTL cache: 18 → 0 Postgres round-trips
inside the 5 s TTL, verdict unchanged; self-heal refetch 90 s); dependency-review enforcing
on PRs (PR #50 proof); Trivy HIGH/CRITICAL gate enforcing in `build-images.yml` — found 22
real base-image CVEs per representative image and correctly fails the run (nothing accepted,
`.trivyignore` empty by policy → **backlog row H: remediate or formally accept; every main
image build reads red until drained — images still push**). Hardening backlog C–F reconciled
with evidence; DL-50 records the ADR-0007 DockerHub→GHCR drift for a future amendment cycle.
Evidence: `docs/reports/sprint-129-fixpack/live-proof.md`.
**S130 (base-image chore) SHIPPED 2026-07-19** (merged `8aefe2a`, 0.71.03, tag `v0.71.03`;
Codex-built, planning review re-ran the gate — exit 0, 1597 passed / 100 %; PR #51 checks
green; post-merge `build-images` on main **GREEN**). Trivy keeps HIGH/CRITICAL `exit-code: 1`,
adds `ignore-unfixed: true`, and now scans **all 14 images** (widened from the S129
representative trio); all Dockerfiles are two-stage `dhi.io/python:3.13-dev` → `dhi.io/
python:3.13` (venv-carrying, no shell/uv at runtime — nonroot minimal base); actionable
findings 22 → 0; provider image 215 MB → 150 MB; `.trivyignore` still empty; permanent
provider missing-config smoke + size note added to the workflow. Live proof:
`docs/reports/sprint-130-base-image/live-proof.md` (run `29681635979`, all 14 `s130-test`
images). Row H Done; R005 Adopted. **2026-07-19 threat-model review added backlog rows I**
(per-agent spine/bus credential scoping — the shared `POSTGRES_DSN`/Service Bus string is
the real blast-radius item, DL-49-adjacent Kerckhoffs discussion) **and J** (dispatcher
image COPYs the whole repo — slim to the dispatch import closure).
**2026-07-20 morning check:** the 07-19 22:30Z fire **Succeeded on `:s130`** and correctly
placed no RunRequest (Sunday — calendar-gate clean skip; first production proof of the DHI
dispatcher image). Post-restore verification closed DRIFT-023's loose end: `sched-2026-07-15`
had completed **7/7 `ACCEPTANCE PASS`** (1 AMD paper buy) before the quota tripped; Friday
07-17's session run is the outage's one lost run (not re-fired — day-keyed). **The new
stack's first session-day run is tonight, Mon 2026-07-20 22:30 UTC** — green = zero
`*_degraded` notes + full-signal confidences.
**S131 (blast radius) SHIPPED 2026-07-20** (merged `0ca7459`, 0.71.04, tag `v0.71.04`;
Codex-built, planning review re-ran the gate — exit 0, 1608 passed / 100 %; post-merge CI +
CodeQL + build-images all GREEN). Backlog row I part 1 + row J delivered: **15 per-agent Neon
roles** (`ta_<agent>`, identical grants — attribution + revocability now, RLS deferred as
DL-51), secret-backed per-target `POSTGRES_DSN` delivery + `postgres-flip` runbook +
`-UseSharedPostgresDsn` rollback; **dispatcher image slimmed** to its measured import closure
(the shared-code lazy `__init__` exports are what let it drop `agents/`/`orchestration/`/
`scripts/` wholesale). Live proof: 15 `ta_*` roles connected + attributable in
`pg_stat_activity`, `ta_canary` revoked→refused→purged with the fleet green. **Honest
deviation (correct conservative call):** identities proven via a controlled audit, not by
firing a production trading run outside market hours — operator follow-up is to repeat the
`pg_stat_activity` query during a live KEDA window. Backlog row I narrowed to **part 2
(Service Bus SAS)**; row J Done. The fleet still runs `:s130` — the per-role DSN flip is an
operator infra step (outside 22:25–00:30 UTC), not carried by an image retag.
**S132 + S133 PACKAGED 2026-07-20** (both ready for handover, execute after the 07-20 nightly
run reads healthy — fixes-first still holds, so a red run reprioritizes). **S132 = mutation
testing** (`docs/sprints/sprint-132-mutation-testing.md`, targets 0.71.05, backlog row G):
mutmut over the deterministic decision engines (analyst/PM/scanner/execution gates,
acceptance, veto context) — kill or explain every survivor, fix any latent gate bug;
mutmut stays a manual periodic exercise, never a CI gate. **S133 = Service Bus SAS**
(`docs/sprints/sprint-133-servicebus-sas.md`, targets 0.71.06, backlog row I part 2,
sequences after S132): per-agent scoped SAS replacing the shared `RootManage` connection
string (entity-level Send/Listen; 12-rule/namespace cap forces per-topic), mirroring S131's
secret-backed delivery + rollback; lower-severity (bus = pointers+RPC, not data). **P12
scorecard-run** stays queued until ~2 weeks of clean-news nights accumulate (runway starts
tonight) — it cannot execute meaningfully until then.
The etalon north-star holds (DL-19):
remaining gray law clauses → green with cited tests; **every sprint ends with a real-environment
functionality check** (`docs/laws/functionality-checks.md`) + teardown. Each sprint/chore on its own
`sprint-NN-<slug>` branch; merge to `main` is the deploy trigger (rebuilds + pushes agent images).

## Next

- **DL-47 — operations dashboard (ACTIVE ARC).** **S122 SHIPPED 2026-07-10 (0.66.00, merged `820b8c9`)** — Section III run view. **S123 SHIPPED 2026-07-10 (0.67.00, merged `2ad656e`)** — Sections I/II, Azure REST read port, real logs/images, A$ costs, and live vitals; LAW-02 row + screenshots captured. **S124 SHIPPED 2026-07-11 (0.68.00, merged `b9ed20e`)** — glance-first
  master verdict + `NO_TRADE` acceptance verdict + operator-language sweep (redline r2, reqs
  13–15). **S125 SHIPPED 2026-07-13 (0.69.00, merged `9420b78`)** — tier-1 bounded
  operator chat only. The repair agent remains a later tier and was deliberately not exposed.
  **S126 SHIPPED 2026-07-15 (0.70.00, merged `297354b`)** — resume-from-stage
  (supersession + `RESUMES` lineage) + `DeployRecord` deploy-currency judgement + tri-state bus
  health. **THE ARC IS CLOSED.** Design spec:
  `docs/design/dashboard-mockup.html` (interactive; built from the real 07-08/07-09 runs).
- **Watch outcome (2026-07-09 22:30 UTC run, verified 2026-07-10):** cron fired (3/3 nights),
  7/7 stages on `:s121`; **S120 reconciliation proven live** — critical divergence Flag raised
  exactly as predicted (CSCO 88→177 + missing BAC/WFC), monitor adopted broker truth (graph now
  matches broker, 6 positions), pending-fill refresh stamped all 4 stale Fills. **But
  `ACCEPTANCE FAIL`** — a legitimate no-trade day (all 5 candidates below the 0.600 regime floor)
  trips the hard `analyst.scored ≥ 1` / `pm.evaluated ≥ 1` floors: gate semantics need a no-trade
  verdict — **scheduled: S124 Part A** (packaged 2026-07-11). The 07-10 run repeated the
  signature (7/7 complete, 5 candidates 0.533–0.595 vs floor 0.600, `ACCEPTANCE FAIL`). Contributing: all four enrichment feeds
  (fundamentals/news/sectors/earnings) ran degraded in-fleet — investigate why (secrets? rate
  limits at 22:30?). The pending critical Flag awaits operator ack.
- **DL-46 — deploy gap (DECIDED 2026-07-14, S126):** option C shipped — append-only
  `DeployRecord` + the dashboard's `current/behind/unverified` judgement; option A (deploy step
  in CI) remains the recorded end state, deferred not rejected. The fleet reads **behind** today;
  retag via `/deploy-fleet` (now appends `DeployRecord`) when the operator chooses.
- **DL-42 — SHIPPED (S119 0.64.00 + S121 0.65.01).** Compiled judge + challenger are the live
  champions; defender stays hand-written; golden re-frozen to 5 robust cases. Next layer when
  prioritized: EvoPrompt/TextGrad bake-off behind the same port (R003).
- **Deliberation as a reasoning/competence source (DL-39, DIRECTION)** — the transcript's *why*, not
  the verdict, is the asset: grade whether the expert model reasons at senior-analyst level and learn
  which parameters carry the decision. Assembles DL-31 (`--score`) + DL-09 + ADR-0010/CI-2; needs a
  research item + a live runway before packaging. Companion **DL-40 (parked)**: literacy-tiered verdict
  explanations (low/mid/high) as a `surfaces/` renderer, ruling single-sourced.
- **Remaining DL-36 hardening** — destructive executors (`rotate-credential`/`recreate-instance`) stay
  human-manual until a provider-specific write path + approval UI land; the diskcache CVE from the
  offline DSPy extra → hardening-backlog (not in runtime/images).
- **Deferred behind a perfect etalon (DL-19):** CI-1..CI-6 (ADR-0013, S90–S95) · the bundle **generator** ·
  ADR-0010 reusable predictor registry/promotion (first instance landed in S107) · P12 scorecard-run (needs
  a live news runway) · P13 cross-asset graph · `contracts/` substrate/pack split.

## Pointers

Product `docs/PRD.md` · architecture `docs/architecture.md` · phases `docs/build-plan.md` · closed
decisions `docs/decisions/INDEX.md` · open threads `docs/design-log.md` · "does it work"
`docs/laws/{ledger,drift-register,functionality-checks}.md` · per-agent `agents/<name>/mission.md`.
