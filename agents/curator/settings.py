"""Curator agent settings and dataset-assembly tunables.

Agent: curator
Role: own defaults for corpus selection, minimum dataset size, and example schema ref.
External I/O: process environment and the .env file.
"""

from __future__ import annotations

from pydantic_settings import SettingsConfigDict

from kernel import AgentSettings, tunable


class CuratorSettings(AgentSettings):
    """Settings for out-of-band dataset assembly."""

    model_config = SettingsConfigDict(env_prefix="CURATOR_", frozen=True)

    max_examples: int = tunable(
        5000,
        why="Cap a single dataset build so out-of-band work never starves trading.",
        ge=1,
        le=100_000,
        unit="examples",
    )
    min_examples_for_split: int = tunable(
        3,
        why="Below this, a 3-way split cannot fill each split; build is degraded.",
        ge=3,
        le=1000,
        unit="examples",
    )
    schema_ref: str = "curator.training_example.v1"
    min_train_examples: int = tunable(
        2,
        why="Below this the train split cannot establish a majority class; "
        "training degrades.",
        ge=1,
        le=10_000,
        unit="examples",
    )
    predictor_strategy: str = "majority_class"  # identity, not a knob
