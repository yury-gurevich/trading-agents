<!-- Agent: planning | Role: sprint handover — a credential probe spends, and an absent veto is not green -->
# Sprint 202 — a credential probe that cannot fail is not an entry condition

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-202-a-probe-that-cannot-fail-proves-nothing`
**Status:** BUILT
**Version:** *next available MINOR at merge*
**Effort:** S
**Decisions:** work-queue **item 50** (closed) · [DL-163](../design-log.md) (operator decision) · [DL-164](../design-log.md) (implementation, re-sequenced) · **DRIFT-058** (new, CORRECTED) · [DL-125](../design-log.md) non-regression · work-queue **item 53** (new)

> **Why this bump kind.** MINOR. The probe schema gains a field packs can use (`json_body`) and the
> Anthropic probes move to a different endpoint — new capability on both counts, even though the
> sprint exists to fix a defect. Under-bumping a capability is the failure the HARD RULE guards.

---

## 🔴 MUST RULE — laws read before code

| Location | What lives there | How treated |
| --- | --- | --- |
| `agents/master/laws/laws.md` | `MST-NEV-06`, `MST-FAIL-04`, `MST-OBS-04` — credential handover | read; **not edited** |
| `agents/master/laws/test-plan.md` | proven/unproven per master clause | read; `MST-NEV-06` gains a citation |
| `agents/execution/laws/laws.md` | `EXEC-OUT-09`, `EXEC-OBS-04` — posture + fail-open severity | read; **not edited** |
| `agents/execution/laws/test-plan.md` | proven/unproven per execution clause | read; `EXEC-OBS-04` gains two citations |
| `docs/laws/drift-register.md` | the appendable law-adjacent file | **DRIFT-058 added and CORRECTED here** |

**Law-cycle question — does this sprint change `contracts/`, or add a guarantee an agent did not
previously make?** **No, and that is the finding.** `MST-NEV-06` already promises a credential has
*"passed live"* before handover, and `EXEC-OBS-04` already promises acceptance can distinguish an
advisory outage from a binding no-verdict submission. Both clauses meant what this sprint makes true;
neither was delivered. So no clause is owed, no `contracts/` file changes, and the vocabulary pack
does **not** move — but a drift row is owed, because a clause that was green on an oracle that cannot
fail is a register row, not a silent fix (conventions §9).

⚠️ **The invariant this must not break: a veto that ran and degraded on *some* of its subjects
stays green.** The change makes a veto that reviewed **nothing** red — by either route. Asserted
directly, not assumed: `test_a_partially_degraded_veto_stays_green`, parametrised over 1-of-2,
1-of-3 and 2-of-3 failures.

🪤 **The first cut of this sprint drew that line in the wrong place** — see the Correction section
below. It keyed on the absent-`DeliberationRun` statuses only, and would have fired on **0** runs
while leaving all **4** real occurrences green.

---

## Goal

The required Anthropic credential probe fails when the account cannot spend, and a run that
submitted buys with no veto at all reports red under `advisory` posture.

## Why (context)

Work-queue item 50, from **nine** blind nights — `2026-08-21, -24, -25, -26, -28` and
`2026-09-08, -09, -10, -11`, each with `real_debate_count = 0`. Every deliberator activated clean and
every debate then failed with `400 … credit balance is too low`. *(Item 50 was filed citing four
nights; the full extent was measured on 2026-09-13 by `/audit-costs`.)*

🚨 **DL-36 Piece A was built correctly and asked the wrong question.** The probe's
`credential_failure_statuses` already contained **400**. It called `GET /v1/models` — free metadata,
no tokens, not billed. A key on a zero-credit account is a **valid** key, so the probe returned 200
and handover proceeded. *The failure list was right; the endpoint was wrong.*

### Measured, 2026-09-13 — against the live Anthropic API

| Request to `POST /v1/messages` | Status | Meaning |
| --- | --- | --- |
| valid key, `max_tokens: 1`, body present | **200** (7 in / 1 out) | probe passes, **$0.00006** |
| invalid key | **401** | credential failure |
| valid key, **no body** | **400** | 🚨 a *valid* key fails |
| valid key, retired model name | **404** | a pack typo reads as a credential failure |

🪤 **Row three is why this is not the one-line pack edit DL-163 predicted.** `HttpProbeRequest`
carried no body, so pointing the pack at `/v1/messages` alone would have returned 400 for every key
and failed **all four required** Anthropic probes at once — a credit outage traded for a total
activation outage.

🪤 **Row four is why the gate could not be deferred.** A 404 from a rotted model name halts all three
deliberators; under `advisory` the run then submits its buys with no veto and a **green** board. A
stricter probe without a run-level gate converts our own config drift into unreviewed orders.

### Measured, 2026-09-13 — against the live spine, over the 40 linked `ExecutionRun` rows

| Condition | Occurrences |
| --- | --- |
| `advisory` + `proceeded_unvetoed` | **0** |
| `advisory` + `applied_failed_open`, `failed_open_count == reviewed` | **4** |
| `advisory` + `applied_failed_open`, `0 < failed_open_count < reviewed` | **0** |
| `advisory` + `applied` (clean) | 7 |
| `advisory` + `not_required` | 1 |
| no posture prop (predates S185) | 28 |
| **total `ExecutionRun`** | **69** |

🎯 **Row two is the incident.** All four carry `real_debate_count = 0` and a `failed_open_reason`
naming `400 … credit balance is too low`. The rule has to reach them, and keying on row one alone
does not — that was the first cut's error, corrected below.

🪤 **Row three is the case that stays green, and it has occurred 0 times.** The status label made a
partial fail-open look like the common case; the ledger says the opposite.

---

## Scope

1. **Probe bodies exist** — `HttpProbeRequest.body`, a `json_body` validator serialising with sorted
   keys, and a `with_json_content_type` helper the runner applies so no pack entry can forget it.
2. **The transport sends the body** — `data=request.body`, which is `None` for every pre-existing
   GET, leaving them byte-identical.
3. **Four pack entries move** to `POST https://api.anthropic.com/v1/messages` with
   `{"model": "claude-opus-5", "max_tokens": 1, "messages": [{"role": "user", "content": "."}]}` —
   `operator`, `deliberator-manager`, `-proponent`, `-opponent`. All four are `required: true`.
