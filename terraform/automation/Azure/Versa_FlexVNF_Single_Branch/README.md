This Terraform Template is intended to Automate the bringing up Single Instance of Versa FlexVNF Branch on Azure.

# Pre-requisites for using this template:

- **Terraform Install:** To Download & Install Terraform, refer Link "www.terraform.io/downloads.html"
- **Terraform Setup for Azure:** To Setup Terraform for Azure Account, refer link "https://docs.microsoft.com/en-us/azure/virtual-machines/linux/terraform-install-configure".
  Here you will get Subscription ID, Client ID, Client Secret and Tenant ID required for terraform login.
- **Versa FlexVNF Image:** Versa provided FlexNVF image is available.
- Virtual Network (VNet) is already created and minimum 3 subnets created in that VNet required for Management, WAN & LAN Port.
  
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
- flexvnf.sh file.

**main.tf file:**

main.tf template file will perform below actions/activities when executed:

- Provision one resource group with name "Versa_FlexVNF_RG". Resource Group name can be changed if required after updating terraform.tfvars file.
- Provision Public IP for Management Port and also one Static Public IP for WAN Port.
- Provision Network Security Group and add all the firewall rules required for FlexVNF.
- Provision Network Interfaces for FlexVNF.
- Install Versa FlexVNF instance and run cloud-init script for:
  - Updating /etc/network/interface file.
  - Inject the ssh key for admin user

**var.tf file:**

var.tf file will have definition for all the variables defined/used as part of this template. User does not need to update anything in this file.

**terraform.tfvars file:**

terraform.tfvars file is being used to get the variables values from user. User need to update the required fields according to their environment. This file will have below information:

- subscription_id : Provide the Subscription ID information here. This information will be obtained as part of terraform login done above under Pre-requisites step.
- client_id : Provide the Client ID information here. This information will be obtained as part of terraform login done above under Pre-requisites step.
- client_secret : Provide the Client Secret information here. This information will be obtained as part of terraform login done above under Pre-requisites step.
- tenant_id : Provide the Tenant ID information here. This information will be obtained as part of terraform login done above under Pre-requisites step.
- location : Provide the location where user wants to deploy Versa FlexVNF. E.g. westus, centralus etc.
- resource_group : Provide the resource group name where all the resources belonging to Versa FlexVNF Branch will be created. Default resource group name "Versa_FlexVNF_RG" will be used.
- ssh_key : Provide the ssh public key information here. This key will be injected into instances which can be used to login into instances later on. Azure does not provide the option to generate the keys. User has to generate the ssh key using "sshkey-gen" or "putty key generator" tool to generate the ssh keys. Here Public key information is required.
- mgmt_subnet : Provide the subnet information being used for Management Port.
- wan_subnet : Provide the subnet information being used for WAN Port.
- lan_subnet : Provide the subnet information being used for LAN Port.
- image_flexvnf : Provide the Versa FlexVNF Image ID.
- vm_name : Provide the name of VM being used. The VM will be crated with this name in Azure. By default, "Versa_FlexVNF" VM name is being used.
- flexvnf_vm_size : Provide the instance type/size which will be used to provision the Versa FlexVNF Instance. By default, Standard_DS3 will be used.

**output.tf file:**

output.tf file will have information to provide the output for the parameters (e.g. Management IP, Public IP, CLI command, UI Login for Versa FlexVNF instances) after terraform apply operation is succeeded. User does not need to update anything in this file.

**flexvnf.sh file:**

flexvnf.sh file will have bash script which will be executed as part of cloud-init script on Versa FlexVNF Instance. Don't update anything in this file.

**Note:** It will bring up the Branch on Azure with required number of interfaces. User still need to do ZTP after branch is on boarded using this template.
