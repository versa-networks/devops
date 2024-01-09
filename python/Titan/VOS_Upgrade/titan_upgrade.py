#titan_upgrade.py
#

import json
import requests
import urllib3
import getpass
import sys
import time
import re
import csv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

####################definition for timestamp on log messages####################
def local_time():
    seconds = time.time()
    local_time = time.ctime(seconds)
    return local_time

####################Set the standard API request headers####################
json_headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
}


####################Print definition####################
def print_statement(print_variable):
    print(print_variable)

titan_user_variable_print = '''
################################################
# Please enter the following SDWAN / Titan     #
# environment information.                     #
################################################
'''

titan_bad_cred_print = '''
################################################
# !! PLEASE CHECK TITAN CREDENTIALS         !! #
# !! AND TRY AGAIN                          !! #
################################################
'''

titan_connect = '''
################################################
# !! PLEASE CHECK TITAN CONNECTIVITY       !!  #
# !! AND TRY AGAIN                         !!  #
################################################
'''

def else_print(response):
    else_print = (local_time() + " - # Response Code:  " + str(response.status_code) + " - " + str(response.content) + "\n")
    return else_print


####################titan user input variables###################


print_statement(titan_user_variable_print)

titanURL = input("Please enter the titan URL: ") 
titan_org_name = input("Please enter the Titan customer/organization: ")
csv_batch_file = input("Please enter the exact .csv batch file name: ")
titanUserName = input("Please enter your titan Username: ")
titanPassword = getpass.getpass(prompt = "Please enter your titan Password: ")




####################API call url variables####################

## The below is specificall used for testing of the RFC 1918 steering use case
## url structure is as follows:
##
##      Customer name list for customer uuid (GET) = https://<titan_url_or_fqdn>/customer/<org_customer_name>
##      Device list for all devices confgured for an org/customer (GET) = https://<titan_url_or_fqdn>/api/v2/organizations/<org_uuid>/device
##
     

#shared#
https = "https://"

#titan
oauthURL = https + titanURL + '/oxauth/restv1/token'
customers_url = https + titanURL + '/customer/'
device_url = https + titanURL + '/api/v2/organizations/'

devices_string = "/devices/"
upload_string = "/upgrade?isUpgrade=0"
upgrade_string = "/upgrade?isUpgrade=1"
device_uuid_string = '/device'



#################### oxauth headers and data ##########################
##Request OxAuth basic key from Versa and replace <oxauth_key> below ##
#######################################################################
oxauth_headers = {
    'Authorization': 'Basic <oxauth_key>',
    'Content-Type': 'application/x-www-form-urlencoded'
}
oxauth_data = {
    'grant_type': 'password',
    'scope': 'openid profile email uma_protection',
    'username': titanUserName,
    'password': titanPassword
}


## POST (oxauth token) / GET (current device config) / PUT (new device config) api call definitions ###########
def TitanTokenApi(url, call_headers, postData):
    try:
        post_response = requests.post((url), headers=call_headers, verify=False, data=postData, timeout=10)
        post_response.close()
        if re.match('2\d\d', str(post_response.status_code)):
            post_response_json = post_response.json()
            #print(json.dumps(post_response_json, indent=4))
            print("\n" + local_time() + " - # Successfull login to Titan and recieved Oauth Access Token\n ")
            return post_response_json
        else:
            print(else_print(post_response))
            sys.exit(print_statement(titan_bad_cred_print))
    except (requests.exceptions.Timeout, requests.ConnectionError):
        sys.exit(print_statement(titan_connect))

def TitanGetApi(url, call_headers, use_case):
    try:
        get_response = requests.get(url, headers=call_headers, verify=False)
        get_response.close()
        #print(get_response.status_code)
        if re.match('2\d\d', str(get_response.status_code)):
            get_response_json = get_response.json()
            #print(json.dumps(get_response_json, indent=4))
            print("\n" + local_time() + " - # Successfull GET for " + use_case + "\n ")
            return get_response_json
        else:
            print(else_print(get_response))
            sys.exit(print_statement(titan_bad_cred_print))
    except (requests.exceptions.Timeout, requests.ConnectionError):
        sys.exit(print_statement(titan_connect))

