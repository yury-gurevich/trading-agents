"""Deliberation gate tests — regression check against a frozen golden baseline.

Agent: kernel
Role: verify passing_names + check_baseline (regressed / gained / passed) — the
      DL-24 model-swap gate logic — deterministically.
External I/O: none.
"""

from __future__ import annotations

from kernel import BaselineCheck, EvalScore, check_baseline, passing_names


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
