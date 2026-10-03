"""Iteration 1, step 1: is the prompt valid, and does it carry ALL the quant data? ($0, no model call)

For every case and seat it renders the exact messages DSPy would send, then checks:
  A. every number the analyst computed is in the packet, with the same value;
  B. the packet reaches the user message intact;
  C. every number in the packet has a dictionary entry, and that entry is in the system message;
  D. every house rule, the role instructions and the output schema are in the system message;
  E. the output ceiling leaves room for one reading per required number.
It also lists what the production packet withholds (present only in the complete packet), and writes
the rendered prompts to --out so they can be read.

  PYTHONPATH=. uv run --frozen --extra optimizer python -m lab.deliberation.prompt_audit \
      --variant lab/deliberation/variants/lab_t2_book_complete.json --out /tmp/lab/prompts
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .book.entries import lookup
from .book.house_rules import RULES
from .book.house_rules import render as render_rules
from .laws import _same, packet_values, required_numbers
from .program import INSTRUCTIONS, BriefSig, RulingSig, adapter
from .run import BOOK_MD, CASES, COVERAGE, packet_of


def seat_messages(c: dict, variant: dict, seat: str, book: str) -> list[dict]:
    packet = packet_of(c, variant)
    a = adapter(variant.get("adapter", "chat"), book)
    ins = INSTRUCTIONS[variant["instructions"]][seat]
    if seat == "judge":
        inputs = {
            "decision": c["decision"],
            "packet": packet,
            "pro_case": "(pro case)",
            "con_case": "(con case)",
        }
        sig = RulingSig.with_instructions(ins)
    else:
        inputs = {"decision": c["decision"], "packet": packet, "side": seat, "other_case": ""}
        sig = BriefSig.with_instructions(ins)
    return a.format(sig, [], {**inputs, "law_feedback": ""})


def audit_case(c: dict, variant: dict, book: str) -> dict:
    packet = packet_of(c, variant)
    pv = packet_values(packet)
    findings: list[str] = []
    # A. every analyst-computed metric is presented, with its value
    for k, v in sorted(c["metrics"].items()):
        shown = [o.value for o in pv.get(k, [])]
        if not shown:
            findings.append(f"A: analyst metric `{k}` is not in the packet")
        elif not any(_same(s, f"{v:.4g}") or _same(s, repr(v)) for s in shown):
            findings.append(f"A: `{k}` computed {v:.6g} but the packet shows {shown}")
    seats = {}
    debaters, judge_cov = COVERAGE[variant.get("coverage", "decision_rule")]
    for seat in ("pro", "con", "judge"):
        msgs = seat_messages(c, variant, seat, book)
        system, user = msgs[0]["content"], msgs[-1]["content"]
        # B. the packet is intact in the user message
        if packet not in user:
            findings.append(f"B: {seat}: the packet is not intact in the user message")
        # C. every number is defined, and its definition reaches the model
        mode = judge_cov if seat == "judge" else debaters
        req = required_numbers(packet, evidence_only=mode == "evidence")
        for key in req:
            e = lookup(key)
            if e is None:
                findings.append(f"C: {seat}: `{key}` has no dictionary entry")
            elif book and f"`{e.key}`" not in system:
                findings.append(f"C: {seat}: the entry for `{key}` is not in the system message")
        # D. rules, instructions, schema
        if book:
            findings += [f"D: {seat}: house rule {r.id} missing" for r in RULES if f"- {r.id}:" not in system]
        if INSTRUCTIONS[variant["instructions"]][seat].split(".")[0] not in system:
            findings.append(f"D: {seat}: role instructions missing")
        if "must adhere to the JSON schema" not in system or "meaning_here" not in system:
            findings.append(f"D: {seat}: output schema missing")
        # E. room for one reading per required number (about 60 tokens each, plus the case)
        n = sum(len(g) for g in req.values())
        need_out = 60 * n + 1500
        ceiling = variant["models"][seat].get("max_tokens", 16000)
        if need_out > 0.75 * ceiling:
            findings.append(f"E: {seat}: ~{need_out} output tokens needed against a {ceiling} ceiling")
        seats[seat] = {
            "system_chars": len(system),
            "user_chars": len(user),
            "approx_input_tokens": (len(system) + len(user)) // 4,
            "numbers_to_read": n,
            "approx_output_tokens": need_out,
            "messages": msgs,
        }
    prod = required_numbers(c["context"])
    full = required_numbers(c["context"] + "\n" + c.get("supplement", ""))
    withheld = sorted(k for k in full if k not in prod)
    return {"case": c["name"], "findings": findings, "seats": seats, "withheld_in_production": withheld}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    variant = json.loads(Path(a.variant).read_text())
    book = (BOOK_MD.read_text() + "\n" + render_rules()) if variant["book"] == "system" else ""
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    cases = [json.loads(p.read_text()) for p in sorted(CASES.glob("*.json"))]
    total = 0
    for c in (c for c in cases if c["reached_referee"]):
        r = audit_case(c, variant, book)
        total += len(r["findings"])
        s = r["seats"]
        print(
            f"{r['case']:24s} findings {len(r['findings']):2d} | read pro/con/judge "
            f"{s['pro']['numbers_to_read']}/{s['con']['numbers_to_read']}/{s['judge']['numbers_to_read']} | "
            f"judge input ~{s['judge']['approx_input_tokens']} tok | withheld in production: {len(r['withheld_in_production'])}"
        )
        for f in r["findings"]:
            print("    ", f)
        for seat, d in s.items():
            text = "\n\n".join(f"===== {m['role'].upper()} =====\n{m['content']}" for m in d["messages"])
            (out / f"{r['case']}__{seat}.md").write_text(text)
    print(f"\n{'VALID: no findings' if total == 0 else f'{total} FINDINGS'}; rendered prompts in {out}")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
