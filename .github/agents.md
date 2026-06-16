# Copilot Agent Instructions — trading-agents

This file provides persistent context for GitHub Copilot about the repository's coding standards and preferred patterns.

---

## Coding Standards

### Tooling (Strict — Enforced in CI)

- **Python**: `>= 3.13`
- **Ruff**: line-length `88`, Google docstring convention, extensive rule set (`E,W,F,I,N,UP,B,SIM,S,A,C4,DTZ,T20,PT,RUF,ANN,D,TCH,PIE,RET,ARG,ERA`). See `pyproject.toml` for full config and per-file ignores.
- **Mypy**: `strict = true`, `warn_return_any`, `warn_unreachable`, `show_error_codes`.
- **Pydantic**: v2 only. All DTOs, contracts, and settings use Pydantic `BaseModel` / `BaseSettings`.
- **Import Linter**: Four contracts run on every PR. Agents are islands.

### Style Preferences

- Double quotes for strings (Ruff `quote-style = "double"`).
- Type annotations everywhere; `from __future__ import annotations` where needed.
- Pydantic models for *all* request/response types and settings.
- Docstrings: Google convention (but contracts often document via fields + `mission.md` instead of class docstrings).
- Tests: colocated under `tests/` in each package. Contract tests assert typed shapes; unit tests cover private logic.
- No `print()` in library code (use structured logging via kernel observability).
- Append-only by convention for all transactional data.

### Versioning on Merge to `main`

- Feature merges: bump **minor** version, reset patch (`0.13.6` → `0.14.0`).
- Fix merges: bump only **patch** (`0.13.6` → `0.13.7`).

When displaying dates, include local time in the same string, e.g., `2026-04-18 11:37`.

---

**End of Copilot context.**
