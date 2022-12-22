


variable "region" {
  description = "Specifie region for instance creation "
}

variable "access_key" {
    description = "Access key of AWS account to be used to deploy VM on AWS."
}

variable "secret_key" {
    description =  "Secret key of AWS account to be used to deploy VM on AWS."
}

variable "key_pair_name" {
    description = "key pair name for device login"
}

variable "key_pair_file_path" {
  description = "Key file path"
}
variable "device_name"{
  description = "device_name for the instance"
}
variable "cidr_block" {
    description = "IPV4 CIDR for VPC creation"
    # default = "10.193.0.0/16"
}

variable "mgmt_subnet" {
  description = "Management Subnet for VM in AWS"
#   default = "10.193.0.0/24"
}

variable "internet_subnet" {
  description = "Internet Subnet for VM in AWS"
#   default = "10.193.1.0/24"
}

variable "lan_subnet" {
  description = "Lan Subnet for VM in AWS"
#   default = "10.193.2.0/24"
}

variable "tcp_port" {
    description = "Netconf,REST port,Speed Test"
    default = ["2022", "8443","5201"] 
    type = list
}
variable "udp_port" {
    description = "IPsec IKE"
    default = ["500", "4500","4790"] 
    type = list
}

variable "ami" {
    description = "AMI Image to be used to deploy Versa FlexVNF Branch"
}

variable "instance_type" {
    description = "Type of Ec2 instance"
}

variable "dir_southbouth_ip"{
  description = "Director southbound IP for managment"
}

variable "controller_ip"{
    description = "Controller IP for stagging"
}
variable "local_identifier"{
    description = "Local identifier for stagging"
}
variable "remote_identifier"{
    description = "Remote identifier for stagging"
}

variable "serial_number"{
    description = "serial number of the instance"
}
variable "internet_gw"{
    description = "staging internet gayway IP"
}