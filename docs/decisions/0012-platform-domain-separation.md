---
type: Architecture Decision
status: accepted
closes: "Is this a trading application or a domain-agnostic platform? Where is the wall between the reusable substrate and the trading pack, and is it enforced now or just declared?"
tags: [platform, architecture, substrate, decoupling, boundaries, text-defined-business]
---

# ADR-0012 — Platform / domain separation: substrate vs trading pack

**Status:** Accepted
**Date:** 2026-06-21
**Deciders:** Operator

---

## Context

The system has quietly matured into two things wearing one name. Underneath the trading
logic sits a **domain-agnostic substrate**: a master that bootstraps any component with
minimum-privilege **capability grants**, **typed contracts** exchanged on a bus, a **laws**
framework that gives each component a must/never/owns charter, an **ops constitution**
(gates, recovery, points-of-no-return, residency), and a **provenance graph**. None of that
is financial. Trading is the *first domain expressed on top of it* — a **pack**.

This makes the product a platform for **text-defined businesses**: the laws + charters +
contracts are the source code of a business; change the text, change the business. The same
substrate could, in principle, run a manufacturing line (agents driving machinery instead of
a broker) under the same governance.

Two forces are in tension:

- **Generality built ahead of need is waste** (the platform trap). We have exactly one pack;
  speculative platform features would never ship.
