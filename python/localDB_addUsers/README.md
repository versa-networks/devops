## Readme for localDB_addUsers
    - Tested in Python 3.10.4
    - Tested on Director 21.2.2
    - Tested on VOS 21.2.2

## Prerequisites 
  - user_add.csv (example_user_add.csv provided) should be in same directory where python script is run.
  - Reachability to Director is required.
  - Devices should be reachable and in_sync with Director (UI: Administration->Appliances). 

## Executing the Python Scripts
  - Option 1: Update via Service Template (Existing or New)

  - Option 2: Update via Device Template

  - Option 3: Update via Device (NOT RECOMMENDED)

## Output Files
  - Output log file will be saved in the same location the python script is executed.  The following is the nameing convention.
    - add_user.csv_filename_add_user.log 

## Python Scripts in This Directory
  - localDB_addUsers.py:  Will add users to Configuration->Objects and Connectors->Connectors->Users/Groups->Local Database


## Author Information
------------------

Kyle Murray - Versa Networks