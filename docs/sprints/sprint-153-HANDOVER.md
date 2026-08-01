<!-- Agent: planning | Role: operator-facing handover note for delegating S153 -->
# S153 — handover note (operator → Codex)

Everything is staged. Paste the prompt in §3, watch it with §5, review it with §6.

---

## 1 · What is already done for you

| Thing | State |
| --- | --- |
| Branch | **`sprint-153-deliberator-agent`** — created, cut from `main` at `68f71b6` |
| Worktree | **`C:\Users\yury_\Downloads\project\trading-agents-s153`** — clean, nothing written to it |
| Brief | [`sprint-153-deliberator-agent.md`](sprint-153-deliberator-agent.md) — refreshed 2026-08-01 against the live graph |
| `main` | green at `68f71b6`; S152 and S154 merged, nothing in flight |

Nothing has been committed on the branch. A previous launch was stopped after ~4 minutes before it
wrote anything — you are starting from a clean slate, not resuming.

---

## 2 · Run it from the worktree, in a sandbox — this matters

`~/.codex/config.toml` has `approval_policy = "never"` and `sandbox_mode = "danger-full-access"`.
Launched bare, Codex gets unrestricted disk access with no prompts — including `.env`, `infra/` and
`main`. **Always pass `-s workspace-write`**, which confines writes to the worktree, `/tmp` and
`~/.codex/memories`. This is [hardening-backlog](../hardening-backlog.md) row **N**, and the
protection currently lives entirely in remembering this flag.

```powershell
cd C:\Users\yury_\Downloads\project\trading-agents-s153
codex -s workspace-write
```

Use plain `codex` (interactive) rather than `codex exec` — you asked to watch progress, and the
interactive TUI shows each step, lets you interrupt, and lets you answer a question mid-run.

Verify the banner says `sandbox: workspace-write` before you let it work.

---

## 3 · The prompt — paste this

```text
You are the coding agent for Sprint 153 of this repository.

READ FIRST, IN THIS ORDER:
1. docs/sprints/sprint-153-deliberator-agent.md — the authoritative brief. Self-contained for a
   cold start: Why / The design / Shape / Scope (7 items) / Non-goals / Success factors / Risks /
   Closeout. Refreshed 2026-08-01 against the live graph, so its numbers are current.
2. CLAUDE.md and AGENTS.md — project-level hard rules that override defaults.
3. docs/design-log.md entry DL-80 — the reason this sprint exists. Read it before you plan.

WORKING CONTEXT:
- You are already on branch sprint-153-deliberator-agent in a dedicated git worktree, cut from main
  at 68f71b6. Do NOT create another branch, switch branches, merge, or push to main. Push only your
  own branch.
- Stay inside this worktree. Do not read or write .env, infra/*.local.json, or anything outside it.
  Credentials never belong in the tree (CLAUDE.md).

NON-NEGOTIABLE GATES:
- make ci must pass — all 9 steps, 100.00% coverage floor. Never lower the floor.
- Local green is NOT done. Push the branch and poll
  `gh run list --branch sprint-153-deliberator-agent` until ALL FOUR jobs read success: quality,
  test, security (CI) and gate (Security Findings). in_progress is not success. If it goes red,
  YOU FIX IT and poll again — do not report a red gate and stop. Assert a run EXISTS for your head
  SHA before declaring done (hardening-backlog row M).
- import-linter enforces the boundaries: agents never import other agents, and the deliberator must
  not import orchestration. Every module < 200 lines. No magic numbers — kernel.tunable(..., why=).

WHAT MATTERS MOST:
Scope item 1 — the acceptance gate learning to fail when a declared stage produces no artifact —
comes FIRST, and must be OBSERVED FAILING on a historical run before you make it pass. All 23
historical runs lack a DeliberationRun. Without that check the new agent can rot exactly as the old
one did while every run still scores ACCEPTANCE PASS. A gate never seen failing proves nothing
(DL-57/DL-70). Two separate decisions depend on this check existing.

SCOPE BOUNDARY — READ THIS, IT CHANGES WHAT "DONE" MEANS:
You have NO credentials: .env is not in this worktree, by design. So success factors 3 and 4
(deploying three instances; a real DeliberationRun on the live spine) are NOT yours — they are
operator sequencing after merge, exactly as in S151 and S154. Your done is: scope items 1–7,
make ci green, four remote gates green, closeout filled. Do not attempt to reach the live graph,
Azure, or Alpaca. If something seems to require credentials, say so and stop rather than working
around it.

HONESTY RULES (load-bearing here):
- Declaring a capability is never proving it. Every new law clause starts as an unproven grey box
  and turns green only when a functional test cites its clause ID in its docstring. A brand-new
  agent starting at 0/N is the correct, honest number.
- If a law, an ADR, or the brief itself contradicts what you find, STOP and report it. A
  contradiction you surface is a success, not a delay.
- If something is blocked, finish everything else and say plainly what you left out and why. Do not
  quietly narrow the scope.

HANDBACK:
Fill in the "## Closeout — evidence" block at the bottom of the sprint doc — files changed, proven
results with actual command output, remote gate run IDs and job conclusions, and anything NOT met
stated plainly. Never hand back with that block unedited. Then stop; do not merge.
```

---

## 4 · The one change I made to the brief for a delegated run

The sprint doc's success factors 3 and 4 (deploy; a real `DeliberationRun` on the live spine) read
as *the* definition of done — and for the **sprint** they are. But a sandboxed coding agent has no
`.env` and cannot do them. The prompt above says so explicitly, so Codex doesn't either flail
against missing credentials or, worse, quietly claim them as met.

**Consequence to hold onto:** a fully green handback does **not** close [DL-80](../design-log.md).
The LLM veto will still never have run in production until we deploy and prove it. Green code is
honest progress, not the outcome.

---

## 5 · Watching it

In the TUI you will see each step. Out of band, from the main worktree:

```powershell
cd C:\Users\yury_\Downloads\project\trading-agents
git -C ..\trading-agents-s153 status --short        # what it has touched
git -C ..\trading-agents-s153 log --oneline main..HEAD   # what it has committed
gh run list --branch sprint-153-deliberator-agent --limit 5
```

**Three things worth interrupting for:**

1. **It starts anywhere other than scope item 1.** The acceptance check comes first and must be seen
   failing. If it builds the agent bundle first, the check tends to get written to fit whatever was
   built — which is how a gate that cannot fail gets shipped.
2. **It edits an existing `laws.md`.** Only S152 was authorised to do that, and only for execution
   and analyst. The deliberator's law is a **new** file copied from `docs/laws/_TEMPLATE.md` — never
   from provider's.
3. **It lowers the coverage floor, adds `# noqa`, or marks a new law clause green without a test
   citing the clause ID.** Any of those is the gate being bent rather than met.

---

## 6 · What I will do when it hands back

The same review I gave S154, which caught a real finding: read the actual diff, verify the remote
gates **by `headSha`** rather than by quoted run ID, re-run `make ci` independently on the branch
tip, and check the claims against the live graph. Then merge, tag, and tell you what needs your
call. Just point me at the branch when it is done.

---

## 7 · Known risk the brief already names

**The Azure SAS rule cap.** DL-53: Azure caps 12 rules per namespace *and* per entity; the fleet
already carries 33 rules across 13 agents. Three more bus identities may not fit. The brief says to
**count before building** — if they do not fit, the peers-answer-over-the-bus design is the part to
rethink, not the agent. If Codex reports this, it is a correct finding, not a failure.
