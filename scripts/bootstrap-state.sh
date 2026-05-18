#!/usr/bin/env bash
# =============================================================
# bootstrap-state.sh
# Run ONCE before 'terraform init' to create the Azure Blob
# Storage backend for Terraform remote state.
# Usage: bash scripts/bootstrap-state.sh <subscription-id>
# =============================================================
set -euo pipefail

SUBSCRIPTION_ID="${1:?Usage: $0 <azure-subscription-id>}"
RG="rg-cloudpulse-tfstate"
SA="cloudpulsetfstate"   # Must be globally unique
CONTAINER="tfstate"
LOCATION="uksouth"

echo "Creating Terraform remote state backend..."
az account set --subscription "$SUBSCRIPTION_ID"
az group create --name "$RG" --location "$LOCATION"
az storage account create \
  --name "$SA" \
  --resource-group "$RG" \
  --location "$LOCATION" \
  --sku Standard_LRS \
  --encryption-services blob
az storage container create \
  --name "$CONTAINER" \
  --account-name "$SA"

echo ""
echo "✓ Remote state backend ready."
echo "  Update terraform/backend.tf with storage_account_name = \"$SA\" if different."
echo "  Then run: cd terraform && terraform init"
