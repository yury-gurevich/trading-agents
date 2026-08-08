# S171 handover note — paste this at the start of the Codex conversation

You are implementing **one sprint** in the `trading-agents` repo, end to end: code, tests, green
gate, commit, closeout. Work on a branch. Do not merge to `main` without the remote gate green.

## Read first, in this order

1. `CLAUDE.md` at the repo root — project rules. They override your defaults. Non-negotiable.
2. `docs/sprints/sprint-171-a-reply-must-answer-its-own-request.md` — **your spec.** It carries the
   measured evidence, the traps, and the success factors.
3. `docs/design-log.md` → **DL-102** (last entry) — the full diagnosis with the live numbers.

## The defect, in three sentences

The deliberation manager sends a debate request to a peer over Service Bus, then reads the reply by
taking `messages[0]` off the `deliberator-manager.reply` subscription — **with no correlation to the
request it just sent** (`agents/deliberator/peer_client.py:143-154`). On 2026-08-08 this made the
manager consume 5.5-hour-old replies from an earlier run: the proponent had made 18 real `gpt-5.5`
completions, yet the `DeliberationRun` recorded `real_debate_count=0, failed_open_count=18` with a
stale Anthropic error as the reason. The error path merely fails open, but a stale **success** reply
is accepted as a debate turn **for a different ticker's order** — a verdict attributed to the wrong
decision, with no fault raised and a green acceptance gate.

**The fix is small: the correlation key is already on the wire.** `kernel/bus.py:136,158` sets
`correlation_id = message.id` on every response and error; `kernel/bus_azure_receiver.py:135-146`
publishes the reply's ready event with `run_id = str(correlation_id)`. The caller simply never looks
at it. Match on it, and dispose of orphans loudly (dead-letter with a reason) rather than silently.

## Hard rules you must follow

- **Branch, in a worktree:** `sprint-171-a-reply-must-answer-its-own-request`. Never commit sprint
  work directly to `main`.
- **Version:** this is a **fix** → bump the **last two digits** in `pyproject.toml`: `0.90.00` →
  **`0.90.01`**. Stage `uv.lock` if the bump touches it. Breaking the version rule is a blocker.
- **`make ci` must pass, and you must never measure it through a pipe.** `make ci | tail` reports
  `tail`'s exit code, so a real failure reads as green. Redirect to a **file** and read the file:
  `make ci > /tmp/ci.txt 2>&1 ; echo $?`. All 11 steps, including the **100 % coverage floor**.
- **Remote gate:** push the branch, then `make gate-ran` must **exit 0** (it resolves the full SHA
  itself and requires both `CI` and `Security Findings` to have concluded `success`). Do not
  hand-roll the GitHub query; do not merge a branch you have not seen go green on the remote.
- **Module size:** 200 lines is a hard block, 150 a warning. Split before the block. No `# noqa`.
- **Architecture:** `kernel ← contracts ← agents ← orchestration/surfaces`. `kernel` imports nothing
  from the layers above it. Agents never import other agents. Enforced by import-linter.
- **Prove each behaviour by watching it fail first.** Plant the violation, see the test go red,
  restore, see it go green. Report that, not just "tests pass".
- **Use `uv`** — `uv run`, `uv pip`. Never bare `pip`.
- **Secrets never exist as files in the worktree**, not even untracked scratch files.

## Two things that will bite you

- 🪤 **Do not "fix" this by draining the reply queue at startup.** That was the manual mitigation
  already applied on 2026-08-08 and it is precisely the accident being removed — with an empty queue
  a sequential manager correlates *by luck*, and the bug returns on the first timeout, crash,
  restart, or second manager.
- 🪤 **Do not raise `request_timeout_seconds`.** The manager was not timing out. It was reading
  promptly and reading the wrong message.

**Fail-open policy must not change.** If no matching reply arrives before the deadline, the order
still fails open. That is deliberate (S147 / ADR-0017): blocking the run on an LLM outage would
block *exits*. This sprint changes *which* reply is read, never whether the veto can block.

## Definition of done

Every success-factor checkbox in the spec ticked with evidence, plus:

- `make ci` exit 0, unpiped, redirected to a file — paste the counts (`N passed`, coverage `100.00%`).
- `make gate-ran` exit 0 for your pushed commit's **full** SHA.
- The **Closeout — evidence** block at the bottom of the spec filled in. A handback with the
  placeholders still in it is not accepted.
- State plainly what your work does **not** prove. In this repo an unproven claim is worse than a
  missing one — "success is proven, never assumed" (LAW-02).

Do not deploy to the fleet and do not merge to `main` without checking with the operator first.
