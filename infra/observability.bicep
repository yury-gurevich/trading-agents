// trading-agents observability stack
// Provisions: Log Analytics workspace, Application Insights, Data Collection Endpoint, Data Collection Rule
// Target: trading-agents-prod RG, australiaeast, payg-@Office subscription (5ef50a27)
// Created: 2026-06-19 (migrated from traiding-system RG / payg / australiasoutheast)
//
// Deploy:
//   az deployment group create \
//     --subscription 5ef50a27-50a4-4d90-9695-da61b2309cf3 \
//     --resource-group trading-agents-prod \
//     --template-file infra/observability.bicep

@description('Azure region for all resources')
param location string = 'australiaeast'

@description('Log retention in days')
param lawRetentionDays int = 30

@description('App Insights retention in days')
param appiRetentionDays int = 90

// ── Log Analytics Workspace ──────────────────────────────────────────────────

resource law 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: 'law-trading-agents'
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: lawRetentionDays
    workspaceCapping: { dailyQuotaGb: -1 }
  }
}

// ── Application Insights (workspace-based) ───────────────────────────────────

resource appi 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appi-trading-agents'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: law.id
    RetentionInDays: appiRetentionDays
  }
}

// ── Data Collection Endpoint ─────────────────────────────────────────────────

resource dce 'Microsoft.Insights/dataCollectionEndpoints@2022-06-01' = {
  name: 'dce-trading-agents-logs'
  location: location
  properties: {
    networkAcls: { publicNetworkAccess: 'Enabled' }
  }
}

// ── Data Collection Rule ─────────────────────────────────────────────────────

