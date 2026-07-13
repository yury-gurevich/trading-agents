<!-- Agent: planning | Role: sprint handover -->
# Sprint 125 — Operations dashboard, slice 4: the operator chat panel (DL-47)

**Phase:** Operations dashboard (DL-47 slice 4; S122–S124 shipped, 0.66.00→0.68.00)
**Branch:** `sprint-125-operator-chat`
**Status:** ready for handover (packaged 2026-07-12)
**Effort:** M

---

## Why this sprint

DL-47 req 7 ("talk to an LLM in the dashboard") pulled ahead by **req 15**: *"we will have to
leave the coding environment one time and never come back."* Every "how did we go last night"
still drags the operator into the IDE because the investigation skills are reachable only from a
Claude Code session. The chat panel is the mechanism by which asking questions — and eventually
the whole skills catalogue — becomes reachable from the dashboard. Req 15's corollary binds
equally: the mockup's dead chat dock read as broken, so **nothing ships half-wired**.

This slice is **tier 1 only** (DL-47 two-tier chat): the operator agent's bounded Q&A and
command grammar. Tier 2 (the repo-checkout repair session, reqs 11–12) is explicitly out of
scope — it depends on the resume primitive (S126) and a launch mechanism that does not exist yet.

## What already exists (read before estimating — this sprint is exposure, not plumbing)

- `agents/operator/` — LOCKED laws; `interpret(HumanCommand) → CommandResult` and
  `explain(ExplainRequest) → Explanation`; every call writes `CommandAudit` + `LLMCall`
  (the priced ledger `/audit-costs` reads); `HumanCommand.channel` already admits `"dashboard"`.
- `surfaces/mcp_tools.dispatch_tool` + `surfaces/context.py` — the **bounded surface dispatch**
  already used by the MCP server: `command` (interpret → confirm round-trip → supervisor),
  `status`, `runs`, `incidents`, `explain`. Tested, jargon-guarded types.
- `surfaces/dashboard/` — threading WSGI app (one slow request no longer wedges the UI),
  `/api/runs/{id}/bundle` (the DL-47 context bundle), the verdict/vitals projections.

## Decisions taken at packaging (LAW-06)

