"""Run a prompt variant over the case set and report what the expert understood, used and decided.

  PYTHONPATH=. uv run --frozen --extra optimizer python -m lab.deliberation.run \
      --variant lab/deliberation/variants/lab_t2.json --engine fake --out /tmp/lab-run
  # real models (needs ANTHROPIC_API_KEY in the environment; refuses without a spend cap):
      --engine real --max-usd 5
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import dspy

from .book.house_rules import render as render_rules
from .engines import make_lm, price
from .laws import DICT, check_brief, check_ruling
from .program import INSTRUCTIONS, BriefSig, RulingSig, adapter, render_brief, seat

LAB = Path(__file__).parent
CASES = LAB / "cases" / "synthetic"
BOOK_MD = LAB / "book" / "generated" / "dictionary.md"


class Checked(dspy.Module):
    """One seat with its own form-law retry loop (no dspy.Refine: it forces temperature, DL-264 am. 5)."""

    def __init__(self, predictor, kind: str, retries: int):
        super().__init__()
        self.p, self.kind, self.retries = predictor, kind, retries

    def forward(self, **inputs):
        attempts, feedback = [], ""
        for _ in range(1 + self.retries):
            try:
                out = self.p(**inputs, law_feedback=feedback)
                obj = out.brief if self.kind == "brief" else out.ruling
                v = (
                    check_brief(obj, inputs["packet"], inputs.get("side", "?"))
                    if self.kind == "brief"
                    else check_ruling(obj, inputs["packet"])
                )
            except Exception as e:  # parse failure, provider error: recorded, not hidden
                obj, v = None, None
                attempts.append(
                    {"output": None, "error": f"{type(e).__name__}: {str(e)[:300]}", "violations": []}
                )
                feedback = "Your previous answer could not be parsed. Follow the output structure exactly."
                continue
            attempts.append(
                {"output": obj.model_dump(), "error": None, "violations": [x.__dict__ for x in v]}
            )
            if not v:
                break
            feedback = "\n".join(f"- {x.clause} {x.message}. {x.feedback}" for x in v)
        return dspy.Prediction(final=obj, attempts=attempts)


def estimate(variant: dict, cases: list[dict], book: str) -> tuple[float, float, bool]:
    """(expected $, upper-bound $, all models priced)."""
    exp = up = 0.0
    priced = True
    n_brief = 2 * (variant.get("rounds", 1) if variant["topology"] == "T0" else 1)
    for c in cases:
        tin = (len(book) + len(c["context"]) + 6000) / 4
        for role, n in (("pro", n_brief / 2), ("con", n_brief / 2), ("judge", 1)):
            spec = variant["models"][role]
            p = price(spec["model"])
            if p is None:
                priced = False
                continue
            mt = spec.get("max_tokens", 16000)
            exp += n * (tin * p[0] + 4000 * p[1]) / 1e6
            up += n * (1 + variant.get("retries", 1)) * (tin * p[0] + mt * p[1]) / 1e6
    return exp, up, priced


def run_case(c: dict, variant: dict, lms: dict, book: str) -> dict:
    ins = INSTRUCTIONS[variant["instructions"]]
    r = variant.get("retries", 1)
    pro = Checked(seat(BriefSig, ins["pro"], lms["pro"]), "brief", r)
    con = Checked(seat(BriefSig, ins["con"], lms["con"]), "brief", r)
    judge = Checked(seat(RulingSig, ins["judge"], lms["judge"]), "ruling", r)
    base = {"decision": c["decision"], "packet": c["context"]}
    turns = []
    with dspy.context(adapter=adapter(variant.get("adapter", "chat"), book)):
        if variant["topology"] == "T2":
            par = dspy.Parallel(num_threads=2, disable_progress_bar=True)
            p_out, c_out = par(
                [
                    (
                        pro,
                        dspy.Example(**base, side="pro", other_case="").with_inputs(
                            *base, "side", "other_case"
                        ),
                    ),
                    (
                        con,
                        dspy.Example(**base, side="con", other_case="").with_inputs(
                            *base, "side", "other_case"
                        ),
                    ),
                ]
            )
            turns = [("pro", 1, p_out), ("con", 1, c_out)]
        else:
            p_out = c_out = None
            for rnd in range(1, variant.get("rounds", 1) + 1):
                p_out = pro(**base, side="pro", other_case=render_brief(c_out.final) if c_out else "")
                c_out = con(**base, side="con", other_case=render_brief(p_out.final))
                turns += [("pro", rnd, p_out), ("con", rnd, c_out)]
        j_out = judge(**base, pro_case=render_brief(p_out.final), con_case=render_brief(c_out.final))
    seats = [{"seat": s, "round": n, "attempts": o.attempts} for s, n, o in turns]
    seats.append({"seat": "judge", "round": 1, "attempts": j_out.attempts})
    return {
        "case": c["name"],
        "expert_view": c["expert_view"],
        "decision": c["decision"],
        "seats": seats,
        "ruling": j_out.final.model_dump() if j_out.final else None,
    }


def ledger(lms: dict) -> dict:
    seen, out = set(), {"input_tokens": 0, "output_tokens": 0, "usd": 0.0, "unpriced_calls": 0, "calls": 0}
    for lm in lms.values():
        if id(lm) in seen:
            continue
        seen.add(id(lm))
        for h in lm.history:
            u = h.get("usage") or {}
            ti, to = u.get("prompt_tokens") or 0, u.get("completion_tokens") or 0
            out["calls"] += 1
            out["input_tokens"] += ti
            out["output_tokens"] += to
            p = price(h.get("model") or "")
            if p:
                out["usd"] += (ti * p[0] + to * p[1]) / 1e6
            else:
                out["unpriced_calls"] += 1
    out["usd"] = round(out["usd"], 4)
    return out


def report(results: list[dict], variant: dict, cost: dict) -> str:
    first, final = Counter(), Counter()
    key_reads: dict[str, Counter] = defaultdict(Counter)
    key_errors: Counter = Counter()
    lines = [
        f"# Lab run: {variant['name']}",
        "",
        f"Topology {variant['topology']}, instructions "
        f"`{variant['instructions']}`, book `{variant['book']}`, adapter `{variant.get('adapter', 'chat')}`, "
        f"retries {variant.get('retries', 1)}. Cost: {cost}.",
        "",
        "## Rulings",
        "",
        "| Case | Ruling | Decisive | Market basis? | Expert view (planner draft, to be approved) |",
        "| --- | --- | --- | --- | --- |",
    ]
    for r in results:
        rl = r["ruling"] or {}
        dec = rl.get("decisive", [])
        market = any(DICT.get(k) and DICT[k].pillar != "pm_gate" for k in dec)
        lines.append(
            f"| {r['case']} | {rl.get('ruling', 'FAILED')} | {', '.join(dec)} | {'yes' if market else 'NO'} "
            f"| {r['expert_view'][:110]} |"
        )
        for s in r["seats"]:
            a0, af = s["attempts"][0], s["attempts"][-1]
            for v in a0["violations"]:
                first[v["clause"]] += 1
                if v["clause"] in ("DEC-FORM-01", "DEC-FORM-02"):
                    key_errors[v["metric"]] += 1
            for v in af["violations"]:
                final[v["clause"]] += 1
            first["PARSE"] += a0["error"] is not None
            final["PARSE"] += af["error"] is not None
            for rd in (af["output"] or {}).get("readings", []) + (af["output"] or {}).get("own_readings", []):
                key_reads[rd["metric"]][s["seat"]] += 1
    lines += [
        "",
        "## Form-law violations (first attempt -> after retry)",
        "",
        "| Clause | First | Final |",
        "| --- | --- | --- |",
    ]
    for k in sorted(set(first) | set(final)):
        lines.append(f"| {k} | {first[k]} | {final[k]} |")
    lines += [
        "",
        "## What was read, by whom, and misread how often (first attempts)",
        "",
        "| Key | pro | con | judge | first-attempt misreads |",
        "| --- | --- | --- | --- | --- |",
    ]
    for k in sorted(set(key_reads) | set(key_errors), key=lambda k: (-sum(key_reads[k].values()), k)):
        c = key_reads[k]
        lines.append(f"| `{k}` | {c['pro']} | {c['con']} | {c['judge']} | {key_errors[k]} |")
    unread = sorted(k for k, e in DICT.items() if e.pillar != "pm_gate" and k not in key_reads)
    lines += [
        "",
        f"**Market keys never read by any seat ({len(unread)}):** " + ", ".join(f"`{k}`" for k in unread),
    ]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", required=True)
    ap.add_argument("--engine", choices=["fake", "real"], default="fake")
    ap.add_argument("--out", required=True)
    ap.add_argument("--cases", default="", help="comma-separated case names; default all")
    ap.add_argument("--max-usd", type=float, default=None)
    a = ap.parse_args(argv)
    variant = json.loads(Path(a.variant).read_text())
    if a.engine == "fake":
        variant["models"] = {k: {"model": "fake"} for k in ("pro", "con", "judge")}
    names = [n for n in a.cases.split(",") if n]
    cases = [json.loads(p.read_text()) for p in sorted(CASES.glob("*.json"))]
    cases = [c for c in cases if c["reached_referee"] and (not names or c["name"] in names)]
    book = (BOOK_MD.read_text() + "\n" + render_rules()) if variant["book"] == "system" else ""
    exp, up, priced = estimate(variant, cases, book)
    print(f"{len(cases)} cases; estimated ${exp:.2f} expected, ${up:.2f} upper bound; all priced: {priced}")
    if a.engine == "real" and (a.max_usd is None or exp > a.max_usd or not priced):
        print("REFUSED: a real run needs --max-usd at or above the expected cost, and every model priced.")
        return 2
    dspy.configure_cache(enable_disk_cache=False, enable_memory_cache=False)
    lms = {role: make_lm(spec) for role, spec in variant["models"].items()}
    results = [run_case(c, variant, lms, book) for c in cases]
    cost = ledger(lms)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(
        json.dumps({"variant": variant, "cost": cost, "results": results}, indent=1)
    )
    (out / "report.md").write_text(report(results, variant, cost))
    print(f"wrote {out / 'report.md'}; cost {cost}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