4. **A veto that could not execute breaches**, as `veto_never_ran`, by **either** route —
   `proceeded_unvetoed` with an approved buy (no `DeliberationRun`), or `applied_failed_open` where
   every reviewed subject failed open (a `DeliberationRun` that reviewed nothing).
4b. **The attribution logic moves to its own module**, `trading_deliberation_attribution.py`, because
   it now carries real policy and the view was at 194 of 200 lines.
5. **Two drift guards** — the pack's probe model is asserted equal to
   `llm_factory.DEFAULT_MODEL["anthropic"]`; the content type is supplied by the runner.
6. **DRIFT-058** written and CORRECTED; **item 53** filed for the probes left blind on purpose.

### Out of scope

- **The three `required: false` OpenAI probes** and **`orchestration/packs/trading_vault_probes.py`**
  — the same blindness exactly. Queued as **item 53**: the OpenAI entries halt nothing, and the vault
  probes are reached only by the two `seed_key_vault*` scripts, which gate no run. Recorded rather
  than silently left, because an undocumented blind probe is how this defect survived four nights.
- **Re-probing between debates.** Credit exhausted *mid-run* is still uncovered; see DL-164.
- **A law cycle.** Answered No above, with the reason.

### The road not taken

- **Render config templates into the probe body.** Rejected: the credential travels in a header so a
  body carries no secret, and `format_map` over JSON would have to escape every brace.
- **Classify `404` as a pack defect, not a credential failure.** Rejected as scope — the reason
  string is already `http_404`, halting is right either way, and the model-drift assertion removes
  the likeliest cause. Recorded in DL-164 because it is a real asymmetry.
- **Make every absent veto red regardless of posture or direction.** Rejected: the rule is about
  *unreviewed exposure*, which is why a sell-only `proceeded_unvetoed` run stays green.
- **Key the rule on the status label alone.** Tried first, and it produced a gate that fires on
  **0** of 69 runs while the condition the operator named sits in the ledger 4 times under a
  different label. Rejected on measurement; see the Correction section.
- **Let each pack entry declare its own `content-type`.** Rejected: forgetting it produces a 400
  indistinguishable from an exhausted credential, on a fail-closed path. The runner defaults it and
  still lets a pack override.

