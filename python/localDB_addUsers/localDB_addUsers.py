import requests
import json
import csv
import urllib3
import getpass
import time
import os


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

####User input varaibles###################################################
print("")
print("#################################")
print("#Enter the following information#")
print("#################################")
print("")
username = input("What is your username?: ") 
passwrd_user = getpass.getpass() 
auth = username,passwrd_user
upass_message = " Please check connectivity to director and  username/password and try again."
director_ip = input("What is the primary Director IP or Hostname?: ")
org_name = input("What is the Org name where the user should be added?: ")
csv_batch_file = input("What is the full name of the .csv Batch File?: ")

##User input for option selection (1-Service Template, 2-Device Template, 3-Device)
print("")
print("###################################")
print("Enter 1 to use Service Template")
print("Enter 2 to use Device Template")
print("Enter 3 to use Device (NOT RECOMMENDED)")
print("")
option_select_input = input("Please select an option (1-3): ")
print("")



##Set the standard API request headers###################################
headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
}

##URL Variables###########################################################
https = "https://"
create_service_template_string = ':9182/vnms/template/serviceTemplate'
create_device_user_string = ':9182/api/config/devices/device/'
create_template_user_string = ':9182/api/config/devices/template/'
create_user_org_string = '/config/orgs/org-services/'
create_user_user_string = '/user-identification/local-database/users'

##Set time def for print outputs###########################################
def local_time():
    seconds = time.time()
    local_time = time.ctime(seconds)
    return local_time

##Batch file conversion from csv to json#################################

jsonFile = csv_batch_file + ".json"

def csv_to_json(csvFile, jsonFile):
    jsonArray = []
    with open(csv_batch_file, encoding='utf-8') as csvf:
        csvReader = csv.DictReader(csvf)
        for row in csvReader:
            jsonArray.append(row)
    with open(jsonFile, "w", encoding='utf-8') as jsonf:
        jsonString = json.dumps(jsonArray, indent=4)
        jsonf.write(jsonString)

csv_to_json(csv_batch_file, jsonFile)

##Load json variables from converted json batch file#################################
with open(csv_batch_file + ".json", "r") as json_batch_file:
    variables = json.load(json_batch_file)
    json_batch_file.close()

##Set data structure to use with json variables for correct data format##############
data_begin = '{"user":{"name":"'
data_description = '","description":"'
data_groups = '","groups":["'
data_passwd = '"],"passwd":"'
data_first_name = '","first-name":"'
data_last_name = '","last-name":"'
data_email_address = '","email-address":"'
data_status = '","status":"'
data_password = '","password":"'
last_quote = '"'
data_end = '}}'

#user specific data definitions###
def add_username():
    add_username = item["name"]
    return add_username

def add_description():   
    add_description = item["description"]
    return add_description

def add_groups():    
    add_groups = item["groups"]
    return add_groups

def add_passwd():    
    add_passwd = item["passwd"]
    return add_passwd

def add_firstname():    
    add_firstname = item["first-name"]
    return add_firstname

def add_lastname():   
    add_lastname = item["last-name"]
    return add_lastname

def add_emailaddress():  
    add_emailaddress = item["email-address"]
    return add_emailaddress

def add_status():    
    add_status = item["status"]
    return add_status

def add_password():    
    add_password = item["password"]
    return add_password

##output log file create and update###############################################
output_log = csv_batch_file + "_add_user.log"

def output_log_create():
    with open(output_log, "w") as output_log_file:
        output_log_file.write("###" + csv_batch_file + "add user to local database log file###\n")
        output_log_file.close

def add_st_add_log_data():
    add_st_issue_log_data = local_time() + " Successfully created Service Template " + s_template_name + "\n"
    return add_st_add_log_data

def add_st_issue_log_data():
    add_st_issue_log_data = local_time() + " issues adding new Service Template " + s_template_name + "\n"
    return add_st_issue_log_data

def add_user_log_data():
    add_user_log_data = local_time() + " " + add_username() + " has been added to the local database\n"
    return add_user_log_data

def add_user_exist_log_data():
    add_user_log_data = local_time() + " " + add_username() + " already exists in the local database\n"
    return add_user_log_data

#cleanup unecessary post script files###
def file_cleanup():
    os.remove( csv_batch_file  + ".json")

