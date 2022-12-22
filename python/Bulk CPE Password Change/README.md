
Script for changing cli (admin) password of all the VOS cpes in an Organization
------------------------------------------------------------------------------------------

Tested in Python 3.10.5
Tested on Versa Director 21.2.2
Tested on VOS 21.2.2

------------------------------------------------------------------------------------------
Purpose

The script changes cli (admin) password of all the VOS cpes in an Organization. 
The script uses the API interface of Director.
Script logs are saved in password_change_log.txt file.

------------------------------------------------------------------------------------------
Prerequisites

certifi==2021.10.8
charset-normalizer==2.0.12
idna==3.3
requests==2.27.1
urllib3==1.26.9

#pip3 freeze > prerequisites.txt
#pip install -r prerequisites.txt

------------------------------------------------------------------------------------------
Usage

command-line> python CPE-CLI-PASS-CHANGE.py [-h] [--ip IP] [--port PORT] [-u USER] [-p PASSWORD]

Script for changing cli (admin) password of VOS CPEs in an Organization

options:
  -h, --help            	show this help message and exit
  --ip 	     	          	IP address of Director
  --port 		           	Rest API port of Director
  -u USER, --user 	  		GUI username of Director
  -p PASSWORD, --password  	GUI password of Director