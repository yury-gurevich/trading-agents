# Loughran–McDonald sentiment word lists (vendored)

`lm_positive.txt` (354 words) and `lm_negative.txt` (2 355 words) are the **Positive**
and **Negative** categories of the Loughran–McDonald master dictionary, one
lowercased word per line, sorted. They are loaded at import by
`agents/analyst/domain/sentiment_rules.py` and **unioned** with a curated set of
finance-news headline terms that the dictionary omits (it was built for 10-K
filings, so headline verbs such as *beat, surge, plunge, rally, jump, tumble,
profit, record, upgrade* are absent). The two sources are polarity-disjoint.

## Provenance

- Source file: `Loughran_and_McDonald_2014.cat` from the
  [quanteda.sentiment](https://github.com/quanteda/quanteda.sentiment/blob/master/sources/Loughran-McDonald/Loughran_and_McDonald_2014.cat)
  mirror of the master dictionary.
- Canonical home: Software Repository for Accounting and Finance, University of
  Notre Dame — <https://sraf.nd.edu/loughranmcdonald-master-dictionary/>.
- Counts match the published 2014 master dictionary exactly (Negative 2 355,
  Positive 354).

## Citation

Loughran, T. and McDonald, B. (2011), "When Is a Liability Not a Liability?
Textual Analysis, Dictionaries, and 10-Ks." *The Journal of Finance*, 66: 35–65.

The master dictionary is distributed free for research use; this is a single-user,
non-commercial research project.

## Updating

To refresh to a newer master-dictionary release, regenerate both files from the
source (lowercase, dedupe, sort, one word per line, trailing newline). The loader
and the disjointness test in `tests/test_sentiment_rules.py` will catch any
polarity overlap introduced by a new release.
