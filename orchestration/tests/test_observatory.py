"""Observatory substrate tests — invariant evaluation + render.

Agent: orchestration
Role: verify Check/_holds (required, floor, ceiling, oneof, missing), breaches, and
      render (reached, unreached, breach vs clean) deterministically.
External I/O: none.
"""

from __future__ import annotations

from orchestration.observatory import (
    Breach,
    Check,
    StageView,
    accept,
    breaches,
    render,
)


def _stage(
    observed: dict[str, object],
    checks: tuple[Check, ...],
    outputs: tuple[str, ...] = (),
) -> StageView:
    return StageView(
        "s", "trig", observed, reached=True, checks=checks, outputs=outputs
    )


def test_required_present_and_missing() -> None:
    ok = breaches(_stage({"a": 1}, (Check("a", "required"),)))
    missing = breaches(_stage({}, (Check("a", "required"),)))
    assert ok == ()
    assert missing == (Breach("s", "a", "MISSING"),)


def test_floor_pass_and_fail() -> None:
    assert breaches(_stage({"n": 5}, (Check("n", "floor", 1.0),))) == ()
    fail = breaches(_stage({"n": 0}, (Check("n", "floor", 1.0),)))
    assert fail == (Breach("s", "n", "0 < floor 1.0"),)


def test_ceiling_pass_and_fail() -> None:
    assert breaches(_stage({"n": 2}, (Check("n", "ceiling", 10.0),))) == ()
    fail = breaches(_stage({"n": 11}, (Check("n", "ceiling", 10.0),)))
    assert fail == (Breach("s", "n", "11 > ceiling 10.0"),)


def test_oneof_pass_and_fail() -> None:
    checks = (Check("r", "oneof", ("risk_on", "neutral")),)
    assert breaches(_stage({"r": "neutral"}, checks)) == ()
    fail = breaches(_stage({"r": "boom"}, checks))
    assert fail == (Breach("s", "r", "boom not in ('risk_on', 'neutral')"),)


def test_floor_on_missing_value_is_a_breach() -> None:
    fail = breaches(_stage({}, (Check("n", "floor", 1.0),)))
    assert fail == (Breach("s", "n", "MISSING"),)


def test_unreached_stage_is_one_breach() -> None:
    stage = StageView("prov", "RunRequest", {}, reached=False)
    assert breaches(stage) == (Breach("prov", "*stage*", "NOT REACHED"),)


def test_render_clean_run() -> None:
    stages = (
        _stage(
            {"returned": 99},
            (Check("returned", "floor", 1.0),),
            ("tickers   AAPL MSFT", "quality   ok  returned=99/99"),
        ),
    )
    out = render(stages)
    assert "[s]  <- trig" in out
    assert "  tickers   AAPL MSFT" in out
    assert "  quality   ok  returned=99/99" in out
    assert "OK - all invariants hold" in out
    assert "WARN" not in out


def test_render_flags_breach_and_unreached() -> None:
    stages = (
        _stage({"returned": 0}, (Check("returned", "floor", 1.0),)),
        StageView("pm", "x", {}, reached=False),
    )
    out = render(stages)
    assert "WARN  returned: 0 < floor 1.0" in out
    assert "[pm]  <- x   ... NOT REACHED" in out
    assert "2 WARN - inspect above" in out


def test_accept_passes_when_clean_with_passing_cross_check() -> None:
    stages = (_stage({"out": 1}, (Check("out", "floor", 1.0),)),)
    result = accept(stages, (lambda observed: None,))
    assert result.passed
    assert result.breaches == ()


def test_accept_fails_on_a_per_stage_breach() -> None:
    stages = (_stage({"out": 0}, (Check("out", "floor", 1.0),)),)
    result = accept(stages, ())
    assert not result.passed


def test_accept_fails_on_a_cross_stage_breach() -> None:
    stages = (_stage({"out": 5}, ()),)

    def cross(observed: dict[str, dict[str, object]]) -> Breach | None:
        return Breach("s", "out", "boundary") if observed["s"]["out"] != 1 else None

    result = accept(stages, (cross,))
    assert not result.passed
    assert result.breaches == (Breach("s", "out", "boundary"),)
