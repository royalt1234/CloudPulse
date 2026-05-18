# Remote state stored in Azure Blob Storage
# Pre-create with: scripts/bootstrap-state.sh
terraform {
  backend "azurerm" {
    resource_group_name  = "rg-cloudpulse-tfstate"
    storage_account_name = "cloudpulsetfstate" # Must be globally unique — change if taken
    container_name       = "tfstate"
    key                  = "cloudpulse.terraform.tfstate"
  }
}
