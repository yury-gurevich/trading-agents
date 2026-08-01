---
type: Architecture Decision
status: accepted
closes: "Is the operator the only agent allowed to call an LLM, and does it exclusively own the LLMCall audit label? When a second agent needs to reason with a model, does it write LLMCall too, or its own label?"
tags: [operator, deliberator, llm, audit, cost, substrate, adr-0012, dl-80, dl-63, laws]
---

# ADR 0020 — `LLMCall` is substrate, not the operator's

**Status:** Accepted · **Date:** 2026-08-01 · **Decider:** Yury Gurevich (product owner), on a
finding raised by the delegated coding agent before any code was written

## Context

S153 makes deliberation a real fleet agent so the LLM veto finally runs ([DL-80](../design-log.md)).
The brief hands the deliberator an `ANTHROPIC_API_KEY` and makes *"an `LLMCall` node dated after this
deploy"* a success factor. Preparing to implement it, the coding agent stopped and reported a
contradiction rather than working around it. It was right, and on verification the conflict is
sharper than first reported.

The operator's LOCKED constitution says:

- **`OPR-IDN-01`** — *"It is the sole LLM boundary."* (status ⬜, unproven)
- **`OPR-IDN-02`** — *"The operator exclusively writes these graph labels (single-writer rule):
  `CommandAudit`, `Intent`, `LLMCall`."* (status **🟩 green**, pinned by
  `test_operator_boundary_claims_graph_labels_once`)

and `contracts/operator.py` encodes it: `owns_graph=("CommandAudit", "Intent", "LLMCall")`.

Two facts decided this:

1. **There is no code drift.** Only `agents/operator/store.py` writes `LLMCall` today. The law is
   currently honoured exactly, so this is a genuine forward-looking conflict — the good kind, caught
   before implementation rather than rationalised after it.
2. **`LLMCall` is already a cost ledger with two consumers.** `surfaces/dashboard/llm_costs.py`
   enumerates every `LLMCall` node, and the `/audit-costs` skill prices LLM spend from it. The
   deliberator is about to become the system's **largest** LLM consumer — three roles, multiple
   rounds, on every `PMRun`.

## Decision

**`LLMCall` is a substrate-level audit record, not an operator-owned artifact.**

- **Any agent may call an LLM provider** under its own laws, its own bounded parameters, and its own
  fault boundary. The operator is no longer *the* LLM boundary.
- **Every agent that calls an LLM writes its own `LLMCall` node** into the one shared ledger,
  carrying at minimum the model, token counts, and the calling agent's identity.
- **The operator keeps `CommandAudit` and `Intent` exclusively.** Those are genuinely operator
  concepts — the record of a human command and its parsed intent. Only its claim on `LLMCall`
  changes.
- **The operator remains the sole *operator-command* LLM boundary**: it is still the only path from
  human text to a `TypedIntent`. What it loses is exclusivity over *the act of calling a model*,
  which was always a broader claim than its job needed.

## Why not a deliberator-owned label

`DeliberationLLMCall` was the obvious alternative: it changes no law, breaks no green test, and lets
S153 start immediately. It was rejected on two grounds.

1. **It fragments the cost ledger, silently.** Both consumers enumerate `LLMCall` and nothing else,
   so the moment the deliberator ships, the system's biggest LLM spender disappears from the bill
   while the cost report still renders a confident total. That is the
   [DL-57](../design-log.md)/[DL-59](../design-log.md) pattern — *didn't look* rendering identically
   to *looked and found nothing* — landing on the instrument the operator uses to watch spend.
2. **It is a pack concept doing a substrate job.** [ADR-0012](0012-platform-domain-separation.md)
   asks *substrate or pack?* of every decision. An audit record of a provider call contains no
   trading concept whatsoever. Giving it a domain-specific name is exactly the leak the platform
   wall exists to prevent, and the second pack would inherit the mistake.

The operator's exclusivity was never a considered architectural stance. It is an artifact of the
operator having been the only agent that called a model when its law was written.

## The road not taken (LAW-06)

- **`DeliberationLLMCall`** — rejected above.
- **Keep `LLMCall` operator-owned and have the deliberator ask the operator to make its calls** —
  rejected. It would put a control-plane agent in the hot path of every debate turn, invert the
  dependency direction (a pipeline agent depending on the operator), and make the operator a
  bottleneck for a stage that must run on every `PMRun`. The single-writer rule would be preserved
  in letter while the architecture got materially worse.
- **Widen the two cost consumers to enumerate both labels** — rejected as the worst of both. It
  keeps the fragmentation and adds a second thing to remember every time a new LLM caller appears.
- **Leave `OPR-IDN-01` untouched and amend only `OPR-IDN-02`** — rejected as dishonest. If another
  agent calls a model, "sole LLM boundary" is false; narrowing the label claim while leaving the
  broader sentence standing would leave a known-untrue clause in a constitution.

## Consequences

- **`OPR-IDN-01` and `OPR-IDN-02` must be amended** and `contracts/operator.py`'s `owns_graph`
  narrowed to `("CommandAudit", "Intent")`. `OPR-IDN-02` is **green**, so
  `test_operator_boundary_claims_graph_labels_once` must be re-pointed — the clause stays green
  because the amended clause is still fully proven, not because the assertion was loosened.
- This is a **narrowing of an existing proven clause**, which is *not* what the S152 standing
  convention covers (that convention governs *lacking declarations* of decided capabilities). A
  scope reduction on a locked, proven clause needs its own decision — which is why this is an ADR
  and not a line in a sprint doc.
- **It happens in its own chore, before S153**, so no law amendment is smuggled into a feature
  implementation. That sequencing was the coding agent's recommendation and it is correct.
- Every future LLM-calling agent inherits a settled answer instead of re-litigating this.
- **Not decided here:** whether `LLMCall` should gain a declared property list under the S144
  vocabulary guard, and whether the calling agent's identity is a new property or derivable from
  edges. That belongs to whichever sprint first writes an `LLMCall` from a non-operator agent —
  S153.
