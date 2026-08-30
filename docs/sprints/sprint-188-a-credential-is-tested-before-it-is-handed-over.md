<!-- Agent: planning | Role: sprint handover -->
# Sprint 188 — a credential is tested before it is handed over

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-188-a-credential-is-tested-before-it-is-handed-over`
**Status:** SPEC
**Version:** *next available MINOR at merge*
**Effort:** M
**Decisions:** DL-36 (the policy this finally implements) · [DL-134](../design-log.md) (the addendum that found it unwired) · a new DL for the five design decisions below

> **Why this bump kind.** MINOR. Master gains a capability it does not have: refusing activation when
> a credential it is about to hand over does not work. The substrate for it was built and tested;
> nothing in production could reach it, so no behaviour existed to fix.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/master/laws/laws.md` | Master's **locked constitution** (v1 LOCKED) | **Read-only during a build.** A clause you believe is wrong is a `drift-register.md` row plus a report — never a quiet edit |
| `agents/master/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted. Master's rollup is **10 / 39** — most of what you will lean on is ⬜ |
| `docs/laws/conventions.md`, `ledger.md`, `drift-register.md` | Umbrella laws + rollups | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`SEC`**, **`NEV`**, **`FAIL`**, **`OBS`**, **`DEP`**, **`CAP`**, **`PARAM`**.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read `test-plan.md` alongside `laws.md`. If a clause you rely on is ⬜, say so.
3. Read `docs/laws/conventions.md` and `docs/laws/drift-register.md`.
4. **Answer the law-cycle question below.**
5. **Write the Law reading record** (bottom of this file) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answer before step 5

> Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously make?

**Yes — and the answer is already decided: this sprint owes a full law cycle.** No `contracts/` file
changes, but master gains two guarantees it does not currently make:

- activation **refuses** when a required credential fails its declared test, and
- every activation **records which credentials were tested**.

So: new clauses in `agents/master/laws/laws.md` (bump to **v1.1**, Changelog line), a `test-plan.md`
row per clause, the clause ID cited in each test docstring, the rollup updated in **both**
`docs/laws/ledger.md` **and** `docs/laws/INDEX.md`, and a `drift-register.md` row for anything the
change slips under.

🪤 **The rollup is derived, not declared.** `make ci` recomputes it — let the gate tell you the number.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/master/credential_probes.py` *(new)* | `agents/master/laws/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `SEC` (master is the sole Key Vault accessor — a probe handles live secret material), `FAIL` (fail-safe posture) |
| `agents/master/entrypoint.py` | same | `DEP` / `CAP` — what master is allowed to load and from where |
| `agents/master/agent.py` (read only, likely no edit) | same | `NEV` — never hand over a credential the policy did not grant |
| `orchestration/packs/trading_credential_tests.json` *(new)* | ADR-0012 (platform/pack wall) | the declaration is **pack** data; the mechanism is **substrate** |
| `infra/deploy-agents.ps1` | — | production state: full cycle, and see the cmd.exe ceiling trap |

⚠️ **The invariant this sprint must not break: the master image stays pack-agnostic.** It contains
`kernel/`, `contracts/`, `agents/master/` and nothing else (S86 / DL-12 leak #2, commit `9326872`:
*"deploy wiring — feed pack policy to master, image stays pure"*). If your change requires importing
`orchestration/` or `agents/provider/` from inside the master image, **stop and report** — you have
taken the rejected option.

---

## Goal

At merge, the deployed master runs a **declared** liveness test against every credential it is about
to hand an agent, and **refuses activation** when a required one fails — so a broken provider key is
caught at activation, in an escalation that names it, instead of six nights later in a debate
transcript full of fail-opens.

## Why (context)

On 2026-08-19 the deliberator's OpenAI key ran dry and on 2026-08-20 the Anthropic key hit an
operator-set spend limit. For **six scheduled nights** the fleet activated cleanly, traded unvetoed,
and failed the acceptance gate every night for an external non-defect ([DL-125](../design-log.md)).
The mechanism designed to catch exactly this — *"master tests every credential before giving it to an
agent"* (DL-36 Piece A) — was **built, tested, and unreachable**.

Found 2026-08-30 while writing [DL-134](../design-log.md), looking for a cheap way to prove the
master → Key Vault → deliberator path without spending a whole scheduled run. There is no cheap way,
because there is no test. That is what this sprint fixes.

### Measured, 2026-08-30 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Master receives no credential tests in production | `credential_tests: tuple[CredentialTest, ...] = ()` at `agents/master/agent.py:57`; `entrypoint.py:90-96` constructs `MasterAgent` **without the argument** | *[measured 2026-08-30]* file read |
| The trading composition root never runs | `build_trading_master` (`orchestration/master_serve.py`) is imported **only** by `orchestration/tests/test_master_serve.py` | *[measured 2026-08-30]* repo-wide grep |
| …and could not run even if called | `agents/master/Dockerfile` copies only `kernel/ contracts/ agents/master/`; `CMD ["python","-m","agents.master.entrypoint"]`; no CMD override in `infra/deploy-agents.ps1` | *[measured 2026-08-30]* |
| The remediation chain is unreachable for the same reason | `handle_activation_remediation` is called only inside `if failures:`; `failures` can only be non-empty if `credential_tests` is non-empty | *[measured 2026-08-30]* `agents/master/agent.py:105-131` |
| 8 live probes already exist | `tiingo`, `fmp`, `finnhub`, `alpaca-data`, `alpaca-broker`, `openai`, `anthropic`, `postgres` in `orchestration/packs/trading_vault_probes.py` | *[measured 2026-08-30]* |
| …but they run only at **seed** time, from the operator's machine | called only by `scripts/seed_key_vault.py` and `scripts/seed_key_vault_live_check.py` | *[measured 2026-08-30]* |
| Packs already reach master as base64 JSON in env | live master env: `MASTER_GRANT_POLICY_B64`, `MASTER_SECRET_MAP_B64`, `GRAPH_VOCABULARY_B64` (+5 others) | *[measured 2026-08-30]* `az containerapp show -n master` |
| Live master has no remediation override | 8 env keys, **none** is `MASTER_REMEDIATION_MODE` → the `"manual"` default applies | *[measured 2026-08-30]* same query |
| Master module sizes (200 = hard block) | `entrypoint.py` **150**, `agent.py` **182**, `store.py` **194**, `remediation.py` **199**, `credential_test.py` **103** | *[measured 2026-08-30]* `wc -l` |
| Master law rollup | LOCKED v1, **10 / 39** clauses proven | *[measured 2026-08-30]* `docs/laws/ledger.md:51` |
| `az` command-line ceiling | ~**8,191** chars via `az.cmd`; `GRAPH_VOCABULARY_B64` alone is >12,000 and needs its own narrow call | *[carried from DL-85 — not re-measured]* `infra/deploy-agents.ps1:74-82` |

---

## Scope — and what is deliberately NOT here

1. **The failing test first: activation refuses a bad required credential.** A declared probe that
   answers `401` makes `activate()` raise `ActivationRefused`, leaves the agent in `PRE_FLIGHT`, and
   writes an `Escalation` naming the credential. Assert on the raised state and the written node, not
   on a log line.
2. **A declarative probe mechanism inside the master substrate.** New module
   `agents/master/credential_probes.py`, **stdlib only**, which turns a JSON declaration into
   `tuple[CredentialTest, ...]`. Two probe kinds are enough for every credential in the pack:
   - `http_status` — method, url, header template, expected status set;
   - `dsn_select_1` — connect using the named DSN key and `SELECT 1`.
   Header values template the secret by name (`{ANTHROPIC_API_KEY}`) resolved from the config
   `resolve_and_test` already produces.
3. **Loader + entrypoint wiring.** `MASTER_CREDENTIAL_TESTS_B64` with a path fallback — the **same
   shape** as `MASTER_SECRET_MAP_B64`, so follow `parse_secret_map` / `load_secret_map` rather than
   inventing a second convention. Build the tests and a `PassCache`, pass both to `MasterAgent`.
4. **The trading declaration** — `orchestration/packs/trading_credential_tests.json`, per agent type.
   Start from the eight probes that already exist; express them as `http_status` / `dsn_select_1`.
5. **Deploy wiring** — `infra/deploy-agents.ps1` passes the new env var, next to the grant policy and
   secret map.
6. **The law cycle** named above, master laws → **v1.1**.
7. **The live functionality check** — see *Sequencing after merge*.

### Out of scope (do NOT build this sprint)

- **Wiring the remediation catalogue, executors, or the remediation LLM.** They are unwired for the
  same root cause and it is tempting to fix both. Do not. 🚨 **This sprint makes the remediation path
  *reachable for the first time*** — before it, `failures` was always empty. `remediation_mode`
  defaults to `"manual"` (refuse + escalate to a human) and the live master sets no override
  (measured). **Leave it that way. Do not set `automatic`.**
- **Moving the SDK-based probes into the master image.** `tiingo`/`fmp`/`finnhub`/`alpaca-data` are
  written against `agents.provider.*` classes. Their *auth* check is an HTTP call; re-express it, do
  not import them. The image stays pure.
- **Deleting `orchestration/master_serve.py`.** It is production-dead, and that is worth deciding —
  separately, with its own reasoning. Not here.
- **Testing credentials anywhere except activation.** No periodic re-probing, no health endpoint.
- **No ADR reversal.** An ADR is reversed by a new ADR, never by a sprint.

### The road not taken (LAW-06)

- **Import the pack probes from `entrypoint.py`.** Rejected twice over: `import-linter` forbids
  `agents → orchestration`, and `orchestration/` is not in the master image, so the import would fail
  at runtime even if the contract allowed it.
- **Copy `orchestration/` and `agents/provider/` into the master image and switch `CMD` to
  `orchestration.master_serve`.** Rejected: it breaks "image stays pure" (S86 / DL-12 leak #2) and it
  would let arbitrary pack Python execute inside the **sole Key Vault accessor** — the one process in
  the fleet where that matters most.
- **Have master call a probe endpoint on each agent.** Rejected: it inverts the dependency — the agent
  would have to be running before master decides whether to activate it.
- **Reuse `ProbeResult` from `vault_seed` as the test return type.** Rejected: `CredentialTest.run`
  is `Callable[[Mapping[str,str]], bool]` and already exists. Adapt at the edge; do not widen a
  substrate type to match a pack helper.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**

1. **Declaration-as-data, and which probe kinds the substrate implements.** The fork is data vs code.
   Data is chosen (above) — record *why*, and record the kind vocabulary you settle on. A third kind
   added later is cheap; a wrong abstraction here is not.
2. **🚨 Transport failure is not credential failure — and this is the subtle one.** A probe that
   cannot distinguish *"your key is rejected"* from *"the network blipped"* will halt the whole fleet
   on a transient DNS failure, which is worse than the outage this sprint exists to prevent.
   **Decide by the response, not by the exception type**: an HTTP response of `401`/`403` (or the
   declared failure statuses) is a **credential failure** → a required one blocks activation. A
   timeout, DNS error, connection reset or `5xx` is a **transport failure** → record a fault, do
   **not** block, and do **not** cache a pass. Write this down; it is the clause an `OBS`/`FAIL` law
   row will cite.
3. **Which credentials are `required` per agent type.** A required failure blocks activation, so this
   list is a fleet-availability decision, not a formality. Getting it wrong turns one degraded feed
   into a fleet that will not start. Justify each `required: true` individually.
4. **`cheap` vs `costly`, and the `PassCache` TTL.** An auth probe like `/v1/models` costs no tokens,
   so most are `cheap` — but *cheap* still means an outbound HTTP call on **every** activation, and
   the fleet activates 16 apps. Decide the TTL with that number in front of you.
5. **What activation records.** New props on the existing activation node (which credentials were
   tested, which passed, which were skipped as cached) → a **graph vocabulary change**, which makes
   the deploy a full `up`. Confirm the vocabulary entry is added, or the fail-closed write guard will
   reject the write mid-cascade (S148 stall, DL-85).

🪤 **Take the next free DL number, then re-check it at merge.** The log has historic duplicates and
entries are prepended at the top *and* appended at the bottom. A branch cut before another DL lands
will collide even when the number was free at branch time (S183 hit this).

---

## Blast radius — measured 2026-08-30

| What | Detail |
| --- | --- |
| Files changed | `agents/master/credential_probes.py` **(new)**; `agents/master/entrypoint.py` **150 → must stay < 200** (put the loader in the new module, not here); `orchestration/packs/trading_credential_tests.json` **(new)**; `orchestration/packs/trading_graph_vocabulary.json`; `infra/deploy-agents.ps1`; `agents/master/laws/laws.md` + `test-plan.md`; `docs/laws/ledger.md`, `docs/laws/INDEX.md`, `docs/laws/drift-register.md`; new tests |
| Agents affected | **master only.** No agent imports another; the new module imports stdlib + `agents.master.*` only |
| Contract change? | No `contracts/` file — **but a new guarantee, so the law cycle is mandatory** |
| Graph vocabulary change? | **Yes** (decision 5) → the deploy is a **full `up`**, not a retag |
| New env keys / tunables | `MASTER_CREDENTIAL_TESTS_B64`; a `PassCache` TTL tunable → also forces a full `up` |
| Deploy implication | **Full `up`.** 🚨 Not before `sched-2026-08-31` — see *Sequencing* |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Record the five design decisions** in `docs/design-log.md`, with rejected alternatives.
3. **Plant A1 and watch it fail.** Paste the red output.
4. **Implement** the probe kinds, the loader, the entrypoint wiring, then the pack declaration.
5. **Law cycle** — clauses, test-plan rows, docstring citations, both rollups, drift row.
6. **Prove the guards can fail (DL-70)** — for each new guard, break it, watch it go red, restore.
   State this per guard, not once for all of them.
7. **`make ci` green** — all 12 steps, **redirected to a file, never piped**.
8. **Fill the handback sections** at the bottom of this file.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 A required credential whose probe answers `401` refuses activation | declaration with one required `http_status` probe; fake transport returning 401 | `ActivationRefused` raised, agent stays `PRE_FLIGHT`, an `Escalation` node names that credential |
| A2 | All probes passing activates normally and records what was tested | all-pass fake transport | activation succeeds **and** the activation node lists the tested credential names |
| A3 | 🪤 A transport failure is **not** a credential failure | fake transport raising timeout / returning 503 | activation **proceeds**, a fault is recorded naming the transport cause, and **no pass is cached** |
| A4 | An optional credential's failure does not block | `required: false` probe returning 401 | activation succeeds; the failure is still recorded |
| A5 | `PassCache` skips a costly probe inside the TTL and re-runs it outside | injected clock | probe call count 1 then 2; a cached pass never turns a later real failure green |
| A6 | 🪤 An unknown probe kind is refused loudly at load | declaration with `kind: "nope"` | load raises; it does **not** skip the entry and report success. *(This is item 35's shape — a silent skip is the bug class this sprint is about.)* |
| A7 | 🪤 **No secret value appears anywhere** | probe with a known sentinel secret, forced to fail | the sentinel appears in **no** fault message, escalation prop, probe record or exception text — assert on the written nodes, not by eyeballing output |
| A8 | An empty or absent declaration is loud, not silently green | `MASTER_CREDENTIAL_TESTS_B64` unset | a startup fault/refusal names it. **Zero tests must never read as "all credentials fine"** — that is the exact state this sprint found in production |

---

## Success factors

- [ ] A required credential failing its declared probe **refuses activation**, leaves the agent in `PRE_FLIGHT`, and writes an `Escalation` naming it — proven by A1, not asserted.
- [ ] A transport failure does **not** refuse activation, and does not cache a pass (A3).
- [ ] No secret value reaches any fault, node prop, or exception text (A7).
- [ ] An empty/absent declaration is loud (A8).
- [ ] The master image still contains only `kernel/`, `contracts/`, `agents/master/` — `Dockerfile` unchanged, or the change is named and justified.
- [ ] `remediation_mode` is untouched and still `"manual"`; nothing in this sprint sets `"automatic"`.
- [ ] Design decisions recorded with rejected alternatives.
- [ ] Law cycle done: master laws **v1.1**, a test-plan row per clause, clause IDs cited in docstrings, rollup updated in **both** `ledger.md` and `INDEX.md`, drift row filed.
- [ ] Every new guard planted, watched to fail, restored — **stated per guard**.
- [ ] Every touched module < 200 lines. `entrypoint.py` is at **150**; report its final count.
- [ ] `make ci` exit 0, 100.00 % coverage, redirected to a file.
- [ ] `make gate-ran` `GATE PROVEN` for the branch tip, run from the worktree whose `HEAD` is that commit, printed SHA checked.

---

## Traps

🪤 **The thing that looks like success and is not: a declaration that fails to load, leaving zero
tests.** Every probe "passes", activation is clean, and the fleet is exactly as blind as it is today —
with a green sprint on top. A8 exists for this. Assert the **count** of loaded tests, not just that
loading did not raise.

🪤 **Transport failure vs credential failure** (design decision 2). A fail-closed probe that treats a
DNS blip as a bad key halts the fleet. Read the *response*, not the exception class.

🪤 **This sprint makes the remediation path reachable for the first time.** Before it, `failures` was
always empty, so `handle_activation_remediation` was dead code. After it, a failing credential enters
that flow. `remediation_mode` is `"manual"` by default and the live master sets no override
(measured 2026-08-30) — **verify that is still true at deploy time**, and change nothing.

🪤 **The `az` command-line ceiling.** The new B64 var rides the same `containerapp create` call as
`MASTER_GRANT_POLICY_B64` and `MASTER_SECRET_MAP_B64`, and `az.cmd` inherits cmd's ~8,191-character
limit. Keep `trading_credential_tests.json` small. If the call goes over, follow
`GRAPH_VOCABULARY_B64`'s pattern — its own narrow call after create (DL-85), **not** a shortened
declaration.

🪤 **A worktree has no `.env`.** Every probe test must run against a fake transport and fixture
config. Any proof that needs a live secret is **vacuous in a worktree** — state which tree you ran in.

🪤 **`make ci` never through a pipe.** `make ci | tail` reports `tail`'s exit code. Redirect to a file
and read the file.

🪤 **The graph vocabulary change is fail-closed.** If decision 5 adds props without a
`trading_graph_vocabulary.json` entry, the write guard rejects mid-cascade and the run stalls
(S148 / DL-85). Add the entry in the same commit as the prop.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `entrypoint.py` **150**, `agent.py` **182**, `store.py` **194**, `remediation.py` **199**, `credential_test.py` **103**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds. 🪤 A **mode selector** is *not* a
  tunable — check master's PARAM table before registering. A TTL **is** a tunable; a probe *kind* is not.
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **all 12 steps** green, **100.00 % coverage floor**, redirected to a file.
- Version bump of the kind named at the top (**MINOR**), `uv.lock` staged with it.
- Secrets never through the worktree.

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**.
   🪤 Run it from the worktree whose `HEAD` is the commit you are proving — it resolves the SHA from
   the working directory and **ignores** a `SHA=` argument. Check the printed SHA against
   `git rev-parse HEAD`.
2. Merge to `main` locally and push. 🪤 Check you are not on the branch already.
3. **Post-merge CodeQL** — `codeql.yml` runs only on `main`, so a green branch gate is not proof.
4. **Deploy: a full `up`, and NOT before `sched-2026-08-31`.** Monday's scheduled run is the proof of
   the `s187` deploy and of the master → Key Vault → deliberator path ([DL-135](../design-log.md));
   a full `up` before it destroys that. Sequence behind S172's deploy so the two `up`s do not collide.
5. **Live functionality check, then tear down** (record in `docs/laws/functionality-checks.md`):
   point one non-critical agent's declaration at a deliberately wrong secret, watch activation refuse
   with an `Escalation` naming it, restore the declaration, watch the same agent activate. **Do not
   corrupt a Key Vault secret to produce this** — change the declaration, which is data you control
   and can revert without touching secret material.

---

## Handover — paste this to Codex

```text
Branch: sprint-188-a-credential-is-tested-before-it-is-handed-over (create it BEFORE any code, never
work on main). Read docs/sprints/sprint-188-a-credential-is-tested-before-it-is-handed-over.md whole
before starting; this block is a summary, not a replacement.

