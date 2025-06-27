# Getting Started with Ansible and Versa
This directory contains the example files described in the [Getting Started With Ansible and Versa](https://academy.versa-networks.com/docs/getting-started-with-ansible-and-versa/) Versa Academy article.

## Install pipenv
You need to install pipenv to install the python packages required to run the playbook. Please refer to the [pipenv documentation](https://pipenv.pypa.io) how to do that. 

## Clone and install packages

Clone the complete devops repository to your local machine

`git clone https://gitlab.com/versa-networks/devops.git`

Go to the getting-started-with-ansible directory

`cd devops/ansible/getting-started-with-ansible`

Create your virtual python environment with pipenv shell. 

`pipenv shell`

Install packages from the Pipfile.lock

`pipenv insall`


## Update variables to your environment

Update the the Versa Director base URL, organization name and address object name to your environment in the group_vars/all.yaml file. 

Update the inventory file (invetory.yaml) for your setup

## Run the playbook

You can run the playbook using the following command: 

`ansible-playbook -i inventory.yaml playbooks/updateAddressObject.yaml`
