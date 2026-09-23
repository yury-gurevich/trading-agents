<!-- Agent: planning | Role: the proposed next development leg — phases P16–P20, their work items and unit-of-work estimates -->
# Next leg — from "it runs" to "it earns, and the platform is real"

**Status:** PROPOSED, 2026-09-23, planner. Not yet accepted by the operator. The reasoning and the
roads not taken are in [DL-209](design-log.md).

**What this document is.** A plan for the next leg of development, written to be cut into
**extension sprints**. Each work item below (`E16.1`, `E17.2`, …) is sized to become **one sprint
spec** built from [`sprints/_TEMPLATE.md`](sprints/_TEMPLATE.md). The legs are numbered **P16–P20**
so [`build-plan.md`](build-plan.md) can adopt them as phases at closeout, the same way P11 was added
as an extension.

**What this document is not.** It is not a status board. When a leg is accepted, its items become rows
in [`work-queue.md`](work-queue.md), and their progress lives there and in [`STATE.md`](STATE.md). This
file changes only when the plan changes. A second live tracker is what made the build plan go stale
once already.

**Evidence labels:** **[measured 2026-09-23]** means read today from the broker, the repo or git.
**[assumed]** means not yet checked. Every *[assumed]* line is a risk to the estimate, and where one
matters, the first work item in its leg is the measurement.

---

## 1. Where we are

**The machine is built.** P0–P12, P14 and P15 are complete; P13 was deferred on purpose; the work queue
holds one queued item (75) and one parked item (71). The fleet trades unattended every night on paper,
and `ACCEPTANCE PASS` is proven live. **[measured 2026-09-23]**

**Whether it earns has never been measured.** The PRD's success measures (G1–G5) are about trust,
quiet running and control; none of them is about return. Read from the Alpaca paper account today
**[measured 2026-09-23]**:

| Since the first fill (2026-07-07) | Value |
| --- | --- |
| Portfolio return | **+2.13 %**: $100,000 → $102,133 (peak $102,837 on 2026-08-20) |
| SPY, same window | **+3.43 %** |
| Capital in the market | about **22 %**: $22.3k long, $79.7k cash |
| Activity | 259 fills (170 buys, 89 sells) across 35 symbols; 23 positions open, +$686 unrealized |

With 22 % exposure, holding SPY alone would have returned about 0.75 %, so the result is not bad. But
2.5 months and 35 symbols cannot tell skill from luck. The last two weeks of work were almost
entirely self-audit: gate tooling, status docs and dashboard consistency. The next leg should point the
same evidence discipline at the question that decides everything else: **is there an edge?**

**What already exists to build on** **[measured 2026-09-23]**:

- **Replay dataset.** `scripts/replay_dataset.py` caches about 263k daily bars plus VIX in OneDrive,
  never in the repo. It covers today's ~98 names only, so it is **survivorship-biased**.
- **Walk-forward backtest.** `agents/researcher/domain/backtest.py` (`run_walkforward`) works at the
  signal level: top-k rebalancing, information coefficient (IC), turnover, slippage, holdout. It does
  not run PM gates, stops or sizing.
- **Forecaster evaluation battery** (`agents/forecaster/domain/evaluation.py`, `return_scorecard.py`):
  rank IC, quantile spread, decay.
- **Reporter metrics** (`agents/reporter/domain/metrics.py`): approval, execution, close triggers,
  profit factor and expectancy. There is **no equity curve and no benchmark**.
- **Telegram notices**, one way, live since S219.
- **Survivorship handling: none.** Searching `agents`, `kernel`, `contracts` and `scripts` for
  "survivorship" finds nothing.

---

## 2. The unit of work

**One unit = one sprint:** a branch, then `make ci`, push, `make gate-ran`, merge, and a deploy plus
live check when runtime code changed. That is the loop in [CLAUDE.md](../CLAUDE.md), and each `E` item
below is one of these.

| Size | Units | What it looks like |
| --- | --- | --- |
| **S** | 0.5–1 | One module plus tests, no law change, no deploy or an image-only retag |
| **M** | 1–2 | A few modules, a law amendment (PARAM rows or new clauses), a deploy, one scheduled-run proof |
| **L** | 2–3 | A new capability across agents, or a new data source; a law cycle; proof over several runs |

**Throughput:** 34 sprint and chore docs were added between 2026-09-01 and 2026-09-23, about
**1.5 a day [measured 2026-09-23]**. Most of those were small fixes. For the M and L items here, plan on
**0.5–1 unit per working day [assumed]**. Wall-clock time is limited in two other ways:

