"""A27-A29: declared writes, injected Telegram and the sensor's read-only surface.

Agent: orchestration
Role: prove pack vocabulary, transport payload and the image's nine module copies.
External I/O: reads local source and pack files only.
"""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

from kernel import InMemoryGraphStore
from kernel.graph_guarded import GuardedGraphStore
from kernel.graph_vocabulary import Vocabulary
from orchestration.container_queries import ContainerLogReadError
from orchestration.container_sensor_guard import sense_safely
from orchestration.telegram_client import TelegramClient
from orchestration.tests.container_sensor_helpers import (
    MEASURED,
    NOW,
    SETTINGS,
    FakeAlarm,
    FakeReader,
)

ROOT = Path(__file__).resolve().parents[2]
MODULES = (
    "container_alarm_text",
    "container_brief",
    "container_events",
    "container_lines",
    "container_logs",
    "container_queries",
    "container_sensor",
    "container_sensor_graph",
    "container_sensor_guard",
)


def test_a27_pack_accepts_events_reads_edges_and_failures() -> None:
    """DSP-OUT-07 / DSP-OBS-03: real sensor writes satisfy the pack's closed
    vocabulary.
    """
    vocabulary = Vocabulary.from_mapping(
        json.loads(
            (ROOT / "orchestration/packs/trading_graph_vocabulary.json").read_text(
                encoding="utf-8"
            )
        )
    )
    inner = InMemoryGraphStore()
    graph = GuardedGraphStore(inner, vocabulary, writer="dispatcher")
    assert (
        sense_safely(
            graph,
            FakeReader(list(MEASURED.values())),
            FakeAlarm(),
            now=NOW,
            settings=SETTINGS,
        )
        == "container-sensor read 8 rows: 8 new events, 7 alarms, told 7"
    )
    line = sense_safely(
        graph,
        FakeReader(failure=ContainerLogReadError("403")),
        FakeAlarm(),
        now=NOW + timedelta(minutes=10),
        settings=SETTINGS,
    )
    assert line == "error container-sensor failed: ContainerLogReadError (403)"
    assert len(inner.list_nodes("ContainerEvent")) == 8
    assert len(inner.list_nodes("ContainerSensorRead")) == 2
    assert len(inner.list_nodes("Fault")) == 1


def test_a28_send_alarm_posts_only_chat_and_plain_text() -> None:
    """DSP-SEC-01: send_alarm's injected sender receives only the chat id and text."""
    sent: list[tuple[str, dict[str, object], float]] = []

    def sender(method: str, payload: dict[str, object], timeout: float) -> object:
        sent.append((method, payload, timeout))
        return {"ok": True, "result": {"message_id": 55}}

    credential = "test"
    client = TelegramClient(api_token=credential, chat_id="operator", sender=sender)
    assert client.send_alarm(text="Container alarm: fixture") == 55
    assert len(sent) == 1
    assert sent[0][:2] == (
        "sendMessage",
        {"chat_id": "operator", "text": "Container alarm: fixture"},
    )
    assert credential not in repr(sent)


def test_a29_sensor_has_only_log_reads_and_identity_get() -> None:
    """DSP-NEV-03: sensor source has no management API or mutating HTTP operation."""
    sources = [
        (ROOT / "orchestration" / f"{name}.py").read_text(encoding="utf-8")
        for name in MODULES
    ]
    source = "\n".join(sources)
    assert "management.azure.com" not in source
    assert all(
        f'method="{method}"' not in source for method in ("PUT", "PATCH", "DELETE")
    )
    assert source.count('method="GET"') == source.count('method="POST"') == 1
    assert all(len(text.splitlines()) < 200 for text in sources)


def test_image_copies_all_sensor_modules() -> None:
    """DSP-FAIL-04: the job image carries each of the nine sensor modules by name."""
    dockerfile = (ROOT / "orchestration/Dockerfile").read_text(encoding="utf-8")
    for module in MODULES:
        path = f"orchestration/{module}.py"
        assert f"COPY {path} {path}\n" in dockerfile
