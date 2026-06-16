"""Real Layer-0 dependency probes (DEP-*).

Agent: probes
Role: prove each shared dependency is healthy against the real system, through the
provider's functional channels (not mocks).
External I/O: Neo4j, market-data feeds (Stooq/Finnhub), Postgres (raw OHLCV fallback).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

GREEN, WARN, RED, SKIP = "GREEN", "WARN", "RED", "SKIP"


@dataclass
class Result:
    """One probe outcome, tagged with the DEP-* law id it proves."""

    dep: str
    name: str
    status: str
    detail: str


def probe_config(creds: dict[str, str]) -> list[Result]:
    """DEP-CONFIG-01 — required keys for the active stage are present."""
    missing = [
        k for k in ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD") if not creds.get(k)
    ]
    if missing:
        return [
            Result("DEP-CONFIG-01", "config: required keys", RED, f"missing {missing}")
        ]
    extra = [
        k
        for k in ("PROVIDER_FINNHUB_API_KEY", "DATABASE_URL", "ANTHROPIC_API_KEY")
        if creds.get(k)
    ]
    return [
        Result(
            "DEP-CONFIG-01",
            "config: required keys",
            GREEN,
            f"neo4j + {len(extra)} feed/llm creds",
        )
    ]


def probe_clock(creds: dict[str, str]) -> list[Result]:
    """DEP-CLOCK-01 — a UTC instant is available."""
    return [
        Result(
            "DEP-CLOCK-01",
            "clock: UTC instant",
            GREEN,
            datetime.now(tz=UTC).isoformat(timespec="seconds"),
        )
    ]


def probe_neo4j(creds: dict[str, str]) -> list[Result]:
    """DEP-NEO4J-01/02/03 — reachable, round-trips, enforces uniqueness."""
    uri, user, pw = (
        creds.get("NEO4J_URI"),
        creds.get("NEO4J_USER"),
        creds.get("NEO4J_PASSWORD"),
    )
    db = creds.get("NEO4J_DATABASE") or "neo4j"
    if not uri:
        return [Result("DEP-NEO4J-01", "neo4j", SKIP, "no NEO4J_URI")]
    try:
        from neo4j import GraphDatabase
    except ImportError:
        return [
            Result("DEP-NEO4J-01", "neo4j", SKIP, "driver missing (--extra runtime)")
        ]
    out: list[Result] = []
    drv = GraphDatabase.driver(uri, auth=(user, pw), connection_timeout=15)
    try:
        drv.verify_connectivity()
        out.append(
            Result("DEP-NEO4J-01", "neo4j: reachable", GREEN, uri.split("@")[-1])
        )
        with drv.session(database=db) as session:
            key = "depprobe-" + uuid.uuid4().hex
            session.run("CREATE (n:_DepProbe {key:$k, v:1})", k=key)
            value = session.run(
                "MATCH (n:_DepProbe {key:$k}) RETURN n.v AS v", k=key
            ).single()["v"]
            session.run("MATCH (n:_DepProbe {key:$k}) DELETE n", k=key)
            out.append(
                Result(
                    "DEP-NEO4J-02",
                    "neo4j: write/read",
                    GREEN if value == 1 else RED,
                    "round-trip",
                )
            )
            out.append(_neo4j_uniqueness(session))
    except Exception as exc:
        out.append(
            Result(
                "DEP-NEO4J-01",
                "neo4j: reachable",
                RED,
                f"{type(exc).__name__}: {str(exc)[:50]}",
            )
        )
    finally:
        drv.close()
    return out


def _neo4j_uniqueness(session: object) -> Result:
    name = "depprobe_unique"
    session.run(
        f"CREATE CONSTRAINT {name} IF NOT EXISTS "
        "FOR (n:_DepProbeU) REQUIRE n.key IS UNIQUE"
    )
    key = "u-" + uuid.uuid4().hex
    session.run("CREATE (n:_DepProbeU {key:$k})", k=key)
    rejected = False
    try:
        session.run("CREATE (n:_DepProbeU {key:$k})", k=key)
    except Exception:
        rejected = True
    session.run("MATCH (n:_DepProbeU {key:$k}) DELETE n", k=key)
    session.run(f"DROP CONSTRAINT {name} IF EXISTS")
    return Result(
        "DEP-NEO4J-03",
        "neo4j: uniqueness enforced",
        GREEN if rejected else RED,
        "duplicate rejected" if rejected else "duplicate ALLOWED",
    )


def probe_feed_ohlcv(creds: dict[str, str]) -> list[Result]:
    """DEP-FEED-01 — OHLCV reachable (live Stooq, or the raw Postgres fallback)."""
    from agents.provider.sources import StooqDataSource
    from contracts.common import Window

    end = datetime.now(tz=UTC).date()
    window = Window(start=end - timedelta(days=12), end=end)
    out: list[Result] = []
    try:
        bars = StooqDataSource().fetch_ohlcv(("AAPL",), window)
        out.append(
            Result(
                "DEP-FEED-01",
                "OHLCV: Stooq live",
                GREEN if bars else WARN,
                f"{len(bars)} bars",
            )
        )
    except Exception as exc:
        out.append(
            Result(
                "DEP-FEED-01",
                "OHLCV: Stooq live",
                WARN,
                f"down ({type(exc).__name__}); FMP/fallback covers",
            )
        )
    out.append(_fmp_ohlcv(creds))
    out.append(_postgres_ohlcv(creds))
    return out


def _fmp_ohlcv(creds: dict[str, str]) -> Result:
    """FinancialModelingPrep stable EOD — the live OHLCV source (free tier)."""
    key = creds.get("FNP_API_KEY")
    if not key:
        return Result("DEP-FEED-01", "OHLCV: FMP live", SKIP, "no FNP_API_KEY")
    import json
    import urllib.request

    url = (
        "https://financialmodelingprep.com/stable/historical-price-eod/light"
        f"?symbol=AAPL&apikey={key}"
    )
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:  # noqa: S310 - declared FMP endpoint
            data = json.loads(resp.read())
        count = len(data) if isinstance(data, list) else 0
        return Result(
            "DEP-FEED-01",
            "OHLCV: FMP live",
            GREEN if count else RED,
            f"{count} AAPL EOD bars",
        )
    except Exception as exc:
        return Result("DEP-FEED-01", "OHLCV: FMP live", RED, f"{type(exc).__name__}")


def _postgres_ohlcv(creds: dict[str, str]) -> Result:
    dsn = creds.get("DATABASE_URL")
    if not dsn:
        return Result(
            "DEP-FEED-01", "OHLCV: Postgres fallback (raw)", SKIP, "no DATABASE_URL"
        )
    try:
        import psycopg2
    except ImportError:
        return Result(
            "DEP-FEED-01",
            "OHLCV: Postgres fallback (raw)",
            SKIP,
            "psycopg2 missing (--extra probes)",
        )
    try:
        conn = psycopg2.connect(dsn, connect_timeout=15)
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM price_cache WHERE ticker = 'AAPL'")
        count = cur.fetchone()[0]
        conn.close()
        return Result(
            "DEP-FEED-01",
            "OHLCV: Postgres fallback (raw)",
            GREEN if count else RED,
            f"{count} AAPL bars",
        )
    except Exception as exc:
        return Result(
            "DEP-FEED-01",
            "OHLCV: Postgres fallback (raw)",
            RED,
            f"{type(exc).__name__}",
        )


def probe_feed_fundamentals(creds: dict[str, str]) -> list[Result]:
    """DEP-FEED-02 — the keyed feed authenticates and returns data."""
    key = creds.get("PROVIDER_FINNHUB_API_KEY")
    if not key:
        return [
            Result(
                "DEP-FEED-02",
                "fundamentals: Finnhub",
                SKIP,
                "no PROVIDER_FINNHUB_API_KEY",
            )
        ]
    from agents.provider.fundamentals import FinnhubDataSource
    from contracts.common import Window

    end = datetime.now(tz=UTC).date()
    window = Window(start=end - timedelta(days=5), end=end)
    try:
        source = FinnhubDataSource(
            api_key=key, base_url="https://finnhub.io/api/v1", timeout=10
        )
        metrics = source.fetch_fundamentals(("AAPL",), window).get("AAPL", {})
        return [
            Result(
                "DEP-FEED-02",
                "fundamentals: Finnhub live",
                GREEN if metrics else RED,
                f"{len(metrics)} AAPL metrics",
            )
        ]
    except Exception as exc:
        return [
            Result(
                "DEP-FEED-02",
                "fundamentals: Finnhub live",
                RED,
                f"{type(exc).__name__}",
            )
        ]


def probe_llm(creds: dict[str, str]) -> list[Result]:
    """DEP-LLM-01 — the model provider is configured (live ping gated for cost)."""
    if not creds.get("ANTHROPIC_API_KEY"):
        return [Result("DEP-LLM-01", "llm: Anthropic", SKIP, "no ANTHROPIC_API_KEY")]
    return [
        Result(
            "DEP-LLM-01", "llm: Anthropic", SKIP, "key present; live ping gated (cost)"
        )
    ]


def probe_tele(creds: dict[str, str]) -> list[Result]:
    """DEP-TELE-01 — the telemetry plane (deferred provisioning)."""
    note = (
        "Prometheus URL present; Event Hubs not provisioned"
        if creds.get("PROMETHEUS_REMOTE_WRITE_URL")
        else "not provisioned"
    )
    return [Result("DEP-TELE-01", "telemetry: Azure", SKIP, note)]


# Order mirrors docs/laws/dependencies.md "Probe sequencing".
PROBES = (
    probe_config,
    probe_clock,
    probe_neo4j,
    probe_feed_ohlcv,
    probe_feed_fundamentals,
    probe_llm,
    probe_tele,
)
