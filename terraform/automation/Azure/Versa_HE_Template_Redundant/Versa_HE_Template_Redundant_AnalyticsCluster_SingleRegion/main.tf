# Configure the Microsoft Azure Provider
provider "azurerm" {
  subscription_id = var.subscription_id
  client_id       = var.client_id
  client_secret   = var.client_secret
  tenant_id       = var.tenant_id
  version         = "~>2.6.0"
  features {}
}

provider "random" {
  version = "~> 2.2"
}

provider "template" {
  version = "~> 2.1"
}

# Create a resource group in each region
resource "azurerm_resource_group" "versa_rg" {
  count    = length(var.location)
  name     = "${var.resource_group}-${1 + count.index}"
  location = var.location[count.index]

  tags = {
    environment = "VersaHeadEndHA"
  }
}

# Add template to use custom data for Director:
data "template_file" "user_data_dir" {
  count    = length(var.location)
  template = file("director-${1 + count.index}.sh")

  vars = {
    hostname_dir_master = var.hostname_director[0]
    hostname_dir_slave  = var.hostname_director[1]
    dir_master_mgmt_ip  = azurerm_network_interface.director_nic_1[0].private_ip_address
    dir_slave_mgmt_ip   = azurerm_network_interface.director_nic_1[1].private_ip_address
    hostname_van_1      = var.hostname_van[0]
    hostname_van_2      = var.hostname_van[1]
    van_1_mgmt_ip       = azurerm_network_interface.van_nic_1[0].private_ip_address
    van_2_mgmt_ip       = azurerm_network_interface.van_nic_1[1].private_ip_address
    sshkey              = var.ssh_key
  }
}

# Add template to use custom data for Controller:
data "template_file" "user_data_ctrl" {
  template = file("controller.sh")

  vars = {
    sshkey             = var.ssh_key
    dir_master_mgmt_ip = azurerm_network_interface.director_nic_1[0].private_ip_address
    dir_slave_mgmt_ip  = azurerm_network_interface.director_nic_1[1].private_ip_address
  }
}

# Add template to use custom data for Analytics:
data "template_file" "user_data_van" {
  count    = length(var.hostname_van)
  template = file("van.sh")

  vars = {
    hostname_dir_master = var.hostname_director[0]
    hostname_dir_slave  = var.hostname_director[1]
    dir_master_mgmt_ip  = azurerm_network_interface.director_nic_1[0].private_ip_address
    dir_slave_mgmt_ip   = azurerm_network_interface.director_nic_1[1].private_ip_address
    hostname_van        = var.hostname_van[count.index]
    van_mgmt_ip         = azurerm_network_interface.van_nic_1[count.index].private_ip_address
    sshkey              = var.ssh_key
  }
}

# Create virtual network in each region
resource "azurerm_virtual_network" "versaNetwork" {
  count               = length(var.location)
  name                = "Versa_VNet-${1 + count.index}"
  location            = var.location[count.index]
  address_space       = [var.vpc_address_space[count.index]]
  resource_group_name = azurerm_resource_group.versa_rg[count.index].name

  tags = {
    environment = "VersaHeadEndHA"
  }
}

# Create Route Tables for Director to Router traffic pass through
resource "azurerm_route_table" "versa_udr_1" {
  count               = length(var.location)
  name                = "VersaRouteTableDir-Router-${1 + count.index}"
  location            = var.location[count.index]
  resource_group_name = azurerm_resource_group.versa_rg[count.index].name
}

# Add Route in Route Tables for Director to Router traffic pass through
resource "azurerm_route" "versa_route_1" {
  count                  = length(var.location)
  name                   = "VersaRouteDir-Router-${1 + count.index}"
  resource_group_name    = azurerm_resource_group.versa_rg[count.index].name
  route_table_name       = azurerm_route_table.versa_udr_1[count.index].name
  address_prefix         = "0.0.0.0/0"
  next_hop_type          = "VirtualAppliance"
  next_hop_in_ip_address = azurerm_network_interface.router_nic_2[count.index].private_ip_address
}

# Create Route Tables for Router to Controller traffic pass through
resource "azurerm_route_table" "versa_udr_2" {
  count               = length(var.location)
  name                = "VersaRouteTableRouter-Ctrl-${1 + count.index}"
  location            = var.location[count.index]
  resource_group_name = azurerm_resource_group.versa_rg[count.index].name
}

# Add Route in Route Tables for Router to Controller traffic pass through
resource "azurerm_route" "versa_route_2" {
  count                  = length(var.location)
  name                   = "VersaRouteRouter-Ctrl-${1 + count.index}"
  resource_group_name    = azurerm_resource_group.versa_rg[count.index].name
  route_table_name       = azurerm_route_table.versa_udr_2[count.index].name
  address_prefix         = "0.0.0.0/0"
  next_hop_type          = "VirtualAppliance"
  next_hop_in_ip_address = azurerm_network_interface.controller_nic_2[count.index].private_ip_address
}

