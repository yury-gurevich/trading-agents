<!-- Agent: planning | Role: archive — STATE history split out 2026-09-18 -->
# State archive 12 — the late-August deliberation and sizing residue

**Split out of [`../STATE.md`](../STATE.md) on 2026-09-18**, when the S212 and S214 merges pushed STATE.md
past its own 200-line rule. Nothing here is live. Chains from [STATE-11.md](STATE-11.md).

🪤 **Read these as of their own date.** The 73 % veto rate recorded below was superseded on 2026-09-18:
[DL-173](../design-log.md) traced it to a code-level collapse of `revise` and `overturn` into one action,
and [ADR-0029](../decisions/0029-a-revise-is-a-finding-an-overturn-is-a-block.md) narrowed the block to
`overturn` only. The ADR-0023 falsifiable test below was therefore never settled on its own terms.

---

🟠 **FLIP CONDITION 1 of 3 on `sched-2026-08-31`** — the posture landed, but `real_debate_count` was **0** and
`failed_open_count == 0` only vacuously; PM approved nothing, so no debate ran. 🟩 **Its real purpose is now met
another way:** S188's in-fleet tests show all three deliberators passing `anthropic` through master's Key Vault, so
the credential path is proven and only **debate mechanics** still need item 3's K=4 run. Posture stays `advisory`.

🟩 **PROVEN LIVE — ADR-0023's PM half, unattended, first time.** GOOG sized at 0.998 %; GOOGL then **failed** at
1.67 % > 1 %. 🚨 Pre-S184 both passed, opening **two positions in one company** ([DL-122](design-log.md)).

🚨 **NOT PROVEN — ADR-0023's falsifiable test** (the 73 % veto rate falls materially). **73 % stands as the last
honest figure** ([DL-119](design-log.md) amendment). 🪤 `sched-2026-08-31` supplied **no** data — zero debates.

🚨 **NOT PROVEN — S182 live.** 2026-08-21's stops carry `stop_pct_source=position`, written eight minutes before
execution ran, so the fallback never fired. 🪤 **Do not re-check it that way** — run-start reconciliation closes it.

**Shipped and deployed, detail in the sprint docs and design log.** **S184** merged `18c41b1` (`0.91.00`), `GATE PROVEN` at `8613d72`, PM rows `PM-NEV-07/08/09` 🟩, DRIFT-042..046 `CORRECTED`, deployed `s184` with `ENV PRESERVATION` 16/16 and zero drift. Two defects the merge exposed are fixed on `chore-gate-outcome-refuses-ambiguity`: `GateOutcome.passed` re-collapsed the states S184 had just separated and now raises; CodeQL **#187** was `py/mismatched-multiple-assignment`, **the same rule and package as #177 four days earlier**, because `codeql.yml` runs only on `main` (queue item 31). 🟢 **That trap did not fire this time** — `main` at `19dc2b2` is `GATE PROVEN` on CI, Security Findings **and CodeQL**, with **0** open error-level alerts. **S182** merged `2fc0672` (`0.90.16`), deployed `s182`. 🪤 A `verify-2026-08-20-s184-a` teardown reported false success because `ScanRun` is uuid-keyed and the verification query reused the teardown's own filter ([DL-124](design-log.md)); a second pass removed 24 nodes + 25 edges and the pollers' own predicates now read **0 pending** at every stage, 22 positions intact.

🪤 **One live residue, not urgent:** **2 NFLX shares** from the S172 test harness, never vetoed (selling is a real trade). The `cancel_stop` `HTTP 422` half is **closed**.

---

## Appended 2026-09-19 — S205 and the S204 verification block

Moved from `../STATE.md` when the S213 merge pushed it past 200 lines again.

🟩 **PROVEN RESULT — [S205](sprints/sprint-205-a-type-clause-names-the-fields-it-requires.md) MERGED
`af75079` (`0.98.03`), 2026-09-15 — work-queue **item 30** closed, and a clause family stopped being its own
oracle.** The twelve `TYP` clauses that said a payload *"matches `contracts/<agent>.py` exactly"* now **name the
fields they require**, each traceable to the clause that needs it; two new guard modules fail when a required
field is deleted, proven on three agents (Scanner `skipped_filters`, Master `capability_declaration`,
Researcher `backtest`). Zero `contracts/` edits — `git diff --stat -- contracts` empty.
🟩 **Verified independently on the merged SHA, not on the handback's word:**
`assert_gate_ran.py --sha af75079346a74f402408a6795ee881666f61b051` printed `GATE PROVEN` — image build, CI,
CodeQL, Security Findings and the dependency run all green; `main`'s later tip `8faf856` is `GATE PROVEN` too,
so no S205 commit rides above a gated one (the S186 hazard). 🟩 **Local `make ci`:** 2756 passed, 4 skipped,
100.00 %, pip-audit and detect-secrets clean. **No deploy, and checked rather than assumed:** the diff is laws,
test-plans, docs, two `tests/` modules and the version — nothing that ships in an image.
🪤 **Two forced decisions found and deliberately not built**, carried as open rows rather than as silent
residue: [DRIFT-060](laws/drift-register.md) — nothing requires `CONTRACT.version` to move when required fields
change; [DRIFT-061](laws/drift-register.md) — five execution output clauses name fields `contracts.execution`
does not carry.
