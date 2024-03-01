This Terraform Template is intended to Automate the bringing up Versa Head End setup on Azure in redundant mode. It will bring up 2 instances of Versa Director & Versa Controller in different regions and 2 analytics node for cluster config in primary region.

# Pre-requisites for using this template:

- **Terraform Install:** To Download & Install Terraform, refer Link "www.terraform.io/downloads.html"
- **Terraform Setup for Azure:** To Setup Terraform for Azure Account, refer link "https://docs.microsoft.com/en-us/azure/virtual-machines/linux/terraform-install-configure".
  Here you will get Subscription ID, Client ID, Client Secret and Tenant ID required for terraform login.
- **Versa Head End Images:** Image available and added in Azure in .vhd format for:
  - Versa Director
  - Versa Controller
  - Versa Analytics
  
- **Role:** At least &quot;contributor&quot; level role is required to the Terraform user used to run this template.

# Usage:

- Download all the files in PC where Terraform is installed. It is recommended that place all the files in new/separate folder as terraform will store the state file for this environment once it is applied.
- Go to the folder where all the required files are placed using command prompt.
- Use command `terraform init` to initialize. it will download necessary terraform plugins required to run this template.
- Then use command `terraform plan` to plan the deployment. It will show the plan regarding all the resources being provisioned as part of this template.
- At last use command `terraform apply` to apply this plan in action for deployment. It will start deploying all the resource on Azure.


It will require below files to run it.

- main.tf file.
- var.tf file.
- terraform.tfvars file.
- output.tf file.
- director-1.sh file.
- director-2.sh file.
- controller.sh file.
- van.sh file.

**main.tf file:**

main.tf template file will perform below actions/activities when executed:

- Provision one resource group with name "Versa_HE_HA-1" and "Versa_HE_HA-2" in respective region. Resource Group name can be changed if required after updating terraform.tfvars file.
- Provision one Virtual Network "10.54.0.0/16" in region one and another Virtual Network "10.55.0.0/16" in another region. This can be changed after updating terraform.tfvars file.
- Provision 6 Subnets with /24 network in each region. This can be changed after updating terraform.tfvars file.
  - First subnet for management of all the versa HE instances. Here Public IP will be assigned to each port.
  - Second subnet for Director SB, Router NB and Analytics SB ports.
  - Third subnet will be for Router to Router connectivity to run BGP between routers.
  - Fourth subnet will be for Router SB and Controller NB ports. This is Control network.
  - Fifth subnet will be for Controller SB and Branch NB ports. This is WAN network.
  - Sixth subnet will be for Branch SB ports. This is LAN network.
- Provision the VNet Peering between these networks across region.
- Provision Public IP for all the instances for Management Port and also one Static Public IP for Controller WAN Port.
- Provision User Defined Routes.
- Provision Network Security Group and add all the firewall rules required for HE setup.
- Provision Network Interfaces for all the instances.
- Install Versa Director instances in each region and run cloud-init script for:
  - Updating the /etc/network/interface file.
  - Updating the /etc/hosts and hostname file.
  - Inject the ssh key for Administrator User
  - Generate the new certificates.
  - Execute vnms-startup script in non-interactive mode.
- Install Versa Router instances in each region and run cloud-init script for:
  - Updating /etc/network/interface file.
  - Inject the ssh key for admin user
- Install Versa Controller instances in each region and run cloud-init script for:
  - Updating /etc/network/interface file.
  - Inject the ssh key for admin user
- Install Versa Analytics instances in primary region and run the cloud-init script for:
  - Updating the /etc/network/interface file.
  - Updating the /etc/hosts file.
  - Inject the ssh key for versa user
  - Copy certificates from Versa Director and install this certificate into Analytics.

**var.tf file:**

var.tf file will have definition for all the variables defined/used as part of this template. User does not need to update anything in this file.

**terraform.tfvars file:**

terraform.tfvars file is being used to get the variables values from user. User need to update the required fields according to their environment. This file will have below information:

