#----------------------------------------------------------------------
# Variable's value defined here
#----------------------------------------------------------------------

subscription_id      = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
client_id            = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
client_secret        = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
tenant_id            = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
location             = ["westus", "centralus"]
resource_group       = "Versa_HE_HA"
ssh_key              = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDvgZTNiWaCKYS0zacbiN0raJHJoOTa a@versa"
vpc_address_space    = ["10.231.0.0/16", "10.232.0.0/16"]
newbits_subnet       = "8"
image_director       = ["/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/versa/providers/Microsoft.Compute/images/Director-WUS", "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/versa/providers/Microsoft.Compute/images/Director-CUS"]
image_controller     = ["/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/versa/providers/Microsoft.Compute/images/Controller-WUS", "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/versa/providers/Microsoft.Compute/images/Controller-CUS"]
image_analytics      = "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/versa/providers/Microsoft.Compute/images/Analytics-WUS"
hostname_director    = ["versa-director-wus", "versa-director-cus"]
hostname_van         = ["versa-analytics-1", "versa-analytics-2"]
director_vm_size     = "Standard_B4ms"
controller_vm_size   = "Standard_B4ms"
router_vm_size       = "Standard_B4ms"
analytics_vm_size    = "Standard_B4ms"
van_disk_size        = 80
controller_disk_size = 80