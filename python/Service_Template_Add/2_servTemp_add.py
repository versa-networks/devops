import json
import requests
import urllib3
import getpass
import csv
import sys
import time
import os


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


#definition for timestamp on log messages
def local_time():
    seconds = time.time()
    local_time = time.ctime(seconds)
    return local_time

##Set the standard API request headers###################################
headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
}


##Print definition######################################################
def print_statement(print_variable):
    print(print_variable)

##User input varaibles###################################################
user_variable_print = '''
################################################
# Please enter the following environment       #
# information.                                 #
################################################
'''
servTemp_print = '''
############################################
# Please select the Service Template Type: #
# 1 = Stateful Firewall                    #
# 2 = NextGen Firewall                     #
# 3 = QOS                                  #
# 4 = General                              #
# 5 = Applicatoin Steering                 #
############################################
'''

def new_template():
    if servTemp_option == "1":
        new_template = "{'name': '" + servTemp_name + "', 'category': 'stateful-firewall', 'organization': '" + org_name + "', 'templateAssociationType': 'DEVICE_GROUP'}],"
        return new_template
    if servTemp_option == "2":
        new_template = "{'name': '" + servTemp_name + "', 'category': 'nextgen-firewall', 'organization': '" + org_name + "', 'templateAssociationType': 'DEVICE_GROUP'}],"
        return new_template
    if servTemp_option == "3":
        new_template = "{'name': '" + servTemp_name + "', 'category': 'class-of-service', 'organization': '" + org_name + "', 'templateAssociationType': 'DEVICE_GROUP'}],"
        return new_template
    elif servTemp_option == "4":
        new_template = "{'name': '" + servTemp_name + "', 'category': 'general', 'organization': '" + org_name + "', 'templateAssociationType': 'DEVICE_GROUP'}],"
        return new_template
    if servTemp_option == "5":
        new_template = "{'name': '" + servTemp_name + "', 'category': 'applications', 'organization': '" + org_name + "', 'templateAssociationType': 'DEVICE_GROUP'}],"
        return new_template


print_statement(user_variable_print)
   
director_ip = raw_input("What is the primary Director IP or Hostname?: ")
org_name = raw_input("What is the org name?: ")
servTemp_name = raw_input("What is the Service Template name? ")

print_statement(servTemp_print)
servTemp_option = raw_input("Please enter Template type (1-5): ")

csv_batch_file = raw_input("What is the full batch file name? ")
username = raw_input("What is your username?: ") 
passwrd = getpass.getpass()
auth = username,passwrd

##Batch file conversion from csv to json#################################
jsonFile = csv_batch_file + ".json"
csv_data = {}

with open(csv_batch_file, encoding="utf-8") as csvFile:
    csvReader = csv.DictReader(csvFile)
    for rows in csvReader:
        key = rows["device_group"]
        csv_data[key] = rows

with open(jsonFile, "w", encoding="utf-8") as jsonFile:
    jsonFile.write(json.dumps(csv_data))
    jsonFile.close

##Load json variables from converted json batch file#################################
with open(csv_batch_file + ".json", "r") as json_batch_file:
    variables = json.load(json_batch_file)
    json_batch_file.close()

with open(csv_batch_file + "_log.txt", "w") as batchLogFile:
    batchLogFile.write(csv_batch_file + "##" + local_time() + "## Log File")
    batchLogFile.close()


##API call url variables#####################################################
https = "https://"
device_group_string = ":9182/nextgen/deviceGroup/"
device_status_string = ":9182/vnms/template/deviceGroup/deviceStatus"
dg_post_string = ":9182/vnms/template/deviceGroup/deviceStatus"
device_commit_string = ":9182/vnms/template/applyTemplate/"
task_string = ":9182/vnms/tasks/task/"
org_check_string = ':9182/vnms/organization/orgs?offset=0&limit=25'


dg_post_url = https + director_ip + dg_post_string
org_check_url = https + director_ip + org_check_string

bad_upass = '''
        ################################################
        # !! PLEASE CHECK USERNAME/PASSWORD        !!  #
        # !! AND AND TRY AGAIN                     !!  #
        ################################################
        '''

director_connect = '''
        ################################################
        # !! PLEASE CHECK DIRECTOR CONNECTIVITY    !!  #
        # !! AND TRY AGAIN                         !!  #
        ################################################
        '''

