<<<<<<< HEAD
=======
###########################
# Tenancy details
#
# Information to access your tenancy
############################

>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3
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

<<<<<<< HEAD
variable "regions" {
  description = "Placeholder for multiple Region deployment"
}


=======
variable "availability_domain" {
  description = "Instance shape required for the Analytics Nodes"
}

>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3
variable "private_key_path" {
  description = "Path to the Private Key"
}

variable "par_compartment_id" {
<<<<<<< HEAD
  description = "ID of the parent compartment"
}

variable "compartment_name" {
  description = ""
}

variable "compartment_description" {
  description = ""
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
=======
  description = "ID of the parent compartment, where resources are to be created"
}

###########################
# Image IDS
#
# These need to be created beforehand in the Oracle UI
############################
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3

variable "analytics_image_id" {
  description = "Image Id for the VAN nodes"
}

variable "director_image_id" {
  description = "Image Id for the Director"
}

variable "vos_image_id" {
  description = "Image Id for the Director"
}

<<<<<<< HEAD
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
=======
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

variable "router_cidr_block" {
  description = "Router Private CIDR Block. Needs to be included in the VCN block"
}

###########################
# VAN Cluster Size Variables
#
# Number of VAN nodes to deploy
############################
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3

variable "analytics_nodes_number" {
  description = "number of Analytics nodes to be deployed"
}

variable "search_nodes_number" {
  description = "number of Search nodes to be deployed"
}

<<<<<<< HEAD
variable "logforwarders_nodes_number" {
  description = "number of Log Forwarders nodes to be deployed"
}
=======
variable "logforwarder_nodes_number" {
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

variable "logforwarder_instance_shape" {
  description = "Instance shape required for the Log Forwarder Nodes"
}
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3

variable "director_instance_shape" {
  description = "Instance shape required for the Director"
}

<<<<<<< HEAD
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
=======
variable "ssh_public_key_file" {
  description = "Path to SSH Public Key"
}

>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3