def TitanPutApi(url, call_headers, put_data, use_case):
    try:
        put_response = requests.put(url, headers=call_headers, data=put_data, verify=False)
        put_response.close()
        #print(put_response.status_code)
        if re.match('2\d\d', str(put_response.status_code)):
            put_response_json = put_response.json()
            message_response = put_response.json()["message"]
            #print(json.dumps(put_response_json, indent=4))
            print("\n" + local_time() + " - # Successfull PUT commit for device " + use_case + "\n ")
            print("\n" + local_time() + " - # " + message_response + " - " + use_case + "\n ")
            return put_response_json
        else:
            print(else_print(put_response))
            sys.exit(print_statement(titan_bad_cred_print))
    except (requests.exceptions.Timeout, requests.ConnectionError):
        sys.exit(print_statement(titan_connect))


##This portion will create a file for the oxauth token, run the POST TitanTokenApi call, and save the token to a .txt file
## The token will then be added to transaction headers that will be used for the GET and PUT api calls
with open("titan_accessToken.txt", "w") as accessTokenFile:
    accessTokenFile.write(TitanTokenApi(oauthURL, oxauth_headers, oxauth_data)["access_token"])
accessTokenFile.close

with open("titan_accessToken.txt", "r") as accessTokenFile:   
    transaction_headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + str(accessTokenFile.read())
        }
accessTokenFile.close()


##This portion will get the org_uuid based on the user entered org_name
##where org_uuid will be used for additoinal API calls
org_uuid_use_case = titan_org_name + " - organization/customer uuid"
org_uuid = TitanGetApi(customers_url + titan_org_name, transaction_headers, org_uuid_use_case)["data"]["id"]


##This portion will create a device list for all devices deployed by the organization
## and include the site name, device name, and device uuid
org_devices_use_case = titan_org_name + " - all configured devices"
with open("org_site_list.json", "w") as siteListFile:
    siteListFile.write(json.dumps(TitanGetApi(customers_url + org_uuid + device_uuid_string, transaction_headers, org_devices_use_case), indent=4))
    siteListFile.close()

device_list = []

with open("org_site_list.json", "r") as siteListFile:
    site_list = json.loads(siteListFile.read())
    for site in site_list["data"]:
        site_name = site["siteName"]
        for device in site["devices"]:
            device_name = device["deviceName"]
            device_uuid = device["id"]
            device_list_data = {
                "siteName": site_name,
                "deviceName": device_name,
                "id": device_uuid
            }
            device_list.append(device_list_data)
#print(json.dumps(device_list, indent= 4))


##This portion will create a device list for all devices requireing the change that
##have been identified in the .csv batch file
device_change_list = []

with open(csv_batch_file, encoding="utf-8") as csvFile:
    csvReader = csv.DictReader(csvFile)
    for row in csvReader:
        device_change_list.append(row)
#print(json.dumps(device_change_list, indent= 4))


##This portion will compare the list of all devices in the org/customer with the 
##devices listed in the .csv batch file to identify device uuid of devices to upgrade
for change_device in device_change_list:
    change_device_name = change_device["device_name"]
    upload_or_upgrade = change_device["task"]
    for device in device_list:
        if change_device_name == device["deviceName"]:
            device_name = device["deviceName"]
            device_uuid = device["id"]
            #print(device_name + "-" + device_uuid)

            ##UPLOAD SOFTWARE ONLY - the below will upload the software to the device only, no upgrade will be performed
            if upload_or_upgrade == "upload":
                upload_usecase = device_name + " - upload new software."
                upload_put_data = ""
                #print(device_url + org_uuid + devices_string + device_uuid + upload_string)
                TitanPutApi(device_url + org_uuid + devices_string + device_uuid + upload_string, transaction_headers, str(upload_put_data), upload_usecase)

            ##UPGRADE SOFTWARE - the below will upgrade the device.
            elif upload_or_upgrade == "upgrade":
                upgrade_usecase = device_name + " - upgrade device to new software."
                upload_put_data = ""
                #print(device_url + org_uuid + devices_string + device_uuid + upgrade_string)
                TitanPutApi(device_url + org_uuid + devices_string + device_uuid + upgrade_string, transaction_headers, str(upload_put_data), upgrade_usecase)


