"""The declared set of modules that decide an operator prompt's text.

Agent: operator
Role: name every module whose source shapes an operator prompt, and compute the
      recipe digest recorded on each `LLMCall` the operator writes.
External I/O: reads those modules' source files once, at import.

The operator shares the substrate `LLMCall` ledger (ADR-0020) but not the
deliberation renderer, so it declares its own recipe. Reusing the deliberator's
digest would assert something false about which code produced the row — and the
field exists precisely to stop that kind of claim.

🪤 `evidence.py` is in the list although it builds no prompt text directly: it
selects the evidence nodes `build_explain_user` interpolates, so a change to how
much or which evidence is gathered changes the rendered prompt. A recipe that
covered only the string-formatting module would compare equal across exactly
the change most likely to alter an answer.
"""

from __future__ import annotations

from agents.operator.domain import evidence, grammar, prompts
from kernel.prompt_recipe import recipe_digest

#: Every module whose source can change the text of an operator prompt.
PROMPT_MODULES = (evidence, grammar, prompts)

#: Computed once per process: module source cannot change under a running image.
PROMPT_RECIPE_HASH = recipe_digest(PROMPT_MODULES)
