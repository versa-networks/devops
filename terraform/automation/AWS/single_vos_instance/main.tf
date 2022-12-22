# Configure the AWS Provider
provider "aws" {

    region = var.region
    access_key = var.access_key
    secret_key = var.secret_key
}

data "aws_availability_zones" "available" {
  state = "available"
}

#create VPC
resource "aws_vpc" "vos_vpc" {
  cidr_block       = var.cidr_block
  instance_tenancy = "default"

  tags = {
    Name = "${var.device_name}_vpc"
  }
}

#create internet gateway

resource "aws_internet_gateway" "vos_ig" {
  vpc_id = aws_vpc.vos_vpc.id
  tags = {
    Name = "${var.device_name}_ig"
  }
}

#Add default route to the internet gateway

resource "aws_default_route_table" "vos_rt" {
  default_route_table_id = aws_vpc.vos_vpc.default_route_table_id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.vos_ig.id
  }
  tags = {
    Name = "${var.device_name}_rt"
  }
}

#create security group for managment

resource "aws_security_group" "vos_sg_mgnt" {
  name        = "${var.device_name}_sg_mgnt"
  description = "Allow SSH inbound for managment traffic"
  vpc_id      = aws_vpc.vos_vpc.id 
    
  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "SSH for mgnt"
    from_port        = 22
    to_port          = 22
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
  }
  tags = {
    Name = "${var.device_name}_sg_mgnt"
  }
}

#create security group for internet

resource "aws_security_group" "vos_sg_internet" {
  name        = "${var.device_name}_sg_internet"
  description = "Allow SDWAN inbound traffic"
  vpc_id      = aws_vpc.vos_vpc.id 
    
  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.device_name}_sg_internet"
  }
}

# Add ingress rules to the internet security group


resource "aws_security_group_rule" "vos_sg_internet_tcp_rules" {
  count = length(var.tcp_port)
  type              = "ingress"
  from_port         = var.tcp_port[count.index]
  to_port           = var.tcp_port[count.index]
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.vos_sg_internet.id

}
resource "aws_security_group_rule" "vos_sg_internet_udp_rules" {
  count = length(var.udp_port)
  type              = "ingress"
  from_port         = var.udp_port[count.index]
  to_port           = var.udp_port[count.index]
  protocol          = "udp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.vos_sg_internet.id

}

#create security group for LAN

resource "aws_security_group" "vos_sg_lan" {
  name        = "${var.device_name}_sg_lan"
  description = "Allow LAN traffic"
  vpc_id      = aws_vpc.vos_vpc.id 
    
  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
  }
  ingress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
  }
  tags = {
    Name = "${var.device_name}_sg_lan"
  }
}

#create subnet for managment

resource "aws_subnet" "vos_mgnt" {
  vpc_id     = aws_vpc.vos_vpc.id
  cidr_block = var.mgmt_subnet
  availability_zone = "${data.aws_availability_zones.available.names[0]}"
  tags = {
    Name = "${var.device_name}_mgnt"
  }
}

  # create managment interface
resource "aws_network_interface" "vos_mgnt_interface" {
  subnet_id = aws_subnet.vos_mgnt.id
  source_dest_check = false
  security_groups = [aws_security_group.vos_sg_mgnt.id]
    tags = {
    Name = "${var.device_name}_mgnt_interface"
  }
}

#EIPs associated with mgnt network interface

resource "aws_eip" "vos_mgnt_interface_public_ip" {
  vpc                       = true
  network_interface         = aws_network_interface.vos_mgnt_interface.id
}

#create subnet for Internet

resource "aws_subnet" "vos_internet" {
  vpc_id     = aws_vpc.vos_vpc.id
  cidr_block = var.internet_subnet
  availability_zone = "${data.aws_availability_zones.available.names[0]}"
  tags = {
    Name = "${var.device_name}_internet"
  }
}

  # create internet interface

resource "aws_network_interface" "vos_internet_interface" {
  subnet_id = aws_subnet.vos_internet.id
  source_dest_check = false
  security_groups = [aws_security_group.vos_sg_internet.id]
    tags = {
    Name = "${var.device_name}_internet_interface"
  }
}

#EIPs associated with internet network interface
resource "aws_eip" "vos_internet_interface_public_ip" {
  vpc                       = true
  network_interface         = aws_network_interface.vos_internet_interface.id
}

#create subnet for lan

resource "aws_subnet" "vos_lan" {
  vpc_id     = aws_vpc.vos_vpc.id
  cidr_block = var.lan_subnet
  availability_zone = "${data.aws_availability_zones.available.names[0]}"
  tags = {
    Name = "${var.device_name}_lan"
  }
}

  # create lan interface
resource "aws_network_interface" "vos_lan_interface" {
  subnet_id = aws_subnet.vos_lan.id
  source_dest_check = false
  security_groups = [aws_security_group.vos_sg_lan.id]  
    tags = {
    Name = "${var.device_name}_lan_interface"
  }
}


#create Ec2 instance

resource "aws_instance" "vos_tf_vos" {
    
    ami = var.ami
    instance_type = var.instance_type
    root_block_device {
      delete_on_termination = true
    }
    availability_zone = "${data.aws_availability_zones.available.names[0]}"
    network_interface {
      network_interface_id = aws_network_interface.vos_mgnt_interface.id
      device_index         = 0
    }    
    network_interface {
      network_interface_id = aws_network_interface.vos_internet_interface.id
      device_index         = 1
    }
    network_interface {
      network_interface_id = aws_network_interface.vos_lan_interface.id
      device_index         = 2
    }
    user_data = <<-EOF
      #!bin/bash
      sed -i.bak "\$a\Match Address ${var.dir_southbouth_ip}/32\n  PasswordAuthentication yes\nMatch all" /etc/ssh/sshd_config
      sudo service ssh restart
      EOF
    provisioner "file" {
    source      = "init_staging.sh"
    destination = "/tmp/init_staging.sh"
    connection {
      type = "ssh"
      host = "${aws_eip.vos_mgnt_interface_public_ip.public_ip}"
      user = "admin"
      # private_key = file("/Users/dinz/Downloads/${var.key_pair_name}.pem")
      private_key = file("${var.key_pair_file_path}/${var.key_pair_name}.pem")
    }
    }
    provisioner "remote-exec" {
      inline = [
        "echo 'sleep 1m' >> /tmp/init_staging.sh",
        "echo 'sudo -S < <(echo 'versa123') /opt/versa/scripts/staging.py -w 0 -c ${var.controller_ip} -s ${aws_eip.vos_internet_interface_public_ip.private_ip}/24 -g ${var.internet_gw} -l ${var.local_identifier} -r ${var.remote_identifier} -n ${var.serial_number}' >> /tmp/init_staging.sh",
        "chmod +x /tmp/init_staging.sh",
        "/tmp/init_staging.sh",
       ]
    connection {
      type = "ssh"
      host = "${aws_eip.vos_mgnt_interface_public_ip.public_ip}"
      user = "admin"
      # private_key = file("/Users/dinz/Downloads/${var.key_pair_name}.pem")
      private_key = file("${var.key_pair_file_path}/${var.key_pair_name}.pem")
    }
    }
    key_name = "${var.key_pair_name}"
    tags = {
      "name" = "${var.device_name}_tf_vos"
    }
}
