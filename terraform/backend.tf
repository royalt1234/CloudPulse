# Remote state stored in Azure Blob Storage
# Pre-create with: scripts/bootstrap-state.sh
terraform {
  backend "azurerm" {
    resource_group_name  = "rg-cloudpulse-tfstate"
    storage_account_name = "cloudpulse49b706" # Must be globally unique — update per subscription if needed
    container_name       = "tfstate"
    key                  = "cloudpulse.terraform.tfstate"
  }
}
