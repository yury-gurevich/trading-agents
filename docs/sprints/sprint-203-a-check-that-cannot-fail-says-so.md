<!-- Agent: planning | Role: sprint handover — every check either can fail, or declares that it could not -->
# Sprint 203 — a check that cannot fail says so

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-203-a-check-that-cannot-fail-says-so` *(already created from `e4ef0b8`)*
**Status:** BUILT
**Version:** `0.98.02` (PATCH)
**Effort:** M
**Decisions:** work-queue **items 53, 56, 41** · [DL-152](../design-log.md) (the recurring shape) · [DRIFT-058](../laws/drift-register.md) (the lesson this generalises) · a new drift row is **owed** — see the law-cycle answer

> **Why this bump kind.** PATCH. Three defects, no new capability: a probe that cannot fail, a report
> that cannot discriminate but prints a confident number, and a switch that would do nothing
> silently. Each is a thing already claiming to work. No contract changes, no new endpoint.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/master/laws/laws.md` | **LOCKED v1.2.** `MST-NEV-06`, `MST-FAIL-04`, `MST-OBS-04` govern credential handover | **Read-only.** A clause you believe is wrong is a `drift-register.md` row plus a report |
| `agents/master/laws/test-plan.md` | proven 🟩 vs unproven ⬜ per master clause | Read alongside `laws.md`; note if a clause you rely on is ⬜ |
| `docs/laws/conventions.md` §9 | drift/register conventions | Read — item 41's answer comes from here |
| `docs/laws/drift-register.md` | the **one** law-adjacent file you may append to | **DRIFT-059 is owed here** (see below) |

**Law-cycle question — does this sprint change `contracts/`, or add a guarantee an agent did not
previously make?**

**No clause is owed, and for item 41 that is itself the finding.** Measured 2026-09-14: master laws
are **LOCKED v1.2** and contain **no remediation clause at all** — `grep -oE "MST-[A-Z]+-[0-9]+"`
returns 44 clause IDs across `DEP/FAIL/IDM/IDN/IN/NEV/OBS/ORD/OUT/PERF/SEC/STA/TRG/TYP`, and not one
of them speaks to remediation. The arc is *deliberately* later (DL-144: Pieces C/D), so **writing a
clause now for an unbuilt feature is premature**. `conventions.md` gives the exact instruction for
this case: *"If a law is silent where you needed a decision, that silence is a finding: record it and
add a `drift-register.md` row."*

🚨 **So item 41 ships as a defensive code fix plus DRIFT-059**, not a law cycle. Do **not** add an
`MST-*` clause; do **not** bump master laws to v1.3. If you believe a clause is genuinely owed, stop
and report rather than writing one.

⚠️ **The invariant this must not break: no probe may start failing for a reason that is not a real
credential failure.** Item 53 makes three probes billable. A malformed request body returns the same
`4xx` as a dead key — this is measured, not theoretical (S202: a bodyless `POST /v1/messages`
returned **400 for a valid key**). Every new probe shape must be measured against the live API in
both arms before it lands.

---

## Goal

Three checks that report success by saying nothing are made to either fail honestly or declare that
they could not have failed.

## Why (context)

[DRIFT-058](../laws/drift-register.md), written 2026-09-13, records the generalisable lesson from
S202: **a green row whose oracle cannot fail proves only that the oracle ran.** These three items are
the same shape in three other places, and [DL-152](../design-log.md) — *a producer that knew
something it never said* — is now at **six** instances.

| # | Where | What it claims | What it can actually do |
| --- | --- | --- | --- |
| **53** | 3 pack `openai` probes + 2 `trading_vault_probes.py` probes | "this credential works" | calls a **free metadata** endpoint; a key that cannot spend passes |
| **56** | `scripts/compare_order_tolerances.py` | "flat and scaled both drop 0.00 %" | true, and it **could not have said anything else** while the narrower band was applied |
| **41** | `remediation_mode=automatic` | a documented operator switch | returns `None` at an unwired guard — **no fault, no flag, no marker** |

### Measured, 2026-09-14

