## Service Template add to device group and commit (without new bind data)
    - Tested in Python 3.11
    - Tested in Python 3.10
    - Tested in Python 2.7
    - Tested on Director 21.2.2, 21.2.3
    - Tested on VOS 21.2.2, 21.2.3

## Use Case:
    - New service template is created that needs to be added to multiple device groups and committed.  
    - This would be most useful in deployments that have a large amount of device groups (for example, 1 device group per device as I have seen in a few deployments).
    - Utilizes a batch file (csv) approach where a list of device groups can be in the batch file to target a pilot, regional, etc., approach.
    - Caveats:
        - The script in the current version cannot be utilized for a service template that introduces new bind data.
        - Commit in 21.2.3 cannot be done for service template config only and will commit all changes to the device even if not part of the new service template.
        - Feature for the above bullet will be available in 22.1 and will look to adjust when that is GA.


## Prerequisites 
  - Batch file should be in same directory where python script is run (example file in repo).
  - Reachability to Director is required.
  - Devices should be in_sync with Director (UI: Administration->Appliances). Devices not in_sync will be skipped and 
    identified in output files.

## Executing the Python Scripts
  - Create a batch csv file for Device Groups where Service Template will be added / committed.
  - Run servTemp_add.py (either python2 or python3)

## Output Files
  - Output log files will be saved in the same location the python script is executed. 




## Author Information
------------------

Kyle Murray - Versa Networks
