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

output "aws_role_arn" {
  description = "AWS IAM Role ARN for OIDC federation"
  value       = module.aws_oidc.role_arn
}

output "azure_workload_client_id" {
  description = "Client ID for Azure Workload Identity"
  value       = azurerm_user_assigned_identity.workload.client_id
}

output "gcp_provider_name" {
  description = "GCP Workload Identity Provider Name"
  value       = module.gcp_oidc.workload_identity_provider_name
}

output "gcp_service_account_email" {
  description = "GCP Service Account Email"
  value       = module.gcp_oidc.service_account_email
}

output "entra_client_id" {
  description = "Entra ID Application (Client) ID for the React SPA"
  value       = azuread_application.spa.client_id
}

output "entra_tenant_id" {
  description = "Azure Tenant ID"
  value       = var.azure_tenant_id
}
