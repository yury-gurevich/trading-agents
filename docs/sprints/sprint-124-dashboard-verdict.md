<!-- Agent: planning | Role: sprint handover -->
# Sprint 124 — Operations dashboard, slice 3: glance-first master verdict + operator language (DL-47)

**Phase:** Operations dashboard (DL-47 slice 3; S122 shipped 0.66.00, S123 shipped 0.67.00)
**Branch:** `sprint-124-dashboard-verdict`
**Status:** ready for handover (packaged 2026-07-11)
**Effort:** M

---

## Why this sprint

Operator redline r2 (DL-47 reqs 13–15, `docs/design-log.md`), issued after first real use of the
shipped slices: the dashboard opens reading-first — prose ledes, section headers, tables — when a
dashboard's job is an **immediate at-a-glance verdict**: one dominant RED or GREEN indicator backed
by color and motion, with everything else explained **on demand**. Internal build vocabulary
(S-numbers, DL-chips) also leaks into the operator surface.

There is a second, load-bearing defect: **the verdict the dashboard would show is currently a
lie on quiet days.** The 2026-07-10 scheduled run completed 7/7 with every candidate legitimately
below the confidence floor — a healthy no-trade day — yet the acceptance gate prints `FAIL`
(`analyst.scored: 0 < floor 1.0`). A master light wired to that gate would glow RED on a healthy
night. This slice therefore also closes the known gate-policy gap (Watch item, 07-09/07-10): a
first-class **no-trade verdict**. The light ships only together with the fix that makes it honest.

**Resequencing (recorded in DL-47 status):** this verdict slice runs as S124; operator chat is
S125; resume-from-stage + the DL-46 tripwire *judgement* move to S126.

## Decisions taken at packaging (LAW-06)

1. **Binary master light; warnings badge, no amber.** The operator's contract is RED or GREEN.
   **GREEN** = the selected run's acceptance verdict is `PASS` or `NO_TRADE` **and** no
   fault-class vital (spine/bus unreachable, operator-held escalation, run stalled mid-pipeline).
   **RED** = anything in that list is broken. Warning-class facts (pending flags, degraded feeds,
   untracked LLM spend) do **not** flip the light — they render as a count badge beside it and as
   rows in the drill-down. *Ruled out:* a three-state amber light (dilutes the binary contract;
   warnings stay visible without stealing the verdict).
2. **Acceptance gains a first-class `NO_TRADE` verdict** in
   `orchestration/packs/trading_acceptance.py` (pack side — ADR-0012 clean). When the pipeline is
   complete (all stages present) and `analyst.scored == 0` **with rejection evidence present**
   (every rejection carries its confidence and the regime floor it missed), the verdict is
   `NO_TRADE` — pass-equivalent for exit codes and the light, distinct in the label.
   `FAIL` remains for missing stages, conservation breaches, or zero-scored *without* the
   explaining evidence. `scripts/accept.py` prints the new verdict. Floors on the trade path are
   untouched — this adds a verdict, it does not loosen a gate.
