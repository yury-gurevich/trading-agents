# Scenarios — the situations the ops realm must be ready for

You said you're bad at predicting these. So here's a starter catalogue, grouped by trigger.
Each becomes a **runbook** in the owning department. The point isn't to build them all now —
it's to *have the index* so none is a surprise (LAW-04) and each is recoverable (LAW-03).
This list is itself a proposal (LAW-01): add, split, reprioritise freely.

## Continuity / disaster
| Scenario | Owner dept | Hard parts | PNR? |
| --- | --- | --- | --- |
| Region goes down / must evacuate | Platform + GRC | move graph + fleet to new region | yes (cutover) |
| Data-residency law forces a jurisdiction move | GRC → Data + Platform | legal gate, full re-deploy elsewhere | yes |
| Graph store corrupted / lost | Data | restore from backup, replay | — |
| Aura trial expires (≈2026-06-29) | Data | cut over to permanent store before lapse | yes (instance delete) |
| Credential leaked / compromised | Security & IAM | rotate everything, revoke, re-grant | — |
| Accidental resource/RG deletion | Platform/GRC | restore from IaC + backup | (the delete was PNR) |

## Growth / change
| Scenario | Owner | Notes |
| --- | --- | --- |
| Custom domain instead of generic FQDN | Networking | cert + DNS + ingress rebind |
| Scale up (more load / more agents) | Platform | replica + size dials |
| Add a new agent / data feed | Release Eng | new image, new grant, new secret |
| Move Aura → self-host VM | Data | the permanent-store decision |

## Security / compliance
| Scenario | Owner | Notes |
| --- | --- | --- |
| Scheduled credential rotation | Security & IAM | PAT/key/keypair cadence |
| Access revocation (offboard a key) | Security & IAM | revoke + verify downstream still works |
| Audit request ("prove why data is here") | GRC | answered from ledger + ADRs (LAW-05) |
| Retention / data-retirement policy | GRC + Data | delete with proof, within law |

## Cost (the chargeable-era ones)
| Scenario | Owner | Notes |
| --- | --- | --- |
| Spend spike / budget cap hit | SRE + GRC | alert, identify, scale-to-zero / pause |
| Idle resources burning money | SRE | the "is anything left running?" sweep |
| Pre-action cost estimate before a deploy | Service Desk | the CONFIRM gate (LAW-04 / CM-01) |

## Operational / lifecycle
| Scenario | Owner | Notes |
| --- | --- | --- |
| Deploy fails mid-fleet (partial) | Release Eng | LAW-02 says partial = fail → roll back |
| GHCR `:latest` drifts from what's deployed | Release Eng | version-pin + reconcile |
| Backup/restore drill (prove recovery works) | Data + GRC | untested backup = broken backup |
| Decommission / retire the whole system | GRC | ordered teardown + final archive |
| Scheduled config backup | GRC + each dept | snapshot configs to a safe store |

## How to use this
1. Pick a scenario → it belongs to a department → write its runbook under that dept.
2. If it has an irreversible step → add it to `maintenance/points-of-no-return.md`.
3. If it spends or is irreversible → it needs a LAW-04 CONFIRM in `ta`.
4. Rank by *likelihood × cost-of-being-unprepared*; do the top few first.
