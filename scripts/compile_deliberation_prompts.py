"""Compile DSPy deliberation role prompts into PromptArtifact JSON.

Agent: tooling
Role: build ADR-0010 artifacts for defender/challenger/judge from the existing
      deliberation eval libraries, behind the PromptOptimizer port.
External I/O: writes prompt artifact JSON; imports DSPy only through the optimizer.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.deliberation_eval import _CLASS1, _CLASS2  # noqa: E402

from kernel import (  # noqa: E402
    CHALLENGER_SYSTEM,
    DEFENDER_SYSTEM,
    DELIBERATION_ROLE_FILENAMES,
    DELIBERATION_ROLE_TASKS,
    DELIBERATION_ROLES,
    JUDGE_SYSTEM,
    PromptArtifact,
    PromptExample,
)
from kernel.dspy_optimizer import DSPyPromptOptimizer  # noqa: E402

_CLASS1_CALIBRATION = (
    " Compiled calibration from the existing Class-1 library: when grounding names "
    "an implementation-specific flaw, address that exact flaw before generic "
    "finance caution. Preserve these distinctions: pooled cross-sectional sigma is "
    "not per-name volatility; calendar-day staleness is not trading-session "
    "freshness; the sector cap is not a name-correlation penalty; fixed-fraction "
    "sizing is not volatility-adjusted; Alpha158 weight 0.00 contributes nothing; "
    "LightGBM shadow output does not feed the live decision."
)
_CHALLENGER_CALIBRATION = (
    " For each attack, explicitly state why the exact flaw should force REVISE or "
    "OVERTURN rather than being dismissed as a policy preference. For the calendar "
    "staleness pattern, say that calendar-day counting can falsely pass a signal "
    "that is stale in trading-session terms after a long weekend; that is the "
    "decision flaw under test. Do not frame calendar staleness as merely using "
    "the wrong clock; say that rule-compliant calendar freshness still needs a "
    "post-holiday recheck because the context warns about multi-session staleness."
)

_ROLE_INSTRUCTIONS = {
    "defender": DEFENDER_SYSTEM + _CLASS1_CALIBRATION,
    "challenger": CHALLENGER_SYSTEM + _CLASS1_CALIBRATION + _CHALLENGER_CALIBRATION,
    "judge": (
        JUDGE_SYSTEM
        + " If the Challenger catches a grounded implementation-specific flaw from "
        "the evidence, do not uphold the decision." + _CLASS1_CALIBRATION
    ),
}


def _case_rows() -> tuple[tuple[object, ...], ...]:
    return (*_CLASS2, *_CLASS1)


def _role_output(role: str, flaw: str) -> str:
    if role == "defender":
        return (
            "Defend the decision honestly from the supplied evidence; do not deny "
            f"this known evaluation flaw: {flaw}"
        )
    if role == "challenger":
        return flaw
    return json.dumps({"ruling": "revise", "rationale": flaw}, sort_keys=True)


def build_prompt_examples(role: str) -> tuple[PromptExample, ...]:
    """Build role examples from the existing Class-1/Class-2 eval libraries."""
    examples: list[PromptExample] = []
    for name, decision, blind, ground, flaw, keywords in _case_rows():
        examples.append(
            PromptExample(
                inputs={
                    "case": str(name),
                    "decision": str(decision),
                    "context": f"{blind} {ground}",
                    "flaw_keywords": list(keywords),
                },
                output=_role_output(role, str(flaw)),
                rationale=str(flaw),
            )
        )
    return tuple(examples)


def _artifact_model(role: str, debate_model: str, judge_model: str) -> str:
    return judge_model if role == "judge" else debate_model


def _artifact_version(base_version: str, role: str, model: str) -> str:
    return f"{base_version}-{role}-{model}"


def _artifact_json(artifact: PromptArtifact) -> str:
    payload = {
        "task": artifact.task,
        "model": artifact.model,
        "version": artifact.version,
        "system_prompt": artifact.system_prompt,
        "examples": [
            {
                "inputs": example.inputs,
                "output": example.output,
                "rationale": example.rationale,
            }
            for example in artifact.examples
        ],
    }
    return json.dumps(payload, indent=2) + "\n"


def compile_artifacts(
    *,
    debate_model: str,
    judge_model: str,
    version: str,
    output_dir: Path,
    dspy_module: object | None = None,
) -> dict[str, Path]:
    """Compile all role prompts and write one artifact JSON per role."""
    optimizer = DSPyPromptOptimizer(dspy_module=dspy_module)
    output_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    for role in DELIBERATION_ROLES:
        model = _artifact_model(role, debate_model, judge_model)
        artifact = optimizer.compile_prompt(
            task=DELIBERATION_ROLE_TASKS[role],
            model=model,
            version=_artifact_version(version, role, model),
            instruction=_ROLE_INSTRUCTIONS[role],
            examples=build_prompt_examples(role),
        )
        path = output_dir / DELIBERATION_ROLE_FILENAMES[role]
        path.write_text(_artifact_json(artifact), encoding="utf-8")
        written[role] = path
    return written


def main() -> None:
    """Compile the S119 role prompt artifacts."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    parser = argparse.ArgumentParser(description="compile deliberation role prompts")
    parser.add_argument("--debate-model", default="gpt-5.5")
    parser.add_argument("--judge-model", default="claude-opus-4-8")
    parser.add_argument("--version", default="2026-07-08-s119-v1")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="directory for deliberation_*_prompt.json artifacts",
    )
    args = parser.parse_args()
    written = compile_artifacts(
        debate_model=args.debate_model,
        judge_model=args.judge_model,
        version=args.version,
        output_dir=args.output_dir,
    )
    for role, path in written.items():
        print(f"wrote {role}: {path}")


if __name__ == "__main__":
    main()
