#----------------------------------------------------------------------
# Variable's value defined here
#----------------------------------------------------------------------

subscription_id    = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
client_id          = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
client_secret      = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
tenant_id          = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
location           = "eastus2"
resource_group     = "Versa_HE_HA_Setup"
ssh_key            = "ssh-rsa TNiWaCKYS0zacbiN0raJHJoOTaQ6iApXmFdTXmdxjUiipTyrzpluMFgDxI0KeHZNNaxHBXuB a@versa"
vpc_address_space  = "10.217.0.0/16"
newbits_subnet     = "8"
image_director     = "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/VersaCentralUS/providers/Microsoft.Compute/images/21.2.1-Trusty-GA-Director"
image_controller   = "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/VersaCentralUS/providers/Microsoft.Compute/images/21.2.1-Trusty-GA-VOS"
image_analytics    = "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/VersaCentralUS/providers/Microsoft.Compute/images/21.2.1-Trusty-GA-VAN"
hostname_director  = ["versa-director-1", "versa-director-2"]
hostname_van       = ["versa-analytics-1", "versa-analytics-2", "versa-analytics-3", "versa-analytics-4"]
director_vm_size   = "Standard_B2ms"
controller_vm_size = "Standard_B4ms"
analytics_vm_size  = "Standard_B2ms"
van_disk_size      = 80
