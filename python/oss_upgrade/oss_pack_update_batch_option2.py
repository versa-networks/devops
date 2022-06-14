from multiprocessing.sharedctypes import Value
from threading import local
import requests
import json
import csv
import urllib3
import getpass
import time
import os
from itertools import islice
from itertools import zip_longest

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

##User input varaibles###################################################
username = input("What is your username?") 
passwrd = getpass.getpass() 
auth = username,passwrd
upass_message = " Please check connectivity to director and  username/password and try again."

director_ip = input("What is the primary Director IP or Hostname?")
csv_batch_file = input("What is the full name of the .csv Batch File?")
oss_pack_version = input("What is the OSS pack version(YYYYMMDD)?")

##Set the standard API request headers###################################

headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
}


##URL Variables###########################################################
https = "https://"
appliance_detail_url = ':9182/vnms/appliance/appliance?offset=0&limit=2000'
oss_pack_url = ':9182/vnms/osspack/device/install-osspack'
deep = '?deep=true'
fw_slash =':9182/'


##Appliance check variables################################################
reach_status = "UNREACHABLE"
sync_status = "IN_SYNC"
in_progress = 'IN_PROGRESS'
completed = 'COMPLETED'


##Set time def for print outputs###########################################
def local_time():
    seconds = time.time()
    local_time = time.ctime(seconds)
    return local_time


##Output file name variables / ###########################################
output_log = csv_batch_file + "_OSS_version_" + oss_pack_version + ".log"
output_csv = csv_batch_file + "_OSS_version_" + oss_pack_version + ".csv"




##Batch file conversion from csv to json#################################
jsonFile = csv_batch_file + ".json"
csv_data = {}

with open(csv_batch_file, encoding="utf-8") as csvFile:
    csvReader = csv.DictReader(csvFile)
    for rows in csvReader:
        key = rows["hostname"]
        csv_data[key] = rows

with open(jsonFile, "w", encoding="utf-8") as jsonFile:
    jsonFile.write(json.dumps(csv_data))
    jsonFile.close


##Load json variables from converted json batch file#################################
##output_group defined for number of devices to group within the batch###############

with open(csv_batch_file + ".json", "r") as json_batch_file:
    variables = json.load(json_batch_file)
    def variables_elements(n, iterable, padvalue='x'):
        return zip_longest(*[iter(iterable)]*n, fillvalue=padvalue)

output_group = variables_elements(5,variables)

#Definitions##############################################################

#Appliance data definitions###
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

def appliance_ping():
    appliance_ping = appliance["ping-status"]
    return appliance_ping

def appliance_sync():
    appliance_sync = appliance["sync-status"]
    return appliance_sync

def appliance_oss():
    appliance_oss = appliance["OssPack"]["osspackVersion"]
    return appliance_oss

#Update data definition###
def data():
    update_type = '{"update-type":"full","devices":'
    pre_device = '["'
    post_device = '"],'
    pre_version = '"version":"'
    post_version = '"}'
    data = update_type + pre_device + item + post_device + pre_version + oss_pack_version + post_version
    return data

#create status check response id dictionary###
response_id_dict = {}

#Output log and file definitions###
def output_log_create():
    with open(output_log, "w") as output_log_file:
        output_log_file.write("###" + csv_batch_file + "_OSS_version_" + oss_pack_version + "###\n")
        output_log_file.close

def init_log_data():
    init_log_data = local_time() + " " + appliance_name() + " OSS pack upgrade initiated########\n"
    return init_log_data

def init_log_data_print_write():
    print(init_log_data())
    output_log_file.write(init_log_data())

def issue_log_data():
    issue_log_data = local_time() + " " + appliance_name() + " encountered issues upgrading OSS pack.\n"
    return issue_log_data

def reach_log_data():
    reach_log_data = local_time() + " " + appliance_name() + " is either unreachable or out of sync with Director\n"
    return reach_log_data

def prog_log_data():
    prog_log_data = " " + item + " OSS pack upgrade COMPLETED " + response_id + "\n"
    return prog_log_data

