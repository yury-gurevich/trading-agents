# operator agent image.
FROM python:3.13-slim
WORKDIR /app
RUN pip install --no-cache-dir "uv==0.4.29"
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --extra runtime --no-dev
COPY kernel/ kernel/
COPY contracts/ contracts/
COPY agents/operator/ agents/operator/
EXPOSE 8000
CMD ["uv", "run", "python", "-m", "agents.operator.entrypoint"]
