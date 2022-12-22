## Readme for Device Sync Status
    - Tested in Python 3.10.4
    - Tested on Director 21.2.2
    - Tested on VOS 20.2.4, 21.2.2, 21.2.3

## Prerequisites 
  - Director Connectivity (Script uses basic auth, oauth must be added if required)

## Executing the Python Script
  - run sync_status.py

## Output Files
  - Output file will be saved in the same folder where script is run.
  - Naming convention of output file = local_time() + "_" + org_name + "_device_sync_status.csv"
  - Output file .csv columns = Device_Group_Name,Device_Name,Template_Sync_State,Director_Sync_State 

## Python Scripts in This Directory
  - sync_status.py


## Author Information
------------------

Kyle Murray - Versa Networks