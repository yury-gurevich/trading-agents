<!-- Agent: deliberator | Role: sprint spec — make every value rendered into the debate packet state its own unit and scope -->
# S177 — every number in the packet names its unit and its scope

**Closes:** work-queue items 16 and 18 · **Opens from:** [DL-112](../design-log.md),
[DL-104](../design-log.md) (a)(b) · **Type:** fix ·
**Target version:** next available PATCH at merge — **do not pin it in this file** ·
**Branch:** `sprint-177-every-number-names-its-unit`

> Handover to a delegated coding agent. Everything under **Measured** was read off this repo or the
> live spine on **2026-08-15**, after `s176b` deployed. Everything marked **Assumed** has **not**
> been verified — check it before building on it. Do not treat an unmarked claim as measured.

## Why

**Four times now, the deliberator has vetoed a real order because a value in its packet could only
be misread.** Not one of the four was a wrong number. Every one was a *correctly computed* value
whose name did not carry its unit or its scope, and a careful reader — human or model — drew the
only conclusion the label supported.

| # | The value | What the reader assumed | What it actually was | Cost | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | `stop_pct vs ATR% -> PASSED` inside the `stop_vs_regime_volatility gate:` line | a gate outcome | a comparison **no gate performs**, on a **41-period** ATR beside the analyst's 14-period | 6 of 15 objections (DL-104) | **fixed** S175 |
| 2 | absent portfolio/batch facts | the book is empty | the packet simply **carries no holdings** | SCHW, then AVGO/CSCO/GOOGL | **fixed** S175 |
| 3 | `sentiment_positive=11` beside `sentiment_articles=9` | 11 articles vs 9 articles → corrupt feed | **11 lexicon word occurrences** across **9 headlines** | XOM + part of AMZN | **fixed** DL-112 |
| 4 | `deployed=0.00` in `max_sector_pct` detail | zero portfolio exposure to Semiconductors | **zero exposure *from this batch so far*** | AVGO `overturn` | **OPEN — this sprint** |

**Measured, instance 4.** In [`concentration.py`](../../agents/portfolio_manager/domain/concentration.py),
`SectorBook.__init__` seeds `self._names` from held positions and **never seeds `self._deployed`**.
So `deployed` accumulates only within one PM run. On `sched-2026-08-14`:

```text
AVGO   max_sector_pct        sector=Semiconductors; deployed=0.00;    order_cost=786.04
       max_names_per_sector  sector=Semiconductors; existing_sector_names=2
GOOGL  max_sector_pct        sector=Media;          deployed=687.05;  order_cost=691.72
```

`existing_sector_names=2` correctly saw AMD and NVDA. `deployed=687.05` for GOOGL is **exactly**
GOOG's `order_cost` from moments earlier in the same batch. Both numbers are right; only one of them
is readable. The judge overturned AVGO for *"the sector cap reports Semiconductors deployed=0.00
despite AMD/NVDA already held, so the buy approval rests on a false sector-exposure input"* — which
is a correct objection to the **label** and a wrong conclusion about the **data**.

**The point of this sprint is the class, not the fourth instance.** Fixing `deployed` alone buys one
veto. The packet has ~20 rendered value sites, and four have now been found defective *by a model
reading them in production* — the cheapest possible detector, but only after the order was lost.

## The design decisions this sprint has to make

**1 · Does `deployed` get a better name, or does the gate change behaviour?** 🚨 **Recommended:
name only.** Seeding `_deployed` from held positions would change **which orders get approved** —
a trading-behaviour change with its own risk, belonging in an ADR, not in a labelling sweep.
**Measured:** the dollar cap is near-inert today anyway — threshold `0.3 × $102,777 = $30,833`
against ~$1,000 positions, so `max_names_per_sector=3` binds first every time. File the behaviour
question as its own item; do not fold it in.

**2 · What is the convention?** Two families need different answers:

- **Producer-owned names** (`sentiment_*`, gate `detail=` strings): put the unit or scope **in the
  name**, as DL-112 did. `deployed` → `deployed_this_batch` (or equivalent). Durable, and it
  survives anything downstream.
- **Open-name dicts** the deliberator does not own — `candidate.metrics`, `verdict.features`,
  `market.fundamentals` (vendor keys) — **cannot be renamed at the render site.** Decide between a
  rendered scope prefix, a legend line, or an explicit "units unknown" boundary in the style of the
  `_PORTFOLIO_BATCH_BOUNDARY` constant S175 added. **This is the real design question.**

