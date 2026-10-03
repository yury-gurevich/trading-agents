<!-- Agent: planning | Role: helicopter view of what is left to build, by capability rather than by sprint -->
# What remains to build: the functional view

**Snapshot, taken 2026-10-03 at `main` = `0.121.03`.** This is not a tracker. The ranked queue is
still [work-queue.md](work-queue.md), and live state is still [STATE.md](STATE.md). This page answers
one question: **which capabilities does the system still lack?** It groups the open work by what the
system will be able to do, not by sprint. Where a source document holds the detail, the row links to it.

**Status key:** 🔴 not started · 🟠 partly built, or measurement running · 🅿️ parked behind a trigger
or decision · 🚦 the operator's decision · ⏳ waiting on market sessions, not effort.

---

## Baseline: what already works

The pack trades on paper every NYSE session without anyone touching it: scan → analyse → PM risk gates →
LLM referee → execution with broker stops → monitor → report, on 16 Container Apps over a Postgres
graph spine. Holdings are reconciled to the broker every run. The operator gets one Telegram brief a
night and a dashboard that shows the book against SPY and the unattended-run clocks. A survivorship-free
ten-year replay harness exists and agrees with live decisions on the fleet's own inputs. Everything
below is what is **not** there yet.

---

## 1. Prove there is an edge (next-leg P17)

The question that decides the rest: does the pipeline beat SPY held at the same exposure, out of sample?

