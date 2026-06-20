# forecaster agent image.
# Needs the 'forecaster' extra for PyTorch + Transformers (FinBERT).
FROM python:3.13-slim
WORKDIR /app
RUN pip install --no-cache-dir "uv==0.4.29"
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --extra runtime --extra forecaster --no-dev
COPY kernel/ kernel/
COPY contracts/ contracts/
COPY agents/forecaster/ agents/forecaster/
EXPOSE 8000
CMD ["uv", "run", "python", "-m", "agents.forecaster.entrypoint"]
