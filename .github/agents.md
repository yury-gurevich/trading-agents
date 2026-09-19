# Copilot Agent Instructions — trading-agents

This file provides persistent context for GitHub Copilot about the repository's coding standards and preferred patterns. The working rules (branches, the CI gate, `make gate-ran`, secrets) live in [`CLAUDE.md`](../CLAUDE.md), [`AGENTS.md`](../AGENTS.md) and [`copilot-instructions.md`](copilot-instructions.md); where this file disagrees, they win.

---

## Coding Standards

### Tooling (Strict — Enforced in CI)

- **Python**: `>= 3.13`
- **Ruff**: line-length `88`, Google docstring convention, extensive rule set (`E,W,F,I,N,UP,B,SIM,S,A,C4,DTZ,T20,PT,RUF,ANN,D,TCH,PIE,RET,ARG,ERA`). See `pyproject.toml` for full config and per-file ignores.
- **Mypy**: `strict = true`, `warn_return_any`, `warn_unreachable`, `show_error_codes`.
- **Pydantic**: v2 only. All DTOs, contracts, and settings use Pydantic `BaseModel` / `BaseSettings`.
- **Import Linter**: Four contracts (`.importlinter`) run in `make ci` and on every push. Agents are islands.

### Style Preferences

- Double quotes for strings (Ruff `quote-style = "double"`).
- Type annotations everywhere; `from __future__ import annotations` where needed.
- Pydantic models for *all* request/response types and settings.
- Docstrings: Google convention (but contracts often document via fields + `mission.md` instead of class docstrings).
- Tests: colocated under `tests/` in each package. Contract tests assert typed shapes; unit tests cover private logic.
- No `print()` in library code (use structured logging via kernel observability).
- Append-only by convention for all transactional data.

### Versioning (`MAJOR.MM.PP`)

- Feature: bump the **middle** group, reset the last (`0.13.06` → `0.14.00`).
- Fix: bump only the **last** group (`0.13.06` → `0.13.07`).
- Docs-only or read-only tooling: no bump.

When displaying dates, include local time in the same string, e.g., `2026-04-18 11:37`.

---

**End of Copilot context.**
