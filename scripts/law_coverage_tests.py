"""Resolve law-book test citations against live pytest functions.

Agent: tooling
Role: map test-plan citation text to AST docstrings in agent-local tests.
External I/O: filesystem reads of test files.
"""

from __future__ import annotations

import ast
import re
from typing import TYPE_CHECKING

from scripts.law_coverage_model import Citation, Resolution, TestTarget

if TYPE_CHECKING:
    from pathlib import Path

TEST_NAME_RE = re.compile(r"\btest_[A-Za-z0-9_]+\b")
FILE_TEST_RE = re.compile(r"(?P<file>[\w./\\-]+\.py)?::(?P<name>test_[A-Za-z0-9_]+)")
TEXT_CITATION_RE = re.compile(
    r"[\w./\\-]+\.py::test_[A-Za-z0-9_]+|::test_[A-Za-z0-9_]+|\btest_[A-Za-z0-9_]+\b"
)
SKIP_PARTS = frozenset({".git", "mutants"})


class TestResolver:
    """Resolve cited tests under ``agents/<agent>/tests``."""

    def __init__(self, root: Path) -> None:
        self._root = root
        self._cache: dict[str, dict[str, list[TestTarget]]] = {}
        self._files: dict[str, tuple[Path, ...]] = {}

    def resolve(self, agent: str, citation: Citation) -> Resolution:
        """Resolve one citation to live test targets, or describe why it cannot."""
        if citation.file_part is not None:
            return self._resolve_named_file(agent, citation)
        matches = self._test_index(agent).get(citation.test_name, [])
        if not matches:
            return Resolution(citation, missing="test function does not exist")
        if len(matches) > 1:
            return Resolution(
                citation, ambiguous=tuple(target.path for target in matches)
            )
        return Resolution(citation, targets=tuple(matches))

    def _resolve_named_file(self, agent: str, citation: Citation) -> Resolution:
        files = self._matching_files(agent, citation.file_part or "")
        if not files:
            return Resolution(citation, missing="test file does not exist")
        if len(files) > 1:
            return Resolution(citation, ambiguous=files)
        index = self._functions_in_file(files[0])
        matches = index.get(citation.test_name, [])
        if not matches:
            return Resolution(citation, missing="test function does not exist in file")
        if len(matches) > 1:
            return Resolution(
                citation, ambiguous=tuple(target.path for target in matches)
            )
        return Resolution(citation, targets=tuple(matches))

    def _test_index(self, agent: str) -> dict[str, list[TestTarget]]:
        if agent not in self._cache:
            index: dict[str, list[TestTarget]] = {}
            for path in self._agent_test_files(agent):
                for name, targets in self._functions_in_file(path).items():
                    index.setdefault(name, []).extend(targets)
            self._cache[agent] = index
        return self._cache[agent]

    def _matching_files(self, agent: str, file_part: str) -> tuple[Path, ...]:
        cache_key = f"{agent}:{file_part}"
        if cache_key in self._files:
            return self._files[cache_key]
        normalized = file_part.replace("\\", "/").removeprefix("./")
        candidates: list[Path] = []
        direct_paths = [
            self._root / normalized,
            self._agent_test_root(agent) / normalized,
        ]
        for candidate in direct_paths:
            if _usable_test_path(candidate):
                candidates.append(candidate)
        if not candidates:
            for path in self._agent_test_files(agent):
                relative = path.relative_to(self._agent_test_root(agent)).as_posix()
                if relative == normalized or path.name == normalized:
                    candidates.append(path)
        result = tuple(dict.fromkeys(candidates))
        self._files[cache_key] = result
        return result

    def _functions_in_file(self, path: Path) -> dict[str, list[TestTarget]]:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            return {}
        functions: dict[str, list[TestTarget]] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                if not node.name.startswith("test_"):
                    continue
                functions.setdefault(node.name, []).append(
                    TestTarget(path, node.name, ast.get_docstring(node) or "")
                )
        return functions

    def _agent_test_files(self, agent: str) -> tuple[Path, ...]:
        root = self._agent_test_root(agent)
        if not root.is_dir():
            return ()
        return tuple(
            path for path in sorted(root.rglob("*.py")) if _usable_test_path(path)
        )

    def _agent_test_root(self, agent: str) -> Path:
        return self._root / "agents" / agent / "tests"


def extract_citations(text: str) -> tuple[Citation, ...]:
    """Extract supported test citations from a test-plan cell."""
    chunks = re.findall(r"`([^`]+)`", text) or TEXT_CITATION_RE.findall(text)
    citations: list[Citation] = []
    last_file: str | None = None
    for chunk in chunks:
        for token in _split_chunk(chunk):
            citation, last_file = _parse_token(token, last_file)
            if citation is not None:
                citations.append(citation)
    return tuple(citations)


def _split_chunk(chunk: str) -> list[str]:
    return [part.strip() for part in re.split(r"\s*[;,]\s*", chunk) if part.strip()]


def _parse_token(
    token: str, last_file: str | None
) -> tuple[Citation | None, str | None]:
    if token.lower() in {"_tbd_", "tbd", "n/a", "none"}:
        return None, last_file
    match = FILE_TEST_RE.fullmatch(token)
    if match is not None:
        file_part = match.group("file") or last_file
        name = match.group("name")
        raw = f"{file_part}::{name}" if file_part and token.startswith("::") else token
        return Citation(raw=raw, file_part=file_part, test_name=name), file_part
    if TEST_NAME_RE.fullmatch(token):
        return Citation(raw=token, test_name=token), last_file
    return None, last_file


def _usable_test_path(path: Path) -> bool:
    return path.is_file() and not SKIP_PARTS.intersection(path.parts)
