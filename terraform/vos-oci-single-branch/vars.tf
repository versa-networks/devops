variable "tenancy_ocid" {
  description = "Tenenacy ID for the Oracle Account"
}

variable "user_ocid" {
  description = "User ID for the OCI account"
}
  
variable "fingerprint" {
  description = "Fingerprint for the Oracle Account"
}

variable "region" {
  description = "region for the Oracle Account"
}

variable "private_key_path" {
  description = "Path to the Private Key"
}

variable "par_compartment_id" {
  description = "ID of the parent compartment"
}

variable "compartment_description" {
  description = ""
}

variable "compartment_name" {
  description = ""
}

variable "vcn_cidr_block" {
  description = ""
}

variable "vcn_display_name" {
  description = ""
}

variable "mgmt_cidr_block" {
  description = "LAN CIDR Block. Needs to be included in the VCN block"
}

variable "wan_cidr_block" {
  description = "LAN CIDR Block. Needs to be included in the VCN block"
}

variable "lan_cidr_block" {
  description = "LAN CIDR Block. Needs to be included in the VCN block"
}

variable instance_availability_domain {
  description = "Availability domain for the desired instance"
}

variable "instance_shape" {
  description = "Shape for the required instance"
}

variable "instance_name" {
  description = "name for the VOS instance"
}

variable "ssh_public_key_file" {
  default = "~/.ssh/id_rsa.pub"
}
