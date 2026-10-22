"""S289-A9 through A12: fixed models and their ranked ensemble.

Agent: tooling
Role: prove training algebra and the lazy native LightGBM call without installing it.
External I/O: none.
"""

from __future__ import annotations

import sys
from types import ModuleType

import numpy as np
from scripts.exp015_models import fit, lightgbm_trainer
from scripts.exp015_ranks import group_ranks, ranked_features, session_ic
from tests.exp015_fixtures import SignalBooster, planted_panel, trainer


def test_a9_composite_signs():
    """S289-A9: a positive signal and its negative mirror yield equal composites."""
    panel = planted_panel()
    x = ranked_features(panel)[:, :1]
    original = fit(x, panel.excess[:, 1], panel.sessions, trainer)
    mirror = fit(1 - x, panel.excess[:, 1], panel.sessions, trainer)
    np.testing.assert_array_equal(original.signs, [1])
    np.testing.assert_array_equal(mirror.signs, [-1])
    a = original.predict(x, panel.sessions)["composite"]
    b = mirror.predict(1 - x, panel.sessions)["composite"]
    np.testing.assert_allclose(a, b, atol=1e-15)


def test_a10_ridge_closed_form():
    """S289-A10: centred ranked-target normal equation with lambda exactly 1."""
    panel = planted_panel()
    x = ranked_features(panel)
    target = panel.excess[:, 1].copy()
    target[0] = np.nan
    got = fit(x, target, panel.sessions, trainer)
    usable = np.isfinite(target)
    mean = x[usable].mean(axis=0)
    centred = x[usable] - mean
    y = group_ranks(target[usable], panel.sessions[usable])
    np.testing.assert_allclose(got.ridge_mean, mean)
    np.testing.assert_allclose(
        (centred.T @ centred + np.eye(20)) @ got.ridge_beta,
        centred.T @ (y - y.mean()),
        atol=1e-12,
    )


def test_a11_ranked_ensemble():
    """S289-A11: ordered predictions; ensemble averages three ranks, IC above 0.3."""
    panel = planted_panel()
    x = ranked_features(panel)
    fitted = fit(x, panel.excess[:, 1], panel.sessions, trainer)
    got = fitted.predict(x, panel.sessions)
    assert tuple(got) == ("composite", "ridge", "lightgbm", "ensemble")
    expected = np.mean(
        [group_ranks(got[name], panel.sessions) for name in tuple(got)[:3]], axis=0
    )
    np.testing.assert_allclose(got["ensemble"], expected)
    assert min(got["ensemble"]) >= 0
    assert max(got["ensemble"]) <= 1
    assert (
        np.mean(
            list(
                session_ic(got["ensemble"], panel.excess[:, 1], panel.sessions).values()
            )
        )
        > 0.3
    )
    assert len(fitted.importances()) == 20


def test_a12_lightgbm_fixed_settings(monkeypatch):
    """S289-A12: stand-in module observes native Dataset and train with 200 rounds."""
    calls = {}
    module = ModuleType("lightgbm")
    x, y = np.ones((12, 20)), np.arange(12, dtype=float)
    dataset, booster = object(), SignalBooster()

    def make_dataset(data, *, label, params):
        assert data is x
        assert label is y
        assert params == {"verbosity": -1}
        calls["dataset"] = True
        return dataset

    def train(params, data, *, num_boost_round):
        calls["params"], calls["rounds"] = params, num_boost_round
        assert data is dataset
        return booster

    monkeypatch.setattr(module, "Dataset", make_dataset, raising=False)
    monkeypatch.setattr(module, "train", train, raising=False)
    monkeypatch.setitem(sys.modules, "lightgbm", module)
    assert lightgbm_trainer(x, y) is booster
    assert calls == {
        "dataset": True,
        "rounds": 200,
        "params": {
            "objective": "regression",
            "max_depth": 3,
            "learning_rate": 0.05,
            "num_leaves": 31,
            "min_data_in_leaf": 500,
            "feature_fraction": 0.8,
            "seed": 0,
            "deterministic": True,
            "num_threads": 1,
            "force_col_wise": True,
            "verbosity": -1,
        },
    }
