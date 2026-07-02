param(
  [string]$SubscriptionId = "5ef50a27-50a4-4d90-9695-da61b2309cf3",
  [string]$ResourceGroup = "trading-agents",
  [string]$VaultName = "trading-agents-kv",
  [string]$SeederClientId = $env:AZURE_SP_CLIENT_ID,
  [string]$Role = "Key Vault Secrets Officer"
)

$ErrorActionPreference = "Stop"

if (-not $SeederClientId) {
  throw "AZURE_SP_CLIENT_ID or -SeederClientId is required"
}

az account set --subscription $SubscriptionId
$scope = "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.KeyVault/vaults/$VaultName"
$objectId = az ad sp show --id $SeederClientId --query id -o tsv

if (-not $objectId) {
  throw "Service principal not found for client id $SeederClientId"
}

$existing = az role assignment list `
  --scope $scope `
  --assignee $objectId `
  --query "[?roleDefinitionName=='$Role'].id | [0]" `
  -o tsv

if ($existing) {
  Write-Host "Role already present: $Role on $VaultName for $objectId"
  exit 0
}

az role assignment create `
  --assignee-object-id $objectId `
  --assignee-principal-type ServicePrincipal `
  --role $Role `
  --scope $scope `
  -o json

Write-Host "Granted $Role on $VaultName in resource group $ResourceGroup to $objectId"
