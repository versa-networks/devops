import ssl
import re
import json
import requests
import csv
import urllib3
import argparse
import sys

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

STR_POST_ADDRESS_TEMPLATE_OK            = '[->] address %s for template %s was created with status code %s'
STR_POST_ADDRESS_TEMPLATE_NOK           = '[!!] address %s for template %s was not created. Verify the service attributes. Status code %s.\n[!!] Error: %s\n' 
STR_POST_ADDRESS_DEVICE_OK              = '[->] address %s for device %s was created with status code %s'
STR_POST_ADDRESS_DEVICE_NOK             = '[!!] address %s for device %s was not created. Verify the service attributes. Status code %s.\n[!!] Error: %s\n'

STR_POST_ADDRESS_GROUP_TEMPLATE_OK      = '[->] address group %s for template %s was created with status code %s'
STR_POST_ADDRESS_GROUP_TEMPLATE_NOK     = '[!!] address group %s for template %s was not created. Verify the service attributes. Status code %s.\n[!!] Error: %s\n' 
STR_POST_ADDRESS_GROUP_DEVICE_OK        = '[->] address group %s for device %s was created with status code %s'
STR_POST_ADDRESS_GROUP_DEVICE_NOK       = '[!!] address group %s for device %s was not created. Verify the service attributes. Status code %s.\n[!!] Error: %s\n'

STR_CONNEXION_ERROR                     = '\n[!!] Could not connect to %s\n'
STR_FILE_ERROR                          = '\n[!!] Could not find the file %s\n'
STR_OBJECT_ERROR                        = '\n[!!] Something is wrong with the object %s. Verify the CSV file.\n'

URL_POST_DEVICE_ADDRESS                 = 'https://%s:9182/api/config/devices/device/%s/config/orgs/org-services/%s/objects/addresses'
URL_POST_TEMPLATE_ADDRESS               = 'https://%s:9182/api/config/devices/template/%s/config/orgs/org-services/%s/objects/addresses'
URL_POST_DEVICE_ADDRESS_GROUPS          = 'https://%s:9182/api/config/devices/device/%s/config/orgs/org-services/%s/objects/address-groups'
URL_POST_TEMPLATE_ADDRESS_GROUPS        = 'https://%s:9182/api/config/devices/template/%s/config/orgs/org-services/%s/objects/address-groups'


HTTP_HEADER                             = {"Content-Type": "application/json", "Accept": "application/json"}
JSON_ADDRESS_PAYLOAD                    = '{"address":{"name":"%s","ipv4-prefix":"%s"}}'
JSON_GROUP_PAYLOAD                      = '{"group":{"name":"%s","address-list":["%s"]}}'

def post_address(payload):
    try:
        if re.match('device\:.*',args.target):
            device_name         = args.target.split(':',1)[1]
            url                 = URL_POST_DEVICE_ADDRESS % (args.ip, device_name, args.org)
            api_request         = requests.post(url, auth=(args.user, args.password), headers=HTTP_HEADER, data=payload.encode('utf-8'), verify=False)
            api_response        = api_request.text
            api_status_code     = api_request.status_code
            address_name        = json.loads(payload)['address']['name']

            if re.match('2\d\d', str(api_status_code)):
                print(STR_POST_ADDRESS_DEVICE_OK % (address_name, device_name, api_status_code))
            else:
                error_message = api_request.json()
                print(STR_POST_ADDRESS_DEVICE_NOK % (address_name, device_name, api_status_code, error_message))


        if re.match('template\:.*',args.target):
            template_name       = args.target.split(':',1)[1]
            url                 = URL_POST_TEMPLATE_ADDRESS % (args.ip, template_name, args.org)
            api_request         = requests.post(url, auth=(args.user, args.password), headers=HTTP_HEADER, data=payload.encode('utf-8'), verify=False)
            api_response        = api_request.text
            api_status_code     = api_request.status_code
            address_name        = json.loads(payload)['address']['name']
            
            if re.match('2\d\d', str(api_status_code)):
                print(STR_POST_ADDRESS_TEMPLATE_OK % (address_name, template_name, api_status_code))
            else:
                error_message = api_request.json()
                print(STR_POST_ADDRESS_TEMPLATE_NOK % (address_name, template_name, api_status_code, error_message))
            

    except (requests.exceptions.Timeout, requests.ConnectionError):
        sys.exit(STR_CONNEXION_ERROR % (args.ip))

