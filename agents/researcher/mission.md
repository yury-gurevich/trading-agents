# Researcher Agent

**Mission.** Mine accumulated evidence for parameter and strategy improvements and
propose bounded, measurable changes into the human-review queue — never apply them.

## Owns
- Improvement experiments.
- Evidence selection over historical runs.
- Proposal generation into the parameter-change queue.

## Boundary — contract: `contracts/researcher.py`
- **Consumes:** `propose(ResearchRequest) -> ParameterChangeProposal`,
  `evidence(ResearchRequest) -> Explanation`.
- **Emits:** `proposal_queued`.
- **Depends on (read-only):** `reporter` / the provenance graph.

## Data ownership
- **Postgres:** `improvement_experiments`, `parameter_change_queue`,
  `researcher_configs`.
- **Graph:** `Experiment`, `ParamChange` (`Experiment -[:PROPOSES]-> ParamChange`).

## External I/O
- None.

## MCP surface
- `propose`, `evidence`.

## Never
- Apply a parameter change — proposes into the review queue only.
- Bypass the evidence-window requirement.
- Propose a forbidden parameter combination.