# Create Route Tables for Router to Router traffic pass through
resource "azurerm_route_table" "versa_udr_3" {
  count               = length(var.location)
  name                = "VersaRouteTableRouter-Router-${1 + count.index}"
  location            = var.location[count.index]
  resource_group_name = azurerm_resource_group.versa_rg[count.index].name
}

# Add Route in Route Tables for Router to Router traffic pass through
resource "azurerm_route" "versa_route_3" {
  count                  = length(var.location)
  name                   = "VersaRouteRouter-Router-${1 + count.index}"
  resource_group_name    = azurerm_resource_group.versa_rg[count.index].name
  route_table_name       = azurerm_route_table.versa_udr_3[count.index].name
  address_prefix         = "0.0.0.0/0"
  next_hop_type          = "VirtualAppliance"
  next_hop_in_ip_address = azurerm_network_interface.router_nic_3[1 - count.index].private_ip_address
}

# Create Management Subnet in each region
resource "azurerm_subnet" "mgmt_subnet" {
  count                = length(var.location)
  name                 = "MGMT-NET-${1 + count.index}"
  resource_group_name  = azurerm_resource_group.versa_rg[count.index].name
  virtual_network_name = azurerm_virtual_network.versaNetwork[count.index].name
  address_prefix       = cidrsubnet(element(azurerm_virtual_network.versaNetwork[count.index].address_space, count.index, ), var.newbits_subnet, 1, )
}

# Create Traffic Subnet for Director, Router and Analytics
resource "azurerm_subnet" "dir_router_network_subnet" {
  count                = length(var.location)
  name                 = "Director-Router-Network-${1 + count.index}"
  resource_group_name  = azurerm_resource_group.versa_rg[count.index].name
  virtual_network_name = azurerm_virtual_network.versaNetwork[count.index].name
  address_prefix       = cidrsubnet(element(azurerm_virtual_network.versaNetwork[count.index].address_space, count.index, ), var.newbits_subnet, 2, )
}

# Create Traffic Subnet for Router and Router connectivity
resource "azurerm_subnet" "router_network_subnet" {
  count                = length(var.location)
  name                 = "Router-Router-Network-${1 + count.index}"
  resource_group_name  = azurerm_resource_group.versa_rg[count.index].name
  virtual_network_name = azurerm_virtual_network.versaNetwork[count.index].name
  address_prefix       = cidrsubnet(element(azurerm_virtual_network.versaNetwork[count.index].address_space, count.index, ), var.newbits_subnet, 3, )
}

# Create Traffic Subnet for Router and Controller (Control Network)
resource "azurerm_subnet" "control_network_subnet" {
  count                = length(var.location)
  name                 = "CONTROL-NET-${1 + count.index}"
  resource_group_name  = azurerm_resource_group.versa_rg[count.index].name
  virtual_network_name = azurerm_virtual_network.versaNetwork[count.index].name
  address_prefix       = cidrsubnet(element(azurerm_virtual_network.versaNetwork[count.index].address_space, count.index, ), var.newbits_subnet, 4, )
}

# Create Traffic Subnet for Controller and Branch (WAN Network)
resource "azurerm_subnet" "wan_network_subnet" {
  count                = length(var.location)
  name                 = "WAN-NET-${1 + count.index}"
  resource_group_name  = azurerm_resource_group.versa_rg[count.index].name
  virtual_network_name = azurerm_virtual_network.versaNetwork[count.index].name
  address_prefix       = cidrsubnet(element(azurerm_virtual_network.versaNetwork[count.index].address_space, count.index, ), var.newbits_subnet, 5, )
}

# Create Traffic Subnet for Branch and Client (LAN Network)
resource "azurerm_subnet" "lan_network_subnet" {
  count                = length(var.location)
  name                 = "LAN-NET-${1 + count.index}"
  resource_group_name  = azurerm_resource_group.versa_rg[count.index].name
  virtual_network_name = azurerm_virtual_network.versaNetwork[count.index].name
  address_prefix       = cidrsubnet(element(azurerm_virtual_network.versaNetwork[count.index].address_space, count.index, ), var.newbits_subnet, 6, )
}

# Create Traffic Subnet for Analytics and Analytics (VAN Cluster Network)
resource "azurerm_subnet" "van_network_subnet" {
  name                 = "VAN-NET"
  resource_group_name  = azurerm_resource_group.versa_rg[0].name
  virtual_network_name = azurerm_virtual_network.versaNetwork[0].name
  address_prefix       = cidrsubnet(element(azurerm_virtual_network.versaNetwork[0].address_space, 0, ), var.newbits_subnet, 7, )
}

