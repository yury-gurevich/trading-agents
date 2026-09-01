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

🚨 **RETRACTED 2026-08-20, before any code was written — this spec was wrong.** It originally
claimed `stop_target_mode` should be registered as a `tunable()` because it is a bare default at
[`analyst/settings.py:140`](../../agents/analyst/settings.py#L140). **The locked analyst law says
otherwise, deliberately**, and the law is right:

```text
| stop_target_mode | "flat" | Literal["flat","scaled"] — config | NO (mode selector) |
  ADR-0013 champion–challenger selector; `flat` is the champion.
  Not a tunable — it selects which formula runs, not a value within one |
```

S152's amendment log records the same call in words. The execution law carries **identical** wording
for `order_price_tolerance_mode`. So "not a tunable" is a first-class, reasoned category here — a
tunable is *a value within* a formula; a mode selector chooses *which formula runs* — and both
switches are documented in their PARAM tables with default, type and rationale. **They were never
invisible.** 🪤 **Do not register it, and do not file law drift against these rows.** The remaining,
real point stands: **the deliberator cannot see which mode produced the stop**, which is decision 4
below and needs no law change at all.

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
| `agents/analyst/settings.py` | — | 🪤 **Do not touch** — `stop_target_mode` is correctly a mode selector, not a tunable |

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
4. **~~Register `stop_target_mode` as a `tunable()`~~ — REMOVED 2026-08-20.** The locked analyst law
   declares it **`NO (mode selector)`** on purpose (ADR-0013, S152). Registering it would violate the
   law, and filing drift against the law would be filing drift against a correct rule. **Do neither.**
5. **Make the stop attest its basis**, reusing `volatility_present` / `volatility_fallback` if they
   already reach the recommendation.
6. **Check the debate packet actually improves.** The point is that the deliberator stops having to
   infer. Render the new fields and re-read a stored packet by hand.
7. `make ci` green (**redirected to a file, never piped**); every new guard planted, watched to fail,
   restored.

## Success factors

- [x] A ticker with no earnings date is recorded as **`earnings_window` not evaluated**, provably
      distinct from one that passed it. Same for `max_beta`.
- [x] Decision 2 applied: "no data" and "no upcoming earnings" are distinguishable, or the reason
      they are not is recorded.
- [x] `stop_target_mode` is **left exactly as it is** — not registered, no law drift filed.
- [x] The stop's basis (mode + ATR availability) reaches the debate packet.
- [x] **No change to which orders are approved**, or the change is named and justified.
- [x] Decisions 1–4 recorded with rejected alternatives.
- [x] `filters.py` does not cross 200; ideally back under 150.
- [x] Each new guard planted, watched to fail, restored — stated per guard.
- [x] `make ci` exit 0, 100.00 % coverage.
- [x] `make gate-ran` **GATE PROVEN**, run from the worktree whose `HEAD` is the commit, SHA checked.

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
   floor 0.025, ceiling 0.08, and stop_target_mode selects it.

   CORRECTION 2026-08-20 - AN EARLIER VERSION OF THIS SPEC WAS WRONG. It told you to register
   stop_target_mode as a tunable(). DO NOT. The locked analyst law declares it
   "NO (mode selector)" deliberately: "ADR-0013 champion-challenger selector; flat is the champion.
   Not a tunable - it selects which formula runs, not a value within one." The execution law says
   the identical thing about order_price_tolerance_mode. This is a reasoned category, not an
   oversight, and both switches ARE documented in their PARAM tables.
   DO NOT register it. DO NOT file law drift against those rows - the law is correct and the spec
   was not. The real defect is only that the DEBATE PACKET cannot see which mode produced the stop,
   which needs no law change.

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
6. Leave stop_target_mode exactly as it is. No registration, no law drift row.
7. Make the stop attest its basis (mode + whether ATR was available). resolve_stop_target ALREADY
   computes volatility_present and volatility_fallback - check whether they are persisted before
   adding new fields.
8. make ci green, REDIRECTED TO A FILE not piped. Plant every guard, watch it fail, restore.

CONSTRAINTS
- Attestation is ADDITIVE. The same tickers should survive and the same stops be chosen. If your
  diff changes which orders are approved you have gone out of scope - EXCEPT via decision 4, which
  may legitimately drop tickers that were silently sailing through. Say so explicitly if it does.
- Do NOT turn scaled stops on. The machinery is built and tempting.
- Do NOT edit any laws.md, and do NOT add a drift row for the mode-selector PARAM rows. Before
  treating any parameter question as drift, READ agents/<name>/laws/laws.md first - CLAUDE.md
  requires it, and skipping it is exactly how this spec got the instruction wrong.
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

**Status:** IMPLEMENTED — local proof complete; first pushed implementation tip remote-gated.

**Result:** Scanner filter evidence is now three-state. `Candidate` and `FilterVerdict` carry
`skipped_filters`, and the debate packet renders the skipped list beside the survived list. A ticker
with no earnings date records `earnings_window` as not evaluated; a ticker with a known past earnings
date records a negative `days_to_earnings` and an evaluated `earnings_window` pass. Thin beta history
records `max_beta` as skipped. The stop basis now reaches the debate packet from existing
`StopTargetEvidence`: selected mode, ATR availability, ATR value, applied stop/target, fallback flag,
and counterfactual mode.

`stop_target_mode` was left exactly as the corrected spec requires: no `tunable()` registration, no
law drift row, no default flip. No approval predicate changed: unknown earnings remains an attested
skip rather than a drop, near-future earnings still drops, thin beta remains an attested skip rather
than a drop, and the flat stop champion remains selected.

**Files changed:** `contracts/scanner.py`; `agents/scanner/domain/filter_attestation.py`;
`agents/scanner/domain/filters.py`; `agents/scanner/domain/ranking.py`;
`agents/scanner/tests/test_scanner_earnings.py`; `agents/scanner/tests/test_scanner_beta.py`;
`agents/scanner/tests/test_scanner_domain.py`; `agents/deliberator/context.py`;
`agents/deliberator/context_pm.py`; `agents/deliberator/context_stop.py`;
`tests/veto_context_fixtures.py`; `tests/test_veto_context.py`; `docs/design-log.md`;
`docs/STATE.md`; `pyproject.toml`; `uv.lock`.

**Design decisions:** Recorded as
[`DL-126`](../design-log.md#dl-126---s183-skipped-filters-and-stop-basis-are-explicit---status-decided-2026-08-20).
Decisions: carry not-evaluated as a sibling `skipped_filters` field; split no-data earnings from
known non-upcoming/past earnings; do not mark normal sparse earnings coverage as provider
degradation in S183; render stop basis from existing analyst evidence while leaving
`stop_target_mode` unchanged. Rejected alternatives are recorded there.

**Proof:** Planted focused guards first, before the implementation. The red run was:

```text
uv run pytest agents/scanner/tests/test_scanner_earnings.py agents/scanner/tests/test_scanner_beta.py agents/analyst/tests/test_scaled_stop_targets.py tests/test_veto_context.py --no-cov
exit 1
```

Active red failures included:

- no-earnings-date attestation: `AttributeError: 'Survivor' object has no attribute
  'skipped_filters'`;
- past-earnings split: `KeyError: 'days_to_earnings'`;
- thin-beta attestation: `AttributeError: 'Survivor' object has no attribute 'skipped_filters'`;
- stop-basis packet line: assertion failed because the packet had no `stop_target basis`.

The corrected focused proof was:

```text
uv run pytest agents/scanner/tests/test_scanner_earnings.py agents/scanner/tests/test_scanner_beta.py agents/scanner/tests/test_scanner_domain.py agents/analyst/tests/test_scaled_stop_targets.py agents/analyst/tests/test_stop_target_evidence.py tests/test_veto_context.py --no-cov
34 passed in 1.29s
```

Manual packet inspection rendered the new fields:

```text
Analyst recommendation ... stop_target basis: mode=flat; volatility_present=True; volatility_fallback=False; atr_pct=2.94%; applied_stop_pct=3.00%; applied_target_pct=8.00%; counterfactual_mode=scaled
Scanner candidate ... survived_filters=['price', 'volume']; skipped_filters=['earnings_window']
Scanner verdict ... filter_fired=None; ... skipped_filters=['earnings_window']
```

Line-count proof: `agents/scanner/domain/filters.py` is 136 lines; the new
`agents/scanner/domain/filter_attestation.py` is 43 lines.

**Guards planted:** `test_no_earnings_data_records_earnings_gate_not_evaluated`,
`test_past_earnings_date_records_evaluated_pass_not_missing_data`,
`test_beta_cap_drops_high_beta_keeps_low_beta_skips_thin_history`, and
`test_context_renders_stop_target_basis_from_analyst_evidence` were planted red, watched fail as
above, and restored green in the focused run and full gate.

**`make ci`:** redirected to `C:\Users\yury_\Downloads\project\trading-agents-s183-make-ci.log`.
Exit code 0. Pytest reported `2332 passed, 6 skipped`, required coverage reached at `100.00 %`.
`pip-audit` reported no known vulnerabilities. `detect-secrets` passed.

**`make gate-ran`:** run from
`C:\Users\yury_\Downloads\project\trading-agents-s183` at
`50086f3a5231223104732fa4fee80df23bd34338`.

```text
GATE PROVEN for 50086f3a5231223104732fa4fee80df23bd34338:
  Security Findings: success
  CI: success
```

This closeout update is docs-only; the final handback must also cite `make gate-ran` for the pushed
docs-only branch tip.