| Claim | Value | How |
| --- | --- | --- |
| Pack `openai` probes | **3**, all `GET https://api.openai.com/v1/models`, all `required: false` | *[measured]* `trading_credential_tests.json` |
| Their `credential_failure_statuses` | already include **429** | *[measured]* same file — **the failure list is right; the endpoint is wrong**, exactly as S202 found for Anthropic |
| What OpenAI returns when drained | `429 … no credits remaining`, 2026-08-19 | *[recorded]* [DL-125](../design-log.md) |
| Vault probes with the same blindness | `probe_openai` (`:111`), `probe_anthropic` (`:121`) | *[measured]* `trading_vault_probes.py` |
| Who calls the vault probes | only `scripts/seed_key_vault.py`, `scripts/seed_key_vault_live_check.py` | *[measured]* grep; they gate **no run** |
| Tolerance report over 170 orders | `flat 0.00` / `scaled 0.00`, identical | *[measured]* `compare_order_tolerances.py` |
| Scaled wider than flat | **170 of 170** (75–250 bps vs a fixed 50) | *[measured]* never equal, never narrower |
| The silent remediation guard | `if llm is None or not catalogue: return None` | *[read]* `remediation_execution.py:141` |
| Why it is always unwired | `entrypoint.py:105` builds `MasterAgent` with none of the four remediation args | *[read]* import-linter forbids `agents → orchestration`, where `build_trading_master` lives (S86/DL-12) |

🎯 **`entrypoint.py:101` already does the right thing three lines above the defect** — it raises
`ValueError` when a secret map arrives with no credential tests. Item 41 is that same move for
remediation; the precedent and the idiom are in the file you are editing.

---

## Scope

### 1. Item 53 — the probes that cannot fail

**1a. The three pack `openai` entries** → a minimal billable call, mirroring what S202 did for
Anthropic. The runner already supports bodies (`json_body`, added S202), so this is a pack edit.

🚨 **MEASURE THE REQUEST SHAPE FIRST — do not take this spec's word for it.** S202's one-line pack
edit would have taken the whole fleet down, and only a live measurement caught it. Before editing the
pack, run all three arms against the real API from the **main** checkout (where `.env` lives) and
record the statuses in the test plan:

| Arm | Expect | Why it matters |
| --- | --- | --- |
| valid key + your body | `200` | the probe must pass for a working key |
| invalid key | a status in `credential_failure_statuses` | the probe must be able to fail |
| valid key + **no body** | *record it* | if this is also `4xx`, a forgotten body is indistinguishable from a dead key |

🪤 **The model field is a drift hazard.** S202 asserts the Anthropic probe's model equals
`llm_factory.DEFAULT_MODEL["anthropic"]` because a retired model name returns **404** and the runner
maps every `4xx` to a credential failure. Do the same for `DEFAULT_MODEL["openai"]` (currently
`gpt-5.5`). 🪰 **Note the parameter name may differ** — newer OpenAI models take
`max_completion_tokens` rather than `max_tokens`. **Measure; do not assume.**

**1b. The two vault probes** (`probe_openai:111`, `probe_anthropic:121`) → same treatment. These gate
no run, so they are lower risk, but leaving a known-blind probe undocumented is how item 50 survived
nine nights. `trading_vault_probes.py` is at **169** lines — if the change pushes it past 200, split
rather than trimming the explanation.

### 2. Item 56 — the report that cannot discriminate

`scripts/compare_order_tolerances.py` (**172** lines) must say when its answer was structurally
determined. The computation is **correct** — `_would_fill` compares the actual execution price
against each mode's limit — so **do not change the arithmetic.** Add the missing statement.

The discriminating condition is: *was the applied band the wider one on every row?* If so, the
narrower mode cannot show a drop and the comparison is uninformative in that direction. Render that
as a labelled line, not a footnote a reader can skip.

🎯 **Since 2026-09-13 the applied band is `scaled`** (the wider one — operator decision, DL-165), so
after a few trading nights this report becomes informative for the first time and the label should
flip on its own. A test should pin **both** states, using fixtures, not live data.

### 3. Item 41 — the switch that would do nothing

Make `remediation_mode="automatic"` refuse to be silent. Two acceptable shapes; pick one and record
why in the sprint doc:

- **Raise at construction** (`entrypoint.py`, mirroring the `:101` precedent) — loudest, fails before
  any escalation exists, and matches the file's idiom.
- **Stamp the `Escalation`** with why no attempt was made — survives into the graph and is queryable
  later, but the run has already happened.

🪤 **Do NOT wire the remediation catalogue.** Pieces C/D are deliberately later (DL-144). The defect
is the *silence*, not the absence.

**Also write DRIFT-059**: master laws are silent on remediation, so a documented operator switch has
no clause governing its behaviour. Status OPEN, with the forced decision named (clause it, or state
that remediation is outside the locked constitution until Pieces C/D land).

### Out of scope