def output_csv_create():
    with open(output_csv, "w") as output_csv_file:
        output_csv_file.write("hostname;reachability;director_sync;update_status;oss_version;task_id\n")
        output_csv_file.close

def issue_csv_data():
    issue_csv_data = appliance_name() + ";" + appliance_ping() + ";" + appliance_sync() + ";issue upgrading OSS;issue upgrading OSS;issue upgrading OSS;\n"
    return issue_csv_data

def reach_csv_data():
    reach_csv_data = appliance_name() + ";" + appliance_ping() + ";" + appliance_sync() + ";unreachable or out of sync;unreachable or out of sync;issue upgrading OSS;\n"
    return reach_csv_data

def prog_csv_data():
    prog_csv_data = item + ";" + appliance_ping() + ";" + appliance_sync() + ";COMPLETED;" + oss_pack_version + ";" + response_id + "\n"
    return prog_csv_data

def reach_data_print_write():
    print(reach_log_data()) 
    output_log_file.write(reach_log_data())
    output_csv_file.write(reach_csv_data())

def issue_data_print_write():
    print(issue_log_data())
    output_log_file.write(issue_log_data())
    output_csv_file.write(issue_csv_data())

def prog_data_print_write():
    print(local_time() + prog_log_data())
    output_log_file.write(local_time() + prog_log_data())
    output_csv_file.write(prog_csv_data())

##cleanup unecessary post script files###
def file_cleanup():
    os.remove(csv_batch_file  + ".json")


#Upgrade OSS pack on all batch devices and check for status######################
print("")
print("")
print('########################################')
print('##### Begin OSS pack update process#####')
print('########################################')
print("")
print("")
appliance_detail_response()
output_log_create()
output_csv_create()
if appliance_detail_response().status_code == 200:
    with open(output_log, "a+") as output_log_file, open(output_csv, "a+") as output_csv_file:
        for group in output_group:
            print("###############Init Group###############")
            print("")
            for item in group:
                for appliance in appliance_list():
                    if item in appliance_name():
                        if reach_status not in appliance_ping() and sync_status in appliance_sync():
                            oss_pack_post = requests.post((https + director_ip + oss_pack_url), headers=headers, data = data(), verify=False, auth=auth)
                            oss_pack_post_json = oss_pack_post.json()
                            response_id = oss_pack_post_json["TaskResponse"]["link"]["href"]
                            response_id_d = {item:response_id}
                            response_id_dict.update(response_id_d)
                            if oss_pack_post.status_code == 201:
                                init_log_data_print_write()
                        else:
                            init_log_data_print_write()
                            reach_data_print_write()
            print("###############Check Group###############")
            print("")
            appliance_detail_response ()
            for item in group:
                for appliance in appliance_list():
                    if item in response_id_dict and item in appliance_name():
                        if reach_status not in appliance_ping() and sync_status in appliance_sync():
                            print(item)
                            print(response_id_dict[item])
                            response_id = response_id_dict[item]
                            oss_pack_check = requests.get((https + director_ip + fw_slash + response_id), headers=headers, verify=False, auth=auth)
                            oss_pack_check.close
                            oss_pack_check_json = oss_pack_check.json()
                            oss_pack_check_status = oss_pack_check_json["versa-tasks.task"]["versa-tasks.task-status"]
                            print(oss_pack_check_status)
                            for oss in oss_pack_check:
                                if oss_pack_check.status_code == 200 and oss_pack_check_status == completed:
                                    prog_log_data()
                                    prog_csv_data()
                                    local_time()
                                elif oss_pack_check.status_code == 200 and oss_pack_check_status == in_progress:
                                    oss_pack_check = requests.get((https + director_ip + fw_slash + response_id), headers=headers, verify=False, auth=auth)
                                    oss_pack_check.close
                                    oss_pack_check_json = oss_pack_check.json()
                                    oss_pack_check_status = oss_pack_check_json["versa-tasks.task"]["versa-tasks.task-status"]
                            print(oss_pack_check_status)
                            prog_data_print_write()
                        else:
                            reach_data_print_write()
                    
else:
    print(upass_message)

file_cleanup()   