- **Market sessions.** A live proof needs a scheduled run, and there is one per NYSE session. Items
  marked ⏳ wait on sessions, not on effort, and can overlap other work.
- **Builder availability.** The coding agent's credits are provisional (Copilot is the stopgap).
  The unit counts don't change; the calendar does.

---

## 3. The leg at a glance

| Leg | Question it answers | Units | Elapsed (effort, then wait) | Depends on |
| --- | --- | --- | --- | --- |
| **P16** Scoreboard | Are we beating the index, today? | **4** | ~1 week + 1 run ⏳ | — |
| **P17** Historical proof | Is there an edge over ten years, out of sample? | **7** | ~2 weeks | P16 (shared metric code) |
| 🚦 **Gate G-EDGE** | Operator reads EXP-014 and picks branch A or B | 0 | one decision | P17 |
| **P18A** Put the edge to work | How much capital, which pillars, what next signal? | **5** | ~1.5 weeks | G-EDGE = A |
| **P18B** Freeze the pack | Keep a quiet reference workload; stop tuning | **1** | 1 day | G-EDGE = B |
| **P19** Operator out of the loop | Can it run a month with nobody looking? | **4** | ~1 week + 20 sessions ⏳ | P16 (brief shows the scoreboard) |
| **P20** Second pack | Is the platform general, or is it a trading app? | **8** | ~2–3 weeks | ADR-0012; best after G-EDGE |
| **Total** |  | **28 (branch A) / 24 (branch B)** | **~6–11 weeks (A) / ~5–10 weeks (B)** at 0.5–1 unit per working day **[assumed]** |  |

**Recommended order.** P16, then P17, then 🚦. **P19's first item (E19.1) can run alongside P17**: it
touches none of the same modules, and every day it runs is a day of unattended evidence banked. P20
comes last on branch A. On branch B it comes straight after 🚦, because it becomes the main line of
work.

```text
P16 ──► P17 ──► 🚦 G-EDGE ──► A: P18A ──► P20
  │                   └─────► B: P18B ──► P20
  └──► P19 (E19.1 in parallel with P17; E19.3's 20-session clock starts whenever E19.2 lands)
```

---

## 4. Legs and work items

### P16 — Scoreboard: "are we beating the index?" · 4 units

**Exit:** the dashboard shows portfolio return, SPY return and exposure-matched SPY since inception
and over rolling 20- and 60-session windows. On a scheduled run the equity figure reconciles to Alpaca
to the cent. The operator chat can answer "are we beating the market?" from graph facts only.

| ID | Item | Size | Notes |
| --- | --- | --- | --- |
| E16.1 | **Equity snapshot per run.** At run start, the agent that already reads the broker snapshot for reconciliation (DL-44) also records an `EquitySnapshot` fact: equity, cash, long market value, broker as-of. | M (1.5) | New vocabulary type, so a **full `up`**, not a retag (the S202 lesson). Which agent writes it: **[assumed]** monitor; confirm against the reconciler. ⏳ 1 run. |
| E16.2 | **Performance metrics, one definition.** A pure metrics module: time-weighted return, benchmark return, exposure-matched benchmark (average exposure × SPY), excess return, max drawdown, realized vs unrealized P&L. The same code will score the P17 replay. | M (1) | One definition for live and replay (the DL-208 lesson). The benchmark ticker is **pack config**, never substrate (ADR-0012). |
| E16.3 | **Backfill from broker history.** A one-time read-only script loads Alpaca portfolio history since 2026-07-07 as `EquitySnapshot` facts marked `source=backfill`, so the scoreboard starts with 2.5 months instead of zero. | S (0.5) | Alpaca date traps apply: 1D bars are labelled +1 day in UTC. |
| E16.4 | **Surface it.** A glance tile on the dashboard (**vs SPY**: green, amber or red on excess return), a chat tool answer, and one line in the nightly Telegram notice. | S (1) | Glance-first; no S-numbers in the UI (DL-47). |

### P17 — Historical proof: a full-pipeline walk-forward replay · 7 units