- **Work-queue item 55** (the empty-response outage signature). Deliberately left: S202's corrected
  gate already turns a total-outage night red, so the remaining value is small and it needs net-new
  tooling. It stays ranked below these three.
- **Wiring remediation.** See above.
- **Changing `compare_order_tolerances`' arithmetic.** It is right.

### The road not taken

- **One sprint covering all four "cannot fail" items including 55.** Rejected: 55 needs a new script
  while these three are edits to existing files, and its value was already demoted once (it was filed
  claiming "nothing watches it" hours before S202 made that false).
- **Adding an `MST-*` remediation clause.** Rejected — see the law-cycle answer. Premature for an
  arc that is deliberately unbuilt; conventions call for a drift row instead.
- **Making the OpenAI probes `required: true` while we are in there.** Rejected: that is a posture
  change, not a defect fix, and it would halt three deliberators on a vendor we do not currently use
  (`DELIBERATOR_LLM_PROVIDER=anthropic`). File it if you think it is right; do not do it here.

---

## Blast radius

| What | Detail |
| --- | --- |
| Files changed | `trading_credential_tests.json`, `trading_vault_probes.py` **169**, `compare_order_tolerances.py` **172**, `agents/master/entrypoint.py` **169**, `docs/laws/drift-register.md` |
| Contract change? | No |
| Graph vocabulary change? | **Only if** you choose the stamp-the-`Escalation` shape for item 41 — that adds a property and **moves the pack**, which forces a full `up`. The raise-at-construction shape does not. **State which you chose and what it implies.** |
| Deploy implication | 🚨 **Ask the injected-pack question, not just the vocabulary one.** `trading_credential_tests.json` ships as `MASTER_CREDENTIAL_TESTS_B64`, and `entrypoint.py:42` says **b64 wins** over the baked file — so this needs a **full `up`**, never a retag. See `deploy-fleet` step 1, corrected 2026-09-13 after this nearly shipped inert |
| Live spend added | 3 OpenAI probes × per activation, at whatever your measurement shows. Record the number; do not estimate it |

🪤 **Module headroom is tight.** `entrypoint.py` 169, `remediation_execution.py` 180,
`compare_order_tolerances.py` 172, `trading_vault_probes.py` 169 — all against a **200-line hard
block**. Split before you hit it; `# noqa` is forbidden.

---

## Success factors

- [ ] Each of the 3 pack `openai` probes calls a **billable** endpoint, measured green for a working
      key and **measured failing** for an unusable one.
- [ ] The pack's OpenAI model is asserted equal to `llm_factory.DEFAULT_MODEL["openai"]`.
- [ ] Both vault probes likewise exercise spend, not metadata.
- [ ] `compare_order_tolerances` labels the structurally-uninformative case, with **both** states
      pinned by tests.
- [ ] Its arithmetic is unchanged — assert `_would_fill` behaviour is identical before and after.
- [ ] `remediation_mode="automatic"` with an unwired catalogue **cannot** fail silently.
- [ ] The remediation catalogue is **not** wired.
- [ ] DRIFT-059 written, status OPEN, forced decision named.
- [ ] Every new/changed test watched **red first** (DL-70) — say which, and paste the red output.
- [ ] `make ci` exit 0, 100.00 % coverage, redirected to a **file** and read from the file.
- [ ] `make gate-ran` exit 0 from **this** worktree, printed SHA checked against `git rev-parse HEAD`.

---

## Traps

🪤 **A probe body is a fail-closed path.** Get the shape wrong and every affected probe fails at once
— for a *valid* key. Measure both arms live before committing, and let the runner supply
`content-type` (S202 added `with_json_content_type` for exactly this).

🪤 **Do not "fix" the tolerance arithmetic.** It is correct and was already misdiagnosed once — I
called the script defective in this session and was wrong. The defect is that it does not say when its
answer was forced.

🪤 **`Position.status` stays `"open"` by design** — if any check you write touches positions, use
`is_active_position_node`, never the raw prop ([DL-73](../design-log.md), and I repeated it this
session).

🪤 **Never measure the gate through a pipe.** `make ci | tail` reports `tail`'s exit code. Redirect to
a file and read the file.

🪤 **Run `make gate-ran` from the worktree whose `HEAD` is the commit you are proving** — it resolves
the SHA from the working directory and a `SHA=` argument is ignored. Check the printed SHA.

---

## Test plan

