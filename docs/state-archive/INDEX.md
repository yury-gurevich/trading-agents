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

## A note on the overlapping ranges

`STATE-04` is titled S99–S118 and `STATE-05` S102–S126, which look like they overlap — they do not
duplicate content. The **S102 and S103 entries lingered in STATE.md's *Recent* section past the
2026-07-08 split** (they were the fleet arc's headline results and stayed visible deliberately), so
their detail travelled into `STATE-05` at the 2026-07-22 split. Ranges here are *nominal*; the
entries themselves are unique to one file. If you cannot find a sprint, search all five — or use
`docs/sprints/sprint-NN-*.md`, which is always authoritative for a single sprint.

## When to split again

Trigger: STATE.md's *Recent* section becomes the bulk of the file (~50 %+) or the file passes
roughly 400 lines. Procedure: move the oldest *Recent* entries verbatim into the next
`STATE-NN.md`, give it a header naming its range and the arcs it covers, chain it to the previous
archive, add a row above, and update the *Older sprints* pointer in STATE.md plus the row in
[`../INDEX.md`](../INDEX.md). Check at the same time that the newest sprints actually have *Recent*
entries — at the 2026-07-22 split, S128–S134 existed only inside the header paragraph, so a
size-only trim would have dropped them.
