import json
import requests
import urllib3
import getpass
import csv
import sys
import time
import re
from sseclient import SSEClient
import jinja2
import traceback
import os, glob
import shutil
import string
import secrets

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


#definition for timestamp on log messages
def local_time():
    seconds = time.time()
    local_time = time.ctime(seconds)
    return local_time

##Print definition######################################################
def print_statement(print_variable):
    print(print_variable)

##Print variables#######################################################
directory_abort_print = '''
################################################
# Script has been aborted due to existence     #
# of batch directory. If you wish to run the   #
# script, please rename the batch file to have #
# a new directory created                      #
################################################
'''

concerto_user_variable_print = '''
################################################
# Please enter the following SSE / Concerto    #
# environment information.                     #
################################################
'''

concerto_bad_cred_print = '''
################################################
# !! PLEASE CHECK CONCERTO CREDENTIALS      !! #
# !! AND TRY AGAIN                          !! #
################################################
'''

concerto_connect = '''
################################################
# !! PLEASE CHECK CONCERTO CONNECTIVITY    !!  #
# !! AND TRY AGAIN                         !!  #
################################################
'''

concerto_data_error = '''
################################################
# !! DATA ENTERED FOR THE PREVIOUS STEP    !!  #
# !! MAY HAVE BEEN INCORRECT. PLEASE       !!  #
# !! RE-START THE SCRIPT.                  !!  #
################################################
'''


#User Variable entry validation print and lists
#Validation list for Tenant, VPNName, and BGP import export policies based on api response.  Not included in this section.
def print_list(list):
    for item in list:
        print(item)
    print("\n------------------------------------------------\n")

sasegw_print = '''
################################################
Below are the SASE Gateways available.       
Please enter the desired Gateway Name from   
the list.                                    
------------------------------------------------
'''

vpnName_print = '''
################################################
Below are the customer VPNs available.       
Please enter the desired VPN Name from       
the list.                                    
------------------------------------------------
'''

bgp_policy_print = '''
################################################
Available BGP Policies listed below:         
------------------------------------------------
'''


valid_ike_transforms = ["3des-md5", "3des-sha1", "aes128-sha1", "aes128-md5", 
                        "aes256-sha1", "aes256-md5", "aes128-sha256", "aes256-sha256",
                        "aes128-sha384", "aes256-sha384", "aes128-sha512", "aes256-sha512",]

ike_transform_print = '''
################################################
Available Tranforms:                         
------------------------------------------------
'''

valid_ipsec_transforms = ["esp-aes128-sha1", "esp-3des-md5", "esp-3des-sha1", "esp-aes128-ctr-sha1",
                          "esp-aes128-ctr-xcbc", "esp-aes128-gcm", "esp-aes128-md5", "esp-aes128-sha256",
                          "esp-aes128-sha384", "esp-aes128-sha512", "esp-aes256-gcm", "esp-aes256-md5",
                          "esp-aes256-sha1", "esp-aes256-sha256", "esp-aes256-sha384", "esp-aes256-sha512",
                          "esp-null-md5"]

ipsec_transform_print = '''
################################################
Available Tranforms:                         
------------------------------------------------
'''

valid_ike_versions = ["v1", "v2", "v2-or-v1"]

valid_dh_groups = ["mod1", "mod2", "mod5", "mod14", "mod15",
                   "mod16", "mod19", "mod20", "mod21", 
                   "mod25", "mod26", "mod-none"]

DH_print = '''
################################################
Available DH Groups:                        
------------------------------------------------
'''

ipsec_auth_types = ["PSK", "Certificate"]

#PSK auto generate
alphabet = string.ascii_letters + string.digits# + string.punctuation
valid_punctuation = ''.join([c for c in alphabet if c not in ('\'', '"', '\\')])

# default IKE / IPSEC configuration

defaultIKEIPSec_print = '''
################################################
Default IKE and IPSec Parameters
################################################
ike_version = v2
ike_transform = aes256-sha256
ike_dh_group = mod19
ike_rekey_time = 28800
ike_dpdt_timeout = 30
ipsec_transform = esp-aes128-gcm
ipsec_dh_group = mod-none
ipsec_hello_interval= 10
ipsec_rekey_time = 28800
ipsec_auth_type = PSK
ipsec_auth_type_key = psk
local_identity_type = FQDN
remote_identity_type = FQDN                       
------------------------------------------------
'''

ike_version = "v2"
ike_transform = "aes256-sha256"
ike_dh_group = "mod19"
ike_rekey_time = "28800"
ike_dpdt_timeout = "30"
ipsec_transform = "esp-aes128-gcm"
ipsec_dh_group = "mod-none"
ipsec_hello_interval= "10"
ipsec_rekey_time = "28800"
ipsec_auth_type = "PSK"
ipsec_auth_type_key = "psk"
local_identity_type = "FQDN"
remote_identity_type = "FQDN"