# Associate Route Table for Director to Router pass through subnet
resource "azurerm_subnet_route_table_association" "dir_subnet_rt_table" {
  count          = length(var.location)
  subnet_id      = azurerm_subnet.dir_router_network_subnet[count.index].id
  route_table_id = azurerm_route_table.versa_udr_1[count.index].id
}

# Associate Route Table for Router to Controller pass through subnet
resource "azurerm_subnet_route_table_association" "ctrl_subnet_rt_table" {
  count          = length(var.location)
  subnet_id      = azurerm_subnet.control_network_subnet[count.index].id
  route_table_id = azurerm_route_table.versa_udr_2[count.index].id
}

# Associate Route Table for Router to Router pass through subnet
resource "azurerm_subnet_route_table_association" "router_subnet_rt_table" {
  count          = length(var.location)
  subnet_id      = azurerm_subnet.router_network_subnet[count.index].id
  route_table_id = azurerm_route_table.versa_udr_3[count.index].id
}

# Create Public IP for Directors
resource "azurerm_public_ip" "ip_dir" {
  count               = length(var.location)
  name                = "PublicIP_Director-${1 + count.index}"
  location            = var.location[count.index]
  resource_group_name = azurerm_resource_group.versa_rg[count.index].name
  allocation_method   = "Dynamic"

  tags = {
    environment = "VersaHeadEndHA"
  }
}

# Create Public IP for Routers
resource "azurerm_public_ip" "ip_router" {
  count               = length(var.location)
  name                = "PublicIP_Router-${1 + count.index}"
  location            = var.location[count.index]
  resource_group_name = azurerm_resource_group.versa_rg[count.index].name
  allocation_method   = "Dynamic"

  tags = {
    environment = "VersaHeadEndHA"
  }
}

# Create Public IP for Controllers
resource "azurerm_public_ip" "ip_ctrl" {
  count               = length(var.location)
  name                = "PublicIP_Controller-${1 + count.index}"
  location            = var.location[count.index]
  resource_group_name = azurerm_resource_group.versa_rg[count.index].name
  allocation_method   = "Dynamic"

  tags = {
    environment = "VersaHeadEndHA"
  }
}

# Create Public IP for Controllers WAN Interface
resource "azurerm_public_ip" "ip_ctrl_wan" {
  count               = length(var.location)
  name                = "PublicIP_Controller-${1 + count.index}_WAN"
  location            = var.location[count.index]
  resource_group_name = azurerm_resource_group.versa_rg[count.index].name
  allocation_method   = "Static"

  tags = {
    environment = "VersaHeadEndHA"
  }
}

# Create Public IP for Analytics
resource "azurerm_public_ip" "ip_van" {
  count               = length(var.hostname_van)
  name                = "PublicIP_VAN-${1 + count.index}"
  location            = var.location[0]
  resource_group_name = azurerm_resource_group.versa_rg[0].name
  allocation_method   = "Dynamic"

  tags = {
    environment = "VersaHeadEndHA"
  }
}

