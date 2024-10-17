import json
import requests
import urllib3
import getpass
import csv
import os
import datetime
import re
import sys


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


##Set the standard API request headers###################################
headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
}


##User input varaibles###################################################
print(
    '''
    ################################################
    # Please enter the following environment       #
    # information.                                 #
    ################################################
    '''
)

director_ip = input("What is the primary Director IP or Hostname?: ")
org_name = input("What is the org name?: ")
username = input("What is your username?: ") 
passwrd = getpass.getpass()
auth = username,passwrd


##script run print variables###############################################
def script_begin_print():
    print(
        '''
        ################################################
        # Running Script for configured CGNAT addresses#
        # Dedpending on the size of the environment,   #
        # this script may take some time to complete.  #
        ################################################
        '''
    )

def dir_connect_print():
    print(
        '''
        ################################################
        # !! PLEASE CHECK DIRECTOR CONNECTIVITY    !!  #
        # !! AND TRY AGAIN                         !!  #
        ################################################
        '''
    )

def bad_upass_print():
    print(
        '''
        ################################################
        # !! PLEASE CHECK USERNAME/PASSWORD        !!  #
        # !! AND AND TRY AGAIN                     !!  #
        ################################################
        '''
    )

def org_check_print():
    print(
        '''
        ################################################
        # !! ORGANIZATION DOES NOT EXIST ON VERSA  !!  #
        # !! DIRECTOR. PLEASE CHECK ENSURE CORRECT !!  #
        # !! ORG NAME WAS ENTERED                  !!  #
        ################################################
        '''
    )

def script_complete_print():
    print(
        '''
        ################################################
        # Script has completed.                        #
        #                                              #
        # For spreadsheet output, open cgnat_csv(.txt) #
        # in Excel & use ; delimiter                   #
        #                                              #
        ################################################
        '''
    )


##Set time def for print and log file outputs############################
def local_time():
    local_time = datetime.datetime.now().strftime("_%Y_%m_%d_%H_%M_%S_")
    return local_time


##create file outputs####################################################
cgnat_log_output = "cgnat_log_" + local_time() + "_.log"
cgnat_csv_output = "cgnat_csv_" + local_time() + "_.txt"

def output_file_create():
    with open(cgnat_log_output, "w") as cgnat_log_file:
        cgnat_log_file.write("cgnat_log_" + local_time() + "\n")
        cgnat_log_file.close
    with open(cgnat_csv_output, "w") as cgnat_csv_file:
        cgnat_csv_file.write("appliance_name;appliance_uuid;appliance_location;cgnat_type;cgnat_name;cgnat_low_address;cgnat_high_address\n")
        cgnat_csv_file.close


##API call variables#####################################################
https = "https://"
org_check_string = ':9182/vnms/organization/orgs?offset=0&limit=25'
login_url = ":9182/versa/login"
org_string = '/config/orgs/org-services/'
appliance_detail = ':9182/vnms/appliance/filter/'
appliance_detail_string = '?offset=0&limit=2000'
api_device_url = ':9182/api/config/devices/device/'
nat_pool_command = '/cgnat/pools/pool?deep=true&offset=0&limit=25'
interface_string = "/config/interfaces?deep&offset=0&limit=25"

appliance_detail_url = https + director_ip + appliance_detail + org_name + appliance_detail_string
org_check_url = https + director_ip + org_check_string


##get api call definition#####################################################
def get_api(url):
    try:
        get_response = requests.get((url), headers=headers, verify=False, auth=auth, timeout=10)
        get_response.close()
        if get_response.status_code == 200:
            get_response_json = get_response.json()
            #print(json.dumps(get_response_json, indent=4))
            return get_response_json
        else:
            sys.exit(bad_upass_print())
    except (requests.exceptions.Timeout, requests.ConnectionError):
        sys.exit(dir_connect_print())

##get api only status
def get_api_status(url):
    get_status_response = requests.get((url), headers=headers, verify=False, auth=auth, timeout=10)
    get_status_response.close()
    return get_status_response