##Add users to local database#######################
print("")
print("#############################")
print("#Add users to local database#")
print("#############################")
print("")
with open(output_log, "a+") as output_log_file:
    ##############################################################################################
    #########Option 1 Existing or New Service Template############################################
    ##############################################################################################
    if option_select_input == "1":
        s_template_exist = input("Update existing Service Template(y or n)?: ")
        if s_template_exist == "y" or s_template_exist == "Y" or s_template_exist == "yes":
            s_template_name = input("What is existing Service Template name?: ")
            print("")
        elif s_template_exist == "n" or s_template_exist == "N" or s_template_exist == "no":
            s_template_name = input("What is the new Service Template name?: ")
            print("")
            new_st_data = '{"versanms.templateData":{"category":"general","composite_or_partial":"partial","isDynamicTenantConfig":false,"name":"' + s_template_name + '","providerTenant":"' + org_name + '"}}'
            add_service_template = requests.post((https + director_ip + create_service_template_string), headers=headers, data=new_st_data, verify=False, auth=auth)
            if add_service_template.status_code == 201:
                print(add_st_add_log_data())
                output_log_file.write(add_st_add_log_data())
            else:
                print(add_st_issue_log_data())
                output_log_file.write(add_st_issue_log_data())
        for item in variables:
            data = data_begin + add_username() + data_description + add_description() + data_groups + add_groups() + data_passwd + add_passwd() + data_first_name + add_firstname() + data_last_name + add_lastname() + data_email_address + add_emailaddress() + data_status + add_status() + data_password + add_password() + last_quote + data_end
            add_user_response = requests.post((https + director_ip + create_template_user_string + s_template_name + create_user_org_string + org_name + create_user_user_string), headers=headers, data=data, verify=False, auth=auth)
            add_user_response.close()
            if add_user_response.status_code == 201:
                print(add_user_log_data())
                output_log_file.write(add_user_log_data())
            elif add_user_response.status_code == 409:
                print(add_user_exist_log_data())
                output_log_file.write(add_user_exist_log_data())
            else:
                print(upass_message)
                print(add_st_issue_log_data())
                output_log_file.write(add_st_issue_log_data())
    #########################################################################################
    #########Option 2 Update SASE Device Template############################################
    #########################################################################################
    elif option_select_input == "2":
        device_template_name = input("What is the Device Template Name?: ")
        for item in variables:
            data = data_begin + add_username() + data_description + add_description() + data_groups + add_groups() + data_passwd + add_passwd() + data_first_name + add_firstname() + data_last_name + add_lastname() + data_email_address + add_emailaddress() + data_status + add_status() + data_password + add_password() + last_quote + data_end
            add_user_response = requests.post((https + director_ip + create_device_user_string + device_template_name + create_user_org_string + org_name + create_user_user_string), headers=headers, data=data, verify=False, auth=auth)
            add_user_response.close()
            if add_user_response.status_code == 201:
                print(add_user_log_data())
                output_log_file.write(add_user_log_data())
            elif add_user_response.status_code == 409:
                print(add_user_exist_log_data())
                output_log_file.write(add_user_exist_log_data())
            else:
                print(upass_message)
    #########################################################################################
    #########Option 2 Update Devicee############################################
    #########################################################################################
    elif option_select_input == "3":
        print("!!!WARNING. THIS IS NOT A RECOMMENDED OPTION. CHANGES!!!!!!")
        print("!!!MADE DIRECTLY ON THE DEVICE CAN BE EASILY OVERWRITTEN!!!")
        device_name = input("What is the Device Name?: ")
        for item in variables:
            data = data_begin + add_username() + data_description + add_description() + data_groups + add_groups() + data_passwd + add_passwd() + data_first_name + add_firstname() + data_last_name + add_lastname() + data_email_address + add_emailaddress() + data_status + add_status() + data_password + add_password() + last_quote + data_end
            #print(data)
            #print(https + director_ip + create_user_string_api_string + device_name + create_user_string_org_string + org_name + create_user_string_user_string)
            add_user_response = requests.post((https + director_ip + create_device_user_string + device_name + create_user_org_string + org_name + create_user_user_string), headers=headers, data=data, verify=False, auth=auth)
            add_user_response.close()
            if add_user_response.status_code == 201:
                print(add_user_log_data())
                output_log_file.write(add_user_log_data())
            elif add_user_response.status_code == 409:
                print(add_user_exist_log_data())
                output_log_file.write(add_user_exist_log_data())
            else:
                print(upass_message)
    else:
        print("Please re-run the script and enter a valid option")

output_log_file.close

file_cleanup()
