.PHONY: install lint format type test boundaries check ci clean

PKGS = kernel contracts agents orchestration surfaces

install:        ## Install all dependencies (incl. dev group)
	uv sync

lint:           ## Run ruff linter + formatter check
	uv run ruff check .
	uv run ruff format --check .

format:         ## Auto-fix lint issues and format code
	uv run ruff check --fix .
	uv run ruff format .

type:           ## Run mypy type checker
	uv run mypy $(PKGS)

boundaries:     ## Enforce the agent-isolation import contracts
	uv run lint-imports

test:           ## Run all tests with coverage
	uv run pytest

check:          ## Run all quality checks (same as "am I done?")
	uv run pre-commit run --all-files
	uv run pytest

ci:             ## Simulate the GitHub CI quality/security lane locally
	uv run ruff check . --output-format=github
	uv run ruff format --check .
	uv run mypy $(PKGS)
	uv run lint-imports
	uv run python scripts/check_module_size.py $(PKGS) tests
	uv run python scripts/check_module_header.py kernel contracts agents scripts
	uv run pytest
	-uv run pip-audit
	uv run pre-commit run detect-secrets --all-files

clean:          ## Remove build artifacts
	rm -rf .venv htmlcov .mypy_cache .pytest_cache .ruff_cache