##Initial User input varaibles###################################################

print_statement(concerto_user_variable_print)

csv_batch_file = input("Please enter the exact name of your csv batch file: ")
concertoURL = input("Please enter the Concerto URL: ") 
concertoTenant = input("Please enter the name of your Concerto Tenant: ")
concertoClientID = input("Please enter the Concerto client_id provided by Versa: ") 
concertoClientSecret = input("Please enter the Concerto client_secret provided by Versa: ") 
concertoUserName = input("Please enter your Concerto Username: ")
concertoPassword = getpass.getpass(prompt = "Please enter your Concerto Password: ")
print("\n")


##Check if batch file directory already exists
batch_dir_compile = re.compile(r"^([^.]*)*")
batch_dir = re.search(batch_dir_compile, csv_batch_file).group(0)
if os.path.exists(batch_dir):
    print("A directory for batch " + batch_dir + " already exists.")
    dir_overwrite = ""
    while dir_overwrite != "no" or dir_overwrite != "n":
        dir_overwrite = input("Would you like to continue (yes or no) (WARNING - EXISTING DIRECTORY WILL BE OVERWRITTEN)?: ")
        if dir_overwrite == "no" or dir_overwrite == "n":
            sys.exit(print_statement(directory_abort_print))
        if dir_overwrite != "yes" or dir_overwrite != "y":
            shutil.rmtree(batch_dir)
            break

batch_dir_path = batch_dir + "/"

##Create batch directory and log file
if not os.path.exists(batch_dir):
    os.makedirs(batch_dir)

with open(batch_dir_path + csv_batch_file + "_concerto.log", "w") as LogFile:
    LogFile.write(local_time() + " - #### BEGIN LOG - " + csv_batch_file + " ####\n")
    LogFile.close()

def LogFile_write(log_statement):
    with open(batch_dir_path + csv_batch_file + "_concerto.log", "a+") as LogFile:
        LogFile.write(log_statement)
        LogFile.close()

##API call url variables#####################################################

#Set the standard API  application/json request headers
json_headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
}
#shared#
https = "https://"

#concerto#
oauthURL = concertoURL + '/portalapi/v1/auth/token'
concertoTenantURL = concertoURL + '/portalapi/v1/tenants/tenant/name/' + concertoTenant
concerto_v1_URL = concertoURL + '/portalapi/v1/tenants/'
sase_gw_string = '/regions/sasegateways'


##Convert csv batch file to json and make callable variables
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

#Concerto Credentials check and Oauth Token######################################

def concertoTokenApi(url, call_headers, postData):
    try:
        post_response = requests.post((url), headers=call_headers, verify=False, data=postData, timeout=10)
        post_response.close()
        post_response_json = post_response.json()
        if re.match('2\d\d', str(post_response.status_code)):
            #print(json.dumps(post_response_json, indent=4))
            print("\n# Successfull login to Concerto and recieved Oauth Access Token ")
            LogFile_write(local_time() + " - # Successfull login to Concerto and recieved Oauth Access Token\n")
            return post_response_json
        else:
            print(local_time() + " - # Response Code:  " + str(post_response.status_code) + "-" + str(post_response_json["message"])  + "\n")
            LogFile_write(local_time() + " - # " + str(post_response.status_code) + "-" + str(post_response_json["message"])  + "\n")
            sys.exit(print_statement(concerto_bad_cred_print))
    except (requests.exceptions.Timeout, requests.ConnectionError):
        sys.exit(print_statement(concerto_connect))

##Concerto Access Token##
oauthData = ('{"client_id": "' + concertoClientID + '","client_secret": "' + concertoClientSecret + '","grant_type": "password","password": "'
              + concertoPassword + '","scope": "global","username": "' + concertoUserName+ '"}')

with open(batch_dir_path + "concerto_accessToken.txt", "w") as accessTokenFile:
    accessTokenFile.write(concertoTokenApi(https + oauthURL, json_headers, oauthData)["access_token"])
accessTokenFile.close

with open(batch_dir_path + "concerto_accessToken.txt", "r") as accessTokenFile:   
    transaction_headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + str(accessTokenFile.read())
        }
accessTokenFile.close()


