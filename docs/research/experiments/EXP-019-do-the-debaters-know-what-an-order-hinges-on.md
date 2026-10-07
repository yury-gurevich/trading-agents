# EXP-019 — Do the two debaters know what an order hinges on, and does telling them the score arithmetic make them know it?

**Status:** PRE-REGISTERED 2026-10-06 (`3a33716c`) · **RUN INTERRUPTED 2026-10-06** after 31 of the 52
planned calls ($3.91): the Anthropic account ran out of credit. Interim numbers are in Appendix R. No
verdict yet; sections 6 to 8 wait for the rest of the run, which is not before the account is funded
again (the operator, 2026-10-06: no funds until Sunday 2026-10-11; [DL-265](../../design-log.md)).
**Decision / origin:** [DL-264](../../design-log.md) and its amendment (the operator, 2026-10-06: *"Can
we make LLM understand and assign 'weights' to the quant values we send them … not only the value, but
general significance of an indicator in relation of other indicators"*) · work-queue **107** · notes in
[rounds-and-weights](../dspy/rounds-and-weights.md).
**Cost:** capped at **$10** (operator, 2026-10-06: *"go ahead"*, on *"OK to spend up to $10 on it?"*).
Estimate $7.70 for 70 calls; no new call starts once $9.00 is recorded.

**Found 2026-10-07 20:37 AEDT, by the builder of
[S255](../../sprints/sprint-255-the-packet-states-the-score-arithmetic.md):** arm B's first line says that inside `quant_metrics` *each key ending in `_score`* is a 0-100 band score. Four such keys are on a 0-1 scale: `technical_score`, `fundamental_score`, `sentiment_score` and `composite_score` (measured over 1,765 recorded recommendations: 20 distinct keys end in `_score`, and these four never exceed 1.0). The planner wrote the sentence and did not check it against the keys. The frozen cases and
Appendix P are not edited: the run so far, and its remainder, measure that text. S255 ships the line with
one clause added that excepts the four keys.

## 1. Why we needed this experiment

The defender and the challenger are the only place a language model touches a decision, and their
turns are what the judge rules on. The operator's question is whether they can weigh one kind of
evidence against another, and whether what they say rests on facts.

Measured without a model call ([rounds-and-weights](../dspy/rounds-and-weights.md)): the analyst's
confidence is arithmetic in code, the packet prints the scores with no weight and no formula, and GILD
on `sched-2026-10-05` cleared its floor only on the sentiment score while the debate argued about
*"an undisclosed mapping"*. Work-queue 107 proposes two builds: the packet states the arithmetic, and
each debater's turn records typed weights. Both change the production prompt, which is gated by
ADR-0010. Building them without this experiment would risk a prompt change that the debaters do not
use, and a typed weight that means nothing. The experiment answers three things first: what the
debaters assume today, whether the arithmetic makes them right, and whether their answer follows a
changed input.

Earlier evidence: R009 found values copied accurately and meanings often wrong; S246's replay found the
defender reading 0 sentiment values in 88 readings; EXP-016 found a stated probability can be confident
and wrong.

## 2. Hypothesis

**The unit.** A *hinge* is defined in code. A pillar (technical, fundamental, sentiment) is a hinge of
an approved order when the order's confidence clears its floor and would not clear it with that
pillar's score at a neutral 0.50, everything else unchanged. Each debater turn answers that question
for each pillar with a probability, so every answer has a truth.

- **H1 (told the arithmetic, the debaters know the hinge).** On the recorded packets with the
  arithmetic added (arm B): at least **49 of 54** answers fall on the right side of 0.5, at least **8 of
  10** true hinges are found, and arm B's Brier score is lower than arm A's with the 95 % interval of
  the paired difference below zero.
- **H2 (the answer follows a changed input).** On the four packets whose relative-strength band is
  moved, in arm B: the answer is right both before and after the change in at least **7 of 8** cases
  where the truth flips, and in at least **14 of 16** where it does not.
- **H0.** Either bar is missed: the arithmetic alone does not make the debaters weigh the evidence
  correctly, and the build in work-queue 107 needs more than a packet change.
- **Arm A has no bar.** It is today's packet. It is not expected to be answerable from the packet,
  which gives one equation for three unknown weights. Its job is to measure what the debaters assume
  today. Reference points: always answering "no" scores a Brier of 0.185, and a constant 5 / 27 scores
  0.151.
- **S (the extension, if the budget allows).** A second run of arm B agrees with the first on the side
  of 0.5 in at least **49 of 54** answers. A weight that changes between runs is not a weight.

**Why these bars.** 90 % is the level at which a reader could rely on a single turn's answer; the
hinge counts are set one or two short of all, to allow one borderline case each. With nine orders the
interval is wide and is reported as it is.

**Described, with no bar:** which kind of evidence each role says its position rests on most (a
probability over six families), whether the argument names the hinge pillar, the parse rate, the
tokens, the latency and the cost.

## 3. Data

- **Source.** The nine debated orders whose `DeliberationRun` stores the packet the roles were given
  (stored since the `s246` deploy): TGT, C, DE, EMR, JNJ (2026-10-01), UNP (2026-10-02), MRK, AMGN and
  GILD (2026-10-05). TGT is from the planner-fired fleet test run of 2026-10-01; the rest are scheduled
  runs. Read from the live graph on 2026-10-06, read-only.
- **Where it lives.** OneDrive `trading-agents-data/exp019/`, never the repo (the packets carry vendor
  fundamentals and headlines). `exp019_packets.json`, sha-256 prefix `7df65c237d3f`, 82,471 bytes;
  `exp019_cases.json`, prefix `c5c04b3e10ff`.
- **Cases.** 13: the nine recorded packets and four changed ones (DE, UNP, MRK, GILD). A changed packet
  moves the analyst's relative-strength band by one step and recomputes every value derived from it
  (`relative_strength`, `rs_score`, `technical_score`, `composite_score`, `confidence`, and the two
  printed `confidence_score`s). The band is chosen by a fixed rule: the nearest band that keeps the
  order approved and changes the set of hinge pillars. Five packets have no such band.
- **Truth.** 27 pillar answers on the recorded packets, of which **5** are hinges (DE technical and
  sentiment, EMR technical, MRK sentiment, GILD sentiment). On the four changed packets the truth flips
  for sentiment in all four (three stop being a hinge, UNP becomes one) and stays for the other eight.
- **Checked at build.** Each case's confidence is reproduced from its own sub-scores and the code's
  weights to four places (13 of 13).
- **Known defects.** Nine orders, all buys, all under the `neutral` regime, all with three pillars
  present. Five of the 27 truths are within 0.003 of the floor and are also reported apart. The
  challenger reads the defender's turn, so the two roles' answers are not independent.

## 4. Tools and setup

- **Machine:** Intel Core i7-7660U (2 cores / 4 threads, 2.5 GHz), 15.9 GB RAM, Windows 10 Pro 19045.
- **Python** 3.13.2 through **uv** 0.8.14; **dspy** 3.4.0 and **anthropic** 0.120.2, both at the
  lock's versions, in a worktree pinned at `3391df9d` and synced with the `llm` and `optimizer` extras.
- **Model:** `claude-opus-5`, `effort=high`, `max_tokens` 8,192, through the kernel's own Anthropic
  client: the model, effort and ceiling the three deployed deliberators run. No temperature is sent, as
  in production. The model's own thinking is not requested or recorded.
- **Format:** DSPy's `ChainOfThought` with S246's `GuidedReasoning`, then three `Noul` outputs, one
  `Choice` and the argument, rendered and parsed by DSPy's own `ChatAdapter`. This differs from the
  runtime in one way: DSPy repairs malformed JSON before parsing, where the runtime refuses it.
- **Seeds:** the interval's resampling `20261006` (10,000 resamples, by order). The model has none.
- **Concurrency:** 4 units at a time, 3 attempts on a transport failure.
- **Cost cap:** $10. Prices from `orchestration/packs/llm_pricing.json` ($5 and $25 per million input
  and output tokens, cache read 0.1×, cache write 1.25×), applied to the vendor's own usage block.

## 5. How it was conducted

1. Froze the nine recorded propositions, built the 13 cases and their truth in code, and checked each
   case's arithmetic.
2. Ran all three phases with a canned model answer, at no cost, to prove the rendering, the parsing,
   the ledger and the scorer end to end.
3. Committed this pre-registration and the three scripts before any paid call.
4. **Phase 1:** the nine recorded packets, in arm A (the packet as recorded) and arm B (the packet plus
   the arithmetic block). For each: the defender's first turn, then the challenger's first turn on the
   defender's rendered readings, gaps and argument. The defender's typed answers are not shown to the
   challenger. 36 calls.
5. **Phase 2:** the four changed packets, both arms, the same way. 16 calls.
6. **Phase 3, the extension:** arm B on the nine recorded packets a second time, started only if no
   more than $7.50 is recorded after phase 2. 18 calls.
7. Scored with `exp019_score.py`. Nothing in the design changes after the first paid answer is seen.

## 6. Results

Not run.

## 7. Conclusions

Not run.

## 8. Recommended code changes, and how to implement them

Not run.

## Appendix P — Pre-registration (frozen)

Committed before any paid call; the commit is named in the status line once the run is recorded.

**Question.** For an order the pipeline approved, does a debater know which pillar of the analyst's
score the approval hinges on, today and when the packet states the arithmetic, and does its answer
follow when one input is changed?

**Truth, from code.** With the analyst's settings at `3391df9d`: technical = 0.80 × mean(technical
sub-scores) / 100 + 0.20 × `rs_score` / 100; fundamental = mean(fundamental sub-scores) / 100;
composite = (0.50 × technical + 0.30 × fundamental + 0.20 × sentiment) ÷ the weights present;
confidence = 0.30 + 0.60 × composite. A pillar is a **hinge** when confidence ≥ the floor and
confidence with that pillar at 0.50 < the floor. A truth within 0.003 of the floor is **borderline**.

