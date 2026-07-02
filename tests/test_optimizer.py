"""Prompt optimizer port tests.

Agent: kernel
Role: verify the PromptOptimizer public contract and DSPy-backed offline adapter.
External I/O: none.
"""

from __future__ import annotations

import sys

from kernel import PromptArtifact, PromptExample, PromptOptimizer
from kernel.dspy_optimizer import DSPyPromptOptimizer


def _example() -> PromptExample:
    return PromptExample({"failure": "blank secret"}, "refetch-from-key-vault", "safe")


def test_prompt_optimizer_port_accepts_dspy_adapter() -> None:
    optimizer: PromptOptimizer = DSPyPromptOptimizer(dspy_module=object())
    artifact = optimizer.compile_prompt(
        task="remediation-selection",
        model="gpt-5.5",
        version="v1",
        instruction="Choose the least destructive remediation.",
        examples=(_example(),),
    )
    assert isinstance(artifact, PromptArtifact)
    assert artifact.system_prompt.startswith("Choose the least destructive")
    assert "refetch-from-key-vault" in artifact.system_prompt
    assert artifact.examples == (_example(),)


def test_dspy_adapter_imports_optional_dependency_when_not_injected() -> None:
    fake_module = object()
    previous = sys.modules.get("dspy")
    sys.modules["dspy"] = fake_module
    try:
        artifact = DSPyPromptOptimizer().compile_prompt(
            task="remediation-selection",
            model="gpt-5.5",
            version="v1",
            instruction="Choose safely.",
            examples=(),
        )
    finally:
        if previous is None:
            del sys.modules["dspy"]
        else:
            sys.modules["dspy"] = previous
    assert artifact.system_prompt == (
        "Choose safely.\n\n"
        "Use the examples as the compiled champion prompt. Always choose one\n"
        "remediation from the provided enum and return JSON only."
    )


def test_dspy_adapter_allows_examples_without_rationale() -> None:
    artifact = DSPyPromptOptimizer(dspy_module=object()).compile_prompt(
        task="remediation-selection",
        model="gpt-5.5",
        version="v1",
        instruction="Choose safely.",
        examples=(PromptExample({"failure": "unknown"}, "pause-and-escalate"),),
    )
    assert "rationale=" not in artifact.system_prompt
