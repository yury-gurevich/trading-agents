<!-- Agent: tooling | Role: live evidence -->
# Sprint 133 Service Bus SAS Live Proof

Date: 2026-07-22 AEST. Window check: the provisioning and flip ran outside the
22:25-00:30 UTC fleet window.

## Cap And Model

- Current Microsoft Learn Service Bus quotas page confirms the cap still applies:
  12 shared-access authorization rules per namespace, queue, or topic.
- Live namespace preflight found only the namespace-level `RootManageSharedAccessKey`
  before this sprint's scoped rules.
- Chosen model: entity-level topic authorization rules with separate Send/Listen
  rights. The measured plan produced 13 Service Bus targets, 33 topic rules, and
  `CAP_VIOLATIONS={}`.
- `master` has no measured Service Bus topic rights in the source plan; scoped
  delivery removes its Service Bus runtime env instead of inventing a permission.

## Provisioning

Commands, with all key material suppressed:

```powershell
uv run python scripts\sb_sas_plan.py
uv run python scripts\sb_provision_sas.py `
  --resource-group trading-agents `
  --namespace-name trading-agents-bus `
  --key-vault-name trading-agents-kv `
  --ensure-topics
```

Final provisioner output:

```text
{"rules": 33, "targets": 13}
```

Key Vault verification listed secret names only:

```text
servicebus-connection* secret name count: 26
```

Topic authorization-rule counts after provisioning:

```text
analysis.recommendations.ready=2
curator.reply=2
curator.requests=1
data.ready.market=1
data.request.market=1
execution.fills.ready=2
execution.reply=2
forecaster.requests=2
monitor.decisions.ready=2
operator.requests=1
orchestration.reply=2
portfolio.orders.ready=2
report.snapshot.ready=2
researcher.reply=2
researcher.requests=1
run.trigger=2
scan.candidates.ready=2
supervisor.requests=4
```

Note: the first provisioning attempt was interrupted after topic/rule creation
because Azure CLI Key Vault writes were too slow. The script was corrected to use
Key Vault REST writes with an Azure CLI bearer token, so generated connection
strings stay out of CLI argv and stdout. The idempotent retry completed as shown
above.

## Delivery Flip

Scoped delivery command:

```powershell
pwsh -NoProfile -File infra\deploy-agents.ps1 servicebus-flip
```

Result:

```text
[OK] master Service Bus env removed
[OK] scanner Service Bus secretref
[OK] analyst Service Bus secretref
[OK] portfolio-manager Service Bus secretref
[OK] execution Service Bus secretref
[OK] monitor Service Bus secretref
[OK] reporter Service Bus secretref
[OK] forecaster Service Bus secretref
[OK] operator Service Bus secretref
[OK] supervisor Service Bus secretref
[OK] curator Service Bus secretref
[OK] researcher Service Bus secretref
[OK] provider Service Bus secretref
[OK] dispatcher-cron Service Bus secretref
```

`az containerapp show` / `az containerapp job show` verified env names and
secretRefs only:

```text
master:NO_SERVICEBUS_ENV
scanner..provider: AZURE_SERVICEBUS_CONNECTION_STRING=secretref:servicebus-connection-string
scanner..provider: AZURE_SERVICEBUS_CONNECTION_STRINGS_JSON=secretref:servicebus-connection-strings
dispatcher-cron: AZURE_SERVICEBUS_CONNECTION_STRING=secretref:servicebus-connection-string
dispatcher-cron: AZURE_SERVICEBUS_CONNECTION_STRINGS_JSON=secretref:servicebus-connection-strings
```

Post-flip preflight:

```text
[OK] per-target Postgres DSNs: 14/14
[OK] Service Bus admin connection config
[OK] per-target Service Bus SAS strings: 13/13
[OK] GHCR images present: 14/14
```

Rollback:

```powershell
pwsh -NoProfile -File infra\deploy-agents.ps1 servicebus-flip -UseSharedServiceBusDsn
```

## LAW-02 Functionality Proof

Controlled canary command:

```powershell
uv run --extra azure python scripts\sb_sas_live_check.py `
  --resource-group trading-agents `
  --namespace-name trading-agents-bus
```

Result:

```text
{"correlation_id": "0be146ff-a36f-4454-9778-f34f998dc3fa", "created": ["s133-204137411c-request", "s133-204137411c-reply"], "least_authority_refusal": "ValueError", "positive_served": 1, "reply_type": "response", "request_id": "0be146ff-a36f-4454-9778-f34f998dc3fa", "revocation_refusal": "ServiceBusAuthenticationError", "run_id": "s133-204137411c"}
```

Interpretation:

- Positive path: a requester used a Send-only scoped identity on the request
  topic, a served worker used Listen-only on that topic, the served worker used
  Send-only on the reply topic, and the requester used Listen-only on the reply
  topic. `positive_served=1` and the reply was a `response`.
- Least authority: the requester Send identity was refused when used on the
  reply topic (`ValueError`, emitted as exception type only).
- Revocation: deleting the requester Send rule on the request topic locked out
  that identity (`ServiceBusAuthenticationError`, emitted as exception type
  only).
- Teardown: `az servicebus topic list` for `s133-*` returned no rows after the
  check.
- Fleet health after the canary revocation: all 13 Container Apps and
  `dispatcher-cron` reported provisioning state `Succeeded`.

Container-origin proof on production topics is left as an operator follow-up for
the next coordinated KEDA window. The controlled proof used the same
`AzureServiceBusBus` and `AzureServiceBusRequestConsumer` runtime primitives with
disposable canary topics to avoid injecting production messages.
