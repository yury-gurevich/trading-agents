// container-apps.bicep — Container Apps Environment for trading-agents.
// Creates a Log Analytics workspace and the managed Container Apps Environment
// that every Container App runs inside. Must be deployed BEFORE main.bicep.
//
// Run via:  pwsh infra/setup-container-apps.ps1
//
// Resources created:
//   • Log Analytics Workspace     (30-day retention; environment + app logs)
//   • Container Apps Environment  (Consumption; linked to Log Analytics)
//
// Outputs (written to .env by setup-container-apps.ps1):
//   AZURE_CA_ENV_NAME, AZURE_CA_ENV_ID, AZURE_CA_DEFAULT_DOMAIN,
//   AZURE_LA_WORKSPACE_ID

targetScope = 'resourceGroup'

@description('Azure region for all resources.')
param location string = 'australiaeast'

@description('Short prefix applied to every resource name.')
param prefix string = 'trading-agents'

// ── Log Analytics Workspace ───────────────────────────────────────────────────
// Container Apps requires a Log Analytics workspace for environment-level
// system logs and per-container stdout/stderr.

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${prefix}-logs'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018' // pay-per-GB; cheapest for low-volume workloads
    }
    retentionInDays: 30
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// ── Container Apps Environment ────────────────────────────────────────────────
// Consumption plan — scale-to-zero, pay-per-use. One environment covers all
// agents; individual Container Apps are created via deploy.sh / az CLI.

resource caEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${prefix}-env'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────

@description('Container Apps Environment name — pass to az containerapp create/update --environment.')
output caEnvName string = caEnv.name

@description('Container Apps Environment resource ID — used as environmentId in child Container Apps.')
output caEnvId string = caEnv.id

@description('Default domain for apps in this environment (e.g. <hash>.<region>.azurecontainerapps.io).')
output caDefaultDomain string = caEnv.properties.defaultDomain

@description('Log Analytics workspace customer ID — for diagnostics and querying.')
output logAnalyticsWorkspaceId string = logAnalytics.properties.customerId
