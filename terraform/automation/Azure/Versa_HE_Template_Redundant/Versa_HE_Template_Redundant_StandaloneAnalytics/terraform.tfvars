#----------------------------------------------------------------------
# Variable's value defined here
#----------------------------------------------------------------------

subscription_id		= "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
client_id		= "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
client_secret		= "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
tenant_id		= "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
location		= ["westus", "centralus"]
resource_group		= "Versa_HE_HA"
ssh_key			= "ssh-rsa sks;lwlfdewf3ur439r93u4oweodfewkdoeiri309849r3uofeojfojfoewkfkdpow3i043898r43ri43pdi03id043kdpokp43dlsmclkdsjpow09w a@versa"
vpc_address_space	= ["10.54.0.0/16", "10.55.0.0/16"]
newbits_subnet		= "8" 
image_director		= ["/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/versa/providers/Microsoft.Compute/images/16.1R2-S11-GA-Director", "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/VersaCentralUS/providers/Microsoft.Compute/images/16.1R2-S11-GA-Director"]
image_controller	= ["/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/versa/providers/Microsoft.Compute/images/16.1R2-S11-GA-FlexVNF", "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/VersaCentralUS/providers/Microsoft.Compute/images/16.1R2-S11-GA-FlexVNF"]
image_analytics		= ["/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/versa/providers/Microsoft.Compute/images/16.1R2-S11-GA-Analytics", "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/VersaCentralUS/providers/Microsoft.Compute/images/16.1R2-S11-GA-Analytics"]
hostname_director	= ["versa-director-wus", "versa-director-cus"]
hostname_van		= ["versa-analytics-wus", "versa-analytics-cus"]
director_vm_size	= "Standard_DS3"
controller_vm_size	= "Standard_DS3"
router_vm_size		= "Standard_DS3"
analytics_vm_size	= "Standard_DS3"