**3 · Is a rendered boundary enough, or must each value be individually correct?** S175's
`_PORTFOLIO_BATCH_BOUNDARY` proved a blanket disclaimer works for *absence*. That the same shape
works for *units* is **Assumed, not measured**.

## The audit surface — every rendered value site

**Measured** by reading [`context.py`](../../agents/deliberator/context.py) and
[`context_pm.py`](../../agents/deliberator/context_pm.py) in full on 2026-08-15.

| Site | Risk | Note |
| --- | --- | --- |
| `_gate_line` `detail=` free text (`context_pm.py:82-88`) | 🚨 **known defective** | where `deployed=` lives; every gate writes its own detail string with no convention |
| `_quant_metrics` (`context_pm.py:148-155`) | 🚨 **partly fixed** | DL-112 fixed two names; the rest are unaudited. **Check `atr_pct` — its period is stated nowhere**, and instance 1 was an ATR period confusion |
| `_dict(market.fundamentals[t])` (`context.py:124`) | high | **vendor keys, mixed units** — ratios, dollars and percents under free-form names, all rendered `.4g` |
| `_dict(candidate.metrics)` (`context.py:141`) | high | scanner metric names, open set |
| `_dict(verdict.features)` (`context.py:102`) | high | filter feature names, open set |
| `market.quality.requested/returned` (`context.py:110`) | medium | a **ticker** count (`98/99`) rendered near bar counts |
| `Provider sentiment` (`context.py:126`) vs `sentiment_score` (`context_pm.py:29`) | medium | two scorers for one concept (lexicon champion, provider advisory). **Measured: `market.sentiment` is `{}` in the latest snapshot, so the collision is not live today** — it returns if the provider feed does |
| `_pct` vs `_num` (`context_pm.py:140-145`) | medium | `0.05` renders as `5.00%` or `0.050` depending only on **which helper the author picked** |
| `est_price={amount} {currency}` (`context_pm.py:65-71`) | low | dollars here; the stored field is `est_price_cents`. Confirm no site renders cents beside dollars |
| `_PORTFOLIO_BATCH_BOUNDARY` (`context.py:31-35`) | — | the S175 precedent to extend, or the thing to prove insufficient |

## Steps, in order

1. **Reproduce instance 4 as a failing test** before changing anything — a `SectorBook` with a held
   position in a sector must render a detail string a reader cannot mistake for portfolio exposure.
2. **Decide and record the convention** (decisions 1–3) in `docs/design-log.md` **before** applying
   it. LAW-06: the road not taken is part of the deliverable.
3. **Fix instance 4** by the chosen convention. Do **not** change `SectorBook` gate behaviour.
4. **Walk the audit table row by row.** Each row gets a verdict in the closeout: *correct as-is*,
   *fixed*, or *cannot be fixed at this site + why*. A row with no verdict is an incomplete sprint.
5. **Add the guard.** At least one test that fails if a gate `detail=` string reintroduces an
   unscoped accumulator name.
6. `make ci` green, **plant each new guard and watch it fail**, restore.

## Success factors

- [ ] `deployed` (or its replacement) cannot be read as portfolio-wide exposure — asserted in a test.
- [ ] `SectorBook` approval behaviour is **unchanged** — proven by a zero diff in existing tests.
- [ ] Every row of the audit table carries a verdict in the closeout.
- [ ] The convention is recorded in `docs/design-log.md` with its rejected alternatives.
- [ ] Each new guard was **planted and watched to fail**, then restored — stated per guard.
- [ ] `make ci` exit 0, 100.00 % coverage, module sizes under the warn line.
- [ ] The behaviour question from decision 1 is filed as its own item, not silently fixed.

## Traps

🪤 **Do not fix this by teaching the prompt.** All four instances could be papered over with prompt
text explaining the units. That makes correctness depend on prompt wording every future reader must
also receive — rejected in DL-112 for exactly that reason.

🪤 **`Recommendation.quant_metrics` is vocabulary-enforced as a *single* property.** Metric names
*inside* it are free, so renaming them does **not** move the pack and the deploy stays an image-only
retag. **Verify before relying on it:** `git show HEAD:orchestration/packs/trading_graph_vocabulary.json
| sha256sum` against the deployed commit.