**Cases.** The nine recorded packets and the four changed ones named in section 3, as written to
`exp019_cases.json` (prefix `c5c04b3e10ff`) by `exp019_build.py`.

**Arms.** A: the recorded packet. B: the packet followed by three lines: the score arithmetic as a
rule for every order, the same arithmetic with this order's numbers (sub-score means, pillar scores,
contributions, composite, confidence, floor, margin), and the regime rule (the VIX selects a label
that is printed and changes no number). **The block never says which pillar is a hinge.**

**Roles and calls.** Defender round 1, then challenger round 1 on the defender's rendered turn, with
the production role prompts as the signature's instructions. `claude-opus-5`, `effort=high`,
`max_tokens` 8,192.

**Outputs, in order.** `reasoning` (S246's readings and gaps); `hinge_technical`, `hinge_fundamental`,
`hinge_sentiment` (each a `Noul`: *would this order have missed its confidence floor if that pillar's
score had been a neutral 0.50, with every other value as the packet gives it?*); `decisive` (a `Choice`
over technical, fundamental, sentiment, regime, bracket, book: *the one kind of evidence your position
on this order rests on most*); `argument`.

**Scoring.**

- An answer is *right* when its probability is on the truth's side of 0.5. Brier = mean (p − truth)².
- **H1:** arm B right in ≥ 49 of 54 and ≥ 8 of 10 true hinges found, and Brier(B) − Brier(A) with a
  95 % interval below zero (paired by order, pillar and role; resampled by order, 10,000 resamples,
  seed `20261006`).
- **H2:** arm B right before and after in ≥ 7 of 8 flips and ≥ 14 of 16 unchanged.
- **S:** the two runs of arm B on the same side of 0.5 in ≥ 49 of 54.
- **Described, no bar:** arm A on every measure; the mean `decisive` probabilities by arm and role, and
  the probability placed on the hinge pillar for orders that have one; whether the argument names the
  hinge pillar's evidence (a word match, an upper bound); parse rate, tokens, latency, cost.

**Failure handling.** A transport failure is retried, up to 3 attempts. A completion stopped at
`max_tokens` or refused is billed, final and unread. An unread turn's answers count as wrong in the
"right of N" counts and are left out of the Brier score. If more than 2 of an arm's 18 phase-1 turns
are unread, that arm's result is INSUFFICIENT. If the defender's call fails outright, the challenger
is not asked.

**Order and budget.** Phase 1, then phase 2, then phase 3 only if the recorded spend is at most $7.50.
No new call starts once $9.00 is recorded. The cap is $10.

**Not changed after the first paid answer:** the cases, the block, the questions, the bars, the scorer.
A defect in the scripts that stops the run is fixed, named in Appendix R, and the affected calls are
re-run; nothing else is.

**Scripts, frozen** (sha-256 prefixes): `exp019_build.py` `8fb1af697cd8`, `exp019_run.py`
`9c46a720f967`, `exp019_score.py` `de5d55d72d33`.

## Appendix R — Run record

**Run 2026-10-06, interrupted.** Planner, from the worktree pinned at `3391df9d`, key from the main
checkout's `.env`. Pre-registered at `3a33716c` (22:59 AEDT), before the first paid call.

**What ran.** Phase 1 only, and not all of it: **31 of its 36 calls** were answered, for **$3.91**
(283,152 input tokens of all kinds and 117,021 output tokens; 2,504 to 6,228 output tokens a call; the
slowest call 76 s; 0 `max_tokens` stops). 30 turns were read. One was not: DE's challenger in arm A
wrote its reasoning and its typed answers and no `argument`, the failure S246's replay saw once in 20.

**Why it stopped.** At about 23:10 AEDT the vendor refused four calls, three attempts each, with
*"Your credit balance is too low to access the Anthropic API"*: GILD's defender in arm B (so its
challenger was never asked), and the challengers of AMGN (both arms) and GILD (arm A). No answer was
produced, seen or billed for any of them. They were moved out of the ledger into
`exp019_refused.jsonl`, so the runner makes those calls when it is next run; the ledger as it stood is
kept as `exp019_calls.before-quarantine.jsonl`. 🩹 **A deviation from "three attempts, then unread":**
a refused call is a run that was stopped, not a turn that could not be read.

