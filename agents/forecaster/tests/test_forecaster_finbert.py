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
from agents.forecaster.finbert import (
    FINBERT_REVISION,
    ConfigurationError,
    FinBERTModel,
)


def _fake_transformers(calls: list[dict[str, str]]) -> SimpleNamespace:
    def fake_pipeline(task: str, model: str, revision: str) -> object:
        calls.append({"task": task, "model": model, "revision": revision})

        def run(headlines: list[str]) -> list[dict[str, object]]:
            return [{"label": "positive", "score": 0.8} for _ in headlines]

        return run

    return SimpleNamespace(pipeline=fake_pipeline)


def test_finbert_requires_transformers(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(_name: str) -> object:
        raise ModuleNotFoundError("transformers")

    monkeypatch.setattr(importlib, "import_module", missing)
    with pytest.raises(ConfigurationError, match="not installed"):
        FinBERTModel()


def test_finbert_scores_and_aligns_each_headline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, str]] = []
    fake = _fake_transformers(calls)
    monkeypatch.setattr(importlib, "import_module", lambda _name: fake)
    model = FinBERTModel(model_ref="ProsusAI/finbert")
    aligned = NEUTRAL + NEUTRAL * 0.8
    assert model.score_headlines(("h1", "h2")) == (aligned, aligned)


def test_finbert_loads_the_revision_exp024_measured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The default load names the full 2023 commit, never the Hub's moving head."""
    calls: list[dict[str, str]] = []
    fake = _fake_transformers(calls)
    monkeypatch.setattr(importlib, "import_module", lambda _name: fake)
    FinBERTModel()
    FinBERTModel(revision="main")
    # pragma: allowlist nextline secret
    assert FINBERT_REVISION == "4556d13015211d73dccd3fdd39d39232506f3e43"
    assert calls == [
        {
            "task": "sentiment-analysis",
            "model": "ProsusAI/finbert",
            "revision": FINBERT_REVISION,
        },
        {"task": "sentiment-analysis", "model": "ProsusAI/finbert", "revision": "main"},
    ]
