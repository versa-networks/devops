from argparse import ArgumentParser
import argparse
import csv
from dataclasses import dataclass
#from ssl import CERT_NONE, create_default_context
import getpass
import json
import re
import sys
from urllib import request
import requests
import urllib3
import os 
from pathlib import Path
import time
import ipaddress


#suppress certificate verification warnings to accept self signed certificate
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


#create class that will describe appliance
@dataclass
class ApplianceNameUuid:
    device_name : str
    device_uuid : str
    device_serial : str
    device_location : str
    device_hardware : str


parser = ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,description='''---Versa Networks---
CSV file will contain all devices from selected Tenant. 
Script will save data in the same folder from where it is executed. User who execute the script should have write permissinons in the folder as it will create a file called inventory with gathered data. 
Script is compatible with Python version 3\n
''')

parser.add_argument('-u','--user',dest='username',help='your Versa Director username',metavar='')
parser.add_argument('-p','--password',dest='password',help='your Versa Director password (to enter password in a hidden format skip this option)',metavar='')
parser.add_argument('-t','--tenant',dest='tenant',help='Tenant name value',metavar='')
parser.add_argument('-d','--director',dest='destinationVD',help='Director FQDN or IP',metavar='')
args = parser.parse_args()

#Check if input for Director IP / FQDN is in a valid or expected format
def is_destinationVD_valid(destinationVD):
    if ('http://' in destinationVD):
        args.destinationVD = destinationVD[7:]
        args.destinationVD = destinationVD.split('/')[2]
        return destinationVD and '.' in destinationVD
    elif ('https://' in destinationVD):       
        args.destinationVD = destinationVD[8:]
        args.destinationVD = destinationVD.split('/')[2]
        return destinationVD and '.' in destinationVD
    else:
        args.destinationVD = destinationVD.split('/')[0]
        return destinationVD and '.' in destinationVD

#method to convert json appliance object into python Appliance object
def appliance_from_json(json_appliance):
    device_name = json_appliance['name']
    device_uuid = json_appliance['uuid']
    device_location = str
    device_serial : str
    device_hardware : str
    if 'Hardware' in json_appliance: 
        if 'serialNo' in json_appliance['Hardware']: device_serial = json_appliance['Hardware']['serialNo'] 
        else: device_serial = "No Serial Number"
        if 'model' in json_appliance['Hardware']: device_hardware = json_appliance['Hardware']['model']
        else: device_hardware = "Can't identify hardware type" 
    else:  
        device_serial = "No Serial Number" 
        device_hardware = "Can't identify hardware type"
    if 'location' in json_appliance:
        device_location = json_appliance['location']
    else:
        device_location = "Can't identify location"
    return ApplianceNameUuid(device_name,device_uuid,device_serial,device_location,device_hardware)

urls_list = []
appliance_list = []
failed_connection = []

#iterate accross devices and get serial number, hardware model and location information. Generate list of appliances with inner list of appliance details
def appliance_objects(appliances):
    appliance_object_list = []
    for appliance in appliances:
        appliance_name = appliance_from_json(appliance).device_name
        appliance_hardware = appliance_from_json(appliance).device_hardware
        appliance_serial = appliance_from_json(appliance).device_serial
        appliance_location = appliance_from_json(appliance).device_location
        appliance_object = [appliance_name, appliance_hardware, appliance_serial, appliance_location]
        appliance_object_list.append(appliance_object)
        appliance_object = []
    return appliance_object_list



def appliances_url(appliances):
#Create a loop to print all appliances names and UUID. Generate API URLs and return those in a list    
    for json_appliance in appliances:
        appliance = appliance_from_json(json_appliance)
        url_appliance_inf_detail = f'https://{args.destinationVD}:9182/vnms/dashboard/appliance/{appliance.device_name}/live?uuid={appliance.device_uuid}&command=interfaces%2Finfo%2F{args.tenant}?deep'
        urls_list.append(url_appliance_inf_detail)
        appliance_list.append(appliance.device_name)
    return urls_list, appliance_list

