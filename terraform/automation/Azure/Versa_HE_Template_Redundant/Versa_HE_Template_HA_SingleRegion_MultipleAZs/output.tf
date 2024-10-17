output "Versa_Director-1_Instance" {
  value = azurerm_virtual_machine.directorVM[0].name
}

output "Versa_Director-1_MGMT_IP" {
  value = azurerm_network_interface.director_nic_1[0].private_ip_address
}

output "Versa_Director-1_Public_IP" {
  value = data.azurerm_public_ip.dir_pub_ip[0].ip_address
}

output "Versa_Director-1_CLI_sshCommand" {
  value = "ssh -i id_rsa Administrator@${data.azurerm_public_ip.dir_pub_ip[0].ip_address}"
}

output "Versa_Director-1_UI_Login" {
  value = "https://${data.azurerm_public_ip.dir_pub_ip[0].ip_address}"
}

output "Versa_Director-2_Instance" {
  value = azurerm_virtual_machine.directorVM[1].name
}

output "Versa_Director-2_MGMT_IP" {
  value = azurerm_network_interface.director_nic_1[1].private_ip_address
}

output "Versa_Director-2_Public_IP" {
  value = data.azurerm_public_ip.dir_pub_ip[1].ip_address
}

output "Versa_Director-2_CLI_sshCommand" {
  value = "ssh -i id_rsa Administrator@${data.azurerm_public_ip.dir_pub_ip[1].ip_address}"
}

output "Versa_Director-2_UI_Login" {
  value = "https://${data.azurerm_public_ip.dir_pub_ip[1].ip_address}"
}

output "Versa_Controller-1_Instance" {
  value = azurerm_virtual_machine.controllerVM[0].name
}

output "Versa_Controller-1_MGMT_IP" {
  value = azurerm_network_interface.controller_nic_1[0].private_ip_address
}

output "Versa_Controller-1_Public_IP" {
  value = data.azurerm_public_ip.ctrl_pub_ip[0].ip_address
}

output "Versa_Controller-1_CLI_sshCommand" {
  value = "ssh -i id_rsa admin@${data.azurerm_public_ip.ctrl_pub_ip[0].ip_address}"
}

output "Versa_Controller-1_InternetTransport_Public_IP" {
  value = data.azurerm_public_ip.ctrl_inet_pub_ip[0].ip_address
}

output "Versa_Controller-1_WanTransport_Public_IP" {
  value = data.azurerm_public_ip.ctrl_wan_pub_ip[0].ip_address
}

output "Versa_Controller-2_Instance" {
  value = azurerm_virtual_machine.controllerVM[1].name
}

output "Versa_Controller-2_MGMT_IP" {
  value = azurerm_network_interface.controller_nic_1[1].private_ip_address
}

output "Versa_Controller-2_Public_IP" {
  value = data.azurerm_public_ip.ctrl_pub_ip[1].ip_address
}

output "Versa_Controller-2_CLI_sshCommand" {
  value = "ssh -i id_rsa admin@${data.azurerm_public_ip.ctrl_pub_ip[1].ip_address}"
}

output "Versa_Controller-2_InternetTransport_Public_IP" {
  value = data.azurerm_public_ip.ctrl_inet_pub_ip[1].ip_address
}

output "Versa_Controller-2_WanTransport_Public_IP" {
  value = data.azurerm_public_ip.ctrl_wan_pub_ip[1].ip_address
}

output "Versa_Analytics-1_Instance" {
  value = azurerm_virtual_machine.vanVM[0].name
}

output "Versa_Analytics-1_Instance_MGMT_IP" {
  value = azurerm_network_interface.van_nic_1[0].private_ip_address
}

output "Versa_Analytics-1_Instance_Public_IP" {
  value = data.azurerm_public_ip.van_pub_ip[0].ip_address
}

output "Versa_Analytics-2_Instance" {
  value = azurerm_virtual_machine.vanVM[1].name
}

output "Versa_Analytics-2_Instance_MGMT_IP" {
  value = azurerm_network_interface.van_nic_1[1].private_ip_address
}

output "Versa_Analytics-2_Instance_Public_IP" {
  value = data.azurerm_public_ip.van_pub_ip[1].ip_address
}

output "Versa_Analytics-3_Instance" {
  value = azurerm_virtual_machine.vanVM[2].name
}

output "Versa_Analytics-3_Instance_MGMT_IP" {
  value = azurerm_network_interface.van_nic_1[2].private_ip_address
}

output "Versa_Analytics-3_Instance_Public_IP" {
  value = data.azurerm_public_ip.van_pub_ip[2].ip_address
}

output "Versa_Analytics-4_Instance" {
  value = azurerm_virtual_machine.vanVM[3].name
}

output "Versa_Analytics-4_Instance_MGMT_IP" {
  value = azurerm_network_interface.van_nic_1[3].private_ip_address
}

output "Versa_Analytics-4_Instance_Public_IP" {
  value = data.azurerm_public_ip.van_pub_ip[3].ip_address
}
