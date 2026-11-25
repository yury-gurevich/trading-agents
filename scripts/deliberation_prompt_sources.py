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
# What the judge rules on (S291, DL-326). It replaced S119's "do not uphold once a
# flaw is named", under which every ruling from 2026-09-18 was `revise`.
JUDGE_ORDER_RULE = (
    " Rule on what distinguishes THIS order from every other order the system "
    "would approve. A design property that is true of every order, such as a "
    "figure printed and not enforced (the target's size against the stop is one), "
    "fixed-fraction sizing, or a regime label that changes no number, is a design "
    "note and cannot decide the ruling unless this order's own case relies on it. "
    "Passing every gate does not earn an uphold: the gates are why the order "
    "reached you. Rule uphold when this name's own evidence supports the order and "
    "the objections are shared or unsupported. Rule revise when this name's own "
    "evidence shows a material weakness the gates do not answer, such as "
    "confidence that clears its floor only through one pillar, news or a recent "
    "move against the thesis, or an event inside the holding period. Rule overturn "
    "only when evidence specific to this order shows it should not be placed, such "
    "as a wrong input it depends on or a stated limit it breaks. A revise or "
    "overturn rationale states only the evidence that decided it and names no "
    "design note."
)
# Hypotheticals, so the judge sees every ruling demonstrated: (name, decision,
# context, ruling, rationale). They state no fact about this system's code.
JUDGE_CONTRAST_CASES = (
    (
        "shared-disclosed-figure",
        "Buy KO: every enforced gate passed.",
        "A ratio in the report is printed and rejects no order at any value. KO's "
        "inputs are current and its stop is recorded. The challenger's only "
        "objection is that this ratio is not enforced.",
        "uphold",
        "the objection holds for every order and names nothing wrong with this one",
    ),
    (
        "shared-sizing-rule",
        "Buy PG, sized like every other order.",
        "PG has beta 0.4 and an ordinary range for its history. The challenger's "
        "only objection is that the sizing rule ignores volatility.",
        "uphold",
        "the sizing rule is shared by every order and this low-beta name gives it "
        "no extra force",
    ),
    (
        "one-pillar-clearance",
        "Buy XYZ at confidence 0.61.",
        "The floor is 0.60. With its sentiment score at neutral the confidence "
        "would be 0.58, and its technical and fundamental scores are below neutral.",
        "revise",
        "this order clears its floor only through sentiment, so its case is "
        "thinner than its score suggests",
    ),
    (
        "wrong-price-input",
        "Buy 10 XYZ at the estimated price of $412.00.",
        "The latest close in the evidence is $41.20, so the order's estimated "
        "price is ten times the market's.",
        "overturn",
        "the order's price contradicts its own latest close, so its size and stop "
        "rest on a wrong input",
    ),
    (
        "stated-limit-broken",
        "Buy ABC, a new issuer in Energy.",
        "The evidence states a limit of three names per sector and shows three "
        "Energy names already held, so ABC would be the fourth.",
        "overturn",
        "this order breaks the stated limit on names in its sector",
    ),
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
