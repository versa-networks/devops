import json
import requests
import urllib3
import getpass
import csv
import sys
import time
import re
import os, glob
import jinja2


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

director_user_variable_print = '''
################################################
# Please enter the following SDWAN / Director  #
# environment information.                     #
################################################
'''

org_check_print = '''
################################################
# !! ORGANIZATION DOES NOT EXIST ON VERSA  !!  #
# !! DIRECTOR. PLEASE CHECK ENSURE CORRECT !!  #
# !! ORG NAME WAS ENTERED                  !!  #
################################################
'''

director_bad_cred_print = '''
################################################
# !! PLEASE CHECK DIRECTOR CREDENTIALS      !! #
# !! AND TRY AGAIN                          !! #
################################################
'''

director_connect = '''
################################################
# !! PLEASE CHECK DIRECTOR CONNECTIVITY    !!  #
# !! AND TRY AGAIN                         !!  #
################################################
'''

trans_vr_print = '''
################################################
Available SD-WAN VRs are listed below:         
------------------------------------------------
'''

lan_vr_print = '''
################################################
Available SD-WAN VRs are listed below:         
------------------------------------------------
'''

def else_print(response):
    else_print = (local_time() + " - # Response Code:  " + str(response.status_code) + " - " + str(response.content) + "\n")
    return else_print

####################Director user input variables####################

print_statement(director_user_variable_print)

csv_batch_file = input("Please enter the exact name of your csv batch file: ")
directorURL = input("Please enter the Director URL: ") 
directorTenant = input("Please enter the name of your Director Tenant: ")
directorClientID = input("Please enter the Director client_id: ") 
directorClientSecret = input("Please enter the Director client_secret: ") 
directorUserName = input("Please enter your Director Username: ")
directorPassword = getpass.getpass(prompt = "Please enter your Director Password: ")

#Batch directory (created during Concerto script)
batch_dir_compile = re.compile(r"^([^.]*)*")
batch_dir = re.search(batch_dir_compile, csv_batch_file).group(0)
batch_dir_path = batch_dir + "/"

####################API call url variables####################

#shared#
https = "https://"

#director
oauthURL = directorURL + ':9182/auth/token'
org_check_string = ':9183/vnms/organization/orgs?offset=0&limit=25'
dev_temp_url = directorURL + ':9183/api/config/devices/template/'
vnms_url = directorURL + ':9183/vnms/template/applyTemplate/'
vnms_task_url = directorURL + ':9183/vnms/tasks/task/'
#post_test_url = directorURL + ':9183/versa/ncs-services/api/operational/devices/device/'


interfaces_string = '/config/interfaces'
org_orgs_string = '/config/orgs/org/'
org_deep_string = '/config/orgs/org?deep'
org_services_string = '/config/orgs/org-services/'
traffic_id_string = '/traffic-identification/using'
routing_instance_string = '/config/routing-instances/routing-instance/'
routing_inst_int_string = '/interfaces'
ipsec_vpn_string = '/ipsec/vpn-profile/'
monitor_string = '/config/monitor'
bgp_string = '/protocols/bgp/rti-bgp/'
bgp_group_string = '/group'
static_string = '/routing-options/static'
redist_string = '/policy-options/redistribution-policy'
commit_devices_string = "/devices"
deep_string = '?deep=true'
#ping_test_string = '/live-status/diagnostics/ping'

bgp_instance_base = int(3000) + int(12) #may increase to 15 in future version.  Source velocity template
tvi_interfaces = ["tvi-15/1989", "tvi-15/1990", "tvi-15/1991", "tvi-15/1992", "tvi-15/1993"]
                        
####################Create log file for batch####################
with open(batch_dir_path + csv_batch_file + "_director.log", "w+") as LogFile:
    LogFile.write(local_time() + " - #### BEGIN LOG - " + csv_batch_file + " ####\n")
    LogFile.close()

def LogFile_write(log_statement):
    with open(batch_dir_path + csv_batch_file + "_director.log", "a+") as LogFile:
        LogFile.write(log_statement)
        LogFile.close()

####################Convert csv batch file to json and make callable variables####################
jsonFile = batch_dir_path + csv_batch_file + ".json"

def csv_to_json_vars(csvFilePath, jsonFilePath):
    jsonArray = []
    with open(csvFilePath, encoding="utf-8") as csvFile:
        csvReader = csv.DictReader(csvFile)
        for row in csvReader:
            jsonArray.append(row)
    with open(jsonFilePath, "w", encoding="utf-8") as jsonFile:
        jsonString = json.dumps(jsonArray, indent=4)
        jsonFile.write(jsonString)
        jsonFile.close
    with open(jsonFilePath, "r") as jsonFile:
        variables = json.load(jsonFile)
        jsonFile.close()
        return variables


