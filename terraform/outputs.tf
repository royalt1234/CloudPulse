output "azure_dashboard_url" {
  description = "CloudPulse dashboard URL on Azure (AKS)"
  value       = "http://${trimspace(data.local_file.azure_url.content)}"
}

output "aks_cluster_name" {
  description = "AKS cluster name"
  value       = module.aks.cluster_name
}

output "acr_server" {
  description = "ACR login server"
  value       = module.acr.login_server
}

output "azure_workload_client_id" {
  description = "Client ID for Azure Workload Identity"
  value       = azurerm_user_assigned_identity.workload.client_id
}

output "entra_client_id" {
  description = "Entra ID Application (Client) ID for the React SPA"
  value       = azuread_application.spa.client_id
}

output "entra_tenant_id" {
  description = "Azure Tenant ID"
  value       = var.azure_tenant_id
  sensitive   = true
}
