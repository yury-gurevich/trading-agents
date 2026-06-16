// trading-agents observability stack — Azure Managed Prometheus + Grafana
// Deploys into an existing resource group.
//
// Resources created:
//   • Azure Monitor Workspace  (managed Prometheus storage + query)
//   • Azure Managed Grafana    (pre-wired to the Monitor workspace)
//   • Azure Container Registry (stores trading-agents + prometheus images)
//   • User-assigned Managed Identity (lets Prometheus remote_write to Monitor)
//   • Role assignment: Monitoring Metrics Publisher on the workspace
//   • Container Apps Environment
//   • Container App: trading-agents + prometheus sidecar (same pod)

targetScope = 'resourceGroup'

@description('Azure region for all resources.')
param location string = 'australiaeast'

@description('Short prefix applied to every resource name.')
param prefix string = 'trading-agents'

@description('Container image tag to deploy.')
param imageTag string = 'latest'

// ── Azure Monitor Workspace ───────────────────────────────────────────────────

resource monitorWorkspace 'Microsoft.Monitor/accounts@2023-04-03' = {
  name: '${prefix}-monitor'
  location: location
}

// ── Azure Managed Grafana ─────────────────────────────────────────────────────

resource grafana 'Microsoft.Dashboard/grafana@2023-09-01' = {
  name: '${prefix}-grafana'
  location: location
  sku: {
    name: 'Standard'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    publicNetworkAccess: 'Enabled'
    grafanaIntegrations: {
      azureMonitorWorkspaceIntegrations: [
        {
          azureMonitorWorkspaceResourceId: monitorWorkspace.id
        }
      ]
    }
  }
}

// ── Grafana can read from the Monitor workspace ───────────────────────────────

resource grafanaMonitoringReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  // Monitoring Reader (43d0d8ad-25c1-4cac-a5cb-fe654b1eec97)
  name: guid(monitorWorkspace.id, grafana.id, 'MonitoringReader')
  scope: monitorWorkspace
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '43d0d8ad-25c1-4cac-a5cb-fe654b1eec97'
    )
    principalId: grafana.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// ── Azure Container Registry ──────────────────────────────────────────────────

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  // ACR names must be globally unique, alphanumeric only, 5-50 chars
  name: replace('${prefix}acr', '-', '')
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

// ── User-assigned Managed Identity for Prometheus remote_write ────────────────

resource prometheusIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${prefix}-prometheus-id'
  location: location
}

resource metricsPublisher 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  // Monitoring Metrics Publisher (3913510d-42f4-4e42-8a64-420c390055eb)
  name: guid(monitorWorkspace.id, prometheusIdentity.id, 'MetricsPublisher')
  scope: monitorWorkspace
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '3913510d-42f4-4e42-8a64-420c390055eb'
    )
    principalId: prometheusIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// ── Container Apps Environment ────────────────────────────────────────────────
// Created by infra/container-apps.bicep (run setup-container-apps.ps1 first).

resource caEnv 'Microsoft.App/managedEnvironments@2024-03-01' existing = {
  name: '${prefix}-env'
}

// ── Container App: trading-agents + prometheus sidecar ───────────────────────
//
// Both containers share the same pod so Prometheus can scrape localhost:8000.

resource tradingApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: prefix
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${prometheusIdentity.id}': {}
    }
  }
  properties: {
    environmentId: caEnv.id
    configuration: {
      // No external ingress — this app does not expose a public HTTP endpoint.
      // Prometheus metrics are consumed internally by the sidecar.
      registries: [
        {
          server: acr.properties.loginServer
          username: acr.listCredentials().username
          passwordSecretRef: 'acr-password' // pragma: allowlist secret
        }
      ]
      secrets: [
        {
          name: 'acr-password'
          value: acr.listCredentials().passwords[0].value
        }
        {
          name: 'neo4j-password'
          // Set via: az containerapp secret set --name trading-agents --secret-name neo4j-password --value <value>
          value: 'REPLACE_WITH_NEO4J_PASSWORD'
        }
      ]
    }
    template: {
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
      containers: [
        {
          name: 'trading-agents'
          image: '${acr.properties.loginServer}/trading-agents:${imageTag}'
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            { name: 'METRICS_PORT', value: '8000' }
            { name: 'NEO4J_PASSWORD', secretRef: 'neo4j-password' } // pragma: allowlist secret
          ]
        }
        {
          name: 'prometheus'
          image: '${acr.properties.loginServer}/prometheus-trading:${imageTag}'
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          env: [
            {
              name: 'REMOTE_WRITE_URL'
              value: monitorWorkspace.properties.metrics.prometheusQueryEndpoint
            }
            {
              name: 'MANAGED_IDENTITY_CLIENT_ID'
              value: prometheusIdentity.properties.clientId
            }
          ]
        }
      ]
    }
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────

@description('Grafana workspace URL — open this in your browser.')
output grafanaEndpoint string = 'https://${grafana.properties.endpoint}'

@description('Azure Monitor Workspace Prometheus query endpoint.')
output prometheusQueryEndpoint string = monitorWorkspace.properties.metrics.prometheusQueryEndpoint

@description('Remote-write endpoint for Prometheus → Azure Monitor.')
output remoteWriteUrl string = '${monitorWorkspace.properties.metrics.prometheusQueryEndpoint}/api/v1/write'

@description('ACR login server — used by deploy.sh to tag and push images.')
output acrLoginServer string = acr.properties.loginServer

@description('Prometheus managed identity client ID — used by the Prometheus sidecar container.')
output managedIdentityClientId string = prometheusIdentity.properties.clientId

@description('ACR login server for docker push.')
output acrLoginServer string = acr.properties.loginServer

@description('Managed identity client ID (used in prometheus.yml azuread block).')
output managedIdentityClientId string = prometheusIdentity.properties.clientId