🪤 **A renamed metric key has two ends.** DL-112's rename needed the producer (`sentiment_rules.py`),
the consumer (`sentiment_reading.py`) and four test files. Grep the old name to zero before
declaring done.

🪤 **Historical graph nodes keep the old names.** 433 `SentimentReading` nodes and every past
`Recommendation` carry pre-rename keys. Do not write a migration; do not assert on historical props.

🪤 **The gate `detail=` strings are written by the PM, read by the deliberator, and owned by
neither.** A convention living only in the deliberator will not stop the next PM gate from inventing
an ambiguous name.

## Handover — paste this to Codex

```text
Work item: S177 — every number in the debate packet names its unit and its scope.
Repo: trading-agents. Read docs/sprints/sprint-177-every-number-names-its-unit.md in full before
writing anything. Read CLAUDE.md. Read docs/INDEX.md before opening any docs folder.

WHAT IS WRONG
The deliberator has now vetoed four real orders because a value in its packet could only be
misread. None of the four was a wrong number - each was correctly computed under a name that did
not carry its unit or scope. Three are fixed (S175 x2, DL-112). The fourth is open:

  agents/portfolio_manager/domain/concentration.py, SectorBook.__init__ seeds self._names from
  held positions but NEVER seeds self._deployed. So the max_sector_pct detail string renders
  "deployed=0.00" meaning "nothing from THIS BATCH yet", while reading as "no portfolio exposure
  to this sector". On sched-2026-08-14 the judge OVERTURNED a real AVGO buy for exactly that,
  even though existing_sector_names=2 in the same gate report correctly saw AMD and NVDA held.
  Proof that deployed is batch-scoped: GOOGL's deployed=687.05 is exactly GOOG's order_cost from
  moments earlier in the same run.

WHAT TO DO
1. Failing test first, reproducing the misreadable string.
2. Record the naming convention in docs/design-log.md WITH rejected alternatives, before applying.
3. Fix the label. DO NOT change SectorBook approval behaviour - seeding _deployed from held
   positions changes which orders get approved and needs its own ADR. File it separately.
4. Walk every row of the audit table in the spec. Each row gets a verdict in the closeout:
   correct as-is / fixed / cannot be fixed here + why. Pay attention to atr_pct in quant_metrics -
   its period is stated nowhere, and an ATR period confusion was instance 1.
5. Add a guard that fails if a gate detail= string reintroduces an unscoped accumulator name.
6. make ci green. Plant EVERY new guard, watch it fail, restore. Report each plant in the closeout.

CONSTRAINTS
- Do not fix this with prompt text. Rejected in DL-112: it makes correctness depend on prompt
  wording that every future reader must also receive.
- Metric names inside Recommendation.quant_metrics are NOT vocabulary-enforced (quant_metrics is
  one enforced property). Renaming them must not move the pack - verify the sha256 either side.
- A renamed key has a producer, a consumer and tests. Grep the old name to zero.
- Do not migrate historical nodes and do not assert on their props.
- Branch sprint-177-every-number-names-its-unit. Version: next available PATCH at merge, do not
  pin it. Fill in the Closeout block at the bottom of the spec before handing back.
```

## Closeout — evidence

<!-- FILL THIS IN BEFORE HANDING BACK. A handback with this placeholder intact is not accepted. -->

**Result:** implemented on branch `sprint-177-every-number-names-its-unit` as `0.90.12`.
`SectorBook` approval behaviour was not changed: the old sector-cap and sector-name tests still
pass, and the new tests assert only evidence labels/rendering. The graph vocabulary pack is
unchanged versus `HEAD`; current SHA-256:
`13c0e3a0ef38eed61019c35cecf252f5729967979011bdfbf0146d8c907ad3ff`.

**Files changed:** `agents/portfolio_manager/domain/concentration.py`,
`agents/portfolio_manager/domain/position_gates.py`,
`agents/portfolio_manager/domain/exits.py`, `agents/deliberator/context.py`,
`agents/deliberator/context_pm.py`, new `agents/deliberator/context_values.py`,
new `agents/deliberator/context_market.py`, `tests/test_veto_context.py`,
new `tests/test_veto_context_value_labels.py`, `tests/veto_context_gate_fixtures.py`,
`orchestration/tests/test_veto_stage.py`, `agents/portfolio_manager/tests/test_sector_cap.py`,
new `agents/portfolio_manager/tests/test_sector_evidence_labels.py`, `docs/design-log.md`,
`docs/STATE.md`, `pyproject.toml`, `uv.lock`.

