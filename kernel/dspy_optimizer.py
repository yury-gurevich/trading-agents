"""DSPy-backed prompt optimizer adapter.

Agent: kernel
Role: keep DSPy behind the PromptOptimizer port; runtime loads artifacts, not DSPy.
External I/O: optional import of the offline DSPy dependency.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass

from kernel.optimizer import PromptArtifact, PromptExample


@dataclass(frozen=True)
class DSPyPromptOptimizer:
    """First PromptOptimizer implementation, used offline to compile prompts."""

    dspy_module: object | None = None

    def compile_prompt(
        self,
        *,
        task: str,
        model: str,
        version: str,
        instruction: str,
        examples: tuple[PromptExample, ...],
    ) -> PromptArtifact:
        """Compile a deterministic few-shot artifact while requiring DSPy offline."""
        self._dspy()
        prompt = _few_shot_prompt(instruction, examples)
        return PromptArtifact(
            task=task,
            model=model,
            version=version,
            system_prompt=prompt,
            examples=examples,
        )

    def _dspy(self) -> object:
        if self.dspy_module is not None:
            return self.dspy_module
        return importlib.import_module("dspy")


def _few_shot_prompt(instruction: str, examples: tuple[PromptExample, ...]) -> str:
    lines = [
        instruction.strip(),
        "",
        "Use the examples as the compiled champion prompt. Always choose one",
        "remediation from the provided enum and return JSON only.",
    ]
    if examples:
        lines.append("")
        lines.append("Examples:")
    for example in examples:
        lines.append(f"- failure={example.inputs}; remediation={example.output}")
        if example.rationale:
            lines.append(f"  rationale={example.rationale}")
    return "\n".join(lines).strip()
