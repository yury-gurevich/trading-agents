FROM python:3.13-slim

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY agents ./agents
COPY contracts ./contracts
COPY kernel ./kernel
COPY scripts ./scripts

RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev --extra runtime --extra azure

CMD ["uv", "run", "python", "-m", "agents.deliberator.entrypoint"]
