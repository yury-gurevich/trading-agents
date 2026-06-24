# Agent-bundle genesis — the etalon and how to reproduce it

**Status:** living standard (v0.1, 2026-06-24) · **Owner:** operator + AI · governed by `laws/LAW-01`

> The platform's real product is not any single agent — it is the **method that reproduces
> agent-bundles**. Each bundle is a written-down unit of *what good looks like*, so that intent
> survives the human↔AI handoff and the system can rely on it **by default** instead of re-deriving
> it. This document is the hand-crafted **etalon**: the reference specimen *and* the generative
> method. The denser and more explicit the boundaries recorded here, the more faithfully the system
> can reproduce them — and, eventually, generate new bundles itself (the self-bootstrap moonshot).
>
> This etalon is **extracted from practice**, not invented: it names the pattern we have now built
> three times. Its boundaries are meant to be *refined by the operator* — that refinement is the work.

**Sequence — first the reference, then the copier.** The immediate goal is **not** a generator. It is
to bring the **trading-agents bundle itself to demonstrated perfection** — *that finished bundle is
etalon v0.1*. You cannot reproduce a reference that is not yet a reference. The generator (see
*self-reproduction*, below) is the **far endgame**, earned only once the etalon is proven complete.

## Laws define a space, not a solution — creativity is first-class

The laws, charters, gates, and NEVERs **do not prescribe the solution**. They draw the **boundaries of
a space**; inside it, the **agents own and creatively discover** the solution. The constraints say
*where the walls are*, never *what to find in the room*.

- A bundle that is only gates and NEVERs defines a **cage**, not a creative space — and a cage cannot
  discover anything. Each charter must therefore leave **deliberate room for discovery**: the *what to
  find* is the agent's; only the *where it may not go* is the law's.
- This extends LAW-01: not merely "tune the dials," but **search the lawful space for a better
  solution** — the dials are one axis; creative re-composition within bounds is another.
- The test of a good boundary: it **rules out the unsafe/incoherent** without **prescribing the
  answer**. If a law forces a single outcome, it has stopped being a boundary and become the solution —
  suspect it.
- Ownership: the **solution belongs to the agents** that discover it; the laws (and the operator) own
  only the **space** and the **gate** that admits a discovery as good.

---

## What a bundle IS — the parts

A bundle is the full set below, not just code. Each part has a fixed home and a template.

| Part | Artifact / location | Role | Template |
| --- | --- | --- | --- |
| **Identity & laws** | a charter (`ops/departments/<n>/charter.md`) or an agent `laws.md` | the bounded remit + IN/OUT scope + the hard NEVERs | `ops/_template/charter.md` · `docs/laws/_TEMPLATE.md` |
| **Gates** | charter §OPS-GATE | GO/NO-GO preconditions — *validate-then-run* | — |
| **Runbooks** | charter §OPS-ACT | the actions: idempotent? dry-run? postcondition? rollback? | — |
| **Points of no return** | charter §OPS-PNR + `ops/maintenance/points-of-no-return.md` | every irreversible step, guarded | — |
| **Parameters** | `tunable()` in the agent's settings | the dials, bounded + justified | `kernel/config.py` |
| **Recorded decisions** | ADR (`docs/decisions/`) / design-log / `ops/maintenance/ledger.md` | the *why* + the road not taken (LAW-06) | ADR frontmatter |
| **Navigability** | `INDEX.md` per folder, README, live cross-links | findable by humans + AI (Housekeeping) | — |
| **Runtime binding** | `.claude/agents/<name>.md` | wires the laws to an executable agent | `librarian.md` / `tuner.md` |
| **Graduation** | LAW-01 CI-05 | human-gated → automatic, *earned* by a clean ledger | — |

## The genesis method — how to birth a bundle

1. **Name the recurring process.** The "I see an agent here" moment: a bounded, repeatable remit
   with an owner and a measurable goal.
2. **Write the charter** from `ops/_template/charter.md` — fill *every* section; make IN/OUT
   **testable predicates** (they become the gates).
3. **Record the why** in the design-log while fresh; promote to an **ADR** if it closes a question
   "forever" (LAW-06). Capture the road not taken.
4. **Wire the runtime binding** — `.claude/agents/<name>.md` whose body **points at the charter as
   the single source of truth** (never restates it) and enforces its gates + NEVERs.
5. **Register** in `ops/INDEX.md` + `ops/org-map.md`, and write a `ledger.md` row.
6. **Graduate** when the ledger earns it (LAW-01 CI-05) — human-gated until a clean track record.

## The invariants — boundaries every bundle must hold

These are what make bundles interchangeable, legible, and reproducible. A bundle that breaks one is
not to the etalon.

- **One source of truth.** The charter/`laws.md` is canonical; the runtime binding only *points*.
- **Every NEVER is explicit**, and every irreversible step is a **PNR** with a confirm + snapshot.
- **Validate-then-run.** Anything we can anticipate is a gate, never a mid-run error.
- **Nothing blind.** No tuning/promotion/deletion without recorded evidence + operator gate
  (LAW-01 CI-03) — and everything recorded (LAW-06).
- **Reversible-or-PNR**, and **del-before-delete** (recoverable trash, not destruction).
- **Every folder self-describes** with an `INDEX.md`.

## The reference specimens (copy these)

| Bundle | Laws | Runtime binding | State |
| --- | --- | --- | --- |
| **Experimentation & Tuning** | `ops/departments/experimentation/charter.md` | `.claude/agents/tuner.md` | charter + binding; machinery = CI-1…CI-6 (ADR-0013) |
| **Housekeeping & Navigability** | `ops/departments/housekeeping/charter.md` | `.claude/agents/librarian.md` | charter + binding; functional now |
| **Pipeline agents** (provider, scanner, …) | `agents/<n>/laws/laws.md` | the running agents | the original specimens (LOCKED v1) |

## The endgame — self-reproduction (DEFERRED, not now)

The destination is a **generator** that, given a named process, emits the bundle skeleton from this
etalon — charter stub, binding stub, INDEX rows, ledger row — for a human to fill and gate. At that
point the platform produces its own agents from its own written standard. **This document is the spec
that generator targets**; every boundary we add here is one less thing it has to be told.

**But it is too early.** The gate to start building the generator is: **etalon v0.1 — the
trading-agents bundle — is demonstrably perfect** (complete laws, green clauses, a finished pipeline
that trades, every part of the bundle present and coherent, room-for-creativity included). Until the
reference is perfect, a copier would only reproduce its gaps. **Perfect the bundle first.**
