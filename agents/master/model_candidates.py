"""The pack's ordered LLM candidates and the agent types that choose among them.

Agent: master
Role: parse and validate the declared vendor, model and effort list (DL-289 P1).
External I/O: reads the declaration file when load_llm_plan is called.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from kernel.llm_factory import KEY_ENV, model_provider

if TYPE_CHECKING:
    from collections.abc import Mapping


@dataclass(frozen=True)
class LlmCandidate:
    """One declared way to run an LLM role: a vendor, a model and an effort."""

    vendor: str
    model: str
    effort: str

    @property
    def label(self) -> str:
        """Name the candidate in records and lines: ``vendor/model/effort``."""
        return f"{self.vendor}/{self.model}/{self.effort}"


@dataclass(frozen=True)
class LlmRole:
    """The configuration keys an agent type reads its candidates from.

    The chosen candidate's vendor, model and effort, and the later candidates that
    also passed, in order, as ``vendor/model/effort`` labels joined by commas
    (DL-289 P3).
    """

    vendor_key: str
    model_key: str
    effort_key: str
    fallbacks_key: str


@dataclass(frozen=True)
class LlmPlan:
    """The ordered candidates and the agent types that run on the first working one."""

    candidates: tuple[LlmCandidate, ...]
    roles: Mapping[str, LlmRole]

    def ordered(self, provider: str) -> tuple[LlmCandidate, ...]:
        """The declared provider's candidates first, each group in declared order."""
        first = tuple(item for item in self.candidates if item.vendor == provider)
        rest = tuple(item for item in self.candidates if item.vendor != provider)
        return first + rest


def parse_llm_plan(text: str) -> LlmPlan:
    """Parse the LLM pack; refuse anything a role could not run on."""
    raw = json.loads(text)
    if not isinstance(raw, dict):
        raise ValueError("LLM declaration must be an object")
    entries = raw.get("candidates")
    if not isinstance(entries, list) or not entries:
        raise ValueError("LLM declaration needs a non-empty candidates list")
    candidates = tuple(_candidate(entry) for entry in entries)
    if len({item.label for item in candidates}) != len(candidates):
        raise ValueError("LLM candidates must not repeat")
    roles = raw.get("roles", {})
    if not isinstance(roles, dict):
        raise ValueError("LLM roles must map agent types to keys")
    return LlmPlan(
        candidates, {str(name): _role(name, keys) for name, keys in roles.items()}
    )


def load_llm_plan(path: str) -> LlmPlan:
    """Load the LLM pack from a JSON file at *path*."""
    return parse_llm_plan(Path(path).read_text(encoding="utf-8"))


def _candidate(entry: object) -> LlmCandidate:
    if not isinstance(entry, dict):
        raise ValueError("an LLM candidate must be an object")
    vendor, model, effort = (_text(entry, key) for key in ("vendor", "model", "effort"))
    if vendor not in KEY_ENV:
        raise ValueError(f"unknown LLM candidate vendor {vendor!r}")
    owner = model_provider(model)
    if owner not in (None, vendor):
        raise ValueError(f"model {model!r} belongs to {owner}, not {vendor}")
    return LlmCandidate(vendor, model, effort)


def _role(name: object, keys: object) -> LlmRole:
    if not isinstance(keys, dict):
        raise ValueError(f"LLM role {name!r} must be an object")
    fields = ("vendor", "model", "effort", "fallbacks")
    return LlmRole(*(_text(keys, key) for key in fields))


def _text(entry: dict[str, object], key: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"LLM declaration field {key!r} must be a non-empty string")
    return value
