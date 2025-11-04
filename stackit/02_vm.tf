resource "stackit_server" "server1" {
  project_id = var.project_id
  boot_volume = {
    size                  = 100
    source_type           = "image"
    source_id             = "<image id>"
    performance_class     = "storage_premium_perf0"
    delete_on_termination = true
  }
  availability_zone  = "eu01-1"
  name               = "versa-mgmt-nic-server1"
  machine_type       = var.flavor
  network_interfaces = [stackit_network_interface.lan1.network_interface_id, stackit_network_interface.lan2.network_interface_id]
}

resource "stackit_server" "server2" {
  project_id = var.project_id
  boot_volume = {
    size                  = 100
    source_type           = "image"
    source_id             = "<image id>"
    performance_class     = "storage_premium_perf0"
    delete_on_termination = true
  }
  availability_zone  = "eu01-1"
  name               = "versa-mgmt-nic-server2"
  machine_type       = var.flavor
  network_interfaces = [stackit_network_interface.lan3.network_interface_id, stackit_network_interface.lan4.network_interface_id]
}
