data "stackit_network" "versa-network" {
  project_id = var.project_id
  network_id = var.versa_network_id
}

data "stackit_network" "versa-mgmt-network" {
  project_id = var.project_id
  network_id = var.versa_mgmt_network_id
}

resource "stackit_network_interface" "lan1" {
  project_id         = var.project_id
  network_id         = data.stackit_network.versa-network.network_id
  security           = false
  name               = "LAN1"
  ipv4               = "10.0.1.11"
}

resource "stackit_network_interface" "lan2" {
  project_id = var.project_id
  network_id = data.stackit_network.versa-mgmt-network.network_id
  security   = false
  name       = "LAN2"
  ipv4       = "192.168.1.11"
}

resource "stackit_network_interface" "lan3" {
  project_id = var.project_id
  network_id = data.stackit_network.versa-network.network_id
  security   = false
  name       = "LAN3"
  ipv4       = "10.0.1.12"
}

resource "stackit_network_interface" "lan4" {
  project_id = var.project_id
  network_id = data.stackit_network.versa-mgmt-network.network_id
  security   = false
  name       = "LAN4"
  ipv4       = "192.168.1.12"
}

resource "stackit_network_interface" "lan5" {
  project_id = var.project_id
  network_id = data.stackit_network.versa-network.network_id
  security   = false
  name       = "LAN5"
  ipv4       = "10.0.1.13"
}

resource "stackit_network_interface" "lan6" {
  project_id = var.project_id
  network_id = data.stackit_network.versa-mgmt-network.network_id
  security   = false
  name       = "LAN6"
  ipv4       = "192.168.1.13"
}

resource "stackit_network_interface" "lan7" {
  project_id = var.project_id
  network_id = data.stackit_network.versa-network.network_id
  security   = false
  name       = "LAN7"
  ipv4       = "10.0.1.14"
}

resource "stackit_network_interface" "lan8" {
  project_id = var.project_id
  network_id = data.stackit_network.versa-mgmt-network.network_id
  security   = false
  name       = "LAN8"
  ipv4       = "192.168.1.14"
}

resource "stackit_network_interface" "lan9" {
  project_id = var.project_id
  network_id = data.stackit_network.versa-network.network_id
  security   = false
  name       = "LAN9"
  ipv4       = "10.0.1.15"
}

resource "stackit_network_interface" "lan10" {
  project_id = var.project_id
  network_id = data.stackit_network.versa-mgmt-network.network_id
  security   = false
  name       = "LAN10"
  ipv4       = "192.168.1.15"
}

resource "stackit_network_interface" "lan11" {
  project_id         = var.project_id
  network_id         = data.stackit_network.versa-network.network_id
  security           = false
  name               = "LAN11"
  ipv4               = "10.0.1.16"
}

resource "stackit_network_interface" "lan12" {
  project_id         = var.project_id
  network_id         = data.stackit_network.versa-mgmt-network.network_id
  security           = false
  name               = "LAN12"
  ipv4               = "192.168.1.16"
}

resource "stackit_network_interface" "lan13" {
  project_id         = var.project_id
  network_id         = data.stackit_network.versa-network.network_id
  security           = false
  name               = "LAN13"
  ipv4               = "10.0.1.17"
}

resource "stackit_network_interface" "lan14" {
  project_id         = var.project_id
  network_id         = data.stackit_network.versa-mgmt-network.network_id
  security           = false
  name               = "LAN14"
  ipv4               = "192.168.1.17"
}

resource "stackit_network_interface" "lan15" {
  project_id         = var.project_id
  network_id         = data.stackit_network.versa-network.network_id
  security           = false
  name               = "LAN15"
  ipv4               = "10.0.1.18"
}

resource "stackit_network_interface" "lan16" {
  project_id = var.project_id
  network_id = data.stackit_network.versa-mgmt-network.network_id
  security   = false
  name       = "LAN16"
  ipv4       = "192.168.1.18"
}

resource "stackit_network_interface" "lan17" {
  project_id         = var.project_id
  network_id         = data.stackit_network.versa-network.network_id
  security           = false
  name               = "LAN17"
  ipv4               = "10.0.1.19"
}

resource "stackit_network_interface" "lan18" {
  project_id = var.project_id
  network_id = data.stackit_network.versa-mgmt-network.network_id
  security   = false
  name       = "LAN18"
  ipv4       = "192.168.1.19"
}

resource "stackit_network_interface" "lan19" {
  project_id         = var.project_id
  network_id         = data.stackit_network.versa-network.network_id
  security           = false
  name               = "LAN19"
  ipv4               = "10.0.1.20"
}

resource "stackit_network_interface" "lan20" {
  project_id = var.project_id
  network_id = data.stackit_network.versa-mgmt-network.network_id
  security   = false
  name       = "LAN20"
  ipv4       = "192.168.1.20"
}

resource "stackit_network_interface" "lan21" {
  project_id         = var.project_id
  network_id         = data.stackit_network.versa-network.network_id
  security           = false
  name               = "LAN21"
  ipv4               = "10.0.1.21"
}

resource "stackit_network_interface" "lan22" {
  project_id = var.project_id
  network_id = data.stackit_network.versa-mgmt-network.network_id
  security   = false
  name       = "LAN22"
  ipv4       = "192.168.1.21"
}

resource "stackit_public_ip" "director_public_ip" {
  project_id           = var.project_id
  network_interface_id = stackit_network_interface.lan5.network_interface_id
}

# resource "stackit_public_ip" "analytics-1-public-ip" {
#  project_id           = var.project_id
#  network_interface_id = stackit_network_interface.lan1.network_interface_id
#}
=======
  ipv4       = "b.b.b.b"
}

resource "stackit_public_ip" "server1_public_ip" {
  project_id           = var.project_id
  network_interface_id = stackit_network_interface.lan1.network_interface_id
}

>>>>>>> stackit/01_network.tf
# resource "stackit_public_ip" "server2_public_ip" {
#     project_id = var.project_id
#     network_interface_id = stackit_network_interface.lan2.network_interface_id
# }

// Security Group and Security Group Rules
resource "stackit_security_group" "sg1" {
  project_id = var.project_id
  name       = "sg1"
}

resource "stackit_security_group_rule" "ssh_ingress" {
  security_group_id = stackit_security_group.sg1.security_group_id
  project_id        = var.project_id
  direction         = "ingress"
  protocol = {
    name = "tcp"
  }
  port_range = {
    max = 22
    min = 22
  }
}

resource "stackit_security_group_rule" "icmp_ingress" {
  security_group_id = stackit_security_group.sg1.security_group_id
  project_id        = var.project_id
  direction         = "ingress"
  icmp_parameters = {
    code = 0
    type = 8
  }
  protocol = {
    name = "icmp"
  }
}

resource "stackit_security_group_rule" "icmp_egress" {
  security_group_id = stackit_security_group.sg1.security_group_id
  project_id        = var.project_id
  direction         = "egress"
  icmp_parameters = {
    code = 0
    type = 8
  }
  protocol = {
    name = "icmp"
  }
}