def versa_get_api(url):
    try:
        get_response = requests.get((url), headers=headers, verify=False, auth=auth, timeout=10)
        get_response.close()
        if get_response.status_code == 200:
            get_response_json = get_response.json()
            #print(json.dumps(get_response_json, indent=4))
            return get_response_json
        else:
            sys.exit(print_statement(bad_upass))
    except (requests.exceptions.Timeout, requests.ConnectionError):
        sys.exit(print_statement(director_connect))


##check director connectivity and if user in put org exists on director##
org_check_print = '''
        ################################################
        # !! ORGANIZATION DOES NOT EXIST ON VERSA  !!  #
        # !! DIRECTOR. PLEASE CHECK ENSURE CORRECT !!  #
        # !! ORG NAME WAS ENTERED                  !!  #
        ################################################
        '''

script_begin = f'''
        ################################################
        # Running Script to update {servTemp_name}     #
        # on batch devices.                            #
        ################################################
        '''

script_complete = f'''
        ################################################
        # Script has completed. Please check logs for  #
        # addition of {servTemp_name} to Device Groups #
        # and commit on devices.                       #
        ################################################
        '''

def org_check():
    org_list = versa_get_api(org_check_url)["organizations"]
    for org in org_list:
        if org_name == org["name"]:
                org_check = "exists"
                print_statement(script_begin)
                return org_check
        else:
            pass


def versa_dg_get_api(url):
    try:
        get_response = requests.get((url), headers=headers, verify=False, auth=auth, timeout=10)
        get_response.close()
        if get_response.status_code == 200:
            print(local_time() + " - " + item + " - Running GET for currently configured Service Templates\n")
            batchLogFile.write(local_time() + " - " + item + " - Running GET for currently configured Service Templates\n")
            get_response_json = get_response.json()
            #print(json.dumps(get_response_json, indent=4))
            inv_name = "'inventory-name': " + str(get_response_json["inventory-name"]) + ","
            templateAssoc = str(get_response_json["template-association"])
            new_templateAssoc = "'template-association':" + templateAssoc.replace("]", ",") + new_template()
            dg_device_group = str("{'device-group': {'name': '" + item + "',") 
            dg_organization = str("'dg:organization': '" + org_name + "',")
            twofactor_auth = "'dg:enable-2factor-auth': '" + str(get_response_json["enable-2factor-auth"]) + "',"
            en_stag_url = "'dg:enable-staging-url': '" + str(get_response_json["enable-staging-url"]) + "',"
            conf_on_branch = "'dg:ca-config-on-branch-notification': '" + str(get_response_json["ca-config-on-branch-notification"]) + "',"
            post_stg_temp = "'dg:poststaging-template': '" + str(get_response_json["poststaging-template"]) + "'}}"
            print(local_time() + " - " + item + " - Adding new Servcie Template to Device Group PUT data\n")
            batchLogFile.write(local_time() + " - " + item + " - Adding new Servcie Template to Device Group PUT data\n")
            with open(item + "put_data.txt", "w") as putDataFile_txt:
                putData_raw = dg_device_group + dg_organization + twofactor_auth + conf_on_branch + en_stag_url + new_templateAssoc + inv_name + post_stg_temp
                putData_comma = putData_raw.replace("'", '"')
                putData_space = putData_comma.replace(" ", "")
                putDataFile_txt.write(putData_space)
                putDataFile_txt.close()
            with open(item + "put_data.json", "w") as putDataFile_json:
                putData_raw = dg_device_group + dg_organization + twofactor_auth + conf_on_branch + en_stag_url + new_templateAssoc + inv_name + post_stg_temp
                putData_comma = putData_raw.replace("'", '"')
                putDataFile_json.write(putData_comma)
                putDataFile_json.close()
        else:
            sys.exit(print_statement(bad_upass))
    except (requests.exceptions.Timeout, requests.ConnectionError):
        sys.exit(print_statement(director_connect))

