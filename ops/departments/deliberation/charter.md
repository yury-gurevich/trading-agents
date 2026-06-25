---
department: deliberation
tier: x cross-cutting
owner: operator + AI deliberation loop  (→ candidate "Tribunal" agent)
status: draft
version: 0.3
implements_with: ["the debate harness (to build)", docs/decisions/0010-llm-interaction-quality-gate.md, ops/laws/LAW-05-defendable-decision.md]
---

# Charter — Deliberation (defend → attack → judge a decision)

> A **decision-agnostic** primitive. Given a *proposition* (a stated decision + its rationale and
> evidence), three LLM roles argue it — **Defender** argues for, **Challenger** attacks, **Judge**
> weighs the exchange and rules — and the **transcript becomes the decision's recorded, evidence-linked
> "why" (LAW-05)**. It **stress-tests** a decision and records a defensible verdict. It does **not make**
> the decision and **never executes** it. Subordinate to LAW-01…06.

## OPS-IDN · Identity

Cross-cutting substrate capability. Takes a proposition (a candidate decision + context/evidence) and
runs a **bounded** LLM debate across three separated roles, returning a **verdict** (uphold / overturn /
revise) plus the transcript as the LAW-05 defence. Decision-agnostic: the same engine argues a PM
buy/sell/hold, a parameter change, or a solution design. It originates nothing and executes nothing —
it makes decisions **defensible**.

### What is IN / OUT

**IN:** stress-testing a stated decision via structured LLM debate; producing a verdict + a recorded
rationale; champion–challenger of *arguments*; bounded, role-separated deliberation.

**OUT:** *making* the decision (the owning agent does) · *executing* it (execution does) · unbounded
open-ended chat (debate is bounded — fixed rounds, fixed roles, token budget) · ruling on safety/capital
by itself (a debate **informs**; the owning agent + operator gate still decide, LAW-01 CI-03).

## OPS-OWN · Owns (single-writer)

- The debate artifacts on the graph: `Debate`, `Argument`, `Verdict` nodes + their transcript.
- The three **role prompts** (Defender / Challenger / Judge `system_prompt`s — tunable, ADR-0010).
- This charter. Does **not** own the decision, its evidence, or its execution.

## OPS-UP · Upstream (needs)

- An **LLM provider** (the operator/forecaster plumbing; ADR-0010 eval-gated prompts).
- A **proposition**: the decision under test + its context/evidence.

## OPS-DOWN · Downstream (blast radius)

The owning decision-maker consumes the verdict; LAW-05 records cite the transcript. A biased Judge or a
lazy/sycophantic Challenger → misleading verdicts → bad decisions trusted. Contained by the gates and by
the operator remaining the final gate — **the debate advises, it does not decide.**

## OPS-GATE · Preflight gates (GO / NO-GO)

| Gate ID | Check | Pass criteria | On fail |
| --- | --- | --- | --- |
| G-PROP | a well-formed proposition (decision + context) is present | present | block |
| G-ROLES | all three role prompts resolve, and are **distinct** | Defender ≠ Challenger ≠ Judge | block |
| G-LLM | the LLM provider is reachable and within budget (validate-then-run) | green | block, name the cause |
| G-BOUND | a max-rounds and token budget are set (debate is bounded, never open-ended) | both set | block |

## OPS-ACT · Actions / Runbooks

| Action | Gates | Idempotent | Dry-run | Postcondition | Rollback | Blast radius |
| --- | --- | --- | --- | --- | --- | --- |
| open debate | G-PROP/ROLES/LLM/BOUND | yes | print the prompts | `Debate` node created | delete node | none |
| run rounds | — | yes (per debate id) | — | N rounds Defender↔Challenger; transcript persisted (or trial `invalid` on fault) | none (read-only on the decision) | LLM calls only |
| judge | — | yes | — | `Verdict` = uphold/overturn/revise + rationale | none | none |
| record | — | yes | — | transcript + verdict attached to the decision as its LAW-05 "why" | none | none |

## OPS-PNR · Points of no return

