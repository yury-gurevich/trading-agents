"""GitHub tree-comparison tests for deploy currency.

Agent: surfaces
Role: prove only runtime file differences make a rebuilt main read "behind".
External I/O: none; GitHub reads are injected fakes.
"""

from __future__ import annotations

import json
from base64 import b64encode
from hashlib import sha256
from typing import TYPE_CHECKING

import pytest

from surfaces.dashboard.github_builds import GitHubReadError
from surfaces.tests.test_github_builds import _reader, _Response

if TYPE_CHECKING:
    from urllib.request import Request

_PYPROJECT = '[project]\nname = "trading-agents"\nversion = "{}"\n'
_LOCK = '[[package]]\nname = "trading-agents"\nversion = "{}"\n\n{}'
_HTTPX = '[[package]]\nname = "httpx"\nversion = "{}"\n'


class _GitHub:
    """Serve two commits' recursive trees and the blobs they point at."""

    def __init__(self, base: dict[str, str], head: dict[str, str]) -> None:
        self.trees = {"base": base, "head": head}
        self.blobs = {
            _blob(text): text for tree in (base, head) for text in tree.values()
        }
        self.truncated = False
        self.encoding = "base64"
        self.content: str | None = None
        self.urls: list[str] = []

    def __call__(self, request: Request, *, timeout: float) -> _Response:
        assert timeout == 3.0
        url = request.full_url
        self.urls.append(url)
        payload: dict[str, object]
        if "/git/trees/" in url:
            commit = url.split("/git/trees/")[1].removesuffix("?recursive=1")
            entries: list[object] = [
                {"path": path, "type": "blob", "sha": _blob(text)}
                for path, text in self.trees[commit].items()
            ]
            entries += [{"path": "kernel", "type": "tree", "sha": "t"}, "not-an-entry"]
            payload = {"truncated": self.truncated, "tree": entries}
        else:
            text = self.blobs[url.rsplit("/", 1)[1]]
            content = self.content or b64encode(text.encode()).decode()
            payload = {"encoding": self.encoding, "content": content}
        return _Response(json.dumps(payload).encode())


def _blob(text: str) -> str:
    return sha256(text.encode()).hexdigest()


def _commit(version: str, changed: dict[str, str] | None = None) -> dict[str, str]:
    files = {
        "kernel/graph.py": "graph v1",
        "agents/analyst/laws/laws.md": "law v1",
        "agents/analyst/tests/test_rules.py": "test v1",
        "surfaces/dashboard/app.py": "app v1",
        "scripts/check_module_size.py": "gate v1",
        "docs/STATE.md": "state v1",
        "pyproject.toml": _PYPROJECT.format(version),
        "uv.lock": _LOCK.format(version, _HTTPX.format("0.28.1")),
    }
    return files | (changed or {})


def test_docs_tests_gates_and_a_version_bump_change_nothing_that_runs() -> None:
    """The shape main had on 2026-09-23: laws, gates and the version moved."""
    head = _commit(
        "0.109.2",
        {
            "agents/analyst/laws/laws.md": "law v2",
            "agents/analyst/tests/test_rules.py": "test v2",
            "surfaces/dashboard/app.py": "app v2",
            "scripts/check_module_size.py": "gate v2",
            "docs/STATE.md": "state v2",
        },
    )
    github = _GitHub(_commit("0.108.0"), head)

    assert _reader(github).runtime_changes("base", "head") == ()
    assert "https://api.github.com/repos/owner/repo/git/trees/base?recursive=1" in (
        github.urls
    )


def test_code_dependency_and_file_set_changes_are_runtime_changes() -> None:
    base = _commit("0.108.0", {"agents/analyst/old_rule.py": "old"})
    head = _commit(
        "0.109.0",
        {
            "kernel/graph.py": "graph v2",
            "uv.lock": _LOCK.format("0.109.0", _HTTPX.format("0.28.2")),
            "agents/analyst/new_rule.py": "new",
        },
    )
    del head["pyproject.toml"]

    assert _reader(_GitHub(base, head)).runtime_changes("base", "head") == (
        "agents/analyst/new_rule.py",
        "agents/analyst/old_rule.py",
        "kernel/graph.py",
        "pyproject.toml",
        "uv.lock",
    )


def test_a_comparison_is_read_once_because_commits_are_immutable() -> None:
    github = _GitHub(_commit("0.108.0"), _commit("0.109.0"))
    reader = _reader(github)

    first = reader.runtime_changes("base", "head")
    reads = len(github.urls)
    second = reader.runtime_changes("base", "head")

    assert first == second == ()
    assert len(github.urls) == reads


@pytest.mark.parametrize("fault", ["truncated", "encoding", "padding", "undecodable"])
def test_an_incomplete_read_raises_rather_than_guessing(fault: str) -> None:
    github = _GitHub(_commit("0.108.0"), _commit("0.109.0"))
    github.truncated = fault == "truncated"
    github.encoding = "utf-8" if fault == "encoding" else "base64"
    github.content = {"padding": "abc", "undecodable": "//4="}.get(fault)

    with pytest.raises(GitHubReadError, match="incomplete"):
        _reader(github).runtime_changes("base", "head")
