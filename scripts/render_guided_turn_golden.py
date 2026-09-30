"""Write the guided turn's golden fixture from real DSPy.

Agent: tooling
Role: render DSPy's system and user messages for fixture inputs, and parse every
      case of S246's parse table with `ChatAdapter`, into the golden the runtime
      is proven against (B1, B2). Its output is never edited by hand (DL-252 D1).
External I/O: imports the offline `dspy` package; writes the golden JSON file.

Run it (the only way the golden is written):
  LITELLM_LOCAL_MODEL_COST_MAP=True PYTHONPATH=. uv run --frozen --extra optimizer \
      python scripts/render_guided_turn_golden.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import TYPE_CHECKING

from scripts.deliberation_guided_program import guided_program, load_dspy
from scripts.guided_turn_golden_cases import PARSE_CASES, SYSTEM_CASES, USER_CASES

if TYPE_CHECKING:
    from types import ModuleType

GOLDEN = Path("tests/fixtures/deliberation_guided_golden.json")
COMMAND = (
    "LITELLM_LOCAL_MODEL_COST_MAP=True PYTHONPATH=. uv run --frozen --extra optimizer "
    "python scripts/render_guided_turn_golden.py"
)


def build_golden(dspy_module: ModuleType | None = None) -> dict[str, object]:
    """Return every rendering and parse the runtime must reproduce."""
    dspy = load_dspy(dspy_module)
    adapter = dspy.ChatAdapter()
    # The instructions reach only the system message's last block, so one
    # signature serves the prefix, every user message and every parse.
    signature = _signature(dspy, "Argue.")
    return {
        "generator": "scripts/render_guided_turn_golden.py",
        "command": COMMAND,
        "dspy_version": str(dspy.__version__),
        "prefix": (
            adapter.format_field_description(signature)
            + "\n"
            + adapter.format_field_structure(signature)
            + "\n"
        ),
        "requirements": adapter.user_message_output_requirements(signature),
        "system": [
            {
                "name": name,
                "instructions": instructions,
                "rendered": adapter.format_system_message(
                    _signature(dspy, instructions)
                ),
            }
            for name, instructions in SYSTEM_CASES
        ],
        "user": [
            {
                "name": name,
                "inputs": inputs,
                "rendered": adapter.format_user_message_content(
                    signature, inputs, main_request=True
                ),
            }
            for name, inputs in USER_CASES
        ],
        "parse": [
            {
                "name": name,
                "completion": completion,
                "dspy": _parsed(adapter, signature, completion),
            }
            for name, completion in PARSE_CASES
        ],
    }


def _signature(dspy: ModuleType, instructions: str) -> object:
    program = guided_program(instructions, dspy)
    return program.predict.signature  # type: ignore[attr-defined]


def _parsed(adapter: object, signature: object, completion: str) -> dict[str, object]:
    try:
        fields = adapter.parse(signature, completion)  # type: ignore[attr-defined]
    except Exception as exc:  # the golden records any refusal, by its type
        return {"parsed": False, "error": type(exc).__name__}
    return {
        "parsed": True,
        "reasoning": fields["reasoning"].model_dump(mode="json"),
        "argument": fields["argument"],
    }


def write_golden(path: Path, dspy_module: ModuleType | None = None) -> Path:
    """Write the golden as UTF-8 JSON, keys in the order built."""
    text = json.dumps(build_golden(dspy_module), indent=2, ensure_ascii=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    """Write the golden fixture with the real DSPy."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=GOLDEN)
    args = parser.parse_args(argv)
    print(f"wrote {write_golden(args.out)}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