##Concerto API call Definitions (POST, GET, PUT)###################################
#Concerto Post API defenition#
def concertoPostApi(url, call_headers, postData, print_data):
    try:
        post_response = requests.post((url), headers=call_headers, verify=False, data=postData, timeout=10)
        post_response.close()
        if re.match('2\d\d', str(post_response.status_code)):
            post_response_json = post_response.json()
            #print(json.dumps(post_response_json, indent=4))
            print(print_data)
            LogFile_write(print_data)
            return post_response_json
        elif post_response.status_code == 400:
            LogFile_write(local_time() + " - # Reponse Code: " + str(post_response.status_code) + " - Existing Concerto configuration present\n")
            print(local_time() + " - # Reponse Code: " + str(post_response.status_code) + " - Existing Concerto configuration present\n")
        else:
            print(local_time() + " - # Reponse Code: " + str(post_response.status_code) + "\n")
            LogFile_write(local_time() + " - # Reponse Code: " + str(post_response.status_code) + "\n")
            if str(post_response_json["message"]):
              print(local_time() + " - # Message: " + str(post_response_json["message"]) + "\n")
              LogFile_write(local_time() + " - # Message: " + str(post_response_json["message"]) + "\n")
            else:
              traceback.print_exception(*sys.exc_info())
              sys.exit(print_statement(concerto_data_error))
    except (requests.exceptions.Timeout, requests.ConnectionError):
        sys.exit(print_statement(concerto_connect))


#Concerto GET API defenition#
def concerto_get_api(url,oauthHeader):
    try:
        get_response = requests.get((url), headers=oauthHeader, verify=False, timeout=10)
        get_response.close()
        if re.match('2\d\d', str(get_response.status_code)):
            get_response_json = get_response.json()
            #print(json.dumps(get_response_json, indent=4))
            return get_response_json
        else:
            print(local_time() + " - # " + str(get_response.status_code) + "-" + str(get_response_json["message"])  + "\n")
            LogFile_write(local_time() + " - # " + str(get_response.status_code) + "-" + str(get_response_json["message"])  + "\n")
            sys.exit(print_statement(concerto_data_error))
    except (requests.exceptions.Timeout, requests.ConnectionError):
        sys.exit(print_statement(concerto_connect))

#Concerto PUT API defenition#
def concertoPutApi(url, call_headers, putData):
    try:
        put_response = requests.put((url), headers=call_headers, verify=False, data=putData, timeout=10)
        put_response.close()
        if re.match('2\d\d', str(put_response.status_code)):
            put_response_json = put_response.json()
            #print(json.dumps(put_response_json, indent=4))
            return put_response_json
        else:
            print(local_time() + " - # " + str(put_response.status_code) + "-" + str(put_response_json["message"])  + "\n")
            LogFile_write(local_time() + " - # " + str(put_response.status_code) + "-" + str(put_response_json["message"])  + "\n")
            sys.exit(print_statement(concerto_data_error))
    except (requests.exceptions.Timeout, requests.ConnectionError):
        sys.exit(print_statement(concerto_connect))


##Concerto Tenant Name to Tenant UUID GET)##########################################
print("\n# Requesting tenant " + concertoTenant + " tenant UUID")
LogFile_write(local_time() + " - # Requesting tenant " + concertoTenant + " tenant UUID\n")
tenantUUID = concerto_get_api(https + concertoTenantURL,transaction_headers)["tenantInfo"]["uuid"]
print("\n# Successfull response for " + concertoTenant + " tenant UUID")
LogFile_write(local_time() + " - # Successfull response for " + concertoTenant + " tenant UUID\n")
#print(tenantUUID)


##Concerto GET for Configured SASE Gateways###########################################
with open (batch_dir_path + "sase_gateways.json", "w") as saseGWfile:
    print("\n# Requesting list of available Cloud Gateways and VPN Names for " + concertoTenant)
    saseGWfile.write(json.dumps(concerto_get_api(https + concerto_v1_URL + tenantUUID + sase_gw_string, transaction_headers)))
    saseGWfile.close()


#Print configured SASE GW list and request user input variable
with open(batch_dir_path + "sase_gateways.json", "r", encoding="utf-8") as saseGWfile:
  saseGW_dict = json.loads(saseGWfile.read())
  print_statement(sasegw_print)
  for saseGW in saseGW_dict["data"]:
    region = saseGW["regionName"]
    for gw in saseGW["saseGatewayInfos"]:
        gw_name = gw["gatewayName"]
        print("# Gateway Region: " + region + " / " + "Gateway Name: " + gw_name + "\n")

  saseGateway = input("Please enter the SASE GW name used for Site-to-Site Tunnels: ")


  #Print configured VPN Name list and request user input variable
  print_statement(vpnName_print)
  for saseGW in saseGW_dict["data"]:
    for gw in saseGW["saseGatewayInfos"]:
      gw_name = gw["gatewayName"] #new 20may2025
      if gw_name == saseGateway: #new 20may2025
        for vpn in gw["vpnInfos"]:
            vpn_name = vpn["vpnName"]
            print("# " + vpn_name + "\n")
  
  vpnName = input("Please enter the VPN Name used for Site-to-Site Tunnels: ")

