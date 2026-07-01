# Sprint 104 — Credential-tested activation + escalation on failure (DL-36, Pieces A+B)

**Phase:** Credential-validated activation (DL-36)
**Branch:** `sprint-104-credential-tested-activation`
**Status:** planned
**Effort:** L

---

## Goal

Make the master **test every credential before handing it to an agent**, and on a required-credential
failure **refuse activation (fail-safe) and record an escalation** — never distribute a broken credential
(DL-36; the frenzy that locked Aura was untested Neo4j creds). This is Pieces **A** (test-before-handover)
and **B** (escalation record + human gate + one-shot counter) of DL-36. The LLM remediation planner (C)
and the execute→production→document pipeline (D) are **out** — deferred until their design questions close.

**Operator decisions baked in (2026-07-01):**
- **A+B together** — test-before-handover *and* the escalation/refuse/one-shot structure in one arc.
- **Cheap live + cache costly** — side-effect-free tests run live every activation; costly/side-effecting
  ones (LLM ping, broker submit) use a cached recent pass or a gated flag, never a real call per activation.

## Scope

### In

**Substrate (master, pack-agnostic):**

- `agents/master/credential_test.py` — a `CredentialTest` type: `(env_var, probe, cost)` where `cost ∈
  {cheap, costly}`. A `resolve_and_test(agent_type, store, secret_map, tests, *, force_costly=False,
  cache)` that, for each entitled secret: fetch → if `cheap` run its probe live; if `costly` use the
  cached pass (or run live only when `force_costly`) → include in the config **only on pass**. Returns
  `(config, failures)` where `failures` names each credential that has no passing test.
- `agents/master/agent.activate`: call `resolve_and_test` instead of `resolve_config`. If any **required**
  credential is in `failures`, do **not** issue ACTIVATE — instead write an `Escalation` and raise/return
  a typed `ActivationRefused` (fail-safe: an agent is never activated with an untested/failing credential).
- A test-result **cache** (graph node `CredentialTest` or in-memory keyed by `(env_var, day)`) so a
  recent costly pass counts; cheap tests always run.

**Escalation + human gate (Piece B):**

- `agents/master/store.write_escalation` — an `Escalation` node (master `owns_graph += Escalation`):
  `agent_type`, `failed_credentials`, `mode` (`manual`/`automatic`), `auto_attempts`, `status`
  (`open`/`resolved`), `created_at`. On failure the master writes it and flags for human
  (`supervisor.flag_for_human` or an `Escalation` the human surface lists).
- **Mode + one-shot:** `MasterSettings.remediation_mode` (default `manual`). In `manual`, a failure →
  refuse + escalate + STOP. In `automatic`, allow **one** retry (`auto_attempts` < 1) then force `manual`
  and escalate — the crash-loop bound as governance. (The retry does nothing useful yet without C/D; the
  counter + mode are the structure C/D consume.)
- A read-only surface: `surfaces` query listing open `Escalation`s (so a human can see what's blocked).

**Pack (trading, injected — ADR-0012):**

- `orchestration/packs/trading_credential_tests.json` (or `.py`) — maps each secret env-var to its probe
  + cost + whether it is **required** for the owning agent. Reuses `probes/checks.py` logic (Neo4j
  connect = cheap; Tiingo/FMP/Finnhub/Alpha Vantage auth GET = cheap; Alpaca submit + Anthropic ping =
  costly). Loaded by path, never imported — the master substrate names no trading credential.

### Out

- **C — LLM remediation planning** and **D — execute→production→documentation** (separate sprints; design
  first — see DL-36 open questions).
- The rich approve/set-mode **command** UI (operator command). B ships the `Escalation` node + a read-only
  list; the interactive approval flow lands with C/D.
- No change to the credentials themselves or the deploy wiring (S/the frenzy fix already corrected those).

## Deliverables

- `agents/master/credential_test.py` (substrate mechanism) + `write_escalation` in `store.py` + `activate`
  wired to test-before-handover + `MasterSettings.remediation_mode`.
- `orchestration/packs/trading_credential_tests.json` (pack map) + a loader (`load_credential_tests`,
  path-injected like `load_secret_map`).
- Surface: list open escalations.
- Unit tests: a passing cred is handed over; a failing **required** cred → `ActivationRefused` + an
  `Escalation` written + no ACTIVATE; a failing **optional** cred → omitted, activation proceeds; costly
  test uses the cache (no live call); `automatic` mode allows exactly one retry then forces `manual`.
- `make ci` green, 100% coverage, modules ≤ 200 lines with headers.

## Decisions to confirm (before building)

- **Required vs optional per credential.** Which creds are *required* (failure blocks activation) vs
  *optional* (failure just omits the cred)? Recommend: Neo4j required for every agent; feed/broker creds
  required only for the agents that own them (provider/execution); LLM optional. Capture in the pack map.
- **Cache scope.** Recommend a per-(env_var, UTC-day) cache node so a costly pass is reused within the
  day; cheap tests always live. Confirm the TTL.
- **Where the human sees escalations.** The read-only surface list now; the approve/automatic-mode command
  is C/D. Confirm that split.

## Acceptance / exit criteria

- [ ] A required credential that fails its test → the agent is **not** activated; an `Escalation` is
      written; the master does not raise into a crash-loop (fail-safe, like `ensure_reachable_or_halt`).
- [ ] A passing credential is handed over unchanged; an optional failure is omitted, activation proceeds.
- [ ] A `costly` test is satisfied by a cached pass (no live call at activation); `cheap` tests run live.
- [ ] `automatic` mode allows exactly one auto-attempt, then forces `manual` + escalates.
- [ ] `make ci` green; **functionality check** (below) passes; register row added.

## Functionality check (per the sprint-close rule)

Against real Aura + real creds: (1) activate an agent whose Neo4j cred is **good** → handover succeeds, no
`Escalation`. (2) Inject a **deliberately bad** credential (e.g. wrong password in a throwaway secret
store) → the master refuses activation and writes an `Escalation`, **without hammering** (one test, fail
safe — use a fake/one-shot store, not repeated live auth). **Tear down** the `Escalation` + any test nodes
(Aura → prior count). Record in `docs/laws/functionality-checks.md`.

## Dependencies

- **DL-36** (this sprint's source); reuses `probes/checks.py` (tests), `agents/master` activation,
  `kernel/startup.ensure_reachable_or_halt` (fail-safe precedent), `supervisor.flag_for_human`.
- Respects ADR-0012 (substrate/pack wall): the master ships the *mechanism*; the pack ships the
  credential→test map.

## Version bump

New capability (credential-tested activation + escalation). **0.44.01 → 0.45.00** (feat → MINOR).

## Notes

Pieces **C** (LLM remediation planning, bounded catalogue) and **D** (execute→production→documentation,
one-automatic-shot) follow once their DL-36 open questions are settled. A+B delivers the safety core:
*test before you trust, refuse + escalate on failure, never loop.*
