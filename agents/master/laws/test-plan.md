# `Master` — Law Test-Plan

**Prefix:** `MST` · **status:** LOCKED v1.2 · **aligned with:** laws.md LOCKED v1.2

| Clause | Description | Test | Status |
| --- | --- | --- | --- |
| MST-IDN-01 | `start()` writes Session node | `test_start_writes_session_node` | 🟩 |
| MST-STA-01 | `session_id` None before start, non-None after | `test_start_exposes_session_id` | 🟩 |
| MST-OUT-01 | EHLO → ACTIVATE with matching fields | `test_activate_returns_activate_message` | 🟩 |
| MST-STA-02 | `activate()` writes `AgentInstance` with state=active | `test_activate_writes_agent_instance_node` | 🟩 |
| MST-STA-03 | `activate()` writes one `CapabilityGrant` per capability | `test_activate_writes_capability_grant_nodes` | 🟩 |
| MST-IDM-01 | Two EHLO of same type → distinct instance IDs | `test_activate_second_instance_of_same_type_gets_unique_id` | 🟩 |
| MST-NEV-01 | Unknown agent_type rejected; no graph write | `test_activate_unknown_agent_type_raises` | 🟩 |
| MST-NEV-06 | Master never hands over a pack-declared credential until its applicable credential test has either passed live or has a fresh costly-pass cache entry; a failed required credential test refuses activation and writes no `AgentInstance` | `test_required_http_status_401_refuses_activation`; `test_credential_probe_body.py::test_a_drained_key_refuses_activation` (the 400 a credit-exhausted account returns, DRIFT-058) | 🟩 |
| MST-OUT-02 | `drain()` returns `DRAINMessage` | `test_drain_returns_drain_message` | 🟩 |
| MST-STA-04 | `drain()` writes `drain_reason` to AgentInstance | `test_drain_marks_instance_in_graph` | 🟩 |
| MST-NEV-02 | `drain` on unknown instance_id raises `KeyError` | `test_drain_unknown_instance_raises` | 🟩 |
| MST-FAIL-04 | Credential-test transport failures are visible faults, not credential failures; activation may proceed, no pass is cached, and required failures are decided from credential rejection; optional credential failures do not block activation | `test_transport_failure_faults_without_blocking_or_caching`; `test_optional_credential_failure_is_recorded_without_blocking` | 🟩 |
| MST-SEC-04 | Credential-test evidence never contains raw secret values; activation records, escalations, faults, and refusal exceptions name credential/test labels and sanitized causes only | `test_secret_values_never_appear_in_credential_probe_records` | 🟩 |
| MST-DEP-04 | A credential-bearing pack must supply a non-empty credential-test declaration at startup; missing declarations, empty declarations, and unknown probe kinds are rejected loudly instead of being treated as zero successful tests | `test_missing_credential_tests_for_secret_pack_is_loud`; `test_unknown_probe_kind_is_refused_loudly` | 🟩 |
| MST-OBS-04 | Successful activation records applicable credential-test evidence on the `AgentInstance`: live-tested names, live-passed names, cached-pass names, optional failures, and transport failures | `test_activation_records_tested_credentials`; `test_optional_credential_failure_is_recorded_without_blocking`; `test_transport_failure_faults_without_blocking_or_caching` | 🟩 |
| MST-IDN-02 | Master exclusively owns listed graph labels | architecture / import-linter | ⬜ |
| MST-IDN-03 | Master sole Key Vault accessor | deferred S74 | ⬜ |
| MST-IN-03 | Malformed EHLO → no graph write, fault emitted | integration test (deferred) | ⬜ |
| MST-NEV-03 | No trading logic | static (contract) | ⬜ |
| MST-NEV-04 | Private key never distributed | deferred S74 | ⬜ |
| MST-SEC-01 | RSA signature on ACTIVATE | deferred S74 | ⬜ |
| MST-DEP-01 | Graph reachability guard before startup failure | integration (deferred) | ⬜ |
| MST-DEP-02 | Key Vault credential resolution | deferred S74 | ⬜ |
| MST-IN-01 | activate accepts EHLOMessage fields, rejects unknown agent_type with ValueError | _tbd_ | ⬜ |
| MST-IN-02 | drain accepts DRAINMessage, requires known AgentInstance, and raises KeyError for unknown IDs | _tbd_ | ⬜ |
| MST-TRG-01 | activate is triggered by EHLO on the handshake queue | _tbd_ | ⬜ |
| MST-TRG-02 | drain is triggered by operator/supervisor or master's crash-recovery path | _tbd_ | ⬜ |
| MST-OUT-03 | start() writes a Session node with started_at for crash recovery | _tbd_ | ⬜ |
| MST-IDM-02 | restart reads existing Session nodes before writing a new Session | _tbd_ | ⬜ |
| MST-ORD-01 | start() must precede activate(); activate without a live session cannot link to session_id | _tbd_ | ⬜ |
| MST-ORD-02 | master startup and live handshake queue precede trading-agent EHLO | _tbd_ | ⬜ |
| MST-FAIL-01 | graph unavailable on activate is faulted and re-raised without acknowledging EHLO | _tbd_ | ⬜ |
| MST-FAIL-02 | graph unavailable on drain is faulted and re-raised while the agent continues running | _tbd_ | ⬜ |
| MST-FAIL-03 | single-point-of-failure mitigation is a risk charter: thin master, state in Postgres, and platform restart are architectural claims, not an agent-local observation | Charter: no single functional observation can prove the RISK-1 mitigation envelope; failures are covered by the narrower FAIL rows. | 📜 |
| MST-TYP-01 | EHLOMessage, ACTIVATEMessage, DRAINMessage, and AgentState match contracts/master.py | _tbd_ | ⬜ |
| MST-TYP-02 | ACTIVATE capability_grants is a JSON-safe map and never contains product names | _tbd_ | ⬜ |
| MST-SEC-02 | each agent receives only credentials for declared capability_grants, never the full .env | _tbd_ | ⬜ |
| MST-SEC-03 | DEFAULT_GRANTS is the authoritative privilege table and cannot be changed by runtime config | _tbd_ | ⬜ |
| MST-OBS-01 | every activate() writes a queryable AgentInstance node | _tbd_ | ⬜ |
| MST-OBS-02 | every drain() records drain_reason on AgentInstance | _tbd_ | ⬜ |
| MST-OBS-03 | graph and Key Vault errors reach the fault channel through fault_boundary | _tbd_ | ⬜ |
| MST-PERF-01 | activate() writes one AgentInstance plus N CapabilityGrant nodes and meets the stated p99 budget | _tbd_ | ⬜ |
| MST-NEV-05 | master has no dependency on trading-agent code | import-linter: "Agents may not import one another" | 🧱 |
| MST-DEP-03 | master depends on no trading-agent code; knowledge stays in DEFAULT_GRANTS and AgentDefinition rows | import-linter: "Agents may not import one another" | 🧱 |

Functional tests live in `agents/master/tests/test_master_agent.py`.