# Create Network Security Groups and rules for Director
resource "azurerm_network_security_group" "versa_nsg_dir" {
  count               = length(var.location)
  name                = "VersaDir-NSG-${1 + count.index}"
  location            = var.location[count.index]
  resource_group_name = azurerm_resource_group.versa_rg[count.index].name
  security_rule {
    name                       = "Versa_Security_Rule_TCP"
    priority                   = 151
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_ranges    = ["22", "4566", "4570", "5432", "443", "9182-9183", "4949", "20514", "6080", "9090"]
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
  security_rule {
    name                       = "Versa_Security_Rule_UDP"
    priority                   = 201
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Udp"
    source_port_range          = "*"
    destination_port_ranges    = ["20514"]
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
  security_rule {
    name                       = "Versa_Security_Rule_Outbound"
    priority                   = 251
    direction                  = "Outbound"
    access                     = "Allow"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  tags = {
    environment = "VersaHeadEndHA"
  }
}

# Create Network Security Groups and rules for FlexVNF
resource "azurerm_network_security_group" "versa_nsg_vnf" {
  count               = length(var.location)
  name                = "VersaFlexVNF-NSG-${1 + count.index}"
  location            = var.location[count.index]
  resource_group_name = azurerm_resource_group.versa_rg[count.index].name
  security_rule {
    name                       = "Versa_Security_Rule_TCP"
    priority                   = 151
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_ranges    = ["22", "2022", "1024-1120", "3000-3003", "9878", "8443"]
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
  security_rule {
    name                       = "Versa_Security_Rule_UDP"
    priority                   = 201
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Udp"
    source_port_range          = "*"
    destination_port_ranges    = ["500", "3002-3003", "4500", "4790"]
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
  security_rule {
    name                       = "Versa_Security_Rule_Outbound"
    priority                   = 251
    direction                  = "Outbound"
    access                     = "Allow"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
  security_rule {
    name                       = "Versa_Security_Rule_ESP"
    priority                   = 301
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "*"
    source_address_prefix      = "VirtualNetwork"
    destination_address_prefix = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
  }

  tags = {
    environment = "VersaHeadEndHA"
  }
}

# Create Network Security Groups and rules for Analytics
resource "azurerm_network_security_group" "versa_nsg_van" {
  name                = "VersaAnalytics-NSG"
  location            = var.location[0]
  resource_group_name = azurerm_resource_group.versa_rg[0].name
  security_rule {
    name                       = "Versa_Security_Rule_TCP"
    priority                   = 151
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_ranges    = ["22", "7000-7001", "7199", "9042", "9160", "8080", "8443", "1234", "5000", "8008", "8983"]
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
  security_rule {
    name                       = "Versa_Security_Rule_UDP"
    priority                   = 201
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Udp"
    source_port_range          = "*"
    destination_port_ranges    = ["1234", "123"]
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
  security_rule {
    name                       = "Versa_Security_Rule_Outbound"
    priority                   = 251
    direction                  = "Outbound"
    access                     = "Allow"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  tags = {
    environment = "VersaHeadEndHA"
  }
}

# Create Management network interface for Directors
resource "azurerm_network_interface" "director_nic_1" {
  count                = length(var.location)
  name                 = "Director-${1 + count.index}_NIC1"
  location             = var.location[count.index]
  resource_group_name  = azurerm_resource_group.versa_rg[count.index].name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "Director-${1 + count.index}_NIC1_Configuration"
    subnet_id                     = azurerm_subnet.mgmt_subnet[count.index].id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.ip_dir[count.index].id
  }

  tags = {
    environment = "VersaHeadEndHA"
  }
}

# Create Southbound network interface for Directors
resource "azurerm_network_interface" "director_nic_2" {
  count                = length(var.location)
  name                 = "Director-${1 + count.index}_NIC2"
  location             = var.location[count.index]
  resource_group_name  = azurerm_resource_group.versa_rg[count.index].name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "Director-${1 + count.index}_NIC2_Configuration"
    subnet_id                     = azurerm_subnet.dir_router_network_subnet[count.index].id
    private_ip_address_allocation = "Dynamic"
  }

  tags = {
    environment = "VersaHeadEndHA"
  }
}

# Create Management network interface for Routers
resource "azurerm_network_interface" "router_nic_1" {
  count                = length(var.location)
  name                 = "Router-${1 + count.index}_NIC1"
  location             = var.location[count.index]
  resource_group_name  = azurerm_resource_group.versa_rg[count.index].name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "Router-${1 + count.index}_NIC1_Configuration"
    subnet_id                     = azurerm_subnet.mgmt_subnet[count.index].id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.ip_router[count.index].id
  }

  tags = {
    environment = "VersaHeadEndHA"
  }
}

# Create Northbound network interface for Routers
resource "azurerm_network_interface" "router_nic_2" {
  count                = length(var.location)
  name                 = "Router-${1 + count.index}_NIC2"
  location             = var.location[count.index]
  resource_group_name  = azurerm_resource_group.versa_rg[count.index].name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "Router-${1 + count.index}_NIC2_Configuration"
    subnet_id                     = azurerm_subnet.dir_router_network_subnet[count.index].id
    private_ip_address_allocation = "Dynamic"
  }

  tags = {
    environment = "VersaHeadEndHA"
  }
}

# Create BGP network interface for Routers (Router to Router connectivity)
resource "azurerm_network_interface" "router_nic_3" {
  count                = length(var.location)
  name                 = "Router-${1 + count.index}_NIC3"
  location             = var.location[count.index]
  resource_group_name  = azurerm_resource_group.versa_rg[count.index].name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "Router-${1 + count.index}_NIC3_Configuration"
    subnet_id                     = azurerm_subnet.router_network_subnet[count.index].id
    private_ip_address_allocation = "Dynamic"
  }

  tags = {
    environment = "VersaHeadEndHA"
  }
}

# Create Southbound network interface for Routers
resource "azurerm_network_interface" "router_nic_4" {
  count                = length(var.location)
  name                 = "Router-${1 + count.index}_NIC4"
  location             = var.location[count.index]
  resource_group_name  = azurerm_resource_group.versa_rg[count.index].name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "Router-${1 + count.index}_NIC4_Configuration"
    subnet_id                     = azurerm_subnet.control_network_subnet[count.index].id
    private_ip_address_allocation = "Dynamic"
  }

  tags = {
    environment = "VersaHeadEndHA"
  }
}

# Create Management network interface for Controllers
resource "azurerm_network_interface" "controller_nic_1" {
  count                = length(var.location)
  name                 = "Controller-${1 + count.index}_NIC1"
  location             = var.location[count.index]
  resource_group_name  = azurerm_resource_group.versa_rg[count.index].name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "Controller-${1 + count.index}_NIC1_Configuration"
    subnet_id                     = azurerm_subnet.mgmt_subnet[count.index].id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.ip_ctrl[count.index].id
  }

  tags = {
    environment = "VersaHeadEndHA"
  }
}

# Create Northbound/Control network interface for Controllers
resource "azurerm_network_interface" "controller_nic_2" {
  count                = length(var.location)
  name                 = "Controller-${1 + count.index}_NIC2"
  location             = var.location[count.index]
  resource_group_name  = azurerm_resource_group.versa_rg[count.index].name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "Controller-${1 + count.index}_NIC2_Configuration"
    subnet_id                     = azurerm_subnet.control_network_subnet[count.index].id
    private_ip_address_allocation = "Dynamic"
  }

  tags = {
    environment = "VersaHeadEndHA"
  }
}

# Create Southbound/WAN network interface for Controllers
resource "azurerm_network_interface" "controller_nic_3" {
  count                = length(var.location)
  name                 = "Controller-${1 + count.index}_NIC3"
  location             = var.location[count.index]
  resource_group_name  = azurerm_resource_group.versa_rg[count.index].name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "Controller-${1 + count.index}_NIC3_Configuration"
    subnet_id                     = azurerm_subnet.wan_network_subnet[count.index].id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.ip_ctrl_wan[count.index].id
  }

  tags = {
    environment = "VersaHeadEndHA"
  }
}