####################Concerto Credentials check and Oauth Token####################


def directorTokenApi(url, call_headers, postData):
    try:
        post_response = requests.post((url), headers=call_headers, verify=False, data=postData, timeout=10)
        post_response.close()
        if re.match('2\d\d', str(post_response.status_code)):
            post_response_json = post_response.json()
            #print(json.dumps(post_response_json, indent=4))
            print("\n" + local_time() + " - # Successfull login to Director and recieved Oauth Access Token\n ")
            LogFile_write("\n" + local_time() + " - # Successfull login to Director and recieved Oauth Access Token\n ")
            return post_response_json
        else:
            print(else_print(post_response))
            LogFile_write(else_print(post_response))
            sys.exit(print_statement(director_bad_cred_print))
    except (requests.exceptions.Timeout, requests.ConnectionError):
        sys.exit(print_statement(director_connect))

####################Director Access Token####################
oauthData = ('{"client_id": "' + directorClientID + '","client_secret": "' + directorClientSecret +
              '","grant_type": "password","password": "' + directorPassword + '","scope": "global","username": "'
                + directorUserName+ '"}')

with open(batch_dir_path + "director_accessToken.txt", "w") as accessTokenFile:
    accessTokenFile.write(directorTokenApi(https + oauthURL, json_headers, oauthData)["access_token"])
accessTokenFile.close

with open(batch_dir_path + "director_accessToken.txt", "r") as accessTokenFile:   
    transaction_headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + str(accessTokenFile.read())
        }
accessTokenFile.close()


####################Director API call Definitions (POST, PATCH, GET)####################

director_data_error = '''
################################################
# !! DATA ENTERED FOR THE PREVIOUS STEP    !!  #
# !! MAY HAVE BEEN INCORRECT. PLEASE       !!  #
# !! RE-START THE SCRIPT.                  !!  #
################################################
'''

#Director Post API defenition#
def directorPostApi(url, call_headers, postData, config_item, template_name):
    try:
        post_response = requests.post((url), headers=call_headers, verify=False, data=postData, timeout=10)
        post_response.close()
        if re.match('2\d\d', str(post_response.status_code)):
            print(local_time() + " - # Reponse Code: " + str(post_response.status_code) + 
                  " - " + config_item + "created successfully for " + template_name + "\n")
            LogFile_write(local_time() + " - # Reponse Code: " + str(post_response.status_code) + 
                          " - " + config_item + "created successfully for " + template_name + "\n")
        elif re.match('4\d\d', str(post_response.status_code)):
            post_response_json = post_response.json()
            for error in post_response_json["errors"]["error"]:
                error_info = error["error-tag"]
                print(local_time() + " - # Reponse Code: " + str(post_response.status_code) + 
                  " - " + config_item + " - " + template_name + " - "  + error_info + "\n")
                LogFile_write(local_time() + " - # Reponse Code: " + str(post_response.status_code) + 
                  " - " + config_item + " - " + template_name + " - "  + error_info + "\n")
                print(else_print(post_response))
                LogFile_write(else_print(post_response))
            return error_info
            pass
        else:
            print(else_print(post_response))
            LogFile_write(else_print(post_response))
            pass
    except (requests.exceptions.Timeout, requests.ConnectionError):
        sys.exit(print_statement(director_connect))

def directorPatchApi(url, call_headers, patchData, config_item, template_name):
    try:
        patch_response = requests.patch((url), headers=call_headers, verify=False, data=patchData, timeout=10)
        patch_response.close()
        if re.match('2\d\d', str(patch_response.status_code)):
            print(local_time() + " - # Reponse Code: " + str(patch_response.status_code) + 
                  " - " + config_item + "created successfully for " + template_name + "\n")
            LogFile_write(local_time() + " - # Reponse Code: " + str(patch_response.status_code) + 
                          " - " + config_item + "created successfully for " + template_name + "\n")
        elif re.match('4\d\d', str(patch_response.status_code)):
            print(else_print(patch_response))
            LogFile_write(else_print(patch_response))
            pass
        else:
            print(else_print(patch_response))
            LogFile_write(else_print(patch_response))
            pass
    except (requests.exceptions.Timeout, requests.ConnectionError):
        sys.exit(print_statement(director_connect))