WHAT IS BROKEN. agents/master/agent.py:57 declares credential_tests: tuple[CredentialTest, ...] = ()
and agents/master/entrypoint.py:90-96 builds MasterAgent without that argument. No pack supplies any.
So DL-36 Piece A - "master tests every credential before handing it to an agent" - runs ZERO tests in
the deployed fleet, and activation succeeding proves nothing. Because failures is then always empty,
handle_activation_remediation is unreachable too. This is why a dead LLM key went unnoticed for six
scheduled nights (DL-125).

WHY THE OBVIOUS FIX IS WRONG. orchestration/master_serve.py already accepts credential_tests, and
orchestration/packs/trading_vault_probes.py already has 8 working probes. You cannot use either from
the master image: agents/master/Dockerfile copies only kernel/, contracts/ and agents/master/, the CMD
is python -m agents.master.entrypoint, and import-linter forbids agents -> orchestration. The master
image stays pack-agnostic (S86 / DL-12, commit 9326872 "image stays pure"). If your design needs to
import orchestration/ or agents/provider/ inside that image, STOP and report - that is the rejected
option.

WHAT TO BUILD. Credential tests reach master as DATA, exactly like the grant policy and secret map
already do (MASTER_GRANT_POLICY_B64, MASTER_SECRET_MAP_B64 - verified on the live app).
1. agents/master/credential_probes.py (new, stdlib only): turns a JSON declaration into
   tuple[CredentialTest, ...]. Two kinds: http_status (method, url, header template, expected
   statuses) and dsn_select_1. Header values template the secret by name from the config
   resolve_and_test already builds.