##check director connectivity and if org exists on director##
def org_check():
    org_list = get_api(org_check_url)["organizations"]
    for org in org_list:
        if org_name == org["name"]:
                org_check = "exists"
                output_file_create()
                script_begin_print()
                return org_check
        else:
            pass

##########################################################################
##Appliances definitions:
# used to generate a list of devices for the tenant
# with associated  device specific values
##########################################################################
def appliance_name():
    appliance_name = get_appliance["name"]
    return appliance_name

def appliance_uuid():
    appliance_uuid = get_appliance["applianceLocation"]["applianceUuid"]
    return appliance_uuid

def appliance_type():
    appliance_type = get_appliance["applianceLocation"]["type"]
    return appliance_type

def appliance_location():
    if "location" in get_appliance:
        appliance_location = get_appliance["location"]
    else:
        appliance_location = ("no location listed")
    return appliance_location


##########################################################################
##print/file output else definitions
# will be reflected in print output as well as output files
##########################################################################
def else_function():
    with open(cgnat_log_output, "a+") as cgnat_log_file, open(cgnat_csv_output, "a+") as cgnat_csv_file:
        print(local_time() + " " + appliance_name() + " " + appliance_uuid() + " " + appliance_location() + "!!POSSIBLE CGNAT MISCONFIG!!")
        cgnat_log_file.write(local_time() + " " + appliance_name() + " " + appliance_uuid() + " " + appliance_location() + " " + "!!POSSIBLE CGNAT MISCONFIG!!\n")
        cgnat_csv_file.write(appliance_name() + ";" + appliance_uuid() + ";" + appliance_location() + ";" + "POSSIBLE MISCONFIG" + ";" + "POSSIBLE MISCONFIG" + ";" + "POSSIBLE MISCONFIG" + ";" + "POSSIBLE MISCONFIG" + "\n")

def else_no_cgnat_function():
    with open(cgnat_log_output, "a+") as cgnat_log_file, open(cgnat_csv_output, "a+") as cgnat_csv_file:
        print(local_time() + " " + appliance_name() + " " + appliance_uuid() + " " + appliance_location() + " " + "No CGNAT-pool configured")
        cgnat_log_file.write(local_time() + " " + appliance_name() + " " + appliance_uuid() + " " + appliance_location() + " " + "No CGNAT-pool Confgiured\n")
        cgnat_csv_file.write(appliance_name() + ";" + appliance_uuid() + ";" + appliance_location() + ";" + "No CGNAT-pool" + ";" + "No CGNAT-pool" + ";" + "No CGNAT-pool" + ";" + "No CGNAT-pool" + "\n")
        cgnat_log_file.close
        cgnat_csv_file.close


##########################################################################
##cgnat definitions
# used to identify cgnat pools as well as type of pool
##########################################################################
def cgnat_range():
    with open(cgnat_log_output, "a+") as cgnat_log_file, open(cgnat_csv_output, "a+") as cgnat_csv_file:
        if "address" in get_cgnat:
            cgnat_type = "address-pool"
            cgnat_address_list = get_cgnat["address"]
            cgnat_name = get_cgnat["name"]
            for cgnat in cgnat_address_list:
                print(local_time() + " " + appliance_name() + " " + appliance_uuid() + " " + appliance_location() + " " + cgnat_type + " " + cgnat_name + " " + cgnat)
                cgnat_log_file.write(local_time() + " " + appliance_name() + " " + appliance_uuid() + " " + appliance_location() + " " + cgnat_type + " " + cgnat_name + " " + cgnat + "\n")
                cgnat_csv_file.write(appliance_name() + ";" + appliance_uuid() + ";" + appliance_location() + ";" + cgnat_type + ";" + cgnat_name + ";" + cgnat + ";" + "N/A" + "\n")
        elif "address-range" in get_cgnat:
            cgnat_type = "address-range"
            cgnat_range_list = get_cgnat["address-range"]["range"]
            cgnat_name = get_cgnat["name"]
            for cgnat in cgnat_range_list:
                cgnat_range_low = cgnat["low"]
                cgnat_range_high = cgnat["high"]
                print(local_time() + " " + appliance_name() + " " + appliance_uuid() + " " + appliance_location() + " " + cgnat_type + " " + cgnat_name + " " + cgnat_range_low + " " + cgnat_range_high)
                cgnat_log_file.write(local_time() + " " + appliance_name() + " " + appliance_uuid() + " " + appliance_location() + " " + cgnat_type + " " + cgnat_name + " " + cgnat_range_low + " " + cgnat_range_high + "\n")
                cgnat_csv_file.write(appliance_name() + ";" + appliance_uuid() + ";" + appliance_location() + ";" + cgnat_type + ";" + cgnat_name + ";" + cgnat_range_low + ";" + cgnat_range_high + "\n")
        elif "egress-network" in get_cgnat:
            #egress network ip addresses will be identified by the egress interface definitions in the next section
            pass
        else:
            else_function()
    cgnat_log_file.close
    cgnat_csv_file.close