---

## Blast radius

| What | Detail |
| --- | --- |
| Files changed | `credential_probe_support.py` **131**, `credential_probes.py` **164**, `credential_probe_transports.py` **62**, `trading_credential_tests.json`, `trading_deliberation_view.py` **194** |
| Tests added | `agents/master/tests/test_credential_probe_body.py` **175** (new), `orchestration/tests/test_trading_deliberation_unvetoed.py` **99** (new) |
| Contract change? | No |
| Graph vocabulary change? | **No** — `advisory_attribution` is an acceptance-view observed key that already existed; only its value set grows |
| Deploy implication | 🚨 **Full `up`, never a retag** — corrected below. The vocabulary pack does **not** move, but `trading_credential_tests.json` is injected as `MASTER_CREDENTIAL_TESTS_B64` and `b64` wins over the baked file, so only an `up` refreshes it |
| Live spend added | **$0.00006** per Anthropic probe activation, ×4 required probes = **$0.00024** per full fleet activation (7 input at $5/MTok + 1 output at $25/MTok — Opus 5 rates verified 2026-09-13 against `platform.claude.com`, matching `orchestration/packs/llm_pricing.json`) |

---

## Success factors

- [x] A declared `json_body` reaches the transport as deterministic sorted bytes.
- [x] A body probe gets `content-type: application/json` without a pack entry declaring it.
- [x] A pack-declared content type is not duplicated.
- [x] Every pre-existing bodyless probe still sends `body is None`.
- [x] A 400 from a drained account refuses activation and writes an `Escalation`.
- [x] All four required Anthropic probes POST to `/v1/messages` with `max_tokens: 1`.
- [x] The pack's probe model equals the adapter default — asserted, not assumed.
- [x] `advisory` + `proceeded_unvetoed` + a buy breaches as `veto_never_ran`.
- [x] `applied_failed_open` with a reason stays green (DL-125 non-regression).
- [x] Binding posture untouched.
- [x] Tests watched **red first** — 14 failures.
- [x] `make ci` exit 0, 100.00 % coverage.
- [x] The real pack, loaded through the real runner, probes the live API green.

---

## Traps

🪤 **A green law row whose oracle cannot fail proves only that the oracle ran.** `MST-NEV-06` was
green on a correct test of a runner that was never the defect. Before trusting a probe, ask what
result would falsify it — `GET /v1/models` has no such result. This is the generalisable lesson and
it is recorded as **DRIFT-058**, not just here.

🪤 **Tightening a precondition without tightening the gate it feeds can make the failure worse.**
DL-163 sequenced the probe first on the grounds that it "fails before orders exist". It does not —
DL-36 halts the *agent*, and under `advisory` the run proceeds. Both halves had to ship together.

🪤 **The existing `proceeded_unvetoed` parametrize case in
`test_trading_deliberation_not_required.py` still passes — but only because its fixture approves no
buy.** A comment now says so at the call site. A test that keeps passing for a different reason than
its name implies is worse than one that fails.

---

## Test plan results

| # | Test | Status |
| --- | --- | --- |
| A1 | `test_declared_json_body_reaches_the_transport_as_sorted_bytes` | PASS (red first) |
| A2 | `test_a_body_probe_gets_a_json_content_type` | PASS (red first) |
| A3 | `test_a_pack_declared_content_type_is_not_duplicated` | PASS |
| A4 | `test_a_probe_declaring_no_body_sends_none` | PASS (red first) |
| A5 | `test_a_non_object_json_body_is_rejected_at_load` | PASS (red first) |
| A6 | `test_a_drained_key_refuses_activation` | PASS (green both sides — the runner was never the defect) |
| A7 | `test_the_anthropic_probe_spends_rather_than_reading_metadata` ×4 | PASS (red first) |
| A8 | `test_the_probe_model_tracks_the_adapter_default` ×4 | PASS (red first) |
| B1 | `test_unvetoed_advisory_buy_breaches` | PASS (red first) |
| B2 | `test_unvetoed_advisory_sell_only_run_stays_green` | PASS |
| B3 | `test_unvetoed_advisory_with_unreadable_pm_payload_breaches` | PASS (red first) |
| B4 | `test_a_veto_that_reviewed_nothing_breaches` ×3 | PASS (the 4 real occurrences) |
| B5 | `test_a_partially_degraded_veto_stays_green` ×3 | PASS (the case that stays green) |
| B6 | `test_a_fail_open_without_a_reason_is_still_unattributed` | PASS |
| B7 | `test_a_clean_applied_veto_stays_green` | PASS |
| B8 | `test_binding_posture_is_untouched_by_the_advisory_rule` | PASS |
| B9 | `test_advisory_veto_that_reviewed_nothing_fails_acceptance` (end to end) | PASS |
| B10 | `test_advisory_fail_open_on_every_subject_does_not_pass` | PASS |

