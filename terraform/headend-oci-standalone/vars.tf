###########################
# Tenancy details
#
# Information to access your tenancy
############################

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

variable "availability_domain" {
  description = "Instance shape required for the Analytics Nodes"
}

variable "private_key_path" {
  description = "Path to the Private Key"
}

variable "par_compartment_id" {
  description = "ID of the parent compartment, where resources are to be created"
}

###########################
# Image IDS
#
# These need to be created beforehand in the Oracle UI
############################

variable "analytics_image_id" {
  description = "Image Id for the VAN nodes"
}

variable "director_image_id" {
  description = "Image Id for the Director"
}

variable "vos_image_id" {
  description = "Image Id for the Director"
}

###########################
# Networking Variables
#
# Including network display names, IP spaces and others
############################

variable "vcn_display_name" {
  description = ""
}

variable "vcn_cidr_block" {
  description = ""
}

variable "northbound_cidr_block" {
  description = "Northbound CIDR Block. Needs to be included in the VCN block"
}

variable "southbound_cidr_block" {
  description = "Soutbound CIDR Block. Needs to be included in the VCN block"
}

variable "control_cidr_block" {
  description = "Control CIDR Block. Needs to be included in the VCN block"
}

variable "wan_cidr_block" {
  description = "WAN Private CIDR Block. Needs to be included in the VCN block"
}

###########################
# VAN Cluster Size Variables
#
# Number of VAN nodes to deploy
############################

variable "analytics_nodes_number" {
  description = "number of Analytics nodes to be deployed"
}

variable "search_nodes_number" {
  description = "number of Search nodes to be deployed"
}

variable "logforwarders_nodes_number" {
  description = "number of Log Forwarders nodes to be deployed"
}
###########################
# Instance names
#
# Size of the VM instances
############################

variable "director_instance_name" {
  description = "Instance name for the Director"
}

variable "analytics_instance_name" {
  description = "Instance name for the Analytics Nodes"
}

variable "search_instance_name" {
  description = "Instance name for the Search Nodes"
}

variable "logforwarder_instance_name" {
  description = "Instance name for the Log Forwarder Nodes"
}

variable "logforwarder_instance_name" {
  description = "Instance name for the Log Forwarder Nodes"
}

variable "svnf_instance_name" {
  description = "Instance name for the Service VNF"
}

variable "controller_instance_name" {
  description = "Instance name for the Controller"
}

###########################
# Instance shapes
#
# Size of the VM instances
############################

variable "controller_instance_shape" {
  description = "Instance shape for the Versa Controller"
}

variable "svnf_instance_shape" {
  description = "Instance shape for the Versa Service VNFs"
}

variable "analytics_instance_shape" {
  description = "Instance shape required for the Analytics Nodes (Analytics and Search)"
}

variable "analytics_mem_in_gbs" {
  description = "Memory in Gbps for Versa Analytics Nodes (Analytics and Search)"
}

variable "analytics_ocpus" {
  description = "OCPUs for Versa Analytics Nodes (Analytics and Search)"
}

variable "director_mem_in_gbs" {
 description = "Memory in Gbps for Versa Director Node"
}

variable "director_ocpus" {
  description = "OCPUs for Versa Director Node"
}

variable "logforwarder_mem_in_gbs" {
 description = "Memory in Gbps for Log Forwarders"  
}

variable "logforwarder_ocpus" {
  description = "OCPUs for Log Forwarder"
}

variable "director_instance_shape" {
  description = "Instance shape required for the Director"
}

variable "ssh_public_key_file" {
  description = "Path to SSH Public Key"
}

