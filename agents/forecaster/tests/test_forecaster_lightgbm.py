"""LightGBM adapter tests — lazy import isolated; the gate never loads lightgbm.

Agent: forecaster
Role: verify construction fails clearly when lightgbm is absent (the real booster
      load + inference are integration-only, # pragma: no cover).
External I/O: none (importlib is monkeypatched).
"""

from __future__ import annotations

import importlib

import pytest

from agents.forecaster.lightgbm_model import ConfigurationError, LightGBMModel


def test_lightgbm_model_requires_lightgbm(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(_name: str) -> object:
        raise ModuleNotFoundError("lightgbm")

    monkeypatch.setattr(importlib, "import_module", missing)
    with pytest.raises(ConfigurationError, match="not installed"):
        LightGBMModel(model_path="missing.txt")
