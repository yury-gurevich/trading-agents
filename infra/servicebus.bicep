// trading-agents command bus — Azure Service Bus (ADR-0005: event-driven pub/sub + claim-check)
// Provisions: a Service Bus namespace (Standard — topics/subscriptions + dead-letter) for the
// distributed agent serve transport (S100). The trade-spine DATA path stays on the graph (DL-08);
// this bus carries capability requests + `ready:<ref>` events between containers.
// Target: trading-agents RG, australiaeast, payg-@Office subscription (5ef50a27)
//
// Deploy:
//   az deployment group create \
//     --subscription 5ef50a27-50a4-4d90-9695-da61b2309cf3 \
//     --resource-group trading-agents \
//     --template-file infra/servicebus.bicep
//
// After deploy, fetch the connection string (a secret — do NOT commit it; it goes to .env / Key Vault):
//   az servicebus namespace authorization-rule keys list \
//     --resource-group trading-agents --namespace-name trading-agents-bus \
//     --name RootManageSharedAccessKey --query primaryConnectionString -o tsv

@description('Azure region for all resources.')
param location string = 'australiaeast'

@description('Service Bus namespace name (globally unique; must NOT end in "-sb" or "-mgmt").')
param namespaceName string = 'trading-agents-bus'

// ── Service Bus namespace (Standard: topics/subscriptions + dead-letter) ──────
// Basic tier only supports queues; topics/subscriptions (ADR-0005) require Standard.

resource sb 'Microsoft.ServiceBus/namespaces@2022-10-01-preview' = {
  name: namespaceName
  location: location
  sku: {
    name: 'Standard'
    tier: 'Standard'
  }
  properties: {
    minimumTlsVersion: '1.2'
  }
}

// ── A probe topic + subscription so the connection string can be smoke-tested ─
// One live send->receive round-trip validates the namespace + connection string
// (tested-before-use, DL-36). The real per-capability topics are created by S100
// at bind time. Dead-lettering-on-expiry mirrors the S100 ack policy.

resource readyTopic 'Microsoft.ServiceBus/namespaces/topics@2022-10-01-preview' = {
  parent: sb
  name: 'ready'
  properties: {
    defaultMessageTimeToLive: 'P14D'
    enableBatchedOperations: true
  }
}

resource probeSub 'Microsoft.ServiceBus/namespaces/topics/subscriptions@2022-10-01-preview' = {
  parent: readyTopic
  name: 'probe'
  properties: {
    deadLetteringOnMessageExpiration: true
    maxDeliveryCount: 10
    defaultMessageTimeToLive: 'P14D'
  }
}

// ── Outputs (non-secret; fetch the connection string via az, see header) ──────

@description('Service Bus namespace name.')
output namespaceName string = sb.name

@description('Service Bus namespace AMQPS endpoint.')
output serviceBusEndpoint string = sb.properties.serviceBusEndpoint
