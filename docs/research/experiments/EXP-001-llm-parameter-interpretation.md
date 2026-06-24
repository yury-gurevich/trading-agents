# EXP-001 · Do the LLMs understand our decision parameters? (gpt-5.4 vs gpt-5.5)

**Date:** 2026-06-24 · **Status:** complete · **Feeds:** DSPy role-prompt grounding (DL-21/22)

## Purpose

The Deliberation roles (Defender / Challenger / Judge) argue *about* the system's decision parameters.
**Their debate is only as good as their understanding of those parameters** — a role that misreads a
knob argues from a false model, and a fluent-but-wrong argument is *worse* than none (it is falsely
reassuring). So before trusting the debate, probe: **does the LLM we use actually understand our 86
decision parameters — and where does its understanding diverge from our implementation?** Those
divergences (deltas) are precisely what DSPy must encode into the role context.

## Process

- Extracted all **86 decision-shaping `tunable()` parameters** (analyst, provider, scanner, PM, monitor,
  forecaster) as `agent.name = default`, **withholding our `why` justifications** — so we test the
  model's *own* understanding, not its ability to parrot ours.
- Asked the model, cold, for each parameter: *what it measures + how to read the value + why it matters*,
  with an explicit instruction to say **`UNSURE` + best guess, do not bluff**.
- Ran the identical prompt on **gpt-5.4**, then **gpt-5.5** (controls: same prompt, same params, same
  system role "senior quantitative equity analyst").
- Critiqued both against [`../quant-methods/quant-methods.md`](../quant-methods/quant-methods.md) and the
  source code; classified the deltas.

## Delivery

- Two raw transcripts (session scratchpad): `llm_param_interpretation.txt` (gpt-5.4),
  `llm_param_gpt55.txt` (gpt-5.5).
- The critique + model comparison:
  [`../quant-methods/llm-interpretation-deltas.md`](../quant-methods/llm-interpretation-deltas.md) — the
  three delta classes and the 5.4-vs-5.5 table.
- Decision-log capture: **DL-22**.
- Action taken: switched `OPENAI_MODEL` → **gpt-5.5** in `.env` (local).

## Interpretation

Both models are **competent quants** (~90% correct on general finance), so the debate stands on a solid
base. The errors, classified:

1. **Implementation misreads** (model's textbook ≠ our code): e.g. `max_daily_move_sigma` read as a
   *per-stock* vol filter — it is a **pooled cross-sectional** z-score data gate; `base_*` read as fixed
   — they are **regime-modulated** seeds.
2. **Dangerous assumptions** (assumes guardrails we lack): gpt-5.4 read `max_sector_pct` as controlling
   *correlated* concentration — but we have a **sector cap, not a name-correlation penalty**, and the
   pipeline just opened 4 semis. **gpt-5.5 did NOT make this over-claim** (scoped it to "sector
   concentration control").
3. **Honest `UNSURE`** on the genuinely obscure (Nadaraya-Watson, Alpha158) — low risk.

**Model comparison:** gpt-5.5 > gpt-5.4 — full coverage (5.4 truncated), and it **shrinks the Class-2
risk** (over-claiming). But **neither closes Class-1** (our-system specifics) — that is not a capability
gap, it is a grounding gap no model will guess.

**What it feeds (the DSPy correction targets):** the compiled role context must carry (a) per-parameter
**implementation notes** where our code ≠ textbook (the withheld `why` fields), (b) the **coverage gaps**
([quant-methods Part 2](../quant-methods/quant-methods.md)) as explicit *"the system does NOT do X"*
facts, and (c) **chunked, retrieved** parameter context (don't dump 86 at once — 5.4 truncated). Model
quality buys plausibility + scope discipline; grounding buys our-system fidelity — **DSPy needs both,
and the eval (do upheld decisions outperform?) still gates.**

**Prerequisite for DSPy to act:** an outcome-labelled eval set (decisions with known results), which the
pipeline must first *produce* — the bundle now trades (0.28.01), so that data is starting to exist.
