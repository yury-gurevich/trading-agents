# Scheduled dispatcher image.
# Places the day-keyed RunRequest from a Container Apps Job.
FROM python:3.13-slim
WORKDIR /app
RUN pip install --no-cache-dir "uv==0.4.29"
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --extra runtime --no-dev
COPY kernel/ kernel/
COPY contracts/ contracts/
COPY agents/ agents/
COPY orchestration/ orchestration/
COPY scripts/ scripts/
CMD ["uv", "run", "python", "scripts/dispatch_scheduled_run.py"]
