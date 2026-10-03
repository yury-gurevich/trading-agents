"""The trio as a DSPy program: signatures, the book adapter, and the two topologies.

T0: sequential debate (pro, con reading pro, repeated `rounds` times), then the judge.
T2: pro and con write independent briefs in parallel; the judge reads both and decides.
The book (dictionary + house rules) is rendered by the adapter into the SYSTEM message, outside the
signature instructions, so an optimiser cannot rewrite it and the provider can cache it (DL-264 §16).
"""

from __future__ import annotations

import json
from typing import Literal

import dspy
from kernel.deliberation_prompts import CHALLENGER_SYSTEM, DEFENDER_SYSTEM, JUDGE_SYSTEM

from .outputs import Brief, Ruling

LAB_PRO = (
    "You are the PRO deliberator on a proposed stock purchase. Make the strongest honest case FOR buying now. "
    "Read first: list in `readings` every value you rely on (exact packet key, exact value, its scale, what it "
    "means here, whether it is favourable for this buy, how much it weighs). Argue only from those readings, "
    "using the dictionary for meanings and the house rules for how this system works. Build the case on market "
    "evidence; process facts may support but never carry it. Name in `gaps` missing evidence that would change it."
)
LAB_CON = LAB_PRO.replace("PRO deliberator", "CON deliberator").replace(
    "FOR buying now", "AGAINST buying now"
)
LAB_JUDGE = (
    "You are the JUDGE, the expert who decides. First read the packet yourself (`own_readings`, same rules as the "
    "debaters). Then test each case's claims against the packet: accept or reject each with its reason, always "
    "answering the losing side's strongest claim. Decide: uphold (trade), revise (trade, with a recorded finding) "
    "or overturn (block); see house rule H1. List in `decisive` the keys your ruling rests on: at least one must "
    "be a high-weight market reading. In `rationale`, explain why THIS combination of data and market conditions "
    "leads to THIS ruling."
)
INSTRUCTIONS = {
    "lab": {"pro": LAB_PRO, "con": LAB_CON, "judge": LAB_JUDGE},
    "production": {"pro": DEFENDER_SYSTEM, "con": CHALLENGER_SYSTEM, "judge": JUDGE_SYSTEM},
}


class BriefSig(dspy.Signature):
    """Argue one side of the order."""

    decision: str = dspy.InputField(desc="the PM-approved order under review")
    packet: str = dspy.InputField(desc="the evidence packet, exactly as the fleet renders it")
    side: Literal["pro", "con"] = dspy.InputField()
    other_case: str = dspy.InputField(desc="the opposing case so far; empty when briefs are independent")
    law_feedback: str = dspy.InputField(
        desc="corrections from the form-law check of your previous attempt; empty on a first attempt"
    )
    brief: Brief = dspy.OutputField()


class RulingSig(dspy.Signature):
    """Decide the order."""

    decision: str = dspy.InputField(desc="the PM-approved order under review")
    packet: str = dspy.InputField(desc="the evidence packet, exactly as the fleet renders it")
    pro_case: str = dspy.InputField()
    con_case: str = dspy.InputField()
    law_feedback: str = dspy.InputField(
        desc="corrections from the form-law check of your previous attempt; empty on a first attempt"
    )
    ruling: Ruling = dspy.OutputField()


class BookAdapterMixin:
    """Append the book to the system message; signature instructions stay the only optimisable text."""

    book: str = ""

    def format_system_message(self, signature):
        base = super().format_system_message(signature)
        return (
            f"{base}\n\n=== REFERENCE BOOK (fixed; read before you start) ===\n{self.book}"
            if self.book
            else base
        )


class BookChatAdapter(BookAdapterMixin, dspy.ChatAdapter):
    pass


class BookJSONAdapter(BookAdapterMixin, dspy.JSONAdapter):
    pass


def adapter(kind: str, book: str):
    a = BookJSONAdapter() if kind == "json" else BookChatAdapter()
    a.book = book
    return a


def seat(sig, instructions: str, lm) -> dspy.Predict:
    p = dspy.Predict(sig.with_instructions(instructions))
    p.lm = lm
    return p


def render_brief(b: Brief | None) -> str:
    if b is None:
        return ""
    lines = [
        f"- {r.metric}={r.value} [{r.scale}] {r.direction}, weight {r.weight}: {r.meaning_here}"
        for r in b.readings
    ]
    return "Readings:\n" + "\n".join(lines) + f"\nGaps: {json.dumps(b.gaps)}\nCase: {b.case}"
