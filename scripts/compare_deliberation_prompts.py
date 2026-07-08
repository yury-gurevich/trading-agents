"""Compare champion deliberation prompts against compiled role artifacts.

Agent: tooling
Role: report S119 prompt quality metrics per role and hard-fail on golden
      firewall regressions.
External I/O: stdout; optional LLM provider calls when --real is supplied.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.deliberate import build_role_llms  # noqa: E402
from scripts.deliberation_eval import _CLASS1, _build  # noqa: E402

from kernel import (  # noqa: E402
    DEFAULT_DELIBERATION_PROMPTS,
    DeliberationPrompts,
    LLMJudgeScorer,
    PromptArtifact,
    check_robust,
    load_deliberation_prompt_artifacts,
    pass_rate,
    prompts_from_artifacts,
    run_debates,
    score_debate,
    score_understanding,
    understanding_rate,
)
from orchestration.packs.trading_parameter_truths import (  # noqa: E402
    TRADING_PARAMETER_TRUTHS,
)


@dataclass(frozen=True)
class PromptSetMetrics:
    """Measured quality for one prompt bundle."""

    keyword_pass_rate: float
    judge_pass_rate: float
    understanding: float
    stability: float
    firewall_passed: bool
    regressed: tuple[str, ...]


@dataclass(frozen=True)
class RoleComparison:
    """Champion-vs-compiled result for one role artifact."""

    role: str
    champion: PromptSetMetrics
    challenger: PromptSetMetrics


class _FakeReportLLM:
    """Deterministic fake for CI-safe report execution."""

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        del user, tool_schema
        if '"caught": true' in system or "SPECIFIC FLAW" in system:
            return '{"caught": true}'
        if "JUDGE" in system or '"ruling"' in system:
            return '{"ruling": "revise", "rationale": "specific flaw caught"}'
        if "CHALLENGER" in system:
            return (
                "max_daily_move_sigma = pooled cross-sectional batch gate; "
                "base_min_confidence = regime-modulated baseline; "
                "signal_diversity_slack = unused pillar rationale. "
                "pooled cross-sectional calendar trading day name-correlation "
                "fixed-fraction beta weight 0.00 shadow does not feed."
            )
        return "Defends the decision while citing the supplied evidence."


def _class1_cases() -> tuple[object, ...]:
    return _build(_CLASS1, grounded=True)


def _golden_passing(golden_path: Path) -> frozenset[str]:
    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    return frozenset(str(name) for name in golden["passing"])


def _transcript_text(debate: object) -> str:
    return " ".join(turn.text for turn in debate.transcript)


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _stability(
    debate_runs: tuple[tuple[object, ...], ...],
    cases: tuple[object, ...],
    golden_passing: frozenset[str],
) -> float:
    stable = 0
    for index, case in enumerate(cases):
        if case.name not in golden_passing:
            continue
        verdicts = {run[index].verdict.ruling for run in debate_runs}
        stable += int(len(verdicts) == 1)
    return stable / len(golden_passing) if golden_passing else 0.0


def _write_transcripts(
    transcript_dir: Path | None,
    label: str,
    debate_runs: tuple[tuple[object, ...], ...],
    cases: tuple[object, ...],
    keyword_runs: tuple[tuple[object, ...], ...],
    judge_runs: tuple[tuple[object, ...], ...],
) -> None:
    if transcript_dir is None:
        return
    transcript_dir.mkdir(parents=True, exist_ok=True)
    lines = [f"# Deliberation Transcripts: {label}", ""]
    for run_index, (debates, keyword_scores, judge_scores) in enumerate(
        zip(debate_runs, keyword_runs, judge_runs, strict=True), start=1
    ):
        lines.extend((f"## Run {run_index}", ""))
        for case, debate, keyword_score, judge_score in zip(
            cases, debates, keyword_scores, judge_scores, strict=True
        ):
            lines.extend(
                (
                    f"### {case.name}",
                    "",
                    f"Decision: {case.proposition.decision}",
                    "",
                    f"Context: {case.proposition.context}",
                    "",
                )
            )
            for turn in debate.transcript:
                lines.extend((f"**{turn.role} r{turn.round}**", "", turn.text, ""))
            lines.extend(
                (
                    f"Verdict: {debate.verdict.ruling} - {debate.verdict.rationale}",
                    "",
                    f"Keyword scorer passed: {keyword_score.passed}",
                    f"LLM-judge scorer passed: {judge_score.passed}",
                    "",
                )
            )
    (transcript_dir / f"{label}.md").write_text(
        "\n".join(lines).rstrip() + "\n", encoding="utf-8"
    )


def evaluate_prompt_set(
    *,
    debate_llm: object,
    debate_judge_llm: object,
    scorer_judge_llm: object,
    prompts: DeliberationPrompts,
    rounds: int,
    repeats: int,
    threshold: float,
    golden_passing: frozenset[str],
    transcript_label: str = "",
    transcript_dir: Path | None = None,
) -> PromptSetMetrics:
    """Evaluate one prompt set on Class-1 grounded cases and stability repeats."""
    cases = _class1_cases()
    scorer = LLMJudgeScorer(scorer_judge_llm)
    debate_runs = tuple(
        run_debates(
            debate_llm,
            cases,
            max_rounds=rounds,
            judge_llm=debate_judge_llm,
            prompts=prompts,
        )
        for _ in range(repeats)
    )
    keyword_runs = tuple(
        tuple(
            score_debate(debate, case) for debate, case in zip(run, cases, strict=True)
        )
        for run in debate_runs
    )
    judge_runs = tuple(
        tuple(scorer(debate, case) for debate, case in zip(run, cases, strict=True))
        for run in debate_runs
    )
    understanding = [
        understanding_rate(
            score_understanding(_transcript_text(debate), TRADING_PARAMETER_TRUTHS)
        )
        for run in debate_runs
        for debate in run
    ]
    firewall = check_robust(judge_runs, golden_passing, threshold=threshold)
    _write_transcripts(
        transcript_dir,
        transcript_label,
        debate_runs,
        cases,
        keyword_runs,
        judge_runs,
    )
    return PromptSetMetrics(
        keyword_pass_rate=_mean([pass_rate(run) for run in keyword_runs]),
        judge_pass_rate=_mean([pass_rate(run) for run in judge_runs]),
        understanding=_mean(understanding),
        stability=_stability(debate_runs, cases, golden_passing),
        firewall_passed=firewall.passed,
        regressed=firewall.regressed,
    )


def compare_roles(
    *,
    artifacts: dict[str, PromptArtifact],
    debate_llm: object,
    debate_judge_llm: object,
    scorer_judge_llm: object,
    rounds: int,
    repeats: int,
    threshold: float,
    golden_path: Path,
    transcript_dir: Path | None = None,
) -> tuple[RoleComparison, ...]:
    """Compare champion prompts with one compiled role overlaid at a time."""
    golden_passing = _golden_passing(golden_path)
    champion = evaluate_prompt_set(
        debate_llm=debate_llm,
        debate_judge_llm=debate_judge_llm,
        scorer_judge_llm=scorer_judge_llm,
        prompts=DEFAULT_DELIBERATION_PROMPTS,
        rounds=rounds,
        repeats=repeats,
        threshold=threshold,
        golden_passing=golden_passing,
        transcript_label="champion",
        transcript_dir=transcript_dir,
    )
    return tuple(
        RoleComparison(
            role=role,
            champion=champion,
            challenger=evaluate_prompt_set(
                debate_llm=debate_llm,
                debate_judge_llm=debate_judge_llm,
                scorer_judge_llm=scorer_judge_llm,
                prompts=prompts_from_artifacts({role: artifacts[role]}),
                rounds=rounds,
                repeats=repeats,
                threshold=threshold,
                golden_passing=golden_passing,
                transcript_label=f"artifact-{role}",
                transcript_dir=transcript_dir,
            ),
        )
        for role in ("defender", "challenger", "judge")
    )


def _pct(value: float) -> str:
    return f"{value:.0%}"


def _pass_pair(metrics: PromptSetMetrics) -> str:
    return f"{_pct(metrics.keyword_pass_rate)}/{_pct(metrics.judge_pass_rate)}"


def format_table(comparisons: tuple[RoleComparison, ...]) -> str:
    """Render the per-role champion-vs-challenger table."""
    lines = [
        "| role | champion pass kw/judge | challenger pass kw/judge | "
        "champion understanding | challenger understanding | champion stability | "
        "challenger stability | firewall |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in comparisons:
        verdict = "PASS" if row.challenger.firewall_passed else "FAIL"
        if row.challenger.regressed:
            verdict = f"FAIL ({', '.join(row.challenger.regressed)})"
        lines.append(
            f"| {row.role} | {_pass_pair(row.champion)} | "
            f"{_pass_pair(row.challenger)} | {_pct(row.champion.understanding)} | "
            f"{_pct(row.challenger.understanding)} | "
            f"{_pct(row.champion.stability)} | {_pct(row.challenger.stability)} | "
            f"{verdict} |"
        )
    return "\n".join(lines)


def _build_report_llms(real: bool) -> tuple[object, object, object]:
    if real:
        debate_llm, debate_judge_llm = build_role_llms(True)
        return debate_llm, debate_judge_llm, debate_llm
    fake = _FakeReportLLM()
    return fake, fake, fake


def main() -> None:
    """Run the champion-vs-challenger report."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    parser = argparse.ArgumentParser(description="compare deliberation role prompts")
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument(
        "--golden", type=Path, default=Path("scripts/deliberation_golden.json")
    )
    parser.add_argument("--real", action="store_true")
    parser.add_argument("--rounds", type=int, default=1)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--max-debate-calls", type=int, default=150)
    parser.add_argument(
        "--transcript-dir",
        type=Path,
        default=None,
        help="optional directory for markdown debate transcripts",
    )
    args = parser.parse_args()

    prompt_sets = 1 + 3
    cases = len(_CLASS1)
    debate_calls = cases * prompt_sets * args.runs
    print(
        f"CALL PLAN: {cases} cases x {prompt_sets} prompt sets x "
        f"{args.runs} repeats = {debate_calls} debate calls "
        f"(+{debate_calls} scorer calls)"
    )
    if debate_calls > args.max_debate_calls:
        raise SystemExit("call plan exceeds max; trim --runs, not cases")

    artifacts = load_deliberation_prompt_artifacts(args.artifact_dir)
    debate_llm, debate_judge_llm, scorer_judge_llm = _build_report_llms(args.real)
    comparisons = compare_roles(
        artifacts=artifacts,
        debate_llm=debate_llm,
        debate_judge_llm=debate_judge_llm,
        scorer_judge_llm=scorer_judge_llm,
        rounds=args.rounds,
        repeats=args.runs,
        threshold=args.threshold,
        golden_path=args.golden,
        transcript_dir=args.transcript_dir,
    )
    if args.transcript_dir is not None:
        print(f"TRANSCRIPTS: {args.transcript_dir}")
    print(format_table(comparisons))
    if any(not row.challenger.firewall_passed for row in comparisons):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