**The fleet shares the key.** The fleet's `anthropic-api-key` in Key Vault and the planner's key are the
same key (compared by hash; neither was printed). The empty account is the fleet's too.

**The estimate was wrong.** A call cost **$0.126** on average against the $0.11 assumed from S246's
replay: the turns write more. At the measured rate phases 1 and 2 cost about $6.70; the extension would
then start, and the $9.00 stop would cut it short.

**How the calls were driven.** The first unit was run alone to prove the parse on a real answer; then
phase 1 in two slices of nine units. Each went through the frozen runner's own `unit()` and ledger,
with the ids and order of `--phase 1`, so that one tool call stayed inside its time limit. The frozen
scripts were not edited.

**Interim numbers, not a verdict** (`exp019_score.py` on the partial ledger, sha-256 prefix
`20e5d6053784`). Phase 2 has not run, and five phase-1 turns are missing.

| | Arm A, today's packet | Arm B, with the arithmetic |
| --- | --- | --- |
| Turns answered and read, of 18 | 15 | 15 |
| Answers right, of the 45 given | 34 | 45 |
| Wrong answers | 11, all false alarms | 0 |
| True hinges found, of those asked | 7 of 7 | 8 of 8 |
| Probabilities between 0.2 and 0.8 | 10 of 45 | 0 of 45 |
| Brier score (always "no" scores 0.185) | 0.190 | 0.002 |
| Weight placed on the hinge pillar, orders that have one | 0.39 | 0.68 |

