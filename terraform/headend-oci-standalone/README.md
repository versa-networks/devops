# Terraform Script for Simple Headend in OCI (Oracle Cloud)

This repository is intended to deploy a Simple Headend (1 Director, 1 Analytics cluster (Analytics, Search, Log Forwarder), 2 Controllers and 1 SVNF). in Oracle cloud infrastructure. It is expected that the customer preloads the Versa Images to their Oracle account and creates an API for its user to perform operations. 

Note: This script is currently tailored for ALS nodes. It needs further work for it to be more generic

## main.tf
This is the main module for the script. Describes all the operations needed in Terraform to deploy an Headend.

## terraform.tfvars
Is a file where the user can save the desired values for the Variables.

## vars.tf
You declare the variables in this file