##BGP Import and Export Policy lookup files
def bgp_policy_json ():
    with open(batch_dir_path + "bgp_policy.json", "w", encoding ="utf-8") as jsonFile:
        bgp_policies = concerto_get_api(https + concerto_v1_URL + tenantUUID + 
                                       "/sase/bgp-policy/summarize", transaction_headers)["data"]
        bgp_policy_json = json.dumps(bgp_policies, indent = 4)
        jsonFile.write(bgp_policy_json)
        jsonFile.close()
    with open(batch_dir_path + "bgp_policy.json", "r", encoding="utf-8") as jsonFile:
        bgp_policy_list = json.loads(jsonFile.read())
        valid_policy_array = []
        for policy in bgp_policy_list:
            if "name" in policy:
                bgp_policy_name = policy["name"]
                valid_policy_array.append(bgp_policy_name)
                print(bgp_policy_name)
        print("\n")
    with open(batch_dir_path + "valid_bgp_policy.json", "w", encoding="utf-8") as policy_jsonFile:
        jsonString = json.dumps(valid_policy_array, indent=4)
        policy_jsonFile.write(jsonString)
        policy_jsonFile.close
    return(bgp_policy_json)


#User input for tunnel type
while True:
    tunnel_type = input("Please enter the tunnel type (ipsec or gre): ").lower()
    if tunnel_type in ['ipsec', 'gre']:
        break
    else:
        print("Invalid input. Please enter 'ipsec' or 'gre'.")


if tunnel_type == "ipsec":#testing for addition of GRE
    mtu = "1336"#testing for addition of GRE
#IPSEC user input Versa Best Practices vs manual configuration
    tunnel_bestPract = ""
    while tunnel_bestPract != "yes" or tunnel_bestPract != "y":
        print("\n")
        print_statement(defaultIKEIPSec_print)
        print("Would you like to use default IKE/IPSEC parameters listed above (yes or no)? ")
        tunnel_bestPract = input('!! To configure custom parameters enter "no" !!: ')

        #Manual configuration of IKE/IPSEC Parameters
        if tunnel_bestPract == "no" or tunnel_bestPract == "n": #ipsec included for future version GRE use case
            #IKE variable user input
            ike_version = input("Please enter the IKE Version (v1, v2, or v2-or-v1): ")
            while ike_version not in valid_ike_versions:
              ike_version = input("Please enter a valid IKE Version (v1, v2, or v2-or-v1): ")

            print_statement(ike_transform_print)
            print_list(valid_ike_transforms)
            ike_transform = input("Please enter the IKE Transform from the above list: ")
            while ike_transform not in valid_ike_transforms:
              ike_transform = input("Please enter a valid IKE Transform from the above list: ")

            print_statement(DH_print)
            print_list(valid_dh_groups)
            ike_dh_group = input("Please enter the IKE PFS (DH) Group from the list above: ")
            while ike_dh_group not in valid_dh_groups:
              ike_dh_group = input("Please enter a valid IKE PFS (DH) Group from the list above: ")

            ike_rekey_time_int = int(input("Please enter the IKE rekey time in seconds: "))
            while ike_rekey_time_int <= 131 or ike_rekey_time_int >= 864001:
                ike_rekey_time_int = int(input("Please enter a valid IKE rekey time in seconds (132-86400): "))
            ike_rekey_time = str(ike_rekey_time_int)

            ike_dpdt_time_int = int(input("Please enter the IKE DPDT timeout in seconds: "))
            while ike_dpdt_time_int >= 36000:
                ike_dpdt_time_int = int(input("Please enter a valid IKE DPDT timeout in seconds (0-36000): "))
            ike_dpdt_timeout = str(ike_dpdt_time_int)

            #IPSec user input
            print_statement(ipsec_transform_print)
            print_list(valid_ipsec_transforms)
            ipsec_transform = input("Please enter the IPSEC Transform from the above list: ")
            while ipsec_transform not in valid_ipsec_transforms:
              ipsec_transform = input("Please enter a valid IPSEC Transform from the above list: ")

            print_statement(DH_print)
            print_list(valid_dh_groups)
            ipsec_dh_group = input("Please enter the IPSEC PFS (DH) Group from the list above: ")
            while ike_dh_group not in valid_dh_groups:
               ipsec_dh_group = input("Please enter a valid IPSEC PFS (DH) Group from the list above: ")

            ipsec_hello_int = int(input("Please enter the IPSEC hello interval: "))
            while ipsec_hello_int >= 36000:
                ipsec_hello_int = int(input("Please enter a valid IKE DPDT timeout in seconds (0-36000): "))
            ipsec_hello_interval = str(ipsec_hello_int)

            ipsec_rekey_time_int = int(input("Please enter the IPSEC rekey time in seconds: "))
            while ipsec_rekey_time_int <= 131 or ipsec_rekey_time_int >= 864001:
                ipsec_rekey_time_int = int(input("Please enter a valid IPSEC rekey time in seconds (132-86400): "))
            ipsec_rekey_time = str(ike_rekey_time_int)


            #Authenticaiton user input
            ipsec_auth_type = input("Please enter the Authentication Method (PSK or Certificate): ")
            while ipsec_auth_type not in ipsec_auth_types:
              ipsec_auth_type = input("Please enter a valid Authentication Method (PSK or Certificate): ")

            if ipsec_auth_type == "PSK":
                #Local Concerto Auth user input
                ipsec_auth_type_key = "psk"
                local_identity_type = "FQDN"
                with open(batch_dir_path + "sase_gateways.json", "r", encoding="utf-8") as saseGWfile:
                    saseGW_dict = json.loads(saseGWfile.read())
                    for saseGW in saseGW_dict["data"]:
                            for gateway in saseGW["saseGatewayInfos"]:
                                if gateway["gatewayName"] == saseGateway:
                                    for wanInterface in gateway["wanInterfaces"]:
                                        local_identity_value = wanInterface["circuitFQDN"]
            break
        
        #Versa Best Practice configuration of IKE/IPSEC parameters
        if tunnel_bestPract == "yes" or tunnel_bestPract == "y": #ipsec included for future version GRE use case
           with open(batch_dir_path + "sase_gateways.json", "r", encoding="utf-8") as saseGWfile:
                    saseGW_dict = json.loads(saseGWfile.read())
                    for saseGW in saseGW_dict["data"]:
                            for gateway in saseGW["saseGatewayInfos"]:
                                if gateway["gatewayName"] == saseGateway:
                                    for wanInterface in gateway["wanInterfaces"]:
                                        local_identity_value = wanInterface["circuitFQDN"]
        break

