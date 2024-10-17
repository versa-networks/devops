<<<<<<< HEAD
#Tenancy and Key Details
=======
###########################
# Tenancy details
#
# Information to access your tenancy
############################
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3
tenancy_ocid = " "
user_ocid = " "
fingerprint = " "
private_key_path = " "
par_compartment_id = " "
<<<<<<< HEAD

#Image ID's
=======
region = "us-sanjose-1"
availability_domain = " "

###########################
# Image IDS
#
# These need to be created beforehand in the Oracle UI
############################
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3
analytics_image_id = " "
director_image_id = " "
vos_image_id = " "

<<<<<<< HEAD
#Deployment variables
ssh_public_key_file = " "
regions = ["us-sanjose-1", "us-phoenix-1"]
region = "us-sanjose-1"
availability_domain = " "
compartment_name = "Headend-Compartment"
compartment_description = "Headend Compartment"
vcn_display_name1 = "ALS-VCN-1"
vcn_display_name2 = "ALS-VCN-2"
vcn_cidr_block = "10.140.0.0/16"
northbound_cidr_block = "10.140.0.0/24"
southbound_cidr_block = "10.140.1.0/24"
wan_cidr_block = "10.140.2.0/24"
=======
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
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3
director_mem_in_gbs = "16"
director_ocpus = "8"
analytics_mem_in_gbs = "16"
analytics_ocpus = "8"
logforwarder_mem_in_gbs = "4"
logforwarder_ocpus = "2"
<<<<<<< HEAD
analytics_nodes_number = "1"
search_nodes_number = "1"
logforwarders_nodes_number = "1"
analytics_instance_shape = "VM.Standard.E4.Flex"
director_instance_shape = "VM.Standard.E4.Flex"
director_instance_name = "ALS-Director"
monitoring_instance_shape = "VM.Standard.E4.Flex"
monitoring_instance_name = "ALS-Director"
controller_instance_shape = "VM.Standard2.4"
=======
analytics_instance_shape = "VM.Standard.E4.Flex"
director_instance_shape = "VM.Standard.E4.Flex"
controller_instance_shape = "VM.Standard2.4"
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3
