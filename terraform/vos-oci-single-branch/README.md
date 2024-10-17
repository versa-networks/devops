# Terraform Script for Standalon VOS Branch in OCI (Oracle Cloud)

This script is designed to deploy a Standalone Branch in Oracle Cloud. It performs all the required operations to support the branch, from the Compartment creation, the VNET creation, and the deployment of the VOS instance. It expects the user to upload the required image to its account and to create the appropiate API keys for authentication.

## main.tf
This is the main module for the script. Describes all the operations needed in Terraform to deploy a Standalone VOS Branch.

## terraform.tfvars
Is a file where the user can save the desired values for the Variables.

## vars.tf
You declare the variables in this file

## output.tf
<<<<<<< HEAD
File that stores important values for the output in Terrafor. 
=======
File that stores important values for the output in Terraform. Currently a placeholder for future development. 
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3
