from argparse import ArgumentParser
import argparse
import csv
from dataclasses import dataclass
#from ssl import CERT_NONE, create_default_context
import getpass
import json
import re
import sys
from urllib import request
import requests
import urllib3

#suppress certificate verification warnings to accept self signed certificate
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#create class that will describe appliance
@dataclass
class ApplianceOsDetails:
    device_name : str
    device_os_version : str
    device_os_type : str

def is_destinationVD_valid(destinationVD):
    if ('http://' in destinationVD):
        args.destinationVD = destinationVD[7:]
        args.destinationVD = destinationVD.split('/')[2]
        return destinationVD and '.' in destinationVD
    elif ('https://' in destinationVD):       
        args.destinationVD = destinationVD[8:]
        args.destinationVD = destinationVD.split('/')[2]
        return destinationVD and '.' in destinationVD
    else:
        args.destinationVD = destinationVD.split('/')[0]
        return destinationVD and '.' in destinationVD
    
#method to convert json appliance object into python ApplianceOsDetails object
def appliance_from_json(json_appliance):
    if 'Hardware' in json_appliance:
        if 'packageName' in json_appliance['Hardware']:     
            os_type = 'Ubuntu Version 18.04 BIONIC' if re.search('-B',json_appliance['Hardware']['packageName'])  else 'Ubuntu Version 14.05 TRUSTY'
    else: 
        devUnreachable = json_appliance['name']
        print(f'Verify that {devUnreachable} is not reachable. Device OS Type can\'t be identified')
        os_type = 'unknown'
    software_version = json_appliance['softwareVersion'].split(' ')[0]
    return ApplianceOsDetails(json_appliance['name'],software_version,os_type)

#Add command line options support

parser = ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,description='''---Versa Networks---
CSV file will contain all devices from your Tenant. 
Executing script with Provider tenant username will list all available devices. 
Ensure FQDN or IP address of Versa Director is reachable before executing the script.
Script is compatible with Python version 3\n
Example : "python Get_Ubuntu_Version_v1.py"
Optionally execute script with below arguments in a single line.\n
Devices details will be saved in Device_List.csv by default.
If OS Type is unknown, verify that device is reachable from Versa Director''')

parser.add_argument('-d','--dest',dest='destinationVD',help='specify IP address or FQDN of your Versa Director',metavar='')
parser.add_argument('-u','--user',dest='username',help='your Versa Director username',metavar='')
parser.add_argument('-p','--password',dest='password',help='your Versa Director password (to enter password in a hidden format skip this option)',metavar='')
parser.add_argument('-f','--filename',dest='filename',help='filename where device list will be saved',metavar='',default='Device_List.csv')
args = parser.parse_args()

if args.destinationVD is None:
    args.destinationVD = input('specify a valid IP address or FQDN of your Versa Director: ')
    is_destinationVD_valid(args.destinationVD)
else:
    is_destinationVD_valid(args.destinationVD)

if (not args.username):
    args.username = input('enter your Versa Director username: ')

if (not args.password):
    args.password = getpass.getpass('enter your Versa Director password: ')


#Request URL variable
url = f'https://{args.destinationVD}:9182/vnms/appliance/appliance?offset=0&limit=2500'
print(f'Connecting to https://{args.destinationVD}')
print('')

#Connect to VD and get response
try:
    response_full = requests.get(url,verify=False,timeout=10,auth=requests.auth.HTTPBasicAuth(args.username,args.password))
    if response_full.status_code == 401:
        sys.exit('HTTP response 401. Authentication failed.')
    else: response_json = response_full.json()
except (requests.exceptions.Timeout, requests.ConnectionError):
    sys.exit(f'Connection to Versa Director failed. Please verify HTTPs access to {args.destinationVD}')

appliances = response_json['appliances']

#recreate json received object into defined object ApplianceOsDetails
#appliances = list(map(appliance_from_json,appliances))

appliances = [appliance_from_json(json_appliance) for json_appliance in appliances]

bionic_counter =0
trusted_counter = 0
unknown_counter = 0

for appliance in appliances:
    if (appliance.device_os_type == 'Ubuntu Version 18.04 BIONIC'):
        bionic_counter += 1
    elif (appliance.device_os_type == 'Ubuntu Version 14.05 TRUSTY'):
        trusted_counter += 1
    else:
        unknown_counter += 1

sum_counter = bionic_counter + trusted_counter + unknown_counter
print('---')
print(f'{bionic_counter} devices have Ubuntu Version 18.04 installed. {trusted_counter} devices have Ubuntu Version 14.05 installed.')
print(f'{unknown_counter} devices are not reachable from Versa Director.')
print(f'Total number of devices is {sum_counter}.')
print(f'Please check {args.filename} file to get detailed information')


#Save appliances details into csv file
with open (args.filename, 'w', encoding='UTF8', newline='') as f:
    writer = csv.DictWriter(f,fieldnames=['device_name','device_os_version','device_os_type'])
    header = {'device_name':'Device Name','device_os_version':'Device OS Version','device_os_type':'Device OS Type'}
    writer.writerow(header)
    writer.writerows(map(vars,appliances))

#Print in output json sorted and formatted
#print(json.dumps(appliances,sort_keys=True,indent=4))
#Print applicance without formatting it, and check if it has Bionic Version
#print(appliances.endswith('-B'))

