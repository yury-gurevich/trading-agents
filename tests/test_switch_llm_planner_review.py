"""Provider-switch cases added at the planner's review of S262.

Agent: tooling
Role: prove a no-change apply ends at once and an update that did not take fails.
External I/O: temporary evidence files only.
"""

from pathlib import Path

from tests.switch_llm_testkit import APPS, FakeAzure, run_switch

from kernel import InMemoryGraphStore


def test_apply_with_nothing_to_change_ends_at_once(tmp_path: Path) -> None:
    """MST-OUT-04: no update means no fleet check to wait for, and no failure."""
    azure = FakeAzure(differing=())

    code, output = run_switch(tmp_path / "evidence", azure, graph=InMemoryGraphStore())

    assert code == 0, output
    assert azure.updates == []
    assert not (tmp_path / "evidence").exists()
    assert output[-1].startswith("nothing to apply")
    assert not any("proof" in line for line in output)


def test_an_update_that_did_not_take_fails(tmp_path: Path) -> None:
    """MST-NEV-07: a successful update call is not proof the value was applied."""
    azure = FakeAzure(differing=("master",))

    def revert(state: dict[str, object]) -> None:
        env = state["properties"]["template"]["containers"][0]["env"]  # type: ignore[index]
        for entry in env:
            if entry["name"] == APPS["master"]:
                entry["value"] = "anthropic"

    azure.mutate = revert  # type: ignore[assignment]

    code, output = run_switch(tmp_path, azure)

    assert code == 1, output
    assert "master: declared provider was not applied" in output
