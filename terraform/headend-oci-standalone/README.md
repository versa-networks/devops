<<<<<<< HEAD
# Terraform Script for Simple Headend in OCI (Oracle Cloud)

This repository is intended to deploy a Simple Headend (1 Director, 1 Analytics cluster (Analytics, Search, Log Forwarder), 2 Controllers and 1 SVNF). in Oracle cloud infrastructure. It is expected that the customer preloads the Versa Images to their Oracle account and creates an API for its user to perform operations. 

Note: This script is currently tailored for ALS nodes. It needs further work for it to be more generic
=======
#Terraform Script for Simple Headend in OCI (Oracle Cloud)

This repository is intended to deploy a Versa Headend in a single Oracle Cloud Infrastructure Region with: 
- 1 Director
- 1 Analytics cluster (Analytics, Search, Log Forwarder). The user can manually define how many instances he wants with each personality. If the number variables are set to 0, no node of that personality is created.
- 1 Service VNF
- 1 Controller 
It is expected that the customer preloads the Versa Images to their Oracle account and creates an API Key for its user to perform operations. You can find more information about how to perform those tasks in the following link. 

This script also deploys the necesary subnets for the operations, as well as an Internet Gateway for them. It also creates a DRG to enable inter-region connectivity.
- Northbound Subnet
- Southbound Subnet
- Control Subnet
- WAN subnet
- Router subnet


Due to the complexity of managing multiple Oracle Regions with a single script, we recommend to deploy a single script for each region in case you want to deploy a diverse gateway. This script deploys a DRG for inter-region communication. The user would need to build the connectivity between regions manually.
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3

## main.tf
This is the main module for the script. Describes all the operations needed in Terraform to deploy an Headend.

## terraform.tfvars
Is a file where the user can save the desired values for the Variables.

## vars.tf
You declare the variables in this file

