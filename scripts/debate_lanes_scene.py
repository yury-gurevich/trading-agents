"""Run the production manager and debaters together over the chosen transport.

Agent: tooling
Role: build D5's scene and implement D8's warm-up, first poll and late-turn waits.
External I/O: none on memory; disposable Azure topics only when live is selected.
"""

from __future__ import annotations

import threading
import time
from collections import Counter
from typing import Any

from scripts.debate_lanes_live import LiveTransport
from scripts.debate_lanes_memory import MemoryTransport
from scripts.debate_lanes_model import MANAGER, SleepingLLM, pm_node, warm_up
from scripts.debate_lanes_observers import CheckingPeerClient, TimedBus
from scripts.debate_lanes_report import build_report, is_clean

from agents.deliberator.agent import DeliberatorAgent
from agents.deliberator.poll import review_pm_node
from agents.deliberator.settings import DeliberatorSettings
from agents.deliberator.store import DELIBERATION_RUN_LABEL
from kernel import CollectingFaultSink, InMemoryGraphStore, InProcessBus, fault_boundary
from kernel.serve_loop import serve_once


def run(
    *,
    transport: str = "memory",
    concurrency: int = 4,
    replicas: int | None = None,
    orders: int = 8,
    rounds: int = 2,
    turn_seconds: float = 0.5,
    wait_seconds: float = 5.0,
    replica_start_delay: float = 0.0,
    requests_a_pass: int | None = None,
) -> dict[str, Any]:
    """Measure one fresh scene without changing any production request or reply."""
    warm_up()
    if transport not in {"memory", "live"}:
        raise ValueError("transport must be memory or live")
    wire = (
        MemoryTransport(requests_a_pass)
        if transport == "memory"
        else LiveTransport(requests_a_pass)
    )
    replicas = concurrency if replicas is None else replicas
    graph, sink = InMemoryGraphStore(), CollectingFaultSink()
    served: list[dict[str, Any]] = []
    calls: list[dict[str, Any]] = []
    errors: list[str] = []
    lock, stop = threading.Lock(), threading.Event()
    threads: list[threading.Thread] = []
    first_polls: list[threading.Event] = []
    starter: threading.Thread | None = None
    report = {
        "transport": transport,
        "concurrency": concurrency,
        "replicas": replicas,
        "orders": orders,
        "rounds": rounds,
        "turn_seconds": turn_seconds,
        "wait_seconds": wait_seconds,
        "replica_start_delay_seconds": replica_start_delay,
        "requests_a_pass": wire.sb.receive_max_messages,
    }

    def replica(role: str, identity: str, index: int, polled: threading.Event) -> None:
        name = f"{role}-{index}"
        try:
            with fault_boundary(
                sink, agent=identity, module=__name__, capability="serve", reraise=False
            ) as capture:
                settings = DeliberatorSettings(
                    _env_file=None, role=role, instance_name=identity, max_rounds=rounds
                )
                bus = InProcessBus()
                DeliberatorAgent(
                    bus, graph=graph, llm=SleepingLLM(turn_seconds), settings=settings
                ).bind()
                consumer = wire.consumer(graph, identity)
                observer = TimedBus(bus, name, served, lock)
                while not stop.is_set():
                    serve_once(consumer, observer, sink=sink)
                    polled.set()
            if capture.fault is not None:
                with lock:
                    errors.append(
                        f"{name}: {capture.fault.error_type}: {capture.fault.message}"
                    )
        finally:
            polled.set()  # a failed replica must also release the startup wait

    def start_replicas() -> None:
        if stop.wait(replica_start_delay):
            return
        for thread in threads:
            if not stop.is_set():
                thread.start()

    try:
        for role, identity in (
            ("proponent", wire.proponent),
            ("opponent", wire.opponent),
        ):
            for index in range(replicas):
                polled = threading.Event()
                first_polls.append(polled)
                threads.append(
                    threading.Thread(
                        target=replica,
                        args=(role, identity, index, polled),
                        daemon=True,
                    )
                )
        settings = DeliberatorSettings(
            _env_file=None,
            role="manager",
            max_rounds=rounds,
            debate_concurrency=concurrency,
            proponent_identity=wire.proponent,
            opponent_identity=wire.opponent,
        )
        if settings.identity != MANAGER:
            raise ValueError("the manager must be deliberator-manager")
        manager = DeliberatorAgent(
            InProcessBus(), graph=graph, llm=SleepingLLM(0.0), settings=settings
        )
        client = CheckingPeerClient(
            wire.peer_client(graph, wait_seconds, sink), calls, lock
        )
        pm = pm_node(graph, orders)
        if replica_start_delay == 0:
            start_replicas()
            for polled in first_polls:
                polled.wait()
        began = time.monotonic()
        if replica_start_delay > 0:
            starter = threading.Thread(target=start_replicas, daemon=True)
            starter.start()
        review_pm_node(
            pm,
            graph=graph,
            manager=manager,
            peer_client=client,
            settings=settings,
            sink=sink,
        )
        span = time.monotonic() - began
        time.sleep(min(2 * turn_seconds + 0.3, 12))
        stop.set()
        for thread in threads:
            if thread.ident is not None:
                thread.join(timeout=turn_seconds + 8)
        (record,) = graph.list_nodes(DELIBERATION_RUN_LABEL)
        report = build_report(
            report,
            props=dict(record.props),
            counts=wire.counts(),
            reply_topic=wire.reply_topic,
            calls=calls,
            served=served,
            span=span,
            errors=errors,
            faults=dict(Counter(f.error_type for f in sink.faults)),
        )
    finally:
        stop.set()
        if starter is not None:
            starter.join()
        for thread in threads:
            if thread.ident is not None and thread.is_alive():
                thread.join(timeout=turn_seconds + 8)
        report["teardown"] = wire.close()
    if transport == "live":
        report["production_unchanged"] = wire.production_unchanged
        report["production_subscriptions_before"] = wire.production_before
        report["production_subscriptions_after"] = wire.production_after
    report["clean"] = is_clean(report)
    return report