# Create Management network interface for Analytics
resource "azurerm_network_interface" "van_nic_1" {
  count                = length(var.hostname_van)
  name                 = "VAN-${1 + count.index}_NIC1"
  location             = var.location[0]
  resource_group_name  = azurerm_resource_group.versa_rg[0].name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "VAN-${1 + count.index}_NIC1_Configuration"
    subnet_id                     = azurerm_subnet.mgmt_subnet[0].id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.ip_van[count.index].id
  }

  tags = {
    environment = "VersaHeadEndHA"
  }
}

# Create Southbound network interface for Analytics
resource "azurerm_network_interface" "van_nic_2" {
  count                = length(var.hostname_van)
  name                 = "VAN-${1 + count.index}_NIC2"
  location             = var.location[0]
  resource_group_name  = azurerm_resource_group.versa_rg[0].name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "VAN-${1 + count.index}_NIC2_Configuration"
    subnet_id                     = azurerm_subnet.dir_router_network_subnet[0].id
    private_ip_address_allocation = "Dynamic"
  }

  tags = {
    environment = "VersaHeadEndHA"
  }
}

# Create van to van cluster network interface for Analytics
resource "azurerm_network_interface" "van_nic_3" {
  count                = length(var.hostname_van)
  name                 = "VAN-${1 + count.index}_NIC3"
  location             = var.location[0]
  resource_group_name  = azurerm_resource_group.versa_rg[0].name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "VAN-${1 + count.index}_NIC3_Configuration"
    subnet_id                     = azurerm_subnet.van_network_subnet.id
    private_ip_address_allocation = "Dynamic"
  }

  tags = {
    environment = "VersaHeadEndHA"
  }
}

# Associate security group to Director Management Network Interface
resource "azurerm_network_interface_security_group_association" "dir_mgmt_nic_nsg" {
  count                     = length(var.location)
  network_interface_id      = azurerm_network_interface.director_nic_1[count.index].id
  network_security_group_id = azurerm_network_security_group.versa_nsg_dir[count.index].id
}

# Associate security group to Director Southbound Network Interface
resource "azurerm_network_interface_security_group_association" "dir_sb_nic_nsg" {
  count                     = length(var.location)
  network_interface_id      = azurerm_network_interface.director_nic_2[count.index].id
  network_security_group_id = azurerm_network_security_group.versa_nsg_dir[count.index].id
}

# Associate security group to Router Management Network Interface
resource "azurerm_network_interface_security_group_association" "router_mgmt_nic_nsg" {
  count                     = length(var.location)
  network_interface_id      = azurerm_network_interface.router_nic_1[count.index].id
  network_security_group_id = azurerm_network_security_group.versa_nsg_vnf[count.index].id
}

# Associate security group to Router Northbound Network Interface
resource "azurerm_network_interface_security_group_association" "router_nb_nic_nsg" {
  count                     = length(var.location)
  network_interface_id      = azurerm_network_interface.router_nic_2[count.index].id
  network_security_group_id = azurerm_network_security_group.versa_nsg_vnf[count.index].id
}

