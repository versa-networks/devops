# Getting Started with Ansible and Versa
This directory contains the example files described in the Getting Started With Ansible and Versa documentation. Link: TBA

## How to install

Clone the complete devops repository to your local machine

`git clone https://gitlab.com/versa-networks/devops.git`

Go to the getting-started-with-ansible directory

`cd devops/ansible/getting-started-with-ansible`

Create your virtual python environment with pipenv shell. Ansible and all dependend packages will be installed based on the Pipfile.  

`pipenv shell`

## Update variables to your environment

Update the the Versa Director base URL, organization name and address object name to your environment in the group_vars/all.yaml file. 

## Run the playbook

You can run the playbook using the following command: 

`ansible-playbook -i inventory.yaml playbooks/updateAddressObject.yaml`







