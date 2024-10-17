output "Versa_Director_Instance" {
  value = azurerm_virtual_machine.directorVM.name
}

output "Versa_Director_MGMT_IP" {
  value = azurerm_network_interface.director_nic_1.private_ip_address
}

output "Versa_Director_Public_IP" {
  value = data.azurerm_public_ip.dir_pub_ip.ip_address
}

output "Versa_Director_CLI_sshCommand" {
  value = "ssh -i id_rsa Administrator@${data.azurerm_public_ip.dir_pub_ip.ip_address}"
}

output "Versa_Director_UI_Login" {
  value = "https://${data.azurerm_public_ip.dir_pub_ip.ip_address}\n"
}

output "Versa_Controller_Instance" {
  value = azurerm_virtual_machine.controllerVM.name
}

output "Versa_Controller_MGMT_IP" {
  value = azurerm_network_interface.controller_nic_1.private_ip_address
}

output "Versa_Controller_Public_IP" {
  value = data.azurerm_public_ip.ctrl_pub_ip.ip_address
}

output "Versa_Controller_CLI_sshCommand" {
  value = "ssh -i id_rsa admin@${data.azurerm_public_ip.ctrl_pub_ip.ip_address}"
}

output "Versa_Controller_WAN_Public_IP" {
  value = "${data.azurerm_public_ip.ctrl_wan_pub_ip.ip_address}\n"
}

output "Versa_Analytics_Instance" {
  value = azurerm_virtual_machine.vanVM.name
}

output "Versa_Analytics_MGMT_IP" {
  value = azurerm_network_interface.van_nic_1.private_ip_address
}

output "Versa_Analytics_Public_IP" {
  value = data.azurerm_public_ip.van_pub_ip.ip_address
}

output "Versa_Analytics_CLI_sshCommand" {
  value = "ssh -i id_rsa versa@${data.azurerm_public_ip.van_pub_ip.ip_address}"
}

output "Versa_Analytics_UI_Login" {
  value = "http://${data.azurerm_public_ip.van_pub_ip.ip_address}:8080\n"
}