if tunnel_type == "gre":
    mtu = "1400"#testing for addition of GRE


#dynamic routing (bgp) user input
dynamic_routing = ""
while dynamic_routing != "no" or dynamic_routing != "n":
    user_dynamic_routing ="Would you like to leverage dynamic routing (EBGP) between SSE and SD-WAN (yes or no)?: "
    dynamic_routing = input(user_dynamic_routing)
    if dynamic_routing == "yes" or dynamic_routing == "y":

        #BGP password user variable input and check
        user_bgp_password_config = ""
        while user_bgp_password_config != "no" or user_bgp_password_config != "n":
            user_bgp_password_config ="Would you like configure a BGP password (yes or no)?: "
            bgp_password_config = input(user_bgp_password_config)
            if bgp_password_config == "yes" or bgp_password_config == "y":
                bgp_password = getpass.getpass(prompt = "Please enter the BGP password: ")
                bgp_password_confirm = getpass.getpass(prompt = "Please re-enter the BGP password: ")
                while bgp_password != bgp_password_confirm:
                    print("!! Entered BGP passwords do not match !!")
                    bgp_password = getpass.getpass(prompt = "Please enter the BGP password: ")
                    bgp_password_confirm = getpass.getpass(prompt = "Please re-enter the BGP password: ")
                    if bgp_password == bgp_password_confirm:
                        break
                break
            if bgp_password_config == "no" or bgp_password_config == "n":
                bgp_password = ""  
                break
                
        #BGP import and export user variable input and check       
        policy_config = ""
        while policy_config != "no" or policy_config != "n":
            user_policy_config = "Would you like to configure common BGP Import and Export policies (yes or no)?: "
            policy_config = input(user_policy_config)
            if policy_config == "yes" or policy_config == "y":
                print_statement(bgp_policy_print)
                bgp_policy_json ()
                with open(batch_dir_path + "bgp_policy.json", "r", encoding="utf-8") as bgpPolicyfile:
                    bgp_policy_list = json.loads(bgpPolicyfile.read())
                    for policy in bgp_policy_list:
                        if "name" in policy:
                            bgp_policy_name = policy["name"]
                    if bgp_policy_name:
                        with open(batch_dir_path + "valid_bgp_policy.json", "r", encoding="utf-8") as policy_jsonFile:
                            valid_policy_list = json.loads(policy_jsonFile.read())
                            bgp_import_name = input("Please enter the BGP IMPORT policy from the above list: ")
                            while bgp_import_name not in valid_policy_list:
                                bgp_import_name = input("Please enter the BGP IMPORT policy from the above list: ")
                            for policy in bgp_policy_list:
                                if bgp_import_name == policy["name"]:
                                    bgp_import_policy = policy["uuid"]
                            bgp_export_name = input("Please enter the BGP EXPORT policy from the above list: ")
                            while bgp_export_name not in valid_policy_list:
                                bgp_export_name = input("Please enter the BGP EXPORT policy from the above list: ")
                            for policy in bgp_policy_list:
                                if bgp_export_name == policy["name"]:
                                    bgp_export_policy = policy["uuid"]
                    else:
                        print("## !! There are no BGP Policies configured.  Skipping BGP policy configuration!! ##")
                    break
            if policy_config == "no" or policy_config == "n":
                bgp_import_policy = ""
                bgp_export_policy = ""
                break
        break
    if dynamic_routing == "no" or dynamic_routing == "n":
        break

