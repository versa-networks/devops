## Readme for titan_upgrade
    - Tested in Python 3.11
    - Tested on Titan 10.2.2


## Prerequisites 
  - Batch file (example = test_batch.csv) should be in same directory where python script is run.
  - Reachability to Titan is required.
  - Request OxAuth key from Versa.


## Executing the Python Script.
  - Update batch file (example = test_batch.csv) device names and task (upload vs upgrade).
  - Replace <oxauth_key> in line 101 of script with OxAuth key recieved from Versa.
  - Run python script titan_upgrade.py.  The following information is required and will be asked for when script is run:
    - Titan URL
    - Titan Organization Name
    - CSV Batch File Name
    - Titan Username
    - Titan Password


## Files in This Directory
  - test_batch.csv: example batch file, update devices and task (upload vs upgrade)
  - titan_upgrade.py: python script for upgrading multiple Titan managed VOS devices. 


## Author Information
------------------

Kyle Murray - Versa Networks