def directorPutApi(url, call_headers, putData, config_item, template_name):
    try:
        put_response = requests.put((url), headers=call_headers, verify=False, data=putData, timeout=10)
        put_response.close()
        if re.match('2\d\d', str(put_response.status_code)):
            print(local_time() + " - # Reponse Code: " + str(put_response.status_code) + 
                  " - " + config_item + "created successfully for " + template_name + "\n")
            LogFile_write(local_time() + " - # Reponse Code: " + str(put_response.status_code) + 
                          " - " + config_item + "created successfully for " + template_name + "\n")
        else:
            print(else_print(put_response))
            LogFile_write(else_print(put_response))
    except (requests.exceptions.Timeout, requests.ConnectionError):
        sys.exit(print_statement(director_connect))


def director_get_api(url,oauthHeader):
    try:
        get_response = requests.get((url), headers=oauthHeader, verify=False, timeout=10)
        get_response.close()
        if re.match('2\d\d', str(get_response.status_code)):
            get_response_json = get_response.json()
            #print(json.dumps(get_response_json, indent=4))
            return get_response_json
        else:
            print(else_print(get_response))
            LogFile_write(else_print(get_response))
    except (requests.exceptions.Timeout, requests.ConnectionError):
        sys.exit(print_statement(director_connect))

def commit_task_progress (config_item, post_task_id, task_status):
    task_progress = (local_time() + " - # " + config_item + template_name + " - " + "Task ID:" + post_task_id + " - " + task_status)
    return task_progress


def commitPostApi(url, call_headers, postData, config_item, template_name):
    try:
        post_response = requests.post((url), headers=call_headers, verify=False, data=postData, timeout=10)
        post_response.close()
        if re.match('2\d\d', str(post_response.status_code)):
            post_response_json = post_response.json()
            #print(json.dumps(post_response_json, indent=4))
            post_task_id = post_response_json["versanms.templateResponse"]["taskId"]
            post_message = post_response_json["versanms.templateResponse"]["message"]
            task_start = (local_time() + " - # Reponse Code: " + str(post_response.status_code) + 
                          " - " + config_item + template_name + " - " + post_message + " " + " Task ID: " + post_task_id + "\n")
            print(task_start)
            LogFile_write(task_start)
            chars = "|/-\\"
            i = 0
            task_status = director_get_api(https + vnms_task_url + post_task_id,transaction_headers)["versa-tasks.task"]["versa-tasks.task-status"]
            print(commit_task_progress (config_item, post_task_id, task_status))
            while task_status != "COMPLETED":
                task_status = director_get_api(https + vnms_task_url + post_task_id,transaction_headers)["versa-tasks.task"]["versa-tasks.task-status"]
                if task_status == "FAILED":
                    commit_status = commit_task_progress (config_item, post_task_id, task_status)
                    for get in director_get_api(https + vnms_task_url + post_task_id,transaction_headers)["versa-tasks.task"]["versa-tasks.progressmessages"]["versa-tasks.progressmessage"]:
                        task_fail = get["versa-tasks.message"]
                        print("\n" + str(commit_status) + "-" + str(task_fail))
                        LogFile_write(str(commit_status) + "-" + str(task_fail) + "\n")
                    print("\n")
                    break
                elif task_status != "COMPLETED":
                    sys.stdout.write('\r' + "Task ID: " + post_task_id + " - " + task_status + " " + chars[i])
                    sys.stdout.flush()
                    time.sleep(0.001)
                    i = (i + 1) % len(chars)
                    #print(print_progress(config_item, post_task_id))
                    #print(str(commit_task_progress (config_item, post_task_id, task_status)))
                elif task_status == "COMPLETED":
                    print("\n" + str(commit_task_progress (config_item, post_task_id, task_status)) + "\n")
                    LogFile_write(commit_task_progress (config_item, post_task_id, task_status) + "\n")
            #return task_status
        else:
            print(else_print(post_response))
            LogFile_write(else_print(post_response))
    except (requests.exceptions.Timeout, requests.ConnectionError):
        sys.exit(print_statement(director_connect))

