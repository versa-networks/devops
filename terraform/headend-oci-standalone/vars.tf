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

variable "regions" {
  description = "Placeholder for multiple Region deployment"
}


variable "private_key_path" {
  description = "Path to the Private Key"
}

variable "par_compartment_id" {
  description = "ID of the parent compartment, where resources are to be created"
}

variable "vcn_display_name1" {
  description = ""
}

variable "vcn_display_name2" {
  description = ""
}

variable "vcn_cidr_block" {
  description = ""
}

variable "northbound_cidr_block" {
  description = "Northbound CIDR Block. Needs to be included in the VCN block"
}

variable "southbound_cidr_block" {
  description = "LAN CIDR Block. Needs to be included in the VCN block"
}

variable "wan_cidr_block" {
  description = "LAN CIDR Block. Needs to be included in the VCN block"
}

variable "analytics_image_id" {
  description = "Image Id for the VAN nodes"
}

variable "director_image_id" {
  description = "Image Id for the Director"
}

variable "vos_image_id" {
  description = "Image Id for the Director"
}

variable "controller_instance_shape" {
  description = "Instance shape for the VOS Service VNFs"
}

variable "analytics_instance_shape" {
  description = "Instance shape required for the Analytics Nodes"
}

variable "availability_domain" {
  description = "Instance shape required for the Analytics Nodes"
}

variable "analytics_mem_in_gbs" {
  description = "Memory in Gbps for Versa Analytics Nodes"
}

variable "analytics_ocpus" {
  description = "OCPUs for Versa Analytics Nodes"
}

variable "director_mem_in_gbs" {
 description = "Memory in Gbps for Versa Director Node"
}

variable "director_ocpus" {
  description = "OCPUs for Versa Directir Node"
}


variable "logforwarder_mem_in_gbs" {
 description = "Memory in Gbps for Log Forwarders"  
}

variable "logforwarder_ocpus" {
  description = "OCPUs for Log Forwarder"
}

variable "analytics_nodes_number" {
  description = "number of Analytics nodes to be deployed"
}

variable "search_nodes_number" {
  description = "number of Search nodes to be deployed"
}

variable "logforwarders_nodes_number" {
  description = "number of Log Forwarders nodes to be deployed"
}

variable "director_instance_shape" {
  description = "Instance shape required for the Director"
}

variable "director_instance_name" {
  description = "Instance namee required for the Director"
}

variable "monitoring_instance_shape" {
  description = "Instance shape required for the Monitoring"
}

variable "monitoring_instance_name" {
  description = "Instance namee required for the Monitoring"
}

variable "ssh_public_key_file" {
  description = "Path to SSH Public Key"
}