# Associate security group to Router to Router connectivity Network Interface
resource "azurerm_network_interface_security_group_association" "router_router_nic_nsg" {
  count                     = length(var.location)
  network_interface_id      = azurerm_network_interface.router_nic_3[count.index].id
  network_security_group_id = azurerm_network_security_group.versa_nsg_vnf[count.index].id
}

# Associate security group to Router Southbound Network Interface
resource "azurerm_network_interface_security_group_association" "router_sb_nic_nsg" {
  count                     = length(var.location)
  network_interface_id      = azurerm_network_interface.router_nic_4[count.index].id
  network_security_group_id = azurerm_network_security_group.versa_nsg_vnf[count.index].id
}

# Associate security group to Controller Management Network Interface
resource "azurerm_network_interface_security_group_association" "ctrl_mgmt_nic_nsg" {
  count                     = length(var.location)
  network_interface_id      = azurerm_network_interface.controller_nic_1[count.index].id
  network_security_group_id = azurerm_network_security_group.versa_nsg_vnf[count.index].id
}

# Associate security group to Controller Control Network Interface
resource "azurerm_network_interface_security_group_association" "ctrl_ctrl_nic_nsg" {
  count                     = length(var.location)
  network_interface_id      = azurerm_network_interface.controller_nic_2[count.index].id
  network_security_group_id = azurerm_network_security_group.versa_nsg_vnf[count.index].id
}

# Associate security group to Controller WAN Network Interface
resource "azurerm_network_interface_security_group_association" "ctrl_wan_nic_nsg" {
  count                     = length(var.location)
  network_interface_id      = azurerm_network_interface.controller_nic_3[count.index].id
  network_security_group_id = azurerm_network_security_group.versa_nsg_vnf[count.index].id
}

# Associate security group to Analytics Management Network Interface
resource "azurerm_network_interface_security_group_association" "van_mgmt_nic_nsg" {
  count                     = length(var.hostname_van)
  network_interface_id      = azurerm_network_interface.van_nic_1[count.index].id
  network_security_group_id = azurerm_network_security_group.versa_nsg_van.id
}

# Associate security group to Analytics Southbound Network Interface
resource "azurerm_network_interface_security_group_association" "van_sb_nic_nsg" {
  count                     = length(var.hostname_van)
  network_interface_id      = azurerm_network_interface.van_nic_2[count.index].id
  network_security_group_id = azurerm_network_security_group.versa_nsg_van.id
}

# Associate security group to Analytics to Analytics Cluster Network Interface
resource "azurerm_network_interface_security_group_association" "van_van_nic_nsg" {
  count                     = length(var.hostname_van)
  network_interface_id      = azurerm_network_interface.van_nic_3[count.index].id
  network_security_group_id = azurerm_network_security_group.versa_nsg_van.id
}

# Enable global peering between the two virtual network 
resource "azurerm_virtual_network_peering" "peering" {
  count                        = length(var.location)
  name                         = "VNetPeering-to-${element(azurerm_virtual_network.versaNetwork.*.name, 1 - count.index)}"
  resource_group_name          = azurerm_resource_group.versa_rg[count.index].name
  virtual_network_name         = azurerm_virtual_network.versaNetwork[count.index].name
  remote_virtual_network_id    = element(azurerm_virtual_network.versaNetwork.*.id, 1 - count.index)
  allow_virtual_network_access = true
  allow_forwarded_traffic      = true
  allow_gateway_transit        = false
  depends_on                   = [azurerm_virtual_machine.directorVM, azurerm_virtual_machine.routerVM, azurerm_virtual_machine.controllerVM, azurerm_virtual_machine.vanVM, ]
}

# Generate random text for a unique storage account name
resource "random_id" "randomId" {
  count = length(var.location)
  keepers = {
    resource_group = azurerm_resource_group.versa_rg[count.index].name
  }
  byte_length = 4
}

# Create storage account for boot diagnostics of Director VMs
resource "azurerm_storage_account" "storageaccountDir" {
  count                    = length(var.location)
  name                     = "dir${1 + count.index}diag${random_id.randomId[count.index].hex}"
  resource_group_name      = azurerm_resource_group.versa_rg[count.index].name
  location                 = var.location[count.index]
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = {
    environment = "VersaHeadEndHA"
  }
}

# Create storage account for boot diagnostics of Router VMs
resource "azurerm_storage_account" "storageaccountRouter" {
  count                    = length(var.location)
  name                     = "rout${1 + count.index}diag${random_id.randomId[count.index].hex}"
  resource_group_name      = azurerm_resource_group.versa_rg[count.index].name
  location                 = var.location[count.index]
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = {
    environment = "VersaHeadEndHA"
  }
}

