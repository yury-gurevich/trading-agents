"""Prompt-recipe digest tests.

Agent: kernel
Role: prove the digest moves when a renderer moves, holds when it does not, and
      that the hand-maintained module lists cover what actually builds a prompt.
External I/O: writes one temporary module to tmp_path.
"""

from __future__ import annotations

import sys
from types import ModuleType
from typing import TYPE_CHECKING

from kernel.prompt_recipe import RECIPE_UNKNOWN, recipe_digest

if TYPE_CHECKING:
    from pathlib import Path


def _module(name: str, source: str, tmp_path: Path) -> ModuleType:
    path = tmp_path / f"{name}.py"
    path.write_text(source, encoding="utf-8")
    module = ModuleType(name)
    module.__file__ = str(path)
    return module


def test_the_digest_is_stable_for_unchanged_source(tmp_path: Path) -> None:
    one = _module("alpha", "X = 1\n", tmp_path)

    assert recipe_digest([one]) == recipe_digest([one])


def test_changing_a_modules_source_changes_the_digest(tmp_path: Path) -> None:
    """Item 44: the whole point — a moved renderer is visible without replaying."""
    before = recipe_digest([_module("alpha", "def render(): return 'a'\n", tmp_path)])
    after = recipe_digest([_module("alpha", "def render(): return 'b'\n", tmp_path)])

    assert before != after


def test_the_digest_does_not_depend_on_the_order_modules_are_listed(
    tmp_path: Path,
) -> None:
    """Otherwise a tidy-up of the declaration tuple would read as a code change."""
    one = _module("alpha", "X = 1\n", tmp_path)
    two = _module("beta", "Y = 2\n", tmp_path)

    assert recipe_digest([one, two]) == recipe_digest([two, one])


def test_moving_code_between_modules_changes_the_digest(tmp_path: Path) -> None:
    """🪤 The module name is hashed too, so total source is not the whole input.

    Without this, cutting a function out of `context_pm` and pasting it into
    `context_values` would leave the digest equal while the import graph — and
    therefore what actually runs — had changed.
    """
    split = recipe_digest(
        [
            _module("alpha", "def render(): return 'a'\n", tmp_path),
            _module("beta", "", tmp_path),
        ]
    )
    merged = recipe_digest(
        [
            _module("alpha", "", tmp_path),
            _module("beta", "def render(): return 'a'\n", tmp_path),
        ]
    )

    assert split != merged


def test_an_unreadable_module_makes_the_whole_digest_unknown(tmp_path: Path) -> None:
    """🪤 Fail loud, not partial: a digest over *some* of the renderer is worse.

    A partial digest compares equal across a change in the part it omitted,
    which is the single failure this field must not have — so one unreadable
    module invalidates the answer rather than narrowing it.
    """
    readable = _module("alpha", "X = 1\n", tmp_path)
    missing = ModuleType("beta")
    missing.__file__ = str(tmp_path / "does-not-exist.py")
    no_file = ModuleType("gamma")

    assert recipe_digest([readable, missing]) == RECIPE_UNKNOWN
    assert recipe_digest([readable, no_file]) == RECIPE_UNKNOWN


def test_an_empty_module_set_is_not_silently_a_valid_digest() -> None:
    """An empty declaration hashes to a real value, so assert what it is.

    This is deliberately *not* RECIPE_UNKNOWN: an empty tuple is a programming
    error in the declaration, and it must not be confusable with the
    legitimately-unreadable case. Pinned so the distinction cannot erode.
    """
    assert recipe_digest([]) != RECIPE_UNKNOWN
    assert len(recipe_digest([])) == 64


def test_the_deliberator_declares_every_module_that_builds_its_prompt() -> None:
    """🪤 The hand-maintained list is the whole correctness of the field.

    Derived from the real import graph rather than restated, so adding a context
    module without declaring it fails here instead of silently widening the
    blind spot. `build_veto_context` and `render_debate_prompt` are the two
    entry points; every first-party module reachable from them must be declared.
    """
    from agents.deliberator.prompt_recipe import PROMPT_MODULES

    declared = {module.__name__ for module in PROMPT_MODULES}
    reachable = _first_party_closure(
        ("agents.deliberator.context", "kernel.deliberation")
    )

    # Exact, not a subset: this also fails if a module is quietly added to the
    # exemption set, so both halves of the judgement stay visible in review.
    assert reachable - declared == _NOT_PROMPT_TEXT
    assert declared >= {
        "agents.deliberator.context",
        "agents.deliberator.context_market",
        "agents.deliberator.context_pm",
        "agents.deliberator.context_stop",
        "agents.deliberator.context_values",
        "kernel.deliberation",
        "kernel.deliberation_prompts",
    }


def test_the_operator_declares_its_own_recipe_not_the_deliberators() -> None:
    """Sharing one digest would assert something false about which code ran."""
    from agents.deliberator import prompt_recipe as deliberator
    from agents.operator import prompt_recipe as operator

    assert operator.PROMPT_RECIPE_HASH != deliberator.PROMPT_RECIPE_HASH
    assert RECIPE_UNKNOWN not in (
        operator.PROMPT_RECIPE_HASH,
        deliberator.PROMPT_RECIPE_HASH,
    )


#: Reachable from the renderer but contributing no prompt *text*, so declaring
#: them would move the digest on edits that cannot change a prompt. `kernel.llm`
#: is the client protocol and the stop-reason error type — transport and control
#: flow, never a string that reaches the model. Kept as an explicit set rather
#: than a loosened assertion so adding to it is a reviewable act.
_NOT_PROMPT_TEXT = {"kernel.llm"}


def _first_party_closure(roots: tuple[str, ...]) -> set[str]:
    """Modules a root imports, transitively, excluding contracts and stdlib.

    `contracts/` is excluded on purpose: it carries typed payload shapes, not
    prompt text, and folding it in would make the digest move on every unrelated
    contract edit — turning a precise signal into noise that nobody reads.
    """
    seen: set[str] = set()
    queue = list(roots)
    while queue:
        name = queue.pop()
        if name in seen:
            continue
        module = sys.modules.get(name)
        if module is None:
            continue
        seen.add(name)
        for attr in vars(module).values():
            child = getattr(attr, "__module__", None) or getattr(attr, "__name__", None)
            if isinstance(child, str) and child.startswith(
                ("agents.deliberator.", "kernel.")
            ):
                queue.append(child)
    return {name for name in seen if not name.endswith("prompt_recipe")}
