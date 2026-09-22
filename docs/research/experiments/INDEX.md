# Experiments log — research probes (purpose · process · delivery · interpretation)

**What this is:** the log of **research/probe experiments** — guess → run → measure → *learn*. Distinct
from **parameter experiments** (champion–challenger tuning of a `tunable()`), which use the
Experimentation charter's report (what-changed / gain / verdict). A probe asks a *question about the
system* (does the LLM understand our parameters? does feed X cover name Y?) and records what we learned.

## The record format (the definition — every probe uses these four headings)

| Heading | What it captures |
| --- | --- |
| **Purpose** | the question / hypothesis, and *why it matters* (what decision or risk it informs) |
| **Process** | exactly what we did — method, inputs, controls, models, what was withheld |
| **Delivery** | what was produced — outputs, artifacts, where they live |
| **Interpretation** | what it *means* — findings, deltas, the decision taken, and what it *feeds next* |

Rules (inherit LAW-02 / LAW-06): an experiment is recorded **while fresh**; *Interpretation* states the
proven finding, not the hoped-for one; if a probe was inconclusive, say so. The record is the LAW-05
defence for any action it triggers.

## Log

| ID | Title | Date | Feeds |
| --- | --- | --- | --- |
| [EXP-001](EXP-001-llm-parameter-interpretation.md) | Do the LLMs understand our decision parameters? (gpt-5.4 vs 5.5) | 2026-06-24 | DSPy role-prompt grounding (DL-21/22); switched `OPENAI_MODEL`→gpt-5.5 |
| [EXP-002](EXP-002-manufactured-eval-signal.md) | Can we manufacture a DSPy eval signal without trade outcomes? | 2026-06-24 | DL-23 (manufacture the eval set); proved grounded debate catches a known flaw the blind one misses |
| [EXP-003](EXP-003-eval-harness.md) | Build the manufactured-eval harness (Path B) | 2026-06-24 | shipped `kernel/deliberation_eval.py`; finding: a strong model catches textbook flaws blind — grounding's ROI is Class-1 (our-impl) facts; needs a sharper scorer |
| [EXP-004](EXP-004-class1-cases-llm-judge.md) | Arm the drift firewall — Class-1 cases + LLM-judge scorer | 2026-06-25 | ✅ **firewall armed** — on Class-1, grounding Δ = +50 pp (keyword) / **+83 pp (judge)**; judge sharper (blind judge 0% vs keyword 33%). Next: EXP-005 freeze golden baseline + model-swap A/B |
| [EXP-005](EXP-005-model-swap-gate.md) | Operationalise the firewall — golden baseline + model-swap gate | 2026-06-25 | ✅ **firewall trips on a real side-grade** — gpt-5.4 debater silently dropped `calendar-staleness` (4/6) vs gpt-5.5 golden (5/6). `kernel/deliberation_gate.py` + committed golden. Next: N-run hardening (CI-4/S93) |
| [EXP-006](EXP-006-nrun-hardening.md) | Harden the firewall — N-run aggregation against debate noise | 2026-06-25 | ✅ **noise-aware gate** — N=3 reveals `calendar-staleness` was champion-flaky (1/3) so EXP-005's trip was partly noise; gate now trips gpt-5.4 on the *robust* `name-correlation` (2/3→1/3). Found+fixed 400-tok truncation. Next: larger N + margin (CI-4/S93) |
| [EXP-007](EXP-007-aura-snapshot-local-export.md) | Can Aura Free snapshots be stored locally via API? | 2026-07-01 | Snapshot create/list works on the active Free instance, but local download is blocked by `HTTP 403`; Free snapshots are managed rollback only, not off-platform backup proof |
| [EXP-008](EXP-008-correlation-cutoff-replay.md) | Does the 0.70 correlation cutoff decide anything, and is it noise? | 2026-09-17 | Replay of 38 approvals (validated 38/38): **no cutoff from 0.70 down to 0.50 rejects anything** at today's book; weighted ρ⁺ rejects MDLZ ×5. Near 0.70 the verdict is sampling noise (CI spans 0.70 on 12/16 pairs; halves disagree 7/16), **not outlier days** (Δρ +0.001). Feeds work-queue item 68 → an ADR on gate meaning, not urgent |
| [EXP-009](EXP-009-volatility-sizing-replay.md) | Should position size follow volatility, and does the regime label have anything to scale by? | 2026-09-17 | Replay of 61 approved buys (sizing reconstructed 61/61): iso-risk sizing cuts per-position risk dispersion 4.2× → 1.9× and worst loss −30 %, but lost **$445 more** this month (AMD alone −$255; calm names fell) — not free, one window can't settle it. 🚨 **Regime label `neutral` on 50/50 runs: no production source supplies VIX.** Feeds items 62/64 and new item 70 |
| [EXP-010](EXP-010-reward-risk-floor-on-the-built-ratio.md) | What does the reward_risk floor reject on the ratio S211 actually built? | 2026-09-17 | ADR-0027's 1.0 floor was calibrated on favourable ÷ adverse excursion; S211 builds favourable excursion ÷ the ATR stop. Replayed on the branch code over 3 nights × 98 names: 1.0 rejects **55-68 %**, not ~21 %; **0.80 rejects 16-18 %**. Operator set 0.80; S211 returned before merge. Target median halves 8.6 % → 4.2 % (no exit reads it) |
| [EXP-011](EXP-011-regime-markov-and-barrier-calibration.md) | Is the regime a Markov chain, and do simulated stop/target probabilities come true? | 2026-09-17 | 36 y of VIX + 10 y SIP bars × 98 names, 47,485 decisions. Raw regime label **not Markov** (G-test p≈10⁻¹³⁰; 37 switches/yr); a 3-close sticky label is. Regime-weighted barrier simulation adds ~1 % Brier skill; P(stop) over-dispersed. S211's median target touched **50.2 %** ✔. The target/stop ratio **does not predict returns** (passed − rejected +0.03 % [−0.17, +0.23]) and 0.80 would reject a median **49 %** per night → operator: gate **disclosure-only** |
| [EXP-012](EXP-012-volatility-sizing-ten-year-replay.md) | Does volatility-scaled sizing survive a ten-year window with down-legs? | 2026-09-18 | **No.** 47,549 decisions on EXP-011's cached SIP bars (2017-2026, zero cost). Iso-risk delivers dispersion **6.40x -> 2.00x** and still loses **$11,619**; bootstrap [-$19,210, -$4,186], **100 %** of resamples negative (EXP-009's month: -$445 at 98 %). Down-legs favour it (**2018 Q4 +$3,006**, 2022 bear +$1,112) but **not COVID** (-$2,161) and net only +$1,957. Mechanism: **volatile names returned ~5x calm ones** over 10 sessions (D2 +0.092 % -> D9 +0.532 %), and iso-risk buys down that gradient. No variant rescues it. Settles item **62**; contradicts [ADR-0025](../../decisions/0025-concentration-measures-the-book-position-risk-measures-the-capital-base.md) Decision B on returns |
| [EXP-013](EXP-013-regime-scaled-sizing-replay.md) | Should the regime label scale position size? | 2026-09-22 | **No.** 47,533 decisions on the rebuilt EXP-011 dataset (2017-2026, zero cost). 🐛 **Item 64's task could not be done as written** — ADR-0031 assigned the regime the *risk budget*, which ADR-0025's Correction had withdrawn **two days earlier** on EXP-012; ADR-0031 cites EXP-012 **zero** times. Measured the live question instead (scale the *notional* cap): the label moves (**409 changes / 2,475 sessions**) but its median run is **2 sessions vs a 10-session horizon**; forward return **rises** with stress (`neutral` **0.287 %** → `extreme_volatility` **1.880 %**), as does return per unit of dispersion (**0.057** → **0.217**); every less-risk-when-stressed arm loses (mild **−1,818**, strong **−3,157** pct-points; bootstrap **[−3,699, −2,574], 100 % negative**). Same gradient that killed iso-risk. 🪤 Survivorship cuts against it. Closes item **64**; corrects [ADR-0031](../../decisions/0031-regime-scales-the-risk-budget-atr-keeps-the-stop.md) |

## Adding an experiment

1. Next id is `EXP-013`. Create `EXP-00N-<slug>.md` with the four headings above.
2. Add a row here.
3. Link the artifacts (transcripts, critique docs) from *Delivery*.
4. If it triggers a parameter change, that change runs as a **parameter experiment** (charter report) —
   the probe *informs* the dial; it does not move it.