#Collect VRRP IP Adresses from interfaces
def appliances_VRRP_IP_list(appliances, failed_connection):
#Create a loop to generate a list of URLs that can be used to get VRRP IP    
    VRRP_url = {}
    VRRP_IPs = {}
    print('Preparing to start VRRP IPs collection')
    i = 0
    while i < 10:
        i = i + 1
        print(f'{i}0%', end='\r')
        time.sleep(1) 
    print('\n')
    for json_appliance in appliances:
        appliance = appliance_from_json(json_appliance)
        url_appliance_VRRP = f'https://{args.destinationVD}:9182/vnms/dashboard/appliance/{appliance.device_name}/live?command=vrrp%2Fgroup%2Forg%2F{args.tenant}%2Fsummary?deep=true'
        VRRP_url.update({appliance.device_name:url_appliance_VRRP})

    for device_name, connect_url in VRRP_url.items():
        if device_name in failed_connection:
            print(f'Skipping connection to {device_name} as it is not reachable')
            continue
        VRRP_response = requests.get(connect_url, verify=False,timeout=20,auth=requests.auth.HTTPBasicAuth(args.username,args.password))
        if VRRP_response.status_code == 504:
            print(f'ATTENTION! {device_name} didn\'t get VRRP IP due to connection timeout')
            continue 
        if VRRP_response.text.strip():
            VRRP_response_json = VRRP_response.json()

            for entry in VRRP_response_json['collection']['interfaces:summary']:
                VRRP_IP = entry.get('virtual-ip')
                if VRRP_IP:
                    if device_name not in VRRP_IPs:
                        VRRP_IPs[device_name] = []
                    VRRP_IPs[device_name].append(VRRP_IP)
            print(f'VRRP IPs saved for {device_name}')
        else: print(f'{device_name} has no VRRP')    
        time.sleep(2)
    print('VRRP IP address inventory collection completed')
    return VRRP_IPs

#run APIs to Director to get device interface details
def appliances_interfaces(urls_list):
    all_appliances_interfaces = []
    for json_url, appliance_name in zip(urls_list, appliance_list):
        try:
            
            json_response = requests.get(json_url, verify=False,timeout=20,auth=requests.auth.HTTPBasicAuth(args.username,args.password))
            if json_response.status_code == 504:
                print(f"504 Gateway Timeout for device: {appliance_name}. Appliance is not reachable.")
                failed_connection.append(appliance_name)
                continue  
            json_data = json_response.json()
            current_directory = os.path.dirname(os.path.abspath(__file__))
            inventory_file = os.path.join(current_directory,'inventory.json')
            print(f"Inventory file path: {inventory_file} for device {appliance_name}")
            
            
            if os.path.exists(inventory_file):
                with open(inventory_file, 'r') as json_file:
                    existing_data = json.load(json_file)
            else:
                existing_data = []

            separator = "##################################################"
            existing_data.append(separator)
            appliance_name = f'device name: {appliance_name}'
            existing_data.append(appliance_name)
            existing_data.append(json_data)
            
            with open(inventory_file, 'w') as json_file:
                json.dump(existing_data, json_file, indent=4)
            
            all_appliances_interfaces.append(appliance_name)
            all_appliances_interfaces.append(json_data)
            
        except FileNotFoundError:
            print(f"File not found: {inventory_file}. Creating a new file.")
            with open(inventory_file, 'w') as json_file:
                json.dump([], json_file)
        time.sleep(2)
    return all_appliances_interfaces


#Get required information from devices, such as device name, IP addresses and interface information
def parse_appliance_details(all_appliance_interfaces, appliance_object_list):
    csv_data = []
    device_name = None
    device_serial = ""
    device_location = ""
    device_hardware = ""
    for device_details in all_appliance_interfaces:
        interface_names = []
        interface_ips = []
        interface_public_ips = []
        
        if isinstance(device_details, str) and device_details.startswith("device name:"):
            device_name = device_details.split(": ")[1]
        if isinstance(device_details, dict):
            if "interfaces:info" in device_details and "org_intf" in device_details["interfaces:info"]:
                for interface in device_details["interfaces:info"]["org_intf"]:
                    interface_names.append(interface["name"])
                    if "address" in interface and interface["address"]:
                        ip_addresses = [addr["ip"] for addr in interface["address"]] # Join multiple public IPs with a comma
                        interface_ips.append(", ".join(ip_addresses))
                    else:
                        interface_ips.append(None) # Handle cases where there is no address
                    if "public-address" in interface and interface["public-address"]:
                        public_ip_addresses = [addr["public-ip"] for addr in interface["public-address"]] # Join multiple public IPs with a comma
                        interface_public_ips.append(", ".join(public_ip_addresses))
                    else:
                        interface_public_ips.append('No Public IP')  # Handle cases where there is no address, but put no Public IP instead
        
        if device_name is not None and interface_names:
            device_dict = {'Device Name': device_name, 'Device Hardware Model': device_hardware, 'Device Serial Number': device_serial, 'Device Location Info': device_location}

            for interface, ip, public_ip in zip(interface_names, interface_ips, interface_public_ips):
                device_dict[f"{interface}__IP"] = ip
                device_dict[f"{interface}_Public_IP"] = public_ip
            
            csv_data.append(device_dict)
    
            interface_ips = None
            interface_public_ips = None
            device_name = None
    #Add Hardware Model, Serial Number, Location information into each device dictionary. If device is not rechable from VD, it will skip the device
    for device_object in appliance_object_list:
        device_object_name = device_object[0]
        for device in csv_data:
            device_exist_name = device['Device Name']
            if device_object_name == device_exist_name and len(device_object) == 4:    
                device['Device Hardware Model'] = device_object[1]
                device['Device Serial Number'] = device_object[2]
                device['Device Location Info'] = device_object[3]
    #Add VRRP IP addresses for all devices if presented
    list_VRRP_IP = appliances_VRRP_IP_list(appliances, failed_connection)
    for device in csv_data:
        device_object_name = device['Device Name']
        VRRP_IPs = []
        for entry in list_VRRP_IP:
            if entry == device_object_name:
                VRRP_IPs.extend(list_VRRP_IP[entry])
            if VRRP_IPs:
                VRRP_IPs = list(set(VRRP_IPs))
                device['Virtual IP address (VRRP)'] = ', '.join(map(str, VRRP_IPs))
    return csv_data

