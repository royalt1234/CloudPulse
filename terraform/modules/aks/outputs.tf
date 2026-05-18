output "cluster_name" {
  value = azurerm_kubernetes_cluster.main.name
}
output "resource_group_name" {
  value = azurerm_resource_group.main.name
}
output "kube_config_raw" {
  value     = azurerm_kubernetes_cluster.main.kube_config_raw
  sensitive = true
}
output "host" {
  value = azurerm_kubernetes_cluster.main.kube_config[0].host
}
output "client_certificate" {
  value     = azurerm_kubernetes_cluster.main.kube_config[0].client_certificate
  sensitive = true
}
output "client_key" {
  value     = azurerm_kubernetes_cluster.main.kube_config[0].client_key
  sensitive = true
}
output "cluster_ca_certificate" {
  value     = azurerm_kubernetes_cluster.main.kube_config[0].cluster_ca_certificate
  sensitive = true
}
output "kubelet_identity_id" {
  value = azurerm_kubernetes_cluster.main.kubelet_identity[0].object_id
}
output "oidc_issuer_url" {
  value = azurerm_kubernetes_cluster.main.oidc_issuer_url
}
