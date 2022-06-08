##### Readme ansible folder


## /oss_update


- Tested in Ansible: 
		- ansible [core 2.11.12]
		- python version = 3.6.9 
		- jinja version = 2.10  
-  Tested on Director 21.2.2
- Tested on VOS 20.2.4 & 21.2.2

## file structure (tree)
```
.
├── device_list.py
├── roles
│   └── oss_update
│       ├── defaults
│       │   └── main.yml
│       ├── files
│       │   ├── batch_1-test.csv    #<not included in folder, example for batch file location>#
│       │   ├── batch_all-test.csv  #<not included in folder, example for batch file location>#
│       │   └── batch-test.csv      #<not included in folder, example for batch file location>#
│       ├── handlers
│       │   └── main.yml
│       ├── meta
│       │   └── main.yml
│       ├── README.md
│       ├── tasks
│       │   └── main.yml
│       ├── templates
│       │   ├── oss_pack_update_2_batch.j2
│       │   └── oss_pack_update_2.j2
│       ├── tests
│       │   ├── inventory
│       │   └── test.yml
│       ├── .travis.yml
│       └── vars
│           └── main.yml
└── site.yml
```

## site.yml
	- Playbook for user generated vars with the oss_update role.  This is the file to run (ansible-playbook site.yml).
## roles/oss_update/tasks/main.yml
	- Playbook for oss_update role.
## roles/oss_update/templates/oss_pack_update_2_batch.j2 & oss_pack_update_2.j2
	- jinja 2 templates to generate executable .py files run by site.yml->main.yml
## roles/oss_update/files/
	- location to save user created batch files in .csv format.  An overall list of devices can be generated
	  using the device_list.py script located in this folder.  This overall list can then be broken
	  into batches.
	- Playbook generated output files will be saved in this directory (.csv and .log)