| # | Capability still missing | Status | Notes |
| --- | --- | --- | --- |
| 1.1 | **Replay fidelity verdict**: a formal PASS that replay equals live on four sessions of unchanged code | ⏳ 🟠 | Due 2026-10-08, after `sched-2026-10-07`. The fleet is held on `s251` until then. |
| 1.2 | **EXP-014, the ten-year verdict**: excess return over exposure-matched SPY, with a bootstrap interval, a slippage sweep and a drop-one-pillar ablation, written up as an ADR | 🔴 | Runs once 1.1 passes. Price-only (technical + relative strength): fundamentals and sentiment have no point-in-time history on our data plans. |
| 1.3 | **G-EDGE decision**: branch A (there is an edge, put it to work) or branch B (there isn't, freeze the pack) | 🚦 | Capital-risk policy, so the operator decides. Sections 3 and 6 depend on it. |

## 2. Manage the book: exits beyond the stop (work-queue 92, moonshot #1)

🔴 **The largest functional gap in trading behaviour today.** The only exit that ever fires is the
protective stop. Nothing takes profit, trims, adds, or exits on time, and every sell closes the whole
position.

| # | Capability still missing | Status | Notes |
| --- | --- | --- | --- |
| 2.1 | **Calibrated outcome probabilities**: P(target first / stop first / neither) for each buy, settled and scored live | 🟠 ⏳ | Forecast and settlement are built (S239, S241). The scorecard needs about 10 sessions per claim before it has any settled; 0 of 15 were settled on 2026-09-30. |
| 2.2 | **Exit-policy experiment**: stops only, against take-profit at target, a ~10-session time exit, a trailing stop, and a weekend hold, on the replay cache | 🔴 | Pre-registered before it runs, $0 LLM ([DL-240](design-log.md)). |
| 2.3 | **Take-profit at the target**: the target becomes a resting sell beside the stop (bracket / OCO) | 🔴 | The most likely first build. |
| 2.4 | **Holding profiles**: the intended holding period is recorded on each order and acted on | 🔴 | |
| 2.5 | **Trim and add**: partial sells and top-ups decided by evidence | 🔴 | Needs its own law cycle. |
| 2.6 | **The PM decides over distributions** instead of single scores | 🔴 | Moonshot #1 in full. Only once 2.1 shows skill. |

Ruled out: short selling and intraday strategies ([DL-240](design-log.md)).

## 3. Improve and grow the signal (P18A, branch A only)

| # | Capability still missing | Status | Notes |
| --- | --- | --- | --- |
| 3.1 | **Capital deployment**: how much of the book is in the market (position size, max positions, cash floor), chosen from replay arms | 🔴 🚦 | The book is ~22 % invested today. The operator picks the arm. Aligns the PM defaults the fleet overrides. |
| 3.2 | **Pillar reweighting**: drop or down-weight what EXP-014's ablation shows earns nothing | 🔴 | Champion against challenger through the stage gate, never a silent swap. |
| 3.3 | **EXP-015: price-only ensemble against the technical score** | 🟠 | Pre-registered, not yet run. A win enters the forecaster's shadow loop. |
| 3.4 | **Sentiment scorecard (P12)**: does news sentiment earn its 0.20 weight? | 🅿️ | News has been accruing nightly for weeks, so the data may now be enough. |
| 3.5 | **Signal-discovery loop**: the researcher proposes a signal, the harness scores it out of sample, the gate promotes it or not | 🔴 | Moonshot #3. Only worth building once the harness can say no. |

**On branch B instead:** one item. The pack is frozen as the platform's reference workload, tuning stops,
and the LLM referee is kept or dropped on cost against evidence (E18B.1).

## 4. A referee that understands what it judges (deliberator: work-queue 97, 98, 99, 75)

The LLM challenger and judge get ~60 numbers with no definitions, some with misleading names. The work
here is to make their reasoning grounded and measurable, then to optimise it.

| # | Capability still missing | Status | Notes |
| --- | --- | --- | --- |
| 4.1 | **Recorded reasoning for the judge**, as the defender and challenger now have | 🟠 | Done for two of three roles (S246). |
| 4.2 | **Unambiguous names, and one glossary generated from code** for all three roles | 🔴 | 97 (b) and (c). 73 source-owned keys to define. |
| 4.3 | **Complete evidence packet**: holdings, cash, equity, the other orders in the batch, past fills and realised P&L in the ticker, VIX status, ATR, earnings horizon | 🔴 | Item 98. Ships with or just before 4.2. |
| 4.4 | **Offline prompt optimisation (GEPA)**, driven by the completeness and truth assessments | 🔴 | 97 (d). Needs a stated LLM budget. The golden firewall is re-frozen on current models here. |
| 4.5 | **Balanced few-shot examples**: the judge has only ever been shown `revise`, and the defender has no examples at all | 🔴 | Item 75. An experiment on recorded debates; it may explain part of the veto rate. |
| 4.6 | **Barrier forecast shown to the referee** | 🅿️ | Item 99. Trigger: 2.1's live scorecard shows skill (`skill_lo > 0`). |
| 4.7 | **Jev shadow path**: every typed decision at every stage is also put to a cheap typed model, and agreement is recorded | 🅿️ | The operator wants it ([ideas.md](ideas.md)). Not specced or ranked; access is provisioned. |

## 5. The operator out of the loop (P19, PRD Phase C)

| # | Capability still missing | Status | Notes |
| --- | --- | --- | --- |
| 5.1 | **Safe two-way commands from the phone**: pause, resume and acknowledge over Telegram, with a chat-id allowlist, a confirm step and a full audit | 🔴 | E19.2. Opens a new inbound channel, so it gets a scoped security review. |
| 5.2 | **Twenty unattended sessions in a row**: G1 ≥ 95 % of cycles complete, human intervention on < 20 % of healthy days | ⏳ 🟠 | The clocks exist (S236). Baseline G1 was 70 %. This formally closes the etalon bar. |
| 5.3 | **Mobile/PWA approvals and one-tap "why" summaries** | 🔴 | Named in the PRD's Phase C. No leg plans it; Telegram covers the minimal version. |

## 6. A platform, not just a trading app (P20)

The substrate/pack wall is now enforced by `import-linter` (S232). Whether it is general is still
unproven, because only one pack exists.

| # | Capability still missing | Status | Notes |
| --- | --- | --- | --- |
| 6.1 | **A second pack, the repo-steward**: 2–3 agents that watch this repo's CI and doc drift, built through `ops/agent-genesis.md` with zero substrate edits | 🔴 | E20.3. Known leaks to fix in the substrate first: the deliberation prompts and market-pack protocol in the kernel, and the trading rosters of the supervisor and operator. |
| 6.2 | **Both packs on one fleet**: one master, isolated grants, one night | 🔴 | E20.4. |
| 6.3 | **Genesis retrospective**: ADR-0012 moves from declared to proven | 🔴 | E20.5, docs only. |

## 7. Data correctness and lineage (smaller, ranked below live defects)

| # | Capability still missing | Status | Notes |
| --- | --- | --- | --- |
| 7.1 | **Every agent works on the run's as-of date, not the wall clock**, so a test run or replay of a past day reads that day | 🟠 | Item 103 part two: eight reads in the analyst, forecaster, monitor, PM and scanner, plus the barrier history. The provider is fixed (S249). |
| 7.2 | **The graph records which vendor served each bar** | 🔴 | Item 105 (DRIFT-040). Today it records only a "fallback used" flag. |
| 7.3 | **One item's failure never takes a whole stage down**: per-item containment audited in every fan-out stage | 🅿️ | [ideas.md](ideas.md). Fixed in execution only. |

## 8. In flight: built, waiting to land

No new capability here. These items close by being proven, not by being built.

- **The retag after 1.1**: it carries S252 (the six pending-work finders fetch only their work, ~3.8 GB a
  night less transfer) and S253 (a run's snapshot counts broker fills). Each owes an F2 on a live run
  (items 101 and 106).

---

## Not planned in any leg (deferred on purpose)

| Area | Why it waits |
| --- | --- |
| **Live money**: the PRD's staged promotion, paper → broker-shadow → live-manual → live-autopilot | No leg plans it. The natural gate is G-EDGE = A plus 5.2. Capital-risk policy, so the operator decides. |
| **Other markets and exchanges** (PRD Phase D) | The market-pack abstraction exists. No second market is planned before the US loop is trusted. |
| **P13 cross-asset and macro signal graph** | Needs premium supplier and exposure data. No case for it until branch A. |
| **Automated continuous improvement** (ADR-0013: run metrics, parameter sets, gated promotion, optimiser; specs S90–S95) | Specs are queued but superseded in practice. `tunable()` settings exist, and experiments are run and promoted by hand. |
| **Moonshots #4–#6**: a causal DAG over signals, learning from the system's own narration, a full master incident-recovery catalogue | [moonshots.md](moonshots.md). None scheduled. |
| **Regime-driven risk scaling** | EXP-013 found it should not scale risk on this configuration. Folded into section 2's probability work. |

---

## Rough size of what remains

From [next-leg-plan.md](next-leg-plan.md), in units of about one sprint each, at 0.5–1 unit per working day:

| Track | Remaining | Gated by |
| --- | --- | --- |
| Edge proof (1) | ~1 unit plus the operator's decision | Fidelity verdict, 2026-10-08 |
| Book management (2) | Not yet estimated: one experiment plus 3–4 builds | Probabilities need settled sessions |
| Signal (3), branch A | ~5 units (or 1 on branch B) | G-EDGE |
| Referee (4) | ~4–5 units plus an LLM budget | — |
| Operator out of the loop (5) | ~2 units, plus 20 sessions of calendar time | — |
| Second pack (6) | ~5.5 units | Best after G-EDGE |
| Correctness (7) | ~2 small units | — |
