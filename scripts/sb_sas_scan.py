"""AST scanning helpers for the Service Bus SAS planner.

Agent: tooling
Role: collect literal Service Bus topics and request envelopes from source text.
External I/O: none; callers provide source text.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SourceText:
    """A source path and its text, for pure AST planning tests."""

    path: str
    text: str


@dataclass(frozen=True)
class TopicScan:
    """Literal topic actions and AgentMessage sender/recipient pairs."""

    topic_events: tuple[tuple[str, str], ...]
    agent_messages: tuple[tuple[str, str], ...]


def source_paths(root: Path) -> tuple[Path, ...]:
    """Return production source files that can own Service Bus topics."""
    paths: list[Path] = []
    for dirname in ("agents", "orchestration"):
        paths.extend((root / dirname).rglob("*.py"))
    return tuple(path for path in sorted(paths) if "tests" not in path.parts)


def owner_for_path(raw: str) -> str | None:
    """Return the fleet target that owns a source path, if one is inferable."""
    parts = Path(raw).parts
    if not parts:
        return None
    if parts[0] == "agents" and len(parts) > 1:
        return parts[1]
    if parts[0] == "orchestration":
        return "dispatcher"
    return None


def scan_source(source: SourceText) -> TopicScan:
    """Collect literal topic actions and request envelopes from one file."""
    visitor = _TopicVisitor()
    visitor.visit(ast.parse(source.text, filename=source.path))
    return TopicScan(
        tuple(visitor.topic_events),
        tuple(visitor.agent_messages),
    )


class _TopicVisitor(ast.NodeVisitor):
    """Collect literal topic actions and request envelopes from source AST."""

    def __init__(self) -> None:
        self.topic_events: list[tuple[str, str]] = []
        self.agent_messages: list[tuple[str, str]] = []

    def visit_Call(self, node: ast.Call) -> None:
        name = _call_name(node.func)
        if name == "subscribe":
            self._topic_event(node, "Listen")
        elif name == "publish":
            self._topic_event(node, "Send")
        elif name == "claim_check_write":
            topic = _kw_str(node, "topic")
            if topic is not None:
                self.topic_events.append((topic, "Send"))
        elif name == "AgentMessage":
            sender = _kw_str(node, "sender")
            recipient = _kw_str(node, "recipient")
            if sender is not None and recipient is not None:
                self.agent_messages.append((sender, recipient))
        self.generic_visit(node)

    def _topic_event(self, node: ast.Call, right: str) -> None:
        topic = _arg_str(node, 0)
        if topic is not None:
            self.topic_events.append((topic, right))


def _call_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _arg_str(node: ast.Call, index: int) -> str | None:
    if len(node.args) <= index:
        return None
    value = node.args[index]
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return value.value
    return None


def _kw_str(node: ast.Call, name: str) -> str | None:
    for keyword in node.keywords:
        if keyword.arg == name and isinstance(keyword.value, ast.Constant):
            value = keyword.value.value
            return value if isinstance(value, str) else None
    return None
