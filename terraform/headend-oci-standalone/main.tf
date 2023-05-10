###############################################
# Configure the Oracle Cloud Infrastructure
#
# In this section we configure the requirments to connect to the OCI
# You would have need to create a Compartment before hand, as well as the credentials
###############################################
provider "oci" {
  region = var.region
  tenancy_ocid = var.tenancy_ocid
  user_ocid = var.user_ocid
  fingerprint = var.fingerprint
  private_key_path = var.private_key_path
}


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
    dns_label = "versa-headend-vcn"
    #is_ipv6enabled = var.vcn_is_ipv6enabled
}

#Create an Internet Gateway
resource "oci_core_internet_gateway" "headend_internet_gateway" {
    #Required
    
    compartment_id = var.par_compartment_id
    vcn_id = oci_core_vcn.headend_vcn.id
    depends_on = [oci_core_vcn.headend_vcn]

    #Optional
    enabled = "true"
    display_name = "Versa-Headend-IGW"
}

resource "oci_core_drg" "headend_drg" {
    #Required
    compartment_id = var.par_compartment_id

    #Optional
    display_name = "ALS-DRG"
}

resource "oci_core_drg_attachment" "headend_drg_attachment" {
    #Required
    drg_id = oci_core_drg.headend_drg.id

    #Optional
    display_name = "DRG Attachment to Headend VCN"
    network_details {
        #Required
        id = oci_core_vcn.headend_vcn.id
        type = "VCN"

        #Optional
        #route_table_id = oci_core_route_table.test_route_table.id
        #vcn_route_type = var.drg_attachment_network_details_vcn_route_type
    }
}

resource "oci_core_route_table" "northbound_route_table" {
    #Required
    
    compartment_id = var.par_compartment_id
    vcn_id = oci_core_vcn.headend_vcn.id

    #Optional
    display_name = "Versa Route Table for Northbound"
    route_rules {
        #Required
        network_entity_id = oci_core_internet_gateway.headend_internet_gateway.id

        #Optional
        description = "Default route for Versa VCN"
        destination = "0.0.0.0/0"
    }
}

resource "oci_core_route_table" "wan_route_table" {
    #Required
    
    compartment_id = var.par_compartment_id
    vcn_id = oci_core_vcn.headend_vcn.id

    #Optional
    display_name = "Versa Route Table for WAN"
    route_rules {
        #Required
        network_entity_id = oci_core_internet_gateway.headend_internet_gateway.id

        #Optional
        description = "Default route for Versa VCN"
        destination = "0.0.0.0/0"
    }
}

