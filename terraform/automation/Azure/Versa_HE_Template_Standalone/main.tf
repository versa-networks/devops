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
  template = file("director.sh")

  vars = {
    hostname_dir = var.hostname_director
    hostname_van = var.hostname_van
    dir_mgmt_ip  = azurerm_network_interface.director_nic_1.private_ip_address
    sshkey       = var.ssh_key
    van_mgmt_ip  = azurerm_network_interface.van_nic_1.private_ip_address
  }
}

# Add template to use custom data for Controller:
data "template_file" "user_data_ctrl" {
  template = file("controller.sh")

  vars = {
    sshkey      = var.ssh_key
    dir_mgmt_ip = azurerm_network_interface.director_nic_1.private_ip_address
  }
}

# Add template to use custom data for Analytics:
data "template_file" "user_data_van" {
  template = file("van.sh")

  vars = {
    van_mgmt_ip  = azurerm_network_interface.van_nic_1.private_ip_address
    hostname_dir = var.hostname_director
    hostname_van = var.hostname_van
    dir_mgmt_ip  = azurerm_network_interface.director_nic_1.private_ip_address
    sshkey       = var.ssh_key
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
  next_hop_in_ip_address = azurerm_network_interface.controller_nic_2.private_ip_address
}

# Create Management Subnet
resource "azurerm_subnet" "mgmt_subnet" {
  name                 = "MGMT-NET"
  resource_group_name  = azurerm_resource_group.versa_rg.name
  virtual_network_name = azurerm_virtual_network.versaNetwork.name
  address_prefix = cidrsubnet(azurerm_virtual_network.versaNetwork.address_space[0],var.newbits_subnet,1,)
}

# Create Traffic Subnet for Director, Controller and Analytics
resource "azurerm_subnet" "ctrl_network_subnet" {
  name                 = "Control-Network"
  resource_group_name  = azurerm_resource_group.versa_rg.name
  virtual_network_name = azurerm_virtual_network.versaNetwork.name
  address_prefix = cidrsubnet(azurerm_virtual_network.versaNetwork.address_space[0],var.newbits_subnet,2,)
}

# Create Traffic Subnet for Controller and Branch
resource "azurerm_subnet" "wan_network_subnet" {
  name                 = "WAN-Network"
  resource_group_name  = azurerm_resource_group.versa_rg.name
  virtual_network_name = azurerm_virtual_network.versaNetwork.name
  address_prefix = cidrsubnet(azurerm_virtual_network.versaNetwork.address_space[0],var.newbits_subnet,3,)
}

# Associate Route Table to Subnet
resource "azurerm_subnet_route_table_association" "subnet_rt_table" {
  subnet_id      = azurerm_subnet.ctrl_network_subnet.id
  route_table_id = azurerm_route_table.versa_udr.id
}

# Create Public IP for Director
resource "azurerm_public_ip" "ip_dir" {
  name                = "PublicIP_Director"
  location            = var.location
  resource_group_name = azurerm_resource_group.versa_rg.name
  allocation_method   = "Dynamic"

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Create Public IP for Controller
resource "azurerm_public_ip" "ip_ctrl" {
  name                = "PublicIP_Controller"
  location            = var.location
  resource_group_name = azurerm_resource_group.versa_rg.name
  allocation_method   = "Dynamic"

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Create Public IP for Controller WAN Interface
resource "azurerm_public_ip" "ip_ctrl_wan" {
  name                = "PublicIP_Controller_WAN"
  location            = var.location
  resource_group_name = azurerm_resource_group.versa_rg.name
  allocation_method   = "Static"

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Create Public IP for Analytics
resource "azurerm_public_ip" "ip_van" {
  name                = "PublicIP_VAN"
  location            = var.location
  resource_group_name = azurerm_resource_group.versa_rg.name
  allocation_method   = "Dynamic"

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
  name                 = "Director_NIC1"
  location             = var.location
  resource_group_name  = azurerm_resource_group.versa_rg.name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "Director_NIC1_Configuration"
    subnet_id                     = azurerm_subnet.mgmt_subnet.id
    private_ip_address_allocation = "dynamic"
    public_ip_address_id          = azurerm_public_ip.ip_dir.id
  }

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Create Southbound network interface for Director
resource "azurerm_network_interface" "director_nic_2" {
  name                 = "Director_NIC2"
  location             = var.location
  resource_group_name  = azurerm_resource_group.versa_rg.name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "Director_NIC2_Configuration"
    subnet_id                     = azurerm_subnet.ctrl_network_subnet.id
    private_ip_address_allocation = "dynamic"
  }

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Create Management network interface for Controller
resource "azurerm_network_interface" "controller_nic_1" {
  name                 = "Controller_NIC1"
  location             = var.location
  resource_group_name  = azurerm_resource_group.versa_rg.name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "Controller_NIC1_Configuration"
    subnet_id                     = azurerm_subnet.mgmt_subnet.id
    private_ip_address_allocation = "dynamic"
    public_ip_address_id          = azurerm_public_ip.ip_ctrl.id
  }

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Create Northbound/Control network interface for Controller
resource "azurerm_network_interface" "controller_nic_2" {
  name                 = "Controller_NIC2"
  location             = var.location
  resource_group_name  = azurerm_resource_group.versa_rg.name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "Controller_NIC2_Configuration"
    subnet_id                     = azurerm_subnet.ctrl_network_subnet.id
    private_ip_address_allocation = "dynamic"
  }

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Create Southbound/WAN network interface for Controller
resource "azurerm_network_interface" "controller_nic_3" {
  name                 = "Controller_NIC3"
  location             = var.location
  resource_group_name  = azurerm_resource_group.versa_rg.name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "Controller_NIC3_Configuration"
    subnet_id                     = azurerm_subnet.wan_network_subnet.id
    private_ip_address_allocation = "dynamic"
    public_ip_address_id          = azurerm_public_ip.ip_ctrl_wan.id
  }

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Create Management network interface for Analytics
resource "azurerm_network_interface" "van_nic_1" {
  name                 = "VAN_NIC1"
  location             = var.location
  resource_group_name  = azurerm_resource_group.versa_rg.name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "VAN_NIC1_Configuration"
    subnet_id                     = azurerm_subnet.mgmt_subnet.id
    private_ip_address_allocation = "dynamic"
    public_ip_address_id          = azurerm_public_ip.ip_van.id
  }

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Create Southbound network interface for Analytics
resource "azurerm_network_interface" "van_nic_2" {
  name                 = "VAN_NIC2"
  location             = var.location
  resource_group_name  = azurerm_resource_group.versa_rg.name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "VAN_NIC2_Configuration"
    subnet_id                     = azurerm_subnet.ctrl_network_subnet.id
    private_ip_address_allocation = "dynamic"
  }

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Associate security group to Director Management Network Interface
resource "azurerm_network_interface_security_group_association" "dir_mgmt_nic_nsg" {
  network_interface_id      = azurerm_network_interface.director_nic_1.id
  network_security_group_id = azurerm_network_security_group.versa_nsg_dir.id
}

# Associate security group to Director Southbound Network Interface
resource "azurerm_network_interface_security_group_association" "dir_sb_nic_nsg" {
  network_interface_id      = azurerm_network_interface.director_nic_2.id
  network_security_group_id = azurerm_network_security_group.versa_nsg_dir.id
}

# Associate security group to Controller Management Network Interface
resource "azurerm_network_interface_security_group_association" "ctrl_mgmt_nic_nsg" {
  network_interface_id      = azurerm_network_interface.controller_nic_1.id
  network_security_group_id = azurerm_network_security_group.versa_nsg_vnf.id
}

# Associate security group to Controller Control Network Interface
resource "azurerm_network_interface_security_group_association" "ctrl_nb_nic_nsg" {
  network_interface_id      = azurerm_network_interface.controller_nic_2.id
  network_security_group_id = azurerm_network_security_group.versa_nsg_vnf.id
}

# Associate security group to Controller WAN Network Interface
resource "azurerm_network_interface_security_group_association" "ctrl_wan_nic_nsg" {
  network_interface_id      = azurerm_network_interface.controller_nic_3.id
  network_security_group_id = azurerm_network_security_group.versa_nsg_vnf.id
}

# Associate security group to Analytics Management Network Interface
resource "azurerm_network_interface_security_group_association" "van_mgmt_nic_nsg" {
  network_interface_id      = azurerm_network_interface.van_nic_1.id
  network_security_group_id = azurerm_network_security_group.versa_nsg_van.id
}

# Associate security group to Analytics Southbound Network Interface
resource "azurerm_network_interface_security_group_association" "van_sb_nic_nsg" {
  network_interface_id      = azurerm_network_interface.van_nic_2.id
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
  name                     = "dirdiag${random_id.randomId.hex}"
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
  name                     = "ctrldiag${random_id.randomId.hex}"
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
  name                     = "vandiag${random_id.randomId.hex}"
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
  name                         = "Versa_Director"
  location                     = var.location
  resource_group_name          = azurerm_resource_group.versa_rg.name
  depends_on                   = [azurerm_network_interface_security_group_association.dir_mgmt_nic_nsg, azurerm_network_interface_security_group_association.dir_sb_nic_nsg]
  network_interface_ids        = [azurerm_network_interface.director_nic_1.id, azurerm_network_interface.director_nic_2.id]
  primary_network_interface_id = azurerm_network_interface.director_nic_1.id
  vm_size                      = var.director_vm_size

  storage_os_disk {
    name              = "Director_OSDisk"
    caching           = "ReadWrite"
    create_option     = "FromImage"
    managed_disk_type = "Standard_LRS"
  }

  storage_image_reference {
    id = var.image_director
  }

  os_profile {
    computer_name  = var.hostname_director
    admin_username = "versa_devops"
    custom_data    = data.template_file.user_data_dir.rendered
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
    storage_uri = azurerm_storage_account.storageaccountDir.primary_blob_endpoint
  }

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Create Versa Controller Virtual Machine
resource "azurerm_virtual_machine" "controllerVM" {
  name                         = "Versa_Controller"
  location                     = var.location
  resource_group_name          = azurerm_resource_group.versa_rg.name
  depends_on                   = [azurerm_network_interface_security_group_association.ctrl_mgmt_nic_nsg, azurerm_network_interface_security_group_association.ctrl_nb_nic_nsg, azurerm_network_interface_security_group_association.ctrl_wan_nic_nsg]
  network_interface_ids        = [azurerm_network_interface.controller_nic_1.id, azurerm_network_interface.controller_nic_2.id, azurerm_network_interface.controller_nic_3.id]
  primary_network_interface_id = azurerm_network_interface.controller_nic_1.id
  vm_size                      = var.controller_vm_size

  storage_os_disk {
    name              = "Controller_OSDisk"
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
    storage_uri = azurerm_storage_account.storageaccountCtrl.primary_blob_endpoint
  }

  tags = {
    environment = "VersaHeadEnd"
  }
}

# Create Versa Analytics Virtual Machine
resource "azurerm_virtual_machine" "vanVM" {
  name                         = "Versa_Analytics"
  location                     = var.location
  resource_group_name          = azurerm_resource_group.versa_rg.name
  depends_on                   = [azurerm_network_interface_security_group_association.van_mgmt_nic_nsg, azurerm_network_interface_security_group_association.van_sb_nic_nsg]
  network_interface_ids        = [azurerm_network_interface.van_nic_1.id, azurerm_network_interface.van_nic_2.id]
  primary_network_interface_id = azurerm_network_interface.van_nic_1.id
  vm_size                      = var.analytics_vm_size

  storage_os_disk {
    name              = "VAN_OSDisk"
    caching           = "ReadWrite"
    create_option     = "FromImage"
    managed_disk_type = "Standard_LRS"
  }

  storage_image_reference {
    id = var.image_analytics
  }

  os_profile {
    computer_name  = var.hostname_van
    admin_username = "versa_devops"
    custom_data    = data.template_file.user_data_van.rendered
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
    storage_uri = azurerm_storage_account.storageaccountVAN.primary_blob_endpoint
  }

  tags = {
    environment = "VersaHeadEnd"
  }
}

data "azurerm_public_ip" "dir_pub_ip" {
  name                = azurerm_public_ip.ip_dir.name
  resource_group_name = azurerm_resource_group.versa_rg.name
  depends_on          = [azurerm_virtual_machine.directorVM]
}

data "azurerm_public_ip" "ctrl_pub_ip" {
  name                = azurerm_public_ip.ip_ctrl.name
  resource_group_name = azurerm_resource_group.versa_rg.name
#  depends_on          = [azurerm_virtual_machine.controllerVM]
}

data "azurerm_public_ip" "van_pub_ip" {
  name                = azurerm_public_ip.ip_van.name
  resource_group_name = azurerm_resource_group.versa_rg.name
  depends_on          = [azurerm_virtual_machine.vanVM]
}

data "azurerm_public_ip" "ctrl_wan_pub_ip" {
  name                = azurerm_public_ip.ip_ctrl_wan.name
  resource_group_name = azurerm_resource_group.versa_rg.name
  depends_on          = [azurerm_virtual_machine.controllerVM]
}