2. The loader, in that same new module - follow parse_secret_map / load_secret_map, do not invent a
   second convention. entrypoint.py is at 150 lines and the hard block is 200: do NOT put the loader
   there.
3. entrypoint.py: read MASTER_CREDENTIAL_TESTS_B64 (path fallback), pass credential_tests and a
   PassCache to MasterAgent.
4. orchestration/packs/trading_credential_tests.json: the per-agent-type declaration. Re-express the
   existing 8 probes as http_status / dsn_select_1 - do not import them.
5. infra/deploy-agents.ps1: pass the new env var alongside the other two.
6. Full law cycle: master laws v1.1 (two new guarantees - activation refuses on a failed required
   credential; activation records what was tested), test-plan row per clause, clause ID in each test
   docstring, rollup in BOTH docs/laws/ledger.md and docs/laws/INDEX.md, drift row.

ORDER. Read laws -> write the Law reading record -> record the 5 design decisions in
docs/design-log.md WITH rejected alternatives -> plant A1 and watch it fail, paste the red -> then
implement.

THE DECISION THAT MATTERS MOST. Transport failure is NOT credential failure. Decide by the RESPONSE,
not the exception type: 401/403 is a credential failure and a required one blocks activation; a
timeout, DNS error, reset or 5xx is a transport failure - record a fault, do NOT block, do NOT cache
a pass. A probe that treats a DNS blip as a bad key halts the whole fleet, which is worse than the
outage this sprint exists to prevent.

