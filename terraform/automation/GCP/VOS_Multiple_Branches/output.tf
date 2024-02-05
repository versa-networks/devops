output "vos_insatnce_ids" {
  value = google_compute_instance.vm_vos[*].id
}

output "vos_mgmt_public_ips" {
  value = google_compute_instance.vm_vos[*].network_interface[0].access_config.0.nat_ip
}
