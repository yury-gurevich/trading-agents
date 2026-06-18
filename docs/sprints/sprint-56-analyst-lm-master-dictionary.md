# Sprint 56 — Analyst: full Loughran–McDonald master dictionary

**Phase:** P12 (sentiment champion–challenger) — champion deepened.
**Status:** shipped (implemented directly — no coding agent this cycle).
**Version:** `feat` → project `0.4.0 → 0.5.0` (MINOR, HARD RULE).

## Goal

Upgrade the analyst's binding sentiment pillar (the champion) from the ~170-word
curated headline lexicon to the **full Loughran–McDonald master dictionary**, the
"sanctioned upgrade" the module had reserved — without changing the
`score_sentiment` interface or any contract.

## What shipped

- **Vendored the genuine LM master dictionary** as two compact data assets under
  `agents/analyst/domain/data/`:
  - `lm_positive.txt` — 354 words.
  - `lm_negative.txt` — 2 355 words.

  Lowercased, sorted, one word per line. Counts match the published master
  dictionary exactly. Sourced from the `quanteda.sentiment` mirror of
  `Loughran_and_McDonald_2014.cat`; provenance + citation + refresh instructions in
  `agents/analyst/domain/data/README.md`.
- **`sentiment_rules.py`** now loads the two lists via a small `_load_lexicon`
  reader and **unions** them with the prior curated terms (renamed
  `_HEADLINE_POSITIVE` / `_HEADLINE_NEGATIVE`):

  ```python
  _POSITIVE = _load_lexicon("lm_positive.txt") | _HEADLINE_POSITIVE
  _NEGATIVE = _load_lexicon("lm_negative.txt") | _HEADLINE_NEGATIVE
  ```

## Key decision — union, not swap

LM was built for **10-K filings**, so the most common finance-news **headline
verbs are absent from it**: `beat, surge, plunge, rally, jump, tumble, profit,
record, upgrade, rise, fell, drop` (18 verified absent). The input here is news
headlines, so a pure swap would *degrade* the scorer. We therefore **union** the
full LM lists (breadth) with the curated headline terms LM lacks (42 positive +
41 negative net-new). The two sources are **polarity-disjoint** — no curated word
is an LM word of the opposite polarity, and LM's own positive/negative sets are
disjoint — so the union needs **no conflict resolution**. The vendored `.txt`
files stay a faithful copy of LM; the headline terms stay in code.

## Tests

- Existing seven scorer tests pass **unchanged** — every prior "neutral" fixture
  still has zero LM hits, so the union is purely additive (no pinned score moved).
- Added four:
  - `test_lm_only_positive_words_score_positive` — `excellent`, `innovative`.
  - `test_lm_only_negative_words_score_negative` — `fraudulent`, `adverse`.
  - `test_lm_master_dictionary_and_headline_terms_loaded` — sizes ≥ 354 / 2 355
    and representative LM-only + headline-only words present.
  - `test_positive_and_negative_lexicons_are_disjoint` — guards the
    no-conflict-resolution invariant against future LM refreshes.

## Gate

- **No contract change** (analyst CONTRACT 0.1.0).
- The `.txt` assets are exempt from the module size/header guards (Python-only)
  and well under the 500 KB added-file limit.
- 739 tests (was 735; +4), coverage floor 100.00; every module < 200 lines.

## Follow-on

P12's only remaining piece is the **scorecard harness** (compare the three
`SentimentReading`s vs forward returns) — data-runway-gated, not code-gated. Per
the agreed order: harness → P14.
