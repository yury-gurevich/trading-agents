# Curator Agent

**Mission.** Curate the collected provenance graph into clean, labelled, versioned
datasets ready for later LLM training — running out of band, alongside trading,
and never touching the live decision loop.

## Owns

- Data preparation for the graph-derived analysis/training layer: cleaning, labelling,
  example assembly, train/validation/test splitting, and dataset versioning.
- The training corpus and its manifests.

## Boundary — contract: `contracts/curator.py`

- **Consumes:** `build_dataset(DatasetRequest) -> DatasetManifest`,
  `describe_corpus(DatasetRequest) -> Explanation`.
- **Emits:** `dataset_published`.
- **Depends on (read-only):** the provenance graph the other agents produce
  (reached via the reported/graph layer; never imports another agent).

## Data ownership

- **Postgres:** `dataset_manifests`, `dataset_versions`, `training_examples`.
- **Graph:** `Dataset`, `TrainingExample` — derived from operational provenance,
  never overwriting it.

## External I/O (exclusive)

- `dataset_store` — where curated training datasets are written.

## MCP surface

- `build_dataset`, `describe_corpus`.

## Never

- Influence or gate a trading decision.
- Feed a trained model into the live loop without a promotion gate.
- Mutate source provenance written by other agents (read-only over the graph).

> Runs on its own schedule, **in addition to** normal trading processing. It is the
> bridge from "the system records everything" to "the system can learn from what it
> recorded" — kept strictly out of band so data work never perturbs trading.
