"""Real Layer-0 dependency probes (DEP-*).

Agent: probes
Role: prove each shared dependency is healthy against the real system, through the
provider's functional channels (not mocks).
External I/O: PostgreSQL, Neo4j, market-data feeds (Tiingo/FMP/Finnhub), and the
Alpaca paper broker.
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
    has_postgres = bool(creds.get("POSTGRES_DSN"))
    has_neo4j = bool(creds.get("NEO4J_URI"))
    if not (has_postgres or has_neo4j):
        return [
            Result(
                "DEP-CONFIG-01",
                "config: required keys",
                RED,
                "missing POSTGRES_DSN (or NEO4J_URI rollback)",
            )
        ]
    extra = [
        k for k in ("PROVIDER_FINNHUB_API_KEY", "ANTHROPIC_API_KEY") if creds.get(k)
    ]
    backend = "postgres" if has_postgres else "neo4j rollback"
    return [
        Result(
            "DEP-CONFIG-01",
            "config: required keys",
            GREEN,
            f"{backend} + {len(extra)} feed/llm creds",
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


def probe_postgres(creds: dict[str, str]) -> list[Result]:
    """DEP-POSTGRES-01 — reachable and answers a cheap SQL probe."""
    dsn = creds.get("POSTGRES_DSN")
    if not dsn:
        return [Result("DEP-POSTGRES-01", "postgres", SKIP, "no POSTGRES_DSN")]
    try:
        import psycopg
    except ImportError:
        return [
            Result(
                "DEP-POSTGRES-01",
                "postgres",
                SKIP,
                "driver missing (--extra runtime)",
            )
        ]
    try:
        with (
            psycopg.connect(dsn, connect_timeout=10) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute("SELECT 1")
            row = cursor.fetchone()
        return [
            Result(
                "DEP-POSTGRES-01",
                "postgres: reachable",
                GREEN if row and row[0] == 1 else RED,
                "SELECT 1",
            )
        ]
    except Exception as exc:
        return [
            Result(
                "DEP-POSTGRES-01",
                "postgres: reachable",
                RED,
                f"{type(exc).__name__}",
            )
        ]


def probe_neo4j(creds: dict[str, str]) -> list[Result]:
    """DEP-NEO4J-01/02/03 — reachable, round-trips, enforces uniqueness."""
    if creds.get("POSTGRES_DSN") and not creds.get("PROBE_NEO4J"):
        return [Result("DEP-NEO4J-01", "neo4j", SKIP, "postgres active")]
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
    """DEP-FEED-01 — OHLCV reachable: Tiingo (primary) + FMP (validation)."""
    return [_tiingo_ohlcv(creds), _fmp_ohlcv(creds)]


def _tiingo_ohlcv(creds: dict[str, str]) -> Result:
    """Tiingo daily EOD — the runtime-default live OHLCV feed (S44, ADR-0006)."""
    key = creds.get("TIINGO_API_KEY") or creds.get("PROVIDER_TIINGO_API_KEY")
    if not key:
        return Result("DEP-FEED-01", "OHLCV: Tiingo live", SKIP, "no TIINGO_API_KEY")
    from agents.provider.tiingo import TiingoDataSource
    from contracts.common import Window

    end = datetime.now(tz=UTC).date()
    window = Window(start=end - timedelta(days=12), end=end)
    try:
        source = TiingoDataSource(
            api_key=key, base_url="https://api.tiingo.com", timeout=20
        )
        bars = source.fetch_ohlcv(("AAPL",), window)
        return Result(
            "DEP-FEED-01",
            "OHLCV: Tiingo live",
            GREEN if bars else RED,
            f"{len(bars)} AAPL EOD bars",
        )
    except Exception as exc:
        return Result("DEP-FEED-01", "OHLCV: Tiingo live", RED, f"{type(exc).__name__}")


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


def probe_sentiment(creds: dict[str, str]) -> list[Result]:
    """DEP-FEED-02 — Alpha Vantage vendor news sentiment authenticates and returns."""
    key = creds.get("ALPHAVANTAGE_API_KEY")
    if not key:
        return [
            Result(
                "DEP-FEED-02",
                "sentiment: Alpha Vantage",
                SKIP,
                "no ALPHAVANTAGE_API_KEY",
            )
        ]
    from agents.provider.av_sentiment import AlphaVantageSentimentSource

    source = AlphaVantageSentimentSource(
        api_key=key, base_url="https://www.alphavantage.co", timeout=25
    )
    try:
        scores = source.fetch_sentiment(("AAPL",))
    except Exception as exc:
        detail = f"down ({type(exc).__name__})"
        return [Result("DEP-FEED-02", "sentiment: Alpha Vantage live", RED, detail)]
    if "AAPL" in scores:
        detail = f"AAPL vendor sentiment {scores['AAPL']:.2f} (0-1 aligned)"
        return [Result("DEP-FEED-02", "sentiment: Alpha Vantage live", GREEN, detail)]
    return [
        Result("DEP-FEED-02", "sentiment: Alpha Vantage live", WARN, "no AAPL reading")
    ]


def probe_broker(creds: dict[str, str]) -> list[Result]:
    """DEP-BROKER-01/02 — Alpaca paper broker accepts an order and is idempotent."""
    key_id = creds.get("ALPACA_PAPER_API_KEY") or creds.get("ALPACA_API_KEY")
    secret = creds.get("ALPACA_PAPER_API_SECRET") or creds.get("ALPACA_API_SECRET")
    if not key_id or not secret:
        return [
            Result(
                "DEP-BROKER-01",
                "broker: Alpaca paper",
                SKIP,
                "no ALPACA_PAPER_API_KEY / secret",
            )
        ]
    from decimal import Decimal

    from agents.execution.alpaca import AlpacaBroker
    from contracts.common import Money

    broker = AlpacaBroker(
        api_key=key_id,
        secret_key=secret,
        base_url="https://paper-api.alpaca.markets",  # paper only — never live
        timeout=20,
    )
    try:
        broker.fills()  # read-only: proves reachable + authenticated
    except Exception as exc:
        return [
            Result(
                "DEP-BROKER-01",
                "broker: Alpaca paper",
                RED,
                f"unreachable/auth ({type(exc).__name__})",
            )
        ]
    out: list[Result] = []
    client_id = "dep-broker-probe-" + uuid.uuid4().hex[:16]
    ref = Money(amount=Decimal("0.01"))
    try:
        fill = broker.submit(client_id, "AAPL", "buy", 1, ref)
    except Exception as exc:
        detail = f"rejected ({type(exc).__name__})"
        return [Result("DEP-BROKER-01", "broker: submit", RED, detail)]
    accepted = bool(fill.broker_order_id) and fill.status in (
        "filled",
        "partial",
        "pending",
    )
    out.append(
        Result(
            "DEP-BROKER-01",
            "broker: submit -> fill record",
            GREEN if accepted else RED,
            f"{fill.status} ({fill.broker_order_id[:12]})",
        )
    )
    out.append(_broker_idempotent(broker, fill, client_id, ref))
    out.append(_broker_cleanup(broker, fill, ref))
    return out


def _broker_idempotent(
    broker: object, fill: object, client_id: str, ref: object
) -> Result:
    """DEP-BROKER-02 — the same client_order_id replays to one order."""
    try:
        qty = fill.quantity or 1
        replay = broker.submit(client_id, fill.ticker, fill.side, qty, ref)
        same = replay.broker_order_id == fill.broker_order_id
    except Exception as exc:
        detail = f"replay raised ({type(exc).__name__})"
        return Result("DEP-BROKER-02", "broker: idempotent", RED, detail)
    return Result(
        "DEP-BROKER-02",
        "broker: idempotent (client_order_id)",
        GREEN if same else RED,
        "same order on replay" if same else "replay created a new order",
    )


def _broker_cleanup(broker: object, fill: object, ref: object) -> Result:
    """Leave the paper account flat: cancel a resting order, or sell a fill."""
    try:
        if fill.status == "pending":
            broker.cancel(fill.broker_order_id)
            return Result("DEP-BROKER-01", "broker: cleanup", GREEN, "order canceled")
        broker.submit(f"{fill.idempotency_key}-close", fill.ticker, "sell", 1, ref)
        return Result("DEP-BROKER-01", "broker: cleanup", GREEN, "flattened (sell 1)")
    except Exception as exc:
        return Result(
            "DEP-BROKER-01",
            "broker: cleanup",
            WARN,
            f"manual cleanup may be needed ({type(exc).__name__})",
        )


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
    monitor = bool(creds.get("AZURE_MONITOR_CONNECTION_STRING"))
    prom = bool(creds.get("PROMETHEUS_REMOTE_WRITE_URL"))
    if monitor and prom:
        note = "Azure Monitor live; Prometheus URL present; harness unproven"
    elif monitor:
        note = "Azure Monitor live; Prometheus remote-write URL missing"
    else:
        note = "not provisioned"
    return [Result("DEP-TELE-01", "telemetry: Azure", SKIP, note)]


# Order mirrors docs/laws/dependencies.md "Probe sequencing".
PROBES = (
    probe_config,
    probe_clock,
    probe_postgres,
    probe_neo4j,
    probe_feed_ohlcv,
    probe_feed_fundamentals,
    probe_sentiment,
    probe_broker,
    probe_llm,
    probe_tele,
)