**Design decisions:** recorded as [DL-113](../design-log.md): producer-owned rendered values put
unit/scope in the key; open-name producer/vendor dictionaries render with an explicit
`source-owned-units-scope-unknown{...}` boundary; S177 is labels only and does not seed
`SectorBook._deployed` from held positions. Rejected: prompt-only explanation, behaviour change in
this sprint, renderer-side unit inference for source-owned dictionaries, and dropping the evidence.

**Audit table verdicts:**

| Site | Verdict |
| --- | --- |
| `_gate_line` `detail=` free text | **fixed.** PM-produced detail keys now name shares, USD, portfolio scope, and batch scope; `deployed` is now `deployed_this_batch_usd`. Generic gate `value`/`threshold` render with gate-specific labels such as `value_batch_sector_ratio`. |
| `_quant_metrics` | **fixed at this site by boundary.** Rendered as `source-owned-units-scope-unknown{...}`. `sentiment_*_words` was already fixed by DL-112; `atr_pct` is source-owned and tunable-period-sensitive, so S177 does not rename it at the deliberator render site. |
| `_dict(market.fundamentals[t])` | **fixed.** Vendor/free-form fundamentals render under the source-owned unknown-units boundary. |
| `_dict(candidate.metrics)` | **fixed.** Scanner metric maps render under the source-owned unknown-units boundary. |
| `_dict(verdict.features)` | **fixed.** Filter feature maps render under the source-owned unknown-units boundary. |
| `market.quality.requested/returned` | **fixed.** Now `requested_tickers` / `returned_tickers`; stale/anomalous fields already named tickers. |
| `Provider sentiment` vs `sentiment_score` | **fixed.** Provider value is `provider_sentiment_score`; analyst value is `analyst_sentiment_score`. |
| `_pct` vs `_num` | **fixed for current rendered fields.** Shared `percent()` / `number()` helpers sit in `context_values.py`, and existing owned labels now say score/pct where relevant. |
| `est_price={amount} {currency}` | **fixed.** PM order renders `est_price_usd=...`; PM gate details render `est_price_usd`, `position_value_usd`, and `portfolio_value_usd`. |
| `_PORTFOLIO_BATCH_BOUNDARY` | **correct as-is and extended.** The portfolio/batch absence boundary remains, and a separate source-owned metric dictionary boundary was added. |

**Guards planted:**

- Producer detail guard: changed `deployed_this_batch_usd` back to `deployed`; `uv run pytest
  agents/portfolio_manager/tests/test_sector_evidence_labels.py::test_sector_deployment_detail_names_batch_scope_and_unit --no-cov`
  failed on the missing `deployed_this_batch_usd=0.00`; restored and the test passed.
- Source-owned dictionary boundary guard: changed `source-owned-units-scope-unknown{...}` back to
  plain `{...}`; `uv run pytest
  tests/test_veto_context_value_labels.py::test_full_context_names_available_value_units_and_boundaries --no-cov`
  failed on the missing quant-metric boundary; restored and the test passed.
- Gate value label guard: changed `max_sector_pct` labels back to generic `value`/`threshold`;
  `uv run pytest tests/test_veto_context.py::test_context_renders_failed_gate_outcomes_plainly
  --no-cov` failed on the missing `value_batch_sector_ratio` / `threshold_sector_ratio`; restored
  and the test passed.

**`make ci`:** final redirected run `C:\Users\yury_\AppData\Local\Temp\s177-make-ci.log`, exit
code `0`; `2304 passed, 4 skipped`, `100.00 %` coverage; `pip-audit` found no known
vulnerabilities; detect-secrets and untracked-secret scan passed. Earlier full-gate attempts failed
first on ruff-format wrapping, then on two stale orchestration prompt assertions; both were fixed
before the final green run.

**Behaviour question filed as:** [DL-113](../design-log.md), labels-only decision: separately
decide whether `max_sector_pct` should include held portfolio sector dollars instead of only prior
approvals in the current PM run.