**Exit:** **EXP-014** reports ten years of out-of-sample, survivorship-free results for the
deterministic pipeline against SPY and exposure-matched SPY. It includes a bootstrap confidence
interval and a drop-one-pillar attribution, and closes with an ADR stating **edge / no edge / edge in
pillars X**. LLM cost: **$0**, because the replay has no deliberator. That is defensible because since
ADR-0029 only `overturn` blocks an order, and overturns ran at **6.2 %** of reviews **[measured
2026-09-22]**. E17.4 measures the resulting gap rather than assuming it away.

| ID | Item | Size | Notes |
| --- | --- | --- | --- |
| E17.1 | **Spike: can we buy a survivorship-free universe?** Measure point-in-time S&P 500 membership (FMP historical constituents **[assumed available on our plan]**) and bar coverage for delisted names (Alpaca **[assumed thin]**, Tiingo **[assumed good]**, within the 500 symbols/month limit). | S (1) | **Measure first; highest risk in the leg.** If coverage is below ~90 % of member-days, the fallback is to bound the bias: replay the survivors and report the result as an upper bound. |
| E17.2 | **Point-in-time universe + cache.** Extend `replay_dataset.py` with daily membership and delisted bars. The cache stays in OneDrive, never the repo: the repo is public and SIP bars are licensed. | M (1.5) | `scripts/` is size-gated since 2026-09-23: split rather than grow. |
| E17.3 | **Replay harness.** Day by day over the cache, drive the **real** scanner → analyst → PM domain functions (no bus, no graph), fill at the next open with slippage, apply stops and time exits as monitor would, and produce a daily equity curve scored by E16.2's metrics. | L (2.5) | Reuses `run_walkforward` pieces. **[assumed]** the domain functions can be called without the bus; if a stage reads the graph mid-decision, an adapter is part of this item. Scripts may import agents (the `backtest_proposal.py` precedent); agents never import each other. |
| E17.4 | **Fidelity check.** Replay 2026-07-07 → today and compare with what actually happened: approved-order membership, then fills and P&L. The bar, modelled on ADR-0030's 45/45: **≥ 90 % membership**, with every difference explained (deliberator overturns, broker rejections, data differences). | M (1) | **Without this the backtest is fiction.** If fidelity fails, P17 stops here and the gap becomes the work. |
| E17.5 | **EXP-014 plus the verdict ADR.** A 10-year walk-forward with purged, non-overlapping test windows; bootstrap CI on excess return; drop-one-pillar ablations (technical, fundamental, relative strength, sentiment); a 5 bps / 10 bps / 25 bps slippage sweep. | M (1) | The ADR is the input to 🚦. The same survivorship caveat that EXP-013 carried must be **closed** here, not repeated. |

### 🚦 G-EDGE — the operator's decision

This is a **policy decision on capital risk, so it is the operator's** (technical decisions are
delegated; capital-risk policy is not). The planner reads EXP-014 and brings **one recommendation**.

- **A: edge.** Excess return over exposure-matched SPY, with a lower CI bound above 0, survives
  25 bps of slippage.
- **B: no edge.** The pipeline is a beta harvester; staying 78 % in cash is the only thing it adds.

### P18A — Put the edge to work · 5 units (branch A only)

