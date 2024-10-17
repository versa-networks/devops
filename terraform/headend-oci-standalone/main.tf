<<<<<<< HEAD
# Configure the Oracle Cloud Infrastructure
#Multiple regions docs: https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/terraform-targeting-multiple-regions.htm
#private_key_path = var.private_key_path
=======
###############################################
# Configure the Oracle Cloud Infrastructure
#
# In this section we configure the requirments to connect to the OCI
# You would have need to create a Compartment before hand, as well as the credentials
###############################################
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3
provider "oci" {
  region = var.region
  tenancy_ocid = var.tenancy_ocid
  user_ocid = var.user_ocid
  fingerprint = var.fingerprint
  private_key_path = var.private_key_path
}

<<<<<<< HEAD
#provider "oci" {
#  region = var.region
#  alias = "home" 
#  tenancy_ocid = var.tenancy_ocid
#  user_ocid = var.user_ocid
#  fingerprint = var.fingerprint
#  private_key_path = var.private_key_path
#}

#provider "oci" {
# region = var.regions[1]
# alias = "secondary" 
# tenancy_ocid = var.tenancy_ocid
# user_ocid = var.user_ocid
# fingerprint = var.fingerprint
# private_key_path = var.private_key_path
#}

# Create a Compartment
#Not mandatory to create a compartment but it is good practice
resource "oci_identity_compartment" "als_compartment" {
    #Required
    #count = length(var.regions)
    

    compartment_id = var.par_compartment_id
    description = var.compartment_description
    name = var.compartment_name


    #Optional
    freeform_tags = {"Environment"= "Versa Advanced Logging System"}
    enable_delete = "true"
    #Setting enable_delete = true for testing purposes
    #In production it will probably by a good idea to change it to fals
}

resource "oci_core_vcn" "als_vcn" {
    #Required
    
    compartment_id = oci_identity_compartment.als_compartment.id
    depends_on = [oci_identity_compartment.als_compartment]

    #Optional
    cidr_block = var.vcn_cidr_block
    display_name = var.vcn_display_name1
    dns_label = "versavcn"
    #is_ipv6enabled = var.vcn_is_ipv6enabled
}

#resource "oci_core_vcn" "als_vcn2" {
#Required
#    provider = oci.secondary    
#    compartment_id = oci_identity_compartment.als_compartment.id
    ##Optional
#    cidr_block = var.vcn_cidr_block
#    display_name = var.vcn_display_name2
#    dns_label = "versavcn"
    #is_ipv6enabled = var.vcn_is_ipv6enabled
#}


resource "oci_core_internet_gateway" "als_internet_gateway" {
    #Required
    
    compartment_id = oci_identity_compartment.als_compartment.id
    vcn_id = oci_core_vcn.als_vcn.id
    depends_on = [oci_core_vcn.als_vcn]

    #Optional
    enabled = "true"
    display_name = "ALS-IGW"
}

