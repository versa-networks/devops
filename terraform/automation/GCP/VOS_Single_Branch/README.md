This Terraform Template is intended to Automate the bringing up Single Instance of VOS on Google Cloud Platform (GCE).

# Pre-requisites for using this template:

- **Terraform Install:** To Download & Install Terraform, refer Link "www.terraform.io/downloads.html"
- **Terraform Setup for GCP:** To Setup Terraform for Google Cloud Account, first create a service account in google cloud account, refer link "https://cloud.google.com/iam/docs/creating-managing-service-accounts#creating".
  Then create service account keys in json file format for the service account created above, refer link "https://cloud.google.com/iam/docs/creating-managing-service-account-keys#creating_service_account_keys".
  Here you will get one json file for the service account which will be used to authenticate towards google cloud platform.
- **VOS Image:** Versa provided VOS Image available in your google cloud account

# Usage:

- Download all the files in PC where Terraform is installed. It is recommended that place all the files in new/separate folder as terraform will store the state file for this environment once it is applied.
- Go to the folder where all the required files are placed using command prompt.
- Use command `terraform init` to initialize. it will download necessary terraform plugins required to run this template.
- Then use command `terraform plan` to plan the deployment. It will show the plan regarding all the resources being provisioned as part of this template.
- At last use command `terraform apply` to apply this plan in action for deployment. It will start deploying all the resource on Google Cloud.


It will require below files to run it.

- main.tf file.
- var.tf file.
- terraform.tfvars file.
- output.tf file.
- vos.sh file.
- credentials.json file -- Place this file in same folder where above files are downloaded required for authentication.

**main.tf file:**

main.tf template file will perform below actions/activities when executed:

- Provision Public IP for Management Port and also one Static Public IP for WAN Port.
- Provision the firewall rules required for VOS instance.
- Install VOS instance and run cloud-init script for:
  - Updating /etc/network/interface file.
  - Inject the ssh key for admin user.
  - Add exception for Director IP to allow password based authentication during ZTP.

**var.tf file:**

var.tf file will have definition for all the variables defined/used as part of this template. User does not need to update anything in this file.

**terraform.tfvars file:**

terraform.tfvars file is being used to get the variables values from user. User need to update the required fields according to their environment. This file will have below information:

- credentials_file : Provide the credential file path which was obtained during initial setup process for service account.
- project_id : Provide the google cloud project id where head end has to be deployed.
- region : Provide the region where user wants to deploy Versa HE setup. E.g. us-west1, us-central1 etc.
- zone : Provide the zone from the selected region above where all the resources belonging to Versa HE Setup will be created. E.g. us-west1-a, us-central1-a etc.
- ssh_key : Provide the ssh public key information here. This key will be injected into instances which can be used to login into instances later on. User can generate the ssh key using "sshkey-gen" or "putty key generator" tool to generate the ssh keys. Here Public key information is required.
- vos_image : Provide the VOS Image name.
- labels : Provide the labels/tags to be added to the instances.
- machine_type_vos : Provide the machine type/size which will be used to provision the VOS Instance. By default, n1-standard-4 will be used.
- director_mgmt_ip : Provide the Director Management IP which will be added as exception to allow password based login into VOS instance during ZTP.
- mgmt_vpc_name : Provide the name of management VPC where VOS instance will be deployed.
- wan_vpc_name : Provide the name of WAN VPC where VOS instance will be deployed.
- mgmt_subnet_name : Provide the name of management Subent which belongs to management VPC where VOS instance will be deployed.
- wan_subnet_name : Provide the name of WAN Subent which belongs to WAN VPC where VOS instance will be deployed.
- lan_subnet_name : Provide the name of LAN Subent which belongs to LAN VPC where VOS instance will be deployed.

**output.tf file:**

output.tf file will have information to provide the output for the parameters (e.g. instance id, Public IP for the VOS instance) after terraform apply operation is succeeded. User does not need to update anything in this file.

**vos.sh file:**

vos.sh file will have bash script which will be executed as part of cloud-init script on VOS Instance. Don't update anything in this file.