resource dcr 'Microsoft.Insights/dataCollectionRules@2022-06-01' = {
  name: 'dcr-trading-agents-execution'
  location: location
  kind: 'Direct'
  properties: {
    dataCollectionEndpointId: dce.id
    streamDeclarations: {
      'Custom-ObservabilityEvents': {
        columns: [
          { name: 'TimeGenerated', type: 'datetime' }
          { name: 'PipelineRunId',  type: 'string' }
          { name: 'CorrelationId',  type: 'string' }
          { name: 'AgentName',      type: 'string' }
          { name: 'Component',      type: 'string' }
          { name: 'EventType',      type: 'string' }
          { name: 'RunStage',       type: 'string' }
          { name: 'Outcome',        type: 'string' }
          { name: 'Message',        type: 'string' }
          { name: 'Details',        type: 'string' }
          { name: 'Service',        type: 'string' }
          { name: 'ServiceVersion', type: 'string' }
          { name: 'Environment',    type: 'string' }
          { name: 'DurationMs',     type: 'real' }
          { name: 'Retryable',      type: 'boolean' }
          { name: 'ErrorCode',      type: 'string' }
          { name: 'ErrorClass',     type: 'string' }
          { name: 'Provider',       type: 'string' }
          { name: 'Ticker',         type: 'string' }
          { name: 'TradeId',        type: 'string' }
          { name: 'IncidentKey',    type: 'string' }
        ]
      }
      'Custom-HealthSnapshots': {
        columns: [
          { name: 'TimeGenerated',           type: 'datetime' }
          { name: 'Status',                  type: 'string' }
          { name: 'Scheduler',               type: 'string' }
          { name: 'PipelineState',           type: 'string' }
          { name: 'AutomationPosture',       type: 'string' }
          { name: 'EffectiveOperatingMode',  type: 'string' }
          { name: 'CapitalMode',             type: 'string' }
          { name: 'ActiveIncidentCount',     type: 'long' }
          { name: 'RequiresOperatorAction',  type: 'boolean' }
          { name: 'Details',                 type: 'string' }
          { name: 'PipelineRunId',           type: 'string' }
          { name: 'CorrelationId',           type: 'string' }
        ]
      }
      'Custom-Incidents': {
        columns: [
          { name: 'TimeGenerated',   type: 'datetime' }
          { name: 'IncidentId',      type: 'long' }
          { name: 'IncidentKey',     type: 'string' }
          { name: 'Component',       type: 'string' }
          { name: 'Severity',        type: 'string' }
          { name: 'Status',          type: 'string' }
          { name: 'Summary',         type: 'string' }
          { name: 'Reason',          type: 'string' }
          { name: 'Details',         type: 'string' }
          { name: 'OccurrenceCount', type: 'long' }
          { name: 'Transition',      type: 'string' }
          { name: 'PipelineRunId',   type: 'string' }
          { name: 'CorrelationId',   type: 'string' }
        ]
      }
      'Custom-TradingIncidents': {
        columns: [
          { name: 'TimeGenerated',   type: 'datetime' }
          { name: 'IncidentId',      type: 'long' }
          { name: 'IncidentKey',     type: 'string' }
          { name: 'Component',       type: 'string' }
          { name: 'Severity',        type: 'string' }
          { name: 'Status',          type: 'string' }
          { name: 'Summary',         type: 'string' }
          { name: 'Reason',          type: 'string' }
          { name: 'Details',         type: 'string' }
          { name: 'OccurrenceCount', type: 'long' }
          { name: 'Transition',      type: 'string' }
          { name: 'PipelineRunId',   type: 'string' }
          { name: 'CorrelationId',   type: 'string' }
        ]
      }
      'Custom-TradingExecutionTimeline': {
        columns: [
          { name: 'TimeGenerated',   type: 'datetime' }
          { name: 'PipelineRunId',   type: 'string' }
          { name: 'CorrelationId',   type: 'string' }
          { name: 'AgentName',       type: 'string' }
          { name: 'Component',       type: 'string' }
          { name: 'EventType',       type: 'string' }
          { name: 'RunStage',        type: 'string' }
          { name: 'Outcome',         type: 'string' }
          { name: 'Message',         type: 'string' }
          { name: 'TradeId',         type: 'string' }
          { name: 'Ticker',          type: 'string' }
          { name: 'IncidentKey',     type: 'string' }
          { name: 'Details',         type: 'string' }
          { name: 'Service',         type: 'string' }
          { name: 'ServiceVersion',  type: 'string' }
          { name: 'Environment',     type: 'string' }
          { name: 'DurationMs',      type: 'real' }
          { name: 'Retryable',       type: 'boolean' }
          { name: 'ErrorCode',       type: 'string' }
          { name: 'ErrorClass',      type: 'string' }
          { name: 'Sequence',        type: 'long' }
        ]
      }
      'Custom-TradingStructuredLogs': {
        columns: [
          { name: 'TimeGenerated',   type: 'datetime' }
          { name: 'Level',           type: 'string' }
          { name: 'PipelineRunId',   type: 'string' }
          { name: 'CorrelationId',   type: 'string' }
          { name: 'AgentName',       type: 'string' }
          { name: 'Component',       type: 'string' }
          { name: 'EventType',       type: 'string' }
          { name: 'Message',         type: 'string' }
          { name: 'Details',         type: 'string' }
          { name: 'ErrorCode',       type: 'string' }
          { name: 'ErrorClass',      type: 'string' }
          { name: 'Retryable',       type: 'boolean' }
          { name: 'Provider',        type: 'string' }
          { name: 'Ticker',          type: 'string' }
          { name: 'TradeId',         type: 'string' }
          { name: 'IncidentKey',     type: 'string' }
          { name: 'Stack',           type: 'string' }
          { name: 'Exception',       type: 'string' }
          { name: 'Service',         type: 'string' }
          { name: 'ServiceVersion',  type: 'string' }
          { name: 'Environment',     type: 'string' }
          { name: 'Host',            type: 'string' }
          { name: 'DurationMs',      type: 'real' }
        ]
      }
      'Custom-TradingTradeLifecycle': {
        columns: [
          { name: 'TimeGenerated',      type: 'datetime' }
          { name: 'TradeId',            type: 'string' }
          { name: 'RecommendationId',   type: 'string' }
          { name: 'Ticker',             type: 'string' }
          { name: 'LifecycleStage',     type: 'string' }
          { name: 'EventType',          type: 'string' }
          { name: 'Outcome',            type: 'string' }
          { name: 'ApprovalQueueId',    type: 'string' }
          { name: 'ExecutionEventId',   type: 'long' }
          { name: 'BrokerOrderId',      type: 'string' }
          { name: 'PositionId',         type: 'long' }
          { name: 'Details',            type: 'string' }
          { name: 'PipelineRunId',      type: 'string' }
          { name: 'CorrelationId',      type: 'string' }
        ]
      }
      'Custom-TradingDependencyHealth': {
        columns: [
          { name: 'TimeGenerated',   type: 'datetime' }
          { name: 'DependencyName',  type: 'string' }
          { name: 'Provider',        type: 'string' }
          { name: 'Status',          type: 'string' }
          { name: 'LatencyMs',       type: 'real' }
          { name: 'ErrorClass',      type: 'string' }
          { name: 'ErrorMessage',    type: 'string' }
          { name: 'Details',         type: 'string' }
          { name: 'PipelineRunId',   type: 'string' }
          { name: 'CorrelationId',   type: 'string' }
          { name: 'Component',       type: 'string' }
        ]
      }
      'Custom-TradingRecoveryActions': {
        columns: [
          { name: 'TimeGenerated',      type: 'datetime' }
          { name: 'RecoveryActionId',   type: 'long' }
          { name: 'IncidentId',         type: 'long' }
          { name: 'IncidentKey',        type: 'string' }
          { name: 'ActionType',         type: 'string' }
          { name: 'Status',             type: 'string' }
          { name: 'Summary',            type: 'string' }
          { name: 'Details',            type: 'string' }
          { name: 'PipelineRunId',      type: 'string' }
          { name: 'CorrelationId',      type: 'string' }
          { name: 'Component',          type: 'string' }
        ]
      }
    }
    dataFlows: [
      { streams: ['Custom-ObservabilityEvents'],       destinations: ['laMain'], outputStream: 'Custom-TradingObservabilityEvents_CL', transformKql: 'source' }
      { streams: ['Custom-HealthSnapshots'],            destinations: ['laMain'], outputStream: 'Custom-TradingHealthSnapshots_CL',    transformKql: 'source' }
      { streams: ['Custom-Incidents'],                  destinations: ['laMain'], outputStream: 'Custom-TradingIncidents_CL',           transformKql: 'source' }
      { streams: ['Custom-TradingIncidents'],           destinations: ['laMain'], outputStream: 'Custom-TradingIncidents_CL',           transformKql: 'source' }
      { streams: ['Custom-TradingExecutionTimeline'],   destinations: ['laMain'], outputStream: 'Custom-TradingExecutionTimeline_CL',   transformKql: 'source' }
      { streams: ['Custom-TradingStructuredLogs'],      destinations: ['laMain'], outputStream: 'Custom-TradingStructuredLogs_CL',      transformKql: 'source' }
      { streams: ['Custom-TradingTradeLifecycle'],      destinations: ['laMain'], outputStream: 'Custom-TradingTradeLifecycle_CL',      transformKql: 'source' }
      { streams: ['Custom-TradingDependencyHealth'],    destinations: ['laMain'], outputStream: 'Custom-TradingDependencyHealth_CL',    transformKql: 'source' }
      { streams: ['Custom-TradingRecoveryActions'],     destinations: ['laMain'], outputStream: 'Custom-TradingRecoveryActions_CL',     transformKql: 'source' }
    ]
    destinations: {
      logAnalytics: [
        {
          name: 'laMain'
          workspaceResourceId: law.id
        }
      ]
    }
  }
}

// ── Outputs (paste into .env) ────────────────────────────────────────────────

output appiConnectionString string = appi.properties.ConnectionString
output lawWorkspaceId string = law.properties.customerId
output dceIngestionEndpoint string = dce.properties.logsIngestion.endpoint
output dceImmutableId string = dce.properties.immutableId
output dcrImmutableId string = dcr.properties.immutableId
