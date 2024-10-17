variable "credentials_file" {
  description = "Credential file in json format for the service account which will be used to authenticate and provision the required resources."
}

variable "project_id" {
  description = "Google Project ID where Versa head end has to be deployed."
}

variable "region" {
  description = "Region name where Versa head end has to be deployed."
}

variable "ssh_key" {
  description = "SSH Key to be injected into VMs deployed on GCE required for login into instance later on."
}

variable "zone" {
  description = "zone name where Versa head end has to be deployed in a particular region."
}

variable "vos_image" {
  description = "Provide the name of Versa FlexVNF (VOS) Image."
}

variable "labels" {
  description = "Tags/Lavels to be added to the VMs."
  default     = { "infra" = "versa" }
}

variable "machine_type_vos" {
  description = "Provide the machine type (size) for VOS instance to be used."
  default     = "n1-standard-4"
}

variable "director_mgmt_ip" {
  description = "Provide the Director Management IP required to onboard vos via passwrod based authentication for the first time during ztp."
  default     = ""
}

variable "mgmt_vpc_name" {
  description = "Provide the management vpc (network) name required to add necessary firewall rule for vos on management interface."
}

variable "wan_vpc_name" {
  description = "Provide the wan vpc (network) name required to add necessary firewall rule for vos on wan interface."
}

variable "mgmt_subnet_name" {
  description = "Provide the management subnetwork name required to add network interface in management subnet for vos deployment."
}

variable "wan_subnet_name" {
  description = "Provide the wan subnetwork name required to add network interface in wan subnet for vos deployment."
}

variable "lan_subnet_name" {
  description = "Provide the lan subnetwork name required to add network interface in lan subnet for vos deployment."
}