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
  default     = "Versa_HE"
}

variable "ssh_key" {
  description = "SSH Key to be injected into VMs deployed on Azure."
}

variable "vpc_address_space" {
  description = "Virtual Private Network's address space to be used to deploy Versa Head end setup."
  default     = "10.234.0.0/16"
}

variable "newbits_subnet" {
  description = "This is required to create desired netmask from virtual network."
  default     = "8"
}

variable "image_director" {
  description = "Versa Director Image ID to be used to deploy Versa Director."
}

variable "image_controller" {
  description = "Controller/FlexVNF Image ID to be used to deploy Versa Controller."
}

variable "image_analytics" {
  description = "Versa Analytics Image ID to be used to deploy Versa Analytics."
}

variable "hostname_director" {
  description = "Hostname to be used for Versa Director."
  type        = list(string)
  default = [
    "versa-director-1",
    "versa-director-2",
  ]
}

variable "hostname_van" {
  description = "Hostname to be used for Versa Analytics nodes. Number of analytics instances created here will be equal to number of hostname entries made. All VAN instances will be created in primary region only."
  type        = list(string)
  default = [
    "versa-analytics-1",
    "versa-analytics-2",
    "versa-analytics-3",
    "versa-analytics-4",
  ]
}

variable "director_vm_size" {
  description = "Size of Versa Director VM."
  default     = "Standard_DS3"
}

variable "controller_vm_size" {
  description = "Size of Versa Controller VM."
  default     = "Standard_DS3"
}

variable "analytics_vm_size" {
  description = "Size of Versa Analytics VM."
  default     = "Standard_DS3"
}

variable "van_disk_size" {
  description = "Disk size to be provisioned for Analytics VMs."
  default     = "80"
}
