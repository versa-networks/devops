output "vos_insatnce_id" {
  value = google_compute_instance.vm_vos.id
}

output "vos_mgmt_public_ip" {
  value = google_compute_instance.vm_vos.network_interface[0].access_config.0.nat_ip
}
