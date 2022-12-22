import json
import requests
import urllib3
import getpass
import csv
import os
import datetime


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

##Set the standard API request headers###################################

headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
}

##User input varaibles###################################################
username = input("What is your username?: ") 
passwrd = getpass.getpass()
director_ip = input("What is the primary Director IP or Hostname?: ")
org_name = input("What is the org name?: ")
auth = username,passwrd
upass_message = " Please check connectivity to director and  username/password and try again."

##Set time def and and create ouput files###########################################
def local_time():
    local_time = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    return local_time

output_csv = local_time() + "_" + org_name + "_device_sync_status.csv"

def output_csv_create():
    with open(output_csv, "w") as output_csv_file:
        output_csv_file.write("Device_Group_Name,Device_Name,Template_Sync_State,Director_Sync_State\n")
        output_csv_file.close

##URL Variables for basic auth#######################################################
https = "https://"
device_status_url = ':9182/vnms/template/deviceGroup/deviceStatus'
group_info_url = ':9182/nextgen/deviceGroup?organization='
group_info_string = '&offset=0&limit=2000'


#Device group definitions###
def group_info_response():
    group_info_response = requests.get((https + director_ip + group_info_url + org_name + group_info_string), headers=headers, verify=False, auth=auth)
    group_info_response.close()
    return group_info_response

def device_group_list():
    device_group_json = group_info_response().json()
    device_group_list = device_group_json["device-group"]
    return device_group_list

#Payload data definition for device status api call 
def data():
    pre_device_group = '{"versanms.deviceGroups":{"deviceGroupDataList":[{"name":"'
    middle_device_group = '"}],"template-name":"'
    post_device_group = '"}}'
    data = pre_device_group + device_group_name + middle_device_group + "" + post_device_group
    return data

#Device status api call and generated variables
def device_status_response():
    device_status_response = requests.post((https + director_ip + device_status_url), headers=headers, data=data(), verify=False, auth=auth)
    device_status_response.close()
    return device_status_response

def device_status_list():
    device_status_json = device_status_response().json()
    device_status_list = device_status_json["versanms.deviceGroups"]["deviceGroupDataList"]#["deviceDataList"]
    return device_status_list

def device_name():
    device_name = item["name"]
    return device_name

def device_status():
    device_status = item["status"]
    return device_status

def devicesync_status():
    devicesync_status = item["syncStatus"]
    return devicesync_status


#script to generate output file of device sync status.  will not identify empty device groups
output_csv_create()
if group_info_response().status_code == 200:
    with open(output_csv, "a+") as output_csv_file:
        for device in device_group_list():
            device_group_name = device["name"]
            if device_status_response().status_code == 200:
                #print(device_status_list())
                for status in device_status_list():
                    for item in status["deviceDataList"]:
                        output_csv_file.write(device_group_name + "," + device_name() + "," + device_status() + "," + devicesync_status() + "\n")
                        print(device_group_name + ";" + device_name() + ";" + device_status() + ";" + devicesync_status())
    output_csv_file.close
else:
    print(upass_message)