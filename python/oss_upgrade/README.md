### Readme for oss_upgrade
    - Tested in Python 3.10.4
    - Tested on Director 21.2.2
    - Tested on VOS 20.2.4 & 21.2.2

## Scripts for all Devices (up to 2000 total overall deployment size)
	- oss_pack_update.py: Updates 1 device at a time and awaits completion prior to moving to next device
	- oss_pack_update_2.py: Initiates all device updates and runs checks after all devices updates have been initiated.

## Scripts for Batch of Devices (up to 2000 total overall deployment size)
    - batch-test.csv: example .csv file for list of devices included in the batch. Should be in same folder you are running python.  
    - oss_pack_update_batch.py: Updates 1 device in the batch at a time and awaits completion prior to moving to next device
    - oss_pack_update_2 _batch.py: Initiates batch device updates and runs checks after all batch device updates have been initiated.

## Author Information
------------------

Kyle Murray - Versa Networks