##Convert csv static route file to json static route file function
def csv_to_json_static(csvFilePath, jsonFilePath):
    jsonArray = []
    with open(csvFilePath, encoding="utf-8") as csvFile:
        csvReader = csv.DictReader(csvFile)
        for row in csvReader:
            jsonArray.append(row)
    with open(jsonFilePath, "w", encoding="utf-8") as jsonFile:
        jsonString = json.dumps(jsonArray, indent=4)
        jsonFile.write(jsonString)
        jsonFile.close

##Static route configuration user input 
def static_routes(file,device_name):
  destination_nw = input("Please enter the static route ipv4 destination network for SD-WAN branch " + device_name + " (ipv4 address/mask): ")
  static_route_pref = input("Please enter the preference for destination " + destination_nw + ": ")
  file.write(destination_nw + "," + static_route_pref + "\n")
  add_route = ""
  while add_route != "no" or add_route != "n":
    user_add_route = "Would you like to add an additional SSE Gateway to SD-WAN static route for SD-WAN Branch "+ device_name + " (yes or no)?: "
    add_route = input(user_add_route)
    #print(add_route)
    if add_route == "yes" or add_route == "y":
        add_destination_nw = input("Please enter the static route ipv4 destination network for SD-WAN branch " + device_name + " (ipv4 address/mask): ")
        add_static_route_pref = input("Please enter the preference for destination " + add_destination_nw + ": ")
        file.write(add_destination_nw + "," + add_static_route_pref + "\n")
    elif add_route == "no" or add_route == "n":
        break
    
##create jinja2 json body
def Concerto_bgp_importExport(sdwan_bgp_address,sdwan_bgp_asn, bgp_import_policy, 
                              bgp_export_policy, vcg_bgp_asn, bgp_password):
    templateLoader = jinja2.FileSystemLoader(searchpath="./")
    templateEnv = jinja2.Environment(loader=templateLoader)
    TEMPLATE_FILE = "concerto_bgp_importExport.j2"
    template = templateEnv.get_template(TEMPLATE_FILE)
    outputText = template.render(sdwan_bgp_address = sdwan_bgp_address, sdwan_bgp_asn=sdwan_bgp_asn, bgp_import_policy=bgp_import_policy, 
                                 bgp_export_policy=bgp_export_policy, vcg_bgp_asn=vcg_bgp_asn, bgp_password=bgp_password)
    #print(outputText)
    return outputText
   

def Concerto_S2S_j2(tunnel_type, ipsec_auth_type, ipsec_auth_type_key, local_identity_type, 
                    local_identity_value, identity_key, remote_identity_type, remote_identity_value,
                    ike_version, ike_transform, ike_dh_group, 
                    ike_rekey_time, ike_dpdt_timeout, ipsec_transform, ipsec_dh_group, 
                    ipsec_hello_interval, ipsec_rekey_time, staticRoutes , saseGateway, 
                    device_puplic_ip, tunnel_name, protocol, neighbor, 
                    concerto_tunnel_ip, vpnName, mtu):
    templateLoader = jinja2.FileSystemLoader(searchpath="./")
    templateEnv = jinja2.Environment(loader=templateLoader)
    TEMPLATE_FILE = "concertoS2Sbody.j2"
    template = templateEnv.get_template(TEMPLATE_FILE)
    outputText = template.render(tunnel_type=tunnel_type, ipsec_auth_type=ipsec_auth_type, ipsec_auth_type_key=ipsec_auth_type_key, 
                                 local_identity_type=local_identity_type, local_identity_value=local_identity_value, identity_key=identity_key, 
                                 remote_identity_type=remote_identity_type, remote_identity_value=remote_identity_value, 
                                 ike_version=ike_version, ike_transform=ike_transform, ike_dh_group=ike_dh_group, 
                                 ike_rekey_time=ike_rekey_time, ike_dpdt_timeout=ike_dpdt_timeout, ipsec_transform=ipsec_transform, 
                                 ipsec_dh_group=ipsec_dh_group, ipsec_hello_interval=ipsec_hello_interval, ipsec_rekey_time=ipsec_rekey_time, 
                                 staticRoutes=staticRoutes , saseGateway=saseGateway, device_puplic_ip=device_puplic_ip, 
                                 tunnel_name=tunnel_name, protocol=protocol, neighbor=neighbor, 
                                 concerto_tunnel_ip=concerto_tunnel_ip, vpnName=vpnName, mtu=mtu)
    #print(outputText)
    return outputText

