output "Versa_Concerto-1_Instance" {
  value = azurerm_virtual_machine.concertoVM[0].name
}

output "Versa_Concerto-1_MGMT_IP" {
  value = azurerm_network_interface.concerto_nic_1[0].private_ip_address
}

output "Versa_Concerto-1_Public_IP" {
  value = data.azurerm_public_ip.concerto_pub_ip[0].ip_address
}

output "Versa_Concerto-1_CLI_sshCommand" {
  value = "ssh -i id_rsa admin@${data.azurerm_public_ip.concerto_pub_ip[0].ip_address}"
}

output "Versa_Concerto-2_Instance" {
  value = azurerm_virtual_machine.concertoVM[1].name
}

output "Versa_Concerto-2_MGMT_IP" {
  value = azurerm_network_interface.concerto_nic_1[1].private_ip_address
}

output "Versa_Concerto-2_Public_IP" {
  value = data.azurerm_public_ip.concerto_pub_ip[1].ip_address
}

output "Versa_Concerto-2_CLI_sshCommand" {
  value = "ssh -i id_rsa admin@${data.azurerm_public_ip.concerto_pub_ip[1].ip_address}"
}

output "Versa_Concerto-3_Instance" {
  value = azurerm_virtual_machine.concertoVM[2].name
}

output "Versa_Concerto-3_MGMT_IP" {
  value = azurerm_network_interface.concerto_nic_1[2].private_ip_address
}

output "Versa_Concerto-3_Public_IP" {
  value = data.azurerm_public_ip.concerto_pub_ip[2].ip_address
}

output "Versa_Concerto-3_CLI_sshCommand" {
  value = "ssh -i id_rsa admin@${data.azurerm_public_ip.concerto_pub_ip[2].ip_address}"
}
