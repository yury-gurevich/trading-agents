<!-- Agent: scanner | Role: sprint spec — a gate that was never evaluated must say so, and the stop must name its basis -->
# S183 — a gate that did not run says so

**Closes:** the two new deliberator complaints of 2026-08-20 · **Opens from:**
[DL-119](../design-log.md) · **Type:** fix ·
**Target version:** next available **PATCH** at merge — **do not pin it in this file** ·
**Branch:** `sprint-183-a-gate-that-did-not-run-says-so`

> Handover to a delegated coding agent. Everything under **Measured** was read off this repo or the
> live spine on **2026-08-20**. Everything marked **Assumed** has **not** been verified — check it
> before building on it. Do not treat an unmarked claim as measured.

## Why

**Two gates cannot answer the question asked of them, and the deliberator caught both on the same
run.** They look unrelated; they are the same defect — *a gate reports its verdict but not whether
it was evaluated.*

### Complaint 1 — a filter that never ran is indistinguishable from one that passed

The deliberator vetoed **NEE** and **XOM** on `verify-2026-08-20-s182-a`:

> *"NEE's `survived_filters` lists only min_price/min_average_volume/min_relative_strength — no
> `earnings_window` attestation — so `filter_fired=None` only shows no applied filter tripped,
> leaving the event window unverified."*

