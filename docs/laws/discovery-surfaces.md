# Discovery-surface register — what each agent is free to discover (DL-19)

**What this is.** The cage audit ([cage-audit.md](cage-audit.md)) proved the laws are not a cage — but it
also found the real DL-19 gap (F2): the **discovery surfaces are implicit.** The laws name the *walls*
(NEV), the *capabilities* (CAP), and the *dials* (`tunable`), but no agent names **the space it owns and
may creatively search.** This register names the rooms, so the etalon's *creative space* is legible —
"laws define a space, not a solution" made concrete.

It is the **legible map** of the discovery surfaces. Promoting a per-agent *"Discovery surface"* section
into the **LOCKED `_TEMPLATE.md`** (so each charter carries its own) is the deferred next law-cycle step;
this register is its design substrate and informs it (notably the discoverer-vs-executor distinction below).

## How to read each surface

- **Owns (what to find)** — the space the agent creatively searches; the *solution* belongs to the agent.
- **Walls (where it may not go)** — the bounding prohibitions; the *space* belongs to the law.
- **Search** — *dials* (the `tunable` axis, available now) → *re-composition* (DL-19's extension of LAW-01:
  search the lawful space for a better **form**, not just better dial values — **no mechanism yet**, gated
  behind the CI-6 optimiser + the DL-20 discovery discipline).
- **Admitting gate** — the operator/eval gate that accepts a discovery as *good* (the law owns the gate,
  not the answer).

## Discoverers — agents that own a solution space

| Agent | Owns (what to find) | Walls (where it may not go) | Search: dials → re-composition | Admitting gate |
| --- | --- | --- | --- | --- |
| **scanner** | which names to surface and their ranking **order**, within a technical liquidity/momentum screen | SCAN-NEV-02 (no fundamental/sentiment scoring), NEV-05 (no universe mutation), NEV-04 (own labels only) | `min_relative_strength`, `min_price`, `min_average_volume`, `max_beta`, `candidate_cap`, `lookback_days`, `earnings_exclusion_days` → new technical ranking features/combinations | downstream analyst acceptance + run metrics |
| **analyst** | **how to score & weight** technical + fundamental + relative-strength signals into a `confidence` | ANLZ-NEV-01 (no sizing), NEV-03 (no override of the regime gate), NEV-05 (no promoting a shadow sentiment scorer) | `technical_weight`, `fundamental_weight`, `sentiment_weight`, `relative_strength_weight`, `confidence_floor`/`span`, `rs_window`, `signal_diversity_slack`, `max_top_signals` → new signal pillars / scoring forms | stage gate (evidence-based promotion) |
| **forecaster** | the **shadow model + features** that predict returns/sentiment | FORE-NEV-01 (shadow-only), NEV-02 (no gate/veto/block), NEV-03 (no self-promotion) | horizons, `volatility_window`, `momentum_window`, `return_squash_scale`, `system_prompt` → model family & feature set | curator promotion gate; `system_prompt` by the **deliberation eval (DL-24 firewall)** |
| **researcher** | which **parameter changes to propose**, and the evidence that frames them | RES-NEV-01 (never applies a change), NEV-03 (no forbidden combos), NEV-02 (evidence-window floor) | `min_sample_runs`, `min_evidence_window_days`, `max_changes_per_proposal`, confidence water-marks → new proposal hypotheses | the operator approval / stage gate |
| **curator** | **dataset composition** + when/what to train, and the promotion bar | CUR-NEV-01 (no live-decision influence), NEV-02 (promotion gate before live) | `max_examples`, `min_examples_for_split`, `min_train_examples`, `min_promotion_accuracy`, `min_promotion_sample_size` → dataset-assembly strategy & model choice | its own `min_promotion_*` gate |
| **operator** | how to map **NL operator intent → policy/data-path actions** + explanations | OPR-NEV-01 (within policy/data path), NEV-02 (no gate bypass), NEV-05 (not a free-form advisor) | `model`, `max_tokens`, `explain_max_evidence_nodes`, `system_prompt` → intent schema / prompt | `system_prompt` & `model` by the **deliberation eval (DL-24 firewall)** |

## Faithful executors & integrity-keepers — no surface, by design

Per the cage audit's role-relative test (DL-26), these agents are **deterministic by mandate** — they have
no discovery surface and that is *correct scoping*, not a cage:

**provider** (fetch data faithfully) · **execution** (submit the `OrderIntent` exactly) · **monitor**
(apply stops/exits faithfully) · **reporter** (report faithfully) · **supervisor** (route per the
capability matrix) · **master** (bootstrap + least-privilege grant). The PM is mixed: its **sizing
mechanics are deterministic**, but the **risk envelope** (`max_position_pct`, `max_sector_pct`,
`max_names_per_sector`, `min_reward_risk_ratio`, …) is a tunable space the experimentation process searches.

## Status

This register satisfies DL-19 F2 at the **legibility** layer — every discoverer's room is now named. The
two open increments stay sequenced: (a) promote a *"Discovery surface"* section into the LOCKED template so
each charter carries its own (a deliberate law cycle); (b) give **re-composition** a mechanism (CI-6
optimiser + DL-20). The *dial* axis already exists; the *form* axis does not yet.
