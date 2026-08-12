<!-- Agent: planning | Role: archive — STATE history split out 2026-08-12 -->
# State archive 08 — the veto arc: production, first reading, demotion to advisory

**Split out of [`../STATE.md`](../STATE.md) on 2026-08-12.** Nothing here is live. Chains from
[STATE-07.md](STATE-07.md).

One *Recent* entry moved, covering **S166–S171 + `chore-openai-cutover`, versions `0.89.07`–`0.90.01`,
2026-08-08→10**. It is the whole arc in which the LLM veto stopped being a component and became a
posture: the race it had always lost (S166), the audit that reported *"Faults today = 0"* while 18
were being written (S167), its second vendor after the Anthropic key hit its limit (S168), the
uncorrelated peer client (S171), and then the reading of the verdicts themselves — **56 % self-
agreement, roughly 2 of 15 grounds surviving a check against the code** — which is what demoted the
veto to *a good auditor and a bad gate* (DL-104).

Why it was split at 192 rather than 200 lines: the session that closed [DL-106](../design-log.md)
added three paragraphs to *Now* and would have pushed the next one over. Splitting the oldest entry
while its successor arc is still live keeps *Recent* to what a session can actually scan.

**Read next:** [ADR-0022](../decisions/0022-the-veto-gates-buys-never-exits.md) for the posture
itself, [DL-98…DL-104](../design-log.md) for the reasoning, and
[sprint-166](../sprints/sprint-166-the-veto-gates-buys.md),
[sprint-167](../sprints/sprint-167-a-fault-count-cannot-lie.md),
[sprint-171](../sprints/sprint-171-a-reply-must-answer-its-own-request.md) and
[chore-openai-cutover](../sprints/chore-openai-cutover.md) for per-sprint detail. 🪤 **S168 has no
sprint doc of its own** — the second-vendor work is recorded in `chore-openai-cutover.md` and DL-99.

## Recent (verbatim, as it stood in STATE.md)

- **The veto reached production, was read for the first time, and was demoted to advisory (feat + fix,
  0.89.07–0.90.01, 2026-08-08→10 — ADR-0022, DL-98/99/101/102/103/104).** **S166** closed the race the
  veto had always lost: execution reached the broker at 05:36:22 while the `DeliberationRun` saying
  *revise* landed at 05:47:32, and `_drop_vetoed` read an absent veto as *execute everything* — so *not
  finished yet* and *not deployed* were indistinguishable. A buy-carrying `PMRun` is now held for a
  bounded grace (`deliberation_grace_seconds`, default 900); **exits never wait** (ADR-0017). **S167**
  fixed an audit reporting *"Faults today = 0"* while 18 were being written — `Fault` stamps
  `occurred_at`, the query read `created_at`, which is `NULL` on every Fault node (measured both ways at
  the same moment: **18** vs **0**) — and made `failed_open_reason` record the captured cause instead of
  asserting one. **S168** (`0.90.00`) gave the veto a second vendor after the Anthropic key hit its limit
  to 2026-09-01: an `OpenAILLMClient` behind the same port plus an `llm_provider` **tunable, deliberately
  not an automatic fallback chain**, because a silent switch makes *which model reviewed this order*
  unanswerable after the fact. **chore-openai-cutover** granted the key and found the vault and `.env`
  holding **different** OpenAI keys — both authenticated, so nothing was broken, but the fleet would have
  billed a five-week-old key nobody tracked. **S171** (`0.90.01`) fixed a peer client taking `messages[0]`
  with no correlation; cold peers now measure `real_debate_count=18`, `failed_open_count=0`, reply
  subscription **0 active / 0 dead-letter**. 🚨 **Each fix exposed the next.** Correlation revealed the
  debate's true cost — **943 s** against a 900 s grace (DL-103) — so the grace went 900 → 1800; then
  DL-104 read the verdicts and returned it to **900 deliberately**: **45 `revise` of 58** real debates,
  **56 %** self-agreement on the same model and prompt 3.5 h apart, and roughly **2 of 15** grounds
  surviving a check against the code. The veto is a good auditor and a bad gate.
