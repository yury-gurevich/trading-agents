# Scheduled dispatcher image.
# Places the day-keyed RunRequest from a Container Apps Job.
FROM dhi.io/python:3.13-dev AS build
WORKDIR /app
RUN python -m pip install --no-cache-dir "uv==0.4.29"
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --extra runtime --no-dev
COPY kernel/ kernel/
COPY contracts/ contracts/
COPY agents/__init__.py agents/__init__.py
COPY agents/provider/__init__.py agents/provider/__init__.py
COPY agents/provider/domain/__init__.py agents/provider/domain/__init__.py
COPY agents/provider/domain/market_calendar.py agents/provider/domain/market_calendar.py
COPY agents/scanner/__init__.py agents/scanner/__init__.py
COPY agents/scanner/universe.py agents/scanner/universe.py
COPY orchestration/__init__.py orchestration/__init__.py
COPY orchestration/scheduled_dispatch.py orchestration/scheduled_dispatch.py
COPY orchestration/settings.py orchestration/settings.py
COPY orchestration/start.py orchestration/start.py
COPY scripts/dispatch_scheduled_run.py scripts/dispatch_scheduled_run.py
COPY scripts/universe_sp100.txt scripts/universe_sp100.txt

FROM dhi.io/python:3.13
WORKDIR /app
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:${PATH}"
COPY --from=build /app /app
CMD ["python", "scripts/dispatch_scheduled_run.py"]