1. **The chat panel is the operator agent — no second LLM path.** `POST /api/chat` maps a panel
   message onto the existing `dispatch_tool` catalogue with `channel="dashboard"`. The operator
   keeps exclusive LLM I/O, the audit trail stays complete (CommandAudit + LLMCall), and chat
   spend lands in the priced ledger for free. *Ruled out:* the dashboard calling Anthropic
   directly (breaks the operator's exclusive-LLM-I/O law and dodges the ledger); a bespoke chat
   "assistant" beside the operator (two grammars would drift).
2. **In-process binding, local-first.** The dashboard composition root binds the operator the
   same way the MCP server does (`paper_context()`-style context built from `.env`). *Ruled
   out:* a Service Bus round-trip to the fleet's operator container — it is scaled to zero
   outside 22:30–00:30 UTC, and waking the fleet to answer a question inverts the cost model.
   The served path stays the fleet's transport; the surface binds in-process like every surface.
3. **Free text goes through `command`; the panel adds run-scoped quick asks.** The input box
   submits `command(text)`. Beside it, **suggested asks** — deterministic, always-wired chips
   scoped to the selected run ("explain this run", "system status", "open incidents") — call the
   corresponding read tools directly. The selected run id travels with every message so "this
   run" is unambiguous. *Ruled out:* free-form tool routing invented in the frontend (the
   operator's grammar is the router; the UI must not grow a second one).
4. **Gated commands surface the confirm round-trip, never auto-confirm.** When `command` returns
   `requires_confirmation`, the panel renders the typed intent it is about to confirm and an
   explicit **Confirm** button that resends with `confirmed=true`. The DL-36 ladder (one
   automatic shot, then human) is the operator agent's law, not the panel's to relax.
5. **Honest empty state instead of a dead control (req 15 corollary).** If the chat backend
   cannot bind (no `ANTHROPIC_API_KEY`, no graph), `/api/chat` reports it and the panel renders
   a single labeled line ("chat is not connected on this deployment") — visible truth, no input
   box pretending to work. *Ruled out:* hiding the panel entirely (the operator asked where the
   chat is; an explained absence beats a mystery) and a canned demo mode (a lie with extra steps).
6. **Request/response, no streaming.** One POST per message; the threading server carries the
   LLM latency; the panel shows a working indicator. *Ruled out for this slice:* SSE/WebSocket
   streaming (new transport machinery for a nicety; revisit only if real usage hurts).

## Codex kickoff (paste this)

> Execute **Sprint 125 — operator chat panel** exactly as specified in this file
> (`docs/sprints/sprint-125-operator-chat.md`). Read first: DL-47 in `docs/design-log.md`
> (reqs 7, 15, and the two-tier chat block — binding); `surfaces/mcp_tools.py` +
> `surfaces/context.py` (the bounded dispatch you are exposing — extend, don't fork);
> `agents/operator/laws/laws.md` (the boundary you must not widen);
> `docs/design/dashboard-mockup.html` (chat dock design tokens); `surfaces/dashboard/app.py`
> (routing pattern to follow).
>
> - **Start:** from `main` (`git pull`), branch `sprint-125-operator-chat`. Hard gate:
>   `make ci` green, 100 % coverage, ≤200-line modules, headers, tunables for any threshold.
>   Bump **MINOR** (→ 0.69.00) + `uv lock`.
> - **Part A — `/api/chat` endpoint** per decisions 1, 2, 4, 5: POST `{message, run_id,
>   confirmed?}` → `dispatch_tool` with `channel="dashboard"`; response carries the transcript
>   turn (outcome, message text, typed-intent echo when confirmation is required, audit id).
>   Unit tests with the fake LLM client over the full outcome table: answer / refused /
>   needs-confirmation / confirmed-dispatch / backend-unbound.
> - **Part B — chat panel frontend** per decisions 3, 4, 5, 6: dock per the mockup (vanilla
>   JS/CSS, no toolchain), transcript, input, working indicator, run-scoped suggested-ask chips,
>   confirm button rendering the typed intent verbatim, honest not-connected state. No unwired
>   affordance anywhere.
> - **Part C — run grounding**: the selected run id accompanies every message; "explain this
>   run" resolves evidence for that run (verify the operator explain evidence collector handles
>   a run subject; extend the collector minimally if it does not — no new node types).
> - **Part D — guards**: extend the S124 jargon-guard to chat UI strings; a ledger test proving
>   a chat exchange writes `CommandAudit` + `LLMCall` (so `/audit-costs` prices it).
> - **Functionality check (LAW-02):** serve locally against the live Neon spine with the real
>   `ANTHROPIC_API_KEY` from `.env`; ask **"how did we go last night"** with the latest scheduled
>   run selected; screenshot the grounded answer; show the exchange priced in `/audit-costs`
>   output; then demonstrate the not-connected state (unset key) — screenshot both. Record in
>   `docs/laws/functionality-checks.md` + screenshots under
>   `docs/reports/sprint-125-operator-chat/`. Chat writes CommandAudit/LLMCall/Intent nodes to
>   the live spine — name them in the teardown note (they are audit records: keep, don't delete;
>   state that explicitly).
> - **Wrap up:** README index row, fill the **Closeout** block and append **Return notes** at
>   the very end of this file (both mandatory — see those sections), push, hand back.

## Guardrails

- The dashboard never calls an LLM provider or writes the graph directly — everything routes
  through the operator's bounded dispatch (PRD non-negotiable; operator laws).
- Do not widen the tool catalogue or the intent grammar in this sprint — expose what exists.
- No auto-confirm, no confirmation state cached across messages (decision 4).
- No streaming transport (decision 6). No tier-2 affordances (repair session, repo access,
  rebuild buttons) — S126+.
- Chat UI strings pass the jargon guard: no S-numbers, no DL-ids, no internal node labels.
- The panel must never block the verdict hero: chat failures degrade the panel only.

## Definition of done

1. With the fleet asleep and the dashboard served locally, typing **"how did we go last night"**
   returns an evidence-grounded answer about the selected run — without opening the IDE.
2. A gated command shows its typed intent and executes only after an explicit Confirm click;
   the refused/clarification paths render the operator's message verbatim.
3. Every chat exchange is auditable: `CommandAudit` + `LLMCall` nodes exist and `/audit-costs`
   prices the conversation.
4. With no API key bound, the panel states plainly that chat is not connected — no dead input.
5. `make ci` green at 100 %; live check recorded with screenshots (grounded answer + priced
   ledger + not-connected state).

## Closeout (coding agent fills; planning agent verifies before merge)

```text
CLOSEOUT — Sprint 125
Branch / merge commit:   sprint-125-operator-chat / not merged (branch-only handback)
make ci:                 all 9 steps green; 1531 passed, 6 skipped, 100.00% coverage
Functionality check:     live Neon + real Anthropic answered the exact latest-run question;
                         A$0.008530 priced exchange, 0 untracked; grounded and disconnected
                         screenshots + retained audit-node teardown inventory recorded in
                         docs/laws/functionality-checks.md
Version:                 0.68.02 → 0.69.00 (MINOR); uv.lock refreshed
Deviations from spec:    none; screenshots were captured manually because the in-app browser
                         control backend was unavailable, without changing the product proof
```

## Return notes (coding agent appends at handback — mandatory)

Append below, at the very end of this file, everything the next session needs that the closeout
numbers don't carry: surprises found in the code, decisions taken in-flight and why, drift
observed elsewhere, follow-ups you would queue. Do not edit the sections above. A handback is
not accepted while this section is empty or the closeout placeholder is unfilled (LAW-02: the
handback must prove, not restate intent).

<!-- return notes go below this line -->

- **Surprises found:** WSGI request reads blocked when they ignored `CONTENT_LENGTH`; the
  provider's unforced plain-text explanation path could hang; a broad “status” intent stole the
  required retrospective question; and flex declarations overrode the native `[hidden]` rule.
  Exact-length reads, a bounded explanation tool response, run-question routing, an explicit
  hidden rule, and static cache-busters corrected those live-only failures. Repeating identical
  text also reused the operator's deliberately idempotent correlation id, hiding fresh LLM spend;
  an optional surface request id now makes each dashboard POST append a distinct priced exchange
  while MCP callers retain their existing idempotence.
- **In-flight decisions:** the dashboard composition root binds the existing operator and graph
  once, while the dashboard route itself only calls `dispatch_tool`. The run id is appended as
  operator context and the evidence collector reads existing provenance; no new tool, node type,
  graph-write path, streaming transport, or repair affordance was introduced. Audit records from
  the live proof are intentionally retained rather than torn down.
- **Drift observed:** all three deliberation roles receive the same rendered base context, but the
  analyst `ScoreBreakdown.metrics` payload is not persisted in full into `Recommendation` or
  rendered by `veto_context`; role parity therefore exists, full quant-signal availability does
  not. This pre-existing gap is outside the S125 exposure boundary. Separately, the verdict maps
  an unavailable Azure job read to “Activation bus is unreachable” even when the graph contains
  active activation records; that state is unverified, not proof of a bus outage.
- **Follow-ups queued:** persist a typed, bounded quant-evidence payload and render that identical
  payload for Defender, Challenger, and Judge, with a three-role capture test proving every
  calculated quant signal is present. Make bus health tri-state (`reachable` / `unreachable` /
  `unverified`) and require a real probe before the hero says unreachable. Keep tier-2 repair/repo
  access in its separately governed dashboard slice.