None — deliberation is **advisory**: it records and recommends, it never executes. Acting on a verdict
that touches capital is the **owning agent's** PNR, not the debate's.

## OPS-REC · Recovery

Transcripts + verdicts are **append-only** graph nodes; a debate is re-runnable (a new `Debate` node).
RPO = the last persisted round; RTO = re-open the debate.

## OPS-NEV · Never

- Never let the debate **make or execute** the decision — it informs; the owning agent + operator decide.
- Never run **unbounded** (fixed rounds + token budget; G-BOUND).
- Never **hide the transcript** — a verdict without its debate is not a LAW-05 defence.
- Never let **one role both argue and judge** (Defender ≠ Challenger ≠ Judge — independence).
- Never treat a verdict as **ground truth** — it is an argued opinion, recorded, not a fact.
- Never **swap the model silently** (DL-24). The `model` is a *gated* parameter: a downgrade/side-grade
  must run the eval harness on the new model and not regress the golden verdict set — else outputs drift
  unnoticed *deep in the code*. DSPy re-compiles the roles per-model; the eval gates the change.

## OPS-OBS · Observability

`Debate` / `Argument` / `Verdict` nodes on the graph; the transcript human-readable; a surface
`debate <id>` prints the exchange + verdict. Each debate writes a `ledger.md` row.

## OPS-TUNE · Tuning

- **Assess:** do **upheld** decisions out-perform **overturned** ones (the real calibration signal)?
  Judge consistency; debate cost/length; Challenger laziness (does it ever actually overturn?).
- **Improve:** the role prompts are **not hand-written — they are DSPy-compiled** against the eval
  (ADR-0010): DSPy optimizes each role's prompt + demonstrations so the Challenger reliably finds
  material flaws and the Judge calibrates to outcomes (DL-21). Adjust rounds; detect a sycophantic
  Challenger. (The roles are tunables — an Experimentation/DSPy target, not free prose.)

## OPS-PARAM · Parameters

| Param | Default | Range / options | Effect |
| --- | --- | --- | --- |
| `max_rounds` | 3 | 1–10 | debate depth (Defender↔Challenger exchanges) |
| `roles` | Defender, Challenger, Judge | fixed three | the separated voices |
| `token_budget` | per-debate | — | bounds cost (G-BOUND) |
| `defender_temperature` / `challenger_temperature` | higher | 0–1 | argumentative creativity |
| `judge_temperature` | lower | 0–1 | rigour over flair |
| `model` | per `.env` | provider model id | **GATED (DL-24)** — a change must pass the eval (no silent drift); DSPy re-compiles the roles per-model |

## OPS-MNT · Maintenance trigger

When you point the debate at a **new decision type** → register its proposition shape + the context the
roles receive. When you **change a role prompt** → it is an **ADR-0010 eval-gated** change, not a free
edit. When you **change the `model`** (downgrade/side-grade) → run the gate
(`python scripts/deliberation_gate.py --check <model> --real`) against the committed golden baseline and
confirm no regression *before* it goes live (DL-24 · EXP-005). The gate is real: gpt-5.4 trips it.

## Graduation to an agent

Today the owner is "operator + AI deliberation loop." It has agent shape: a bounded remit, an artifact
it solely owns (the transcript/verdict), gates, and a measurable goal (*do upheld decisions outperform?*).
Per **LAW-01 CI-05** it graduates into a **Tribunal** agent — the three roles as sub-agents running this
charter autonomously. The charter is that agent's `laws.md` in waiting.

## Changelog

| Version | Date | Change |
| --- | --- | --- |
| 0.1 | 2026-06-24 | initial draft — decision-agnostic defend/attack/judge debate primitive; the DL-20 deliberation made concrete |
| 0.2 | 2026-06-24 | `model` is a GATED parameter (DL-24) — a downgrade/side-grade must pass the eval; DSPy re-compiles roles per-model to prevent silent output drift |
| 0.3 | 2026-06-25 | the model gate is now runnable (EXP-005) — `scripts/deliberation_gate.py` + a committed golden baseline; gpt-5.4 demonstrably trips it |
