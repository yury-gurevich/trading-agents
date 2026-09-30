"""Hand-written sources the deliberation role prompts are compiled from.

Agent: tooling
Role: hold the challenger and judge base prompts and the Class-1 calibration
      text, so a compile rebuilds the promoted kernel champions from them.
External I/O: none.

S245 (DL-251 D1). The pipeline used to start from the *promoted* kernel constants,
so every re-run nested the calibration and the examples a second time (13,023 vs
6,764 chars). Each base here is its champion's text before " Compiled calibration
from the existing Class-1 library", which is also what a person wrote before the
S121 promotion. The defender has never been promoted, so its kernel constant is
its base and it is not repeated here.

🪤 A sentence here that tells a role how this system's code behaves reaches the
referee on the next promotion. It needs a pin in
`tests/test_deliberation_prompt_facts.py` first (DLIB-NEV-09), or `make ci` fails.
"""

from __future__ import annotations

CHALLENGER_BASE = (
    "You are the CHALLENGER in a decision review. Attack the decision: find its "
    "weakest assumptions, risks, and failure modes; do not be polite or hedge. If it "
    "is genuinely sound, give the single strongest objection. For EVERY system "
    "parameter you invoke (e.g. max_daily_move_sigma, base_min_confidence, "
    "max_sector_pct), FIRST define what it means in THIS system in one clause "
    "('<param> = <meaning>'), THEN reason from that definition. Do not assume a "
    "guardrail the definition does not state. Max ~5 sentences."
)
JUDGE_BASE = (
    "You are the JUDGE in a decision review. Weigh the Defender vs the Challenger "
    "on the merits, not the volume. Reply ONLY as JSON: "
    '{"ruling": "uphold|overturn|revise", "rationale": "<one line>"}.'
)
# Added by the pipeline (S119), so part of the judge's instruction, not its base.
JUDGE_GROUNDED_FLAW_RULE = (
    " If the Challenger catches a grounded implementation-specific flaw from "
    "the evidence, do not uphold the decision."
)
CLASS1_CALIBRATION = (
    " Compiled calibration from the existing Class-1 library: when grounding names "
    "an implementation-specific flaw, address that exact flaw before generic "
    "finance caution. Preserve these distinctions: pooled cross-sectional sigma is "
    "not per-name volatility; fixed-fraction sizing is not volatility-adjusted; "
    "Alpha158 weight 0.00 contributes nothing; LightGBM shadow output does not "
    "feed the live decision."
)
# A steer, not a fact about our code; changing steers is work-queue 75's
# experiment. S245 removed the calendar-staleness sentences that followed it.
CHALLENGER_CALIBRATION = (
    " For each attack, explicitly state why the exact flaw should force REVISE or "
    "OVERTURN rather than being dismissed as a policy preference."
)
