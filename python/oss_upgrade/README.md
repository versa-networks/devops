## Readme for oss_upgrade
    - Tested in Python 3.10.4
    - Tested on Director 21.2.2
    - Tested on VOS 20.2.4 & 21.2.2

## Prerequisites 
  - OSS pack must be downloaded to Director (UI: Administration->Inventory->OS Security Pack->Appliance)
  - Batch file should be in same directory where python script is run.
  - Reachability to Director is required.
  - Devices should be in_sync with Director (UI: Administration->Appliances). Devices not in_sync will be skipped and 
    identified in output files.

## Executing the Python Scripts
  - Option 1: Option 1 will update all devices listed in the batch file 1 at a time.  A device will be completed prior to 
    moving onto the next device in the batch.  Script for Option 1 is oss_pack_update_batch_option1.py.

  - Option 2: Option 2 will update all devices listed in the batch file 5 at a time.  5 devices will be completed prior to 
    moving onto the next group of 5 devices in the batch. Script for Option 2 is oss_pack_update_batch_option2.py.

## Output Files
  - Output files will be saved in the same location the python script is executed.  The following is the nameing convention.
    - batch file name_OSS_version_OSS Version Number.csv 
    - batch file name_OSS_version_OSS Version Number.log

## Python Scripts in This Directory
  - device_list.py: An overall list of devices can be generated using the device_list.py script located in this folder.  
      This overall list can then be brokeninto batches (e.g., Batches of 25 devices, new files = batch1.csv, batch2.csv., etc).
  - oss_pack_update_batch_option1.py: Option 1 script will update all devices in a batch, 1 device at a time.
  - oss_pack_update_batch_option2.py: Option 2 script will update all devices in a batch, in groups of 5.


## Author Information
------------------

Kyle Murray - Versa Networks