#remove subnets for interface IP addresses
def remove_subnet(ip_list):
    return [ip.split('/')[0] for ip in ip_list]

#Get Private interface IPs:
def select_versa_Private_IPs(ip_list):
    private_v_ip_list = []   
    for ip in ip_list:
        ip_addr = ipaddress.IPv4Address(ip)
        if ip_addr.is_private:
            private_v_ip_list.append(ip)
    return private_v_ip_list

#Get Public interface IPs:
def select_versa_Public_IPs(ip_list):
    public_v_ip_list = []   
    for ip in ip_list:
        ip_addr = ipaddress.IPv4Address(ip)
        if not ip_addr.is_private:
            public_v_ip_list.append(ip)
    return public_v_ip_list


#save csv_data in csv file            
def get_csv (csv_data):
    interface_keys = set()
    for entry in csv_data:
        for key in entry.keys():
            if key not in ["Device Name", "Device Hardware Model", "Device Location Info", "Device Serial Number", "Virtual IP address (VRRP)"]:
                interface_keys.add(key)
    interface_keys = sorted(interface_keys, key=lambda x: (x.split('_')[-1] != "Public_IP", x.split('_')))
    #Define CSV columns
    columns = ["Device Name", "Device Hardware Model", "Device Serial Number", "Device Location Info", "Virtual IP address (VRRP)", "All Versa interfaces Private IPs", "All Versa interfaces Public IPs", "All Public/Outside IPs (detected by VOS)"] + interface_keys
    #Write data to CSV file
    current_directory = os.path.dirname(os.path.abspath(__file__))
    csv_file_path = os.path.join(current_directory, f"{args.tenant}_Inventory.csv")
    with open(csv_file_path, "w", encoding='UTF8', newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writeheader()
        for entry in csv_data:
            row = {key: entry.get(key, "") for key in columns}
            all_ips = [entry[key] for key in interface_keys if "__IP" in key and entry.get(key)]
            all_ips_no_subnet = remove_subnet(all_ips)
            all_v_private_ips_no_subnet = select_versa_Private_IPs(all_ips_no_subnet)
            all_v_private_ips_no_subnet_no_duplicates = list(set(all_v_private_ips_no_subnet))
            all_v_public_ips_no_subnet = select_versa_Public_IPs(all_ips_no_subnet)
            all_public_ips = [entry[key] for key in interface_keys if "_Public_IP" in key and entry.get(key) and entry[key] != "No Public IP"]
            row["All Versa interfaces Private IPs"] = ", ".join(all_v_private_ips_no_subnet_no_duplicates)
            row["All Versa interfaces Public IPs"] = ", ".join(all_v_public_ips_no_subnet)
            row["All Public/Outside IPs (detected by VOS)"] = ", ".join(all_public_ips)
            writer.writerow(row)
    print(f"{args.tenant}_Inventory.csv file has been created in {current_directory}.")


#Get all variables
if args.destinationVD is None:
    args.destinationVD = input('enter Director FQDN or IP address: ')
    is_destinationVD_valid(args.destinationVD)
    #args.destinationVD = ''
else:
    is_destinationVD_valid(args.destinationVD)

if (not args.username):
    args.username = input('enter your Versa Director username: ')
    #args.username = 'Administrator'

if (not args.password):
    args.password = getpass.getpass('enter your Versa Director password: ')
    #args.password = 'versa123'
    
if (not args.tenant):
    args.tenant = input('enter your Tenant name: ')
    #args.tenant = 'Versa'

#Request Appliance list from a tenant API
url_appliance_list = f'https://{args.destinationVD}:9182/vnms/appliance/appliance/lite?org={args.tenant}&offset=0&limit=2500'
print('')

#Connect to VD and get response
try:
    response_full = requests.get(url_appliance_list,verify=False,timeout=10,auth=requests.auth.HTTPBasicAuth(args.username,args.password))
    if response_full.status_code == 401:
        sys.exit('HTTP response 401. Authentication failed.')
    else: response_json = response_full.json()
except (requests.exceptions.Timeout, requests.ConnectionError):
    sys.exit(f'Connection to Versa Director failed. Please verify HTTPs access to Director')

appliances = response_json['appliances']
appliance_object_list = appliance_objects(appliances)
appliances_url(appliances)
all_appliance_interfaces = appliances_interfaces(urls_list)
csv_file = parse_appliance_details(all_appliance_interfaces, appliance_object_list)
get_csv(csv_file)
