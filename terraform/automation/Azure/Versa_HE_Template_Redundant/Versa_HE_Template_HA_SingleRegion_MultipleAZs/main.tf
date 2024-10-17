terraform {
  required_version = ">=0.13.0, <=0.14.10"
  required_providers {
    azurerm = {
      version = "~>2.55"
    }
    random = {
      version = "~>3.1"
    }
    template = {
      version = "~>2.2"
    }
  }
}

# Configure the Microsoft Azure Provider
provider "azurerm" {
  subscription_id = var.subscription_id
  client_id       = var.client_id
  client_secret   = var.client_secret
  tenant_id       = var.tenant_id
  features {}
}

# Create a resource group
resource "azurerm_resource_group" "versa_rg" {
  name     = var.resource_group
  location = var.location

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Add template to use custom data for Director:
data "template_file" "user_data_dir" {
  count    = length(var.hostname_director)
  template = file("director-${1 + count.index}.sh")

  vars = {
    hostname_dir_master = var.hostname_director[0]
    hostname_dir_slave  = var.hostname_director[1]
    dir_master_mgmt_ip  = azurerm_network_interface.director_nic_1[0].private_ip_address
    dir_slave_mgmt_ip   = azurerm_network_interface.director_nic_1[1].private_ip_address
    hostname_van_1      = var.hostname_van[0]
    hostname_van_2      = var.hostname_van[1]
    hostname_van_3      = var.hostname_van[2]
    hostname_van_4      = var.hostname_van[3]
    van_1_mgmt_ip       = azurerm_network_interface.van_nic_1[0].private_ip_address
    van_2_mgmt_ip       = azurerm_network_interface.van_nic_1[1].private_ip_address
    van_3_mgmt_ip       = azurerm_network_interface.van_nic_1[2].private_ip_address
    van_4_mgmt_ip       = azurerm_network_interface.van_nic_1[3].private_ip_address
    sshkey              = var.ssh_key
  }
}

# Add template to use custom data for Controller:
data "template_file" "user_data_ctrl" {
  count    = length(var.hostname_director)
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

# Create virtual network
resource "azurerm_virtual_network" "versaNetwork" {
  name                = "Versa_VPC"
  address_space       = [var.vpc_address_space]
  location            = var.location
  resource_group_name = azurerm_resource_group.versa_rg.name

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Create Route Table
resource "azurerm_route_table" "versa_udr" {
  name                = "VersaRouteTable"
  location            = var.location
  resource_group_name = azurerm_resource_group.versa_rg.name
}

# Add Route in Route Table
resource "azurerm_route" "versa_route" {
  name                   = "VersaRoute"
  resource_group_name    = azurerm_resource_group.versa_rg.name
  route_table_name       = azurerm_route_table.versa_udr.name
  address_prefix         = "0.0.0.0/0"
  next_hop_type          = "VirtualAppliance"
  next_hop_in_ip_address = azurerm_network_interface.controller_nic_2[0].private_ip_address
}

# Create Management Subnet
resource "azurerm_subnet" "mgmt_subnet" {
  name                 = "MGMT-NET"
  resource_group_name  = azurerm_resource_group.versa_rg.name
  virtual_network_name = azurerm_virtual_network.versaNetwork.name
  address_prefixes     = [cidrsubnet(azurerm_virtual_network.versaNetwork.address_space[0], var.newbits_subnet, 1, )]
}

# Create Traffic Subnet for Director, Controller and Analytics
resource "azurerm_subnet" "ctrl_network_subnet" {
  name                 = "Control-Network"
  resource_group_name  = azurerm_resource_group.versa_rg.name
  virtual_network_name = azurerm_virtual_network.versaNetwork.name
  address_prefixes     = [cidrsubnet(azurerm_virtual_network.versaNetwork.address_space[0], var.newbits_subnet, 2, )]
}

# Create VAN Traffic Subnet for internal communication between Analytics nodes
resource "azurerm_subnet" "van_internal_network_subnet" {
  name                 = "VAN-Internal-Network"
  resource_group_name  = azurerm_resource_group.versa_rg.name
  virtual_network_name = azurerm_virtual_network.versaNetwork.name
  address_prefixes     = [cidrsubnet(azurerm_virtual_network.versaNetwork.address_space[0], var.newbits_subnet, 3, )]
}

# Create Internet transport Traffic Subnet for Controller and Branch
resource "azurerm_subnet" "inet_network_subnet" {
  name                 = "INET-Network"
  resource_group_name  = azurerm_resource_group.versa_rg.name
  virtual_network_name = azurerm_virtual_network.versaNetwork.name
  address_prefixes     = [cidrsubnet(azurerm_virtual_network.versaNetwork.address_space[0], var.newbits_subnet, 4, )]
}

# Create WAN transport Traffic Subnet for Controller and Branch
resource "azurerm_subnet" "wan_network_subnet" {
  name                 = "WAN-Network"
  resource_group_name  = azurerm_resource_group.versa_rg.name
  virtual_network_name = azurerm_virtual_network.versaNetwork.name
  address_prefixes     = [cidrsubnet(azurerm_virtual_network.versaNetwork.address_space[0], var.newbits_subnet, 5, )]
}

# Associate Route Table to Subnet
resource "azurerm_subnet_route_table_association" "subnet_rt_table" {
  subnet_id      = azurerm_subnet.ctrl_network_subnet.id
  route_table_id = azurerm_route_table.versa_udr.id
}

# Create Public IP for Director
resource "azurerm_public_ip" "ip_dir" {
  count               = length(var.hostname_director)
  name                = "PublicIP_Director_${1 + count.index}"
  location            = var.location
  resource_group_name = azurerm_resource_group.versa_rg.name
  sku                 = "Standard"
  allocation_method   = "Static"
  zones               = [1 + count.index]

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Create Public IP for Controller
resource "azurerm_public_ip" "ip_ctrl" {
  count               = length(var.hostname_director)
  name                = "PublicIP_Controller_${1 + count.index}"
  location            = var.location
  resource_group_name = azurerm_resource_group.versa_rg.name
  sku                 = "Standard"
  allocation_method   = "Static"
  zones               = [1 + count.index]

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Create Public IP for Controller Internet Interface
resource "azurerm_public_ip" "ip_ctrl_inet" {
  count               = length(var.hostname_director)
  name                = "PublicIP_Controller_${1 + count.index}_INET"
  location            = var.location
  resource_group_name = azurerm_resource_group.versa_rg.name
  sku                 = "Standard"
  allocation_method   = "Static"
  zones               = [1 + count.index]

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Create Public IP for Controller WAN Interface
resource "azurerm_public_ip" "ip_ctrl_wan" {
  count               = length(var.hostname_director)
  name                = "PublicIP_Controller_${1 + count.index}_WAN"
  location            = var.location
  resource_group_name = azurerm_resource_group.versa_rg.name
  sku                 = "Standard"
  allocation_method   = "Static"
  zones               = [1 + count.index]

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Create Public IP for Analytics
resource "azurerm_public_ip" "ip_van" {
  count               = length(var.hostname_van)
  name                = "PublicIP_VAN_${1 + count.index}"
  location            = var.location
  resource_group_name = azurerm_resource_group.versa_rg.name
  sku                 = "Standard"
  allocation_method   = "Static"
  zones               = ["1"]

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Create Network Security Groups and rules for Director
resource "azurerm_network_security_group" "versa_nsg_dir" {
  name                = "VersaDir-NSG"
  location            = var.location
  resource_group_name = azurerm_resource_group.versa_rg.name
  security_rule {
    name                       = "Versa_Security_Rule_TCP"
    priority                   = 151
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_ranges    = ["22", "4566", "4570", "5432", "443", "9182-9183", "2022", "4949", "20514", "6080", "9090"]
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
    environment = "VersaHeadEnd"
  }
}

# Create Network Security Groups and rules for FlexVNF
resource "azurerm_network_security_group" "versa_nsg_vnf" {
  name                = "VersaFlexVNF-NSG"
  location            = var.location
  resource_group_name = azurerm_resource_group.versa_rg.name
  security_rule {
    name                       = "Versa_Security_Rule_TCP"
    priority                   = 151
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_ranges    = ["22", "2022", "1024-1120", "3000-3003", "9878", "8443", "5201"]
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
    environment = "VersaHeadEnd"
  }
}

# Create Network Security Groups and rules for Analytics
resource "azurerm_network_security_group" "versa_nsg_van" {
  name                = "VersaAnalytics-NSG"
  location            = var.location
  resource_group_name = azurerm_resource_group.versa_rg.name
  security_rule {
    name                       = "Versa_Security_Rule_TCP"
    priority                   = 151
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_ranges    = ["22", "443", "2181", "2888", "3888", "7000-7001", "7199", "9042", "9160", "8080", "8443", "1234", "8010", "8020", "5000", "5010", "8008", "8983"]
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
    destination_port_ranges    = ["53", "1234", "123"]
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
    environment = "VersaHeadEnd"
  }
}

# Create Management network interface for Director
resource "azurerm_network_interface" "director_nic_1" {
  count                = length(var.hostname_director)
  name                 = "Director_${1 + count.index}_NIC1"
  location             = var.location
  resource_group_name  = azurerm_resource_group.versa_rg.name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "Director_${1 + count.index}_NIC1_Configuration"
    subnet_id                     = azurerm_subnet.mgmt_subnet.id
    private_ip_address_allocation = "dynamic"
    public_ip_address_id          = azurerm_public_ip.ip_dir[count.index].id
  }

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Create Southbound network interface for Director
resource "azurerm_network_interface" "director_nic_2" {
  count                = length(var.hostname_director)
  name                 = "Director_${1 + count.index}_NIC2"
  location             = var.location
  resource_group_name  = azurerm_resource_group.versa_rg.name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "Director_${1 + count.index}_NIC2_Configuration"
    subnet_id                     = azurerm_subnet.ctrl_network_subnet.id
    private_ip_address_allocation = "dynamic"
  }

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Create Management network interface for Controller
resource "azurerm_network_interface" "controller_nic_1" {
  count                = length(var.hostname_director)
  name                 = "Controller_${1 + count.index}_NIC1"
  location             = var.location
  resource_group_name  = azurerm_resource_group.versa_rg.name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "Controller_${1 + count.index}_NIC1_Configuration"
    subnet_id                     = azurerm_subnet.mgmt_subnet.id
    private_ip_address_allocation = "dynamic"
    public_ip_address_id          = azurerm_public_ip.ip_ctrl[count.index].id
  }

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Create Northbound/Control network interface for Controller
resource "azurerm_network_interface" "controller_nic_2" {
  count                = length(var.hostname_director)
  name                 = "Controller_${1 + count.index}_NIC2"
  location             = var.location
  resource_group_name  = azurerm_resource_group.versa_rg.name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "Controller_${1 + count.index}_NIC2_Configuration"
    subnet_id                     = azurerm_subnet.ctrl_network_subnet.id
    private_ip_address_allocation = "dynamic"
  }

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Create Southbound/INTERNET network interface for Controller
resource "azurerm_network_interface" "controller_nic_3" {
  count                = length(var.hostname_director)
  name                 = "Controller_${1 + count.index}_NIC3"
  location             = var.location
  resource_group_name  = azurerm_resource_group.versa_rg.name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "Controller_${1 + count.index}_NIC3_Configuration"
    subnet_id                     = azurerm_subnet.wan_network_subnet.id
    private_ip_address_allocation = "dynamic"
    public_ip_address_id          = azurerm_public_ip.ip_ctrl_inet[count.index].id
  }

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Create Southbound/WAN network interface for Controller
resource "azurerm_network_interface" "controller_nic_4" {
  count                = length(var.hostname_director)
  name                 = "Controller_${1 + count.index}_NIC4"
  location             = var.location
  resource_group_name  = azurerm_resource_group.versa_rg.name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "Controller_${1 + count.index}_NIC4_Configuration"
    subnet_id                     = azurerm_subnet.wan_network_subnet.id
    private_ip_address_allocation = "dynamic"
    public_ip_address_id          = azurerm_public_ip.ip_ctrl_wan[count.index].id
  }

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Create Management network interface for Analytics
resource "azurerm_network_interface" "van_nic_1" {
  count                = length(var.hostname_van)
  name                 = "VAN_${1 + count.index}_NIC1"
  location             = var.location
  resource_group_name  = azurerm_resource_group.versa_rg.name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "VAN_${1 + count.index}_NIC1_Configuration"
    subnet_id                     = azurerm_subnet.mgmt_subnet.id
    private_ip_address_allocation = "dynamic"
    public_ip_address_id          = azurerm_public_ip.ip_van[count.index].id
  }

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Create Southbound network interface for Analytics
resource "azurerm_network_interface" "van_nic_2" {
  count                = length(var.hostname_van)
  name                 = "VAN_${1 + count.index}_NIC2"
  location             = var.location
  resource_group_name  = azurerm_resource_group.versa_rg.name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "VAN_${1 + count.index}_NIC2_Configuration"
    subnet_id                     = azurerm_subnet.ctrl_network_subnet.id
    private_ip_address_allocation = "dynamic"
  }

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Create internal network communication interface for Analytics
resource "azurerm_network_interface" "van_nic_3" {
  count                = length(var.hostname_van)
  name                 = "VAN_${1 + count.index}_NIC3"
  location             = var.location
  resource_group_name  = azurerm_resource_group.versa_rg.name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "VAN_${1 + count.index}_NIC3_Configuration"
    subnet_id                     = azurerm_subnet.van_internal_network_subnet.id
    private_ip_address_allocation = "dynamic"
  }

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Associate security group to Director Management Network Interface
resource "azurerm_network_interface_security_group_association" "dir_mgmt_nic_nsg" {
  count                     = length(var.hostname_director)
  network_interface_id      = azurerm_network_interface.director_nic_1[count.index].id
  network_security_group_id = azurerm_network_security_group.versa_nsg_dir.id
}

# Associate security group to Director Southbound Network Interface
resource "azurerm_network_interface_security_group_association" "dir_sb_nic_nsg" {
  count                     = length(var.hostname_director)
  network_interface_id      = azurerm_network_interface.director_nic_2[count.index].id
  network_security_group_id = azurerm_network_security_group.versa_nsg_dir.id
}

# Associate security group to Controller Management Network Interface
resource "azurerm_network_interface_security_group_association" "ctrl_mgmt_nic_nsg" {
  count                     = length(var.hostname_director)
  network_interface_id      = azurerm_network_interface.controller_nic_1[count.index].id
  network_security_group_id = azurerm_network_security_group.versa_nsg_vnf.id
}

# Associate security group to Controller Control Network Interface
resource "azurerm_network_interface_security_group_association" "ctrl_nb_nic_nsg" {
  count                     = length(var.hostname_director)
  network_interface_id      = azurerm_network_interface.controller_nic_2[count.index].id
  network_security_group_id = azurerm_network_security_group.versa_nsg_vnf.id
}

# Associate security group to Controller Internet Network Interface
resource "azurerm_network_interface_security_group_association" "ctrl_inet_nic_nsg" {
  count                     = length(var.hostname_director)
  network_interface_id      = azurerm_network_interface.controller_nic_3[count.index].id
  network_security_group_id = azurerm_network_security_group.versa_nsg_vnf.id
}

# Associate security group to Controller WAN Network Interface
resource "azurerm_network_interface_security_group_association" "ctrl_wan_nic_nsg" {
  count                     = length(var.hostname_director)
  network_interface_id      = azurerm_network_interface.controller_nic_4[count.index].id
  network_security_group_id = azurerm_network_security_group.versa_nsg_vnf.id
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

# Associate security group to Analytics Internal Communication Network Interface
resource "azurerm_network_interface_security_group_association" "van_inet_nic_nsg" {
  count                     = length(var.hostname_van)
  network_interface_id      = azurerm_network_interface.van_nic_3[count.index].id
  network_security_group_id = azurerm_network_security_group.versa_nsg_van.id
}

# Generate random text for a unique storage account name
resource "random_id" "randomId" {
  keepers = {
    resource_group = azurerm_resource_group.versa_rg.name
  }

  byte_length = 4
}

# Create storage account for boot diagnostics of Director VM
resource "azurerm_storage_account" "storageaccountDir" {
  count                    = length(var.hostname_director)
  name                     = "dir${1 + count.index}diag${random_id.randomId.hex}"
  resource_group_name      = azurerm_resource_group.versa_rg.name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Create storage account for boot diagnostics of Controller VM
resource "azurerm_storage_account" "storageaccountCtrl" {
  count                    = length(var.hostname_director)
  name                     = "ctrl${1 + count.index}diag${random_id.randomId.hex}"
  resource_group_name      = azurerm_resource_group.versa_rg.name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Create storage account for boot diagnostics of Analytics VM
resource "azurerm_storage_account" "storageaccountVAN" {
  count                    = length(var.hostname_van)
  name                     = "van${1 + count.index}diag${random_id.randomId.hex}"
  resource_group_name      = azurerm_resource_group.versa_rg.name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Create Versa Director Virtual Machine
resource "azurerm_virtual_machine" "directorVM" {
  count                        = length(var.hostname_director)
  name                         = "Versa_Director_${1 + count.index}"
  location                     = var.location
  zones                        = [1 + count.index]
  resource_group_name          = azurerm_resource_group.versa_rg.name
  depends_on                   = [azurerm_network_interface_security_group_association.dir_mgmt_nic_nsg, azurerm_network_interface_security_group_association.dir_sb_nic_nsg]
  network_interface_ids        = [azurerm_network_interface.director_nic_1[count.index].id, azurerm_network_interface.director_nic_2[count.index].id]
  primary_network_interface_id = azurerm_network_interface.director_nic_1[count.index].id
  vm_size                      = var.director_vm_size

  storage_os_disk {
    name              = "Director_${1 + count.index}_OSDisk"
    caching           = "ReadWrite"
    create_option     = "FromImage"
    managed_disk_type = "Standard_LRS"
  }

  storage_image_reference {
    id = var.image_director
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
    environment = "VersaHeadEnd"
  }
}

# Create Versa Controller Virtual Machine
resource "azurerm_virtual_machine" "controllerVM" {
  count                        = length(var.hostname_director)
  name                         = "Versa_Controller_${1 + count.index}"
  location                     = var.location
  zones                        = [1 + count.index]
  resource_group_name          = azurerm_resource_group.versa_rg.name
  depends_on                   = [azurerm_network_interface_security_group_association.ctrl_mgmt_nic_nsg, azurerm_network_interface_security_group_association.ctrl_nb_nic_nsg, azurerm_network_interface_security_group_association.ctrl_inet_nic_nsg, azurerm_network_interface_security_group_association.ctrl_wan_nic_nsg]
  network_interface_ids        = [azurerm_network_interface.controller_nic_1[count.index].id, azurerm_network_interface.controller_nic_2[count.index].id, azurerm_network_interface.controller_nic_3[count.index].id, azurerm_network_interface.controller_nic_4[count.index].id]
  primary_network_interface_id = azurerm_network_interface.controller_nic_1[count.index].id
  vm_size                      = var.controller_vm_size

  storage_os_disk {
    name              = "Controller_${1 + count.index}_OSDisk"
    caching           = "ReadWrite"
    create_option     = "FromImage"
    managed_disk_type = "Standard_LRS"
  }

  storage_image_reference {
    id = var.image_controller
  }

  os_profile {
    computer_name  = "versa-flexvnf"
    admin_username = "versa_devops"
    custom_data    = data.template_file.user_data_ctrl[count.index].rendered
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
    environment = "VersaHeadEnd"
  }
}

# Create Versa Analytics Virtual Machine
resource "azurerm_virtual_machine" "vanVM" {
  count                        = length(var.hostname_van)
  name                         = "Versa_Analytics_${1 + count.index}"
  location                     = var.location
  zones                        = ["1"]
  resource_group_name          = azurerm_resource_group.versa_rg.name
  depends_on                   = [azurerm_network_interface_security_group_association.van_mgmt_nic_nsg, azurerm_network_interface_security_group_association.van_sb_nic_nsg, azurerm_network_interface_security_group_association.van_inet_nic_nsg]
  network_interface_ids        = [azurerm_network_interface.van_nic_1[count.index].id, azurerm_network_interface.van_nic_2[count.index].id, azurerm_network_interface.van_nic_3[count.index].id]
  primary_network_interface_id = azurerm_network_interface.van_nic_1[count.index].id
  vm_size                      = var.analytics_vm_size

  storage_os_disk {
    name              = "VAN_${1 + count.index}_OSDisk"
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
    environment = "VersaHeadEnd"
  }
}

data "azurerm_public_ip" "dir_pub_ip" {
  count               = length(var.hostname_director)
  name                = azurerm_public_ip.ip_dir[count.index].name
  resource_group_name = azurerm_resource_group.versa_rg.name
  depends_on          = [azurerm_virtual_machine.directorVM]
}

data "azurerm_public_ip" "ctrl_pub_ip" {
  count               = length(var.hostname_director)
  name                = azurerm_public_ip.ip_ctrl[count.index].name
  resource_group_name = azurerm_resource_group.versa_rg.name
  depends_on          = [azurerm_virtual_machine.controllerVM]
}

data "azurerm_public_ip" "ctrl_inet_pub_ip" {
  count               = length(var.hostname_director)
  name                = azurerm_public_ip.ip_ctrl_inet[count.index].name
  resource_group_name = azurerm_resource_group.versa_rg.name
  depends_on          = [azurerm_virtual_machine.controllerVM]
}

data "azurerm_public_ip" "ctrl_wan_pub_ip" {
  count               = length(var.hostname_director)
  name                = azurerm_public_ip.ip_ctrl_wan[count.index].name
  resource_group_name = azurerm_resource_group.versa_rg.name
  depends_on          = [azurerm_virtual_machine.controllerVM]
}

data "azurerm_public_ip" "van_pub_ip" {
  count               = length(var.hostname_van)
  name                = azurerm_public_ip.ip_van[count.index].name
  resource_group_name = azurerm_resource_group.versa_rg.name
  depends_on          = [azurerm_virtual_machine.vanVM]
}