| # | Test | Watched red first? | Status |
| --- | --- | --- | --- |
| A1 | an `openai` pack probe passes for a working key *(live, through the parsed pack and the real transport)* | n/a | 🟩 `CredentialCheckResult(status='passed')` |
| A2 | an `openai` pack probe **fails** for an unusable key *(live)* | n/a | 🟩 `credential_failure / http_401`; a missing key gives `missing_config:OPENAI_API_KEY` |
| A3 | the pack's OpenAI model equals `DEFAULT_MODEL["openai"]` | 🟩 yes -- `KeyError: 'json_body'` against the old pack | 🟩 `test_the_openai_probe_model_tracks_the_adapter_default` |
| A4 | a bodyless variant is refused / recorded | n/a | 🟩 recorded: **400** `you must provide a model parameter` -- the same trap S202 measured for Anthropic |
| A5 | the budget survives a reasoning model's preamble | 🟩 yes (same red) | 🟩 `test_the_openai_probe_budget_survives_a_reasoning_model` -- **new, not in the spec** (see Return notes) |
| A6 | an unlisted 4xx still fails the probe | n/a -- pins pre-existing behaviour | 🟩 `test_an_unlisted_4xx_still_fails_the_probe` (418 -> `credential_failure`) |
| B1 | `probe_openai` exercises spend, not metadata | 🟩 yes -- `'.../v1/models' != '.../v1/chat/completions'` | 🟩 `test_the_registered_probes_use_the_billable_requests`; live `ProbeResult(ok=True)` valid / `ok=False` invalid |
| B2 | `probe_anthropic` likewise | 🟩 yes (same red) | 🟩 same test; both live arms measured |
| C1 | report labels the uninformative case when the applied band is wider on every row | 🟩 yes -- the last line was `scaled 1 1 0.00 40.00`, with no label | 🟩 `test_a_narrower_applied_band_forces_both_columns_to_zero` + `test_the_rendered_report_carries_the_label` |
| C2 | report does **not** label it once a narrower-applied row exists | 🟩 yes (same red) | 🟩 `test_a_wider_applied_band_makes_the_comparison_informative`, plus the sell-side direction, the unclassified row and the no-data case |
| C3 | `_would_fill` results are unchanged by this sprint | n/a -- pins existing arithmetic | 🟩 `test_would_fill_is_unchanged_by_this_sprint` (4 cases); the pre-existing `flat 2 1 50.00 40.00` assertion is untouched |
| D1 | `automatic` + unwired catalogue raises, and does not return `None` silently | 🟩 yes -- `Failed: DID NOT RAISE ValueError` | 🟩 `test_automatic_remediation_refuses_a_master_that_cannot_remediate` |
| D2 | `manual` is unaffected | n/a | 🟩 `test_manual_remediation_is_unaffected` |

---

## Closeout — evidence

**Status:** BUILT, 2026-09-14.

**Tree the proofs ran in:** `C:/Users/yury_/Downloads/project/wt-s203`, branch
`sprint-203-a-check-that-cannot-fail-says-so`, **no `.env`**. The live vendor measurements ran from
that same tree with the key read out of the main checkout's `.env` at call time — no credential file
was ever created inside this worktree.

**Result:** Three checks that reported success by saying nothing now either fail honestly or declare
that they could not have failed. The three pack `openai` probes and both `trading_vault_probes.py`
LLM probes `POST` a real completion instead of reading free metadata, so a key that cannot spend now
fails the DL-36 entry condition instead of passing it. `compare_order_tolerances` ends every report
with a `comparison:` line saying whether its numbers were reachable or structurally forced.
`remediation_mode="automatic"` refuses to start a master that cannot remediate, instead of returning
`None` at an unwired guard and writing nothing at all.

**Proof — the red runs, before each fix:**

```text
# A3/A5 -- the pack probes, against the pre-S203 pack
E   KeyError: 'json_body'        (9 failed, 1 passed)

# B1/B2 -- the vault probes, with trading_vault_probes.py reverted
E   AssertionError: assert ['https://api...dels?limit=1'] == ['https://api.../v1/messages']
E     At index 0 diff: 'https://api.openai.com/v1/models' != 'https://api.openai.com/v1/chat/completions'

# C1 -- the report, with compare_order_tolerances.py reverted
E   AssertionError: assert False
E    +    where ... = 'scaled\t1\t1\t0.00\t40.00'.startswith('comparison: FORCED')

# D1 -- entrypoint with the guard call removed
E   Failed: DID NOT RAISE ValueError
```

**Proof — the live vendor measurement (2026-09-14, `gpt-5.5`, `POST /v1/chat/completions`):**

