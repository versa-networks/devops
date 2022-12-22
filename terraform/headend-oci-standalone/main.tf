# Configure the Oracle Cloud Infrastructure
#Multiple regions docs: https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/terraform-targeting-multiple-regions.htm
#private_key_path = var.private_key_path
provider "oci" {
  region = var.region
  tenancy_ocid = var.tenancy_ocid
  user_ocid = var.user_ocid
  fingerprint = var.fingerprint
  private_key_path = var.private_key_path
}

#Create VCN Networking
resource "oci_core_vcn" "als_vcn" {
    #Required
    
    compartment_id = var.par_compartment_id

    #Optional
    cidr_block = var.vcn_cidr_block
    display_name = var.vcn_display_name1
    dns_label = "versavcn"
    #is_ipv6enabled = var.vcn_is_ipv6enabled
}


resource "oci_core_internet_gateway" "als_internet_gateway" {
    #Required
    
    compartment_id = var.par_compartment_id
    vcn_id = oci_core_vcn.als_vcn.id
    depends_on = [oci_core_vcn.als_vcn]

    #Optional
    enabled = "true"
    display_name = "ALS-IGW"
}

resource "oci_core_drg" "als_drg" {
    #Required
    compartment_id = var.par_compartment_id

    #Optional
    display_name = "ALS-DRG"
}

resource "oci_core_drg_attachment" "als_drg_attachment" {
    #Required
    drg_id = oci_core_drg.als_drg.id

    #Optional
    display_name = "DRG Attachment to ALS VCN"
    network_details {
        #Required
        id = oci_core_vcn.als_vcn.id
        type = "VCN"

        #Optional
        #route_table_id = oci_core_route_table.test_route_table.id
        #vcn_route_type = var.drg_attachment_network_details_vcn_route_type
    }
}

resource "oci_core_route_table" "northbound_route_table" {
    #Required
    
    compartment_id = var.par_compartment_id
    vcn_id = oci_core_vcn.als_vcn.id

    #Optional
    display_name = "Versa Route Table for Northbound"
    route_rules {
        #Required
        network_entity_id = oci_core_internet_gateway.als_internet_gateway.id

        #Optional
        description = "Default route for Versa VCN"
        destination = "0.0.0.0/0"
    }
}

resource "oci_core_route_table" "wan_route_table" {
    #Required
    
    compartment_id = var.par_compartment_id
    vcn_id = oci_core_vcn.als_vcn.id

    #Optional
    display_name = "Versa Route Table for WAN"
    route_rules {
        #Required
        network_entity_id = oci_core_internet_gateway.als_internet_gateway.id

        #Optional
        description = "Default route for Versa VCN"
        destination = "0.0.0.0/0"
    }
}

resource "oci_core_security_list" "WAN_security_list" {
  
  compartment_id = var.par_compartment_id
  vcn_id         = oci_core_vcn.als_vcn.id
  display_name   = "WAN-security-list"

  egress_security_rules {
      stateless   = false
      destination      = "0.0.0.0/0"
      destination_type = "CIDR_BLOCK"
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

}

resource "oci_core_security_list" "Internode_security_list" {
  
  compartment_id = var.par_compartment_id
  vcn_id         = oci_core_vcn.als_vcn.id
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
  vcn_id         = oci_core_vcn.als_vcn.id
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

resource "oci_core_subnet" "northbound_subnet" {
    #Required
    cidr_block = var.northbound_cidr_block
    
    compartment_id = var.par_compartment_id
    vcn_id = oci_core_vcn.als_vcn.id

    #Optional
    #availability_domain = var.subnet_availability_domain
    #dhcp_options_id = oci_core_dhcp_options.test_dhcp_options.id
    display_name = "als.northbound"
    dns_label = "alsnorthb"
    route_table_id = oci_core_route_table.northbound_route_table.id
    #ipv6cidr_block = var.subnet_ipv6cidr_block
    #prohibit_internet_ingress = var.subnet_prohibit_internet_ingress
    #prohibit_public_ip_on_vnic = var.subnet_prohibit_public_ip_on_vnic
    #route_table_id = oci_core_route_table.test_route_table.id
    security_list_ids = [oci_core_security_list.Internode_security_list.id,oci_core_security_list.Mgmt_security_list.id]
}

resource "oci_core_subnet" "southbound_subnet" {
    #Required
    cidr_block = var.southbound_cidr_block
    
    compartment_id = var.par_compartment_id
    vcn_id = oci_core_vcn.als_vcn.id

    #Optional
    #availability_domain = var.subnet_availability_domain
    #dhcp_options_id = oci_core_dhcp_options.test_dhcp_options.id
    display_name = "als-southbound"
    dns_label = "alssouthb"
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
    vcn_id = oci_core_vcn.als_vcn.id

    #Optional
    #availability_domain = var.subnet_availability_domain
    #dhcp_options_id = oci_core_dhcp_options.test_dhcp_options.id
    display_name = "als-wan"
    dns_label = "alswan"
    route_table_id = oci_core_route_table.wan_route_table.id
    #ipv6cidr_block = var.subnet_ipv6cidr_block
    #prohibit_internet_ingress = var.subnet_prohibit_internet_ingress
    #prohibit_public_ip_on_vnic = var.subnet_prohibit_public_ip_on_vnic
    #route_table_id = oci_core_route_table.test_route_table.id
    security_list_ids = [oci_core_security_list.WAN_security_list.id]
}

resource "oci_core_instance_configuration" "analytics_instance_configuration" {
    #Required
    
    compartment_id = var.par_compartment_id
    display_name = "VAN Instance Configuration"

    instance_details {
        #Required
        instance_type = "compute"
        launch_details {

            availability_domain = var.availability_domain
            
            compartment_id = var.par_compartment_id
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

resource "oci_core_instance_configuration" "search_instance_configuration" {
    #Required
    
    compartment_id = var.par_compartment_id
    display_name = "Search Instance Configuration"

    instance_details {
        #Required
        instance_type = "compute"
        launch_details {

            availability_domain = var.availability_domain
            
            compartment_id = var.par_compartment_id
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

resource "oci_core_instance_configuration" "logforwarder_instance_configuration" {
    #Required
    
    compartment_id = var.par_compartment_id
    display_name = "LogForwarder Instance Configuration"

    instance_details {
        #Required
        instance_type = "compute"
        launch_details {

            availability_domain = var.availability_domain
            
            compartment_id = var.par_compartment_id
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
  compartment_id            = var.par_compartment_id
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
  compartment_id            = var.par_compartment_id
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
  compartment_id            = var.par_compartment_id
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
    
    compartment_id = var.par_compartment_id
    shape = var.director_instance_shape
    display_name = var.director_instance_name

    create_vnic_details {
        #Optional
        assign_public_ip = "true"
        display_name = "dirnorthbound_nic"
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
    compartment_id = var.par_compartment_id
    shape = var.controller_instance_shape
    display_name = "vos-controller-${1 + count.index}"

    create_vnic_details {
        #Optional
        assign_public_ip = "false"
        display_name = "vos_northboundvnic"
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

resource "oci_core_vnic_attachment" "control_vnic_attachment" {
    #Required
    count = 2
    depends_on = [oci_core_instance.vos_controller]
    create_vnic_details {
        #Optional
        display_name = "controller_northbound_nic"
        skip_source_dest_check = "true"
        subnet_id = oci_core_subnet.southbound_subnet.id
    }
    instance_id = oci_core_instance.vos_controller[count.index].id

    #Optional
    display_name = "vos-southbound-nic"
}