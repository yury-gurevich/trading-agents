"""Source proofs for the vocabulary-only deploy action.

Agent: tooling
Role: prove fleet coverage and dispatch without executing the deploy script.
External I/O: read repository source files only.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _script() -> str:
    return (ROOT / "infra/deploy-agents.ps1").read_text(encoding="utf-8")


def _function(name: str) -> str:
    found = re.search(rf"(?ms)^function {name}[^\n]*\n(.*?)^\}}", _script())
    assert found is not None, f"missing {name}"
    return found.group(1)


def test_the_action_is_declared_and_dispatched() -> None:
    """DL-303 D7: vocabulary is accepted and a failed step fails dispatch."""
    source = _script()
    declared = re.search(r"\[ValidateSet\((.*?)\)\]", source, re.S)
    assert declared is not None
    assert "'vocabulary'" in declared.group(1)
    switch = source.split("switch ($Action)", 1)[1]
    assert re.search(
        r"'vocabulary'\s*\{\s*if\s*\(-not\s*\(Enable-Vocabulary\)\)"
        r'\s*\{\s*throw "graph vocabulary not set"\s*\}\s*\}',
        switch,
    )


def test_the_step_sets_every_app_and_the_job_and_reads_each_back() -> None:
    """DL-303 D7: every agent, master and job use the read-back setters."""
    body = _function("Enable-Vocabulary")
    assert 'foreach ($name in @("master") + @($AGENTS.Keys))' in body
    assert "$appOk = Set-AppVocabulary $name" in body
    assert 'Check $appOk "graph vocabulary on $name"' in body
    assert "$ok = $ok -and $appOk" in body
    assert "$jobOk = Set-JobVocabulary" in body
    assert 'Check $jobOk "graph vocabulary on $DISPATCHER_JOB"' in body
    assert "return $ok -and $jobOk" in body
    assert "containerapp" not in body
    assert body.index("Set-AppVocabulary") < body.index("Set-JobVocabulary")
    assert "Get-AppState $name" in _function("Set-AppVocabulary")
    assert "Get-JobState $DISPATCHER_JOB" in _function("Set-JobVocabulary")


def test_the_agent_list_holds_the_fifteen_agent_apps() -> None:
    """DL-303 D7: fifteen named agent apps plus master cover sixteen apps."""
    found = re.search(r"(?ms)^\$AGENTS = \[ordered\]@\{(.*?)^\}", _script())
    assert found is not None
    names = re.findall(r'(?:"([\w-]+)"|(\w+))\s*=', found.group(1))
    agents = {quoted or bare for quoted, bare in names}
    assert len(agents) == 15
    assert "execution" in agents
    assert "master" not in agents


def test_the_pack_declares_the_filled_quantity_on_fill() -> None:
    """EXEC-TYP-04: the fail-closed pack allows execution's new Fill property."""
    path = ROOT / "orchestration/packs/trading_graph_vocabulary.json"
    pack = json.loads(path.read_text(encoding="utf-8"))
    assert "broker_filled_quantity" in pack["properties"]["Fill"]
