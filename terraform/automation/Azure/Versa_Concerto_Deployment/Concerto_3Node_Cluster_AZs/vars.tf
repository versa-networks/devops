variable "subscription_id" {
  description = "Subscription ID of Azure account."
}

variable "client_id" {
  description = "Client ID of Terraform account to be used to deploy VM on Azure."
}

variable "client_secret" {
  description = "Client Secret of Terraform account to be used to deploy VM on Azure."
}

variable "tenant_id" {
  description = "Tenant ID of Terraform account to be used to deploy VM on Azure."
}

variable "location" {
  description = "Location where Versa Head End setup to be deployed."
}

variable "resource_group" {
  description = "Name of the resource group in which Versa Concerto setup will be deployed."
  default     = "Versa_Concerto"
}

variable "ssh_key" {
  description = "SSH Key to be injected into VMs deployed on Azure."
}

variable "vpc_address_space" {
  description = "Virtual Private Network's address space to be used to deploy Versa Concerto setup."
  default     = "10.234.0.0/16"
}

variable "newbits_subnet" {
  description = "This is required to create desired netmask from virtual network."
  default     = "8"
}

variable "image_concerto" {
  description = "Versa concerto Image ID to be used to deploy Versa concerto."
}

variable "cluster_nodes" {
  description = "Number of nodes in cluster."
  default     = 3
}

variable "hostname_concerto" {
  description = "Hostname to be used for Versa concerto."
  type        = list(string)
  default = [
    "versa-concerto-1",
    "versa-concerto-2",
    "versa-concerto-3",
  ]
}

variable "concerto_vm_size" {
  description = "Size of Versa concerto VM."
  default     = "Standard_F8s_v2"
}

