resource "stackit_server" "server1" {
  project_id = var.project_id
  boot_volume = {
    size                  = 100
    source_type           = "image"
    source_id             = "716ccaf5-0e4d-49a8-8931-4c1ac4d350d0"
    performance_class     = "storage_premium_perf14"
    delete_on_termination = true
  }
  availability_zone  = "eu01-1"
  name               = "versa-analytics-analytics-node-1"
  machine_type       = var.flavor
  network_interfaces = [stackit_network_interface.lan1.network_interface_id, stackit_network_interface.lan2.network_interface_id]
}

resource "stackit_server" "server2" {
  project_id = var.project_id
  boot_volume = {
    size                  = 100
    source_type           = "image"
    source_id             = "716ccaf5-0e4d-49a8-8931-4c1ac4d350d0"
    performance_class     = "storage_premium_perf14"
    delete_on_termination = true
  }
  availability_zone  = "eu01-1"
  name               = "versa-analytics-search-node-1"
  machine_type       = var.flavor
  network_interfaces = [stackit_network_interface.lan3.network_interface_id, stackit_network_interface.lan4.network_interface_id]
}

resource "stackit_server" "server3" {
  project_id = var.project_id
  boot_volume = {
    size                  = 150
    source_type           = "image"
    source_id             = "e50be773-2dde-4ff3-a574-dc0810ce27d4"
    performance_class     = "storage_premium_perf0"
    delete_on_termination = true
  }
  availability_zone  = "eu01-1"
  name               = "versa-director-1"
  machine_type       = var.flavor
  network_interfaces = [stackit_network_interface.lan5.network_interface_id, stackit_network_interface.lan6.network_interface_id]
}

resource "stackit_server" "server4" {
  project_id = var.project_id
  boot_volume = {
    size                  = 100
    source_type           = "image"
    source_id             = "716ccaf5-0e4d-49a8-8931-4c1ac4d350d0"
    performance_class     = "storage_premium_perf14"
    delete_on_termination = true
  }
  availability_zone  = "eu01-1"
  name               = "versa-analytics-search-node-2"
  machine_type       = var.flavor
  network_interfaces = [stackit_network_interface.lan7.network_interface_id, stackit_network_interface.lan8.network_interface_id]
}

resource "stackit_server" "server5" {
  project_id = var.project_id
  boot_volume = {
    size                  = 100
    source_type           = "image"
    source_id             = "716ccaf5-0e4d-49a8-8931-4c1ac4d350d0"
    performance_class     = "storage_premium_perf14"
    delete_on_termination = true
  }
  availability_zone  = "eu01-1"
  name               = "versa-analytics-analytics-node-2"
  machine_type       = var.flavor
  network_interfaces = [stackit_network_interface.lan9.network_interface_id, stackit_network_interface.lan10.network_interface_id]
}

resource "stackit_server" "server6" {
  project_id = var.project_id
  boot_volume = {
    size                  = 200
    source_type           = "image"
    source_id             = "716ccaf5-0e4d-49a8-8931-4c1ac4d350d0"
    performance_class     = "storage_premium_perf14"
    delete_on_termination = true
  }
  availability_zone  = "eu01-1"
  name               = "versa-analytics-log-forwarder-node-1"
  machine_type       = var.flavorc2i8
  network_interfaces = [stackit_network_interface.lan11.network_interface_id, stackit_network_interface.lan12.network_interface_id]
}

resource "stackit_server" "server7" {
  project_id = var.project_id
  boot_volume = {
    size                  = 200
    source_type           = "image"
    source_id             = "716ccaf5-0e4d-49a8-8931-4c1ac4d350d0"
    performance_class     = "storage_premium_perf14"
    delete_on_termination = true
  }
  availability_zone  = "eu01-1"
  name               = "versa-analytics-log-forwarder-node-2"
  machine_type       = var.flavorc2i8
  network_interfaces = [stackit_network_interface.lan13.network_interface_id, stackit_network_interface.lan14.network_interface_id]
}

resource "stackit_server" "server8" {
  project_id = var.project_id
  boot_volume = {
    size                  = 1000
    source_type           = "image"
    source_id             = "716ccaf5-0e4d-49a8-8931-4c1ac4d350d0"
    performance_class     = "storage_premium_perf14"
    delete_on_termination = true
  }
  availability_zone  = "eu01-1"
  name               = "versa-analytics-search-node-3"
  machine_type       = var.flavor
  network_interfaces = [stackit_network_interface.lan15.network_interface_id, stackit_network_interface.lan16.network_interface_id]
}

resource "stackit_server" "server9" {
  project_id = var.project_id
  boot_volume = {
    size                  = 1000
    source_type           = "image"
    source_id             = "716ccaf5-0e4d-49a8-8931-4c1ac4d350d0"
    performance_class     = "storage_premium_perf14"
    delete_on_termination = true
  }
  availability_zone  = "eu01-1"
  name               = "versa-analytics-search-node-4"
  machine_type       = var.flavor
  network_interfaces = [stackit_network_interface.lan17.network_interface_id, stackit_network_interface.lan18.network_interface_id]
}

resource "stackit_server" "server10" {
  project_id = var.project_id
  boot_volume = {
    size                  = 200
    source_type           = "image"
    source_id             = "716ccaf5-0e4d-49a8-8931-4c1ac4d350d0"
    performance_class     = "storage_premium_perf14"
    delete_on_termination = true
  }
  availability_zone  = "eu01-1"
  name               = "versa-analytics-log-forwarder-node-3"
  machine_type       = var.flavorc2i8
  network_interfaces = [stackit_network_interface.lan19.network_interface_id, stackit_network_interface.lan20.network_interface_id]
}

resource "stackit_server" "server11" {
  project_id = var.project_id
  boot_volume = {
    size                  = 200
    source_type           = "image"
    source_id             = "716ccaf5-0e4d-49a8-8931-4c1ac4d350d0"
    performance_class     = "storage_premium_perf14"
    delete_on_termination = true
  }
  availability_zone  = "eu01-1"
  name               = "versa-analytics-log-forwarder-node-4"
  machine_type       = var.flavorc2i8
  network_interfaces = [stackit_network_interface.lan21.network_interface_id, stackit_network_interface.lan22.network_interface_id]
}