# Create storage account for boot diagnostics of Controller VMs
resource "azurerm_storage_account" "storageaccountCtrl" {
  count                    = length(var.location)
  name                     = "ctrl${1 + count.index}diag${random_id.randomId[count.index].hex}"
  resource_group_name      = azurerm_resource_group.versa_rg[count.index].name
  location                 = var.location[count.index]
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = {
    environment = "VersaHeadEndHA"
  }
}

# Create storage account for boot diagnostics of Analytics VMs
resource "azurerm_storage_account" "storageaccountVAN" {
  count                    = length(var.hostname_van)
  name                     = "van${1 + count.index}diag${random_id.randomId[0].hex}"
  resource_group_name      = azurerm_resource_group.versa_rg[0].name
  location                 = var.location[0]
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = {
    environment = "VersaHeadEndHA"
  }
}

# Create Versa Director Virtual Machine
resource "azurerm_virtual_machine" "directorVM" {
  count                        = length(var.location)
  name                         = "Versa_Director-${1 + count.index}"
  location                     = var.location[count.index]
  resource_group_name          = azurerm_resource_group.versa_rg[count.index].name
  depends_on                   = [azurerm_network_interface_security_group_association.dir_mgmt_nic_nsg, azurerm_network_interface_security_group_association.dir_sb_nic_nsg]
  network_interface_ids        = [azurerm_network_interface.director_nic_1[count.index].id, azurerm_network_interface.director_nic_2[count.index].id]
  primary_network_interface_id = azurerm_network_interface.director_nic_1[count.index].id
  vm_size                      = var.director_vm_size

  storage_os_disk {
    name              = "Director-${1 + count.index}_OSDisk"
    caching           = "ReadWrite"
    create_option     = "FromImage"
    managed_disk_type = "Standard_LRS"
  }

  storage_image_reference {
    id = var.image_director[count.index]
  }

  os_profile {
    computer_name  = var.hostname_director[count.index]
    admin_username = "versa_devops"
    custom_data    = data.template_file.user_data_dir[count.index].rendered
  }

  os_profile_linux_config {
    disable_password_authentication = true
    ssh_keys {
      path     = "/home/versa_devops/.ssh/authorized_keys"
      key_data = var.ssh_key
    }
  }

  boot_diagnostics {
    enabled     = "true"
    storage_uri = azurerm_storage_account.storageaccountDir[count.index].primary_blob_endpoint
  }

  tags = {
    environment = "VersaHeadEndHA"
  }
}

# Create Versa Router FlexVNF Machines
resource "azurerm_virtual_machine" "routerVM" {
  count                        = length(var.location)
  name                         = "Versa_Router-${1 + count.index}"
  location                     = var.location[count.index]
  resource_group_name          = azurerm_resource_group.versa_rg[count.index].name
  depends_on                   = [azurerm_network_interface_security_group_association.router_mgmt_nic_nsg, azurerm_network_interface_security_group_association.router_nb_nic_nsg, azurerm_network_interface_security_group_association.router_router_nic_nsg, azurerm_network_interface_security_group_association.router_sb_nic_nsg]
  network_interface_ids        = [azurerm_network_interface.router_nic_1[count.index].id, azurerm_network_interface.router_nic_2[count.index].id, azurerm_network_interface.router_nic_3[count.index].id, azurerm_network_interface.router_nic_4[count.index].id]
  primary_network_interface_id = azurerm_network_interface.router_nic_1[count.index].id
  vm_size                      = var.router_vm_size

  storage_os_disk {
    name              = "Router-${1 + count.index}_OSDisk"
    caching           = "ReadWrite"
    create_option     = "FromImage"
    managed_disk_type = "Standard_LRS"
  }

  storage_image_reference {
    id = var.image_controller[count.index]
  }

  os_profile {
    computer_name  = "versa-flexvnf"
    admin_username = "versa_devops"
    custom_data    = data.template_file.user_data_ctrl.rendered
  }

  os_profile_linux_config {
    disable_password_authentication = true
    ssh_keys {
      path     = "/home/versa_devops/.ssh/authorized_keys"
      key_data = var.ssh_key
    }
  }

  boot_diagnostics {
    enabled     = "true"
    storage_uri = azurerm_storage_account.storageaccountRouter[count.index].primary_blob_endpoint
  }

  tags = {
    environment = "VersaHeadEndHA"
  }
}