def director_int_check (https,device_name, oauthHeader):
    try:
        get_response = requests.get((https + interface_status_url), headers=oauthHeader, verify=False, timeout=10)
        get_response.close()
        if re.match('2\d\d', str(get_response.status_code)):
            get_response_json = get_response.json()
            #print(json.dumps(get_response_json, indent=4))
            for interface_status in get_response_json["collection"]["interfaces:brief"]:
                if "tvi-15" in str(interface_status["name"]) and "vrf" in interface_status:
                    oper_status = interface_status["if-oper-status"]
                    admin_status = interface_status["if-admin-status"]
                    interface_vrf = interface_status["vrf"]
                    interface_status_print = local_time() + " -# " + device_name + " - SSE Site-to-Site tunnel for LAN VR: " + interface_vrf + " - " + str(interface_status["name"]) + " - " + oper_status + "," + admin_status + "\n"
                    print_statement(interface_status_print)
                    LogFile_write(interface_status_print)
        else:
            print(else_print(get_response))
            LogFile_write(else_print(get_response))
            pass
    except (requests.exceptions.Timeout, requests.ConnectionError):
        sys.exit(print_statement(director_connect))


####################check director connectivity and if org exists on director####################
def org_check():
    org_list = director_get_api(https + directorURL + org_check_string, transaction_headers)["organizations"]
    with open(batch_dir_path + csv_batch_file + "_orgs.txt", "w") as orgFile:
        for org in org_list:
            if directorTenant == org["name"]:
                    org_check = "exists"
                    org_uuid = org["uuid"]
                    orgFile.write(org_uuid)
                    return org_check
            else:
                pass
    orgFile.close()

####################Director lookup files####################
def dir_trans_vr_json ():
    with open(batch_dir_path + "dir_trans_vr.json", "w", encoding ="utf-8") as jsonFile:
        for org in director_get_api(https + dev_temp_url + device_template + org_deep_string,
                                     transaction_headers)["org"]:
            if org["name"] == directorTenant:
                instances_list = org["available-routing-instances"]
                instances_list_json = json.dumps(instances_list, indent = 4)
                jsonFile.write(instances_list_json)
                jsonFile.close()

def dir_trans_vr_json_print ():
    with open(batch_dir_path + "dir_trans_vr.json", "r", encoding="utf-8") as jsonFile:
        instances_list = json.loads(jsonFile.read())
        for instance in instances_list:
            print(instance)
        print("\n")

def concerto_sse_json (device_name, tunnel_name_ip):
    with open(batch_dir_path + device_name + "_" + tunnel_name_ip + "_SSE_config.json", "r") as sseJsonFile:
        concerto_sse_json = json.loads(sseJsonFile.read())
        return concerto_sse_json

def lan_instance_json():
    with open(batch_dir_path + template_name + "_" + device_name + "_" + tunnel_name_ip + "_routing_inst.json", "w", encoding="utf-8") as routInstFile:
        routInstFile.write(json.dumps(director_get_api(https + dev_temp_url + device_template + routing_instance_string + lan_vr + "?deep=true", 
                                                       transaction_headers), indent=4))
        routInstFile.close()

####################TVI interface to org limits function####################
#performed after checking interface existence
def tvi_org_limits ():
    directorPatchApi(https + dev_temp_url + device_template + org_orgs_string + directorTenant + traffic_id_string,
                     transaction_headers, tvi_limits_data, config_item = "tvi interface to org limits  ", template_name= template_name)


####################Jinja2 Template for tunnel data####################
def Director_S2S_j2(vpn_profile_name, trans_vr, lan_vr, sdwan_id_value, sdwan_id_type,sdwan_int_ip,shared_key, vcg_id_type, vcg_id_value, ipsec_rekey,
                    ipsec_hello, ipsec_transform, ipsec_pfs, ike_version, ike_lifetime, dpdt, ike_transform, dh_group, vcg_public_ip, tvi_interface):
    templateLoader = jinja2.FileSystemLoader(searchpath="./")
    templateEnv = jinja2.Environment(loader=templateLoader)
    TEMPLATE_FILE = "dir_vpn_profile.j2"
    template = templateEnv.get_template(TEMPLATE_FILE)
    outputText = template.render(vpn_profile_name = vpn_profile_name, trans_vr=trans_vr, lan_vr=lan_vr, sdwan_id_value=sdwan_id_value,
                                 sdwan_id_type=sdwan_id_type, shared_key=shared_key, vcg_id_type=vcg_id_type, vcg_id_value=vcg_id_value,
                                 ipsec_rekey=ipsec_rekey, ipsec_hello=ipsec_hello, ipsec_transform=ipsec_transform,
                                 ipsec_pfs=ipsec_pfs, ike_version=ike_version, ike_lifetime=ike_lifetime, dpdt=dpdt, ike_transform=ike_transform,
                                 dh_group=dh_group, vcg_public_ip=vcg_public_ip,sdwan_int_ip=sdwan_int_ip, tvi_interface=tvi_interface)
    #print(outputText)
    return outputText