#below added for GRE testing 3 June
def Concerto_GRE_j2(tunnel_type, staticRoutes , saseGateway, 
                    device_puplic_ip, tunnel_name, protocol, neighbor, 
                    concerto_tunnel_ip, vpnName, mtu):
    templateLoader = jinja2.FileSystemLoader(searchpath="./")
    templateEnv = jinja2.Environment(loader=templateLoader)
    TEMPLATE_FILE = "concertoGREbody.j2"
    template = templateEnv.get_template(TEMPLATE_FILE)
    outputText = template.render(tunnel_type=tunnel_type, staticRoutes=staticRoutes , saseGateway=saseGateway,
                                 device_puplic_ip=device_puplic_ip, tunnel_name=tunnel_name, protocol=protocol, 
                                 neighbor=neighbor, concerto_tunnel_ip=concerto_tunnel_ip, vpnName=vpnName, mtu=mtu)
    #print(outputText)
    return outputText


##Create JSON (Jinja2) body for Concerto S2S tunnel based on csv batch file and configure in Concerto
def Concerto_S2S():
    for variable in csv_to_json_vars(csv_batch_file, jsonFile):
      device_name = variable["device_name"]
      bgp_ip_compile = re.compile(r"^([^/]*)*")
      sdwan_tunnel_ip = re.search(bgp_ip_compile, variable["sdwan_tunnel_ip"]).group(0)
      tunnel_name_ip = sdwan_tunnel_ip.replace(".", "-")
      if tunnel_type == "ipsec": #added for gre testing 3 June
        if ipsec_auth_type == "PSK":
          remote_identity_type = "FQDN"
          remote_identity_value = device_name + "." + concertoTenant + "-" + tunnel_name_ip + ".net"
          identity_key = ''.join(secrets.choice(alphabet) for i in range (32))
      tunnel_name = saseGateway + "_" + device_name + "_" + tunnel_name_ip + "-" + tunnel_type
      with open (batch_dir_path + device_name + "_" + tunnel_name_ip + "_SSE_config.json", "w") as sseConfigFile:
        device_puplic_ip = variable["sdwan_public_ip"] 
        concerto_tunnel_ip = variable["vcg_tunnel_ip"]
        if dynamic_routing == "no" or dynamic_routing == "n":
            protocol = "none"
            neighbor = "[]"
            static_routing = ""
            while static_routing != "no" or static_routing != "n":
                user_static_routing = "Would you like to add static routing from SSE Gateway to SD-WAN branch " + device_name + " (yes or no)?: "
                static_routing = input(user_static_routing)
                if static_routing == "yes" or static_routing == "y":
                    with open(batch_dir_path + device_name + "_" + tunnel_name_ip +  "_static_.csv", "w") as staticCSV, open(batch_dir_path + device_name + "_" + tunnel_name_ip + "_static.json", "w") as staticJSON:
                        staticCSV.write("destination,preference\n")
                        static_routes(staticCSV,device_name)
                    staticCSV.close()
                    staticJSON.close()
                    csv_to_json_static(batch_dir_path + device_name + "_" + tunnel_name_ip +  "_static_.csv", batch_dir_path + device_name + "_" + tunnel_name_ip + "_static.json")
                    with open(batch_dir_path + device_name + "_" + tunnel_name_ip + "_static.json", "r", encoding="utf-8") as staticJSON:   
                      staticRoutes = staticJSON.read()
                      break
                elif static_routing =="no" or static_routing =="n":
                    staticRoutes = "[]"
                    break
        if dynamic_routing == "yes" or dynamic_routing == "y":
            staticRoutes = "[]"
            protocol = "EBGP"
            obj_compile = re.compile(r"^([^/]*)*")
            sdwan_bgp_address = re.search(obj_compile, variable["sdwan_tunnel_ip"]).group(0)
            sdwan_bgp_asn = variable["sdwan_bgp_asn"]
            vcg_bgp_asn = variable["vcg_bgp_asn"]
            neighbor = Concerto_bgp_importExport(sdwan_bgp_address,sdwan_bgp_asn, bgp_import_policy, 
                                                     bgp_export_policy, vcg_bgp_asn, bgp_password)
        else:
            protocol = "none"
            neighbor = "[]"

        #Create body data and run POST API to configure
        if tunnel_type == "ipsec":#testing for addition of GRE
            concertoS2Sbody = Concerto_S2S_j2(tunnel_type, ipsec_auth_type, ipsec_auth_type_key, local_identity_type, 
                                              local_identity_value, identity_key, remote_identity_type, remote_identity_value,
                                              ike_version, ike_transform, ike_dh_group, 
                                              ike_rekey_time, ike_dpdt_timeout, ipsec_transform, ipsec_dh_group, 
                                              ipsec_hello_interval, ipsec_rekey_time, staticRoutes , saseGateway, 
                                              device_puplic_ip, tunnel_name, protocol, neighbor, 
                                              concerto_tunnel_ip, vpnName, mtu)
            concertoS2Sstring = '/sase/site-to-site-tunnels'
            print("\n" + local_time() + " - # Creating Concerto site-to-site tunnel for " + device_name)
            LogFile_write(local_time() + " - # Creating Concerto site-to-site tunnel for " + device_name  + "\n")
            sseConfigFile.write(concertoS2Sbody)
            sseConfigFile.close()
            print_data = local_time() + " - # Successfully created Concerto site-to-site tunnel for " + device_name + "\n"
            concertoPostApi(https + concerto_v1_URL + tenantUUID + concertoS2Sstring , transaction_headers, concertoS2Sbody, print_data)

        #below is for GRE testing 3 June
        if tunnel_type == "gre":#testing for addition of GRE
            concertoGREbody = Concerto_GRE_j2(tunnel_type, staticRoutes , saseGateway, 
                                              device_puplic_ip, tunnel_name, protocol, neighbor, 
                                              concerto_tunnel_ip, vpnName, mtu)
            concertoS2Sstring = '/sase/site-to-site-tunnels'
            print("\n" + local_time() + " - # Creating Concerto site-to-site tunnel for " + device_name)
            LogFile_write(local_time() + " - # Creating Concerto site-to-site tunnel for " + device_name  + "\n")
            sseConfigFile.write(concertoGREbody)
            sseConfigFile.close()
            print_data = local_time() + " - # Successfully created Concerto site-to-site tunnel for " + device_name + "\n"
            concertoPostApi(https + concerto_v1_URL + tenantUUID + concertoS2Sstring , transaction_headers, concertoGREbody, print_data)

