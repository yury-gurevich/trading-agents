# `Master` — Law Test-Plan

**Prefix:** `MST` · **status:** LOCKED v1 · **aligned with:** laws.md LOCKED v1

| Clause | Description | Test | Status |
| --- | --- | --- | --- |
| MST-IDN-01 | `start()` writes Session node | `test_start_writes_session_node` | 🟩 |
| MST-STA-01 | `session_id` None before start, non-None after | `test_start_exposes_session_id` | 🟩 |
| MST-OUT-01 | EHLO → ACTIVATE with matching fields | `test_activate_returns_activate_message` | 🟩 |
| MST-STA-02 | `activate()` writes `AgentInstance` with state=active | `test_activate_writes_agent_instance_node` | 🟩 |
| MST-STA-03 | `activate()` writes one `CapabilityGrant` per capability | `test_activate_writes_capability_grant_nodes` | 🟩 |
| MST-IDM-01 | Two EHLO of same type → distinct instance IDs | `test_activate_second_instance_of_same_type_gets_unique_id` | 🟩 |
| MST-NEV-01 | Unknown agent_type rejected; no graph write | `test_activate_unknown_agent_type_raises` | 🟩 |
| MST-OUT-02 | `drain()` returns `DRAINMessage` | `test_drain_returns_drain_message` | 🟩 |
| MST-STA-04 | `drain()` writes `drain_reason` to AgentInstance | `test_drain_marks_instance_in_graph` | 🟩 |
| MST-NEV-02 | `drain` on unknown instance_id raises `KeyError` | `test_drain_unknown_instance_raises` | 🟩 |
| MST-IDN-02 | Master exclusively owns listed graph labels | architecture / import-linter | ⬜ |
| MST-IDN-03 | Master sole Key Vault accessor | deferred S74 | ⬜ |
| MST-IN-03 | Malformed EHLO → no graph write, fault emitted | integration test (deferred) | ⬜ |
| MST-NEV-03 | No trading logic | static (contract) | ⬜ |
| MST-NEV-04 | Private key never distributed | deferred S74 | ⬜ |
| MST-SEC-01 | RSA signature on ACTIVATE | deferred S74 | ⬜ |
| MST-DEP-01 | Neo4j retry before startup failure | integration (deferred) | ⬜ |
| MST-DEP-02 | Key Vault credential resolution | deferred S74 | ⬜ |

Functional tests live in `agents/master/tests/test_master_agent.py`.
