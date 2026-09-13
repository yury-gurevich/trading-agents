"""The declared set of modules that decide a deliberation prompt's text.

Agent: deliberator
Role: name every module whose source shapes a debate prompt, and compute the
      recipe digest recorded on each `LLMCall`.
External I/O: reads those modules' source files once, at import.

Work-queue item 44: nothing recorded which code rendered a prompt, so whether a
stored `prompt_hash` is comparable to today's renderer was unknowable without
replaying the row and seeing what failed. Re-measured 2026-09-13 on the live
spine: **62 of 285** recorded `defender:r1` turns replay — 21.75 %.

🪤 **This list is the whole correctness of the field, and it is maintained by
hand.** A module that shapes a prompt and is missing here produces the one
failure mode that matters: two rows agreeing on the digest while their prompts
were rendered differently. `test_prompt_recipe.py` pins the list against the
real import graph of `build_veto_context` and `render_debate_prompt`, so adding
a context module without declaring it fails `make ci` rather than silently
widening the blind spot.

**Why one list serves all three roles.** The manager builds the context
(`context*`) and the peers render the turn (`kernel.deliberation`), but all
three run the *same image* from the same build — so the union is correct for
every row any of them writes, and a per-role list would differ only by being
incomplete. The transport in between carries a `DebateProposition`, not a
recipe, so a peer cannot learn the manager's digest; it does not need to,
because they are the same bytes.
"""

from __future__ import annotations

from agents.deliberator import (
    context,
    context_market,
    context_pm,
    context_stop,
    context_values,
)
from kernel import deliberation, deliberation_prompts
from kernel.prompt_recipe import recipe_digest

#: Every module whose source can change the text of a deliberation prompt.
#: `kernel.deliberation` renders the turn and `kernel.deliberation_prompts`
#: holds the champion role prompts; the five `context*` modules build the
#: CONTEXT / EVIDENCE block interpolated into it.
PROMPT_MODULES = (
    context,
    context_market,
    context_pm,
    context_stop,
    context_values,
    deliberation,
    deliberation_prompts,
)

#: Computed once per process: module source cannot change under a running image.
PROMPT_RECIPE_HASH = recipe_digest(PROMPT_MODULES)