####################Jinja2 Templates for BGP data####################

#bgp data for sites where bgp exists and peer goup will be added
def Director_BGP_group_j2(bgp_group_name, sdwan_tunnel_ip, concerto_tunnel_ip, vcg_bgp_asn, sdwan_bgp_asn, bgp_password):
    templateLoader = jinja2.FileSystemLoader(searchpath="./")
    templateEnv = jinja2.Environment(loader=templateLoader)
    TEMPLATE_FILE = "dir_bgp_group_config.j2"
    template = templateEnv.get_template(TEMPLATE_FILE)
    outputText = template.render(bgp_group_name=bgp_group_name, sdwan_tunnel_ip=sdwan_tunnel_ip, concerto_tunnel_ip=concerto_tunnel_ip, 
                                 vcg_bgp_asn=vcg_bgp_asn, sdwan_bgp_asn=sdwan_bgp_asn, bgp_password=bgp_password)
    #print(outputText)
    return outputText

#bgp data for sites where bgp does not exist and bgp will be added
def Director_BGP_proto_j2(bgp_instance, bgp_group_name, sdwan_tunnel_ip, concerto_tunnel_ip, vcg_bgp_asn, sdwan_bgp_asn, bgp_password):
    templateLoader = jinja2.FileSystemLoader(searchpath="./")
    templateEnv = jinja2.Environment(loader=templateLoader)
    TEMPLATE_FILE = "dir_bgp_proto_config.j2"
    template = templateEnv.get_template(TEMPLATE_FILE)
    outputText = template.render(bgp_instance=bgp_instance, bgp_group_name=bgp_group_name, sdwan_tunnel_ip=sdwan_tunnel_ip, concerto_tunnel_ip=concerto_tunnel_ip, 
                                 vcg_bgp_asn=vcg_bgp_asn, sdwan_bgp_asn=sdwan_bgp_asn, bgp_password=bgp_password)
    #print(outputText)
    return outputText

####################Confirm org entered exists####################
if not org_check():
    print_statement(org_check_print)

