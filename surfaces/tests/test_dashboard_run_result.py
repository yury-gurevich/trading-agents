"""Run-result rendering tests: an unproven run never reads as passed.

Agent: surfaces
Role: pin the verdict wording in the static assets and the resume-button styling.
External I/O: reads committed static assets only.
"""

from __future__ import annotations

import re
from pathlib import Path

_STATIC = Path(__file__).parents[1] / "dashboard" / "static"


def _asset(name: str) -> str:
    return (_STATIC / name).read_text(encoding="utf-8")


def test_an_unproven_run_reads_awaiting_fills_not_passed() -> None:
    """UNPROVEN keeps passed=true (DL-59: not a fault) yet must never say "passed"."""
    app_js = _asset("app.js")

    assert 'var unproven = verdict === "UNPROVEN";' in app_js
    assert 'unproven ? "◷ AWAITING FILLS" :' in app_js
    assert 'unproven ? "awaiting fills" :' in app_js
    assert 'pill.className = "pill " + (unproven ? "wait"' in app_js
    assert 'dot.className = "dot " + (unproven ? "warn"' in app_js
    assert app_js.index("} else if (unproven) {") < app_js.index(
        "} else if (v.passed) {"
    )
    css = _asset("app.css")
    assert ".pill.wait {" in css
    assert ".gatecard.wait {" in css


def test_resume_buttons_are_styled_not_the_browser_default() -> None:
    rule = re.search(r"\.resume-action \{([^}]*)\}", _asset("chat.css"))

    assert rule is not None
    for declaration in ("background:", "border:", "color:", "font:"):
        assert declaration in rule.group(1)


def test_every_changed_asset_is_cache_busted() -> None:
    index = _asset("index.html")

    for asset in ("/app.js?v=", "/app.css?v=", "/chat.css?v="):
        assert asset in index
