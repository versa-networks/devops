#output "Versa_FlexVNF_Instance" {
#  value = "${azurerm_virtual_machine.flexVNF.*.name}"
#}

#output "Versa_FlexVNF_MGMT_IP" {
#  value = "${azurerm_network_interface.flexvnf_nic_1.*.private_ip_address}"
#}

#output "Versa_FlexVNF_Public_IP" {
#  value = "${data.azurerm_public_ip.flexvnf_pub_ip.*.ip_address}"
#}

#output "Versa_FlexVNF_WAN_IP" {
#  value = "${azurerm_network_interface.flexvnf_nic_2.*.private_ip_address}"
#}

#output "Versa_FlexVNF_LAN_IP" {
#  value = "${azurerm_network_interface.flexvnf_nic_3.*.private_ip_address}"
#}

#output "Versa_FlexVNF_MGMT_Public_IP" {
#  value = "${data.azurerm_public_ip.flexvnf_wan_pub_ip.*.ip_address}"
#}