else:
    ####################Create tunnel / tvi interface / VPN Profile / BGP Peer on SD-WAN Device Template####################
    for variable in csv_to_json_vars(csv_batch_file, jsonFile):
        device_name = variable["device_name"]
        device_template = variable["device_template"]
        sdwan_int_ip = variable["sdwan_int_ip"]
        bgp_ip_compile = re.compile(r"^([^/]*)*")
        sdwan_tunnel_ip_raw = variable["sdwan_tunnel_ip"]
        sdwan_tunnel_ip = re.search(bgp_ip_compile, variable["sdwan_tunnel_ip"]).group(0)
        tunnel_name_ip = sdwan_tunnel_ip.replace(".", "-") #SD-WAN side
        saseGateway = concerto_sse_json(device_name, tunnel_name_ip)["attributes"]["tunnel"]["value"]["gatewayLinks"]["versaGateway"]
        #vpn_profile_name = str(saseGateway + "-Profile")
        concerto_tunnel_ip_raw = variable["vcg_tunnel_ip"]
        concerto_tunnel_ip = re.search(bgp_ip_compile, variable["vcg_tunnel_ip"]).group(0)
        monitor_name_ip = concerto_tunnel_ip.replace(".", "-")
        vpn_profile_name = str(saseGateway + "-Profile-" + str(monitor_name_ip))
        bgp_group_name = str(saseGateway) + "_Group"
        sdwan_bgp_asn = variable["sdwan_bgp_asn"]
        vcg_bgp_asn = variable["vcg_bgp_asn"]
        template_name = variable["device_template"]
        bgp_neighbor = str(concerto_sse_json(device_name, tunnel_name_ip)["attributes"]["tunnel"]["value"]["addressAndRouting"]["routingProtocol"]["neighbors"])
        static_routes = str(concerto_sse_json(device_name, tunnel_name_ip)["attributes"]["tunnel"]["value"]["addressAndRouting"]["staticRoutes"])

        ##Tunnel interface config, add to limits, and add to appropriate VR.
        for tvi_interface in tvi_interfaces:
            #tunnel_exist = ""
            interface_data = '{"tvi":[{"name":"' + tvi_interface + '","enable":true,"mode":"ipsec","mtu":"1336","type":"ipsec","unit":[{"name":"0","family":{"inet":{"address":[{"addr":"' + sdwan_tunnel_ip_raw + '"}]}},"enable":true}]}]}'
            print(local_time() + " - # Creating required tvi interface for " + template_name)
            tunnel_exist = (directorPostApi(https + dev_temp_url + device_template + interfaces_string, 
                                 transaction_headers, interface_data, config_item = "tvi interface ", 
                                 template_name= template_name))
            if tunnel_exist != "data-exists":
                tvi_limits_data = '{"using":["' + tvi_interface + '.0"]}'
                print(local_time() + " - # Adding tvi interface to org limits " + template_name)
                tvi_org_limits ()
                break
            elif tunnel_exist == "data-exists":
                tvi_confirm = ""
                tvi_confirm_print = f'''
                ##########################################################################################################################
                    SSE Tunnel already exists for Device: {device_name}, Device Template: {device_template}, TVI interface: {tvi_interface}
                    -------------------------------------------------------------------------------------------------------------------
                    Option 1: Update the configuration of an EXISTING SSE Tunnel                                                       
                    Option 2: Configure a NEW SSE Tunnel                                                                               
                ##########################################################################################################################
                '''
                while tvi_confirm != "1" or tvi_confirm != "2":
                    print_statement(tvi_confirm_print)
                    tvi_confirm = str(input("Please enter the SSE Tunnel option from above (1 or 2): "))
                    if tvi_confirm == "1" or tvi_confirm =="2":
                        break
                    break
                if tvi_confirm == "2":
                    pass
                elif tvi_confirm == "1":
                    tvi_limits_data = '{"using":["' + tvi_interface + '.0"]}'
                    print(local_time() + " - # Adding tvi interface to org limits " + template_name)
                    tvi_org_limits ()
                    break
                

        #User input variables based on device configured vrs
        dir_trans_vr_json ()
        with open(batch_dir_path + "dir_trans_vr.json", "r", encoding="utf-8") as trans_vr_jsonFile:
            print_statement(trans_vr_print)
            dir_trans_vr_json_print ()
            valid_trans_vr_list = json.loads(trans_vr_jsonFile.read())
            trans_vr = input("Please enter the tunnel WAN Transport VR for " + device_name + " from the list above: ")
            while trans_vr not in valid_trans_vr_list:
                trans_vr = input("Please enter the tunnel WAN Transport VR for " + device_name + " from the list above: ")
            print_statement(lan_vr_print)
            dir_trans_vr_json_print ()
            lan_vr = input("Please enter the LAN VR for " + device_name + " from the list above: ")
            while lan_vr not in valid_trans_vr_list:
                lan_vr = input("Please enter the LAN VR for " + device_name + " from the list above: ")
        
        lan_instance_json()
        print(local_time() + " - # Adding tvi interface to LAN VR " + template_name)
        vr_int_data = '{"routing-instance":{"interfaces":["' + tvi_interface + '.0"]}}'
        directorPatchApi(https + dev_temp_url + device_template + routing_instance_string + lan_vr, 
                         transaction_headers, vr_int_data, config_item = "tvi interface LAN VR  ", template_name= template_name)



        ##VPN profile from SSE configured tunnel data

        #Identity variables from SSE config file
        identity = concerto_sse_json(device_name, tunnel_name_ip)["attributes"]["tunnel"]["value"]["ipsec"]["authentication"]["psk"]
        sdwan_id_type = "fqdn"
        sdwan_id_value = identity["remote"]["identityValue"]
        vcg_id_type = "fqdn"
        vcg_id_value = identity["local"]["identityValue"]
        shared_key = identity["local"]["shareKey"]

        #IPSEC / IKE variables from SSE config file
        ipsec_ike = concerto_sse_json(device_name, tunnel_name_ip)["attributes"]["tunnel"]["value"]["ipsec"]

        #IPSEC
        ipsec_rekey = str(ipsec_ike["ipsecRekeyTime"]["value"])
        ipsec_transform = ipsec_ike["ipsecTransform"]
        ipsec_pfs = ipsec_ike["ipsecPfsGroup"]
        ipsec_hello = str(ipsec_ike["ipsecHelloInterval"])

        #IKE
        ike_version = ipsec_ike["ikeVersion"]
        ike_lifetime = str(ipsec_ike["ikeRekeyTime"]["value"])
        dpdt = str(ipsec_ike["ikeDPDTimeOut"])
        dh_group = ipsec_ike["ikeDHGroup"]
        ike_transform = ipsec_ike["ikeTransform"]

        #Tunnel Public IP from SSE config file
        with open(batch_dir_path + "sase_gateways.json", "r", encoding="utf-8") as saseGWfile:
          saseGW_dict = json.loads(saseGWfile.read())
          for saseGW in saseGW_dict["data"]:
              for gateway in saseGW["saseGatewayInfos"]:
                  if gateway["gatewayName"] == saseGateway:
                      for interface in gateway["wanInterfaces"]:
                          vcg_public_ip = interface["circuitIPv4PublicAddress"] ##### !!! in prod use sse gw fqdn !!! #####

        #SD-WAN VPN Profile configuration API
        print(local_time() + " - # Creating SSE VPN profile " + template_name)
        tunnel_data = Director_S2S_j2(vpn_profile_name, trans_vr, lan_vr, sdwan_id_value, sdwan_id_type,sdwan_int_ip,shared_key, vcg_id_type, vcg_id_value, ipsec_rekey,
                        ipsec_hello, ipsec_transform, ipsec_pfs, ike_version, ike_lifetime, dpdt, ike_transform, dh_group, vcg_public_ip, tvi_interface)
        with open(batch_dir_path + device_name + "_" + tunnel_name_ip + "_vpnprofile.config.json", "w") as sdwanConfigFile:
            sdwanConfigFile.write(tunnel_data)
            sdwanConfigFile.close()
        directorPutApi(https + dev_temp_url + device_template + org_services_string + directorTenant + ipsec_vpn_string + vpn_profile_name,
                        transaction_headers, tunnel_data, config_item = "vpn profile ", template_name = template_name)

        #SD-WAN BGP configuration API
        if bgp_neighbor == "[]":
            pass
        else:
            print(local_time() + " - # Configuring BGP to SSE GW for " + template_name)
            for neighbor in concerto_sse_json(device_name, tunnel_name_ip)["attributes"]["tunnel"]["value"]["addressAndRouting"]["routingProtocol"]["neighbors"]:
                bgp_password = neighbor["password"]
            with open(batch_dir_path + template_name + "_" + device_name + "_" + tunnel_name_ip + "_routing_inst.json", "r", encoding="utf-8") as routInstFile:
                lan_instance = json.loads(routInstFile.read())
                routInstFile.close()

                #if bgp exists and bgp instance-id assigned add group for SSE
                if "protocols" in lan_instance["routing-instance"] and "bgp" in lan_instance["routing-instance"]["protocols"]:
                    bgp_lan_data = Director_BGP_group_j2(bgp_group_name, sdwan_tunnel_ip, concerto_tunnel_ip, vcg_bgp_asn, sdwan_bgp_asn, bgp_password)
                    with open(batch_dir_path + device_name + "_" + tunnel_name_ip + "_bgp.config.json", "w") as sdwanBGPFile:
                        sdwanBGPFile.write(bgp_lan_data)
                        sdwanBGPFile.close()
                    for bgp in lan_instance["routing-instance"]["protocols"]["bgp"]["rti-bgp"]:
                        bgp_instance = bgp["instance-id"]
                        directorPatchApi(https + dev_temp_url + device_template + routing_instance_string + lan_vr + bgp_string + bgp_instance + bgp_group_string,
                              transaction_headers, bgp_lan_data, config_item = "BGP to SSE GW  ", template_name= template_name)

                #if bgp does not exist configure bgp
                else:
                    global_vrf_id = lan_instance["routing-instance"]["global-vrf-id"]
                    bgp_instance = str(bgp_instance_base + int(global_vrf_id))
                    bgp_lan_data = Director_BGP_proto_j2(bgp_instance, bgp_group_name, sdwan_tunnel_ip, concerto_tunnel_ip, vcg_bgp_asn, sdwan_bgp_asn, bgp_password)
                    directorPatchApi(https + dev_temp_url + device_template + routing_instance_string + lan_vr + "/protocols",
                              transaction_headers, bgp_lan_data, config_item = "BGP to SSE GW  ", template_name= template_name)
                
        #SD-WAN Static Default route configuration and ipsla monitor API
        if static_routes == "[]":
            pass
        else:
            print(local_time() + " - # Creating Static Default route and Monitor for " + template_name)
            monitor_data = '{"monitor":{"name":"SSE-Monitor-' + monitor_name_ip + '","interval":3,"threshold":"5","type":"icmp","ip-addresses":["' + concerto_tunnel_ip  + '"],"sub-type":"none","source-interface":"' + tvi_interface + '.0"}}'
            (directorPostApi(https + dev_temp_url + device_template + monitor_string, 
                            transaction_headers, monitor_data, config_item = "ipsla monitor ", template_name= template_name))
            static_route_data = '{"static":{"route": {"rti-static-route-list": [{"ip-prefix": "0.0.0.0/0","next-hop": "' + concerto_tunnel_ip + '","preference": "1","interface": "' + tvi_interface + '.0","tag": "64513","monitor": "SSE-Monitor-' + monitor_name_ip + '"}]}}}'
            directorPatchApi(https + dev_temp_url + device_template + routing_instance_string + lan_vr + static_string,
                          transaction_headers, static_route_data, config_item = "default route to SSE GW  ", template_name= template_name)
            lan_instance_json()
            with open(batch_dir_path + template_name + "_" + device_name + "_" + tunnel_name_ip + "_routing_inst.json", "r", encoding="utf-8") as routInstFile:
                lan_instance = json.load(routInstFile)
                routInstFile.close()
                redist_to_bgp = lan_instance["routing-instance"]["policy-options"]["redistribute-to-bgp"]
                redist_list_bgp = lan_instance["routing-instance"]["policy-options"]["redistribution-policy"]
                for list in redist_list_bgp:
                    if list["name"] == redist_to_bgp:
                        redist_list = list["term"]
                        static_sse_term = ({"term-name":"STATIC-SSE","match":{"protocol":"static","static-tag":"64513"},"action":{"set-origin":"igp","filter":"reject"}})
                        list["term"] = [static_sse_term] + redist_list
            #print(json.dumps(lan_instance, indent=4))
            redist_data = json.dumps(lan_instance)
            directorPutApi(https + dev_temp_url + device_template + routing_instance_string + lan_vr,
                             transaction_headers, redist_data, config_item = "reject default route redistribution to SD-WAN  ",
                             template_name= template_name)
        print("\n ###########################################################################################################\n")
    print("\n ###########################################################################################################\n")

    #Commit Device Template to Device with either overwrite or merge option
    commit_type = ""
    while commit_type != "1" or commit_type != "2":
        commit_type = str(input("To commit with OVERWRITE option enter 1 / To commit with MERGE option enter 2: "))
        if commit_type == "1":
            commit_mode = "overwrite"
        elif commit_type == "2":
            commit_mode = "merge"
        break
    for variable in csv_to_json_vars(csv_batch_file, jsonFile):
        device_name = variable["device_name"]
        template_name = variable["device_template"]
        concerto_tunnel_ip_raw = variable["vcg_tunnel_ip"]
        concerto_tunnel_ip = re.search(bgp_ip_compile, variable["vcg_tunnel_ip"]).group(0)
        sdwan_tunnel_ip_raw = variable["sdwan_tunnel_ip"]
        sdwan_tunnel_ip = re.search(bgp_ip_compile, variable["sdwan_tunnel_ip"]).group(0)
        commit_print = local_time() + " - # Commiting Device Template " + template_name + " to device " + device_name + " - " + commit_mode + "\n"
        print(commit_print)
        LogFile_write(commit_print)
        commit_data = '{"versanms.templateRequest":{"device-list":["' + str(device_name) + '"],"mode":"' + commit_mode + '"}}'
        commit_taskid = commitPostApi(https + vnms_url + device_template + commit_devices_string, 
                                          transaction_headers, commit_data, config_item = "Commit Device Template: ", 
                                          template_name= template_name)
        time.sleep(1)
        interface_status_url = (directorURL + ':9183/vnms/dashboard/appliance/' + device_name + '/live?command=interfaces%2Fbrief')
        director_int_check (https,device_name, transaction_headers)
        #for interface_status in director_get_api(https + interface_status_url,transaction_headers)["collection"]["interfaces:brief"]:
        #    if "tvi-15" in str(interface_status["name"]) and "vrf" in interface_status:
        #        oper_status = interface_status["if-oper-status"]
        #        admin_status = interface_status["if-admin-status"]
        #        interface_vrf = interface_status["vrf"]
        #        interface_status_print = local_time() + " -# " + device_name + " - SSE Site-to-Site tunnel for LAN VR: " + interface_vrf + " - " + str(interface_status["name"]) + " - " + oper_status + "," + admin_status + "\n"
        #        print_statement(interface_status_print)
        #        LogFile_write(interface_status_print)
        print("\n ###########################################################################################################\n")
txt_files = glob.glob(batch_dir_path + "*.txt")
for file in txt_files:
    os.remove(file)