- **But the substrate must stay extractable** — a single trading concept leaking into the
  substrate quietly welds the platform shut, and forecloses the moonshot (#7) and any second
  pack.

## Decision

1. **This is a platform; trading is its first pack.** We name it so, and design accordingly.
2. **A wall is declared between SUBSTRATE and PACK** — **de jure now, de facto later.**
   - *De jure (now):* a discipline every decision must respect. **No substrate component may
     name, import, or depend on a trading-specific concept.** Trading-specific configuration
     (the agent roster, grant tables, data feeds, risk rules) is **pack-provided input** to
     the substrate, never hardcoded in it.
   - *De facto (later):* physical separation — package boundary / `import-linter` contract /
     separate repo — is deferred until a **second pack** justifies the cost. Per LAW-01, that
     is the trigger to revisit and harden.
3. **Generality is NOT built speculatively.** This ADR is a *cleanliness* discipline, not a
   refactor mandate. We do not add abstractions for businesses we do not have.

### First-cut inventory (provisional under LAW-01)

| Layer | Substrate (platform) | Pack (trading) |
| --- | --- | --- |
| kernel | bus, graph store, claim-check, crypto, bootstrap, errors | — |
| master | bootstrap, identity, the *mechanism* of capability grants | the 12-agent roster it grants to |
| contracts | `common/` base classes, `AgentContract`/`Capability`, master msgs | provider/scanner/… DTOs |
| laws | the schema + cycle (`docs/laws/_TEMPLATE.md`, the process) | each trading agent's `laws.md` |
| ops | the whole `ops/` realm (gates, recovery, residency, CLI) | trading-specific runbooks |
| agents | — | scanner … provider (13) + their domain logic |
| feeds | the `DataSource` protocol shape | Tiingo/Alpaca/Finnhub adapters |

### Known leaks (stop widening; fix opportunistically)

- **`agents/master` `DEFAULT_GRANTS` hardcodes the 12 trading agent types.** This is
  pack-specific policy living in the substrate. Target: master accepts a grant policy; the
  trading pack supplies the roster.
- **`contracts/` mixes** generic base classes with trading DTOs in one tree.

## Consequences

- **Every design decision now asks "substrate or pack?"** and keeps trading concepts out of
  the substrate. This is the cheap insurance the owner asked for: decoupling *de jure* before
  it is worth doing *de facto*.
- **The substrate stays extractable**, keeping the door open to the moonshot (#7) and future
  packs without walking through it today.
- **We accept the current leaks**; we simply stop adding new ones and fix the named ones when
  convenient.
- **Re-opened under LAW-01** when a second pack appears — that is when the wall graduates from
  declared to enforced. This ADR is the defendable record (LAW-05) of why the seam exists.

## Links

- Moonshot #7 (`docs/moonshots.md`) — the platform bootstrapping its own proof.
- ADR-0007 (container-per-agent + master) — the substrate's deployment model.
- ADR-0010 (LLM quality gate) — the champion-challenger pattern #7 lifts to the business level.
- `ops/laws/LAW-01` (continuous improvement) — why this is revisable; `LAW-05` — why it's recorded.

## Correction — 2026-09-26, S232 (P20 E20.2): the named leaks close, and one this ADR did not name

**Leak 1 (`DEFAULT_GRANTS` hardcodes the trading roster) closed three months ago and this ADR never
re-measured it.** [DL-12](../design-log.md) records S84–S86 (2026-06-22): the grant table and secret
map moved to `orchestration/packs/trading_*.json`, loaded by path, and the master image ships neither
— the pack policy travels as deploy-time config (`MASTER_GRANT_POLICY_B64` etc.). Measured again at
S232's spec (2026-09-25): `DEFAULT_GRANTS` appears in **0** `.py` files. The master's own law book had
not caught up — `MST-NEV-01`, `MST-SEC-03` and `MST-DEP-03` still named the deleted constant, and
`MST-SEC-03` asserted the table *"cannot be changed by runtime config"* while its own `PARAM` table
marked the delivery fields `Tunable YES`. S232's law cycle (master laws v1.6, [DRIFT-075](../laws/drift-register.md))
corrects all three clauses to name the pack data actually consulted.

**Leak 2 (`contracts/` mixes generic base classes with trading DTOs) closes in S232.** The substrate
vocabulary — `_Frozen`, `Provenance`, `Explanation` (three names in `contracts/common.py`) and the
master's handshake messages (`contracts/master.py`, 107 lines) — moves into `kernel/payload.py` and
`kernel/handshake.py`. `contracts/common.py` re-exports the three names explicitly (mypy strict); every
other import site is unchanged. The master's 10 remaining imports of `contracts.master` are repointed,
`agents/master/Dockerfile` drops `COPY contracts/`, and `.importlinter` gains a `substrate-imports-no-pack`
contract (source: `kernel`, `agents.master`) alongside a widened `agents-are-islands` (adds
`agents.master`, `agents.deliberator` — 14 modules).

**A third leak this ADR never named, of the same kind: the served-agent roster.** `kernel/serve_transport.py`
hardcoded 9 pack agent-type string literals (`SERVED_AGENT_TYPES`, the deliberator peer/manager types,
and `"deliberator"` in the image-directory lookup) — the same shape as leak 1 (*"the agent roster …
is pack-provided input to the substrate, never hardcoded in it"*, Decision 2), just not in `agents/master`.
S232 moves it to `orchestration/packs/trading_served_agents.json`, read by path from a new
`scripts/served_agent_roster.py` loader (never imported by the substrate). `kernel/serve_transport.py`
keeps only the genuinely generic pieces: `request_topic`, `reply_topic`, `consumer_from_env`.

**Deferred residue (recorded, not closed — see S232's Out of scope and DL-228):**

- `kernel/deliberation_prompts.py` — trading prompts inside the kernel. Moving the module would change
  a module name hashed into every `LLMCall`'s prompt-recipe digest (`kernel/prompt_recipe.py` hashes
  `__name__`), breaking comparability with every already-recorded debate. Stays until a second pack
  actually deliberates.
- `kernel/market_pack.py` — a market-shaped protocol only the trading dashboard reads. Stays until a
  pack that is not a market needs the kernel to register something there.
- Master tests reading trading pack files by path (`agents/master/tests/helpers.py`) — a data
  dependency, not an import; moving 12 files buys the wall nothing.
- The supervisor and the operator still carry trading rosters (per this ADR's first-cut table, both
  stay pack); whether a second pack needs a substrate supervisor is E20.3's question.

**What this correction does not do.** It does not reverse the Decision above, and it does not claim
*de facto* enforcement is complete — `import-linter` reads imports, not names: the deliberation prompts
and the market-pack protocol are trading content that still loads through `kernel/__init__.py`, and a
green wall does not mean *"the substrate knows nothing of trading."* The *de jure → de facto* re-opening
this ADR deferred to a second pack remains E20.5's to record.
