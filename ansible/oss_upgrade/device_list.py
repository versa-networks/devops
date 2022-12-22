import requests
import json
import urllib3
import getpass

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

##User input varaibles###################################################
username = input("What is your username?") 
passwrd = getpass.getpass() 
auth = username,passwrd

director_ip = input("What is the primary Director IP?")
date = input("What is today's date (YYYYMMDD)?")


##Set the standard API request headers###################################

headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
}


##URL Variables###########################################################
https = "https://"
appliance_detail_url = ':9182/vnms/appliance/appliance?offset=0&limit=1500'


#Definitions##############################################################
def appliance_detail_response ():
    appliance_detail_response = requests.get((https + director_ip + appliance_detail_url), headers=headers, verify=False, auth=auth)
    appliance_detail_response.close()
    return appliance_detail_response

def appliance_list():
    appliance_detail_json = appliance_detail_response().json()
    appliance_list = appliance_detail_json["versanms.ApplianceStatusResult"]["appliances"]
    return appliance_list


def appliance_name():
    appliance_name = appliance["name"]
    return appliance_name

def output_create():
    with open(date + "_device_list.csv", "w") as device_list_file:
        device_list_file.write("hostname\n")
        device_list_file.close


##Generate list of environment devices######################
output_create()

if appliance_detail_response().status_code == 200:
    with open(date + "_device_list.csv", "a+") as device_list_file:
        for appliance in appliance_list():
            device_list_file.write(appliance_name() + "\n")
            device_list_file.close
else:
    print(" Please check connectivity to director and  username/password and try again.")