3. **Verdict hero is the landing view; sections become drill-down.** A hero strip above the rail:
   the master light (dominant, animated — CSS pulse/glow, `prefers-reduced-motion` respected), a
   one-sentence plain-language summary ("Last night's run completed — no trades: 5 candidates
   below the confidence bar"), next-fire countdown, warnings badge. The run selector still
   switches context; the hero follows it. Existing sections keep all their content but their
   ledes shrink — nothing is lost, everything is one click deeper. **Dashboards do not explain at
   the beginning — they explain on demand.**
4. **Plain-language summary is deterministic, server-side.** A template over trace/acceptance
   facts (stage counts, rejection reasons, fill counts) in the projection — *not* an LLM call —
   so the CLI, the bundle, and the future chat tier reuse the same sentence. *Ruled out:* LLM
   phrasing (S125's job; the verdict path stays deterministic and testable).
5. **Operator language only, enforced by a jargon-guard test.** All UI strings lose sprint ids
   and design-log ids (the DL-36 chips go; "Self-recovery ladder" keeps its name; ledes/footer
   rewritten in operator terms). A unit test scans the served static assets and every
   API-supplied display string for `\bS\d{2,3}\b` and `\bDL-\d+\b` so the vocabulary cannot creep
   back. Raw image tags stay — they are data in a detail view, not headline copy.
6. **The verdict is a projection, not new telemetry.** `projections_verdict.py` computes the
   light + summary + warnings purely from reads that already exist (acceptance verdict, vitals),
   served at `/api/verdict?run=<id>` and folded into `/bundle`. No new node types, no writes.

## Codex kickoff (paste this)

> Execute **Sprint 124 — dashboard glance-first verdict** exactly as specified in this file
> (`docs/sprints/sprint-124-dashboard-verdict.md`). Read first: DL-47 in `docs/design-log.md`
> — especially **operator redline r2, reqs 13–15** (binding); `docs/design/dashboard-mockup.html`
> (design system; the hero is new — match its tokens); `surfaces/dashboard/` (S122/S123 code —
> extend, don't rework); `orchestration/packs/trading_acceptance.py` + `scripts/accept.py`
> (the gate this sprint extends); `scripts/trace_run.py` (the facts the summary sentence uses).
>
> - **Start:** from `main` (`git pull`), branch `sprint-124-dashboard-verdict`. Hard gate:
>   `make ci` green, 100 % coverage, ≤200-line modules, headers, tunables for any threshold.
>   Bump **MINOR** (0.67.00 → 0.68.00) + `uv lock`.
> - **Part A — `NO_TRADE` acceptance verdict** per packaging decision 2. Truth-table tests:
>   complete+scored → PASS; complete+zero-scored+rejection-evidence → NO_TRADE (exit 0);
>   zero-scored without evidence → FAIL; missing stage → FAIL. CLI prints the verdict.
> - **Part B — verdict projection + endpoint** per decisions 1, 4, 6: `projections_verdict.py`
>   (pure; fake-store tests over the full light truth-table: PASS/NO_TRADE/FAIL × fault-class ×
>   warning-class), `/api/verdict?run=<id>`, folded into `/bundle`.
> - **Part C — frontend hero + de-jargon sweep** per decisions 3 and 5: hero strip (light,
>   summary, next fire, warnings badge), animated with CSS only + `prefers-reduced-motion`;
>   demote section ledes; remove every S-number/DL-id from UI strings.
> - **Part D — jargon-guard test** per decision 5 (static assets + API display strings).
> - **Functionality check (LAW-02):** serve locally against the live Neon spine (read-only).
>   Select `sched-2026-07-10` — today it prints `ACCEPTANCE FAIL`; after Part A the light must be
>   **GREEN** with a "completed — no trades" summary. That flip is the proof. Also screenshot the
>   RED path (any incomplete run id). Record in `docs/laws/functionality-checks.md` + screenshots
>   under `docs/reports/sprint-124-dashboard-verdict/`. Read-only — state the teardown as such.
> - **Wrap up:** README index row, fill the **Closeout** block and append **Return notes** at the
>   very end of this file (both mandatory — see those sections), push, hand back.

## Guardrails

- Surfaces read, never write — no bus, no agent imports, no graph writes.
- Binary light only (decision 1); do not invent an amber state.
- The `NO_TRADE` verdict adds a label; it must not weaken any existing floor, breach check, or
  exit-code contract for genuine failures.
- No chat affordances of any kind — an unwired control is worse than none (req 15 corollary);
  chat is S125. No fleet-behind judgement — S126.
- No internal project vocabulary in anything the operator sees (enforced by Part D).

## Definition of done

1. Opening the dashboard answers "is everything right?" with **zero reading**: a dominant,
   animated RED/GREEN master light + one plain sentence; detail is drill-down.
2. `sched-2026-07-10` shows GREEN "completed — no trades" (and `scripts/accept.py` exits 0 with
   `NO_TRADE`); an incomplete run shows RED with the stalled stage named.
3. No S-number or DL-id anywhere in the UI; the jargon-guard test enforces it in CI.
4. `make ci` green at 100 %; live check recorded with screenshots (GREEN and RED paths).

## Closeout (coding agent fills; planning agent verifies before merge)

```text
CLOSEOUT — Sprint 124
Branch / merge commit:   sprint-124-dashboard-verdict / pending operator merge
make ci:                 GREEN — 1511 passed, 5 skipped, 100.00% coverage
Functionality check:     Live Neon/Azure read-only proof: sched-2026-07-10 = NO_TRADE/GREEN;
                         absent-run RED = stopped before provider. Recorded in
                         docs/laws/functionality-checks.md with GREEN/RED screenshots under
                         docs/reports/sprint-124-dashboard-verdict/. Server stopped; port released;
                         temporary profiles removed; no writes and no data teardown required.
Version:                 0.67.00 → 0.68.00 (MINOR); uv.lock refreshed
Deviations from spec:    No persisted incomplete run remained (all four live scheduled runs were
                         complete), so the RED screenshot uses a read-only absent-run projection
                         and URL deep link; no graph node was fabricated.
```

## Return notes (coding agent appends at handback — mandatory)

Append below, at the very end of this file, everything the next session needs that the closeout
numbers don't carry: surprises found in the code, decisions taken in-flight and why, drift
observed elsewhere, follow-ups you would queue. Do not edit the sections above. A handback is
not accepted while this section is empty or the closeout placeholder is unfilled (LAW-02: the
handback must prove, not restate intent).

<!-- return notes go below this line -->

- The live gate-policy flip is exact: `sched-2026-07-10` moved from the packaged baseline's
  `ACCEPTANCE FAIL` to `ACCEPTANCE NO_TRADE` with exit 0, and its master light is GREEN with five
  evidenced confidence-floor rejections. The same policy also classifies `sched-2026-07-09` as
  `NO_TRADE`; the 07-08 and 07-07 runs remain PASS.
- `NO_TRADE` validates every persisted rejection reason as `confidence < regime floor`, requires
  all seven stages reached, and only permits the analyst-scored / PM-evaluated zero floors. The
  drill-down intentionally retains those raw floor facts while the master verdict and run-result
  card label the completed quiet day pass-equivalent; no trade-path floor was relaxed.
- Warning badges count warning rows/classes, not the raw affected-item total. The live GREEN proof
  has two rows (pending flags and degraded feeds) while the status line retains the underlying
  counts (2 flags, 4 feeds).
- `/api/verdict?run=<id>` projects an absent id as an incomplete RED run, and `/?run=<id>` deep-links
  that diagnostic context into the selector. This was needed because the live spine contained no
  incomplete persisted run and preserves the surfaces-read-never-write boundary.
- On Windows, invoke the acceptance file exactly as its header documents (`PYTHONPATH=.`); direct
  `uv run python scripts/accept.py ...` does not put the repo root on `sys.path`.