# Create Versa Controller Virtual Machines
resource "azurerm_virtual_machine" "controllerVM" {
  count                        = length(var.location)
  name                         = "Versa_Controller-${1 + count.index}"
  location                     = var.location[count.index]
  resource_group_name          = azurerm_resource_group.versa_rg[count.index].name
  depends_on                   = [azurerm_network_interface_security_group_association.ctrl_mgmt_nic_nsg, azurerm_network_interface_security_group_association.ctrl_ctrl_nic_nsg, azurerm_network_interface_security_group_association.ctrl_wan_nic_nsg]
  network_interface_ids        = [azurerm_network_interface.controller_nic_1[count.index].id, azurerm_network_interface.controller_nic_2[count.index].id, azurerm_network_interface.controller_nic_3[count.index].id]
  primary_network_interface_id = azurerm_network_interface.controller_nic_1[count.index].id
  vm_size                      = var.controller_vm_size

  storage_os_disk {
    name              = "Controller-${1 + count.index}_OSDisk"
    caching           = "ReadWrite"
    create_option     = "FromImage"
    managed_disk_type = "Standard_LRS"
    disk_size_gb      = var.controller_disk_size
  }

  storage_image_reference {
    id = var.image_controller[count.index]
  }

  os_profile {
    computer_name  = "versa-flexvnf"
    admin_username = "versa_devops"
    custom_data    = data.template_file.user_data_ctrl.rendered
  }

  os_profile_linux_config {
    disable_password_authentication = true
    ssh_keys {
      path     = "/home/versa_devops/.ssh/authorized_keys"
      key_data = var.ssh_key
    }
  }

  boot_diagnostics {
    enabled     = "true"
    storage_uri = azurerm_storage_account.storageaccountCtrl[count.index].primary_blob_endpoint
  }

  tags = {
    environment = "VersaHeadEndHA"
  }
}

# Create Versa Analytics Virtual Machines
resource "azurerm_virtual_machine" "vanVM" {
  count                        = length(var.hostname_van)
  name                         = "Versa_Analytics-${1 + count.index}"
  location                     = var.location[0]
  resource_group_name          = azurerm_resource_group.versa_rg[0].name
  depends_on                   = [azurerm_network_interface_security_group_association.van_mgmt_nic_nsg, azurerm_network_interface_security_group_association.van_sb_nic_nsg, azurerm_network_interface_security_group_association.van_van_nic_nsg]
  network_interface_ids        = [azurerm_network_interface.van_nic_1[count.index].id, azurerm_network_interface.van_nic_2[count.index].id, azurerm_network_interface.van_nic_3[count.index].id]
  primary_network_interface_id = azurerm_network_interface.van_nic_1[count.index].id
  vm_size                      = var.analytics_vm_size

  storage_os_disk {
    name              = "VAN-${1 + count.index}_OSDisk"
    caching           = "ReadWrite"
    create_option     = "FromImage"
    managed_disk_type = "Standard_LRS"
    disk_size_gb      = var.van_disk_size
  }

  storage_image_reference {
    id = var.image_analytics
  }

  os_profile {
    computer_name  = var.hostname_van[count.index]
    admin_username = "versa_devops"
    custom_data    = data.template_file.user_data_van[count.index].rendered
  }

  os_profile_linux_config {
    disable_password_authentication = true
    ssh_keys {
      path     = "/home/versa_devops/.ssh/authorized_keys"
      key_data = var.ssh_key
    }
  }

  boot_diagnostics {
    enabled     = "true"
    storage_uri = azurerm_storage_account.storageaccountVAN[count.index].primary_blob_endpoint
  }

  tags = {
    environment = "VersaHeadEndHA"
  }
}

data "azurerm_public_ip" "dir_pub_ip" {
  count               = length(var.location)
  name                = azurerm_public_ip.ip_dir[count.index].name
  resource_group_name = azurerm_resource_group.versa_rg[count.index].name
  depends_on          = [azurerm_virtual_machine.directorVM]
}

data "azurerm_public_ip" "router_pub_ip" {
  count               = length(var.location)
  name                = azurerm_public_ip.ip_router[count.index].name
  resource_group_name = azurerm_resource_group.versa_rg[count.index].name
  depends_on          = [azurerm_virtual_machine.routerVM]
}

data "azurerm_public_ip" "ctrl_pub_ip" {
  count               = length(var.location)
  name                = azurerm_public_ip.ip_ctrl[count.index].name
  resource_group_name = azurerm_resource_group.versa_rg[count.index].name
  depends_on          = [azurerm_virtual_machine.controllerVM]
}

data "azurerm_public_ip" "van_pub_ip" {
  count               = length(var.hostname_van)
  name                = azurerm_public_ip.ip_van[count.index].name
  resource_group_name = azurerm_resource_group.versa_rg[0].name
  depends_on          = [azurerm_virtual_machine.vanVM]
}

data "azurerm_public_ip" "ctrl_wan_pub_ip" {
  count               = length(var.location)
  name                = azurerm_public_ip.ip_ctrl_wan[count.index].name
  resource_group_name = azurerm_resource_group.versa_rg[count.index].name
  depends_on          = [azurerm_virtual_machine.controllerVM]
}