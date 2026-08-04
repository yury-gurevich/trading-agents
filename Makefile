.PHONY: install lint format type test boundaries check ci codeql-ast codeql-errors clean \
	docker-build stack-up stack-down stack-deploy stack-rm

PKGS = kernel contracts agents orchestration surfaces
STACK = trading-agents

# Windows/Git-Bash: `/dev/null` resolves to `NUL`, a *character device*, so
# `sys.stdout.isatty()` is TRUE when stdout is redirected there. rich then takes
# its legacy-Windows terminal path and writes import-linter's ":brick:" spinner
# through this host's cp1252 stdio, raising UnicodeEncodeError in the spinner's
# teardown — *after* the contracts have already been checked and printed
# "4 kept, 0 broken". `make ci >/dev/null` therefore reported a false RED on a
# green gate (hardening row S). Forcing UTF-8 stdio fixes it and also makes local
# runs match CI, which is UTF-8 on Linux.
#
# Never measure this gate through a pipe: `make ci | tail` reports tail's exit
# code, not make's. Redirect to a file and read it.
export PYTHONUTF8 = 1

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
	uv run python scripts/check_untracked_secrets.py
	uv run pytest

ci:             ## Simulate the GitHub CI quality/security lane locally
	uv run ruff check . --output-format=github
	uv run ruff format --check .
	uv run mypy $(PKGS)
	uv run lint-imports
	uv run python scripts/check_module_size.py $(PKGS) tests
	uv run python scripts/check_module_header.py $(PKGS) scripts
	uv run python scripts/check_law_coverage.py
	uv run pytest
	uv run pip-audit
	uv run pre-commit run detect-secrets --all-files
	uv run python scripts/check_untracked_secrets.py

gate-selftest:  ## Prove each gate can fail (plants a violation per check)
	uv run python scripts/gate_selftest.py

codeql-ast:     ## Generate CodeQL AST artifacts for FILE=path/to/file.py
ifndef FILE
	$(error Usage: make codeql-ast FILE=kernel/agent.py)
endif
	powershell -ExecutionPolicy Bypass -File scripts/run_codeql_ast.ps1 -SourceFile "$(FILE)"

codeql-errors:  ## List error-level CodeQL findings (the ones that fail CI)
	python scripts/codeql_errors.py

clean:          ## Remove build artifacts
	rm -rf .venv htmlcov .mypy_cache .pytest_cache .ruff_cache

# ── Docker / stack ────────────────────────────────────────────────────────────

docker-build:   ## Build the app container image
	docker build -t trading-agents:local .

stack-up:       ## Start app + Prometheus locally (docker compose)
	docker compose up

stack-down:     ## Stop the local compose stack
	docker compose down

stack-deploy:   ## Deploy as a Docker Swarm stack (build first)
	docker build -t trading-agents:local .
	docker stack deploy -c docker-compose.yml $(STACK)

stack-rm:       ## Remove the deployed Swarm stack
	docker stack rm $(STACK)
