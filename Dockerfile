FROM python:3.14-slim

WORKDIR /app

# Install uv (pinned for reproducibility)
RUN pip install --no-cache-dir "uv==0.4.29"

# Dependency layer — cached unless pyproject.toml or uv.lock changes
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --extra runtime --no-dev

# Application source
COPY . .

# Prometheus metrics endpoint
EXPOSE 8000

# Default: start the metrics server in a thread, then run the CLI dispatcher.
# Override CMD to run other surfaces (e.g. the MCP server).
CMD ["uv", "run", "python", "-m", "surfaces.entrypoint"]
