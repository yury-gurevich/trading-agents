"""Compile the explain prompt the DSPy way: a program, a metric, a trainset, an optimiser, a saved artefact.

GEPA rewrites each seat's INSTRUCTIONS only (the book stays fixed in the system message, outside them),
steered by the explain grader turned into a feedback metric. The feedback names each failed check on its
own line (`CHECK:`) and quotes the dictionary entry for every misread key, because GEPA writes domain facts
into the instruction and cannot see the system-message book (practitioner notes §5).

The cases are split three ways, and the split is fixed before any run:
- train: GEPA reflects on these;
- val: GEPA picks among candidates on these;
- test: held out and never seen by the compile. Seed and compiled prompts are both graded on these, first
  attempt only. That is the result.

  PYTHONPATH=. uv run --frozen --extra optimizer python -m lab.deliberation.explain_compile \
      --variant lab/deliberation/variants/lab_t2_book_complete.json --engine fake --out /tmp/lab/compiled
  # real: --engine real --seats judge --max-metric-calls 24 --max-usd 20 (needs ANTHROPIC_API_KEY)
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import dspy
from dspy.utils.exceptions import LMError

from .book.entries import lookup
from .engines import make_lm, price
from .explain_fake import ExplainFakeEngine, FakeReflection
from .explain_grade import PASS_BAR, grade, passes
from .explain_run import (
    ExplainSeat,
    book_text,
    call_cost,
    explain_case,
    modes,
    report,
)
from .laws import CONTRARIAN_KEYS, entry_text
from .preflight import ProviderAbort
from .program import adapter
from .run import CASES, ledger, packet_of

SPLIT = {
    "train": ["extended_leader", "value_trap", "earnings_inside_hold", "risk_off_high_beta"],
    "val": ["steady_compounder", "correlated_with_holding"],
    "test": [
        "falling_knife",
        "pillars_in_conflict",
    ],  # held out: the hardest reads, never seen by the compile
}
_PARTS = ("coverage", "value", "scale", "concept", "direction", "implied", "critical")


def score_of(g: dict) -> tuple[float, dict]:
    """Half the mean of the graded quantities (a gradient), half the share of pass-bar checks met (the bar)."""
    pn = g["per_number"]
    objectives = {"coverage": g["coverage"]}
    objectives.update({f: 1.0 if pn[f] is None else pn[f] for f in _PARTS[1:]})
    objectives["derivations"] = sum(g["derivations"].values()) / max(1, len(g["derivations"]))
    objectives["pillars"] = sum(g["pillars"].values()) / max(1, len(g["pillars"]))
    objectives["interactions"] = 1.0 if g["interactions_recall"] is None else g["interactions_recall"]
    ok = passes(g)
    score = 0.5 * sum(objectives.values()) / len(objectives) + 0.5 * sum(ok.values()) / len(ok)
    return score, objectives


def feedback_of(g: dict, packet: str, max_keys: int = 25) -> str:
    """One `CHECK:` block per check with an error; every misread key quotes its dictionary entry once."""
    out: list[str] = []
    if g["missing"]:
        out.append(
            f"COVERAGE: {100 * g['coverage']:.0f}% of the required numbers read. Not read: "
            + ", ".join(f"`{k}`" for k in g["missing"])
            + ". Every one must be read (house rule H12); a key printed twice is read twice."
        )
    quoted: set[str] = set()
    for field, head in (
        ("critical", "CRITICAL"),
        ("value", "VALUE"),
        ("scale", "SCALE"),
        ("concept", "CONCEPT"),
        ("direction", "DIRECTION"),
        ("implied", "SUB-SCORE"),
    ):
        bad = [r for r in g["errors"] if r.get(field) is False][:max_keys]
        if not bad:
            continue
        lines = [f"{head}: {len(bad)} wrong."]
        for r in bad:
            f = (
                field
                if field != "critical"
                else ("scale" if r["metric"] not in CONTRARIAN_KEYS else "direction")
            )
            lines.append(
                f"- `{r['metric']}`={r['got']['value']}: you said {r['got'][f]!r}; the code accepts {r['want'][f]!r}."
                + (
                    f" (sub-score expected {r['want']['implied']})"
                    if field == "critical" and r["want"]["implied"] is not None
                    else ""
                )
            )
            if r["metric"] not in quoted and lookup(r["metric"]):
                quoted.add(r["metric"])
                lines.append(f"  Dictionary: {entry_text(r['metric'])}")
        if field == "critical":
            lines.append(
                "  H7: contrarian oscillators score oversold as bullish, but oversold in a downtrend is not support: read "
                "them with the trend. H11: pe, roe, ... in quant_metrics are "
                "0-100 sub-scores; the raw ratios carry vendor names."
            )
        out.append("\n".join(lines))
    wrong_d = [(n, v) for n, v in g["derivation_values"].items() if not g["derivations"][n]]
    if wrong_d:
        out.append(
            "DERIVATIONS: "
            + "; ".join(
                f"{n}: you computed {v['got']}, the code computes {v['want']:.4g}" for n, v in wrong_d
            )
            + ". Rules: technical_score = 0.8 x mean(indicator sub-scores)/100 + 0.2 x rs_score/100; "
            "fundamental_score = mean(fundamental sub-scores)/100; composite = weighted mean of the pillars "
            "present (0.5/0.3/0.2), renormalised; confidence = 0.3 + 0.6 x composite; applied_stop_pct = 2 x "
            "atr_pct; reward/risk = applied_target_pct / applied_stop_pct."
        )
    wrong_p = [(n, v) for n, v in g["pillar_values"].items() if not g["pillars"][n]]
    if wrong_p:
        out.append(
            "PILLARS: "
            + "; ".join(
                f"{n}: you said {v['got']}, its score's band implies {' or '.join(v['want'])}"
                for n, v in wrong_p
            )
        )
    missed = [m for m, f in zip(g["expected_interactions"], g["interactions_found"], strict=True) if not f]
    if missed:
        out.append(
            "INTERACTIONS: not named: " + "; ".join(f"{a} vs {b} ({' or '.join(r)})" for a, b, r in missed)
        )
    return "\n\n".join(out) or "All checks met."


class GuardedSeat(ExplainSeat):
    """The seat as GEPA sees it: a provider error leaves the compile instead of being scored as an answer."""

    def forward(self, decision: str, packet: str):
        try:
            return super().forward(decision=decision, packet=packet)
        except LMError as e:
            raise ProviderAbort(f"{type(e).__name__}: {str(e)[:300]}") from e


def make_metric():
    def metric(gold, pred, trace=None, pred_name=None, pred_trace=None):
        ex = getattr(pred, "explanation", None)
        if ex is None:
            return dspy.Prediction(score=0.0, feedback="The answer could not be parsed into an Explanation.")
        g = grade(ex, gold.packet, gold.case, gold.mode)
        score, objectives = score_of(g)
        return dspy.Prediction(score=score, feedback=feedback_of(g, gold.packet), objective_scores=objectives)

    return metric


def examples(cases: list[dict], names: list[str], variant: dict, mode: str) -> list[dspy.Example]:
    by = {c["name"]: c for c in cases}
    return [
        dspy.Example(
            decision=by[n]["decision"], packet=packet_of(by[n], variant), case=n, mode=mode
        ).with_inputs("decision", "packet")
        for n in names
    ]


def estimate(variant, cases, book, seats, calls, minibatch) -> tuple[float, float, bool]:
    by = {c["name"]: c for c in cases}
    m = modes(variant)
    exp = up = 0.0
    refl = make_reflection_spec(variant)
    rp = price(refl["model"])
    for s in seats:
        seen = [call_cost(variant, by[n], s, m[s], book) for n in SPLIT["train"] + SPLIT["val"]]
        test = [call_cost(variant, by[n], s, m[s], book) for n in SPLIT["test"]]
        if None in seen or None in test or rp is None:
            return 0.0, 0.0, False
        avg_e, avg_u = sum(x[0] for x in seen) / len(seen), sum(x[1] for x in seen) / len(seen)
        n_refl = calls // (2 * minibatch) + 1
        # a reflection reads `minibatch` examples (packet + output + feedback) and writes an instruction
        r_in = minibatch * (len(packet_of(by[SPLIT["train"][0]], variant)) / 4 + 15000) + 4000
        r_e, r_u = (
            (r_in * rp[0] + 4000 * rp[1]) / 1e6,
            (r_in * rp[0] + refl.get("max_tokens", 16000) * rp[1]) / 1e6,
        )
        exp += calls * avg_e + n_refl * r_e + 2 * sum(x[0] for x in test)
        up += calls * avg_u + n_refl * r_u + 2 * sum(x[1] for x in test)
    return exp, up, True


def make_reflection_spec(variant: dict) -> dict:
    return variant.get("reflection") or {"model": variant["models"]["judge"]["model"], "max_tokens": 32000}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", required=True)
    ap.add_argument("--engine", choices=["fake", "real"], default="fake")
    ap.add_argument("--out", required=True)
    ap.add_argument("--seats", default="judge,pro,con", help="compiled in this order; the judge first")
    ap.add_argument("--max-metric-calls", type=int, default=24)
    ap.add_argument("--minibatch", type=int, default=2)
    ap.add_argument("--max-usd", type=float, default=None)
    a = ap.parse_args(argv)
    variant = json.loads(Path(a.variant).read_text())
    seats = [s for s in a.seats.split(",") if s]
    cases = [json.loads(p.read_text()) for p in sorted(CASES.glob("*.json"))]
    cases = [c for c in cases if c["reached_referee"]]
    book = book_text(variant)
    exp, up, priced = estimate(variant, cases, book, seats, a.max_metric_calls, a.minibatch)
    print(
        f"compile {seats}, {a.max_metric_calls} metric calls per seat: estimated ${exp:.2f} expected, ${up:.2f} upper bound"
    )
    if a.engine == "real":
        if a.max_usd is None or exp > a.max_usd or not priced:
            print(
                "REFUSED: a real compile needs --max-usd at or above the expected cost, and every model priced."
            )
            return 2
        student = {s: make_lm(variant["models"][s]) for s in seats}
        reflection = make_lm(make_reflection_spec(variant))
    else:
        tickers = {c["ticker"]: c["name"] for c in cases}
        fake = dspy.LM("fake/student", engine=ExplainFakeEngine("instructed", tickers), cache=False)
        student = {s: fake for s in seats}
        reflection = dspy.LM("fake/reflection", engine=FakeReflection(), cache=False)
    dspy.configure_cache(enable_disk_cache=False, enable_memory_cache=False)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    m = modes(variant)
    summary: dict = {
        "variant": variant["name"],
        "engine": a.engine,
        "book_sha256": hashlib.sha256(book.encode()).hexdigest(),
        "split": SPLIT,
        "pass_bar": PASS_BAR,
        "max_metric_calls": a.max_metric_calls,
        "seats": {},
    }
    metric = make_metric()
    lines = [f"# Compiled explain prompt: {variant['name']} ({a.engine})", ""]
    try:
        for s in seats:
            compile_seat(s, a, variant, cases, book, m, student, reflection, metric, out, summary, lines)
    except ProviderAbort as e:
        summary["aborted"] = f"provider error, nothing scored from it: {e}"
        print(f"ABORTED: a provider call failed during the compile; it was not scored. {e}")
    lms = {**{f"s_{k}": v for k, v in student.items()}, "reflection": reflection}
    summary["cost"] = ledger(lms)
    (out / "compiled.json").write_text(json.dumps(summary, indent=1))
    (out / "report.md").write_text("\n".join(lines + [f"Cost: {summary['cost']}", ""]))
    print(f"wrote {out / 'report.md'}; cost {summary['cost']}")
    for s, d in summary["seats"].items():
        print(
            f"  {s}: held-out pass {d['test_seed']['passes']} -> {d['test_compiled']['passes']} of "
            f"{len(SPLIT['test'])}; book intact {d['book_intact']}"
        )
    return 3 if "aborted" in summary else 0


def compile_seat(s, a, variant, cases, book, m, student, reflection, metric, out, summary, lines) -> None:
    dspy.configure(lm=student[s], adapter=adapter(variant.get("adapter", "chat"), book))
    seed = GuardedSeat(s, m[s])
    gepa = dspy.GEPA(
        metric=metric,
        max_metric_calls=a.max_metric_calls,
        reflection_lm=reflection,
        reflection_minibatch_size=a.minibatch,
        use_merge=False,
        num_threads=1,
        track_stats=True,
        seed=0,
        log_dir=str(out / "gepa" / s),
    )
    best = gepa.compile(
        seed,
        trainset=examples(cases, SPLIT["train"], variant, m[s]),
        valset=examples(cases, SPLIT["val"], variant, m[s]),
    )
    best.save(str(out / f"{s}.json"))
    r = best.detailed_results
    # the held-out result: the seed and the compiled prompt, first attempt only, on cases the compile never saw
    test = [c for c in cases if c["name"] in SPLIT["test"]]
    before = [explain_case(c, variant, {s: seed}, book) for c in test]
    after = [explain_case(c, variant, {s: best}, book) for c in test]
    (out / f"test_{s}_seed.md").write_text(report(before, variant, f"{a.engine}, seed prompt", {}))
    (out / f"test_{s}_compiled.md").write_text(report(after, variant, f"{a.engine}, compiled prompt", {}))

    def tally(rs, seat=s):
        return sum(all(r["seats"][seat]["pass"].values()) for r in rs), [
            round(score_of(r["seats"][seat]["grade"])[0], 3) if r["seats"][seat].get("grade") else 0.0
            for r in rs
        ]

    (bp, bs), (ap_, as_) = tally(before), tally(after)
    system = adapter("chat", book).format(best.explain.signature, [], {"decision": "x", "packet": "y"})[0][
        "content"
    ]
    summary["seats"][s] = {
        "seed_instructions": seed.explain.signature.instructions,
        "compiled_instructions": best.explain.signature.instructions,
        "candidates": len(r.candidates),
        "val_scores": [round(x, 3) for x in r.val_aggregate_scores],
        "test_seed": {"passes": bp, "scores": bs},
        "test_compiled": {"passes": ap_, "scores": as_},
        "book_intact": book in system,
    }
    lines += [
        f"## {s}",
        "",
        f"- candidates {len(r.candidates)}; val scores {summary['seats'][s]['val_scores']}",
        f"- **held out ({', '.join(SPLIT['test'])})**: seed {bp}/{len(test)} pass, scores {bs} -> "
        f"compiled {ap_}/{len(test)} pass, scores {as_}",
        f"- book intact in the system message: {book in system}",
        "",
        "Compiled instruction:",
        "",
        "```text",
        best.explain.signature.instructions,
        "```",
        "",
    ]


if __name__ == "__main__":
    raise SystemExit(main())