def post_group(payload):
    try:
        if re.match('device\:.*',args.target):
            device_name         = args.target.split(':',1)[1]
            url                 = URL_POST_DEVICE_ADDRESS_GROUPS % (args.ip, device_name, args.org)
            api_request         = requests.post(url, auth=(args.user, args.password), headers=HTTP_HEADER, data=payload.encode('utf-8'), verify=False)
            api_response        = api_request.text
            api_status_code     = api_request.status_code
            group_name          = json.loads(payload)['group']['name']

            if re.match('2\d\d', str(api_status_code)):
                print(STR_POST_ADDRESS_GROUP_DEVICE_OK % (group_name, device_name, api_status_code))
            else:
                error_message = api_request.json()
                print(STR_POST_ADDRESS_GROUP_DEVICE_NOK % (group_name, device_name, api_status_code, error_message))


        if re.match('template\:.*',args.target):
            template_name       = args.target.split(':',1)[1]
            url                 = URL_POST_TEMPLATE_ADDRESS_GROUPS % (args.ip, template_name, args.org)
            api_request         = requests.post(url, auth=(args.user, args.password), headers=HTTP_HEADER, data=payload.encode('utf-8'), verify=False)
            api_response        = api_request.text
            api_status_code     = api_request.status_code
            group_name          = json.loads(payload)['group']['name']
            
            if re.match('2\d\d', str(api_status_code)):
                print(STR_POST_ADDRESS_GROUP_TEMPLATE_OK % (group_name, template_name, api_status_code))
            else:
                error_message = api_request.json()
                print(STR_POST_ADDRESS_GROUP_TEMPLATE_NOK % (group_name, template_name, api_status_code, error_message))
            

    except (requests.exceptions.Timeout, requests.ConnectionError):
        sys.exit(STR_CONNEXION_ERROR % (args.ip))

if __name__ == '__main__':

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, description='A script to create address objects on Versa Director from a CSV file')
    parser.add_argument('--ip', default='xxxx.versa-networks.com', type=str,help='IP address of Director')
    parser.add_argument('--target', default='device:BRANCH-11', type=str,help='Device (device:XXX) or Device Template (template:XXX) where the address must be created.')
    parser.add_argument('--org', default='Versa', type=str,help='Organization name')
    parser.add_argument('--user', default='Administrator', type=str,help='GUI username of Director')
    parser.add_argument('--password', default='xxxx', type=str,help='GUI password of Director')
    parser.add_argument('--csv_file', default='address-create.csv', type=str,help='CSV File including the services')
    
    args            = parser.parse_args()

    try:
        csv_file        = open(args.csv_file, 'r')
        csv_reader      = csv.reader(csv_file, delimiter=';')
        address_list    = []
        group_list      = []

    except:
        print(STR_FILE_ERROR %(args.csv_file))
        exit(1)
    
    next(csv_reader)
    for row in csv_reader:

        address_name            = row[0]
        address_ip              = row[1]
        address_member          = row[2]

        if address_ip != "" and address_member == "":
            payload = JSON_ADDRESS_PAYLOAD % (address_name,address_ip)
            address_list.append(payload)
        elif address_ip == "" and address_member != "":
            payload = JSON_GROUP_PAYLOAD % (address_name,address_member.replace(',','", "'))
            group_list.append(payload)
        else:
            print(STR_OBJECT_ERROR % (address_name))

    for address in address_list:
        post_address(address)

    for group in group_list:
        post_group(group)

