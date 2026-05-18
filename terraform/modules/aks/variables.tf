variable "cluster_name" {
  type = string
}
variable "resource_group_name" {
  type = string
}
variable "location" {
  type    = string
  default = "uksouth"
}
variable "vnet_cidr" {
  type    = string
  default = "10.1.0.0/16"
}
variable "kubernetes_version" {
  type    = string
  default = "1.30"
}
variable "node_vm_size" {
  type    = string
  default = "Standard_D2s_v3"
}
variable "node_count" {
  type    = number
  default = 2
}
variable "tags" {
  type    = map(string)
  default = {}
}
