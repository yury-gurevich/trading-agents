"""FinBERT-backed sentiment model (heavy ML, optional, lazily imported).

Agent: forecaster
Role: real per-headline sentiment via transformers behind the SentimentModel port.
External I/O: loads a local FinBERT model at a pinned Hub revision (the optional
              ``forecaster`` dependency group); imported lazily so the unit gate
              never pulls in torch.
"""

from __future__ import annotations

import importlib

from agents.forecaster.domain.sentiment import align_label

#: The 2023-05-23 revision EXP-024 measured; the Hub's 2026-10-12 commits changed the
#: card and the weight files, so an unpinned load could change the scorer unseen.
# pragma: allowlist nextline secret
FINBERT_REVISION = "4556d13015211d73dccd3fdd39d39232506f3e43"


class ConfigurationError(RuntimeError):
    """Raised when the FinBERT model cannot be constructed."""


class FinBERTModel:
    """A transformers FinBERT sentiment pipeline behind the model port."""

    def __init__(
        self, *, model_ref: str = "ProsusAI/finbert", revision: str = FINBERT_REVISION
    ) -> None:
        """Build the pinned FinBERT pipeline, failing early if absent."""
        try:
            transformers = importlib.import_module("transformers")
        except ModuleNotFoundError as exc:
            raise ConfigurationError("transformers is not installed") from exc
        self._pipeline = transformers.pipeline(
            "sentiment-analysis", model=model_ref, revision=revision
        )

    def score_headlines(self, headlines: tuple[str, ...]) -> tuple[float, ...]:
        """Run FinBERT over each headline and align each result to a 0-1 score."""
        results = self._pipeline(list(headlines))
        return tuple(
            align_label(str(item["label"]), float(item["score"])) for item in results
        )
