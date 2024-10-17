## Readme for Configured_CGNATs
    - Tested in Python 3.6.9, 3.10.4
    - Tested in Python 2.7.12, 2.7.17
    - Tested on Director 21.2.2, 21.2.3, 21.3.1
    - Tested on VOS 21.2.2, 21.2.3

## Prerequisites 
  - Depending on the size of the environment, this script may take considerable time to complete.
  - Director Connectivity (Script uses basic auth, oauth must be added if required)
  - Print output displayed when issue with user question responses.
    - Director connectivity error
    - username / password error
    - organization not present error

## Executing the Python Script
  - Python3 run 3_10_cgnat_pools_v2_3.py
  - Python2 run 2_7_cgnat_pools_v2_3.py

## Output Files
  - Output file will be saved in the same folder where script is run.
  - Naming convention of output file
    - "cgnat_log_" + local_time() + "_.log"
    - "cgnat_csv_" + local_time() + "_.txt"
  - For spreadsheet output, open cgnat_csv(.txt) in Excel & use ; delimiter
  - DHCP interfaces used for CGNAT will not have an IP address listed in output files and will be listed as "dhcp interface". Future versions of this script will look to include IP address for DHCP interface as well.

## Python Scripts in This Directory
  - 3_10_cgnat_pools_v2_3.py
  - 2_7_cgnat_pools_v2_3.py

## Author Information
------------------

Kyle Murray - Versa Networks
