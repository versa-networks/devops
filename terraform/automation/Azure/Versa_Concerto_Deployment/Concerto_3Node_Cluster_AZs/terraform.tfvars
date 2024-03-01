#----------------------------------------------------------------------
# Variable's value defined here
#----------------------------------------------------------------------

subscription_id   = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
client_id         = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
client_secret     = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
tenant_id         = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
location          = "centralus"
resource_group    = "Versa_Concerto"
ssh_key           = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDvgZTNiWaCKYS0zacbiN0raJHJoOTaQ6iApXmFdTXCr1NGFm9J a@versa"
vpc_address_space = "10.220.0.0/16"
newbits_subnet    = "8"
cluster_nodes     = 3
hostname_concerto = ["versa-concerto-1", "versa-concerto-2", "versa-concerto-3"]
image_concerto    = "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/VersaCentralUS/providers/Microsoft.Compute/images/Concerto-10.2.1-GA"
concerto_vm_size  = "Standard_F4s_v2"