def egress_network():
    if "egress-network" in get_cgnat:
        egress_network = get_cgnat["egress-network"][0]
        return egress_network
    else:
        pass

def cgnat_egress_name():
    if "egress-network" in get_cgnat:
        cgnat_egress_name = get_cgnat["name"]
        return cgnat_egress_name
    else:
        pass


##########################################################################
##egress interface definitions
# used to identify the egress interface ip address if assigned.
# if dhcp interface, print/file output will not reflect IP address
##########################################################################
def interfaces_list():
    interfaces_list = get_api(interface_list_url)["interfaces"]["vni"]
    with open(cgnat_log_output, "a+") as cgnat_log_file, open(cgnat_csv_output, "a+") as cgnat_csv_file:
        if "egress-network" in get_cgnat:
            egress_network_list = get_cgnat["egress-network"]
            for egress_network in egress_network_list:
                for interface in interfaces_list:
                    egress_network_match = re.search(egress_network + "$", interface["unit"][0]["description"])
                    if egress_network_match:
                        if "address" in interface["unit"][0]["family"]["inet"]:
                            egrress_compile = re.compile(r"^([^/]*)*")
                            egress_addr = interface["unit"][0]["family"]["inet"]["address"][0]["addr"]
                            egress_ip = re.search(egrress_compile, egress_addr).group(0)
                        elif "dhcp" in interface["unit"][0]["family"]["inet"]:
                            egress_ip = "dhcp interface"
                        else:
                            else_function()
                        cgnat_type = "egress-network"
                        print(local_time() + " " + appliance_name() + " " + appliance_uuid() + " " + appliance_location() + " " + cgnat_type + " " + cgnat_egress_name() + " " + egress_ip)
                        cgnat_log_file.write(local_time() + " " + appliance_name() + " " + appliance_uuid() + " " + appliance_location() + " " + cgnat_type + " " + cgnat_egress_name() + " " + egress_ip + "\n")
                        cgnat_csv_file.write(appliance_name() + ";" + appliance_uuid() + ";" + appliance_location() + ";" + cgnat_type + ";" + cgnat_egress_name() + ";" + egress_ip + ";" + "N/A" + "\n")
                    else:
                        pass
    cgnat_log_file.close
    cgnat_csv_file.close


##########################################################################
##Run script for cgnat information 
##########################################################################
if not org_check():
    org_check_print()
else:
    for get_appliance in get_api(appliance_detail_url)["versanms.ApplianceStatusResult"]["appliances"]:
        cgnat_pool_url = https + director_ip + api_device_url + appliance_name() + org_string + org_name + nat_pool_command
        interface_list_url = https + director_ip + api_device_url + appliance_name() + interface_string
        if get_api_status(cgnat_pool_url).status_code == 200:
            for get_cgnat in get_api(cgnat_pool_url)["pool"]:
                cgnat_range()
                interfaces_list()
        else:
            else_no_cgnat_function()

