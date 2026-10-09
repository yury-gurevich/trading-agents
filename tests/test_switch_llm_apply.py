"""Provider-switch apply proofs without Azure or a database.

Agent: tooling
Role: prove ordered narrow updates and snapshots.
External I/O: temporary evidence files only.
"""

from pathlib import Path

from tests.switch_llm_testkit import (
    APPS,
    ROOT,
    FakeAzure,
    FakeClock,
    proof_graph,
    run_switch,
)


def test_d2_apply_changes_only_differences_master_first(tmp_path: Path) -> None:
    """MST-OUT-04 / MST-NEV-07: apply is ordered, narrow, and graph-proven."""
    from scripts.switch_llm_provider import main

    azure = FakeAzure()
    clock = FakeClock()
    output: list[str] = []
    result = main(
        ["--apply", "--evidence-dir", str(tmp_path)],
        runner=azure,
        graph=proof_graph(),
        clock=clock,
        sleep=clock.sleep,
        environ={"POSTGRES_DSN": "fixture"},
        root=ROOT,
        emit=output.append,
    )
    assert result == 0, output
    assert [call[call.index("--name") + 1] for call in azure.updates] == [
        "master",
        "operator",
        "deliberator-manager",
    ]
    for call in azure.updates:
        app = call[call.index("--name") + 1]
        assert call[call.index("--set-env-vars") + 1] == f"{APPS[app]}=openai"
        assert call[call.index("--set-env-vars") + 2] == "-o"
    assert len(list(tmp_path.glob("*.json"))) == 10
    assert all("json" in call for call in azure.calls)
    "\n".join(output).encode("ascii")


def test_d1_report_is_read_only(tmp_path: Path) -> None:
    """MST-OUT-04: reporting names pending differences and never applies them."""
    azure = FakeAzure(differing=("operator",))
    code, output = run_switch(tmp_path, azure, args=[])
    assert code == 3
    assert any("operator:" in line and "differs" in line for line in output)
    assert azure.updates == []
    assert list(tmp_path.iterdir()) == []
    code, output = run_switch(tmp_path, FakeAzure(differing=()), args=[])
    assert code == 0
    assert all("differs" not in line for line in output)


def test_d6_unchanged_apps_are_not_reproven(tmp_path: Path) -> None:
    """MST-OUT-04: unchanged peers are listed and do not require new activations."""
    graph = proof_graph()
    # Only changed non-master targets need an activation; drop both peer facts.
    filtered = type(graph)()
    for label in ("FleetPreflight", "AgentInstance"):
        for node in graph.list_nodes(label):
            if node.key not in ("deliberator-proponent", "deliberator-opponent"):
                filtered.merge_node(label, node.key, dict(node.props))
    code, output = run_switch(tmp_path, FakeAzure(), graph=filtered)
    assert code == 0
    for app in ("deliberator-proponent", "deliberator-opponent"):
        assert f"{app}: unchanged, activation not re-proven" in output


def test_d7_failed_second_update_stops_run(tmp_path: Path) -> None:
    """MST-OUT-04: a failed update stops and names prior changes."""
    azure = FakeAzure()
    azure.fail_app = "operator"
    code, output = run_switch(tmp_path, azure)
    assert code == 1
    assert [call[call.index("--name") + 1] for call in azure.updates] == [
        "master",
        "operator",
    ]
    assert any(
        "already changed: master" in line and "operator" in line for line in output
    )


def test_d8_report_apply_and_prove_output_are_ascii(tmp_path: Path) -> None:
    """MST-OUT-04: every supported mode's output survives redirected Windows stdout."""
    for args in ([], ["--prove-since", "2026-10-09T00:00:00Z"], None):
        _, output = run_switch(tmp_path, FakeAzure(), args=args)
        "\n".join(output).encode("ascii")
