## Readme for Fetch_Interfaces_Details
    - Compatible and tested in Python 3.10.4
    - Tested on Director 22.1.3
    - Script will provide interfaces IP address inventory details (includes DHCP and static interfaces) for each appliance per tenant
    
## Prerequisites 
  - Reachability using port 9182 to Director is required from the host where the script will be executed.
  - Devices should be reachable from Versa Director. If device is not reachable script will not be able to fetch device details
  - Script will save data in the same folder from where it is executed. User who execute the script should have write permissinons in the folder

## Executing the Python Scripts
  - Option 1. Execute the script and follow instructions to provide Versa Director FQDN/IP, username, password and tenant information
  - Option 2. Use arguments with the script
    - -h show help message and exit
    - -d specify IP address or FQDN of your Versa Director
    - -u your Versa Director username
    - -p your Versa Director password (to enter password in a hidden format skip this option)
    - -t tenant name
  

## Output Files
  - Output file will be saved in the same location from where the python script was executed in .csv format with Interfaces and IP address details. Additionally, full interface data will be available in .json format 

## Python Scripts in This Directory
  - fetch_int_details.py.  

## Author Information
------------------

Maksym Dmitriiev - Versa Networks