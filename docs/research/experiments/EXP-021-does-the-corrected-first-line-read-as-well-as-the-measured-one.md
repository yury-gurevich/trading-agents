# EXP-021 — Does the corrected first line read as well as the one that was measured?

**Status:** COMPLETE 2026-10-07 · **both bars met.** With the corrected line `gpt-5.5` answers 54 of 54 right and finds 10 of 10 hinges, and every answer is on the side it was on with the uncorrected line. Pre-registered at `dc949025`, before any paid call
**Decision / origin:** [DL-264](../../design-log.md) amendment 7 and DL-270 on the branch of
[S255](../../sprints/sprint-255-the-packet-states-the-score-arithmetic.md) (the operator, 2026-10-07, on the
planner's proposal to measure the corrected text again: *"run it"*) · work-queue **107** · **Cost:** the same
arm cost $3.44 in [EXP-020](EXP-020-on-the-same-cases-does-gpt-5-5-know-the-hinge-as-opus-does.md); no new
call starts once $3.60 is recorded, so the total cannot pass $4.14. **Spent: $3.29** on 18 calls

## 1. Why we needed this experiment

S255 puts three lines of score arithmetic at the end of the evidence packet. EXP-019 and EXP-020 measured
those lines. Its builder then found that the first line was false in one clause: it called every key
ending in `_score` a 0-100 band score, and four are on a 0-1 scale. The line is corrected with one inserted
clause. The corrected line is what will ship, and no model has read it in an experiment. A change to the
evidence a model reads is within [ADR-0010](../../decisions/0010-llm-interaction-quality-gate.md), so the
corrected text is measured before S255 merges.

## 2. Hypothesis

The unit is EXP-019's: for each of the three pillars, each debater states the probability that the order
would have missed its confidence floor with that pillar at a neutral 0.50. Nine orders, two roles: 54
answers, 10 of them true hinges.

- **K1 (the corrected text works).** On `gpt-5.5`, with the corrected lines: at least **49 of 54** answers on
  the right side of 0.5 and at least **8 of 10** true hinges found. An answer not asked, not read or cut off
  counts as wrong. These are EXP-019's bars.
- **K2 (the correction changes no answer's side).** Against EXP-020's arm B, the same model with the
  uncorrected line: the two are on the same side of 0.5 in at least **90 %** of the answers both gave.
- **K0.** Either bar is missed: the corrected wording is reworked and measured again before S255 merges.

**Described, with no bar:** output tokens, the turns over the fleet's 8,192-token cap, latency and cost,
each against EXP-020's arm B.

## 3. Data

EXP-019's nine recorded cases, with `block` changed by the one inserted clause and nothing else:
`exp019_cases.json` in OneDrive `trading-agents-data/exp021/`, sha256 `c73f9476598a…`, written by
`exp021_cases.py` (Appendix S). Each corrected block is checked to equal the text S255 ships for that
order (`arithmetic_lines` in the sprint's fixture). The truth of each question is unchanged: it was computed
in code before any call. The comparison ledger is EXP-020's, `trading-agents-data/exp020/`.

The inserted clause, after *"is a 0-100 band score in which 50 is neutral"*:

```text
, except technical_score, fundamental_score, sentiment_score and composite_score, which are on a 0-1 scale
```

## 4. Tools and setup

As EXP-020, which this repeats with one line of the packet changed: `gpt-5.5` through the kernel's OpenAI
client, `reasoning_effort=high`, a 16,384-token output ceiling (the fleet's is 8,192; turns over 8,192 are
counted); the worktree `../ta-exp019` pinned at `3391df9d`; DSPy 3.4.0, `openai` 2.49.0, Python 3.13,
Windows 10; EXP-019's `exp019_run.py` unchanged (sha256 `9c46a720f967…`), driven by `exp021_openai.py`
(Appendix S), which applies EXP-020's overrides with a lower spend stop. Calls run one at a time.

## 5. How it was conducted

1. `exp021_cases.py` wrote the nine corrected cases and checked each block against the text S255 ships.
2. The driver was run with `--fake`: 18 calls at $0, and all 18 user messages carry the corrected clause.
3. `exp021_score.py` (Appendix S) was run on EXP-020's ledger: it prints 54 of 54 right and 10 of 10
   hinges found, the counts EXP-019's frozen scorer printed for that ledger.
4. This pre-registration and the three scripts were committed before any paid call.
5. **Arm B, nine orders:** the defender's first turn, then the challenger's with the defender's recorded
   turn as the transcript. 18 calls. Arm A is not run: today's packet has no first line to correct.
6. Failure handling as in EXP-019 and EXP-020. Scoring: `exp021_score.py <exp021> <exp020>`, $0.

## 6. Results

All *[measured]*, from 18 calls for $3.29. Every call was read; none stopped or was refused.

| Hypothesis | Bar | Result |
| --- | --- | --- |
| K1, the corrected text on `gpt-5.5` | at least 49 of 54 right; at least 8 of 10 hinges found | **54 of 54 right; 10 of 10 found.** Met |
| K2, against the uncorrected line (EXP-020's arm B) | at least 90 % on the same side of 0.5 | **54 of 54.** Met |

**Described, against EXP-020's arm B.**

| | Calls | Output tokens, mean | Largest | Over 8,192 | Slowest | Mean cost |
| --- | --- | --- | --- | --- | --- | --- |
| Corrected line, defender | 9 | 5,661 | 7,085 | 0 | 63 s | $0.193 |
| Corrected line, challenger | 9 | 4,529 | 6,435 | 0 | 60 s | $0.173 |
| Uncorrected line, defender | 9 | 6,034 | 8,676 | 2 | 78 s | $0.206 |
| Uncorrected line, challenger | 9 | 4,621 | 5,712 | 0 | 52 s | $0.176 |

## 7. Conclusions

- **The corrected line reads as well as the one that was measured.** On `gpt-5.5` every answer is right, and
  none changed sides. The text S255 ships has now been read by a model in an experiment.
- **No defender turn passed the fleet's cap this time, against two of nine in EXP-020's arm B.** The same
  orders, model and settings gave 8,676 tokens at most then and 7,085 now. That is run-to-run variation, not
  an effect of the clause: over the 25 typed defender turns measured on `gpt-5.5`, 5 passed 8,192. Work-queue
  111 stands.
- **What this does not say.** The corrected line is not measured on Opus. EXP-019's remaining calls will
  measure the uncorrected line on Opus, because its cases are frozen. Each call here was made once.

## 8. Recommended code changes, and how to implement them

1. **S255 ships the corrected line**, as its spec already says. This result is the measurement that
   ADR-0010 asks for on the vendor the fleet debates on today. Whether the merge still waits for Opus is the
   operator's decision.
2. **Nothing else.**

## Appendix P — Pre-registration (frozen)

Committed before any paid call. Frozen: the corrected cases (sha256 `c73f9476598a…`); the runner (sha256
`9c46a720f967…`); the three scripts in Appendix S; `gpt-5.5`, `reasoning_effort=high`, a 16,384-token
ceiling; one call at a time; no new call from $3.60 recorded.

- **K1:** at least 49 of 54 answers on the right side of 0.5 and at least 8 of 10 true hinges found. Not
  asked, not read or cut off counts as wrong.
- **K2:** same side of 0.5 as EXP-020's arm B in at least 90 % of the answers both gave.
- **K0:** either bar missed.
- **Described, no bar:** tokens, turns over 8,192, latency and cost against EXP-020's arm B.

## Appendix R — Run record

Run 2026-10-07, finished 20:59 AEDT, from `../ta-exp019` at `3391df9d`. The ledger, the prompts sent and
these outputs are in OneDrive `trading-agents-data/exp021/`.

**The run, `exp021_openai.py <dir>`:**

```text
corrected text, arm B: 9 units, 18 calls; model gpt-5.5, effort high, ceiling 16384; spent so far $0.0000; no new call from $3.60
  TGT  : calls so far 2, spent $0.3253
  C    : calls so far 4, spent $0.7175
  DE   : calls so far 6, spent $1.0800
  EMR  : calls so far 8, spent $1.3936
  JNJ  : calls so far 10, spent $1.8516
  UNP  : calls so far 12, spent $2.1550
  MRK  : calls so far 14, spent $2.5471
  AMGN : calls so far 16, spent $2.9081
  GILD : calls so far 18, spent $3.2907
done: 18 calls recorded, 18 parsed, 0 stopped, 0 wrote more than the fleet's 8192-token cap; total spent $3.2907
RUN_EXIT=0
```

**The score, `exp021_score.py <exp021 dir> <exp020 dir>`:**

```text
exp021 arm B: right 54 of 54; true hinges found 10 of 10; unread 0
  defender   calls 9 | output tokens mean 5661, max 7085, over the fleet's cap 0 | mean latency 52 s, max 63 s | mean cost $0.193
  challenger calls 9 | output tokens mean 4529, max 6435, over the fleet's cap 0 | mean latency 42 s, max 60 s | mean cost $0.173
  spend $3.2907 for 18 calls
exp021 against exp020, arm B: answered by both 54; same side of 0.5 54
```

**The scorer on EXP-020's ledger, before the run** (the frozen scorer printed the same counts for it):

```text
exp020 arm B: right 54 of 54; true hinges found 10 of 10; unread 0
  defender   calls 9 | output tokens mean 6034, max 8676, over the fleet's cap 2 | mean latency 55 s, max 78 s | mean cost $0.206
  challenger calls 9 | output tokens mean 4621, max 5712, over the fleet's cap 0 | mean latency 43 s, max 52 s | mean cost $0.176
  spend $3.4396 for 18 calls
```

## Appendix S — Scripts

### `exp021_cases.py`

```python
"""EXP-021 cases ($0): EXP-019's nine recorded cases with the first line's scale clause corrected.

  python exp021_cases.py <exp019 dir> <exp021 dir> <S255 fixture json>
Writes <exp021 dir>/exp019_cases.json (the name the frozen runner reads). Only `block` changes, and only
by the one inserted clause. Each corrected block must equal the text S255 ships for that order.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

src, dst, fixture_path = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
OLD = "is a 0-100 band score in which 50 is neutral; technical_score ="
NEW = (
    "is a 0-100 band score in which 50 is neutral, except technical_score, fundamental_score, sentiment_score "
    "and composite_score, which are on a 0-1 scale; technical_score ="
)
cases = [c for c in json.loads((src / "exp019_cases.json").read_text(encoding="utf-8")) if c["variant"] == "recorded"]
shipped = {o["ticker"]: o["arithmetic_lines"] for o in json.loads(fixture_path.read_text(encoding="utf-8"))["orders"]}
for case in cases:
    assert case["block"].count(OLD) == 1, case["ticker"]
    case["block"] = case["block"].replace(OLD, NEW)
    assert case["block"] == shipped[case["ticker"]], case["ticker"]
out = dst / "exp019_cases.json"
out.write_text(json.dumps(cases, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print(f"cases {len(cases)}; every corrected block equals the text S255 ships; sha256 {hashlib.sha256(out.read_bytes()).hexdigest()}")
```

### `exp021_openai.py`

```python
"""EXP-021 driver: EXP-019's frozen runner on gpt-5.5, arm B only, with the corrected first line.

Run from the worktree pinned at EXP-019's commit:
  PYTHONPATH=. uv run --no-sync --env-file <main>/.env python <dir>/exp021_openai.py <dir> [--fake]
<dir> holds an unchanged copy of exp019_run.py and the cases written by exp021_cases.py. The overrides
are EXP-020's, with a lower spend stop: the vendor, the model, its price, the output ceiling, and the
units run one at a time. Resumable. Writes nothing to the graph.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

folder = Path(sys.argv[1])
fake = "--fake" in sys.argv[2:]
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
R.STOP_USD = 3.60
FLEET_CAP = 8192

cases = json.loads((folder / "exp019_cases.json").read_text(encoding="utf-8"))
assert all(c["variant"] == "recorded" and "which are on a 0-1 scale" in c["block"] for c in cases)
ledger = R.Ledger(folder / ("exp019_calls_fake.jsonl" if fake else "exp019_calls.jsonl"))
print(f"corrected text, arm B: {len(cases)} units, {2 * len(cases)} calls; model {R.MODEL}, effort {R.EFFORT}, "
      f"ceiling {R.MAX_TOKENS}; spent so far ${ledger.spent:.4f}; no new call from ${R.STOP_USD:.2f}", flush=True)
for case in cases:  # one at a time: the stop can be passed by one call at most
    R.unit(ledger, fake, 1, case, "B", 1)
    print(f"  {case['ticker']:5s}: calls so far {len(ledger.rows)}, spent ${ledger.spent:.4f}", flush=True)
rows = list(ledger.rows.values())
over = sum(1 for r in rows if r["usage"] and r["usage"]["out"] > FLEET_CAP)
print(f"done: {len(rows)} calls recorded, {sum(1 for r in rows if r['parsed'])} parsed, "
      f"{sum(1 for r in rows if r['error'] and r['error'].startswith('stopped'))} stopped, "
      f"{over} wrote more than the fleet's {FLEET_CAP}-token cap; total spent ${ledger.spent:.4f}", flush=True)
```

### `exp021_score.py`

```python
"""EXP-021 score ($0): arm B's counts by EXP-019's rule, and agreement between two ledgers.

  python exp021_score.py <dir>                 # the counts for <dir>'s arm B
  python exp021_score.py <dir> <other dir>     # and the agreement with <other dir>'s arm B
An answer is right when (probability >= 0.5) equals the truth in the cases file, which is the frozen
scorer's rule. An answer that was not asked or not read counts as wrong.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PILLARS = ("technical", "fundamental", "sentiment")
ROLES = ("defender", "challenger")
FLEET_CAP = 8192


def load(folder: Path) -> dict:
    rows = (json.loads(line) for line in (folder / "exp019_calls.jsonl").read_text(encoding="utf-8").splitlines() if line.strip())
    return {(r["case"], r["role"]): r for r in rows if r["phase"] == 1 and r["arm"] == "B"}


folder = Path(sys.argv[1])
ledger = load(folder)
cases = {c["case"]: c for c in json.loads((folder / "exp019_cases.json").read_text(encoding="utf-8")) if c["variant"] == "recorded"}
judgements = right = hinges = found = unread = 0
for name, case in cases.items():
    for role in ROLES:
        row = ledger.get((name, role))
        for pillar in PILLARS:
            truth = case["truth"].get(pillar)
            if truth is None:
                continue
            judgements += 1
            hinges += truth["hinge"]
            p = row["parsed"]["hinge"][pillar] if row and row["parsed"] else None
            if p is None:
                unread += 1
                continue
            ok = (p >= 0.5) == truth["hinge"]
            right += ok
            found += ok and truth["hinge"]
print(f"{folder.name} arm B: right {right} of {judgements}; true hinges found {found} of {hinges}; unread {unread}")
rows = [r for r in ledger.values() if r["usage"]]
for role in ROLES:
    out = [r["usage"]["out"] for r in rows if r["role"] == role]
    if out:
        sub = [r for r in rows if r["role"] == role]
        print(f"  {role:10s} calls {len(out)} | output tokens mean {sum(out) // len(out)}, max {max(out)}, over the fleet's cap "
              f"{sum(1 for o in out if o > FLEET_CAP)} | mean latency {sum(r['latency_s'] for r in sub) / len(sub):.0f} s, max "
              f"{max(r['latency_s'] for r in sub):.0f} s | mean cost ${sum(r['cost_usd'] for r in sub) / len(sub):.3f}")
print(f"  spend ${sum(r['cost_usd'] for r in ledger.values()):.4f} for {len(ledger)} calls")

if len(sys.argv) > 2:
    other_dir = Path(sys.argv[2])
    other = load(other_dir)
    both = same = 0
    for key in sorted(set(ledger) & set(other)):
        if not ledger[key]["parsed"] or not other[key]["parsed"]:
            continue
        for pillar in PILLARS:
            if cases[key[0]]["truth"].get(pillar) is None:
                continue
            a, b = ledger[key]["parsed"]["hinge"][pillar], other[key]["parsed"]["hinge"][pillar]
            both += 1
            same += (a >= 0.5) == (b >= 0.5)
            if (a >= 0.5) != (b >= 0.5):
                print(f"  differ: {key[0]} {key[1]} {pillar}: {folder.name} {a:.2f}, {other_dir.name} {b:.2f}")
    print(f"{folder.name} against {other_dir.name}, arm B: answered by both {both}; same side of 0.5 {same}")
```
