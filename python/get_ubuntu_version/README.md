## Readme for get_ubuntu_version
    - Compatible and tested in Python 3.10.4
    - Tested on Director 21.2.2, 21.3.1
    - Tested on VOS 21.2.1, 21.2.2, 21.2.3

## Prerequisites 
  - Reachability to Director is required.
  - Devices should be reachable from Versa Director. If device is not reachable script will not be able to identify Ubuntu Version, it will get "unknown" sign

## Executing the Python Scripts
  - Option 1. Execute the script and follow instructions to provide Versa Director FQDN/IP, username and password
  - Option 2. Use arguments with the script
    - -h show help message and exit
    - -d specify IP address or FQDN of your Versa Director
    - -u your Versa Director username
    - -p your Versa Director password (to enter password in a hidden format skip this option)
    - -f filename where device list will be saved

## Output Files
  - Output file will be saved in the same location the python script is executed in .csv format. Default name is Device_List.csv that can be changed with -f option. 

## Python Scripts in This Directory
  - get_ubuntu_version_v1.py.  

## Author Information
------------------

Maksym Dmitriiev - Versa Networks