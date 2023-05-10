###########################
# Tenancy details
#
# Information to access your tenancy
############################
tenancy_ocid = " "
user_ocid = " "
fingerprint = " "
private_key_path = " "
par_compartment_id = " "
region = "us-sanjose-1"
availability_domain = " "

###########################
# Image IDS
#
# These need to be created beforehand in the Oracle UI
############################
analytics_image_id = " "
director_image_id = " "
vos_image_id = " "

###########################
# Networking Variables
#
# Including network display names, IP spaces and others
############################

vcn_display_name = "Versa-Headend-VCN"
vcn_cidr_block = "10.140.0.0/16"
northbound_cidr_block = "10.140.0.0/24"
southbound_cidr_block = "10.140.1.0/24"
control_cidr_block = "10.140.2.0/24"
wan_cidr_block = "10.140.3.0/24"

###########################
# VAN Cluster Size Variables
#
# Number of VAN nodes to deploy
############################

analytics_nodes_number = "1"
search_nodes_number = "1"
logforwarder_nodes_number = "1"

###########################
# Instance names
#
# Size of the VM instances
############################

director_instance_name = "Versa-Director"
analytics_instance_name = "Versa-Analytics"
search_instance_name = "Versa-Search"
logforwarder_instance_name = "Versa-Search"
svnf_instance_name = "Versa-Service-Router"
controller_instance_name = "Versa-Controller"


###########################
# Instance shapes
#
# Size of the VM instances
############################
ssh_public_key_file = " "
director_mem_in_gbs = "16"
director_ocpus = "8"
analytics_mem_in_gbs = "16"
analytics_ocpus = "8"
logforwarder_mem_in_gbs = "4"
logforwarder_ocpus = "2"
analytics_instance_shape = "VM.Standard.E4.Flex"
director_instance_shape = "VM.Standard.E4.Flex"
controller_instance_shape = "VM.Standard2.4"
