## Purpose of the script
<<<<<<< HEAD
The script creates access rules on a secure SD-WAN device ( via the versa Director) from a CSV file. 
You can use the CSV file provided on this page ( ```rules-create.csv``` ) and populate it with your own rules.
Make sure the address & service objects already exist in Versa Director, the script won't create them for you.

```
RULE_NAME;SOURCE_ADDRESS;DESTINATION_ADDRESS;SERVICES;ACTION
r1;192.168.1.0_24;192.168.2.0_24;http;allow
r2;192.168.1.0_24,192.168.2.0_24,192.168.3.0_24;192.168.2.0_24;http,https;allow
r3;192.168.1.0_24,192.168.2.0_24;192.168.2.0_24;http;deny
r4;192.168.1.0_24;192.168.2.0_24;bgp,tftp;allow
...
```
=======
The script creates security access rules on a device or device-template from a CSV file. 
You can use the CSV file provided on this page ( ```rules-create-10.csv``` ) and populate it with your own rules.
Make sure the address, service and application objects already exist on Versa Director, the script won't create them for you.

>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3

## Installation and Dependencies
You will need python3 as well as differents python package. They can be installed locally with pip3
```
pip3 install json
pip3 install requests
pip3 install urllib3
pip3 install argparse
```

## How does it work ?
Before you get started make sure you have the following information:
1) The IP address of the Director where the CPE is managed.
<<<<<<< HEAD
2) The Director Administrator login ( Default is Administrator)
3) The Director Administrator password ( Default is versa123 )
4) The name of the CPE where the change ( or rule review ) is required.
5) The name of the organization where the CPE is managed
6) The name of the Access Policy group where the rules are located ( Default is Default-Policy )
=======
2) The Director Administrator login ( Default is Administrator).
3) The Director Administrator password.
4) The name of the Template or CPE where your want to create those rules
5) The name of your organization.
6) The name of the Access Policy group where your want to install the new rules ( Default is Default-Policy )
7) Optional: you can use the knob ```--bulk yes``` to upload all the rules in one go.
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3

![ALT](./rules-create.png)

One you have the settings above, you can use the script as described below :
<<<<<<< HEAD
Note that by default, ```--user=Administrator``` and  ```--password=versa123```. Make sure you change those variable if required.

```
% python3 rules-create.py --ip 10.43.43.100 --device BRANCH-11 --csv_file rules-create.csv
=======

Example 1: Use the CSV file rules-create-10.csv to create rules on the device office-eu located in the Organization Versa
```
% python3 rules-create.py --user Administrator --password=xxxx --target device:office-eu --csv_file rules-create-10.csv --org Versa

>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3
[->] access rule r6 was created with status code 201
[->] access rule r9 was created with status code 201
[->] access rule r8 was created with status code 201
[->] access rule r3 was created with status code 201
[->] access rule r10 was created with status code 201
[->] access rule r4 was created with status code 201
[->] access rule r5 was created with status code 201
[->] access rule r11 was created with status code 201
[->] access rule r2 was created with status code 201
...
```
<<<<<<< HEAD
   
## How to use the Help command

You can execute the script with the ```--help``` flag to help you the syntax.

```
% python3 rules-create.py --help
usage: rules-create.py [-h] [--ip IP] [--device DEVICE] [--org ORG] [--group GROUP] [--user USER] [--password PASSWORD] [--csv_file CSV_FILE]
=======

Example 2: Use the CSV file rules-create-10.csv to create rules on the template Template-OF-EU located in the Organization Versa
```
% python3 rules-create.py --user Administrator --password=xxxx --target device:Template-OF-EU --csv_file rules-create-10.csv --org Versa

[->] access rule r6 was created with status code 201
[->] access rule r9 was created with status code 201
[->] access rule r8 was created with status code 201
[->] access rule r3 was created with status code 201
[->] access rule r10 was created with status code 201
[->] access rule r4 was created with status code 201
[->] access rule r5 was created with status code 201
[->] access rule r11 was created with status code 201
[->] access rule r2 was created with status code 201
...
```

Example 3: Use the CSV file rules-create-10.csv to create rules on the template Template-OF-EU located in the Organization Versa in one go
```
% python3 rules-create.py --user Administrator --password=xxxx --target template:Template-OF-EU --csv_file rules-create-10.csv --org Versa --bulk yes

[->] access rules with bulk method for template Template-OF-EU were created successfully
```
   
## How to use the Help command

You can execute the script with the ```--help``` flag to help you with the syntax.

```
% python3 rules-create.py --help                                                                                                         
usage: rules-create.py [-h] [--ip IP] [--target TARGET] [--org ORG] [--group GROUP] [--user USER] [--password PASSWORD] [--csv_file CSV_FILE] [--bulk BULK]
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3

Script to load access policies from a CSV file

optional arguments:
  -h, --help           show this help message and exit
<<<<<<< HEAD
  --ip IP              IP address of Director (default: 10.43.43.100)
  --device DEVICE      Branch Device name (default: BRANCH-11)
  --org ORG            Organization name (default: Versa)
  --group GROUP        Policy Group Name (default: Default-Policy)
  --user USER          GUI username of Director (default: Administrator)
  --password PASSWORD  GUI password of Director (default: versa123)
  --csv_file CSV_FILE  CSV File including the access policy rules (default: rules-create.csv)
=======
  --ip IP              IP address of Director (default: cloud221.versa-networks.com)
  --target TARGET      Device (device:XXX) or Device Template (template:XXX) where the rules must be applied.
  --org ORG            Organization name (default: Versa)
  --group GROUP        Policy Group Name (default: Default-Policy)
  --user USER          GUI username of Director (default: Administrator)
  --password PASSWORD  GUI password of Director
  --csv_file CSV_FILE  CSV File including the access policy rules
  --bulk BULK          Bulk the rules in a single API call for faster execution. !!! This mode only works with new Access Policy Group !!! (default: no)
>>>>>>> 542986d30afb78ccc6db2f97bbd644f3231bb1e3
 ```