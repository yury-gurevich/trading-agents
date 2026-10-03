"""Remediation selector regression gate.

Agent: tooling
Role: freeze/check the bounded remediation selector against the trading golden set.
External I/O: stdout; writes the golden on --freeze; optional LLM provider (via
              `scripts/remediation_gate_llm.py`) when --real is supplied.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.master.remediation_gate import RemediationSelectionScore

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_PACK = _ROOT / "orchestration" / "packs"
_CASES = _PACK / "trading_remediation_selection_cases.json"
_CATALOGUE = _PACK / "trading_remediations.json"
_PROMPT = _PACK / "trading_remediation_prompt.json"
_GOLDEN = Path(__file__).with_name("remediation_selector_golden.json")


def _score(real: bool) -> tuple[RemediationSelectionScore, ...]:
    from scripts.remediation_gate_llm import build_real_llm, fake

    from agents.master.remediation import load_remediations
    from agents.master.remediation_gate import (
        load_prompt_artifact,
        load_selection_cases,
        run_selection_eval,
    )

    llm = build_real_llm() if real else fake()
    cases = load_selection_cases(str(_CASES))
    catalogue = load_remediations(str(_CATALOGUE))
    artifact = load_prompt_artifact(str(_PROMPT))
    return run_selection_eval(
        llm, cases, catalogue, system_prompt=artifact.system_prompt
    )


def _freeze(real: bool) -> None:
    from agents.master.remediation_gate import (
        passing_selection_names,
        selection_pass_rate,
    )

    scores = _score(real)
    model = os.environ.get("OPENAI_MODEL", "fake") if real else "fake"
    passing = sorted(passing_selection_names(scores))
    golden = {
        "model": model,
        "date": datetime.now(tz=UTC).date().isoformat(),
        "library": "trading-remediation-selection",
        "passing": passing,
        "pass_rate": selection_pass_rate(scores),
    }
    _GOLDEN.write_text(json.dumps(golden, indent=2) + "\n", encoding="utf-8")
    print(f"FROZEN remediation selector golden ({model})")
    print(f"  passing ({len(passing)}): {passing}")
    print(f"  pass_rate: {golden['pass_rate']:.2f}")
    print(f"  written: {_GOLDEN.name}")


def _check(real: bool) -> int:
    from agents.master.remediation_gate import (
        check_selection_baseline,
        selection_pass_rate,
    )

    golden = json.loads(_GOLDEN.read_text(encoding="utf-8"))
    scores = _score(real)
    result = check_selection_baseline(
        scores, frozenset(str(name) for name in golden["passing"])
    )
    print("REMEDIATION SELECTOR GATE")
    print(f"  pass_rate: {selection_pass_rate(scores):.2f}")
    print(f"  regressed: {list(result.regressed) or 'none'}")
    print(f"  gained:    {list(result.gained) or 'none'}")
    print(f"  VERDICT: {'PASS' if result.passed else 'FAIL'}")
    return 0 if result.passed else 1


def main() -> None:
    """Freeze or check the remediation selector golden."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="remediation selector gate")
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--real", action="store_true", help="call GPT-5.5 via .env")
    args = parser.parse_args()
    if args.freeze == args.check:
        raise SystemExit("pass exactly one of --freeze or --check")
    if args.freeze:
        _freeze(args.real)
        return
    raise SystemExit(_check(args.real))


if __name__ == "__main__":
    main()
