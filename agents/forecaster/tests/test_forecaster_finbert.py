"""FinBERT adapter tests — lazy import isolated; no torch needed.

Agent: forecaster
Role: verify construction failure and label alignment with a fake transformers.
External I/O: none (importlib is monkeypatched).
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest

from agents.forecaster.domain.sentiment import NEUTRAL
from agents.forecaster.finbert import ConfigurationError, FinBERTModel


def test_finbert_requires_transformers(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(_name: str) -> object:
        raise ModuleNotFoundError("transformers")

    monkeypatch.setattr(importlib, "import_module", missing)
    with pytest.raises(ConfigurationError, match="not installed"):
        FinBERTModel()


def test_finbert_scores_and_aligns_each_headline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_pipeline(task: str, model: str) -> object:
        def run(headlines: list[str]) -> list[dict[str, object]]:
            return [{"label": "positive", "score": 0.8} for _ in headlines]

        return run

    fake_transformers = SimpleNamespace(pipeline=fake_pipeline)
    monkeypatch.setattr(importlib, "import_module", lambda _name: fake_transformers)
    model = FinBERTModel(model_ref="ProsusAI/finbert")
    aligned = NEUTRAL + NEUTRAL * 0.8
    assert model.score_headlines(("h1", "h2")) == (aligned, aligned)
