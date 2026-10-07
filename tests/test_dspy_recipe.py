"""The deliberator recipe includes DSPy; the operator recipe stays fixed (S254 A6).

Agent: kernel
Role: verify actual recipe declarations, source bytes and version sensitivity.
External I/O: reads the committed main fixture; source mutation is injected.
"""

from __future__ import annotations

import dspy
import pytest

from agents.deliberator.prompt_recipe import PROMPT_MODULES, PROMPT_RECIPE_HASH
from agents.deliberator.tests.dspy_fixtures import MAIN
from agents.operator.prompt_recipe import PROMPT_RECIPE_HASH as OPERATOR_HASH
from kernel import prompt_recipe


def test_dspy_version_changes_only_the_deliberator_recipe() -> None:
    """DLIB-OBS-07: installed version and both new modules bind the served digest."""
    installed = prompt_recipe.recipe_digest(
        PROMPT_MODULES, versions={"dspy": dspy.__version__}
    )
    different = prompt_recipe.recipe_digest(
        PROMPT_MODULES, versions={"dspy": "different"}
    )
    assert installed == PROMPT_RECIPE_HASH
    assert different != installed
    assert MAIN["operator_prompt_recipe_hash"] == OPERATOR_HASH
    assert {m.__name__ for m in PROMPT_MODULES} >= {
        "kernel.dspy_engine",
        "kernel.deliberation_program",
    }


@pytest.mark.parametrize("name", ["kernel.dspy_engine", "kernel.deliberation_program"])
def test_each_new_modules_source_changes_the_recipe(
    name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DLIB-OBS-07: the declaration actually hashes each new module's bytes."""
    original = prompt_recipe._source_bytes

    def changed(module):
        source = original(module)
        return source + b"\n# changed\n" if module.__name__ == name else source

    monkeypatch.setattr(prompt_recipe, "_source_bytes", changed)
    assert (
        prompt_recipe.recipe_digest(PROMPT_MODULES, versions={"dspy": dspy.__version__})
        != PROMPT_RECIPE_HASH
    )