---

## Closeout — evidence

**Status:** BUILT

**Tree the proofs ran in:** `C:/Users/yury_/Downloads/project/wt-s202`, **no `.env`**. The live API
measurements and the end-to-end pack probe ran in the **main** checkout, where `.env` lives.

**Result:** the four required Anthropic probes exercise spend capability, and an advisory run that
submitted buys with no veto at all reports `veto_never_ran` instead of `ok`.

**Proof — the red run, before the fix:**

```text
E  AssertionError: assert 'ok' == 'veto_never_ran'
FAILED orchestration/tests/test_trading_deliberation_unvetoed.py::test_unvetoed_advisory_buy_breaches
FAILED orchestration/tests/test_trading_deliberation_unvetoed.py::test_unvetoed_advisory_with_unreadable_pm_payload_breaches
FAILED agents/master/tests/test_credential_probe_body.py::test_declared_json_body_reaches_the_transport_as_sorted_bytes
FAILED agents/master/tests/test_credential_probe_body.py::test_a_body_probe_gets_a_json_content_type
FAILED agents/master/tests/test_credential_probe_body.py::test_a_probe_declaring_no_body_sends_none
FAILED agents/master/tests/test_credential_probe_body.py::test_a_non_object_json_body_is_rejected_at_load
FAILED agents/master/tests/test_credential_probe_body.py::test_the_anthropic_probe_spends_rather_than_reading_metadata[operator]
... 14 failed, 7 passed
```

🪤 The **7 that passed** are the non-regression guards — DL-125's fail-open cases, binding posture,
the sell-only branch, and the 400-refuses-activation path. Green on both sides is the correct result
for those: they assert what must **not** change.

**Proof — the green run:** `make ci` **exit 0**, `2695 passed, 6 skipped`, coverage `100.00 %`,
pip-audit clean, detect-secrets clean.

**Not met / verified failing:** none.

---

---

## Correction — the rule as first built could never have fired

Found by `/audit-costs` the same day, before merge. The first cut keyed only on
`proceeded_unvetoed`, and this document reported *"turns 0 of 69 runs red"* as a **feature**. It is
not one: it means the tripwire is **inert**.

| Condition | Occurrences (40 linked `ExecutionRun` rows) |
| --- | --- |
| `advisory` + `proceeded_unvetoed` — *what the first cut keyed on* | **0** |
| `advisory` + `applied_failed_open`, `failed_open_count == reviewed` | **4** |
| `advisory` + `applied_failed_open`, `0 < failed_open_count < reviewed` | **0** |

All four of row two carry `real_debate_count = 0` and a `400 … credit balance is too low` reason —
the incident this sprint exists for, left green by the first cut. **The line is partial-vs-total,
not present-vs-absent.**

🪤 **I cited DL-125 as forbidding this and it says no such thing.** DL-125 argued against nightly red
*for a declared, accepted, external outage*, proposing the declared `advisory` posture so
knowingly-unvetoed submissions get "a stated mode with a truthful green"; its own `sched-2026-08-21`
record treats that run **failing acceptance** as correct. Citing it from memory rather than reading
it is the same error as pricing the probe from memory — both in this sprint, both caught the same day
by running a check rather than by re-reading my own conclusions.

🪤 **Three tests were passing for a reason their names did not describe**, each with a 1-of-1 fixture
that reads as partial and is total: S185's `test_advisory_fail_open_passes_when_attributed`, its
end-to-end twin, and S191's `proceeded_unvetoed` parametrize case. All three fixtures are now
explicitly one or the other. The end-to-end cascade approves exactly **one** order, so it cannot
express a partial fail-open at all; that test now asserts the total outage it actually builds, and
the partial case is asserted at the unit level.

