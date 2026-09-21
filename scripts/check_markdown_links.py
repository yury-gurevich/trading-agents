"""Check tracked Markdown links and GitHub-style fragments.

Agent: tooling
Role: enforce local Markdown link integrity in the offline CI gate.
External I/O: reads tracked files through local git and filesystem paths;
writes reports to stdout.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from shutil import which
from urllib.parse import unquote

_ROOT = Path(__file__).resolve().parents[1]
_FENCE = re.compile(r" {0,3}(`{3,}|~{3,})")
_HEADING = re.compile(r" {0,3}#{1,6}\s+(.+?)\s*#*\s*$")
_LINK = re.compile(
    r"(?P<image>!)?\[(?P<text>[^\]\n]*)\]"
    r"\((?P<href><[^>\n]*>|[^)\s\n]+)(?:\s+['\"][^)]*['\"])?\)"
)
_SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
_PATH_LABEL = re.compile(
    r"(?:\.\.?/)?[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)*\.[A-Za-z0-9_-]+$"
)
_IGNORED_PREFIXES = (
    "node_modules",
    ".venv",
    "mutants",
    "codeql/python-security/reports",
)


def _blank(text: str) -> str:
    return "".join("\n" if char == "\n" else " " for char in text)


def _mask_fences(text: str) -> str:
    fence = ""
    lines: list[str] = []
    for line in text.splitlines(keepends=True):
        match = _FENCE.match(line)
        if fence:
            lines.append(_blank(line))
            if (
                match
                and match.group(1)[0] == fence[0]
                and len(match.group(1)) >= len(fence)
            ):
                fence = ""
        elif match:
            fence = match.group(1)
            lines.append(_blank(line))
        else:
            lines.append(line)
    return "".join(lines)


def _mask_code(text: str) -> str:
    masked = _mask_fences(text)
    result: list[str] = []
    index = 0
    while index < len(masked):
        if masked[index] != "`":
            result.append(masked[index])
            index += 1
            continue
        length = len(masked[index:]) - len(masked[index:].lstrip("`"))
        marker = "`" * length
        end = masked.find(marker, index + length)
        if end == -1:
            result.append(marker)
            index += length
            continue
        result.append(_blank(masked[index : end + length]))
        index = end + length
    return "".join(result)


def _slug(heading: str) -> str:
    # GitHub keeps hyphens AND underscores; dropping "_" turns a valid
    # `#reward_risk-gate` anchor into a reported defect (planner, 2026-09-21).
    kept = "".join(char.lower() for char in heading if char.isalnum() or char in " -_")
    return kept.replace(" ", "-")


def _headings(document: Path) -> set[str]:
    seen: dict[str, int] = {}
    anchors: set[str] = set()
    for line in _mask_fences(document.read_text(encoding="utf-8")).splitlines():
        match = _HEADING.fullmatch(line)
        if not match:
            continue
        base = _slug(match.group(1))
        count = seen.get(base, 0)
        anchor = base if count == 0 else f"{base}-{count}"
        seen[base] = count + 1
        anchors.add(anchor)
    return anchors


def _display(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _ignored(path: Path, root: Path) -> bool:
    try:
        relative = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return False
    return any(
        relative == prefix or relative.startswith(f"{prefix}/")
        for prefix in _IGNORED_PREFIXES
    )


def _target(document: Path, href: str) -> tuple[Path, str] | None:
    value = href[1:-1] if href.startswith("<") and href.endswith(">") else href
    location, separator, fragment = unquote(value).partition("#")
    if _SCHEME.match(location) or location.startswith(("//", "/")):
        return None
    return (
        (document.parent / location).resolve() if location else document.resolve(),
        fragment if separator else "",
    )


def _looks_like_path(text: str) -> bool:
    return bool(_PATH_LABEL.fullmatch(text))


def _path_text_matches(document: Path, label: str, target: Path, root: Path) -> bool:
    candidates = [(document.parent / label).resolve(), (root / label).resolve()]
    docs_root = next(
        (parent for parent in document.parents if parent.name == "docs"), None
    )
    if docs_root:
        candidates.append((docs_root / label).resolve())
    return target in candidates or (
        "/" not in label and target.name == Path(label).name
    )


def check_paths(paths: list[Path], root: Path) -> list[str]:
    """Return every local-link violation in the supplied Markdown documents."""
    errors: list[str] = []
    heading_cache: dict[Path, set[str]] = {}
    for document in paths:
        if _ignored(document, root):
            continue
        text = document.read_text(encoding="utf-8")
        for match in _LINK.finditer(_mask_code(text)):
            href = match.group("href")
            resolved = _target(document, href)
            if resolved is None:
                continue
            target, fragment = resolved
            line = text.count("\n", 0, match.start()) + 1
            location = f"{_display(document, root)}:{line}"
            if not target.exists():
                errors.append(f"{location}: missing target for href '{href}'")
                continue
            if fragment and not match.group("image") and target.suffix.lower() == ".md":
                anchors = heading_cache.setdefault(target, _headings(target))
                if fragment not in anchors:
                    errors.append(
                        f"{location}: missing fragment '{fragment}' in href '{href}'"
                    )
            label = match.group("text")
            if (
                not match.group("image")
                and _looks_like_path(label)
                and not _path_text_matches(document, unquote(label), target, root)
            ):
                errors.append(
                    f"{location}: path-like text '{label}' does not match href '{href}'"
                )
    return errors


def _tracked_markdown(root: Path) -> list[Path]:
    git = which("git")
    if git is None:
        raise RuntimeError("git executable was not found on PATH")
    completed = subprocess.run(  # noqa: S603 - fixed, local read-only git arguments.
        [git, "ls-files", "*.md"],
        cwd=root,
        capture_output=True,
        check=False,
        text=True,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "git ls-files failed")
    return [root / name for name in completed.stdout.splitlines()]


def main(argv: list[str]) -> int:
    paths = (
        [Path(argument).resolve() for argument in argv]
        if argv
        else _tracked_markdown(_ROOT)
    )
    try:
        errors = check_paths(paths, _ROOT)
    except (OSError, RuntimeError) as exc:
        print(f"markdown link check failed: {exc}")
        return 1
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
