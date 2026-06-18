"""Layer-0 dependency probes — the re-runnable green bill of health.

Agent: probes
Role: prove each shared infrastructure dependency (DEP-*) is healthy against the
real systems, through the functional channels, before any agent is trusted.
External I/O: Neo4j, market-data feeds (Tiingo/FMP/Finnhub/AV), Alpaca broker. Run on demand:
``uv run --extra runtime python -m probes`` (not part of the unit gate).
"""
