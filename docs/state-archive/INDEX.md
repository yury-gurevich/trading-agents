<!-- Agent: planning | Role: index — archived STATE history -->
# State archive — index

**How to use:** [`../STATE.md`](../STATE.md) is the **single live tracker** (LAW-02) — always read
it first. When its *Recent* section grows too long to scan, the oldest entries are split out here
**verbatim**, newest archive last. Come here only for the detail of a specific past sprint; for the
canonical chronological list of every sprint, use [`../sprints/README.md`](../sprints/README.md).

**Nothing here is live.** These files are frozen at their split date and are not updated afterwards.

| File | Sprints | Covers | Split out |
| --- | --- | --- | --- |
| [STATE-01.md](STATE-01.md) | S36 → P0 | The earliest history back to phase 0, plus the *Retired components* record (see [`../repo-hygiene.md`](../repo-hygiene.md)) | — |
| [STATE-02.md](STATE-02.md) | S37–S76 | The analyst deterministic port, provider feeds, P14 pub/sub, and the first law cycles | — |
| [STATE-03.md](STATE-03.md) | S77–S96 | Graph-pull work loops, platform/pack extraction, and the etalon-era narrative | — |
| [STATE-04.md](STATE-04.md) | S99–S118 + chores | Fleet-serve receive half (S99/S100), the qlib workflow adoption (S110–S115), the DL-36 credential arc close (S106–S108), and the DL-43 Postgres migration trilogy (S116–S118) | 2026-07-08 |
| [STATE-05.md](STATE-05.md) | S102–S126 | Fleet arc close (S102 distributed run-through, S103 dispatcher cron), DL-42 deliberation prompts (S119/S121), DL-44 broker reconciliation (S120), and the **whole DL-47 dashboard arc** (S123–S126) | 2026-07-22 |
| [STATE-06.md](STATE-06.md) | S128–S146 | Feed resilience (S128), the blast-radius hardening run (S130–S134), ADR-0017 exit authority (S137), broker-native stops (S138), the graph-vocabulary pair (S143/S144), and the **exit-replay outage and its two-sprint recovery** (S145/S146). Contains two claims later corrected in place — **DL-73 was retracted in full** and the first S146 packet was superseded | 2026-07-29 |
| [STATE-07.md](STATE-07.md) | S146→S171 (banners) + S127–S164 (*Recent*) | Two things: the **54 headline banner clauses** that had accreted on STATE.md's `**Last updated:**` line, and the *Recent* entries at `0.89` and below. The banners are the **only narrative record in this series for the S147–S164 arc (`0.81`–`0.86`)** — those versions never received *Recent* entries at all. Covers the LLM veto's first production run and first real block, the two-ended sell-side deadlock, the DL-93 margin discovery, and the S171/DL-103/DL-104 veto arc | 2026-08-11 |
| [STATE-08.md](STATE-08.md) | S166–S171 + `chore-openai-cutover` | The **veto arc** at `0.89.07`–`0.90.01`: the race the veto had always lost (S166), the audit reporting *"Faults today = 0"* while 18 were written (S167), the second vendor after the Anthropic key hit its limit (S168), the uncorrelated peer client (S171), and DL-104's reading of the verdicts — **56 % self-agreement**, ~2 of 15 grounds surviving a check — which demoted the veto to advisory | 2026-08-12 |

## A note on the overlapping ranges

`STATE-04` is titled S99–S118 and `STATE-05` S102–S126, which look like they overlap — they do not
duplicate content. The **S102 and S103 entries lingered in STATE.md's *Recent* section past the
2026-07-08 split** (they were the fleet arc's headline results and stayed visible deliberately), so
their detail travelled into `STATE-05` at the 2026-07-22 split. Ranges here are *nominal*; the
entries themselves are unique to one file. If you cannot find a sprint, search all six — or use
`docs/sprints/sprint-NN-*.md`, which is always authoritative for a single sprint.

## When to split again

Trigger: **STATE.md passes 200 lines** (operator rule, 2026-08-11; the 2026-08-12 split ran at
**192** — splitting on approach rather than on breach, because the session that closed DL-106
would have crossed it — it replaces the old "~50 % or
roughly 400 lines", which was blown by 174 lines before anyone noticed, because nothing measured it).

🪤 **Measure the header line, not just the section count.** At the 2026-08-11 split STATE.md was 574
lines and 164 KB, and **one line held 112,149 characters of it** — the `**Last updated:**` header had
been prepended to once per session since ~2026-07-27 and never pruned, reaching **57 clauses**, two of
them exact duplicates. It was invisible to every session that edited it, because the stamp being
edited sits at the front. STATE.md now carries a size rule in its own *How to read* block: under 200
lines, and a **three-clause header — stamp, version, one headline**, replaced rather than appended.

Procedure: move the oldest *Recent* entries verbatim into the next
`STATE-NN.md`, give it a header naming its range and the arcs it covers, chain it to the previous
archive, add a row above, and update the *Older sprints* pointer in STATE.md plus the row in
[`../INDEX.md`](../INDEX.md). Check at the same time that the newest sprints actually have *Recent*
entries — at the 2026-07-22 split, S128–S134 existed only inside the header paragraph, so a
size-only trim would have dropped them.
