#VPC id
output "vpc_id" {
  value = "${aws_vpc.vos_vpc.id}"
}
#Instance ID
output "instance_id" {
  value = "${aws_instance.vos_tf_vos.id}"
}

# Main route table id

output "main_route_table_id" {
    value = "${aws_vpc.vos_vpc.main_route_table_id}"
}
output "internet_gateway" {
    value = "${aws_internet_gateway.vos_ig.id}"
}
#security Group's
output "security_group_internet" {
  value = "${aws_security_group.vos_sg_internet.id}"
}
output "security_group_mgnt" {
  value = "${aws_security_group.vos_sg_mgnt.id}"
}
output "security_group_lan" {
  value = "${aws_security_group.vos_sg_lan.id}"
}

#Public IP

output "mgnt_interface_public_ip" {
  value = "${aws_eip.vos_mgnt_interface_public_ip.public_ip}"
}
output "internet_interface_public_ip" {
  value = "${aws_eip.vos_internet_interface_public_ip.public_ip}"
}

#Private IP
output "mgnt_interface_private_ip" {
  value = "${aws_eip.vos_mgnt_interface_public_ip.private_ip}"
}
output "internet_interface_private_ip" {
  value = "${aws_eip.vos_internet_interface_public_ip.private_ip}"
}
output "lan_interface_private_ip" {
  value = "${aws_network_interface.vos_lan_interface.private_ip}"
}
output "Connect_to_instance" {
  value = "ssh -i ${var.key_pair_name}.pem admin@${aws_eip.vos_mgnt_interface_public_ip.public_ip}"
} 