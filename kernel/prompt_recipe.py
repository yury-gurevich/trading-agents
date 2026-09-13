"""A digest of the code that renders a prompt, so replayability is knowable.

Agent: kernel
Role: hash the source of the modules that determine a prompt's text, letting a
      recorded call say which renderer produced it without replaying it.
External I/O: reads the source files of the modules it is handed.

Exists because work-queue item 44 measured the cost of not knowing. Re-measured
2026-09-13 against the live spine: **62 of 285** recorded `defender:r1` turns
replay to their stored `prompt_hash` — **21.75 %** — and the split is not
recency, it is *which renderer the run was recorded on*. There was no way to
tell the two apart except by replaying every row and seeing what failed, which
is how [DL-104](../docs/design-log.md)'s 56 % self-agreement had to be
re-derived from stored verdicts rather than replayed prompts (S173).

🪤 **This digest fails in the safe direction, and that is the design.** It
hashes module *source*, so a comment or docstring edit moves it even though the
rendered prompt is byte-identical — a **false "not comparable"**. It can never
do the reverse: any change that alters a prompt necessarily alters the source
that produces it, so the digest never claims comparable when it is not. A
behavioural digest (render a canonical fixture and hash the output) would be
tighter, and was rejected: the veto context is built from a `GraphStore`, so a
fixture render would need a fake graph inside the production call path — a far
larger surface to be wrong in, guarding against nothing worse than an
over-cautious mismatch.

🪤 **The caller declares its own module set, and must.** `import-linter` forbids
`kernel` importing `agents`, and the modules that decide a deliberation prompt
live in both layers — `kernel.deliberation` renders the turn while
`agents.deliberator.context*` builds the context interpolated into it. So this
module takes modules it is handed and never guesses which ones matter; each
agent owns the list of what shapes its own prompts.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable
    from types import ModuleType

RECIPE_UNKNOWN = "unknown"


def recipe_digest(modules: Iterable[ModuleType]) -> str:
    """Hash the source of every module that shapes a prompt, name included.

    The module's dotted name is hashed alongside its bytes, so moving code
    between two modules changes the digest even when the total source does not.
    Returns ``RECIPE_UNKNOWN`` when any module's source cannot be read rather
    than hashing a partial set: a digest over *some* of the renderer would
    compare equal across a change in the part it omitted, which is the one
    failure this module must not have.
    """
    digest = hashlib.sha256()
    for module in sorted(modules, key=lambda item: item.__name__):
        source = _source_bytes(module)
        if source is None:
            return RECIPE_UNKNOWN
        digest.update(module.__name__.encode("utf-8"))
        digest.update(b"\0")
        digest.update(source)
        digest.update(b"\0")
    return digest.hexdigest()


def _source_bytes(module: ModuleType) -> bytes | None:
    """Read one module's source, or None when it is not on disk.

    Source is present in every agent image — each `Dockerfile` copies `kernel/`,
    `contracts/` and its own package as `.py` files — so this is the normal
    path, not a fallback. It still degrades rather than raising, because a
    missing source file must not take the veto down over an audit field.
    """
    origin = getattr(module, "__file__", None)
    if not origin:
        return None
    try:
        return Path(origin).read_bytes()
    except OSError:
        return None
