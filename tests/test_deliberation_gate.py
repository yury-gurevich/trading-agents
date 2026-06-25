"""Deliberation gate tests — regression check against a frozen golden baseline.

Agent: kernel
Role: verify passing_names + check_baseline (regressed / gained / passed) — the
      DL-24 model-swap gate logic — deterministically.
External I/O: none.
"""

from __future__ import annotations

from kernel import (
    BaselineCheck,
    EvalScore,
    check_baseline,
    check_robust,
    pass_fractions,
    passing_names,
    robust_passing,
)


def _score(name: str, *, passed: bool) -> EvalScore:
    return EvalScore(name, flaw_caught=passed, verdict_aligned=passed, passed=passed)


def test_passing_names_keeps_only_passed() -> None:
    scores = (_score("a", passed=True), _score("b", passed=False))
    assert passing_names(scores) == frozenset({"a"})


def test_no_regression_passes() -> None:
    candidate = (_score("a", passed=True), _score("b", passed=True))
    check = check_baseline(candidate, frozenset({"a", "b"}))
    assert check.passed
    assert check.regressed == ()


def test_regression_trips_the_gate() -> None:
    candidate = (_score("a", passed=True), _score("b", passed=False))
    check = check_baseline(candidate, frozenset({"a", "b"}))
    assert not check.passed
    assert check.regressed == ("b",)


def test_gain_is_informational_not_a_trip() -> None:
    candidate = (_score("a", passed=True), _score("b", passed=True))
    check = check_baseline(candidate, frozenset({"a"}))
    assert check.passed
    assert check.gained == ("b",)
    assert isinstance(check, BaselineCheck)


def test_pass_fractions_counts_across_runs() -> None:
    runs = (
        (_score("a", passed=True), _score("b", passed=True)),
        (_score("a", passed=True), _score("b", passed=False)),
    )
    fractions = pass_fractions(runs)
    assert fractions["a"] == 1.0
    assert fractions["b"] == 0.5


def test_pass_fractions_empty_is_empty() -> None:
    assert pass_fractions(()) == {}


def test_robust_passing_threshold_excludes_flaky() -> None:
    runs = (
        (_score("a", passed=True), _score("b", passed=True)),
        (_score("a", passed=True), _score("b", passed=False)),
        (_score("a", passed=True), _score("b", passed=False)),
    )
    assert robust_passing(runs, threshold=1.0) == frozenset({"a"})
    assert robust_passing(runs, threshold=0.3) == frozenset({"a", "b"})


def test_check_robust_trips_on_persistent_regression() -> None:
    runs = (
        (_score("a", passed=True), _score("b", passed=False)),
        (_score("a", passed=True), _score("b", passed=False)),
    )
    check = check_robust(runs, frozenset({"a", "b"}), threshold=0.5)
    assert not check.passed
    assert check.regressed == ("b",)


def test_check_robust_tolerates_one_off_noise() -> None:
    runs = (
        (_score("a", passed=True), _score("b", passed=True)),
        (_score("a", passed=True), _score("b", passed=False)),
        (_score("a", passed=True), _score("b", passed=True)),
    )
    check = check_robust(runs, frozenset({"a", "b"}), threshold=0.5)
    assert check.passed