**Measured — it is exactly right, and it is in the code.**
[`filters.py:131-135`](../../agents/scanner/domain/filters.py#L131-L135):

```python
if "days_to_earnings" in features:
    if features["days_to_earnings"] <= settings.earnings_exclusion_days:
        return "earnings_window", tuple(passed)
    passed.append("earnings_window")
```

If `days_to_earnings` is **absent** the gate is skipped in silence. `_days_to_earnings` returns
`None` when the earnings date is **unknown *or already past***, so absence conflates "no data" with
"no upcoming earnings". [`filters.py:128-131`](../../agents/scanner/domain/filters.py#L128) gives
`max_beta` the identical shape.

**Measured — how often. `verify-2026-08-20-s182-a` carried earnings dates for 10 of 98 tickers —
10 % coverage.** So roughly **88 tickers per run pass the earnings gate without it ever being
evaluated**, and the only trace is an absence from `survived_filters` that nothing consumes.
🚨 **That means the system can buy two days before earnings** whenever the vendor has no date for
that name — which is the normal case, not the edge case.

🪤 **The provider does not flag it.** `quality.notes` on that run was **empty** — no
`earnings_degraded`. 10 % coverage is reported as healthy.

### Complaint 2 — the stop cannot say what it is based on

> *GOOG: "the sizing gate is a fixed-fraction portfolio-ratio cap, not volatility-adjusted, so it
> cannot answer a 5 % stop sitting under ~1.7 daily ATRs (atr_pct=2.938)"*

**Measured — the volatility-scaled stop already exists and is switched off.** S150 shipped the whole
path: [`stop_target.py`](../../agents/analyst/domain/stop_target.py) has `resolve_stop_target`,
`_scaled_stop`, `volatility_present` / `volatility_fallback`, with
`scaled_stop_atr_multiplier=2.0`, `scaled_stop_floor_pct=0.025`, `scaled_stop_ceiling_pct=0.08`.

🚨 **But the switch is not a `tunable()`.**
[`agents/analyst/settings.py:140`](../../agents/analyst/settings.py#L140):

```python
stop_target_mode: StopTargetMode = "flat"
```

A bare default sitting between two properly registered tunables. It is therefore **invisible to the
parameter catalogue and to the operator**, and nothing sets it on the fleet. Same shape as S174's
bare `_DEFAULT_LOOKBACK_DAYS = 60`, which hid a defect for weeks.

## Scope — and what is deliberately NOT here

**In scope: make both gates attest.** A gate must report *evaluated and passed*, *evaluated and
failed*, or *not evaluated* — three states, not two.

🚨 **Out of scope: actually turning scaled stops on.** That is a **champion-vs-challenger
experiment**, not a code change — it moves which orders get approved and needs a measured
before/after on the same `as_of`. Mixing a promotion into this sprint would contaminate exactly the
measurement that justifies it. **This sprint makes the switch visible and the basis legible; a
separate experiment decides the value.**

## The design decisions this sprint has to make

**1 · How is "not evaluated" carried?** `survived_filters` is a `tuple[str, ...]` of names
([`contracts/scanner.py`](../../contracts/scanner.py), 95 lines) rendered straight into the debate at
[`context.py:117`](../../agents/deliberator/context.py#L117). Options:

- **(a) A sibling field** — `skipped_filters: tuple[str, ...]`. Explicit, additive, and the packet
  can render both. Costs a contract change and a vocabulary-pack property if `Candidate` is
  property-enforced — 🪤 **check that before choosing**; only 5 labels are enforced today.
- **(b) Encode in the existing tuple** — e.g. `"earnings_window:not_evaluated"`. No contract change,
  but it makes a list of names into a list of name-value pairs and every reader must now parse.
- 🚨 **Recommended (a)**, because DL-113's rule is that a rendered value names its own meaning, and
  a parsed suffix is the opposite of that.

**2 · Does "no data" differ from "no upcoming earnings"?** `_days_to_earnings` returns `None` for
both. **Decide whether to split them** — a ticker with a known date 90 days out is genuinely safe;
a ticker with no date at all is unknown. 🚨 Collapsing them is what makes 10 % coverage look like
90 % safety. **Recommended: split.**

**3 · Should the provider flag thin coverage?** 10 of 98 with no `earnings_degraded` note. Either
add the note, or record explicitly why thin earnings coverage is not degradation. Do not leave it
undecided — 🪤 the analyst already has a `*_degraded` vocabulary and this is the one feed that does
not use it.

**4 · What does the stop attest?** Minimum: which mode produced it (`flat` / `scaled`) and whether
ATR was available. `resolve_stop_target` **already computes** `volatility_present` and
`volatility_fallback` — 🪤 **check whether they are already persisted before adding fields.**

## Blast radius — measured 2026-08-20

| File | Lines | Note |
| --- | --- | --- |
| `agents/scanner/domain/filters.py` | **154** | just over the 150 warn line; `_evaluate` is the change site |
| `agents/deliberator/context.py` | 131 | renders `survived_filters` |
| `contracts/scanner.py` | 95 | `Survivor` / `FilterVerdict` shapes |
| `agents/analyst/domain/stop_target.py` | 96 | already computes the attestation values |
| `agents/analyst/settings.py` | — | `stop_target_mode` needs `tunable()` registration |

🟢 **No trade decision changes if this is done right.** Attestation is additive: the same tickers
survive, the same stops are chosen. **If your diff changes which orders are approved, you have gone
out of scope** — except via decision 2, which may legitimately drop tickers that were silently
sailing through. **Say so explicitly if it does.**

## Steps, in order

1. **Failing test first:** a ticker with **no** earnings date must end up with `earnings_window`
   recorded as **not evaluated**, and must be distinguishable from one that passed it. Assert on the
   attestation, not on the drop count.
2. **Record decisions 1–4** in `docs/design-log.md` with rejected alternatives, **before**
   implementing. LAW-06. Take the next free DL number — 🪤 the log has duplicates (two `DL-110`, two
   `DL-111`) and entries are prepended at the top *and* appended at the bottom; check first.
3. **Implement the scanner attestation** (both `earnings_window` and `max_beta`).
4. **Register `stop_target_mode` as a `tunable()`** with a `why`, leaving the default **`"flat"`** —
   this sprint makes it visible, it does not flip it.
5. **Make the stop attest its basis**, reusing `volatility_present` / `volatility_fallback` if they
   already reach the recommendation.
6. **Check the debate packet actually improves.** The point is that the deliberator stops having to
   infer. Render the new fields and re-read a stored packet by hand.
7. `make ci` green (**redirected to a file, never piped**); every new guard planted, watched to fail,
   restored.

## Success factors

- [ ] A ticker with no earnings date is recorded as **`earnings_window` not evaluated**, provably
      distinct from one that passed it. Same for `max_beta`.
- [ ] Decision 2 applied: "no data" and "no upcoming earnings" are distinguishable, or the reason
      they are not is recorded.
- [ ] `stop_target_mode` is a registered `tunable()`, default unchanged at `"flat"`.
- [ ] The stop's basis (mode + ATR availability) reaches the debate packet.
- [ ] **No change to which orders are approved**, or the change is named and justified.
- [ ] Decisions 1–4 recorded with rejected alternatives.
- [ ] `filters.py` does not cross 200; ideally back under 150.
- [ ] Each new guard planted, watched to fail, restored — stated per guard.
- [ ] `make ci` exit 0, 100.00 % coverage.
- [ ] `make gate-ran` **GATE PROVEN**, run from the worktree whose `HEAD` is the commit, SHA checked.

## Traps

🪤 **Do not turn scaled stops on.** The machinery is built and tempting. Promotion is an experiment
with its own before/after; this sprint only makes the switch visible.

🪤 **`_days_to_earnings` returns `None` for two different things** — unknown date, and a date already
past. Treating them alike is the root of complaint 1.

🪤 **10 % coverage is the normal case, not an outage.** Any fix that assumes earnings data is usually
present will be wrong for ~88 of 98 tickers per run.

🪤 **A vocabulary-pack property may be needed** if `Candidate` is property-enforced. Only 5 labels
are today — **verify rather than assume**; if it is, code and pack must deploy together.

🪤 **A script run from a git worktree silently gets the in-memory store** — no `.env`. Copy the
refuse-on-in-memory guard from `scripts/sweep_divergence_flags.py`. Never copy `.env` into a worktree.

## Handover — paste this to Codex

```text
Work item: S183 - a gate that did not run says so.
Repo: trading-agents. Read docs/sprints/sprint-183-a-gate-that-did-not-run-says-so.md in full before
writing anything. Read CLAUDE.md. Read docs/INDEX.md before opening any docs folder.

WHAT IS WRONG
Two gates report a verdict but not whether they were evaluated. The deliberator caught both on
verify-2026-08-20-s182-a and vetoed orders over them.

1. A SCANNER FILTER THAT NEVER RAN LOOKS LIKE ONE THAT PASSED.
   agents/scanner/domain/filters.py:131-135 -
     if "days_to_earnings" in features:
         if features["days_to_earnings"] <= settings.earnings_exclusion_days:
             return "earnings_window", tuple(passed)
         passed.append("earnings_window")
   If days_to_earnings is ABSENT the gate is skipped silently. _days_to_earnings returns None when
   the earnings date is unknown OR already past, so absence conflates "no data" with "no upcoming
   earnings". filters.py:128-131 gives max_beta the same shape.
   MEASURED: verify-2026-08-20-s182-a carried earnings dates for 10 of 98 tickers - 10% coverage. So
   ~88 tickers per run pass the earnings gate unevaluated, and the only trace is an absence from
   survived_filters that nothing consumes. The system can buy two days before earnings whenever the
   vendor has no date. quality.notes on that run was EMPTY - no earnings_degraded.

2. THE STOP CANNOT SAY WHAT IT IS BASED ON.
   S150 already built the volatility-scaled stop: stop_target.py has resolve_stop_target,
   _scaled_stop, volatility_present/volatility_fallback, scaled_stop_atr_multiplier=2.0,
   floor 0.025, ceiling 0.08. But agents/analyst/settings.py:140 is
     stop_target_mode: StopTargetMode = "flat"
   a BARE DEFAULT, not a tunable(), sitting between two registered tunables - so the switch is
   invisible to the parameter catalogue and nothing sets it on the fleet. Same shape as S174's bare
   _DEFAULT_LOOKBACK_DAYS = 60.

SCOPE - AND WHAT IS NOT IN IT
IN: make both gates attest. A gate must report evaluated-and-passed, evaluated-and-failed, or
NOT-EVALUATED. Three states, not two.
OUT: turning scaled stops on. That is a champion-vs-challenger EXPERIMENT that moves which orders
get approved and needs a measured before/after on the same as_of. Mixing it in contaminates the
measurement that would justify it. Make the switch visible; do not flip it.

WHAT TO DO
1. Failing test FIRST: a ticker with NO earnings date must end up with earnings_window recorded as
   not-evaluated, distinguishable from one that passed. Assert on the attestation, not the drop count.
2. Record the design decisions in docs/design-log.md WITH rejected alternatives, before implementing.
3. Decide how "not evaluated" is carried. Recommended: a sibling field skipped_filters, NOT an
   encoded suffix inside survived_filters - DL-113's rule is that a rendered value names its own
   meaning, and a parsed suffix is the opposite. Check whether Candidate is property-enforced in
   orchestration/packs/trading_graph_vocabulary.json first; only 5 labels are today. If it is, code
   and pack must deploy together.
4. Decide whether "no data" differs from "no upcoming earnings". _days_to_earnings returns None for
   both. Recommended: SPLIT them - collapsing them is what makes 10% coverage look like 90% safety.
5. Decide whether the provider should flag thin earnings coverage as degraded, or record why not.
   Do not leave it undecided; the analyst already has a *_degraded vocabulary and this feed alone
   does not use it.
6. Register stop_target_mode as a tunable() with a why. LEAVE THE DEFAULT AT "flat".
7. Make the stop attest its basis (mode + whether ATR was available). resolve_stop_target ALREADY
   computes volatility_present and volatility_fallback - check whether they are persisted before
   adding new fields.
8. make ci green, REDIRECTED TO A FILE not piped. Plant every guard, watch it fail, restore.

CONSTRAINTS
- Attestation is ADDITIVE. The same tickers should survive and the same stops be chosen. If your
  diff changes which orders are approved you have gone out of scope - EXCEPT via decision 4, which
  may legitimately drop tickers that were silently sailing through. Say so explicitly if it does.
- Do NOT turn scaled stops on. The machinery is built and tempting.
- 10% earnings coverage is the NORMAL case, not an outage. Any fix that assumes earnings data is
  usually present will be wrong for ~88 of 98 tickers per run.
- agents/scanner/domain/filters.py is 154 lines, just over the 150 warn line. Do not cross 200.
- A script run from a git worktree silently gets the in-memory store (no .env) and every count reads
  0. Copy the refuse-on-in-memory guard from scripts/sweep_divergence_flags.py. NEVER copy .env into
  a worktree.
- Branch sprint-183-a-gate-that-did-not-run-says-so. Version: next available PATCH at merge, do not
  pin it. Push the branch and get `make gate-ran` GATE PROVEN before merging - run it from the
  worktree whose HEAD is the commit, and check the printed SHA. Fill in the Closeout block before
  handing back.
```

## Closeout — evidence

<!-- FILL THIS IN BEFORE HANDING BACK. A handback with this placeholder intact is not accepted. -->

**Status:** SPEC

**Result:** *not yet implemented.*

**Files changed:** *...*

**Design decisions:** *how "not evaluated" is carried, whether no-data differs from no-upcoming-
earnings, whether the provider flags thin coverage, and what the stop attests — as a DL entry with
rejected alternatives.*

**Proof:** *the failing test that came first; a no-earnings-date ticker attested as not-evaluated;
evidence that approved orders did not change, or the named reason they did.*

**Guards planted:** *per guard: what was planted, that it failed, that it was restored.*

**`make ci`:** *exit code, passed/skipped counts, coverage %.*
