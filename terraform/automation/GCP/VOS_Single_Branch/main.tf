# Configure the Google Cloud provider
provider "google" {
  credentials = file(var.credentials_file)
  project     = var.project_id
  region      = var.region
}

# Add check for terraform required version
terraform {
  required_version = ">=0.13, <0.14"
  required_providers {
    google   = "<4.0,>= 2.12"
    random   = "~> 3.0"
    template = "~> 2.2"
  }
}

# Generate random text
resource "random_id" "randomId" {
  byte_length = 4
}

# Add template to parse startup script in metadata for Versa HE instances
data "template_file" "user_data_vos" {
  template = file("vos.sh")

  vars = {
    sshkey      = var.ssh_key
    dir_mgmt_ip = var.director_mgmt_ip
  }
}

# Create firewall rule for Management Port of VOS
resource "google_compute_firewall" "firewall_versa_mgmt" {
  name     = "versa-firewall-mgmt-${random_id.randomId.hex}"
  network  = var.mgmt_vpc_name
  priority = 250

  allow {
    protocol = "icmp"
  }

  allow {
    protocol = "tcp"
    ports    = ["22", "2022"]
  }

}

# Create firewall rule for WAN Port of VOS
resource "google_compute_firewall" "firewall_versa_wan" {
  name     = "versa-firewall-wan-${random_id.randomId.hex}"
  network  = var.wan_vpc_name
  priority = 250

  allow {
    protocol = "icmp"
  }

  allow {
    protocol = "tcp"
    ports    = ["22", "2022", "8443", "1024-1120", "3000-3003", "9878"]
  }

  allow {
    protocol = "udp"
    ports    = ["3002-3003", "500", "4500", "4790"]
  }

  allow {
    protocol = "esp"
  }

}

# Create Public IP for Management Interface for VOS instance
resource "google_compute_address" "pub_ip_mgmt" {
  name = "pub-ip-mgmt-vos-${random_id.randomId.hex}"
}

# Create Public IP for WAN Interface for VOS instance
resource "google_compute_address" "pub_ip_wan" {
  name = "pub-ip-wan-vos-${random_id.randomId.hex}"
}

# Create VOS Instance
resource "google_compute_instance" "vm_vos" {
  name                      = "vos-${random_id.randomId.hex}"
  zone                      = var.zone
  allow_stopping_for_update = true
  can_ip_forward            = true
  labels                    = var.labels
  machine_type              = var.machine_type_vos

  boot_disk {
    initialize_params {
      image = var.vos_image
    }
  }

  network_interface {
    subnetwork = var.mgmt_subnet_name
    access_config {
      nat_ip = google_compute_address.pub_ip_mgmt.address
    }
  }

  network_interface {
    subnetwork = var.wan_subnet_name
    access_config {
      nat_ip = google_compute_address.pub_ip_wan.address
    }
  }

  network_interface {
    subnetwork = var.lan_subnet_name
  }

  metadata_startup_script = data.template_file.user_data_vos.rendered
}
