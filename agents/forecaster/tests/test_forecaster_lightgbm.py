"""LightGBM adapter tests — lazy import isolated; the gate never loads lightgbm.

Agent: forecaster
Role: verify construction fails clearly when lightgbm is absent (the real booster
      load + inference are integration-only, # pragma: no cover).
External I/O: none (importlib is monkeypatched).
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest

from agents.forecaster.lightgbm_model import ConfigurationError, LightGBMModel
from agents.forecaster.settings import ForecasterSettings


def test_lightgbm_model_requires_lightgbm(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(_name: str) -> object:
        raise ModuleNotFoundError("lightgbm")

    monkeypatch.setattr(importlib, "import_module", missing)
    with pytest.raises(ConfigurationError, match="not installed"):
        LightGBMModel(model_path="missing.txt")


def test_lightgbm_ref_names_the_algorithm_it_loads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FORE-IDN-01: the adapter names the algorithm and loads the requested file."""
    loaded: list[str] = []

    class Booster:
        def __init__(self, *, model_file: str) -> None:
            loaded.append(model_file)

    module = SimpleNamespace(Booster=Booster)
    monkeypatch.setattr(importlib, "import_module", lambda _name: module)
    model = LightGBMModel(model_path="m.txt")
    assert loaded == ["m.txt"]
    assert model.ref == "lightgbm-gbdt"
    assert model.ref == ForecasterSettings().return_model_ref