Concerto_S2S()

#Publish and event-stream consumption
with open(batch_dir_path + "concerto_accessToken.txt", "r") as accessTokenFile:   
    task_headers = {
        'Accept': 'text/event-stream',
        'Content-Type': 'text/event-stream;charset=UTF-8',
        'Authorization': 'Bearer ' + str(accessTokenFile.read())
        }
accessTokenFile.close()



def concerto_eventstream_api(url, oauthHeader):
    print(f"Connecting to SSE publish stream: {url}")
    try:
        response = requests.get(url, headers=oauthHeader, stream=True, verify=False, timeout=120)
        client = SSEClient(response)
        print("Connection to SSE publish stream successful.")
        for event in client.events():
            #print("Raw event received:", repr(event))
            try:
                if not event.data.strip():
                    continue
                #print("Raw data:", event.data)
                stream_json = json.loads(event.data)
                #print("Parsed JSON:", json.dumps(stream_json, indent=4))
                message = stream_json.get("message", "")
                if message:
                    #print("Message:", message)
                    print(local_time() + " - # " + message)
                    LogFile_write(local_time() + " - # " + message + "\n")
            except json.JSONDecodeError:
                print("Non-JSON data:", event.data)
    except Exception as e:
        print(f"[ERROR] SSEClient failed to connect or process stream: {e}")


def concerto_gw_publish():
    with open(batch_dir_path + "sase_gateways.json", "r", encoding="utf-8") as saseGWfile:
      saseGW_dict = json.loads(saseGWfile.read())
      for saseGW in saseGW_dict["data"]:
          for gateway in saseGW["saseGatewayInfos"]:
              if gateway["gatewayName"] == saseGateway:
                  gatewayUUID = gateway["gatewayUUID"]
                  gw_publish_body = '''{
                    "gatewayMap": {
                      ''' + '''"''' + saseGateway + '''"''' + ''': ''' + '''"''' + gatewayUUID + '''"''' + '''
                      }
                    }'''
                  concerto_publish_string = "/gateways/publish"
                  task_id = concertoPutApi(https + concerto_v1_URL + tenantUUID + concerto_publish_string , transaction_headers, gw_publish_body)[gatewayUUID]
                  print("\n" + local_time() + " - # Concerto Site-to-Site Tunnel configuraiton being published to " + saseGateway + " Task ID = " + task_id)
                  LogFile_write(local_time() + " - # Concerto Site-to-Site Tunnel configuraiton being published to " + saseGateway + " Task ID = " + task_id + "\n")
                  print("\n# Status messages will be listed below\n")
                  eventstreamURL = https + concertoURL + "/v1/tasks/task/" + task_id
                  print(eventstreamURL)
                  concerto_eventstream_api(eventstreamURL,task_headers)
                      
concerto_gw_publish()

#Remove Access Token File
txt_files = glob.glob(batch_dir_path + "*.txt")
for file in txt_files:
    os.remove(file)



