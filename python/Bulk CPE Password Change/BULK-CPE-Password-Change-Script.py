
from tkinter.messagebox import NO
from urllib.parse import urljoin
from requests.auth import HTTPBasicAuth
import requests
import json
import warnings
import argparse
import re
import getpass
import datetime
import os


warnings.filterwarnings("ignore")

parser = argparse.ArgumentParser(description='Script for changing cli (admin) password of VOS CPEs in an Organization')
parser.add_argument('--ip', default='44.44.44.44', type=str,
                    help='IP address of Director')
parser.add_argument('--port', default='9182', type=str,
                    help='Rest API port of Director')
parser.add_argument('-u', '--user', default='Administrator', type=str,
                    help='GUI username of Director')
parser.add_argument('-p', '--password', default='PASSWORD', type=str,
                    help='GUI password of Director')

args = parser.parse_args()

r_list = []
unr_list = []
file_name = 'password_change_log.txt'

auth_key = HTTPBasicAuth(args.user, args.password)

x = datetime.datetime.now()

print("This script changes cli passwords of all the CPEs in an Organization. It uses rest API interface of Versa Director. \n")
print("Enter the new cli password as input.\n")
print("The password must be at least 8-characters long! \n")
print("The password must include at least 1 capital letter and at least 1 number ! \n")

while True:
    while True:
        org_name = input("Please enter the Organization name : ")
        if not org_name.replace(' ', ''):
            print("The Organization name is mandatory... ")
            continue
        else:
            break
    while True:
        path_name = input("Please enter a file path where the log file will be written (Ex: /home/versa/ or C:\Users\user\Desktop) :")
        if not os.path.exists(path_name):
            print("There is not such a path. Please enter a valid path...")
            continue
        elif not path_name.replace(' ', ''):
            print("There is not such a path. Please enter a valid path...")
            continue
        else:
            break
 
    
    p = getpass.getpass(prompt = "Please enter the new cli password: ")
    if len(p) < 8:
        print("The password must be at least 8-characters long!")
    elif re.search('[0-9]', p) is None:
        print("The password must include at least 1 number!")
    elif re.search('[A-Z]', p) is None:
        print("The password must include at least 1 capital letter!")
    else:
        print("The password is okay !")
        p2 = getpass.getpass(prompt = "Please enter the password again: ")
        if p == p2:
            break
        else:
            print("The passwords you entered didn't match, please try again..")

if p == p2:
    organizations_url = 'https://%s:%s/nextgen/organization' % (args.ip, args.port)
    api_base_url = 'https://%s:%s/vnms/dashboard/tenantDetailAppliances/' % (args.ip, args.port)

    organizations_response = requests.get(organizations_url, auth=auth_key, verify=False)
    assert organizations_response.status_code == 200, 'connection is not valid'
    organizations_response_dict = organizations_response.json()
    
    tenant_dicts = [{'name': x['name']} for x in organizations_response_dict]

    for idx, tenant in enumerate(tenant_dicts):
        if tenant['name'] == org_name:
            tenant_url = urljoin(api_base_url, tenant['name'])
            tenant_result = requests.get(tenant_url, auth=auth_key, verify=False)
            assert tenant_result.status_code == 200, 'connection is not valid'
            tenant_result_dict = tenant_result.json()
            tenant['devices'] = list()
    
            for device in tenant_result_dict:
                dev_name = device['name']
                dev_type = device['applianceLocation']['type']
                
                if device['ping-status'] != 'UNREACHABLE' and (dev_type != 'controller' and dev_type != 'Controller'):

                    pass_url = 'https://%s:%s/api/config/devices/device/%s/config/system/users/admin' % (args.ip, args.port, dev_name)

                    payload = json.dumps({
                        "users": {
                            "name": "admin",
                            "password": p,
                            "ssh-public-key": [],
                            "login": "shell",
                            "role": "admin"
                        }
                    })
                    headers = {
                        'Content-Type': 'application/vnd.yang.data+json',
                    }

                    response = requests.request("PUT", pass_url, headers=headers, data=payload, auth=auth_key, verify=False)

                    if response.status_code == 201 or response.status_code == 204:
                        r_list.append(dev_name)
                        print("\n%s -- CPE cli password was changed. \n" % dev_name)

                    else:
                        if dev_name not in unr_list:
                            unr_list.append(dev_name)
    
                else:
                    if dev_name not in unr_list and (dev_type != 'controller' and dev_type != 'Controller'):
                        unr_list.append(dev_name)
                        #print("%s -- CPE cli password could not be changed. \n" % dev_name)
                        


    with open(os.path.join(path_name, file_name), 'a') as f:
        f.write('\n THE CPEs on which cli password was changed  -- %s \n' % x)
        for element in r_list:
            f.write(element + "\n")
        #f.write('\n THE CPEs on which cli password could not changed -- %s \n' % x)
        #for element in unr_list:
        #    f.write(element + "\n")


print("\n Completed... \n\nLogs can be found in the log file under %s ." % path_name)
