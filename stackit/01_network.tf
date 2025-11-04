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
  security           = true
  name               = "LAN1"
  ipv4               = "x.x.x.x"
  security_group_ids = [stackit_security_group.sg1.security_group_id]
}

resource "stackit_network_interface" "lan2" {
  project_id = var.project_id
  network_id = data.stackit_network.versa-mgmt-network.network_id
  security   = false
  name       = "LAN2"
  ipv4       = "y.y.y.y"
}

resource "stackit_network_interface" "lan3" {
  project_id = var.project_id
  network_id = data.stackit_network.versa-network.network_id
  security   = false
  name       = "LAN3"
  ipv4       = "a.a.a.a"
}

resource "stackit_network_interface" "lan4" {
  project_id = var.project_id
  network_id = data.stackit_network.versa-mgmt-network.network_id
  security   = false
  name       = "LAN4"
  ipv4       = "b.b.b.b"
}

resource "stackit_public_ip" "server1_public_ip" {
  project_id           = var.project_id
  network_interface_id = stackit_network_interface.lan1.network_interface_id
}

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
