"""Iteration 1, step 2: do the deliberators UNDERSTAND the data? (explain, do not decide)

Each seat (pro, con, judge) gets the complete packet, the book in the system message, and one task:
explain the data. (a) Every number as a financial indicator: its kind, unit, meaning here, direction for this
buy, and, for a raw indicator our code scores, the sub-score it maps to. (b) The numbers in combination:
reproduce the six aggregates from their parts, give a verdict per pillar, and name where numbers confirm,
contradict or qualify one another, and the situation the whole describes. Graded by code against keys computed
from the fleet's own scorers (`explain_grade.py`), FIRST attempt only: no feedback, no retry.

  PYTHONPATH=. uv run --frozen --extra optimizer python -m lab.deliberation.explain_run \
      --variant lab/deliberation/variants/lab_t2_book_complete.json --engine fake-good --out /tmp/lab/explain
  # --engine fake-flawed and fake-hedging must FAIL; --compiled DIR evaluates a compiled prompt; --engine real needs --max-usd (and ANTHROPIC_API_KEY)
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import dspy

from .book.house_rules import render as render_rules
from .engines import make_lm, price
from .explain_fake import ExplainFakeEngine
from .explain_grade import EXPECTED_INTERACTIONS, PASS_BAR, grade, passes
from .explain_models import Explanation
from .laws import required_numbers
from .program import adapter
from .run import BOOK_MD, CASES, COVERAGE, ledger, packet_of

QUALITIES = ("good", "flawed", "hedging", "instructed")
ROLE = {
    "pro": "You are the PRO deliberator on a proposed stock purchase; later you will argue FOR it.",
    "con": "You are the CON deliberator on a proposed stock purchase; later you will argue AGAINST it.",
    "judge": "You are the JUDGE, the expert who will decide on a proposed stock purchase.",
}
EXPLAIN = (
    " Before anyone argues or decides, prove that you understand the evidence. Do not argue and do not decide."
    " (1) `interpretations`: one per number you must read ({scope}; house rule H12): the exact packet key, the"
    " value copied exactly, its scale per the dictionary, its indicator family, what it says about THIS stock in"
    " THIS system, its direction for buying now, and, for a raw indicator our code scores, the 0-100 sub-score the"
    " dictionary's bands assign to this value (null otherwise). A key that appears twice with different meanings"
    " or units is read twice."
    " (2) `derivations`: reproduce each of technical_score, fundamental_score, composite_score, confidence_score,"
    " applied_stop_pct and reward_risk_ratio from its parts, with the packet's own numbers and the dictionary's"
    " rules, and give your computed value."
    " (3) `pillars`: one verdict per pillar, with the keys that decide it."
    " (4) `interactions`: every place where numbers confirm, contradict or qualify one another, and what they"
    " mean TOGETHER for this stock."
    " (5) `situation`: what market situation the whole picture describes, in two or three sentences; `overall`:"
    " how the whole bears on buying now."
)
SCOPE = {
    "all": "EVERY number in the packet",
    "evidence": "every number of evidence; you may skip numbers the dictionary marks bookkeeping",
}


class ExplainSig(dspy.Signature):
    """Explain the evidence."""

    decision: str = dspy.InputField(desc="the PM-approved order under review")
    packet: str = dspy.InputField(desc="the evidence packet")
    explanation: Explanation = dspy.OutputField()


def book_text(variant: dict) -> str:
    return (BOOK_MD.read_text() + "\n" + render_rules()) if variant["book"] == "system" else ""


def instructions(seat: str, mode: str) -> str:
    return ROLE[seat] + EXPLAIN.format(scope=SCOPE[mode])


def modes(variant: dict) -> dict[str, str]:
    debaters, judge = COVERAGE[variant.get("coverage", "decision_rule")]
    return {"pro": debaters, "con": debaters, "judge": judge}


def call_cost(variant: dict, c: dict, s: str, mode: str, book: str) -> tuple[float, float] | None:
    """(expected $, upper-bound $) of one explain call; None if the model is unpriced."""
    packet = packet_of(c, variant)
    n = sum(len(g) for g in required_numbers(packet, mode == "evidence").values())
    t_in = (len(book) + len(packet) + 3000) / 4
    t_out = 90 * n + 2500 + 3000  # interpretations + combination + a thinking allowance
    spec = variant["models"][s]
    p = price(spec["model"])
    if p is None:
        return None
    mt = spec.get("max_tokens", 16000)
    return (t_in * p[0] + min(t_out, mt) * p[1]) / 1e6, (t_in * p[0] + mt * p[1]) / 1e6


def estimate(variant: dict, cases: list[dict], book: str) -> tuple[float, float, bool]:
    exp = up = 0.0
    priced = True
    for c in cases:
        for s, mode in modes(variant).items():
            cc = call_cost(variant, c, s, mode, book)
            if cc is None:
                priced = False
                continue
            exp, up = exp + cc[0], up + cc[1]
    return exp, up, priced


class ExplainSeat(dspy.Module):
    """One seat's explainer: the unit DSPy compiles (GEPA rewrites `explain`'s instructions only)."""

    def __init__(self, seat: str, mode: str):
        super().__init__()
        self.explain = dspy.Predict(ExplainSig.with_instructions(instructions(seat, mode)))

    def forward(self, decision: str, packet: str):
        return self.explain(decision=decision, packet=packet)


def seat_program(seat: str, mode: str, lm, compiled: Path | None = None) -> ExplainSeat:
    """The seed program, or the compiled one saved by explain_compile (`<dir>/<seat>.json`)."""
    prog = ExplainSeat(seat, mode)
    if compiled is not None and (compiled / f"{seat}.json").exists():
        prog.load(str(compiled / f"{seat}.json"))
    prog.explain.lm = lm
    return prog


def explain_case(c: dict, variant: dict, programs: dict, book: str) -> dict:
    packet = packet_of(c, variant)
    seats = {}
    with dspy.context(adapter=adapter(variant.get("adapter", "chat"), book)):
        for s, mode in modes(variant).items():
            if s not in programs:
                continue
            try:
                ex = programs[s](decision=c["decision"], packet=packet).explanation
                g = grade(ex, packet, c["name"], mode)
                seats[s] = {
                    "mode": mode,
                    "error": None,
                    "grade": g,
                    "pass": passes(g),
                    "output": ex.model_dump(),
                }
            except Exception as e:  # recorded, not hidden: a parse failure is a failed first attempt
                seats[s] = {
                    "mode": mode,
                    "error": f"{type(e).__name__}: {str(e)[:300]}",
                    "pass": {"parsed": False},
                }
    return {"case": c["name"], "expert_view": c["expert_view"], "seats": seats}


def _pct(x) -> str:
    return "n/a" if x is None else f"{100 * x:.0f}%"


def report(results: list[dict], variant: dict, engine: str, cost: dict) -> str:
    lines = [
        f"# Iteration 1, explain: {variant['name']} ({engine})",
        "",
        f"Packet `{variant.get('packet', 'production')}`, coverage `{variant.get('coverage', 'decision_rule')}`, "
        f"first attempt only. Cost: {cost}.",
        "",
        f"Pass bar (pre-registered, DL-264 amendment 9): {PASS_BAR}",
        "",
        "## (a) each number as a financial indicator, and (b) in combination",
        "",
        "| Case | Seat | Read | Value | Scale | Concept | Direction | Sub-score | Critical | Derivations | Pillars "
        "| Interactions | PASS |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    fails, misread, deriv_wrong = Counter(), Counter(), Counter()
    n_pass = n = 0
    for r in results:
        for s, d in r["seats"].items():
            n += 1
            if d["error"]:
                lines.append(f"| {r['case']} | {s} | PARSE FAILED: {d['error'][:80]} ||||||||||| FAIL |")
                fails["parse"] += 1
                continue
            g, ok = d["grade"], d["pass"]
            pn = g["per_number"]
            n_pass += all(ok.values())
            fails.update(k for k, v in ok.items() if not v)
            for e in g["errors"]:
                misread[e["metric"]] += 1
            deriv_wrong.update(k for k, v in g["derivations"].items() if not v)
            lines.append(
                f"| {r['case']} | {s} | {_pct(g['coverage'])} | {_pct(pn['value'])} | {_pct(pn['scale'])} "
                f"| {_pct(pn['concept'])} | {_pct(pn['direction'])} | {_pct(pn['implied'])} | {_pct(pn['critical'])} "
                f"| {sum(g['derivations'].values())}/{len(g['derivations'])} "
                f"| {sum(g['pillars'].values())}/{len(g['pillars'])} | {_pct(g['interactions_recall'])} "
                f"| {'PASS' if all(ok.values()) else 'FAIL: ' + ', '.join(k for k, v in ok.items() if not v)} |"
            )
    lines += [
        "",
        f"**{n_pass} of {n} seat-cases pass.** Failed checks: "
        + (", ".join(f"{k} ({v})" for k, v in fails.most_common()) or "none"),
        "",
        "Derivations most often wrong: "
        + (", ".join(f"{k} ({v})" for k, v in deriv_wrong.most_common()) or "none"),
        "",
        "Keys most often misread: "
        + (", ".join(f"`{k}` ({v})" for k, v in misread.most_common(15)) or "none"),
        "",
        "## The situation each seat saw, beside the expert view (operator-approved)",
        "",
    ]
    for r in results:
        lines += [f"### {r['case']}", "", f"- **expert view:** {r['expert_view']}"]
        for s, d in r["seats"].items():
            if d["error"]:
                continue
            g = d["grade"]
            exp_int = EXPECTED_INTERACTIONS.get(r["case"], [])
            hit = ", ".join(
                f"{'+' if f else '-'}{'/'.join(sorted(rels))}"
                for (_a, _b, rels), f in zip(exp_int, g["interactions_found"], strict=True)
            )
            lines.append(
                f"- **{s}** ({g['overall']}; expected interactions found: {hit or 'none expected'}): {g['situation']}"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def fake_lms(quality: str, cases: list[dict]) -> dict:
    eng = ExplainFakeEngine(quality, {c["ticker"]: c["name"] for c in cases})
    lm = dspy.LM("fake/explainer", engine=eng, cache=False)
    return {s: lm for s in ("pro", "con", "judge")}


def check_compiled(compiled: Path | None, book: str) -> str | None:
    """A compiled prompt was optimised against one book; refuse it with another (the book is not in it)."""
    if compiled is None:
        return None
    meta = json.loads((compiled / "compiled.json").read_text())
    if meta["book_sha256"] != hashlib.sha256(book.encode()).hexdigest():
        return f"REFUSED: {compiled} was compiled against a different book; recompile."
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", required=True)
    ap.add_argument("--engine", choices=["real", *(f"fake-{q}" for q in QUALITIES)], default="fake-good")
    ap.add_argument("--out", required=True)
    ap.add_argument("--cases", default="", help="comma-separated case names; default all")
    ap.add_argument("--seats", default="pro,con,judge")
    ap.add_argument(
        "--compiled", default=None, help="a directory written by explain_compile; default the seed"
    )
    ap.add_argument("--max-usd", type=float, default=None)
    a = ap.parse_args(argv)
    variant = json.loads(Path(a.variant).read_text())
    names = [x for x in a.cases.split(",") if x]
    seats = [x for x in a.seats.split(",") if x]
    cases = [json.loads(p.read_text()) for p in sorted(CASES.glob("*.json"))]
    cases = [c for c in cases if c["reached_referee"] and (not names or c["name"] in names)]
    book = book_text(variant)
    compiled = Path(a.compiled) if a.compiled else None
    if refusal := check_compiled(compiled, book):
        print(refusal)
        return 2
    if a.engine == "real":
        exp, up, priced = estimate(variant, cases, book)
        print(
            f"{len(cases)} cases x 3 seats; estimated ${exp:.2f} expected, ${up:.2f} upper bound; priced: {priced}"
        )
        if a.max_usd is None or exp > a.max_usd or not priced:
            print(
                "REFUSED: a real run needs --max-usd at or above the expected cost, and every model priced."
            )
            return 2
        lms = {s: make_lm(variant["models"][s]) for s in ("pro", "con", "judge")}
    else:
        lms = fake_lms(a.engine.split("-", 1)[1], cases)
    dspy.configure_cache(enable_disk_cache=False, enable_memory_cache=False)
    m = modes(variant)
    programs = {s: seat_program(s, m[s], lms[s], compiled) for s in seats}
    results = [explain_case(c, variant, programs, book) for c in cases]
    cost = ledger(lms)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    label = f"{a.engine}, {'compiled ' + str(compiled) if compiled else 'seed prompt'}"
    (out / "results.json").write_text(
        json.dumps({"variant": variant, "engine": label, "cost": cost, "results": results}, indent=1)
    )
    (out / "report.md").write_text(report(results, variant, label, cost))
    ok = sum(all(d["pass"].values()) for r in results for d in r["seats"].values())
    print(f"{ok}/{len(seats) * len(results)} seat-cases pass; wrote {out / 'report.md'}; cost {cost}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
