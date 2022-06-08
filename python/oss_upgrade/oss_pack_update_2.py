import requests
import json
import urllib3
import getpass
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

##User input varaibles###################################################
username = input("What is your username?") 
passwrd = getpass.getpass() 
auth = username,passwrd
upass_message = " Please check connectivity to director and  username/password and try again."

director_ip = input("What is the primary Director IP?")
oss_pack_version = input("What is the OSS pack version(YYYYMMDD)?")
todays_date = input("What is today's date(YYYYMMDD) ")

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
seconds = time.time()
local_time = time.ctime(seconds)


##Output file name variables###############################################
output_log = todays_date + "_OSS_version_" + oss_pack_version + ".log"
output_csv = todays_date + "_OSS_version_" + oss_pack_version + ".csv"


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
    data = update_type + pre_device + appliance_name() + post_device + pre_version + oss_pack_version + post_version
    return data

#Output log and file definitions###
def output_log_create():
    with open(output_log, "w") as output_log_file:
        output_log_file.write("###" + todays_date + "_OSS_version_" + oss_pack_version + "###\n")
        output_log_file.close

def init_log_data():
    init_log_data = local_time + " " + appliance_name() + " OSS pack upgrade initiated########\n"
    return init_log_data

def issue_log_data():
    issue_log_data = local_time + " " + appliance_name() + " encountered issues upgrading OSS pack.\n"
    return issue_log_data

def reach_log_data():
    reach_log_data = local_time + " " + appliance_name() + " is either unreachable or out of sync with Director\n"
    return reach_log_data

def prog_log_data():
    prog_log_data = local_time + " " + appliance_name() + " OSS pack upgrade COMPLETED\n"
    return prog_log_data

def output_csv_create():
    with open(output_csv, "w") as output_csv_file:
        output_csv_file.write("hostname;reachability;director_sync;update_status;oss_version\n")
        output_csv_file.close

def issue_csv_data():
    issue_csv_data = appliance_name() + ";" + appliance_ping() + ";" + appliance_sync() + ";issue upgrading OSS;issue upgrading OSS;\n"
    return issue_csv_data

def reach_csv_data():
    reach_csv_data = appliance_name() + ";" + appliance_ping() + ";" + appliance_sync() + ";unreachable or out of sync;unreachable or out of sync;\n"
    return reach_csv_data

def prog_csv_data():
    prog_csv_data = appliance_name() + ";" + appliance_ping() + ";" + appliance_sync() + ";COMPLETED;" + oss_pack_version + "\n"
    return prog_csv_data


#Upgrade OSS pack on all devices ######################
print('##### GET all device status and upgrade identified batch#####')
appliance_detail_response()
output_log_create()
output_csv_create()
if appliance_detail_response().status_code == 200:
    with open(output_log, "a+") as output_log_file, open(output_csv, "a+") as output_csv_file:
        for appliance in appliance_list():
                if reach_status not in appliance_ping() and sync_status in appliance_sync():
                    oss_pack_post = requests.post((https + director_ip + oss_pack_url), headers=headers, data = data(), verify=False, auth=auth)
                    if oss_pack_post.status_code == 201:
                        print(init_log_data())
                        output_log_file.write(init_log_data())
                    else:
                        print(init_log_data())
                        output_log_file.write(init_log_data())
                        print(issue_log_data())
                        output_log_file.write(issue_log_data())
                        output_csv_file.write(issue_csv_data())
                else:
                    print(init_log_data)
                    output_log_file.write(init_log_data())
                    print(reach_log_data()) 
                    output_log_file.write(reach_log_data())
                    output_csv_file.write(reach_csv_data())
else:
    print(upass_message)


#Check upgrade status######################
print('##### GET post upgrade details #####') 
appliance_detail_response()
if appliance_detail_response().status_code == 200:
    with open(output_log, "a+") as output_log_file, open(output_csv, "a+") as output_csv_file:
        for appliance in appliance_list():
            if reach_status not in appliance_ping() and sync_status in appliance_sync() and oss_pack_version in appliance_oss():
                print(prog_log_data())
                output_log_file.write(prog_log_data())
                output_csv_file.write(prog_csv_data())
            elif reach_status not in appliance_ping() and sync_status in appliance_sync() and oss_pack_version not in appliance_oss():
                appliance_detail_response()
                if reach_status not in appliance_ping() and sync_status in appliance_sync() and oss_pack_version in appliance_oss():
                    output_log_file.write(prog_log_data())
                    output_csv_file.write(prog_csv_data())
            else:
                output_log_file.write(reach_log_data())
                output_csv_file.write(reach_csv_data())
                print(issue_log_data())
                output_log_file.write(issue_log_data())
            
















    



