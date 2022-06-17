# Configure the Oracle Cloud Infrastructure
#private_key_path = var.private_key_path
provider "oci" {
  tenancy_ocid = var.tenancy_ocid
  user_ocid = var.user_ocid
  fingerprint = var.fingerprint
  region = var.region
  private_key_path = var.private_key_path
}

#provider "random" {
#    version = "~> 2.2"
#}

#provider "template" {
#    version = "~> 2.1"
#}

# Create a Compartment
resource "oci_identity_compartment" "versa_compartment" {
    #Required
    compartment_id = var.par_compartment_id
    description = var.compartment_description
    name = var.compartment_name

    #Optional
    freeform_tags = {"Environment"= "Versa FlexVNF"}
    enable_delete = "true"
}

# Create a VCN
resource "oci_core_vcn" "versa_vcn" {
    #Required
    compartment_id = oci_identity_compartment.versa_compartment.compartment_id

    #Optional
    cidr_block = var.vcn_cidr_block
    display_name = var.vcn_display_name
    dns_label = "versavcn"
    #is_ipv6enabled = var.vcn_is_ipv6enabled
}

resource "oci_core_internet_gateway" "versa_internet_gateway" {
    #Required
    compartment_id = oci_identity_compartment.versa_compartment.compartment_id
    vcn_id = oci_core_vcn.versa_vcn.id

    #Optional
    enabled = "true"
    display_name = "versa-IGW"
}

resource "oci_core_route_table" "versa_route_table" {
    #Required
    compartment_id = oci_identity_compartment.versa_compartment.compartment_id
    vcn_id = oci_core_vcn.versa_vcn.id

    #Optional
    display_name = "Versa Route Table VCN"
    route_rules {
        #Required
        network_entity_id = oci_core_internet_gateway.versa_internet_gateway.id

        #Optional
        description = "Default route for Versa VCN"
        destination = "0.0.0.0/0"
    }
}

resource "oci_core_security_list" "tf_public_security_list"{
  compartment_id = oci_identity_compartment.versa_compartment.compartment_id
  vcn_id         = oci_core_vcn.versa_vcn.id
  display_name   = "Versa-security-list"

  egress_security_rules {
    stateless        = false
    destination      = "0.0.0.0/0"
    destination_type = "CIDR_BLOCK"
    protocol         = "all"
  }

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
        min = 2022
        max = 2022
    }
  }

  ingress_security_rules {
    stateless   = false
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
    protocol    = "6"
    tcp_options {
        min = 3000
        max = 3003
    }
  }

  ingress_security_rules {
    stateless   = false
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
    protocol    = "6"
    tcp_options {
        min = 8443
        max = 8443
    }
  }

  ingress_security_rules {
    stateless   = false
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
    protocol    = "6"
    tcp_options {
        min = 1024
        max = 1120
    }
  }

  ingress_security_rules {
    stateless   = false
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
    protocol    = "6"
    tcp_options {
        min = 9878
        max = 9878
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

  ingress_security_rules {
    stateless   = false
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
    protocol    = "17"
    udp_options {
        min = 3002
        max = 3003
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
        min = 4750
        max = 4750
    }
  }
}

resource "oci_core_subnet" "mgmt_subnet" {
    #Required
    cidr_block = var.mgmt_cidr_block
    compartment_id = oci_identity_compartment.versa_compartment.compartment_id
    vcn_id = oci_core_vcn.versa_vcn.id

    #Optional
    #availability_domain = var.subnet_availability_domain
    #dhcp_options_id = oci_core_dhcp_options.test_dhcp_options.id
    display_name = "versa-mgmt"
    dns_label = "versamgmt"
    route_table_id = oci_core_route_table.versa_route_table.id
    #ipv6cidr_block = var.subnet_ipv6cidr_block
    #prohibit_internet_ingress = var.subnet_prohibit_internet_ingress
    #prohibit_public_ip_on_vnic = var.subnet_prohibit_public_ip_on_vnic
    #route_table_id = oci_core_route_table.test_route_table.id
    security_list_ids = [oci_core_security_list.tf_public_security_list.id]
}

resource "oci_core_subnet" "wan_subnet" {
    #Required
    cidr_block = var.wan_cidr_block
    compartment_id = oci_identity_compartment.versa_compartment.compartment_id
    vcn_id = oci_core_vcn.versa_vcn.id

    #Optional
    #availability_domain = var.subnet_availability_domain
    #dhcp_options_id = oci_core_dhcp_options.test_dhcp_options.id
    display_name = "versa-wan"
    dns_label = "versawan"
    route_table_id = oci_core_route_table.versa_route_table.id
    #ipv6cidr_block = var.subnet_ipv6cidr_block
    #prohibit_internet_ingress = var.subnet_prohibit_internet_ingress
    #prohibit_public_ip_on_vnic = var.subnet_prohibit_public_ip_on_vnic
    #route_table_id = oci_core_route_table.test_route_table.id
    security_list_ids = [oci_core_security_list.tf_public_security_list.id]
}

resource "oci_core_subnet" "lan_subnet" {
    cidr_block = var.lan_cidr_block
    compartment_id = oci_identity_compartment.versa_compartment.compartment_id
    vcn_id = oci_core_vcn.versa_vcn.id

    #Optional
    #availability_domain = var.subnet_availability_domain
    #dhcp_options_id = oci_core_dhcp_options.test_dhcp_options.id
    display_name = "versa-lan"
    dns_label = "versalan"
    #ipv6cidr_block = var.subnet_ipv6cidr_block
    #prohibit_internet_ingress = var.subnet_prohibit_internet_ingress
    #prohibit_public_ip_on_vnic = var.subnet_prohibit_public_ip_on_vnic
    #route_table_id = oci_core_route_table.test_route_table.id
    security_list_ids = [oci_core_security_list.tf_public_security_list.id]
}

resource "oci_core_instance" "vos_instance" {
    #Required
    availability_domain = var.instance_availability_domain
    compartment_id = oci_identity_compartment.versa_compartment.compartment_id
    shape = var.instance_shape
    display_name = var.instance_name

    create_vnic_details {
        #Optional
        assign_public_ip = "true"
        display_name = "mgmtnic"
        hostname_label = "versamgmt"
        #nsg_ids = [oci_core_security_list.tf_public_security_list.id]
        subnet_id = oci_core_subnet.mgmt_subnet.id
    }
    
    source_details {
        #Required
        source_id = "ocid1.image.oc1.us-sanjose-1.aaaaaaaaa2urgnlzlmpai3bx3a6w6kd3u32ktj7t4kmmutouyfnq2llblara"
        source_type = "image"
    }

    metadata = {
        ssh_authorized_keys = "${file(var.ssh_public_key_file)}"
    }
}

resource "oci_core_vnic_attachment" "wan_vnic_attachment" {
    #Required
    create_vnic_details {
        #Optional
        assign_public_ip = "true"
        display_name = "wan_nic"
        skip_source_dest_check = "true"
        subnet_id = oci_core_subnet.wan_subnet.id
    }
    instance_id = oci_core_instance.vos_instance.id

    #Optional
    display_name = "wan-nic"
}

resource "oci_core_vnic_attachment" "lan_vnic_attachment" {
    #Required
    create_vnic_details {
        #Optional
        display_name = "lan_nic"
        skip_source_dest_check = "true"
        subnet_id = oci_core_subnet.lan_subnet.id
    }
    instance_id = oci_core_instance.vos_instance.id

    #Optional
    display_name = "lan-nic"
}