resource "oci_core_drg" "als_drg" {
    #Required
    compartment_id = oci_identity_compartment.als_compartment.id
=======

###############################################
# Create the VCN Elements
#
# In this section we create the Networking elements, including:
# VCN, Security Lists, Routing Tables, IGW, DRG. 
###############################################

#Create a VCN (Virtual Cloud Network)
resource "oci_core_vcn" "headend_vcn" {
    #Required
    
    compartment_id = var.par_compartment_id

    #Optional
    cidr_block = var.vcn_cidr_block
    display_name = var.vcn_display_name
    dns_label = "versaheadend"
    #is_ipv6enabled = var.vcn_is_ipv6enabled
}

#Create an Internet Gateway
resource "oci_core_internet_gateway" "headend_internet_gateway" {
    #Required
    depends_on = [oci_core_vcn.headend_vcn]
    compartment_id = var.par_compartment_id
    vcn_id = oci_core_vcn.headend_vcn.id

    #Optional
    enabled = "true"
    display_name = "Versa-Headend-IGW"
}

resource "oci_core_drg" "headend_drg" {
    #Required
    depends_on = [oci_core_vcn.headend_vcn]
    compartment_id = var.par_compartment_id
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3

    #Optional
    display_name = "ALS-DRG"
}

<<<<<<< HEAD
resource "oci_core_drg_attachment" "als_drg_attachment" {
    #Required
    drg_id = oci_core_drg.als_drg.id

    #Optional
    display_name = "DRG Attachment to ALS VCN"
    network_details {
        #Required
        id = oci_core_vcn.als_vcn.id
=======
resource "oci_core_drg_attachment" "headend_drg_attachment" {
    #Required
    depends_on = [oci_core_vcn.headend_vcn]
    drg_id = oci_core_drg.headend_drg.id

    #Optional
    display_name = "DRG Attachment to Headend VCN"
    network_details {
        #Required
        id = oci_core_vcn.headend_vcn.id
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3
        type = "VCN"

        #Optional
        #route_table_id = oci_core_route_table.test_route_table.id
        #vcn_route_type = var.drg_attachment_network_details_vcn_route_type
    }
}

resource "oci_core_route_table" "northbound_route_table" {
    #Required
<<<<<<< HEAD
    
    compartment_id = oci_identity_compartment.als_compartment.id
    vcn_id = oci_core_vcn.als_vcn.id
=======
    depends_on = [oci_core_vcn.headend_vcn]
    compartment_id = var.par_compartment_id
    vcn_id = oci_core_vcn.headend_vcn.id
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3

    #Optional
    display_name = "Versa Route Table for Northbound"
    route_rules {
        #Required
<<<<<<< HEAD
        network_entity_id = oci_core_internet_gateway.als_internet_gateway.id
=======
        network_entity_id = oci_core_internet_gateway.headend_internet_gateway.id
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3

        #Optional
        description = "Default route for Versa VCN"
        destination = "0.0.0.0/0"
    }
}

resource "oci_core_route_table" "wan_route_table" {
    #Required
<<<<<<< HEAD
    
    compartment_id = oci_identity_compartment.als_compartment.id
    vcn_id = oci_core_vcn.als_vcn.id
=======
    depends_on = [oci_core_vcn.headend_vcn]
    compartment_id = var.par_compartment_id
    vcn_id = oci_core_vcn.headend_vcn.id
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3

    #Optional
    display_name = "Versa Route Table for WAN"
    route_rules {
        #Required
<<<<<<< HEAD
        network_entity_id = oci_core_internet_gateway.als_internet_gateway.id
=======
        network_entity_id = oci_core_internet_gateway.headend_internet_gateway.id
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3

        #Optional
        description = "Default route for Versa VCN"
        destination = "0.0.0.0/0"
    }
}

resource "oci_core_security_list" "WAN_security_list" {
<<<<<<< HEAD
  
  compartment_id = oci_identity_compartment.als_compartment.id
  vcn_id         = oci_core_vcn.als_vcn.id
=======
  depends_on = [oci_core_vcn.headend_vcn]
  compartment_id = var.par_compartment_id
  vcn_id         = oci_core_vcn.headend_vcn.id
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3
  display_name   = "WAN-security-list"

  egress_security_rules {
      stateless   = false
      destination      = "0.0.0.0/0"
      destination_type = "CIDR_BLOCK"
<<<<<<< HEAD
      protocol    = "17"
      udp_options {
        min = 4500
        max = 4500
      }
  }

  egress_security_rules {
      stateless   = false
      destination      = "0.0.0.0/0"
      destination_type = "CIDR_BLOCK"
      protocol    = "17"
      udp_options {
        min = 4790
        max = 4790
      }
=======
      protocol    = "ALL"
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3
  }

  ingress_security_rules {
    stateless   = false
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
    protocol    = "17"
    udp_options {
      min = 500
      max = 500
    }
  }

<<<<<<< HEAD
}

resource "oci_core_security_list" "Internode_security_list" {
  
  compartment_id = oci_identity_compartment.als_compartment.id
  vcn_id         = oci_core_vcn.als_vcn.id
=======
  ingress_security_rules {
    stateless   = false
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
    protocol    = "17"
    udp_options {
      min = 4500
      max = 4500
    }
  }

  ingress_security_rules {
    stateless   = false
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
    protocol    = "17"
    udp_options {
      min = 4790
      max = 4790
    }
  }

}

resource "oci_core_security_list" "Internode_security_list" {
  depends_on = [oci_core_vcn.headend_vcn]
  compartment_id = var.par_compartment_id
  vcn_id         = oci_core_vcn.headend_vcn.id
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3
  display_name   = "Internode-security-list"

  egress_security_rules {
    stateless   = false
    destination      = var.vcn_cidr_block
    destination_type = "CIDR_BLOCK"
    protocol    = "ALL"
  }

  ingress_security_rules {
    stateless   = false
    source      = var.vcn_cidr_block
    source_type = "CIDR_BLOCK"
    protocol    = "ALL"
  }

}

resource "oci_core_security_list" "Mgmt_security_list" {
<<<<<<< HEAD
  
  compartment_id = oci_identity_compartment.als_compartment.id
  vcn_id         = oci_core_vcn.als_vcn.id
=======
  depends_on = [oci_core_vcn.headend_vcn]
  compartment_id = var.par_compartment_id
  vcn_id         = oci_core_vcn.headend_vcn.id
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3
  display_name   = "Mgmt-security-list"

  ingress_security_rules {
      stateless   = false
      source      = "0.0.0.0/0"
      source_type = "CIDR_BLOCK"
      protocol    = "6"
      tcp_options {
        min = 22
        max = 22
      }
  }

  ingress_security_rules {
      stateless   = false
      source      = "0.0.0.0/0"
      source_type = "CIDR_BLOCK"
      protocol    = "6"
      tcp_options {
        min = 80
        max = 80
      }
  }

  ingress_security_rules {
      stateless   = false
      source      = "0.0.0.0/0"
      source_type = "CIDR_BLOCK"
      protocol    = "6"
      tcp_options {
        min = 443
        max = 443
      }
  }

  ingress_security_rules {
      stateless   = false
      source      = "0.0.0.0/0"
      source_type = "CIDR_BLOCK"
      protocol    = "6"
      tcp_options {
        min = 9182
        max = 9183
      }
  }

  egress_security_rules {
      stateless   = false
      destination      = "0.0.0.0/0"
      destination_type = "CIDR_BLOCK"
      protocol    = "ALL"
  }

}

<<<<<<< HEAD
resource "oci_core_subnet" "northbound_subnet" {
    #Required
    cidr_block = var.northbound_cidr_block
    
    compartment_id = oci_identity_compartment.als_compartment.id
    vcn_id = oci_core_vcn.als_vcn.id
=======
###############################################
# Create the VCN Subnets
#
# In this section we create the Subnets:
# Northbound, Southbound, Control, and WAN
###############################################

resource "oci_core_subnet" "northbound_subnet" {
    #Required
    depends_on = [oci_core_vcn.headend_vcn]
    cidr_block = var.northbound_cidr_block
    compartment_id = var.par_compartment_id
    vcn_id = oci_core_vcn.headend_vcn.id
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3

    #Optional
    #availability_domain = var.subnet_availability_domain
    #dhcp_options_id = oci_core_dhcp_options.test_dhcp_options.id
<<<<<<< HEAD
    display_name = "als.northbound"
    dns_label = "alsnorthb"
=======
    display_name = "headend-northbound-subnet"
    dns_label = "northbsubnet"
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3
    route_table_id = oci_core_route_table.northbound_route_table.id
    #ipv6cidr_block = var.subnet_ipv6cidr_block
    #prohibit_internet_ingress = var.subnet_prohibit_internet_ingress
    #prohibit_public_ip_on_vnic = var.subnet_prohibit_public_ip_on_vnic
<<<<<<< HEAD
    #route_table_id = oci_core_route_table.test_route_table.id
=======
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3
    security_list_ids = [oci_core_security_list.Internode_security_list.id,oci_core_security_list.Mgmt_security_list.id]
}

resource "oci_core_subnet" "southbound_subnet" {
    #Required
<<<<<<< HEAD
    cidr_block = var.southbound_cidr_block
    
    compartment_id = oci_identity_compartment.als_compartment.id
    vcn_id = oci_core_vcn.als_vcn.id
=======
    depends_on = [oci_core_vcn.headend_vcn]
    cidr_block = var.southbound_cidr_block
    
    compartment_id = var.par_compartment_id
    vcn_id = oci_core_vcn.headend_vcn.id
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3

    #Optional
    #availability_domain = var.subnet_availability_domain
    #dhcp_options_id = oci_core_dhcp_options.test_dhcp_options.id
<<<<<<< HEAD
    display_name = "als-southbound"
    dns_label = "alssouthb"
=======
    display_name = "headend-southbound-subnet"
    dns_label = "southbsubnet"
    route_table_id = oci_core_route_table.northbound_route_table.id
    #ipv6cidr_block = var.subnet_ipv6cidr_block
    #prohibit_internet_ingress = var.subnet_prohibit_internet_ingress
    #prohibit_public_ip_on_vnic = var.subnet_prohibit_public_ip_on_vnic
    #route_table_id = oci_core_route_table.test_route_table.id
    security_list_ids = [oci_core_security_list.Internode_security_list.id]
}

resource "oci_core_subnet" "control_subnet" {
    #Required
    depends_on = [oci_core_vcn.headend_vcn]
    cidr_block = var.control_cidr_block
    
    compartment_id = var.par_compartment_id
    vcn_id = oci_core_vcn.headend_vcn.id

    #Optional
    #availability_domain = var.subnet_availability_domain
    #dhcp_options_id = oci_core_dhcp_options.test_dhcp_options.id
    display_name = "headend-control-subnet"
    dns_label = "controlsubnet"
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3
    route_table_id = oci_core_route_table.northbound_route_table.id
    #ipv6cidr_block = var.subnet_ipv6cidr_block
    #prohibit_internet_ingress = var.subnet_prohibit_internet_ingress
    #prohibit_public_ip_on_vnic = var.subnet_prohibit_public_ip_on_vnic
    #route_table_id = oci_core_route_table.test_route_table.id
    security_list_ids = [oci_core_security_list.Internode_security_list.id]
}

resource "oci_core_subnet" "wan_subnet" {
    #Required
<<<<<<< HEAD
    cidr_block = var.wan_cidr_block
    
    compartment_id = oci_identity_compartment.als_compartment.id
    vcn_id = oci_core_vcn.als_vcn.id
=======
    depends_on = [oci_core_vcn.headend_vcn]
    cidr_block = var.wan_cidr_block
    
    compartment_id = var.par_compartment_id
    vcn_id = oci_core_vcn.headend_vcn.id
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3

    #Optional
    #availability_domain = var.subnet_availability_domain
    #dhcp_options_id = oci_core_dhcp_options.test_dhcp_options.id
<<<<<<< HEAD
    display_name = "als-wan"
    dns_label = "alswan"
=======
    display_name = "headend-wan-subnet"
    dns_label = "wansubnet"
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3
    route_table_id = oci_core_route_table.wan_route_table.id
    #ipv6cidr_block = var.subnet_ipv6cidr_block
    #prohibit_internet_ingress = var.subnet_prohibit_internet_ingress
    #prohibit_public_ip_on_vnic = var.subnet_prohibit_public_ip_on_vnic
    #route_table_id = oci_core_route_table.test_route_table.id
    security_list_ids = [oci_core_security_list.WAN_security_list.id]
}

<<<<<<< HEAD
resource "oci_core_instance_configuration" "analytics_instance_configuration" {
    #Required
    
    compartment_id = oci_identity_compartment.als_compartment.id
    display_name = "VAN Instance Configuration"

    instance_details {
        #Required
        instance_type = "compute"
        launch_details {

            availability_domain = var.availability_domain
            
            compartment_id = oci_identity_compartment.als_compartment.id
            create_vnic_details {

                #Optional
                assign_public_ip = "false"
                display_name = "northboundvnic"
                skip_source_dest_check = "true"
                subnet_id = oci_core_subnet.northbound_subnet.id
            }
            display_name = "Analytics"

            #launch_mode = var.instance_configuration_instance_details_launch_details_launch_mode
            metadata = {
                    #ssh_authorized_keys = "${file(var.ssh_public_key_file)}"
            }

            shape = var.analytics_instance_shape
=======
resource "oci_core_subnet" "router_subnet" {
    #Required
    depends_on = [oci_core_vcn.headend_vcn]
    cidr_block = var.router_cidr_block
    
    compartment_id = var.par_compartment_id
    vcn_id = oci_core_vcn.headend_vcn.id

    #Optional
    #availability_domain = var.subnet_availability_domain
    #dhcp_options_id = oci_core_dhcp_options.test_dhcp_options.id
    display_name = "headend-router-subnet"
    dns_label = "routersubnet"
    route_table_id = oci_core_route_table.wan_route_table.id
    #ipv6cidr_block = var.subnet_ipv6cidr_block
    #prohibit_internet_ingress = var.subnet_prohibit_internet_ingress
    #prohibit_public_ip_on_vnic = var.subnet_prohibit_public_ip_on_vnic
    #route_table_id = oci_core_route_table.test_route_table.id
    security_list_ids = [oci_core_security_list.WAN_security_list.id]
}

###############################################
# Instantiate the Versa Analytics cluster
#
# Create the nodes for the Versa Analytics Cluster
# Including all the required VMs (Analytics, Search, Logforwarder)
# As per the Cluster Size defined in the variables 
###############################################

#Create the number of Analytics nodes specified in var.analytics_nodes_number
resource "oci_core_instance" "versa_analytics" {
    #Required
    depends_on = [oci_core_subnet.northbound_subnet]
    count = var.analytics_nodes_number
    availability_domain = var.availability_domain
    compartment_id = var.par_compartment_id
    shape = var.analytics_instance_shape
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3
            shape_config {
                  memory_in_gbs = var.analytics_mem_in_gbs
                  ocpus = var.analytics_ocpus
            }
<<<<<<< HEAD
            
            source_details {
                #Required
                source_type = "image"

                #Optional
                image_id = var.analytics_image_id
            }
        }
        secondary_vnics {

            #Optional
            create_vnic_details {
                #Optional
                assign_public_ip = "false"
                display_name = "sbvnic"
                skip_source_dest_check = "true"
                subnet_id = oci_core_subnet.southbound_subnet.id
            }
            display_name = "sbvnic"
            #nic_index = 1
        }
    }
}

resource "oci_core_instance_configuration" "search_instance_configuration" {
    #Required
    
    compartment_id = oci_identity_compartment.als_compartment.id
    display_name = "Search Instance Configuration"

    instance_details {
        #Required
        instance_type = "compute"
        launch_details {

            availability_domain = var.availability_domain
            
            compartment_id = oci_identity_compartment.als_compartment.id
            create_vnic_details {

                #Optional
                assign_public_ip = "false"
                display_name = "northboundvnic"
                skip_source_dest_check = "true"
                subnet_id = oci_core_subnet.northbound_subnet.id
            }
            display_name = "Search"

            #launch_mode = var.instance_configuration_instance_details_launch_details_launch_mode
            metadata = {
                    #ssh_authorized_keys = "${file(var.ssh_public_key_file)}"
            }

            shape = var.analytics_instance_shape
=======
    display_name = "${var.analytics_instance_name}-${1 + count.index}"

    create_vnic_details {
        #Optional
        display_name = "${var.analytics_instance_name}.${1 + count.index}_northbound_vnic"
        skip_source_dest_check = "true"
        subnet_id = oci_core_subnet.northbound_subnet.id
    }
    
    source_details {
        #Required
        source_id = var.analytics_image_id
        source_type = "image"
    }

    metadata = {
        #ssh_authorized_keys = "${file(var.ssh_public_key_file)}"
    }
}

# Attach a southbound vnic to each Analytics Node
resource "oci_core_vnic_attachment" "analytics_southbound_vnic_attachment" {
    #Required
    depends_on = [oci_core_instance.versa_analytics]
    count = var.analytics_nodes_number
    create_vnic_details {
        #Optional
        display_name = "${var.analytics_instance_name}.${1 + count.index}_southbound_nic"
        skip_source_dest_check = "true"
        subnet_id = oci_core_subnet.southbound_subnet.id
    }
    instance_id = oci_core_instance.versa_analytics[count.index].id

    #Optional
    display_name = "${var.analytics_instance_name}.${1 + count.index}_southbound_vnic"
}


#Create the number of Search nodes specified in var.search_nodes_number
resource "oci_core_instance" "versa_search" {
    #Required
    depends_on = [oci_core_vnic_attachment.analytics_southbound_vnic_attachment]
    count = var.search_nodes_number
    availability_domain = var.availability_domain
    compartment_id = var.par_compartment_id
    shape = var.analytics_instance_shape
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3
            shape_config {
                  memory_in_gbs = var.analytics_mem_in_gbs
                  ocpus = var.analytics_ocpus
            }
<<<<<<< HEAD
            
            source_details {
                #Required
                source_type = "image"

                #Optional
                image_id = var.analytics_image_id
            }
        }
        secondary_vnics {

            #Optional
            create_vnic_details {
                #Optional
                assign_public_ip = "false"
                display_name = "sbvnic"
                skip_source_dest_check = "true"
                subnet_id = oci_core_subnet.southbound_subnet.id
            }
            display_name = "sbvnic"
            #nic_index = 1
        }
    }
}

resource "oci_core_instance_configuration" "logforwarder_instance_configuration" {
    #Required
    
    compartment_id = oci_identity_compartment.als_compartment.id
    display_name = "LogForwarder Instance Configuration"

    instance_details {
        #Required
        instance_type = "compute"
        launch_details {

            availability_domain = var.availability_domain
            
            compartment_id = oci_identity_compartment.als_compartment.id
            create_vnic_details {

                #Optional
                assign_public_ip = "false"
                display_name = "northboundvnic"
                skip_source_dest_check = "true"
                subnet_id = oci_core_subnet.northbound_subnet.id
            }
            display_name = "LogForwarder"

            #launch_mode = var.instance_configuration_instance_details_launch_details_launch_mode
            #metadata = var.instance_configuration_instance_details_launch_details_metadata

            shape = var.analytics_instance_shape
            shape_config {
                  memory_in_gbs = var.analytics_mem_in_gbs
                  ocpus = var.analytics_ocpus
            }
            
            source_details {
                #Required
                source_type = "image"

                #Optional
                image_id = var.analytics_image_id
            }
        }
        secondary_vnics {

            #Optional
            create_vnic_details {
                #Optional
                assign_public_ip = "false"
                display_name = "sbvnic"
                skip_source_dest_check = "true"
                subnet_id = oci_core_subnet.southbound_subnet.id
            }
            display_name = "sbvnic"
            #nic_index = 1
        }
    }
}

resource "oci_core_instance_pool" "analytics_instance_pool" {

  lifecycle {
    create_before_destroy = true
    ignore_changes        = [load_balancers, freeform_tags]
  }

  display_name              = "Analytics-instance-pool"
  compartment_id            = oci_identity_compartment.als_compartment.id
  instance_configuration_id = oci_core_instance_configuration.analytics_instance_configuration.id

  placement_configurations {
    availability_domain = var.availability_domain
    primary_subnet_id = oci_core_subnet.northbound_subnet.id
    secondary_vnic_subnets {
            #Required
            subnet_id = oci_core_subnet.southbound_subnet.id
            display_name = "sbvnic"
        }
  }

  size = var.analytics_nodes_number
}

resource "oci_core_instance_pool" "search_instance_pool" {
depends_on = [oci_core_instance_pool.analytics_instance_pool,oci_core_instance_configuration.analytics_instance_configuration]
  lifecycle {
    create_before_destroy = true
    ignore_changes        = [load_balancers, freeform_tags]
  }

  display_name              = "Search-instance-pool"
  compartment_id            = oci_identity_compartment.als_compartment.id
  instance_configuration_id = oci_core_instance_configuration.search_instance_configuration.id

  placement_configurations {
    availability_domain = var.availability_domain
    primary_subnet_id = oci_core_subnet.northbound_subnet.id
    secondary_vnic_subnets {
            #Required
            subnet_id = oci_core_subnet.southbound_subnet.id
            display_name = "sbvnic"
        }
  }

  size = var.search_nodes_number
}

resource "oci_core_instance_pool" "logforwarder_instance_pool" {
depends_on = [oci_core_instance_pool.analytics_instance_pool,oci_core_instance_pool.search_instance_pool,oci_core_instance_configuration.logforwarder_instance_configuration]
  lifecycle {
    create_before_destroy = true
    ignore_changes        = [load_balancers, freeform_tags]
  }

  display_name              = "LogForwarder-instance-pool"
  compartment_id            = oci_identity_compartment.als_compartment.id
  instance_configuration_id = oci_core_instance_configuration.logforwarder_instance_configuration.id

  placement_configurations {
    availability_domain = var.availability_domain
    primary_subnet_id = oci_core_subnet.northbound_subnet.id
    secondary_vnic_subnets {
            #Required
            subnet_id = oci_core_subnet.southbound_subnet.id
            display_name = "sbvnic"
        }
  }

  size = var.logforwarders_nodes_number
}

resource "oci_core_instance" "als_director" {
    depends_on = [oci_core_instance_pool.logforwarder_instance_pool]
    #Required
    availability_domain = var.availability_domain
    
    compartment_id = oci_identity_compartment.als_compartment.id
=======
    display_name = "${var.search_instance_name}-${1 + count.index}"

    create_vnic_details {
        #Optional
        display_name = "${var.search_instance_name}.${1 + count.index}_northbound_vnic"
        skip_source_dest_check = "true"
        subnet_id = oci_core_subnet.northbound_subnet.id
    }
    
    source_details {
        #Required
        source_id = var.analytics_image_id
        source_type = "image"
    }

    metadata = {
        #ssh_authorized_keys = "${file(var.ssh_public_key_file)}"
    }
}

# Attach a southbound vnic to each Search Node
resource "oci_core_vnic_attachment" "search_southbound_vnic_attachment" {
    #Required
    depends_on = [oci_core_instance.versa_search]
    count = var.search_nodes_number
    create_vnic_details {
        #Optional
        display_name = "${var.search_instance_name}.${1 + count.index}_southbound_nic"
        skip_source_dest_check = "true"
        subnet_id = oci_core_subnet.southbound_subnet.id
    }
    instance_id = oci_core_instance.versa_search[count.index].id

    #Optional
    display_name = "search_${1 + count.index}_southbound_nic"
}

#Create the number of Log Forwarder nodes specified in var.logforwarder_nodes_number
resource "oci_core_instance" "versa_logforwarder" {
    #Required
    depends_on = [oci_core_vnic_attachment.search_southbound_vnic_attachment]
    count = var.logforwarder_nodes_number
    availability_domain = var.availability_domain
    compartment_id = var.par_compartment_id
    shape = var.logforwarder_instance_shape
            shape_config {
                  memory_in_gbs = var.logforwarder_mem_in_gbs
                  ocpus = var.logforwarder_ocpus
            }
    display_name = "${var.logforwarder_instance_name}-${1 + count.index}"

    create_vnic_details {
        #Optional
        display_name = "${var.logforwarder_instance_name}.${1 + count.index}_northbound_vnic"
        skip_source_dest_check = "true"
        subnet_id = oci_core_subnet.northbound_subnet.id
    }
    
    source_details {
        #Required
        source_id = var.analytics_image_id
        source_type = "image"
    }

    metadata = {
        #ssh_authorized_keys = "${file(var.ssh_public_key_file)}"
    }
}

# Attach a southbound vnic to each Log Forwarder Node
resource "oci_core_vnic_attachment" "logforwarder_southbound_vnic_attachment" {
    #Required
    depends_on = [oci_core_instance.versa_logforwarder]
    count = var.logforwarder_nodes_number
    create_vnic_details {
        #Optional
        display_name = "${var.logforwarder_instance_name}.${1 + count.index}_southbound_nic"
        skip_source_dest_check = "true"
        subnet_id = oci_core_subnet.southbound_subnet.id
    }
    instance_id = oci_core_instance.versa_logforwarder[count.index].id

    #Optional
    display_name = "${var.logforwarder_instance_name}.${1 + count.index}_southbound_nic"
}


###############################################
# Instantiate the Versa Director
#
#Create the VM and the VNIC
###############################################

#Creates one instace of the Versa Director
resource "oci_core_instance" "versa_director" {
    #Required
    depends_on = [oci_core_vnic_attachment.logforwarder_southbound_vnic_attachment]
    availability_domain = var.availability_domain
    
    compartment_id = var.par_compartment_id
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3
    shape = var.director_instance_shape
    display_name = var.director_instance_name

    create_vnic_details {
        #Optional
        assign_public_ip = "true"
<<<<<<< HEAD
        display_name = "dirnorthbound_nic"
=======
        display_name = "${var.director_instance_name}_northbound_nic"
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3
        hostname_label = "dirnorthboundnic"
        #nsg_ids = [oci_core_security_list.tf_public_security_list.id]
        subnet_id = oci_core_subnet.northbound_subnet.id
    }

    shape_config {
        #Optional
        memory_in_gbs = var.director_mem_in_gbs
        ocpus = var.director_ocpus
    }

    source_details {
        #Required
        source_id = var.director_image_id
        source_type = "image"
    }

    metadata = {
        #ssh_authorized_keys = "${file(var.ssh_public_key_file)}"
    }
}

<<<<<<< HEAD
resource "oci_core_vnic_attachment" "dirsouthbound_vnic_attachment" {
    #Required
    create_vnic_details {
        #Optional
        display_name = "southbound_nic"
        skip_source_dest_check = "true"
        subnet_id = oci_core_subnet.southbound_subnet.id
    }
    instance_id = oci_core_instance.als_director.id

    #Optional
    display_name = "southbound_nic"
}


resource "oci_core_instance" "vos_controller" {
    #Required
    depends_on = [oci_core_instance_pool.logforwarder_instance_pool,oci_core_instance_pool.search_instance_pool,oci_core_instance_pool.analytics_instance_pool]
    count = 2
    availability_domain = var.availability_domain
    compartment_id = oci_identity_compartment.als_compartment.id
    shape = var.controller_instance_shape
    display_name = "vos-svnf-${1 + count.index}"
=======
# Attach a southbound vnic to the Versa Director
resource "oci_core_vnic_attachment" "dir_southbound_vnic_attachment" {
    #Required
    depends_on = [oci_core_instance.versa_director]
    create_vnic_details {
        #Optional
        display_name = "${var.director_instance_name}_southbound_nic"
        skip_source_dest_check = "true"
        subnet_id = oci_core_subnet.southbound_subnet.id
    }
    instance_id = oci_core_instance.versa_director.id

    #Optional
    display_name = "${var.director_instance_name}_southbound_nic"
}

###############################################
# Instantiate the Versa Service Router
#
#Create the VM and the VNIC
###############################################

resource "oci_core_instance" "versa_svnf" {
    #Required
    depends_on = [oci_core_vnic_attachment.dir_southbound_vnic_attachment]
    availability_domain = var.availability_domain
    compartment_id = var.par_compartment_id
    shape = var.svnf_instance_shape
    display_name = "${var.svnf_instance_name}"
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3

    create_vnic_details {
        #Optional
        assign_public_ip = "false"
<<<<<<< HEAD
        display_name = "vos_northboundvnic"
=======
        display_name = "${var.svnf_instance_name}_northboundvnic"
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3
        skip_source_dest_check = "true"
        subnet_id = oci_core_subnet.northbound_subnet.id
    }
    
    source_details {
        #Required
        source_id = var.vos_image_id
        source_type = "image"
    }

    metadata = {
        #ssh_authorized_keys = "${file(var.ssh_public_key_file)}"
    }
}

<<<<<<< HEAD
resource "oci_core_vnic_attachment" "wan_vnic_attachment" {
    #Required
    count = 2
    depends_on = [oci_core_instance.vos_controller]
    create_vnic_details {
        #Optional
        assign_public_ip = "true"
        display_name = "vos_wan_nic"
        skip_source_dest_check = "true"
        subnet_id = oci_core_subnet.wan_subnet.id
    }
    instance_id = oci_core_instance.vos_controller[count.index].id

    #Optional
    display_name = "vos-wan-nic"
}

resource "oci_core_vnic_attachment" "northbound_vnic_attachment" {
    #Required
    count = 2
    depends_on = [oci_core_instance.vos_controller]
    create_vnic_details {
        #Optional
        display_name = "vos_northbound_nic"
        skip_source_dest_check = "true"
        subnet_id = oci_core_subnet.northbound_subnet.id
    }
    instance_id = oci_core_instance.vos_controller[count.index].id

    #Optional
    display_name = "vos-northbound-nic"
}
=======
resource "oci_core_vnic_attachment" "svnf_southbound_vnic_attachment" {
    #Required
    depends_on = [oci_core_instance.versa_svnf]
    create_vnic_details {
        #Optional
        display_name = "${var.svnf_instance_name}_southbound_vnic"
        skip_source_dest_check = "true"
        subnet_id = oci_core_subnet.southbound_subnet.id
    }
    instance_id = oci_core_instance.versa_svnf.id

    #Optional
    display_name = "${var.svnf_instance_name}_southboundvnic"
}

resource "oci_core_vnic_attachment" "svnf_control_vnic_attachment" {
    #Required
    depends_on = [oci_core_instance.versa_svnf]
    create_vnic_details {
        #Optional
        display_name = "${var.svnf_instance_name}_control_vnic"
        skip_source_dest_check = "true"
        subnet_id = oci_core_subnet.control_subnet.id
    }
    instance_id = oci_core_instance.versa_svnf.id

    #Optional
    display_name = "${var.svnf_instance_name}_control_vnic"
}

resource "oci_core_vnic_attachment" "svnf_router_vnic_attachment" {
    #Required
    depends_on = [oci_core_instance.versa_svnf]
    create_vnic_details {
        #Optional
        display_name = "${var.svnf_instance_name}_router_vnic"
        skip_source_dest_check = "true"
        subnet_id = oci_core_subnet.router_subnet.id
    }
    instance_id = oci_core_instance.versa_svnf.id

    #Optional
    display_name = "${var.svnf_instance_name}_router_vnic"
}

###############################################
# Instantiate the Versa Controller
#
#Create the VM and the VNIC
###############################################

resource "oci_core_instance" "versa_controller" {
    #Required
    depends_on = [oci_core_vnic_attachment.svnf_router_vnic_attachment]
    availability_domain = var.availability_domain
    compartment_id = var.par_compartment_id
    shape = var.controller_instance_shape
    display_name = "${var.controller_instance_name}"

    create_vnic_details {
        #Optional
        assign_public_ip = "false"
        display_name = "${var.controller_instance_name}_northbound_vnic"
        skip_source_dest_check = "true"
        subnet_id = oci_core_subnet.northbound_subnet.id
    }
    
    source_details {
        #Required
        source_id = var.vos_image_id
        source_type = "image"
    }

    metadata = {
        #ssh_authorized_keys = "${file(var.ssh_public_key_file)}"
    }
}

resource "oci_core_vnic_attachment" "controller_wan_vnic_attachment" {
    #Required
    depends_on = [oci_core_instance.versa_controller]
    create_vnic_details {
        #Optional
        assign_public_ip = "true"
        display_name = "${var.controller_instance_name}_wan_vnic"
        skip_source_dest_check = "true"
        subnet_id = oci_core_subnet.wan_subnet.id
    }
    instance_id = oci_core_instance.versa_controller.id

    #Optional
    display_name = "${var.controller_instance_name}_wan_vnic"
}

resource "oci_core_vnic_attachment" "controller_control_vnic_attachment" {
    #Required
    depends_on = [oci_core_vnic_attachment.controller_wan_vnic_attachment]
    create_vnic_details {
        #Optional
        display_name = "${var.controller_instance_name}_control_nic"
        skip_source_dest_check = "true"
        subnet_id = oci_core_subnet.control_subnet.id
    }
    instance_id = oci_core_instance.versa_controller.id

    #Optional
    display_name = "${var.controller_instance_name}_control_nic"
}
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3