resource "oci_core_security_list" "WAN_security_list" {
  
  compartment_id = var.par_compartment_id
  vcn_id         = oci_core_vcn.headend_vcn.id
  display_name   = "WAN-security-list"

  egress_security_rules {
      stateless   = false
      destination      = "0.0.0.0/0"
      destination_type = "CIDR_BLOCK"
      protocol    = "ALL"
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
  
  compartment_id = var.par_compartment_id
  vcn_id         = oci_core_vcn.headend_vcn.id
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
  
  compartment_id = var.par_compartment_id
  vcn_id         = oci_core_vcn.headend_vcn.id
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

###############################################
# Create the VCN Subnets
#
# In this section we create the Subnets:
# Northbound, Southbound, Control, and WAN
###############################################

resource "oci_core_subnet" "northbound_subnet" {
    #Required
    cidr_block = var.northbound_cidr_block
    compartment_id = var.par_compartment_id
    vcn_id = oci_core_vcn.headend_vcn.id

    #Optional
    #availability_domain = var.subnet_availability_domain
    #dhcp_options_id = oci_core_dhcp_options.test_dhcp_options.id
    display_name = "headend-northbound-subnet"
    dns_label = "northb-subnet"
    route_table_id = oci_core_route_table.northbound_route_table.id
    #ipv6cidr_block = var.subnet_ipv6cidr_block
    #prohibit_internet_ingress = var.subnet_prohibit_internet_ingress
    #prohibit_public_ip_on_vnic = var.subnet_prohibit_public_ip_on_vnic
    security_list_ids = [oci_core_security_list.Internode_security_list.id,oci_core_security_list.Mgmt_security_list.id]
}

resource "oci_core_subnet" "southbound_subnet" {
    #Required
    cidr_block = var.southbound_cidr_block
    
    compartment_id = var.par_compartment_id
    vcn_id = oci_core_vcn.headend_vcn.id

    #Optional
    #availability_domain = var.subnet_availability_domain
    #dhcp_options_id = oci_core_dhcp_options.test_dhcp_options.id
    display_name = "headend-southbound-subnet"
    dns_label = "southb-subnet"
    route_table_id = oci_core_route_table.northbound_route_table.id
    #ipv6cidr_block = var.subnet_ipv6cidr_block
    #prohibit_internet_ingress = var.subnet_prohibit_internet_ingress
    #prohibit_public_ip_on_vnic = var.subnet_prohibit_public_ip_on_vnic
    #route_table_id = oci_core_route_table.test_route_table.id
    security_list_ids = [oci_core_security_list.Internode_security_list.id]
}

resource "oci_core_subnet" "control_subnet" {
    #Required
    cidr_block = var.control_cidr_block
    
    compartment_id = var.par_compartment_id
    vcn_id = oci_core_vcn.headend_vcn.id

    #Optional
    #availability_domain = var.subnet_availability_domain
    #dhcp_options_id = oci_core_dhcp_options.test_dhcp_options.id
    display_name = "headend-control-subnet"
    dns_label = "control-subnet"
    route_table_id = oci_core_route_table.northbound_route_table.id
    #ipv6cidr_block = var.subnet_ipv6cidr_block
    #prohibit_internet_ingress = var.subnet_prohibit_internet_ingress
    #prohibit_public_ip_on_vnic = var.subnet_prohibit_public_ip_on_vnic
    #route_table_id = oci_core_route_table.test_route_table.id
    security_list_ids = [oci_core_security_list.Internode_security_list.id]
}

resource "oci_core_subnet" "wan_subnet" {
    #Required
    cidr_block = var.wan_cidr_block
    
    compartment_id = var.par_compartment_id
    vcn_id = oci_core_vcn.headend_vcn.id

    #Optional
    #availability_domain = var.subnet_availability_domain
    #dhcp_options_id = oci_core_dhcp_options.test_dhcp_options.id
    display_name = "headend-wan-subnet"
    dns_label = "wan-subnet"
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
    depends_on = [oci_core_subnet.southbound_subnet]
    count = var.analytics_nodes_number
    availability_domain = var.availability_domain
    compartment_id = var.par_compartment_id
    shape = var.analytics_instance_shape
            shape_config {
                  memory_in_gbs = var.analytics_mem_in_gbs
                  ocpus = var.analytics_ocpus
            }
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
    depends_on = [oci_core_instance.versa_analytics]
    count = var.search_nodes_number
    availability_domain = var.availability_domain
    compartment_id = var.par_compartment_id
    shape = var.analytics_instance_shape
            shape_config {
                  memory_in_gbs = var.analytics_mem_in_gbs
                  ocpus = var.analytics_ocpus
            }
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
    depends_on = [oci_core_instance.versa_search]
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
    depends_on = [oci_core_instance.versa_logforwarder]
    availability_domain = var.availability_domain
    
    compartment_id = var.par_compartment_id
    shape = var.director_instance_shape
    display_name = var.director_instance_name

    create_vnic_details {
        #Optional
        assign_public_ip = "true"
        display_name = "${var.director_instance_name}_northbound_nic"
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

# Attach a southbound vnic to the Versa Director
resource "oci_core_vnic_attachment" "dir_southbound_vnic_attachment" {
    #Required
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
    depends_on = [oci_core_instance.versa_director]
    availability_domain = var.availability_domain
    compartment_id = var.par_compartment_id
    shape = var.svnf_instance_shape
    display_name = "${var.svnf_instance_name}"

    create_vnic_details {
        #Optional
        assign_public_ip = "false"
        display_name = "${var.svnf_instance_name}_northboundvnic"
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

###############################################
# Instantiate the Versa Controller
#
#Create the VM and the VNIC
###############################################

resource "oci_core_instance" "versa_controller" {
    #Required
    depends_on = [oci_core_instance.versa_svnf]
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
