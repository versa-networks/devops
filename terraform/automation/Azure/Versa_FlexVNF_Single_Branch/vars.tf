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
  description = "Name of the resource group in which Versa Head End setup will be deployed."
  default = "Versa_FlexVNF_RG"
}

variable "ssh_key" {
  description = "SSH Key to be injected into VMs deployed on Azure."
}

variable "mgmt_subnet" {
  description = "Management Subnet ID which will be used to create the Interfaces on Management Subnet."
}

variable "wan_subnet" {
  description = "WAN network Subnet which will be used to create the WAN network Interface."
}

variable "lan_subnet" {
  description = "LAN network Subnet which will be used to create the LAN network Interfaces."
}

variable "image_flexvnf" {
  description = "FlexVNF Image ID to be used to deploy Versa FlexVNF Branch."
}

variable "vm_name" {
  description = "Name of the VM to be used which will be displayed in Virtual machines list under Azure Portal."
  default = "Versa_FlexVNF"
}

variable "flexvnf_vm_size" {
  description = "Size of Versa FlexVNF-1 Router VM."
  default = "Standard_DS3"
}