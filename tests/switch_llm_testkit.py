"""Offline provider-switch test dependencies.

Agent: tooling
Role: provide fake Azure state, graph evidence and a deterministic clock.
External I/O: none.
"""

import json
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path
from subprocess import CompletedProcess

from kernel import InMemoryGraphStore

ROOT = Path(__file__).resolve().parents[1]
APPS = {
    "master": "MASTER_LLM_PROVIDER",
    "operator": "OPERATOR_LLM_PROVIDER",
    "deliberator-manager": "DELIBERATOR_LLM_PROVIDER",
    "deliberator-proponent": "DELIBERATOR_LLM_PROVIDER",
    "deliberator-opponent": "DELIBERATOR_LLM_PROVIDER",
}
START = datetime(2026, 10, 9, tzinfo=UTC)


class FakeAzure:
    def __init__(
        self, differing: tuple[str, ...] = ("master", "operator", "deliberator-manager")
    ) -> None:
        self.calls: list[list[str]] = []
        self.replicas: list[object] = []
        self.fail_app = ""
        self.mutate = None
        self.states = {
            app: {
                "identity": {"type": "SystemAssigned"},
                "properties": {
                    "runningStatus": "Running",
                    "template": {
                        "containers": [
                            {
                                "name": app,
                                "image": "image:unchanged",
                                "env": [
                                    {
                                        "name": key,
                                        "value": "anthropic"
                                        if app in differing
                                        else "openai",
                                    },
                                    {"name": "OTHER", "value": "kept"},
                                ],
                            }
                        ],
                        "scale": {"minReplicas": 0},
                    },
                    "configuration": {
                        "secrets": [{"name": "postgres-dsn"}],
                        "ingress": {},
                        "registries": [],
                    },
                },
            }
            for app, key in APPS.items()
        }

    def __call__(self, args: list[str]) -> CompletedProcess[str]:
        self.calls.append(args)
        app = args[args.index("--name") + 1]
        if args[1:3] == ["replica", "list"]:
            return CompletedProcess(
                args, 0, json.dumps(self.replicas), "spinner ignored"
            )
        if args[1] == "update":
            if app == self.fail_app:
                return CompletedProcess(args, 1, "{}", "update failed")
            assignment = args[args.index("--set-env-vars") + 1]
            name, value = assignment.split("=", 1)
            env = self.states[app]["properties"]["template"]["containers"][0]["env"]
            env[:] = [entry for entry in env if entry["name"] != name] + [
                {"name": name, "value": value}
            ]
            if self.mutate is not None:
                self.mutate(self.states[app])
        return CompletedProcess(
            args, 0, json.dumps(deepcopy(self.states[app])), "spinner ignored"
        )

    @property
    def updates(self) -> list[list[str]]:
        return [args for args in self.calls if args[1] == "update"]


class FakeClock:
    def __init__(self) -> None:
        self.now = START

    def __call__(self) -> datetime:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


def proof_graph() -> InMemoryGraphStore:
    graph = InMemoryGraphStore()
    graph.merge_node(
        "FleetPreflight", "passing", {"checked_at": START.isoformat(), "passed": True}
    )
    for app in APPS:
        graph.merge_node(
            "AgentInstance",
            app,
            {
                "agent_type": app,
                "started_at": START.isoformat(),
                "state": "active",
                "credential_tests_passed": ["openai"],
                "credential_tests_declared": ["openai"],
            },
        )
    return graph


def run_switch(
    directory: Path,
    azure: FakeAzure,
    *,
    args: list[str] | None = None,
    graph: object | None = None,
    environ: dict[str, str] | None = None,
    root: Path = ROOT,
) -> tuple[int, list[str]]:
    from scripts.switch_llm_provider import main

    clock = FakeClock()
    output: list[str] = []
    code = main(
        [
            "--apply",
            "--evidence-dir",
            str(directory),
            "--wait-seconds",
            "5",
            "--poll-seconds",
            "2",
        ]
        if args is None
        else args,
        runner=azure,
        graph=proof_graph() if graph is None else graph,
        clock=clock,
        sleep=clock.sleep,
        environ={"POSTGRES_DSN": "fixture"} if environ is None else environ,
        root=root,
        emit=output.append,
    )
    "\n".join(output).encode("ascii")
    return code, output
