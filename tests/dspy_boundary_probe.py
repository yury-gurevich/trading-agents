"""Fresh-process proof of the served DSPy boundary (S254 B1/B2).

Agent: tooling
Role: block excluded imports and sockets while observing the actual served LM.
External I/O: reads fixtures, inspects a temporary cache folder; canned client only.
"""

from __future__ import annotations

import os
import socket
import sys
from importlib import import_module
from pathlib import Path


class Blocker:
    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] in {"diskcache", "litellm"}:
            raise ImportError(f"excluded package: {name}")
        return


def refused(*args, **kwargs):
    raise AssertionError("DSPy attempted a socket connection")


def main() -> None:
    sys.meta_path.insert(0, Blocker())
    socket.socket.connect = refused
    socket.socket.connect_ex = refused
    socket.create_connection = refused
    fixtures = import_module("agents.deliberator.tests.dspy_fixtures")
    engine = import_module("kernel.dspy_engine")
    dspy = import_module("dspy")
    global_history = import_module("dspy.clients.base_lm").GLOBAL_HISTORY
    original = dspy.ChainOfThought.forward
    observed = []

    def forward(program, **inputs):
        lm = dspy.settings.lm
        assert isinstance(lm.engine, engine.ClientEngine)
        assert lm.cache is False
        assert lm.num_retries == 0
        assert dspy.settings.disable_history is True
        assert dspy.settings.adapter.use_json_adapter_fallback is False
        observed.append(lm)
        return original(program, **inputs)

    dspy.ChainOfThought.forward = forward
    assert dspy.cache.enable_disk_cache is False
    assert dspy.cache.enable_memory_cache is False
    client = fixtures.Client(fixtures.answer_for("valid"))
    agent, graph = fixtures.served("defender", client)
    request = fixtures.request_for(fixtures.MAIN["requests"][0])
    for index in range(2):
        reply = agent.debate_turn(
            request.model_copy(update={"request_id": f"boundary-{index}"})
        )
        assert reply.turn.reasoning is not None
    assert len(client.calls) == len(graph.list_nodes("LLMCall")) == len(observed) == 2
    assert client.calls[0] == client.calls[1]
    assert global_history == []
    assert all(lm.history == [] for lm in observed)
    assert list(Path(os.environ["DSPY_CACHEDIR"]).rglob("*")) == []
    assert not {"diskcache", "litellm"} & sys.modules.keys()
    print(
        "served 2; client calls 2; ledger rows 2; own engines 2; "
        "cache files 0; history 0; sockets refused"
    )


if __name__ == "__main__":
    main()
