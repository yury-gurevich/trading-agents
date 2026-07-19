# operator agent image.
FROM dhi.io/python:3.13-dev AS build
WORKDIR /app
RUN python -m pip install --no-cache-dir "uv==0.4.29"
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --extra runtime --extra azure --no-dev
COPY kernel/ kernel/
COPY contracts/ contracts/
COPY agents/operator/ agents/operator/

FROM dhi.io/python:3.13
WORKDIR /app
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:${PATH}"
COPY --from=build /app /app
EXPOSE 8000
CMD ["python", "-m", "agents.operator.entrypoint"]
