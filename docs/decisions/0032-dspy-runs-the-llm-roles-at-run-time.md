---
type: Architecture Decision
status: accepted
closes: "Does DSPy run inside the deployed agents, or only offline to produce prompt text that the runtime copies?"
tags: [llm, dspy, deliberator, runtime, images, adr-0010, dl-184, dl-252, dl-266]
---

# ADR-0032 — DSPy runs the LLM roles at run time; it is not an offline text generator

**Status:** Accepted
**Date:** 2026-10-07
**Deciders:** Operator
**Amends:** [ADR-0010](0010-llm-interaction-quality-gate.md), decision 3 (where DSPy runs). ADR-0010's
gate is unchanged.

---

## Context

ADR-0010 (2026-06-20) adopted DSPy and placed optimisation *"offline, behind a `PromptOptimizer`
port"*. That sentence was read as *DSPy never runs in a deployed agent*. Three later steps built on
that reading, and none of them was the operator's decision about where DSPy runs:

- **2026-07-02.** `dspy` landed in an optional `optimizer` extra that no Dockerfile installs.
- **2026-09-20, [DL-184](../design-log.md).** A new advisory against `diskcache`, which arrives only
  through `dspy`, was accepted on the measured premise that no container installs it.
- **2026-09-30, [DL-252](../design-log.md) (S246).** The operator asked for DSPy's guided chain of
  thought to be recorded. The spec chose to let DSPy render and parse offline into a golden fixture and
  to have the kernel reproduce its text byte for byte, for three reasons: the advisory, LiteLLM on the
  live call path, and a DSPy upgrade silently changing a live prompt.

The operator, 2026-10-07: *"May have been an experiment, i do not know but from the very beginning i
intended it to be an active participant. Revert this decision and let's put dspy back where it
belongs."*

**Measured the same day** ([DL-266](../design-log.md); DSPy 3.4.0, no LLM call, no network). A guided
debate turn was run by `dspy.ChainOfThought` through an engine that wraps our own LLM client:

- the system and user messages our client received equal today's production text byte for byte;
- `litellm` and `diskcache` were never loaded, and the turn runs with both made unimportable;
- nothing was written to DSPy's cache directory with the disk cache off;
- our client was called exactly once per turn, on success and on each failure tried.

So each of the three reasons of 2026-09-30 can be met with DSPy in the image.

## Decision

1. **DSPy runs in the agent's process.** A role whose work is an LLM call is a DSPy program
   (signature, module, adapter) executed at run time. The deliberator's defender and challenger move
   first, the judge next. Any other LLM-attached agent moves when its prompt is next changed.
2. **Our LLM client stays the only thing that talks to a vendor.** DSPy is given an engine that wraps
   `LLMClient`, so the `LLMCall` ledger, the stop reasons, the cost record and the outage handling are
   the ones production has today. LiteLLM is on no call path and in no image.
3. **`diskcache` is installed in no image, and DSPy's disk cache is off at run time.** DL-184's
   premise stays true. The dependency audit checks the package, not the name of an extra.
4. **The wire text is pinned.** The committed golden of the rendered messages is compared in CI with
   what the installed DSPy renders, and the recorded prompt-recipe digest covers the DSPy version. A
   DSPy upgrade that changes a live prompt fails the gate; it cannot arrive silently.
5. **ADR-0010's gate is unchanged.** A frozen evaluation set and a metric still decide whether a
   prompt change ships, and optimiser runs (GEPA and the rest) stay offline. What changes is the
   handover: an optimised program is loaded by the same DSPy code production runs, not copied by hand
   into kernel literals.

## Consequences

- The first build ([S254](../sprints/sprint-254-each-debater-turn-is-run-by-dspy-and-the-prompt-does-not-change.md),
  work-queue 110) changes who renders and calls, and changes no prompt text and no recorded field. Its
  proof is byte-equal messages and unchanged `system_prompt_hash` values.
- The kernel's hand-kept copy of DSPy's format text, and the tests that prove no agent loads DSPy, are
  retired by that sprint. The strict JSON rule of DL-252 D6 stays for now.
- The deliberator image gains DSPy and its dependencies, less `diskcache` and LiteLLM. Measured cost on the planner's machine:
  about one second and 25 MB at import, about 60 MB after the first turn, against a 1 GB container.
- A DSPy version bump becomes a prompt-affecting change: the golden is regenerated and its diff read.
- Typed outputs, `dspy.History`, `dspy.Refine` and a saved optimised program become usable in
  production without a hand-written twin for each.

## Alternatives considered

- **Keep DSPy offline and copy its text (the state this reverses).** Rejected by the operator. Every
  DSPy feature then needs a hand-written twin in the kernel and a parity fixture: S246 needed three
  kernel modules and a golden for one signature, and EXP-019's typed answers would need another set.
- **Install DSPy whole and let it call the vendor through LiteLLM.** Rejected: the calls leave our
  ledger, stop-reason and outage handling, and `diskcache` enters the image against DL-184.
- **Wait for a fixed `diskcache`.** Rejected: none exists (5.6.3, the affected release, is the latest
  on PyPI, measured 2026-10-07), and the measured design never loads the package.
