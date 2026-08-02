# deliberator agent image — one image, three roles (manager / proponent / opponent).
# `--extra llm` is required, not optional: agents/deliberator/llm_anthropic.py resolves
# the Anthropic SDK through importlib at call time, so a missing package fails at the
# first debate turn rather than at import. The stage would come up healthy and produce
# nothing — DL-80's exact failure shape, which this agent exists to end.
FROM dhi.io/python:3.13-dev AS build
WORKDIR /app
RUN python -m pip install --no-cache-dir "uv==0.4.29"
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --extra runtime --extra azure --extra llm --no-dev
COPY kernel/ kernel/
COPY contracts/ contracts/
COPY agents/deliberator/ agents/deliberator/

FROM dhi.io/python:3.13
WORKDIR /app
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:${PATH}"
COPY --from=build /app /app
EXPOSE 8000
CMD ["python", "-m", "agents.deliberator.entrypoint"]