- Paired Brier difference, B − A, over the 42 answers both arms gave: −0.188 [−0.249, −0.111].
- **Today's debaters over-attribute.** Every arm-A error names a pillar as decisive that is not.
- One arm-A defender (GILD) worked the weights out by itself (*"a composite that reproduces exactly as
  0.5*technical + 0.3*fundamental + 0.2*sentiment"*) and still called the technical pillar a hinge.
- The word-match check on arguments is saturated in both arms (7 of 7, 7 of 8) and tells nothing.
- **One arm-B turn, read in full: MRK's challenger.** It wrote that *"by the packet's own arithmetic
  only sentiment is load-bearing"* (neutral sentiment gives 0.5918, below the floor), then that the
  score's positive words come from headlines about a rival. *[checked against the packet]* 7 of MRK's
  20 headlines are about Vaxcyte's pneumococcal vaccine trial, two of them *"Takes Aim at Pfizer and
  Merck"*. The recorded live debate of 2026-10-05 ruled `revise` on the `reward_risk` gate and never
  raised it.

**To finish:** 5 calls of phase 1 and the 16 of phase 2, about $2.80 at the measured rate; then the
extension if the frozen rule allows it.

### Reproducing

From a checkout at `3391df9d` synced with `uv sync --locked --extra llm --extra optimizer`, with the
scripts and `exp019_packets.json` in `<dir>`:
`PYTHONPATH=. uv run --no-sync python <dir>/exp019_build.py <dir>`, then
`PYTHONPATH=. uv run --no-sync --env-file <main>/.env python <dir>/exp019_run.py <dir> --phase 1`
(then `2`, then `3`; `--fake` costs nothing), then `uv run --no-sync python <dir>/exp019_score.py <dir>`.
The model's answers are its own and will differ between runs.

## Appendix S — Scripts

### `exp019_build.py`

```python
"""EXP-019 build ($0): the cases, the arithmetic block, the changed packets and the truth.

Run from a checkout of the repo (it imports the analyst's and provider's own settings
and the relative-strength band rule):
  PYTHONPATH=. uv run --no-sync python <dir>/exp019_build.py <dir>
Reads <dir>/exp019_packets.json (the recorded propositions) and writes
<dir>/exp019_cases.json. Makes no network call.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

from agents.analyst.domain.relative_strength import score_relative_strength
from agents.analyst.settings import AnalystSettings
from agents.provider.settings import ProviderSettings

A, P = AnalystSettings(), ProviderSettings()
W = {"technical": A.technical_weight, "fundamental": A.fundamental_weight, "sentiment": A.sentiment_weight}
FUND = ("pe", "roe", "net_margin", "current_ratio", "pb", "debt_equity", "eps_growth", "revenue_growth")
NOT_TECH = {"rs_score", "technical_score", "fundamental_score", "sentiment_score", "composite_score", "alpha158_score"}
BANDS = {20.0: -7.5, 40.0: -2.5, 60.0: 2.5, 80.0: 7.5}  # band score -> a raw spread in the middle of the band
assert all(score_relative_strength(raw) == band for band, raw in BANDS.items())
BORDERLINE = 0.003


def g4(value: float) -> str:
    return f"{value:.4g}"


def analyst_line(context: str) -> str:
    return next(line for line in context.split("\n") if line.startswith("Analyst recommendation for "))


def quant(context: str) -> dict[str, float]:
    body = analyst_line(context).split("quant_metrics=source-owned-units-scope-unknown{", 1)[1].split("}", 1)[0]
    return {k: float(v) for k, v in (item.split("=", 1) for item in body.split(", "))}


def read(context: str) -> dict:
    q = quant(context)
    tech_subs = {k: v for k, v in q.items() if k.endswith("_score") and k not in NOT_TECH}
    assert len(tech_subs) == int(q["indicators_available"]), (len(tech_subs), q["indicators_available"])
    fund_subs = {k: q[k] for k in FUND if k in q}
    assert not fund_subs or len(fund_subs) == int(q["fundamentals_available"])
    technical = (1 - A.relative_strength_weight) * sum(tech_subs.values()) / len(tech_subs) / 100
    technical += A.relative_strength_weight * q["rs_score"] / 100
    pillars = {
        "technical": technical,
        "fundamental": sum(fund_subs.values()) / len(fund_subs) / 100 if fund_subs else None,
        "sentiment": q.get("sentiment_score"),
    }
    floor = float(re.search(r"base_min_confidence_score=([0-9.]+)", context).group(1))
    return {"q": q, "tech_subs": tech_subs, "fund_subs": fund_subs, "pillars": pillars, "floor": floor}


def confidence(pillars: dict) -> tuple[float, float]:
    present = {k: v for k, v in pillars.items() if v is not None}
    composite = sum(W[k] * v for k, v in present.items()) / sum(W[k] for k in present)
    return composite, A.confidence_floor + A.confidence_span * composite


def truth(pillars: dict, floor: float) -> dict:
    """A pillar is a hinge when the order clears its floor and would not with that pillar at 0.50."""
    actual = confidence(pillars)[1]
    assert actual >= floor
    out = {}
    for name, value in pillars.items():
        if value is None:
            continue
        neutral = confidence({**pillars, name: 0.5})[1]
        out[name] = {"hinge": neutral < floor, "neutral_confidence": round(neutral, 5),
                     "borderline": abs(neutral - floor) < BORDERLINE}
    return out


def block(ticker: str, parsed: dict) -> str:
    """The arithmetic block of arm B: the rule for every order, then this order's numbers."""
    p, q = parsed["pillars"], parsed["q"]
    composite, conf = confidence(p)
    present = {k: v for k, v in p.items() if v is not None}
    total = sum(W[k] for k in present)
    rsw = A.relative_strength_weight
    rule = (
        "Score arithmetic, the rule for every order (definitions from the analyst's code, the same for every "
        "reviewer): inside quant_metrics each key ending in _score, and each fundamental sub-score, is a 0-100 band "
        f"score in which 50 is neutral; technical_score = {1 - rsw:.2f} x (mean of the technical sub-scores / 100) + "
        f"{rsw:.2f} x (rs_score / 100); fundamental_score = (mean of the fundamental sub-scores) / 100; "
        f"composite_score = {W['technical']:.2f} x technical_score + {W['fundamental']:.2f} x fundamental_score + "
        f"{W['sentiment']:.2f} x sentiment_score, divided by the sum of the weights of the pillars that are present; "
        f"confidence = {A.confidence_floor:.2f} + {A.confidence_span:.2f} x composite_score; a pillar score of 0.50 "
        "is neutral; an order is recommended only if confidence >= base_min_confidence_score."
    )
    subs = ", ".join(f"{k}={v:g}" for k, v in parsed["fund_subs"].items())
    parts = [
        f"technical sub-scores ({len(parsed['tech_subs'])}): mean {sum(parsed['tech_subs'].values()) / len(parsed['tech_subs']):.2f}",
        f"rs_score={q['rs_score']:g}",
        f"technical_score={p['technical']:.4f}",
    ]
    if p["fundamental"] is not None:
        parts += [f"fundamental sub-scores ({len(parsed['fund_subs'])}): {subs}", f"fundamental_score={p['fundamental']:.4f}"]
    if p["sentiment"] is not None:
        parts.append(f"sentiment_score={p['sentiment']:.4f}")
    shares = ", ".join(f"{k} {W[k] * v / total:.4f}" for k, v in present.items())
    parts += [
        f"contributions to composite_score: {shares}",
        f"composite_score={composite:.4f}",
        f"confidence={conf:.4f}",
        f"base_min_confidence_score={parsed['floor']:.3f}",
        f"margin over the floor={conf - parsed['floor']:+.4f}",
    ]
    regime = (
        "Regime, the rule for every order: vix_index only selects the regime label (risk_on at or below "
        f"{P.vix_risk_on_threshold:g}, risk_off from {P.vix_risk_off_threshold:g}, high_volatility from "
        f"{P.vix_high_threshold:g}, extreme_volatility from {P.vix_extreme_threshold:g}, neutral otherwise). The label "
        "is printed and changes no number: base_min_confidence_score, base_stop_loss_pct, base_take_profit_pct and "
        "base_max_holding_days are the same constants under every label, and the VIX is not an input to any score."
    )
    return "\n".join((rule, f"Score arithmetic for {ticker}: " + "; ".join(parts) + ".", regime))


def moved(context: str, parsed: dict, band: float) -> str:
    """The packet with the relative-strength band moved and every value derived from it recomputed."""
    q, p = parsed["q"], parsed["pillars"]
    technical = p["technical"] + A.relative_strength_weight * (band - q["rs_score"]) / 100
    composite, conf = confidence({**p, "technical": technical})
    line = analyst_line(context)
    new = line
    for old, repl in (
        (f"technical_score={p['technical']:.3f};", f"technical_score={technical:.3f};"),
        (f"confidence_score={confidence(p)[1]:.3f};", f"confidence_score={conf:.3f};"),
        (f"relative_strength={g4(q['relative_strength'])},", f"relative_strength={g4(BANDS[band])},"),
        (f"rs_score={g4(q['rs_score'])},", f"rs_score={g4(band)},"),
        (f"technical_score={g4(q['technical_score'])},", f"technical_score={g4(technical)},"),
        (f"composite_score={g4(q['composite_score'])},", f"composite_score={g4(composite)},"),
        (f"confidence={g4(q['confidence'])},", f"confidence={g4(conf)},"),
    ):
        assert new.count(old) == 1, (old, new.count(old))
        new = new.replace(old, repl)
    out = context.replace(line, new)
    gate_old = f"confidence_floor gate: enforced_by=analyst; confidence_score={confidence(p)[1]:.3f} vs"
    assert out.count(gate_old) == 1
    return out.replace(gate_old, f"confidence_floor gate: enforced_by=analyst; confidence_score={conf:.3f} vs")


def hinge_set(t: dict) -> tuple[str, ...]:
    return tuple(k for k, v in t.items() if v["hinge"])


def main() -> None:
    folder = Path(sys.argv[1])
    packets = json.loads((folder / "exp019_packets.json").read_text(encoding="utf-8"))
    cases = []
    for pk in packets:
        parsed = read(pk["context"])
        composite, conf = confidence(parsed["pillars"])
        assert abs(conf - parsed["q"]["confidence"]) < 0.0006, (pk["ticker"], conf, parsed["q"]["confidence"])
        t = truth(parsed["pillars"], parsed["floor"])
        base = {"ticker": pk["ticker"], "day": pk["day"], "decision": pk["decision"]}
        cases.append({**base, "case": f"{pk['ticker']}|recorded", "variant": "recorded", "context": pk["context"],
                      "block": block(pk["ticker"], parsed), "truth": t, "confidence": round(conf, 5),
                      "rs_band": parsed["q"]["rs_score"]})
        # the changed packet: the nearest band (fewest steps, ties upward) that keeps the order
        # approved and changes the set of hinge pillars; none if no band does
        current = parsed["q"]["rs_score"]
        for band in sorted(BANDS, key=lambda b: (abs(b - current), -b)):
            if band == current:
                continue
            tech2 = parsed["pillars"]["technical"] + A.relative_strength_weight * (band - current) / 100
            pillars2 = {**parsed["pillars"], "technical": tech2}
            if confidence(pillars2)[1] < parsed["floor"]:
                continue
            if hinge_set(truth(pillars2, parsed["floor"])) == hinge_set(t):
                continue
            context2 = moved(pk["context"], parsed, band)
            again = read(context2)
            conf2 = confidence(again["pillars"])[1]
            assert abs(conf2 - again["q"]["confidence"]) < 0.0006 and abs(conf2 - confidence(pillars2)[1]) < 1e-9
            t2 = truth(again["pillars"], again["floor"])
            cases.append({**base, "case": f"{pk['ticker']}|changed", "variant": "changed", "context": context2,
                          "block": block(pk["ticker"], again), "truth": t2, "confidence": round(conf2, 5),
                          "rs_band": band})
            break
    out = folder / "exp019_cases.json"
    out.write_text(json.dumps(cases, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    for c in cases:
        hinges = "+".join(hinge_set(c["truth"])) or "none"
        edge = [k for k, v in c["truth"].items() if v["borderline"]]
        print(f"{c['case']:16} conf {c['confidence']:.4f} rs_band {c['rs_band']:g} hinges {hinges:22} borderline {edge}")
    print("cases", len(cases), "| sha256", hashlib.sha256(out.read_bytes()).hexdigest()[:12])


if __name__ == "__main__":
    main()
```

### `exp019_run.py`

```python
"""EXP-019 run: the two debaters' first turns, with typed hinge answers and weights.

Run from a checkout of the repo whose environment has the `llm` and `optimizer` extras:
  PYTHONPATH=. uv run --no-sync --env-file <main>/.env python <dir>/exp019_run.py <dir> --phase 1
  ... --phase 2, then --phase 3 (the pre-registered extension); add --fake for a no-cost dry run.
Resumable: a call already in <dir>/exp019_calls.jsonl is never made again. No new call is
started once the recorded spend reaches STOP_USD. Writes nothing to the graph.
"""

from __future__ import annotations

import argparse
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import dspy
from dspy.adapters.decision import resolve_adapter
from dspy.experimental import Choice, Noul

from kernel.deliberation import CHALLENGER_SYSTEM, DEFENDER_SYSTEM, Turn
from kernel.deliberation_guided import GuidedReasoning, render_guided_text, render_transcript
from kernel.llm import LLMCompletionStoppedError, llm_stop_reason
from kernel.llm_factory import build_llm
from kernel.llm_tokens import llm_usage

MODEL, EFFORT, MAX_TOKENS = "claude-opus-5", "high", 8192
STOP_USD, EXTENSION_USD, WORKERS, ATTEMPTS = 9.00, 7.50, 4, 3
PILLARS = ("technical", "fundamental", "sentiment")
ROLE_PROMPT = {"defender": DEFENDER_SYSTEM, "challenger": CHALLENGER_SYSTEM}

Hinge = Noul[
    (True, "with that pillar's score at 0.50 the confidence is below base_min_confidence_score"),
    (False, "with that pillar's score at 0.50 the confidence is still at or above base_min_confidence_score"),
]
Family = Choice[
    ("technical", "the technical pillar: the indicators and relative strength"),
    ("fundamental", "the fundamental pillar"),
    ("sentiment", "the sentiment pillar: the news and its score"),
    ("regime", "the regime: the VIX and its label"),
    ("bracket", "the stop, the target and their ratio"),
    ("book", "the portfolio gates: sizing, sector, cluster, cash, positions"),
]


def _hinge(pillar: str) -> str:
    return (
        f"step 3: would this order have missed its confidence floor if its {pillar}_score had been a neutral "
        "0.50, with every other value as the packet gives it?"
    )


class DebateTurn(dspy.Signature):
    decision: str = dspy.InputField(desc="the decision under test")
    context: str = dspy.InputField(desc="the evidence packet for this decision; every value you read comes from here")
    transcript: str = dspy.InputField(desc="the debate so far")
    hinge_technical: Hinge = dspy.OutputField(desc=_hinge("technical"))
    hinge_fundamental: Hinge = dspy.OutputField(desc=_hinge("fundamental"))
    hinge_sentiment: Hinge = dspy.OutputField(desc=_hinge("sentiment"))
    decisive: Family = dspy.OutputField(desc="step 4: the one kind of evidence your position on this order rests on most")
    argument: str = dspy.OutputField(
        desc="step 5: your turn, at most ~5 sentences, built only from your readings, your gaps and your answers above"
    )


ADAPTER = dspy.ChatAdapter()
SIGNATURE = {
    role: dspy.ChainOfThought(DebateTurn.with_instructions(prompt), rationale_field_type=GuidedReasoning).predict.signature
    for role, prompt in ROLE_PROMPT.items()
}
DECISION = {role: resolve_adapter(object(), ADAPTER, sig, {}) for role, sig in SIGNATURE.items()}
_PRICING = json.loads(Path("orchestration/packs/llm_pricing.json").read_text(encoding="utf-8"))
_RATE, _CACHE = _PRICING["models"][MODEL], _PRICING["cache_multipliers"]


def render(role: str, inputs: dict[str, str]) -> tuple[object, str, str]:
    request = DECISION[role]._prepare(SIGNATURE[role], [], inputs, {})
    messages = ADAPTER.format(request["signature"], [], inputs)
    assert [m["role"] for m in messages] == ["system", "user"]
    return request["signature"], messages[0]["content"], messages[1]["content"]


def parse(role: str, signature: object, completion: str) -> dict:
    out = DECISION[role]._decode([ADAPTER.parse(signature, completion)])[0]
    return {
        "hinge": {p: out[f"hinge_{p}"].probability for p in PILLARS},
        "decisive": {"value": out["decisive"].value, "probabilities": out["decisive"].probabilities,
                     "confidence": out["decisive"].confidence},
        "argument": out["argument"],
        "reasoning": out["reasoning"].model_dump(mode="json"),
        "turn_text": render_guided_text(out["reasoning"], out["argument"]),
    }


def cost_usd(usage: object | None) -> float:
    if usage is None:
        return 0.0
    tokens = usage.tokens_in + usage.cache_read_tokens * _CACHE["read"] + usage.cache_write_tokens * _CACHE["write"]
    return (tokens * _RATE["input"] + usage.tokens_out * _RATE["output"]) / 1e6


class FakeLLM:
    """A canned, well-formed completion: the dry run costs nothing."""

    last_usage, last_stop_reason = None, "end_turn"

    def complete(self, *, system: str, user: str, tool_schema: dict) -> str:
        reasoning = {"readings": [{"metric": "sentiment_score", "value": "0.75", "meaning_here": "fake", "bears_on": "supports"}], "gaps": []}
        choice = {"probabilities": dict.fromkeys(("technical", "fundamental", "regime", "bracket", "book"), 0.1) | {"sentiment": 0.5}, "confidence": 0.5}
        parts = [("reasoning", json.dumps(reasoning)), ("hinge_technical", '{"noul": 0.2}'), ("hinge_fundamental", '{"noul": 0.1}'),
                 ("hinge_sentiment", '{"noul": 0.9}'), ("decisive", json.dumps(choice)), ("argument", "A fake argument.")]
        return "\n\n".join(f"[[ ## {name} ## ]]\n{value}" for name, value in parts) + "\n\n[[ ## completed ## ]]"


class Ledger:
    def __init__(self, path: Path) -> None:
        self.path, self.lock, self.rows = path, threading.Lock(), {}
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                row = json.loads(line)
                self.rows[row["id"]] = row

    @property
    def spent(self) -> float:
        return sum(row["cost_usd"] for row in self.rows.values())

    def add(self, row: dict) -> None:
        with self.lock:
            self.rows[row["id"]] = row
            with self.path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def call(ledger: Ledger, fake: bool, ident: str, role: str, inputs: dict[str, str], meta: dict) -> dict | None:
    if ident in ledger.rows:
        return ledger.rows[ident]
    with ledger.lock:
        if ledger.spent >= STOP_USD:
            return None
    signature, system, user = render(role, inputs)
    prompts = ledger.path.with_name(ledger.path.stem + "_prompts.jsonl")
    with ledger.lock, prompts.open("a", encoding="utf-8", newline="\n") as log:
        log.write(json.dumps({"id": ident, "system": system, "user": user}, ensure_ascii=False) + "\n")
    row = {"id": ident, **meta, "role": role, "model": MODEL, "effort": EFFORT, "completion": None, "parsed": None,
           "error": None, "stop_reason": None, "usage": None, "cost_usd": 0.0, "attempts": 0,
           "system_chars": len(system), "user_chars": len(user)}
    started = time.monotonic()
    for attempt in range(1, ATTEMPTS + 1):
        row["attempts"] = attempt
        llm = FakeLLM() if fake else build_llm("anthropic", api_key=os.environ.get("ANTHROPIC_API_KEY"), model=MODEL,
                                               max_tokens=MAX_TOKENS, effort=EFFORT)
        try:
            row["completion"] = llm.complete(system=system, user=user, tool_schema={})
            row["stop_reason"] = llm_stop_reason(llm)
        except LLMCompletionStoppedError as exc:  # billed and final: no retry
            row["stop_reason"], row["error"] = exc.stop_reason, f"stopped: {exc.stop_reason}"
        except Exception as exc:  # a transport failure costs nothing; try again
            row["error"] = f"{type(exc).__name__}: {exc}"[:300]
            time.sleep(5 * attempt)
            continue
        usage = llm_usage(llm)
        if usage is not None:
            row["usage"] = {"in": usage.tokens_in, "out": usage.tokens_out, "cache_read": usage.cache_read_tokens,
                            "cache_write": usage.cache_write_tokens}
            row["cost_usd"] = cost_usd(usage)
        break
    row["latency_s"] = round(time.monotonic() - started, 1)
    if row["completion"]:
        try:
            row["parsed"], row["error"] = parse(role, signature, row["completion"]), None
        except Exception as exc:  # an unreadable turn is a result, not a crash
            row["error"] = f"unparsed: {type(exc).__name__}: {exc}"[:300]
    ledger.add(row)
    return row


def unit(ledger: Ledger, fake: bool, phase: int, case: dict, arm: str, rep: int) -> None:
    context = case["context"] if arm == "A" else case["context"] + "\n" + case["block"]
    meta = {"phase": phase, "case": case["case"], "ticker": case["ticker"], "variant": case["variant"], "arm": arm, "rep": rep}
    base = f"{case['case']}:{arm}:r{rep}"
    inputs = {"decision": case["decision"], "context": context, "transcript": render_transcript(())}
    defender = call(ledger, fake, f"{base}:defender", "defender", inputs, meta)
    if defender is None or not defender["completion"]:
        return  # the cap was reached, or the defender's call failed: the challenger is not asked
    text = defender["parsed"]["turn_text"] if defender["parsed"] else defender["completion"].strip()
    inputs = {**inputs, "transcript": render_transcript((Turn("defender", 1, text),))}
    call(ledger, fake, f"{base}:challenger", "challenger", inputs, meta)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("folder")
    parser.add_argument("--phase", type=int, required=True, choices=(1, 2, 3))
    parser.add_argument("--fake", action="store_true")
    args = parser.parse_args()
    folder = Path(args.folder)
    cases = json.loads((folder / "exp019_cases.json").read_text(encoding="utf-8"))
    ledger = Ledger(folder / ("exp019_calls_fake.jsonl" if args.fake else "exp019_calls.jsonl"))
    variant = "changed" if args.phase == 2 else "recorded"
    arms, rep = (("B",), 2) if args.phase == 3 else (("A", "B"), 1)
    if args.phase == 3 and ledger.spent > EXTENSION_USD:
        print(f"extension not started: ${ledger.spent:.2f} already spent, above ${EXTENSION_USD:.2f}")
        return
    todo = [(case, arm) for case in cases if case["variant"] == variant for arm in arms]
    print(f"phase {args.phase}: {len(todo)} units, {2 * len(todo)} calls; spent so far ${ledger.spent:.2f}")
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for future in [pool.submit(unit, ledger, args.fake, args.phase, case, arm, rep) for case, arm in todo]:
            future.result()
    rows = [r for r in ledger.rows.values() if r["phase"] == args.phase]
    parsed = sum(1 for r in rows if r["parsed"])
    print(f"phase {args.phase} done: {len(rows)} calls recorded, {parsed} parsed; total spent ${ledger.spent:.4f}")


if __name__ == "__main__":
    main()
```

### `exp019_score.py`

```python
"""EXP-019 score: the pre-registered measures, from the cases and the recorded calls. $0.

  uv run --no-sync python <dir>/exp019_score.py <dir> [exp019_calls_fake]
"""

from __future__ import annotations

import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

PILLARS = ("technical", "fundamental", "sentiment")
ROLES = ("defender", "challenger")
SEED, RESAMPLES = 20261006, 10_000
TALK = {
    "sentiment": re.compile(r"sentiment|news|headline", re.I),
    "fundamental": re.compile(r"fundamental|netProfitMargin|roe|debt|margin|\bpb|revenue|current_?ratio|eps", re.I),
    "technical": re.compile(r"technical|rsi|macd|bollinger|stochastic|williams|ema_spread|sma_distance|obv|golden_cross|choppiness|relative.strength|rs_score", re.I),
}

folder = Path(sys.argv[1])
stem = sys.argv[2] if len(sys.argv) > 2 else "exp019_calls"
cases = {c["case"]: c for c in json.loads((folder / "exp019_cases.json").read_text(encoding="utf-8"))}
rows = [json.loads(line) for line in (folder / f"{stem}.jsonl").read_text(encoding="utf-8").splitlines()]
by = {(r["case"], r["arm"], r["rep"], r["role"]): r for r in rows}
tickers = sorted({c["ticker"] for c in cases.values()})


def prob(case: str, arm: str, rep: int, role: str, pillar: str) -> float | None:
    row = by.get((case, arm, rep, role))
    return row["parsed"]["hinge"][pillar] if row and row["parsed"] else None


def judgements(variant: str, arm: str, rep: int = 1) -> list[dict]:
    out = []
    for case in cases.values():
        if case["variant"] != variant:
            continue
        for role in ROLES:
            for pillar, t in case["truth"].items():
                out.append({"ticker": case["ticker"], "role": role, "pillar": pillar, "truth": t["hinge"],
                            "borderline": t["borderline"], "p": prob(case["case"], arm, rep, role, pillar)})
    return out


def right(j: dict) -> bool:
    return j["p"] is not None and (j["p"] >= 0.5) == j["truth"]


def brier(js: list[dict]) -> float | None:
    scored = [j for j in js if j["p"] is not None]
    return sum((j["p"] - j["truth"]) ** 2 for j in scored) / len(scored) if scored else None


def line(label: str, js: list[dict]) -> str:
    hinges = [j for j in js if j["truth"]]
    b = brier(js)
    return (f"{label}: right {sum(map(right, js))} of {len(js)}; true hinges found {sum(map(right, hinges))} of {len(hinges)}; "
            f"unread {sum(j['p'] is None for j in js)}; Brier {'n/a' if b is None else f'{b:.4f}'}")


print("== operations")
for phase in sorted({r["phase"] for r in rows}):
    ph = [r for r in rows if r["phase"] == phase]
    out = [r["usage"]["out"] for r in ph if r["usage"]]
    print(f"phase {phase}: calls {len(ph)}, parsed {sum(1 for r in ph if r['parsed'])}, max_tokens stops "
          f"{sum(1 for r in ph if r['stop_reason'] == 'max_tokens')}, cost ${sum(r['cost_usd'] for r in ph):.4f}, "
          f"output tokens {min(out, default=0)}-{max(out, default=0)}, latency max {max((r.get('latency_s', 0) for r in ph), default=0)} s")
print(f"total cost ${sum(r['cost_usd'] for r in rows):.4f} over {len(rows)} calls")
for r in rows:
    if not r["parsed"]:
        print("  unread:", r["id"], "|", r["error"])

print("\n== P1: does the role know which pillar the order hinges on (recorded packets)")
base = judgements("recorded", "A")
rate = sum(j["truth"] for j in base) / len(base)
print(f"judgements per arm {len(base)}; true hinges {sum(j['truth'] for j in base)}; constant-base-rate Brier {rate * (1 - rate):.4f}; always-no Brier {rate:.4f}")
for arm in ("A", "B"):
    js = judgements("recorded", arm)
    print(line(f"arm {arm}", js))
    for role in ROLES:
        print("   " + line(role, [j for j in js if j["role"] == role]))
    print("   " + line("not borderline", [j for j in js if not j["borderline"]]))
a, b = judgements("recorded", "A"), judgements("recorded", "B")
pairs = [(x, y) for x, y in zip(a, b, strict=True) if x["p"] is not None and y["p"] is not None]
if pairs:
    per = defaultdict(list)
    for x, y in pairs:
        per[x["ticker"]].append((y["p"] - y["truth"]) ** 2 - (x["p"] - x["truth"]) ** 2)
    rng, names, diffs = random.Random(SEED), sorted(per), []
    for _ in range(RESAMPLES):
        pool = [d for name in rng.choices(names, k=len(names)) for d in per[name]]
        diffs.append(sum(pool) / len(pool))
    diffs.sort()
    point = sum(d for ds in per.values() for d in ds) / sum(len(ds) for ds in per.values())
    print(f"Brier B - A (paired, {len(pairs)} judgements, resampled by order): {point:+.4f} "
          f"[{diffs[int(0.025 * RESAMPLES)]:+.4f}, {diffs[int(0.975 * RESAMPLES) - 1]:+.4f}]")

print("\n== P2: does the answer follow a changed input (the four packets with the relative-strength band moved)")
for arm in ("A", "B"):
    flip = stay = flip_ok = stay_ok = 0
    moves = []
    for case in cases.values():
        if case["variant"] != "changed":
            continue
        rec = cases[f"{case['ticker']}|recorded"]
        for role in ROLES:
            for pillar in case["truth"]:
                t0, t1 = rec["truth"][pillar]["hinge"], case["truth"][pillar]["hinge"]
                p0, p1 = prob(rec["case"], arm, 1, role, pillar), prob(case["case"], arm, 1, role, pillar)
                ok = p0 is not None and p1 is not None and (p0 >= 0.5) == t0 and (p1 >= 0.5) == t1
                if t0 != t1:
                    flip, flip_ok = flip + 1, flip_ok + ok
                    moves.append(f"{case['ticker']}/{role[0]}/{pillar[:4]} {p0}->{p1} (truth {int(t0)}->{int(t1)})")
                else:
                    stay, stay_ok = stay + 1, stay_ok + ok
    print(f"arm {arm}: truth flips, right before and after {flip_ok} of {flip}; truth unchanged, right before and after {stay_ok} of {stay}")
    print("   flips: " + "; ".join(moves))

print("\n== D1: what each role says its position rests on most (mean probability, recorded packets)")
families = ("technical", "fundamental", "sentiment", "regime", "bracket", "book")
for arm in ("A", "B"):
    for role in ROLES:
        got = [by[(c, arm, 1, role)]["parsed"]["decisive"] for c in cases if cases[c]["variant"] == "recorded"
               and (c, arm, 1, role) in by and by[(c, arm, 1, role)]["parsed"]]
        if not got:
            continue
        mean = {f: sum(g["probabilities"][f] for g in got) / len(got) for f in families}
        top = defaultdict(int)
        for g in got:
            top[g["value"]] += 1
        print(f"arm {arm} {role:10} n={len(got)} " + " ".join(f"{f} {mean[f]:.2f}" for f in families) + f" | named most: {dict(top)}")
    on_hinge = []
    for case in cases.values():
        hinges = [p for p, t in case["truth"].items() if t["hinge"]]
        if case["variant"] != "recorded" or not hinges:
            continue
        for role in ROLES:
            row = by.get((case["case"], arm, 1, role))
            if row and row["parsed"]:
                on_hinge.append(sum(row["parsed"]["decisive"]["probabilities"][h] for h in hinges))
    if on_hinge:
        print(f"arm {arm}: orders with a hinge, mean probability placed on the hinge pillar(s): {sum(on_hinge) / len(on_hinge):.2f} (n={len(on_hinge)})")

print("\n== D2: does the argument name the hinge pillar's evidence (word match, an upper bound)")
for arm in ("A", "B"):
    n = hit = 0
    for case in cases.values():
        if case["variant"] != "recorded":
            continue
        for pillar, t in case["truth"].items():
            if not t["hinge"]:
                continue
            for role in ROLES:
                row = by.get((case["case"], arm, 1, role))
                if row and row["parsed"]:
                    n, hit = n + 1, hit + bool(TALK[pillar].search(row["parsed"]["argument"]))
    print(f"arm {arm}: {hit} of {n} arguments name the hinge pillar")

if any(r["rep"] == 2 for r in rows):
    print("\n== S: does a second run of arm B agree with the first (recorded packets)")
    one, two = judgements("recorded", "B", 1), judgements("recorded", "B", 2)
    both = [(x, y) for x, y in zip(one, two, strict=True) if x["p"] is not None and y["p"] is not None]
    same = sum((x["p"] >= 0.5) == (y["p"] >= 0.5) for x, y in both)
    gap = sum(abs(x["p"] - y["p"]) for x, y in both) / len(both) if both else 0.0
    tops = [(by[(c, "B", 1, r)]["parsed"]["decisive"]["value"], by[(c, "B", 2, r)]["parsed"]["decisive"]["value"])
            for c in cases for r in ROLES if cases[c]["variant"] == "recorded"
            and all((c, "B", k, r) in by and by[(c, "B", k, r)]["parsed"] for k in (1, 2))]
    print(f"same side of 0.5 in {same} of {len(both)} judgements; mean |difference| {gap:.3f}; "
          f"same most-important family in {sum(x == y for x, y in tops)} of {len(tops)} turns")
    print("   " + line("second run", two))
```
