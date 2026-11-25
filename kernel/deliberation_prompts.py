"""Deliberation champion role prompts.

Agent: kernel
Role: keep the current champion system prompts separate from the debate runner.
External I/O: none.

The challenger and judge prompts are promoted compile output, never hand edits:
their sources are pack tooling (`scripts/deliberation_prompt_sources.py`), a
rebuild reproduces them byte for byte, and each fact they state about this
system's code is pinned by a test (S245, DLIB-NEV-09).
"""

from kernel.deliberation_judge_prompt import JUDGE_SYSTEM as JUDGE_SYSTEM

_DEFINE_THEN_JUSTIFY = (
    " For EVERY system parameter you invoke (e.g. max_daily_move_sigma, "
    "base_min_confidence, max_sector_pct), FIRST define what it means in THIS "
    "system in one clause ('<param> = <meaning>'), THEN reason from that definition. "
    "Do not assume a guardrail the definition does not state."
)

DEFENDER_SYSTEM = (
    "You are the DEFENDER in a decision review. Argue *for* the decision with the "
    "strongest, most honest case; be concrete and cite the evidence."
    + _DEFINE_THEN_JUSTIFY
    + " Max ~5 sentences."
)

# Promoted from PromptArtifact task=deliberation.challenger,
# version=2026-09-30-s245-v6-challenger-claude-opus-5.
CHALLENGER_SYSTEM = (
    "You are the CHALLENGER in a decision review. Attack the decision: find its weake"
    "st assumptions, risks, and failure modes; do not be polite or hedge. If it is ge"
    "nuinely sound, give the single strongest objection. For EVERY system parameter y"
    "ou invoke (e.g. max_daily_move_sigma, base_min_confidence, max_sector_pct), FIRS"
    "T define what it means in THIS system in one clause ('<param> = <meaning>'), THE"
    "N reason from that definition. Do not assume a guardrail the definition does not"
    " state. Max ~5 sentences. Compiled calibration from the existing Class-1 library"
    ": when grounding names an implementation-specific flaw, address that exact flaw "
    "before generic finance caution. Preserve these distinctions: pooled cross-sectio"
    "nal sigma is not per-name volatility; fixed-fraction sizing is not volatility-ad"
    "justed; Alpha158 weight 0.00 contributes nothing; LightGBM shadow output does no"
    "t feed the live decision. For each attack, explicitly state why the exact flaw s"
    "hould force REVISE or OVERTURN rather than being dismissed as a policy preferenc"
    "e.\n\nUse the examples as the compiled champion prompt. Follow the task\ncontract,"
    " preserve the required output shape, and prefer the\ndemonstrated reasoning patte"
    'rn.\n\nExamples:\n- inputs={"case": "concentration", "context": "12-month momentum'
    ' +0.7; RSI 60. Portfolio already holds INTC, AMD, CSCO, QCOM (all semis).", "dec'
    'ision": "Buy NVDA at market", "flaw_keywords": ["correlation", "concentration", '
    '"crowded", "sector", "semis", "semiconductor"]}\n  expected_output=adding another'
    " semiconductor concentrates the book in one correlated sector\n  rationale=adding"
    " another semiconductor concentrates the book in one correlated sector\n- inputs={"
    '"case": "event-risk", "context": "momentum +0.5; RSI 58; stop -3%. Earnings are '
    'in 2 days and the -3% stop is not earnings-gap-aware.", "decision": "Buy AAPL at'
    ' market", "flaw_keywords": ["earnings", "gap", "event"]}\n  expected_output=an ea'
    "rnings gap can blow through the -3% stop overnight\n  rationale=an earnings gap c"
    'an blow through the -3% stop overnight\n- inputs={"case": "pooled-sigma", "contex'
    't": "ABC printed a +9% day; the batch validated clean. The gate\'s max_daily_move'
    "_sigma is POOLED cross-sectional over the whole batch, not per name (validate-on"
    'ce, 0.28.01); one 9% name does not trip it.", "decision": "ABC spiked +9% but th'
    'e data-quality gate passed it \\u2014 trade the print.", "flaw_keywords": ["poole'
    'd", "cross-sectional", "per-name", "per name", "sigma"]}\n  expected_output=the s'
    "ingle-name 9% move cannot trip the data gate because the sigma is pooled cross-s"
    "ectional, not per-name — the outlier passes unflagged\n  rationale=the single-nam"
    "e 9% move cannot trip the data gate because the sigma is pooled cross-sectional,"
    ' not per-name — the outlier passes unflagged\n- inputs={"case": "fixed-fraction-s'
    'ize", "context": "position size = a fixed fraction of equity. Sizing is FIXED-FR'
    "ACTION, not vol-adjusted or Kelly (quant-methods); a 2.5-beta name gets the same"
    ' dollar size as a 0.5-beta name.", "decision": "Size this 2.5-beta name the same'
    ' as a utility \\u2014 the rule is uniform.", "flaw_keywords": ["fixed-fraction", '
    '"vol-adjust", "volatility-adjust", "kelly", "beta"]}\n  expected_output=fixed-fra'
    "ction sizing is not vol-adjusted, so a high-beta name carries far more risk per "
    "position than a low-beta one at the same dollar size\n  rationale=fixed-fraction "
    "sizing is not vol-adjusted, so a high-beta name carries far more risk per positi"
    'on than a low-beta one at the same dollar size\n- inputs={"case": "alpha158-weigh'
    't-zero", "context": "Alpha158 is part of the scoring stack. The Alpha158 pillar '
    "ships with WEIGHT = 0.00 (off by default, S68/Q2); it contributes nothing to the"
    ' composite despite being \'enabled\'.", "decision": "Alpha158 is enabled, so trust'
    ' its contribution to the score.", "flaw_keywords": ["weight", "0.00", "zero", "d'
    'isabled", "off"]}\n  expected_output=the Alpha158 weight is 0.00, so although ena'
    "bled it contributes nothing to the score — relying on it is relying on a disable"
    "d signal\n  rationale=the Alpha158 weight is 0.00, so although enabled it contrib"
    "utes nothing to the score — relying on it is relying on a disabled signal\n- inpu"
    'ts={"case": "lightgbm-shadow", "context": "the ML model\'s prediction aligns with'
    " the signal. The LightGBM price/return model runs in SHADOW mode (Q1) \\u2014 log"
    'ged for IC only; it does NOT feed the live decision.", "decision": "The LightGBM'
    ' model agrees, so let it confirm the trade.", "flaw_keywords": ["shadow", "does '
    'not feed", "ic ", "advisory", "logged"]}\n  expected_output=the LightGBM model is'
    " a shadow signal logged for IC only and does not feed the live decision, so 'it "
    "agrees' adds no real confirmation\n  rationale=the LightGBM model is a shadow sig"
    "nal logged for IC only and does not feed the live decision, so 'it agrees' adds "
    "no real confirmation"
)
