## Readme for getting eth0 mgmt. IP address from VOS appliances
    - Compatible and tested in Python 3.10.4
    - Tested on Director 22.1.4
    - Script will provide mgmt IP address details for each appliance based on Versa Private IP assignment
    
## Prerequisites 
  - Reachability using ssh from Director is required to VOS Versa Private IP.
  - Devices should be activated on Versa Director. If device is not reachable script will fail to login. Log entries are recorded for failed connections.
  - Script will save data in the same folder from where it is executed. 

## Executing the Python Scripts
  - Copy script and inventory file with Versa Private IPs to Versa Director. Inventory file is a simple .txt file with multiple lines, where one IP per line is recorded.
  - Execute script from Versa Director shell using python. 
  - Script will take username, password and inventory file name as input. Also desired output file name should be provided.
  


## Output Files
  - The output file will be saved in the same location from where the Python script was executed, in .csv format, containing management IPs per device. Additionally, a log file will be created with information on any authentication, connection, or other errors for more granular visibility. 

## Python Scripts in This Directory
  - ssh_get_ethIP.py.  

## Author Information
------------------

Maksym Dmitriiev - Versa Networks