def versa_dg_put_api(url):
    try:
        with open(item + "put_data.txt") as putDataFile_txt:
            put_data_raw = putDataFile_txt.read()
            put_response = requests.put((url), headers=headers, verify=False, data=put_data_raw, auth=auth, timeout=10)
            put_response.close()
            put_status_code = str(put_response.status_code)
            print(local_time() + " - " + item + " - Running PUT to add newly configured Service Templates\n")
            batchLogFile.write(local_time() + " - " + item + " - Running PUT to add newly configured Service Templates\n")
            if put_response.status_code == 200:
                print(local_time() + put_status_code + " - Service Template " + servTemp_name + " added to Device Group " + item + "\n")
                batchLogFile.write(local_time() + put_status_code + " - Service Template " + servTemp_name + " added to Device Group " + item + "\n")
                device_commit()
            elif put_response.status_code == 400:
                print(local_time() + put_status_code + " - Service Template " + servTemp_name + " either does not exist or is already configured in Device Group " + item + "\n")
                batchLogFile.write(local_time() + put_status_code + " - Service Template " + servTemp_name + " either does not exist or is already configured in Device Group " + item + "\n")
            else:
                sys.exit(print_statement(bad_upass))
            return put_status_code
    except (requests.exceptions.Timeout, requests.ConnectionError):
        sys.exit(print_statement(director_connect))

def versa_post_api(url,post_data):
    try:
        post_response = requests.post((url), headers=headers, verify=False, data=post_data, auth=auth, timeout=10)
        post_response.close()
        #print(post_response.status_code)
        if post_response.status_code == 200:
            post_response_json = post_response.json()
            #print(json.dumps(post_response_json, indent=4))
            return post_response_json
        else:
            sys.exit(print_statement(bad_upass))
    except (requests.exceptions.Timeout, requests.ConnectionError):
        sys.exit(print_statement(director_connect))

def device_commit():
    with open(item + "put_data.json") as putDataFile_json:
        dg_read = putDataFile_json.read()
        dg_variables = json.loads(dg_read)
        dg_name = dg_variables["device-group"]["name"]
        temp_name = dg_variables["device-group"]["dg:poststaging-template"]
        sync_check_data = '{"versanms.deviceGroups":{"deviceGroupDataList":[{"name":"' + dg_name + '"}],"template-name":"' + temp_name + '"}}'
        print(local_time() + " - " + item + " - Checking device Director Sync Status\n")
        batchLogFile.write(local_time() + " - " + item + " - Checking device Director Sync Status\n")
        for response in versa_post_api(dg_post_url, sync_check_data)["versanms.deviceGroups"]["deviceGroupDataList"]:
            device_status = response["deviceDataList"]
            for device in device_status:
                device_name = device["name"]
                dir_sync = device["syncStatus"]
                commit_data = '{"versanms.templateRequest":{"device-list":["' + device_name + '"],"mode":"overwrite"}}'
                commit_url = https + director_ip + device_commit_string + temp_name + "/devices"
                if dir_sync == "IN_SYNC":
                    taskID = versa_post_api(commit_url, commit_data)["versanms.templateResponse"]["taskId"]
                    print(local_time() + " - " + item + " -  " + device_name +  " - Committing to Device - Director Task " + taskID + "\n")
                    batchLogFile.write(local_time() + " - " + item + " -  " + device_name +  " - Committing to Device - Director Task " + taskID + "\n")
                    task_url = https + director_ip + task_string + taskID + "?deep=true"
                    task_status = versa_get_api(task_url)["versa-tasks.task"]["versa-tasks.task-status"]
                    while task_status == "IN_PROGRESS":
                        task_status = versa_get_api(task_url)["versa-tasks.task"]["versa-tasks.task-status"]
                        print(local_time() + " - " + item + " - " + device_name +  " - Commit"  + " - " + taskID + " - " + task_status + "\n")
                        batchLogFile.write(local_time() + " - " + item + " -  " + device_name +  " - Commit"  + " - " + taskID + " - " + task_status + "\n")
                elif dir_sync != "IN_SYNC":
                    print(local_time() + " - " + device_name + " - configuraiton is either unreachable or not in sync with Director - !SKIPPING DEVIVCE!\n")
                    batchLogFile.write(local_time() + " - " + device_name + " - configuraiton is not in sync with Director - !SKIPPING DEVIVCE!\n")


#cleanup unecessary post script files###
def file_cleanup():
    os.remove(item + "put_data.json")
    os.remove(item + "put_data.txt")


if not org_check():
    print_statement(org_check_print)
else:
    with open(csv_batch_file + "_log.txt", "a+") as batchLogFile:    
        for item in variables:
            device_group_url = https + director_ip + device_group_string + item
            versa_dg_get_api(device_group_url)
            versa_dg_put_api(device_group_url)
            file_cleanup()
    batchLogFile.close()
print_statement(script_complete)