- subscription_id : Provide the Subscription ID information here. This information will be obtained as part of terraform login done above under Pre-requisites step.
- client_id : Provide the Client ID information here. This information will be obtained as part of terraform login done above under Pre-requisites step.
- client_secret : Provide the Client Secret information here. This information will be obtained as part of terraform login done above under Pre-requisites step.
- tenant_id : Provide the Tenant ID information here. This information will be obtained as part of terraform login done above under Pre-requisites step.
- location : Provide the location where user wants to deploy Versa HE setup. User need to update both the locations where redundant setup is required. E.g. westus and centralus.
- resource_group : Provide the resource group name where all the resources belonging to Versa HE Setup will be created. Default resource group name "Versa_HE_HA" will be used.
- ssh_key : Provide the ssh public key information here. This key will be injected into instances which can be used to login into instances later on. Azure does not provide the option to generate the keys. User has to generate the ssh key using "sshkey-gen" or "putty key generator" tool to generate the ssh keys. Here Public key information is required.
- vpc_address_space : Provide the address space information to create the network in azure in both regions. By default, 10.54.0.0/16 and 10.55.0.0/16 network will be created in respective region.
- newbits_subnet : Provide the subnet information to be cut from the network. By default, /24 subnet will be cut from the network provisioned above. Here, newbits_subnet will have value "8" for this parameter. Since network is in /16 and 8 value here will cut the subnet in /24 (16+8). E.g., If user need to create a subnet of /29 then this newbits_subnet value will be "13" as (16+13=29).
- image_director : Provide the Versa Director Image ID for both the regions.
- image_controller : Provide the Versa Controller Image ID for both the regions.
- image_analytics : Provide the Versa Analytics Image ID for primary region.
- hostname_director : Provide the hostname for both Versa Director instances to be used. By default, "versa-director-wus" and "versa-director-cus" hostname is being used for each instance.
- hostname_van : Provide the hostname for Versa Analytics instances to be used. By default, "versa-analytics-1" and "versa-analytics-2" hostname is being used for each instance. Number of analytics servers will depend upon the number of hostnames mentioned in variable named “hostname_van” in terraform.tfvars file. E.g. if you provide 2 hostnames, then 2 analytics instances will be created in primary region.
- director_vm_size : Provide the instance type/size which will be used to provision the Versa Director Instance. By default, Standard_DS3 will be used.
- controller_vm_size : Provide the instance type/size which will be used to provision the Versa Controller Instance. By default, Standard_DS3 will be used.
- router_vm_size : Provide the instance type/size which will be used to provision the Versa Router Instance. By default, Standard_DS3 will be used.
- analytics_vm_size : Provide the instance type/size which will be used to provision the Versa Analytics Instance. By default, Standard_DS3 will be used.
- van_disk_size : Provide the Disk size to be provisioned for Analytics VMs. Default disk size is 80 GB.
- controller_disk_size : Provide the Disk size to be provisioned for Controller VMs. Default disk size is 80 GB.

**output.tf file:**

output.tf file will have information to provide the output for the parameters (e.g. Management IP, Public IP, CLI command, UI Login for all the instances) after terraform apply operation is succeeded. User does not need to update anything in this file.

**director-1.sh file:**

director-1.sh file will have bash script which will be executed as part of cloud-init script on Versa Director-1 Instance. Don't update anything in this file.

**director-2.sh file:**

director-2.sh file will have bash script which will be executed as part of cloud-init script on Versa Director-2 Instance. Don't update anything in this file.

**controller.sh file:**

controller.sh file will have bash script which will be executed as part of cloud-init script on Versa Controller Instance. Don't update anything in this file.

**van.sh file:**

van-1.sh file will have bash script which will be executed as part of cloud-init script on Versa Analytics-1 Instance. Don't update anything in this file.

As part of this terraform template below topology will be brought up:

 ![Topology](http://gitlab.versa-networks.com/software/devops/blob/master/terraform/azure/Images/Topology_Versa_HE_HA_Azure_VAN_PrimaryRegion.jpg)
