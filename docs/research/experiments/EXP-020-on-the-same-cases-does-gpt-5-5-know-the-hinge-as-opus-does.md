# EXP-020 — On the same frozen cases, does gpt-5.5 know what an order hinges on as Opus does?

**Status:** COMPLETE 2026-10-07 · **both bars met.** With the arithmetic `gpt-5.5` answers 54 of 54 right and finds 10 of 10 hinges, and it is on Opus's side of 0.5 in 45 of 45 answers both gave. Without it the two vendors guess differently. Pre-registered at `ace8d628`, before any paid call
**Decision / origin:** [DL-264](../../design-log.md) amendment 7 (the operator, 2026-10-07: *"maybe we
should continue testing on OpenAI to get confidence tat if we HAVE TO swap from anthropic to openai again
it will give up comparable results"*) · work-queue **107** · the gate of
[S255](../../sprints/sprint-255-the-packet-states-the-score-arithmetic.md) · **Cost:** capped at **$7.00**
(operator, 2026-10-07: *"yeah, the $7 will be sufficient"*); no new call starts once $6.45 is recorded. **Spent: $6.52** on 31 calls

## 1. Why we needed this experiment

The fleet has debated on `gpt-5.5` since 2026-10-06 because the Anthropic account is empty
([DL-265](../../design-log.md)), and a forced swap can happen again. Every measurement of what the debaters
understand was made on Opus. [EXP-019](EXP-019-do-the-debaters-know-what-an-order-hinges-on.md) asks whether
telling the debaters the score arithmetic makes them know what an order hinges on; it is interrupted at 31 of
52 calls, all on Opus, and S255 ships its arm B text into production behind that verdict. If `gpt-5.5` reads
the same text differently, a gate passed on Opus says nothing about the nights the fleet runs on `gpt-5.5`.

One difference is already measured. On the same order `gpt-5.5`'s defender writes 2.7 times the output Opus
writes and reaches 94 % of the fleet's 8,192-token cap (work-queue 111). How often a turn would be cut is
*[ASSUMED]* in that item: two turns are all that is measured.

## 2. Hypothesis

**The unit** is EXP-019's: a pillar is a hinge of an approved order when the order's confidence clears its
floor and would not with that pillar's score at a neutral 0.50. Each debater turn answers that question for
each pillar with a probability. The nine recorded orders hold 27 such questions, 5 of them true, so each arm
has 54 answers across the two roles and 10 true hinges.

- **C1 (told the arithmetic, `gpt-5.5` knows the hinge).** EXP-019's H1 bars, applied to `gpt-5.5`'s arm B:
  at least **49 of 54** answers on the right side of 0.5, and at least **8 of 10** true hinges found. An answer
  that was not asked, not read, or cut off counts as wrong.
- **C2 (the two vendors agree).** On the arm B answers both vendors gave for the same order, role and pillar,
  the two fall on the same side of 0.5 in at least **90 %**: at least 41 of the 45 Opus has given so far. It is
  recounted when Opus's run completes, against the same 90 %.
- **C0.** Either bar is missed: on this task the vendors are not interchangeable, and S255's gate cannot rest
  on one vendor's result.

**Why these bars.** C1 uses EXP-019's own bars so that both vendors are judged by one rule. 90 % is the level
EXP-019 set for relying on a single turn's answer.

**Described, with no bar:** arm A (today's packet) on every measure, as far as the budget reaches; the Brier
difference between the arms on the orders asked in both; the number of turns that write more than 8,192
output tokens, each of which the fleet's cap would have cut; output tokens, latency and cost per call against
Opus's; which kind of evidence each role says its position rests on most.

## 3. Data

EXP-019's frozen cases, unchanged: `exp019_cases.json`, sha256 `c5c04b3e10ff…`, 13 cases of which the 9
with `variant: recorded` are used (every debate that stores its packet, 2026-10-01 to 2026-10-05). Arm A is
the recorded packet. Arm B is the recorded packet, a newline, and the three lines of score arithmetic. The
truth of each question is in the cases file and was computed in code before any call. The files live outside
the repo, in OneDrive `trading-agents-data/exp020/` (a copy of `exp019/`'s cases and scripts).

Opus's answers for the comparison are EXP-019's ledger as it stands: 31 calls, 30 read, 45 arm B answers. Its
missing five phase-1 calls are GILD's defender and challenger in arm B and the challengers of AMGN (both
arms) and GILD (arm A).

## 4. Tools and setup

- **Model:** `gpt-5.5` through the kernel's own OpenAI client (Chat Completions), `reasoning_effort=high`,
  the effort the three deployed deliberators run. No temperature is sent.
- **Output ceiling: 16,384 tokens, not the fleet's 8,192.** This is the one setting that departs from the
  fleet, on purpose. On this vendor the model's reasoning tokens count against the ceiling, and the typed
  turn is expected to pass 8,192 for the defender (*[estimated]* about 9,200, from the ratio measured on one
  debate). A turn cut at the ceiling is billed, unread, and would measure the cap, not the understanding.
  The model is never told the ceiling, so a turn that writes more than 8,192 tokens here is one the fleet
  would have cut: that count is reported.
- **Code:** the worktree `../ta-exp019`, pinned at EXP-019's commit `3391df9d`: the same role prompts, the
  same signature, DSPy 3.4.0, `openai` 2.49.0, Python 3.13, Windows 10.
- **Scripts:** EXP-019's `exp019_run.py` (sha256 `9c46a720f967…`) and `exp019_score.py` (sha256
  `de5d55d72d33…`), unchanged. A driver, `exp020_openai.py` (Appendix S), imports the frozen runner and
  changes six of its names at run time: the vendor, the model, its price, the ceiling, the spend at which no
  new call starts, and the units run one at a time.
- **Seeds:** the scorer's own, `20261006`, 10,000 resamples.
- **Cost cap:** $7.00. No new call starts once $6.45 is recorded. Calls run one at a time, and the dearest
  possible call is about $0.54 (16,384 output tokens at $30 per million, plus the input), so the total cannot
  pass $7.00. *[estimated]* a defender and challenger pair costs about $0.50.

## 5. How it was conducted

1. The folder was set up with unchanged copies of the cases and the two scripts; their hashes were checked
   against `exp019/`'s.
2. The driver was run with `--fake` for both arms: 36 calls recorded at $0, ids equal to EXP-019's, model
   `gpt-5.5`; the patched runner builds the kernel's OpenAI client with the settings above.
3. This pre-registration and the two new scripts were committed before any paid call.
4. **Arm B first, all nine orders:** for each order the defender's first turn, then the challenger's with the
   defender's recorded turn as the transcript. 18 calls.
5. **Then arm A,** in the same order of orders, until the stop. *[estimated]* about four of the nine orders.
6. **Failure handling, as in EXP-019:** a transport failure costs nothing and is retried up to three times; a
   stopped or refused completion is billed, final and unread; an unreadable turn is recorded as unread; if a
   defender's call gives no completion its challenger is not asked.
7. **Scoring:** `exp019_score.py` on this folder for C1 and the described measures, and `exp020_compare.py`
   (Appendix S) for C2, the output tokens against the fleet's cap, latency and cost. Both cost $0.
8. Not run: EXP-019's phase 2 (the moved inputs) and its extension (a second run). Neither is funded here.

## 6. Results

All *[measured]*, from 31 calls for $6.52. The run stopped by its own rule after the thirteenth call of arm
A. Every call was read; none stopped or was refused.

**The bars.**

| Hypothesis | Bar | Result |
| --- | --- | --- |
| C1, `gpt-5.5` with the arithmetic | at least 49 of 54 right; at least 8 of 10 hinges found | **54 of 54 right; 10 of 10 found.** Brier 0.0000. Met |
| C2, agreement with Opus, arm B | at least 90 % on the same side of 0.5 | **45 of 45**, and both right on all 45. Met on every answer Opus has given; nine are still owed by Opus's run |

**Today's packet, arm A (no bar).** Six orders were asked in full and a seventh defender; 39 of the 54
questions were answered. `gpt-5.5` was right on 28 of the 39. Opus, on the 45 it answered, was right on
34. The paired Brier difference between the arms on the 39 answered questions is −0.230, 95 % interval
−0.361 to −0.102. Where both vendors answered the same arm A question, they are on the same side in 31 of
36 and both right in 24. The five disagreements are all on two orders (C and TGT), four of them about the
fundamental pillar.

**Output against the fleet's cap.**

| | Calls | Output tokens, mean | Largest | Over 8,192 | Mean latency | Mean cost |
| --- | --- | --- | --- | --- | --- | --- |
| Opus, defender | 17 | 3,368 | 4,383 | 0 | 41 s | $0.111 |
| Opus, challenger | 14 | 4,268 | 6,228 | 0 | 51 s | $0.144 |
| `gpt-5.5`, defender | 16 | 7,110 | 11,556 | **5** | 66 s | $0.231 |
| `gpt-5.5`, challenger | 15 | 5,344 | 7,320 | 0 | 50 s | $0.188 |

The slowest call took 118 s, against the fleet's 120 s wait for a peer's reply. It is the same call that
wrote 11,556 tokens.

**What each role says its position rests on most, arm B.** The challenger names the bracket (the stop,
the target and their ratio) in 7 of 9 orders. The defender names the book's gates in 5 of 9.

## 7. Conclusions

- **With the score arithmetic in the packet, the two vendors are interchangeable on this question.**
  `gpt-5.5` answers every hinge question correctly, and it agrees with Opus on every answer both have
  given. The gate of S255 holds on the vendor the fleet debates on today.
- **Without it, each vendor guesses, and they guess differently.** On today's packet `gpt-5.5` is right
  on 28 of 39 and Opus on 34 of 45, and they disagree on 5 of 36. So the place where a forced swap
  changes what the debaters believe is the packet as it is now. The arithmetic removes the difference.
- **`gpt-5.5`'s defender writes about twice what Opus's writes, and the fleet's cap would have cut 5 of
  its 16 turns.** A cut turn fails its order open. None of the challenger's turns passed the cap. These
  are the typed turns of this experiment, which ask for more than production's turn does today; the one
  production debate measured on `gpt-5.5` reached 94 % of the cap without passing it. The cap is
  therefore close for today's turn and too low for the typed turn that step 3 of the order of work
  brings.
- **What this does not say.** Nothing about the judge. Nothing about a second round. It did not run the
  moved-input cases, so whether `gpt-5.5`'s answer follows a changed input is not measured. Each call was
  made once, so run-to-run agreement is not measured. Nine orders.
- **A false clause in the text that was measured, found 2026-10-07 20:37 AEDT.** While pinning the lines for
  [S255](../../sprints/sprint-255-the-packet-states-the-score-arithmetic.md), its builder found that
  arm B's first line says that inside `quant_metrics` *each key ending in `_score`* is a 0-100 band score. Four such keys are on a 0-1 scale: `technical_score`, `fundamental_score`, `sentiment_score` and `composite_score` (measured over 1,765 recorded recommendations: 20 distinct keys end in `_score`, and these four never exceed 1.0).
  The planner wrote the sentence. The results above stand as a measurement of that text: every answer was
  right with it. S255 ships the line with one clause added that excepts the four keys. That corrected
  line has not been read by a model in an experiment.

## 8. Recommended code changes, and how to implement them

1. **The arithmetic in the packet** ([S255](../../sprints/sprint-255-the-packet-states-the-score-arithmetic.md),
   in build). This result supports it on `gpt-5.5`. Its merge is held for EXP-019's verdict on Opus by the
   operator's word; whether this result lifts the hold is the operator's decision.
2. **The output cap** (work-queue 111). Raise the bound on the deliberator's `max_tokens`, which is fixed
   at 8,192 in `agents/deliberator/settings.py`, and set a higher cap for the three apps; check the 120 s
   wait for a peer's reply against the 118 s measured here. A fix sprint, size S, with a law-book check of
   the settings' `PARAM` rows. It should land before the typed turn does, and before S255 is deployed on
   `gpt-5.5`, because S255 makes the packet about 1,600 characters longer.
3. **Nothing else.** No prompt change is recommended from this result.

## Appendix P — Pre-registration (frozen)

Committed before any paid call. Frozen: the cases (sha256 `c5c04b3e10ff…`); the runner and the scorer
(sha256 `9c46a720f967…`, `de5d55d72d33…`); the driver and the compare script in Appendix S; `gpt-5.5`,
`reasoning_effort=high`, a 16,384-token ceiling; one call at a time; arm B's nine orders first, then arm A
until the stop; no new call from $6.45 recorded, $7.00 the cap.

- **C1:** `gpt-5.5`, arm B: at least 49 of 54 answers on the right side of 0.5 and at least 8 of 10 true
  hinges found. Not asked, not read or cut off counts as wrong.
- **C2:** arm B answers given by both vendors for the same order, role and pillar: same side of 0.5 in at
  least 90 %. Recounted when Opus's run completes.
- **C0:** either bar missed.
- **Described, no bar:** arm A on every measure; the Brier difference between arms on the orders asked in
  both; turns over 8,192 output tokens; tokens, latency and cost against Opus's; the `decisive` family.

## Appendix R — Run record

Run 2026-10-07, finished 19:10 AEDT, from `../ta-exp019` at `3391df9d`. The ledger, the prompts sent and
these outputs are in OneDrive `trading-agents-data/exp020/`.

**Arm B, `exp020_openai.py <dir> B`:**

```text
arm B: 9 units, 18 calls; model gpt-5.5, effort high, ceiling 16384; spent so far $0.0000; no new call from $6.45
  TGT   arm B: calls so far 2, spent $0.3387
  C     arm B: calls so far 4, spent $0.7670
  DE    arm B: calls so far 6, spent $1.1116
  EMR   arm B: calls so far 8, spent $1.4849
  JNJ   arm B: calls so far 10, spent $1.9480
  UNP   arm B: calls so far 12, spent $2.3508
  MRK   arm B: calls so far 14, spent $2.7244
  AMGN  arm B: calls so far 16, spent $3.0093
  GILD  arm B: calls so far 18, spent $3.4396
arm B done: 18 calls recorded, 18 parsed, 0 stopped, 2 wrote more than the fleet's 8192-token cap; total spent $3.4396
ARM_B_EXIT=0
```

**Arm A, `exp020_openai.py <dir> A`.** The stop rule ended it after MRK's defender; AMGN's and GILD's
units were not started:

```text
arm A: 9 units, 18 calls; model gpt-5.5, effort high, ceiling 16384; spent so far $3.4396; no new call from $6.45
  TGT   arm A: calls so far 2, spent $4.0116
  C     arm A: calls so far 4, spent $4.5324
  DE    arm A: calls so far 6, spent $4.9762
  EMR   arm A: calls so far 8, spent $5.4235
  JNJ   arm A: calls so far 10, spent $5.8844
  UNP   arm A: calls so far 12, spent $6.3112
  MRK   arm A: calls so far 13, spent $6.5181
  AMGN  arm A: calls so far 13, spent $6.5181
  GILD  arm A: calls so far 13, spent $6.5181
arm A done: 13 calls recorded, 13 parsed, 0 stopped, 3 wrote more than the fleet's 8192-token cap; total spent $6.5181
ARM_A_EXIT=0
```

**The frozen scorer, `exp019_score.py <dir>`.** Its section on the moved-input cases is left out: those
cases were not run here.

```text
== operations
phase 1: calls 31, parsed 31, max_tokens stops 0, cost $6.5181, output tokens 3441-11556, latency max 118.3 s
total cost $6.5181 over 31 calls

== P1: does the role know which pillar the order hinges on (recorded packets)
judgements per arm 54; true hinges 10; constant-base-rate Brier 0.1509; always-no Brier 0.1852
arm A: right 28 of 54; true hinges found 7 of 10; unread 15; Brier 0.2296
   defender: right 14 of 27; true hinges found 4 of 5; unread 6; Brier 0.2532
   challenger: right 14 of 27; true hinges found 3 of 5; unread 9; Brier 0.2021
   not borderline: right 26 of 44; true hinges found 5 of 6; unread 10; Brier 0.1861
arm B: right 54 of 54; true hinges found 10 of 10; unread 0; Brier 0.0000
   defender: right 27 of 27; true hinges found 5 of 5; unread 0; Brier 0.0000
   challenger: right 27 of 27; true hinges found 5 of 5; unread 0; Brier 0.0000
   not borderline: right 44 of 44; true hinges found 6 of 6; unread 0; Brier 0.0000
Brier B - A (paired, 39 judgements, resampled by order): -0.2296 [-0.3605, -0.1023]

== D1: what each role says its position rests on most (mean probability, recorded packets)
arm A defender   n=7 technical 0.23 fundamental 0.07 sentiment 0.21 regime 0.07 bracket 0.09 book 0.33 | named most: {'book': 3, 'technical': 2, 'sentiment': 2}
arm A challenger n=6 technical 0.19 fundamental 0.09 sentiment 0.31 regime 0.02 bracket 0.34 book 0.05 | named most: {'technical': 1, 'bracket': 2, 'sentiment': 3}
arm A: orders with a hinge, mean probability placed on the hinge pillar(s): 0.42 (n=5)
arm B defender   n=9 technical 0.22 fundamental 0.07 sentiment 0.22 regime 0.03 bracket 0.08 book 0.37 | named most: {'book': 5, 'technical': 2, 'sentiment': 2}
arm B challenger n=9 technical 0.18 fundamental 0.09 sentiment 0.16 regime 0.03 bracket 0.49 book 0.05 | named most: {'bracket': 7, 'sentiment': 1, 'technical': 1}
arm B: orders with a hinge, mean probability placed on the hinge pillar(s): 0.49 (n=8)

== D2: does the argument name the hinge pillar's evidence (word match, an upper bound)
arm A: 6 of 7 arguments name the hinge pillar
arm B: 9 of 10 arguments name the hinge pillar
```

**The comparison, `exp020_compare.py <exp019 dir> <exp020 dir>`:**

```text
arm B: answered by both 45; same side of 0.5 45; both right 45
  differ: C|recorded arm A challenger fundamental: opus 0.56, gpt-5.5 0.10, truth False
  differ: C|recorded arm A defender fundamental: opus 0.48, gpt-5.5 0.86, truth False
  differ: C|recorded arm A defender sentiment: opus 0.40, gpt-5.5 0.83, truth False
  differ: TGT|recorded arm A challenger fundamental: opus 0.14, gpt-5.5 0.90, truth False
  differ: TGT|recorded arm A defender fundamental: opus 0.30, gpt-5.5 0.75, truth False
arm A: answered by both 36; same side of 0.5 31; both right 24
opus     defender   calls 17 | output tokens mean 3368, max 4383, over the fleet's cap 0 | read 17 | stopped 0 | mean latency 41 s | mean cost $0.111
opus     challenger calls 14 | output tokens mean 4268, max 6228, over the fleet's cap 0 | read 13 | stopped 0 | mean latency 51 s | mean cost $0.144
gpt-5.5  defender   calls 16 | output tokens mean 7110, max 11556, over the fleet's cap 5 | read 16 | stopped 0 | mean latency 66 s | mean cost $0.231
gpt-5.5  challenger calls 15 | output tokens mean 5344, max 7320, over the fleet's cap 0 | read 15 | stopped 0 | mean latency 50 s | mean cost $0.188
spend: opus $3.91 for 31 calls; gpt-5.5 $6.52 for 31 calls
```

## Appendix S — Scripts

### `exp020_openai.py`

```python
"""EXP-020 driver: EXP-019's frozen runner and frozen cases, on gpt-5.5.

Run from the worktree pinned at EXP-019's commit, one arm at a time:
  PYTHONPATH=. uv run --no-sync --env-file <main>/.env python <dir>/exp020_openai.py <dir> B [--fake]
  PYTHONPATH=. uv run --no-sync --env-file <main>/.env python <dir>/exp020_openai.py <dir> A [--fake]
<dir> holds unchanged copies of exp019_cases.json and exp019_run.py. This driver changes six names of
the frozen runner at run time and nothing else: the vendor, the model, its price, the output ceiling,
the spend at which no new call starts, and it runs the units one at a time, one arm per invocation.
Resumable: a call already in <dir>/exp019_calls.jsonl is never made again. Writes nothing to the graph.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

folder, arm = Path(sys.argv[1]), sys.argv[2]
fake = "--fake" in sys.argv[3:]
assert arm in ("A", "B"), arm
sys.path.insert(0, str(folder))
import exp019_run as R  # noqa: E402

_build = R.build_llm


def _openai(provider: str, *, api_key: str | None, model: str, max_tokens: int, effort: str):
    assert provider == "anthropic", provider  # the frozen runner's literal, replaced here and nowhere else
    del api_key
    return _build("openai", api_key=os.environ.get("OPENAI_API_KEY"), model=model, max_tokens=max_tokens, effort=effort)


R.build_llm = _openai
R.MODEL = "gpt-5.5"
R._RATE = R._PRICING["models"]["gpt-5.5"]
R.MAX_TOKENS = 16384
R.STOP_USD = 6.45
FLEET_CAP = 8192

cases = [c for c in json.loads((folder / "exp019_cases.json").read_text(encoding="utf-8")) if c["variant"] == "recorded"]
ledger = R.Ledger(folder / ("exp019_calls_fake.jsonl" if fake else "exp019_calls.jsonl"))
print(f"arm {arm}: {len(cases)} units, {2 * len(cases)} calls; model {R.MODEL}, effort {R.EFFORT}, ceiling {R.MAX_TOKENS}; "
      f"spent so far ${ledger.spent:.4f}; no new call from ${R.STOP_USD:.2f}", flush=True)
for case in cases:  # one at a time: the stop can be passed by one call at most
    R.unit(ledger, fake, 1, case, arm, 1)
    done = [r for r in ledger.rows.values() if r["arm"] == arm]
    print(f"  {case['ticker']:5s} arm {arm}: calls so far {len(done)}, spent ${ledger.spent:.4f}", flush=True)
rows = [r for r in ledger.rows.values() if r["arm"] == arm]
over = sum(1 for r in rows if r["usage"] and r["usage"]["out"] > FLEET_CAP)
print(f"arm {arm} done: {len(rows)} calls recorded, {sum(1 for r in rows if r['parsed'])} parsed, "
      f"{sum(1 for r in rows if r['error'] and r['error'].startswith('stopped'))} stopped, "
      f"{over} wrote more than the fleet's {FLEET_CAP}-token cap; total spent ${ledger.spent:.4f}", flush=True)
```

### `exp020_compare.py`

```python
"""EXP-020 compare ($0): gpt-5.5's answers against Opus's on the same case, arm, role and pillar.

  python exp020_compare.py <exp019 dir> <exp020 dir>
Both folders hold an exp019_calls.jsonl written by the same frozen runner. Phase 1 only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PILLARS = ("technical", "fundamental", "sentiment")
FLEET_CAP = 8192
opus_dir, gpt_dir = Path(sys.argv[1]), Path(sys.argv[2])


def load(folder: Path) -> dict:
    rows = (json.loads(line) for line in (folder / "exp019_calls.jsonl").read_text(encoding="utf-8").splitlines() if line.strip())
    return {(r["case"], r["arm"], r["rep"], r["role"]): r for r in rows if r["phase"] == 1}


opus, gpt = load(opus_dir), load(gpt_dir)
cases = {c["case"]: c for c in json.loads((gpt_dir / "exp019_cases.json").read_text(encoding="utf-8"))}

for arm in ("B", "A"):
    both = same = both_right = 0
    for key in sorted(set(opus) & set(gpt)):
        if key[1] != arm or not opus[key]["parsed"] or not gpt[key]["parsed"]:
            continue
        for pillar in PILLARS:
            truth = cases[key[0]]["truth"].get(pillar)
            if truth is None:
                continue
            a, b = opus[key]["parsed"]["hinge"][pillar], gpt[key]["parsed"]["hinge"][pillar]
            both += 1
            same += (a >= 0.5) == (b >= 0.5)
            both_right += (a >= 0.5) == truth["hinge"] and (b >= 0.5) == truth["hinge"]
            if (a >= 0.5) != (b >= 0.5):
                print(f"  differ: {key[0]} arm {arm} {key[3]} {pillar}: opus {a:.2f}, gpt-5.5 {b:.2f}, truth {truth['hinge']}")
    print(f"arm {arm}: answered by both {both}; same side of 0.5 {same}; both right {both_right}")

for name, ledger in (("opus", opus), ("gpt-5.5", gpt)):
    for role in ("defender", "challenger"):
        rows = [r for r in ledger.values() if r["role"] == role and r["usage"]]
        if not rows:
            continue
        out = [r["usage"]["out"] for r in rows]
        print(f"{name:8s} {role:10s} calls {len(rows):2d} | output tokens mean {sum(out) // len(out)}, max {max(out)}, "
              f"over the fleet's cap {sum(1 for o in out if o > FLEET_CAP)} | read {sum(1 for r in rows if r['parsed'])} | "
              f"stopped {sum(1 for r in rows if r['error'] and r['error'].startswith('stopped'))} | "
              f"mean latency {sum(r['latency_s'] for r in rows) / len(rows):.0f} s | mean cost ${sum(r['cost_usd'] for r in rows) / len(rows):.3f}")
print(f"spend: opus ${sum(r['cost_usd'] for r in opus.values()):.2f} for {len(opus)} calls; "
      f"gpt-5.5 ${sum(r['cost_usd'] for r in gpt.values()):.2f} for {len(gpt)} calls")
```
