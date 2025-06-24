# Concerto script run prior to Director script to limit repetitive user input variables.


# Shared Files:
    - batch_test.csv

# Concerto (SSE) Files:
    - sse_onprem_S2S.py
    - concertoS2Sbody.j2
    - concerto_bgp_importExport.j2

![SSE-OnPrem Flow Chart](https://gitlab.com/kyle.murray.versa/devops/-/blob/master/python/SSE_Site-to-Site_Tunnels/SSE-Onprem.png)

# Director (SDWAN) Files:
    - onprem_sse_S2S.py
    - dir_bgp_group_config.j2
    - dir_bgp_proto_config.j2
    - dir_vpn_profile.j2


# Software Versions:
	- Concerto 11.3 through 12.2.1
	- Director 21.2.2, 21.2.3, 22.1*
	- Python 3.6.9, 3.11.0

# Required Python Modules:
	- json, requests, urllib3, getpass, csv, sys, time, re, os, glob, jinja2, sseclient, traceback, shutil, string, secrets

# Required Files (must have read/write access to directory where stored):
	- sse_onprem_S2S_.py (*Concerto*)
	- concerto_bgp_importExport.j2
	- concertoS2Sbody.j2
	- onprem_sse_S2S.py (*Director*)
	- dir_bgp_group_config.j2
	- dir_bgp_proto_config.j2
	- dir_vpn_profile.j2

# Output log files for Concerto and Director. Folder and file will be created with batch file name
	- <batch_file_name>/<batch_file_name>.csv_concerto.log
	- <batch_file_name>/<batch_file_name>.csv_director.log

# Author Information
------------------

- Kyle Murray - Versa Networks

