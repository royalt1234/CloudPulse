variable "project_name" {
  type        = string
  description = "Project name prefix for all resources"
}
variable "azure_subscription_id" {
  type        = string
  description = "Azure subscription ID"
  sensitive   = true
}
variable "azure_tenant_id" {
  type        = string
  description = "Azure Tenant ID"
  sensitive   = true
}
variable "azure_location" {
  type        = string
  description = "Azure region"
}
variable "kubernetes_version" {
  type        = string
  description = "Kubernetes version for AKS"
}
variable "azure_node_vm_size" {
  type        = string
  description = "Azure VM size for AKS nodes"
}
variable "node_count" {
  type        = number
  description = "Number of worker nodes per cluster"
}
variable "image_tag" {
  type        = string
  description = "Docker image tag to deploy"
  default     = "latest"
}