DO NOT:
- Do NOT wire the remediation catalogue, executors or remediation LLM. Same root cause, deliberately
  out of scope. This sprint makes that path REACHABLE for the first time; remediation_mode is
  "manual" by default and the live master sets no override. Leave it. Never set "automatic".
- Do NOT delete orchestration/master_serve.py, even though it is production-dead. Separate decision.
- Do NOT add periodic re-probing or a health endpoint. Activation only.
- Do NOT edit laws.md except as the law cycle above requires; it is LOCKED v1. A clause you think is
  wrong is a drift-register row plus a report.
- Do NOT use # noqa to get under the module size limit.

TRAPS:
- A declaration that fails to load leaves ZERO tests, every probe "passes", and the sprint ships the
  exact blindness it was meant to fix. Assert the COUNT of loaded tests (test A8).
- An unknown probe kind must raise at load, never be skipped silently (test A6). A silent skip is the
  same bug class as item 35.
- No secret value may appear in any fault message, node prop or exception text (test A7) - assert on
  the written nodes, not by reading output.
- Adding node props without a trading_graph_vocabulary.json entry hits the fail-closed write guard
  and stalls the cascade mid-run (S148 / DL-85). Same commit.
- az.cmd inherits cmd's ~8,191-char command line and the new B64 var rides the master create call.
  Keep the JSON small; if it goes over, give it its own narrow call like GRAPH_VOCABULARY_B64 (DL-85).
