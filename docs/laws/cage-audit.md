# Cage audit — do the laws define a space, or a cage? (DL-19)

**What this is.** DL-19's second lock: *"laws define a space, not a solution — the solution is owned and
creatively discovered by the agents inside it."* This audits the **full prohibition surface** of all 13
agents against the cage test, so etalon v0.1 can claim — *with evidence* — that the bundle leaves
deliberate room for discovery, not just walls. It is the artifact behind STATE's **"No cages"** success
factor.

## The test (from `ops/agent-genesis.md`)

> A good boundary **rules out the unsafe/incoherent** without **prescribing the answer**. If a law forces
> a single outcome, it has stopped being a boundary and become the solution — suspect it.

**Role-relative refinement (DL-26, this audit).** The test is **relative to the agent's role.** Removing
discovery is only a *cage* where discovery is the agent's *job*. A **faithful executor** (provider,
execution, monitor) is *meant* to be deterministic — its lack of a discovery surface is correct scoping,
not a cage. So we classify each agent first by role, then apply the test:

- **Discoverers** own a real solution space and must be left room to search it.
- **Faithful executors / integrity-keepers** are deterministic by mandate; "no room" is correct, not caged.

## Method

Surveyed all ~67 `*-NEV-*` prohibitions plus the configured gates across the 13 agent law books
(`agents/*/laws/laws.md`). Each clause was classed as a **role boundary** (separation of concerns), a
**safety/integrity rule**, or a **prescription** (a cage). Discovery surface = the space the agent owns.

## Per-agent verdict

| Agent | Role | Constraint character | Discovery surface | Verdict |
| --- | --- | --- | --- | --- |
| scanner | discoverer | role + safety boundaries | ranking/selection within the technical universe | space-leaving (surface implicit) |
| analyst | discoverer | role + safety boundaries | how to score & weight the signal set | space-leaving (surface implicit) |
| forecaster | discoverer | effect-bounded (shadow-only) | model & feature design (method fully open) | space-leaving |
| researcher | discoverer | bounds on forbidden combos | parameter proposals within the lawful set | space-leaving |
| curator | discoverer | promotion-gated | dataset composition & model training | space-leaving |
| operator | discoverer-lite | scope boundaries | NL intent → policy mapping | space-leaving (scope-bounded) |
| portfolio_manager | mixed | role + safety gates | the tunable **risk envelope** (sizing mechanics are deterministic) | correctly-deterministic on mechanics |
| provider | faithful executor | data-fidelity boundaries | none — by design | correctly-deterministic |
| execution | faithful executor | submit the intent exactly | none — by design | correctly-deterministic |
| monitor | faithful executor | apply stops/exits faithfully | none — by design | correctly-deterministic |
| reporter | faithful executor | report faithfully | none — by design | correctly-deterministic |
| supervisor | integrity-keeper | route per the capability matrix | none — by design | correctly-deterministic |
| master | integrity-keeper | bootstrap & least-privilege grant | none — by design | correctly-deterministic |

## Findings

**F1 — No prohibition is a cage.** Every NEV is a role boundary (`never sizes`, `never decides what to
trade`, `never self-promotes`) or a safety/integrity rule (`never skip the idempotency key`, `never log
the API key`, `never swallow a fault`). Each rules out the unsafe/incoherent without prescribing *what to
find*. **The bundle's constraint surface is not a cage** — this is positive evidence for etalon v0.1.

**F2 — The real gap: discovery surfaces are *implicit*.** The laws declare the **walls** (NEV), the
**capabilities** (CAP), and the **dials** (PARAM / `tunable`) — but no agent explicitly **names the space
it owns and may creatively search.** The room exists; it is undeclared. A reader of the etalon cannot see,
per agent, *"what is this agent free to discover here?"* — which is exactly what DL-19 says a creative-space
bundle must make legible. **Recommendation:** add a **"Discovery surface"** section to the law schema
(per discoverer: the lawful space it owns + how it may search it). This edits the **LOCKED `_TEMPLATE.md`**,
so it is a deliberate law-cycle change — **deferred to its own cycle, not done here.**

**F3 — Discovery today is dial-only.** Where a space exists (e.g. the analyst's scoring weights), the only
search mechanism is `tunable`-tuning + the deferred optimizer. DL-19 extends LAW-01 from *"tune the dials"*
to *"search the lawful space for a better solution"* (lawful **re-composition**, not just dials) — that
second axis has **no mechanism yet**. It is gated behind the deferred CI-6 optimiser and the discovery
discipline (DL-20).

**F4 — Drift found (logged).** The PM `laws.md` changelog footer reads *"v0 — drafted… Not yet locked"*,
but `docs/laws/INDEX.md`, `CLAUDE.md`, and memory record PM as **LOCKED v1 (S70)**. The footer is stale.
Logged to `drift-register.md`; the PM changelog is reconciled to v1 + the PM-NEV-06 amendment.

## Verdict

**The bundle is not a cage.** Its constraint surface is healthy boundaries and safety rules; the
deterministic agents are deterministic *by mandate*, not by over-constraint. The DL-19 work that remains
is **positive, not corrective** — make the discovery surfaces *explicit* (name the rooms, not just the
walls) and give lawful-space search a mechanism (F2, F3). Both are gated, sequenced increments, not gaps in
the walls. **STATE "No cages" success factor: satisfied — audited, no cages found; the refinement (DL-26)
and the two positive follow-ups are recorded.**