| ID | Item | Size | Notes |
| --- | --- | --- | --- |
| E18A.1 | **Capital-deployment experiment.** Replay arms over `max_position_pct`, `MAX_POSITIONS` and a cash floor on the P17 harness; report return, drawdown and turnover. | M (1) | The operator picks the arm (capital risk). The two PM defaults the fleet overrides get aligned here (S223's residue). |
| E18A.2 | **Pillar reweighting.** Drop or down-weight pillars that EXP-014's ablation shows earn nothing; each change goes through the stage gate as a proposal with replay evidence. | M (1.5) | Champion–challenger, never a silent swap. |
| E18A.3 | **Signal-discovery loop (moonshot #3), first cut.** The researcher proposes a signal, the P17 harness scores it out of sample, and the stage gate promotes it or not. The loop is the deliverable, not any particular signal. | L (2.5) | Only worth building once there is a harness that can say no. |

### P18B — Freeze the pack · 1 unit (branch B only)

| ID | Item | Size | Notes |
| --- | --- | --- | --- |
| E18B.1 | **Reference-workload mode.** Record the verdict ADR; stop tuning trading parameters; keep the nightly run as the platform's canary; decide on the LLM deliberator by cost against evidence. | S (1) | The trading pack becomes the platform's test load, not its product. |

### P19 — Operator out of the loop (PRD Phase C, minimal) · 4 units

**Exit:** 20 consecutive NYSE sessions, with no human command except reading. The PRD's G1 (≥ 95 % of
cycles complete) and G3 (intervention on < 20 % of healthy days) are measured by code, not asserted.
That formally closes the etalon bar.

| ID | Item | Size | Notes |
| --- | --- | --- | --- |
| E19.1 | **Daily brief over Telegram.** One message per session: verdict (RED/GREEN), the P16 scoreboard line, what traded, and what needs you (usually nothing). A strict notification budget; the details stay behind the dashboard. | M (1) | Builds on the S219 notice path. Can run **in parallel with P17**. |
| E19.2 | **Safe two-way commands.** Pause, resume and acknowledge from Telegram through the existing typed operator-intent layer: chat-id allowlist, confirm step, full audit. | L (2) | G4/G5: every command is typed, audited and reversible. Security gets a scoped review here despite the deferred hardening pass, because this opens a new inbound channel. |
| E19.3 | **G-scorecard.** Compute G1 and G3 from the graph (cycles completed; days with a human command), show them on the dashboard, and start the 20-session clock. | S (1) | ⏳ 20 sessions ≈ 4 weeks of calendar time, overlapping everything else. |

### P20 — Second pack: make ADR-0012's wall real · 8 units

**Exit:** a non-trading pack runs on the same substrate and fleet, with **zero substrate edits after
E20.2**. An `import-linter` contract enforces the substrate/pack wall. `ops/agent-genesis.md` is shown
to produce the new pack's agents, not only the hand-built trading ones.

| ID | Item | Size | Notes |
| --- | --- | --- | --- |
| E20.1 | **Choose the pack.** Criteria: no broker, cheap data, a daily cadence, a verifiable outcome. Candidates: (a) a research/news watch pack; (b) a repo-steward pack that watches this repo's CI and doc drift (dogfooding, moonshot #7); (c) a personal-finance reconciler. | 0 | **Operator's choice.** The planner recommends (b): it has real data, a real outcome and no licence cost. |
| E20.2 | **Fix the named leaks.** Master's `DEFAULT_GRANTS` becomes a grant policy the pack supplies; `contracts/` splits into substrate and pack; an `import-linter` contract enforces the wall. | L (2.5) | Touches master and every agent's imports, so a **full `up`** with pack read-back. ⏳ 1 run. |
| E20.3 | **Build the pack via genesis.** Two or three agents with laws from `docs/laws/_TEMPLATE.md`, contracts, and a bus topology. Measure the substrate diff, with a target of 0. | L (3) | Every substrate edit this item needs is a leak found, recorded as a DL and fixed in the substrate, not worked around in the pack. |
| E20.4 | **Both packs on one fleet.** Deploy, schedule, and prove both packs run on one night with isolated grants and one master. | M (1.5) | ⏳ 1–2 runs. |
| E20.5 | **Genesis retrospective.** Update `ops/agent-genesis.md` with what the second pack taught; record the ADR-0012 re-opening (de jure → de facto). | S (1) | Docs only: light path, no bump. |

---

## 5. Standing rules for this leg

- **Process freeze.** Add no new CI gate, tracking surface or status doc unless a defect actually
  reached the broker or the fleet. The meta-work has stopped paying for itself; this leg's evidence
  budget goes to return, not to self-audit.
- **Fixes still come before features.** A live defect found mid-leg is ranked above the next `E`
  item, as it is today.
- **One metric definition.** Live (P16) and replay (P17) use the same code. Two definitions of
  "return" would reproduce DL-208's contradiction on the number that matters most.
- **Spend.** P16, P17 and P20 need no LLM calls. P19's brief is deterministic text. The only
  LLM-bearing path stays the nightly deliberator.

## 6. Parked, deliberately not in this leg

| Item | Why it waits |
| --- | --- |
| Work-queue **75** (defender/challenger grounding) | Tunes the deliberator; worth it only on branch A. |
| Work-queue **71** (regime probabilities) | EXP-013 found the regime should not scale risk on this configuration; revisit on the P17 harness if at all. |
| **P12 sentiment scorecard** | News has been accruing nightly (1,893 headlines on `sched-2026-09-21` **[measured 2026-09-22]**), so the runway may now exist. It is a natural P18A.2 input. |
| **P13** cross-asset graph | Needs premium relationship data; no case until branch A. |
| TypeSafe Jev challenger ([ideas.md](ideas.md)) | A cheaper deliberator; matters on branch A, and only against an eval set. |