- A worktree has NO .env. Probe tests use a fake transport and fixture config. State which tree you
  ran in.
- make ci through a pipe reports the pipe's exit code. Redirect to a file and read the file.

VERSION: next available MINOR at merge - do not pin a number.
GATE: make ci exit 0 (12 steps, 100.00% coverage) redirected to a file, then push the branch and get
make gate-ran GATE PROVEN, run from the worktree whose HEAD is that commit, and check the printed SHA
against git rev-parse HEAD. Fill the Closeout block before handing back; a handback with a
placeholder left in it is returned, not repaired.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output.
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02). **Never write a
   `Result:` for work you have not done.**

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

<!-- Which law files you read, which clauses bind, which are unproven, and the law-cycle answer. -->

---

## Test plan results — fill at handback

| # | Result | Evidence |
| --- | --- | --- |
| A1 | | |
| A2 | | |
| A3 | | |
| A4 | | |
| A5 | | |
| A6 | | |
| A7 | | |
| A8 | | |

---

## Closeout — evidence

<!-- Coding agent: replace this comment with the proven result. Required: files changed with final
     line counts, the A1 red output before the fix, the per-guard DL-70 break/restore statement, the
     loaded-test count from A8, confirmation the Dockerfile is unchanged and remediation_mode
     untouched, the exact `make ci` summary (unpiped, redirected to a file), and `make gate-ran`
     output for the final tip with the SHA checked against the worktree HEAD.
     Do not merge until every success factor above is answered with a measurement. -->

---

## Return notes

<!-- Anything you found that this spec got wrong, and anything the next sprint should know. -->
