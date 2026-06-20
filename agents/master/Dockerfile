# Master bootstrap agent image.
# Needs the 'azure' extra for Key Vault access (wired in S74).
FROM python:3.13-slim
WORKDIR /app
RUN pip install --no-cache-dir "uv==0.4.29"
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --extra runtime --extra azure --no-dev
COPY kernel/ kernel/
COPY contracts/ contracts/
COPY agents/master/ agents/master/
EXPOSE 8000
CMD ["uv", "run", "python", "-m", "agents.master.entrypoint"]
