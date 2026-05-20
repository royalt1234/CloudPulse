locals {
  common_tags = {
    Project     = var.project_name
    Environment = "demo"
    ManagedBy   = "Terraform"
  }
  acr_name = replace("${var.project_name}acr${substr(var.azure_subscription_id, 0, 8)}", "-", "")
}

# ── Phase 1: Azure Infrastructure ────────────────────────────

module "aks" {
  source = "./modules/aks"

  cluster_name        = "${var.project_name}-aks"
  resource_group_name = "rg-${var.project_name}-prod"
  location            = var.azure_location
  kubernetes_version  = var.kubernetes_version
  node_vm_size        = var.azure_node_vm_size
  node_count          = var.node_count
  tags                = local.common_tags
}

module "acr" {
  source = "./modules/acr"

  registry_name       = local.acr_name
  resource_group_name = module.aks.resource_group_name
  location            = var.azure_location
  aks_principal_id    = module.aks.kubelet_identity_id
  tags                = local.common_tags

  depends_on = [module.aks]
}

# ── Phase 2: Build & Push Docker Images ──────────────────────

resource "null_resource" "build_and_push" {
  depends_on = [module.aks, module.acr]

  triggers = {
    image_tag  = var.image_tag
    acr_server = module.acr.login_server
  }

  provisioner "local-exec" {
    working_dir = "${path.module}/../"
    command     = "bash scripts/deploy.sh"
    environment = {
      PROJECT_NAME    = var.project_name
      IMAGE_TAG       = var.image_tag
      AZURE_LOCATION  = var.azure_location
      AZURE_RG        = module.aks.resource_group_name
      AKS_NAME        = module.aks.cluster_name
      ACR_SERVER      = module.acr.login_server
      ACR_USERNAME    = module.acr.admin_username
      ACR_PASSWORD    = module.acr.admin_password
      AZURE_CLIENT_ID = azurerm_user_assigned_identity.workload.client_id
      ENTRA_CLIENT_ID = azuread_application.spa.client_id
      ENTRA_TENANT_ID = var.azure_tenant_id
    }
  }
}

# ── Phase 3: Read Output URL (written by deploy.sh) ──────────
# Pre-create placeholder file so the data source doesn't fail on first apply.
resource "null_resource" "url_placeholder" {
  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    command     = "echo PENDING > '${path.module}/../.azure_url'"
  }
}
# ── Phase 4: Azure Workload Identity ─────────────────────────
resource "azurerm_user_assigned_identity" "workload" {
  name                = "${var.project_name}-workload-id"
  resource_group_name = module.aks.resource_group_name
  location            = var.azure_location
}

resource "azurerm_federated_identity_credential" "workload" {
  name                = "${var.project_name}-fic"
  resource_group_name = module.aks.resource_group_name
  audience            = ["api://AzureADTokenExchange"]
  issuer              = module.aks.oidc_issuer_url
  parent_id           = azurerm_user_assigned_identity.workload.id
  subject             = "system:serviceaccount:cloudpulse:cloudpulse-sa"
}

resource "azurerm_role_assignment" "cost_reader" {
  scope                = "/subscriptions/${var.azure_subscription_id}"
  role_definition_name = "Cost Management Reader"
  principal_id         = azurerm_user_assigned_identity.workload.principal_id
}

resource "azurerm_role_assignment" "monitoring_reader" {
  scope                = "/subscriptions/${var.azure_subscription_id}"
  role_definition_name = "Monitoring Reader"
  principal_id         = azurerm_user_assigned_identity.workload.principal_id
}
data "local_file" "azure_url" {
  filename   = "${path.module}/../.azure_url"
  depends_on = [null_resource.build_and_push, null_resource.url_placeholder]
}

# ── Phase 5: Entra ID App Registration ───────────────────────
data "azuread_client_config" "current" {}

resource "azuread_application" "spa" {
  display_name     = "${var.project_name}-spa"
  owners           = [data.azuread_client_config.current.object_id]
  sign_in_audience = "AzureADMyOrg"

  single_page_application {
    # Allow localhost for development. Production redirect URI is added dynamically after deployment.
    redirect_uris = [
      "http://localhost:3000/",
      "http://localhost:5173/",
      "https://20.54.205.56/",
      "https://cloudpulse.itclabs.live/",
      "https://www.cloudpulse.itclabs.live/"
    ]
  }

  required_resource_access {
    resource_app_id = "00000003-0000-0000-c000-000000000000" # Microsoft Graph

    resource_access {
      id   = "e1fe6dd8-ba39-40d6-84d0-0f30c4976e3d" # User.Read
      type = "Scope"
    }
  }
}
