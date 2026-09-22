"""Oversize `scripts/` modules that predate the size gate reading that folder.

Agent: tooling
Role: name each legacy oversize script and freeze it at its measured line count.
External I/O: none; exports immutable checker constants.

This is a ratchet, not an exemption. `check_module_size.py` fails when a file
here **grows**, when a file **not** here crosses the 200-line block, and when an
entry here has been split below the block and not deleted - so the list can only
shrink, and a file that leaves can never come back silently.

🪤 It is deliberately not the shape of the PARAM baseline (work-queue item 33),
which prints 57 warnings that pass. Every line here can fail the gate.

Retire the whole file by splitting the last entry out of it.
"""

from __future__ import annotations

# path -> the line count measured when the gate first covered `scripts/`
# (2026-09-23). A file may shrink freely; growing by one line fails.
LEGACY_MAX_LINES: dict[str, int] = {
    "scripts/check_law_coverage.py": 228,
    "scripts/check_markdown_links.py": 220,
    "scripts/check_worktrees.py": 201,
    "scripts/compare_deliberation_prompts.py": 363,
    "scripts/deliberate.py": 246,
    "scripts/deliberation_gate.py": 230,
    "scripts/deliberation_replay_batch.py": 240,
    "scripts/evaluate_return_model.py": 288,
    "scripts/gate_selftest_cases.py": 346,
    "scripts/param_law_sync.py": 212,
    "scripts/remediation_gate.py": 206,
    "scripts/retrain_return_model_helpers.py": 200,
    "scripts/run_local.py": 227,
    "scripts/sb_sas_plan.py": 212,
    "scripts/servicebus_request.py": 216,
    "scripts/vocabulary_resolution.py": 268,
}
