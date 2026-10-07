# EXP-020 — On the same frozen cases, does gpt-5.5 know what an order hinges on as Opus does?

**Status:** PRE-REGISTERED 2026-10-07 · no paid call made before this commit
**Decision / origin:** [DL-264](../../design-log.md) amendment 7 (the operator, 2026-10-07: *"maybe we
should continue testing on OpenAI to get confidence tat if we HAVE TO swap from anthropic to openai again
it will give up comparable results"*) · work-queue **107** · the gate of
[S255](../../sprints/sprint-255-the-packet-states-the-score-arithmetic.md) · **Cost:** capped at **$7.00**
(operator, 2026-10-07: *"yeah, the $7 will be sufficient"*); no new call starts once $6.45 is recorded

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

Not yet run.

## 7. Conclusions

Not yet run.

## 8. Recommended code changes, and how to implement them

Not yet run.

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

Not yet run.

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
