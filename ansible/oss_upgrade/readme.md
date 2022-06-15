##### Readme ansible folder

## Readme for oss_upgrade
    - Tested on Director 21.2.2
    - Tested on VOS 20.2.4 & 21.2.2
	- Ansible:
		- ansible [core 2.11.12]
		- python version = 3.6.9 
		- jinja version = 2.10

## Prerequisites 
  - OSS pack must be downloaded to Director (UI: Administration->Inventory->OS Security Pack->Appliance)
  - Batch file should be in role files directory.
  - Reachability to Director is required.
  - Devices should be in_sync with Director (UI: Administration->Appliances). Devices not in_sync will be skipped and 
    identified in output files.


## Executing the Python Scripts
  - Run the ansible-playbook site.yml
  - Select from the following options.
	-	Option 1: Option 1 will update all devices listed in the batch file 1 at a time.  A device will be completed prior to 
		moving onto the next device in the batch.
	-	Option 2: Option 2 will update all devices listed in the batch file 5 at a time.  5 devices will be completed prior to 
		moving onto the next group of 5 devices in the batch.

## Output Files
  - Output files will be saved in the role files directory.  The following is the nameing convention.
    - batch file name_OSS_version_OSS Version Number.csv 
    - batch file name_OSS_version_OSS Version Number.log


## file structure (tree)
```
.
├── device_list.py
├── roles
│   └── oss_update
│       ├── defaults
│       │   └── main.yml
│       ├── files
│       │   ├── batch-1-test.csv #<not included in folder, example for batch file location>#
│       │   └── batch-2-test.csv #<not included in folder, example for batch file location>#
│       ├── handlers
│       │   └── main.yml
│       ├── meta
│       │   └── main.yml
│       ├── README.md
│       ├── tasks
│       │   └── main.yml
│       ├── templates
│       │   ├── oss_pack_update_batch_option1.j2
│       │   └── oss_pack_update_batch_option2.j2
│       ├── tests
│       │   ├── inventory
│       │   └── test.yml
│       ├── .travis.yml
│       └── vars
│           └── main.yml
└── site.yml
```


## Files in This Directory
	- 	device_list.py: An overall list of devices can be generated using the device_list.py script located in this folder.  
      	This overall list can then be brokeninto batches (e.g., Batches of 25 devices, new files = batch1.csv, batch2.csv., etc).
	-	site.yml: Playbook for user generated vars with the oss_update role.  This is the file to run (ansible-playbook site.yml).
	-	tasks/main.yml: Playbook for oss_update role.
	-	templates/oss_pack_update_batch_option1.j2 & oss_pack_update_batch_option2.j2: jinja 2 templates to generate executable .py


## Author Information
------------------

Kyle Murray - Versa Networks