**Corrected numbers:** the outage is **nine** nights, not four. The probe costs **$0.00006**, not
$0.00018 — the first figure used Opus **4.1**'s retired $15/$75 from memory; Opus 5 is $5/$25,
verified against `platform.claude.com`.

🎯 **The signature was free and unwatched.** Every call on those nine nights recorded
`response_hash = e3b0c44298fc…` — SHA-256 of the empty string — at **~300 ms** against a working
night's **~15,000 ms**. The ledger could have named this on 2026-08-21, nineteen days before item 50
was filed. Queued as **item 55**.

### 🚨 Second correction — this needs a full `up`, not an image-only retag

Measured 2026-09-13 while deploying, against the live fleet. The Blast radius table above said
*"image-only retag is sufficient"* on the grounds that the **vocabulary** pack does not move. That
reasoning is right about the vocabulary pack and wrong about this sprint, because the file this
sprint edits is delivered a different way.

| Fact | Value | How |
| --- | --- | --- |
| `trading_graph_vocabulary.json` at `s200` vs `HEAD` | `58769995…` **both** | *[measured]* `git show <sha>:… \| sha256sum` |
| `trading_credential_tests.json` at `HEAD` | `b1496f71…` | *[measured]* same |
| **Deployed** `MASTER_CREDENTIAL_TESTS_B64`, decoded | **`307e2a9a…`** | *[measured]* `az containerapp show -n master` |
| What the deployed pack probes | `GET /v1/models` on **all four** | *[measured]* decoded the live env var |

🚨 **`agents/master/entrypoint.py:42` says `b64` wins**: *"b64 wins so the master image stays
pack-agnostic — the pack is injected at [deploy time]"*. `infra/deploy-agents.ps1:637`
(`Get-MasterCredentialTestsEnv`) is what sets it, and only a full `up` re-runs that function. So an
image-only retag would have pushed new images that still read the **old** credential pack out of an
env var — the fix live in the image, inert in the config, and every verification of "the fleet is on
`s202`" would have passed.

🪤 **That is the DL-46 currency failure in its purest form, and the skill's own step-1 question does
not catch it.** *"Did the vocabulary pack move?"* is the right question for image-vs-pack skew in the
graph write guard; it is the wrong question for a sprint whose payload is a **different** injected
pack. The general rule this sprint adds: **ask which of a change's artifacts are injected at deploy
time, not just whether the vocabulary pack moved.** Three packs are injected that way today —
`GRAPH_VOCABULARY_B64`, `MASTER_CREDENTIAL_TESTS_B64`, `PORTFOLIO_MANAGER_ISSUER_MAP_B64` — and a
retag refreshes none of them.

**Third time in one sprint that a claim made from reasoning failed against a measurement** (the probe
price, the DL-125 citation, and now the deploy path). Each was caught by running the check rather
than by re-reading the reasoning.

## Return notes

- **DL-163 sequenced this wrong and measuring it is what caught that.** Its "probe first, it is
  cheaper, it fails before orders exist" held for the first two clauses and not the third. A bodyless
  POST fails for a valid key, and a halted deliberator does not halt the run. The one-line pack edit
  it recommended would have taken the whole fleet down.
- **The gate change is not a new policy.** `not_required` with an approved buy was already red
  (`buy_veto_missing`, S191). `proceeded_unvetoed` is the same fact with a more honest label, and it
  was green. The board's verdict depended on the wording.
- **The correction below matters more than the original diff.** A gate that fires on nothing is
  worse than no gate, because it reports as coverage. It was caught by running `/audit-costs`,
  not by re-reading the sprint — a check that touches real data beats another pass over my own
  reasoning.
- **The deploy question is not always "did the vocabulary pack move?"** Three packs are injected
  at deploy time and a retag refreshes none of them. This sprint's payload was one of the other
  two, and the habit of checking only the vocabulary hash would have shipped an inert fix.
- **What the next sprint should know:** **item 53** is the rest of this defect — three OpenAI probe
  entries and two vault probes that also cannot fail. They gate nothing today, which is why they
  were left; they are written down so they are not rediscovered by another four-night outage.
