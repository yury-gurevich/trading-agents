"""FinBERT-backed sentiment model (heavy ML, optional, lazily imported).

Agent: forecaster
Role: real per-headline sentiment via transformers behind the SentimentModel port.
External I/O: loads a local FinBERT model (the optional ``forecaster`` dependency
              group); imported lazily so the unit gate never pulls in torch.
"""

from __future__ import annotations

import importlib

from agents.forecaster.domain.sentiment import align_label


class ConfigurationError(RuntimeError):
    """Raised when the FinBERT model cannot be constructed."""


class FinBERTModel:
    """A transformers FinBERT sentiment pipeline behind the model port."""

    def __init__(self, *, model_ref: str = "ProsusAI/finbert") -> None:
        """Build the FinBERT sentiment pipeline, failing early if absent."""
        try:
            transformers = importlib.import_module("transformers")
        except ModuleNotFoundError as exc:
            raise ConfigurationError("transformers is not installed") from exc
        self._pipeline = transformers.pipeline("sentiment-analysis", model=model_ref)

    def score_headlines(self, headlines: tuple[str, ...]) -> tuple[float, ...]:
        """Run FinBERT over each headline and align each result to a 0-1 score."""
        results = self._pipeline(list(headlines))
        return tuple(
            align_label(str(item["label"]), float(item["score"])) for item in results
        )