| Arm | Status | Note |
| --- | --- | --- |
| valid key, `max_completion_tokens: 256` | **200** | 7 input / 26-38 output over five runs |
| invalid key | **401** | `invalid_api_key` |
| valid key, **no body** | **400** | `you must provide a model parameter` |
| valid key, `max_tokens` instead | **400** | `unsupported_parameter` — this model rejects the Anthropic spelling |
| valid key, retired model name | **404** | `model_not_found` |
| valid key, `max_completion_tokens: 1` | **400** | *the near-miss* — see Return notes |

Through the parsed pack and the real transport: `passed` for the live key, `credential_failure /
http_401` for a bogus one. Both corrected vault probes likewise: `ProbeResult(ok=True)` live,
`ok=False` for a bad key, for **both** vendors.

**Proof — the green run:** `make ci` exit **0**, redirected to a file and read from the file.
Counts are recorded in `STATE.md` with the merge.

**`make gate-ran`:** run from this worktree; the printed SHA is recorded in `STATE.md` against the
`git rev-parse HEAD` it was checked against.

**Live measurements (A1/A2 and the per-activation cost):** A1 `passed`, A2 `credential_failure`,
both against the live API. **Cost added per full fleet activation: ~US$0.0028** — three probes x
(7 input tokens @ $5/M + ~30 output @ $30/M) is about US$0.00094 each, roughly **A$0.004** at the
pricing pack's `aud_per_usd` of 1.3945. Taken from the vendor's own `usage` block, not estimated.
The Anthropic vault probe adds one more billable call to a seeding script that only runs by hand.

**Item 41 shape chosen, and why:** **raise at construction.** The spec offered raise-or-stamp. The
stamp shape adds an `Escalation` property, which moves the graph vocabulary pack and forces a full
`up` — a deploy cost for a defect that never reaches an escalation in the first place. Raising
mirrors the check three lines above it in `build_app`, fails before any run happens rather than
after it, and adds no vocabulary. It lives in its own module (`agents/master/remediation_posture.py`)
because `entrypoint.py` was already at 169 of 200 lines.

**Not met / verified failing:** nothing in scope was left unmet. Two honest limits: (1) the OpenAI
probes stay `required: false`, so a drained OpenAI key still will not halt activation — a posture
decision the spec ruled out of scope, now filed as **work-queue item 58** rather than done quietly;
(2) the tolerance label is proven on fixtures, not yet on the live book — the first fills recorded
under the promoted `scaled` band will flip it to `INFORMATIVE` on their own, and nothing here forces
that to happen sooner.

---

## Return notes

**The spec was right about the shape and wrong about one number, and the number would have taken
three deliberators down.** It said to mirror S202's Anthropic body, whose budget is `max_tokens: 1`.
Measured: `gpt-5.5` is a reasoning model and spends the whole budget on reasoning tokens before
emitting any content, so `max_completion_tokens: 1` returns **400 for a valid key**. That is exactly
the failure mode the spec's own trap section warned about, arriving through the parameter the spec
told us to copy. Five runs at 256 consumed 26-38 completion tokens, and an unreached cap is charged
nothing — so a generous cap is strictly safer at identical cost. 🪰 **Generalisable: when a probe
is copied between vendors, the token budget is part of the request shape, not a constant.**

**A second thing the spec did not know: `credential_failure_statuses` has never done anything.** The
runner's two 4xx branches were textually identical, so any non-expected status below 500 is a
credential failure whether the pack lists it or not. S202's "the failure list is right; the endpoint
is wrong" was therefore true for a different reason than it reads — the list could not have been
wrong, because it is never consulted. The fail-closed behaviour is correct and is left exactly as it
was; the identical branches are collapsed and commented so the field stops reading like a control,
and `test_an_unlisted_4xx_still_fails_the_probe` pins it. Whether it *should* become a real filter
(an unlisted 4xx as a transport fault rather than a credential fault) is a behaviour change with
fail-closed consequences — filed as **work-queue item 57**, not decided here.

**What the next sprint should know about item 56.** The label is computed from
`order_tolerance_mode` on the `Fill`, which records the band that was actually applied. A row can
only discriminate when the applied band is the **wider** one — then a fill above the narrower limit
is precisely an order the narrower mode would have refused. Before DL-165 that was true on 0 of 170
rows; after it, it should be true on every new row. 🎯 **If the label still reads `FORCED` after a
week of trading under `scaled`, the promotion did not reach the fleet** — and that is now visible
without re-deriving the argument from first principles.
