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
  value = "https://${data.azurerm_public_ip.dir_pub_ip[0].ip_address}\n"
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
  value = "https://${data.azurerm_public_ip.dir_pub_ip[1].ip_address}\n"
}

output "Versa_Router-1_Instance" {
  value = azurerm_virtual_machine.routerVM[0].name
}

output "Versa_Router-1_MGMT_IP" {
  value = azurerm_network_interface.router_nic_1[0].private_ip_address
}

output "Versa_Router-1_Public_IP" {
  value = data.azurerm_public_ip.router_pub_ip[0].ip_address
}

output "Versa_Router-1_CLI_sshCommand" {
  value = "ssh -i id_rsa admin@${data.azurerm_public_ip.router_pub_ip[0].ip_address}"
}

output "Versa_Router-2_Instance" {
  value = azurerm_virtual_machine.routerVM[1].name
}

output "Versa_Router-2_MGMT_IP" {
  value = azurerm_network_interface.router_nic_1[1].private_ip_address
}

output "Versa_Router-2_Public_IP" {
  value = data.azurerm_public_ip.router_pub_ip[1].ip_address
}

output "Versa_Router-2_CLI_sshCommand" {
  value = "ssh -i id_rsa admin@${data.azurerm_public_ip.router_pub_ip[1].ip_address}"
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

output "Versa_Controller-1_WAN_Public_IP" {
  value = "${data.azurerm_public_ip.ctrl_wan_pub_ip[0].ip_address}\n"
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

output "Versa_Controller-2_WAN_Public_IP" {
  value = "${data.azurerm_public_ip.ctrl_wan_pub_ip[1].ip_address}\n"
}

output "Versa_Analytics_Instances" {
  value = azurerm_virtual_machine.vanVM[*].name
}

output "Versa_Analytics_Instances_MGMT_IP" {
  value = azurerm_network_interface.van_nic_1[*].private_ip_address
}

output "Versa_Analytics_Instances_Public_IP" {
  value = data.azurerm_public_ip.van_pub_ip[*].ip_address
}