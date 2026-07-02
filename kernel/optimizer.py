"""Prompt optimization port for eval-gated LLM tasks.

Agent: kernel
Role: define the substrate-level interface for offline prompt compilation.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PromptExample:
    """One labelled example for a structured LLM task."""

    inputs: dict[str, object]
    output: str
    rationale: str = ""


@dataclass(frozen=True)
class PromptArtifact:
    """Compiled prompt artifact promoted into a runtime champion slot."""

    task: str
    model: str
    version: str
    system_prompt: str
    examples: tuple[PromptExample, ...]


class PromptOptimizer(Protocol):
    """Offline compiler: task + metric examples + model -> prompt artifact."""

    def compile_prompt(
        self,
        *,
        task: str,
        model: str,
        version: str,
        instruction: str,
        examples: tuple[PromptExample, ...],
    ) -> PromptArtifact:
        """Return the compiled prompt artifact for this task/model."""
        ...  # pragma: no cover - protocol declaration only.
