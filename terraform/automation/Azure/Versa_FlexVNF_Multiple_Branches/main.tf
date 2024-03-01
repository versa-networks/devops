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
    environment = "VersaFlexVNF"
  }
}

# Add template to use custom data for FlexVNF:
data "template_file" "user_data_flexvnf" {
  template = file("flexvnf.sh")

  vars = {
    sshkey = var.ssh_key
  }
}

# Create Management Public IP for FlexVNF
resource "azurerm_public_ip" "ip_flexvnf_mgmt" {
  count               = var.count_vms
  name                = "PublicIP_FlexVNF-${1 + count.index}"
  location            = var.location
  resource_group_name = azurerm_resource_group.versa_rg.name
  allocation_method   = "Dynamic"

  tags = {
    environment = "VersaFlexVNF"
  }
}

# Create Public IP for FlexVNF WAN Port
resource "azurerm_public_ip" "ip_flexvnf_wan" {
  count               = var.count_vms
  name                = "PublicIP_WanPort_FlexVNF-${1 + count.index}"
  location            = var.location
  resource_group_name = azurerm_resource_group.versa_rg.name
  allocation_method   = "Static"

  tags = {
    environment = "VersaFlexVNF"
  }
}

# Create Network Security Group and rule
resource "azurerm_network_security_group" "versa_nsg" {
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
    destination_port_ranges    = ["22", "2022", "3000-3003", "8443", "1024-1120", "9878"]
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

# Create Management network interface for FlexVNF
resource "azurerm_network_interface" "flexvnf_nic_1" {
  count               = var.count_vms
  name                = "FlexVNF-${1 + count.index}_NIC1"
  location            = var.location
  resource_group_name = azurerm_resource_group.versa_rg.name

  ip_configuration {
    name                          = "FlexVNF-${1 + count.index}_NIC1_Configuration"
    subnet_id                     = var.mgmt_subnet
    private_ip_address_allocation = "dynamic"
    public_ip_address_id          = azurerm_public_ip.ip_flexvnf_mgmt[count.index].id
  }

  tags = {
    environment = "VersaFlexVNF"
  }
}

# Create WAN network interface for FlexVNF
resource "azurerm_network_interface" "flexvnf_nic_2" {
  count                = var.count_vms
  name                 = "FlexVNF-${1 + count.index}_NIC2"
  location             = var.location
  resource_group_name  = azurerm_resource_group.versa_rg.name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "FlexVNF-${1 + count.index}_NIC2_Configuration"
    subnet_id                     = var.wan_subnet
    private_ip_address_allocation = "dynamic"
    public_ip_address_id          = azurerm_public_ip.ip_flexvnf_wan[count.index].id
  }

  tags = {
    environment = "VersaFlexVNF"
  }
}

# Create LAN network interface for FlexVNF
resource "azurerm_network_interface" "flexvnf_nic_3" {
  count                = var.count_vms
  name                 = "FlexVNF-${1 + count.index}_NIC3"
  location             = var.location
  resource_group_name  = azurerm_resource_group.versa_rg.name
  enable_ip_forwarding = "true"

  ip_configuration {
    name                          = "FlexVNF-${1 + count.index}_NIC3_Configuration"
    subnet_id                     = var.lan_subnet
    private_ip_address_allocation = "dynamic"
  }

  tags = {
    environment = "VersaFlexVNF"
  }
}

# Associate security group to Management Network Interface
resource "azurerm_network_interface_security_group_association" "mgmt_nic_nsg" {
  count                     = var.count_vms
  network_interface_id      = azurerm_network_interface.flexvnf_nic_1[count.index].id
  network_security_group_id = azurerm_network_security_group.versa_nsg.id
}

# Associate security group to WAN Network Interface
resource "azurerm_network_interface_security_group_association" "wan_nic_nsg" {
  count                     = var.count_vms
  network_interface_id      = azurerm_network_interface.flexvnf_nic_2[count.index].id
  network_security_group_id = azurerm_network_security_group.versa_nsg.id
}

# Associate security group to LAN Network Interface
resource "azurerm_network_interface_security_group_association" "lan_nic_nsg" {
  count                     = var.count_vms
  network_interface_id      = azurerm_network_interface.flexvnf_nic_3[count.index].id
  network_security_group_id = azurerm_network_security_group.versa_nsg.id
}

# Generate random text for a unique storage account name
resource "random_id" "randomId" {
    keepers = {
        resource_group = azurerm_resource_group.versa_rg.name
    }

    byte_length = 4
}

# Create storage account for boot diagnostics of FlexVNF VM
resource "azurerm_storage_account" "storageaccountFlexVNF" {
  count                    = var.count_vms
  name                     = "vnf${1 + count.index}diag${random_id.randomId.hex}"
  resource_group_name      = azurerm_resource_group.versa_rg.name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = {
    environment = "VersaFlexVNF"
  }
}

# Create Versa FlexVNF Virtual Machine
resource "azurerm_virtual_machine" "flexVNF" {
  count                        = var.count_vms
  name                         = "${var.vm_name}-${1 + count.index}"
  location                     = var.location
  resource_group_name          = azurerm_resource_group.versa_rg.name
  depends_on                   = [azurerm_network_interface_security_group_association.mgmt_nic_nsg, azurerm_network_interface_security_group_association.wan_nic_nsg, azurerm_network_interface_security_group_association.lan_nic_nsg]
  network_interface_ids        = [azurerm_network_interface.flexvnf_nic_1[count.index].id, azurerm_network_interface.flexvnf_nic_2[count.index].id, azurerm_network_interface.flexvnf_nic_3[count.index].id]
  primary_network_interface_id = azurerm_network_interface.flexvnf_nic_1[count.index].id
  vm_size                      = var.flexvnf_vm_size

  storage_os_disk {
    name              = "${var.vm_name}-${1 + count.index}_OSDisk"
    caching           = "ReadWrite"
    create_option     = "FromImage"
    managed_disk_type = "Standard_LRS"
  }

  storage_image_reference {
    id = var.image_flexvnf
  }

  os_profile {
    computer_name  = "versa-flexvnf"
    admin_username = "versa_devops"
    custom_data    = data.template_file.user_data_flexvnf.rendered
  }

  os_profile_linux_config {
    disable_password_authentication = true
    ssh_keys {
      path     = "/home/versa_devops/.ssh/authorized_keys"
      key_data = var.ssh_key
    }
  }

  boot_diagnostics {
    enabled = "true"
    storage_uri = azurerm_storage_account.storageaccountFlexVNF[count.index].primary_blob_endpoint
  }

  tags = {
    environment = "VersaFlexVNF"
  }
}

data "azurerm_public_ip" "flexvnf_pub_ip" {
  count               = var.count_vms
  name                = azurerm_public_ip.ip_flexvnf_mgmt[count.index].name
  resource_group_name = azurerm_resource_group.versa_rg.name
  depends_on          = [azurerm_virtual_machine.flexVNF]
}

data "azurerm_public_ip" "flexvnf_wan_pub_ip" {
  count               = var.count_vms
  name                = azurerm_public_ip.ip_flexvnf_wan[count.index].name
  resource_group_name = azurerm_resource_group.versa_rg.name
  depends_on          = [azurerm_virtual_machine.flexVNF]
}