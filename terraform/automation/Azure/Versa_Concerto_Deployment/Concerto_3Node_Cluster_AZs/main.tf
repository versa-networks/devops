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
    environment = "VersaConcerto"
  }
}

locals {
  template_var_concerto = {
    sshkey              = var.ssh_key
    hostname_concerto_1 = var.hostname_concerto[0]
    concerto_1_mgmt_ip  = azurerm_network_interface.concerto_nic_1[0].private_ip_address
    hostname_concerto_2 = var.hostname_concerto[1]
    concerto_2_mgmt_ip  = azurerm_network_interface.concerto_nic_1[1].private_ip_address
    hostname_concerto_3 = var.hostname_concerto[2]
    concerto_3_mgmt_ip  = azurerm_network_interface.concerto_nic_1[2].private_ip_address
    mgmt_gw             = cidrhost("${azurerm_subnet.mgmt_subnet.address_prefixes[0]}", 1)
  }
  cloud_init_file = ["concerto-1.sh", "concerto-2.sh", "concerto-3.sh"]
}

# Add template to use custom data for Concerto:
data "template_file" "user_data_concerto" {
  count    = var.cluster_nodes
  template = file(local.cloud_init_file[count.index])

  vars = local.template_var_concerto
}

# Create virtual network
resource "azurerm_virtual_network" "versaNetwork" {
  name                = "Versa_VPC"
  address_space       = [var.vpc_address_space]
  location            = var.location
  resource_group_name = azurerm_resource_group.versa_rg.name

  tags = {
    environment = "VersaConcerto"
  }
}

# Create Management Subnet
resource "azurerm_subnet" "mgmt_subnet" {
  name                 = "Concerto-Management-Subent"
  resource_group_name  = azurerm_resource_group.versa_rg.name
  virtual_network_name = azurerm_virtual_network.versaNetwork.name
  address_prefixes     = [cidrsubnet(azurerm_virtual_network.versaNetwork.address_space[0], var.newbits_subnet, 1, )]
}

# Create Southbound Subnet
resource "azurerm_subnet" "sb_subnet" {
  name                 = "Concerto-Southbound-Subent"
  resource_group_name  = azurerm_resource_group.versa_rg.name
  virtual_network_name = azurerm_virtual_network.versaNetwork.name
  address_prefixes     = [cidrsubnet(azurerm_virtual_network.versaNetwork.address_space[0], var.newbits_subnet, 2, )]
}

# Create Public IP for Concerto
resource "azurerm_public_ip" "ip_concerto" {
  count               = var.cluster_nodes
  name                = "PublicIP_Concerto_${1 + count.index}"
  location            = var.location
  resource_group_name = azurerm_resource_group.versa_rg.name
  sku                 = "Standard"
  allocation_method   = "Static"
  availability_zone   = 1 + count.index

  tags = {
    environment = "VersaConcerto"
  }
}

# Create Network Security Groups and rules for Concerto
resource "azurerm_network_security_group" "versa_nsg_concerto" {
  name                = "Versa-Concerto-NSG"
  location            = var.location
  resource_group_name = azurerm_resource_group.versa_rg.name
  security_rule {
    name                       = "Versa_Security_Rule_TCP"
    priority                   = 151
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_ranges    = ["22", "80", "443", "2181", "9092-9094", "2377", "24007", "7946", "111", "49152"]
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
  security_rule {
    name                       = "Versa_Security_Rule_ICMP"
    priority                   = 161
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Icmp"
    source_port_range          = "*"
    destination_port_range     = "*"
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
    environment = "VersaConcerto"
  }
}

# Create Management network interface for Concerto
resource "azurerm_network_interface" "concerto_nic_1" {
  count                = var.cluster_nodes
  name                 = "Concerto_${1 + count.index}_NIC1"
  location             = var.location
  resource_group_name  = azurerm_resource_group.versa_rg.name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "Concerto_${1 + count.index}_NIC1_Configuration"
    subnet_id                     = azurerm_subnet.mgmt_subnet.id
    private_ip_address_allocation = "dynamic"
    public_ip_address_id          = azurerm_public_ip.ip_concerto[count.index].id
  }

  tags = {
    environment = "VersaConcerto"
  }
}

# Create Southbound network interface for Concerto
resource "azurerm_network_interface" "concerto_nic_2" {
  count                = var.cluster_nodes
  name                 = "Concerto_${1 + count.index}_NIC2"
  location             = var.location
  resource_group_name  = azurerm_resource_group.versa_rg.name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "Concerto_${1 + count.index}_NIC2_Configuration"
    subnet_id                     = azurerm_subnet.sb_subnet.id
    private_ip_address_allocation = "dynamic"
  }

  tags = {
    environment = "VersaConcerto"
  }
}

# Associate security group to Concerto Management Network Interface
resource "azurerm_network_interface_security_group_association" "concerto_mgmt_nic_nsg" {
  count                     = var.cluster_nodes
  network_interface_id      = azurerm_network_interface.concerto_nic_1[count.index].id
  network_security_group_id = azurerm_network_security_group.versa_nsg_concerto.id
}

# Associate security group to Concerto Southbound Network Interface
resource "azurerm_network_interface_security_group_association" "concerto_sb_nic_nsg" {
  count                     = var.cluster_nodes
  network_interface_id      = azurerm_network_interface.concerto_nic_2[count.index].id
  network_security_group_id = azurerm_network_security_group.versa_nsg_concerto.id
}

# Generate random text for a unique storage account name
resource "random_id" "randomId" {
  keepers = {
    resource_group = azurerm_resource_group.versa_rg.name
  }

  byte_length = 4
}

# Create storage account for boot diagnostics of Concerto VM
resource "azurerm_storage_account" "storageaccountDir" {
  count                    = var.cluster_nodes
  name                     = "concerto${1 + count.index}diag${random_id.randomId.hex}"
  resource_group_name      = azurerm_resource_group.versa_rg.name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = {
    environment = "VersaConcerto"
  }
}

# Create Versa Concerto Virtual Machine
resource "azurerm_virtual_machine" "concertoVM" {
  count                        = var.cluster_nodes
  name                         = "Versa_Concerto_${1 + count.index}"
  location                     = var.location
  zones                        = [1 + count.index]
  resource_group_name          = azurerm_resource_group.versa_rg.name
  depends_on                   = [azurerm_network_interface_security_group_association.concerto_mgmt_nic_nsg, azurerm_network_interface_security_group_association.concerto_sb_nic_nsg]
  network_interface_ids        = [azurerm_network_interface.concerto_nic_1[count.index].id, azurerm_network_interface.concerto_nic_2[count.index].id]
  primary_network_interface_id = azurerm_network_interface.concerto_nic_1[count.index].id
  vm_size                      = var.concerto_vm_size

  storage_os_disk {
    name              = "Concerto_${1 + count.index}_OSDisk"
    caching           = "ReadWrite"
    create_option     = "FromImage"
    managed_disk_type = "Standard_LRS"
  }

  storage_image_reference {
    id = var.image_concerto
  }

  os_profile {
    computer_name  = var.hostname_concerto[count.index]
    admin_username = "versa_devops"
    custom_data    = data.template_file.user_data_concerto[count.index].rendered
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
    environment = "VersaConcerto"
  }
}

data "azurerm_public_ip" "concerto_pub_ip" {
  count               = var.cluster_nodes
  name                = azurerm_public_ip.ip_concerto[count.index].name
  resource_group_name = azurerm_resource_group.versa_rg.name
  depends_on          = [azurerm_virtual_machine.concertoVM]
}
