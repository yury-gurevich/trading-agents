"""The guided turn's frozen format text, as DSPy 3.3.1 renders it.

Agent: kernel
Role: hold, as literals, the text DSPy's `ChatAdapter` writes around a guided
      debate turn, so the runtime renders it without importing DSPy (DL-252 D1).
External I/O: none.

Copied from `tests/fixtures/deliberation_guided_golden.json`, which only
`scripts/render_guided_turn_golden.py` writes, from real DSPy.
`tests/test_deliberation_guided.py` proves every literal equal to it; to change
the format, change the program, regenerate the golden, then these literals.

🪤 DSPy writes a space before some newlines (``(GuidedReasoning): `` and
``your objective is: ``). Every newline here is written as an escape, so those spaces
stay inside a literal and no source line ends in whitespace.
"""

from __future__ import annotations

#: DSPy's field-description block and structure block, each ending in a newline.
GUIDED_TURN_PREFIX = (
    "Your input fields are:\n"
    "1. `decision` (str): the decision under test\n"
    "2. `context` (str): the evidence packet for this decision; every "
    "value you read comes from here\n"
    "3. `transcript` (str): the debate so far\n"
    "Your output fields are:\n"
    "1. `reasoning` (GuidedReasoning): \n"
    "2. `argument` (str): step 3: your turn, at most ~5 sentences, "
    "built only from your readings and gaps\n"
    "All interactions will be structured in the following way, "
    "with the appropriate values filled in.\n"
    "\n"
    "[[ ## decision ## ]]\n"
    "{decision}\n"
    "\n"
    "[[ ## context ## ]]\n"
    "{context}\n"
    "\n"
    "[[ ## transcript ## ]]\n"
    "{transcript}\n"
    "\n"
    "[[ ## reasoning ## ]]\n"
    "{reasoning}        # note: the value you produce must adhere to "
    'the JSON schema: {"type": "object", '
    '"$defs": {"EvidenceReading": {"type": "object", '
    '"properties": {"bears_on": {"type": "string", '
    '"description": "how it bears on the decision under test", '
    '"enum": ["supports", "against", "neutral"], "title": "Bears On"}, '
    '"meaning_here": {"type": "string", '
    '"description": "one clause: what this measures in THIS system, '
    'not in general finance", "title": "Meaning Here"}, '
    '"metric": {"type": "string", '
    '"description": "the exact name as it appears in the evidence '
    'packet", "title": "Metric"}, "value": {"type": "string", '
    '"description": "the value copied exactly as the packet writes '
    'it", "title": "Value"}}, "required": ["metric", "value", '
    '"meaning_here", "bears_on"], "title": "EvidenceReading"}}, '
    '"description": "Read before you argue: each later step may use '
    'only what the earlier steps established.", '
    '"properties": {"gaps": {"type": "array", '
    '"description": "step 2: evidence the packet lacks, '
    'marks unavailable, or leaves unit/scope unknown", '
    '"items": {"type": "string"}, "title": "Gaps"}, '
    '"readings": {"type": "array", '
    '"description": "step 1: every value your argument relies on, '
    'read from the packet", '
    '"items": {"$ref": "#/$defs/EvidenceReading"}, '
    '"title": "Readings"}}, "required": ["readings", "gaps"], '
    '"title": "GuidedReasoning"}\n'
    "\n"
    "[[ ## argument ## ]]\n"
    "{argument}\n"
    "\n"
    "[[ ## completed ## ]]\n"
)

#: What DSPy writes before the role prompt, whose every line it then indents.
OBJECTIVE_LEAD = "In adhering to this structure, your objective is: "

#: The output reminder DSPy appends to the user message.
GUIDED_USER_REQUIREMENTS = (
    "Respond with the corresponding output fields, "
    "starting with the field `[[ ## reasoning ## ]]` (must be "
    "formatted as a valid Python GuidedReasoning), "
    "then `[[ ## argument ## ]]`, "
    "and then ending with the marker for `[[ ## completed ## ]]`."
)
