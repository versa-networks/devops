import ssl
import re
import json
import requests
import csv
import urllib3
import argparse
import sys

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

STR_POST_ACCESS_RULE_DEVICE_OK          = '[->] access rule %s for device %s was created with status code %s'
STR_POST_ACCESS_RULE_DEVICE_NOK         = '[!!] access rule %s for device %s was not created. Verify the rule attributes. Status code %s.\n[!!] Error: %s\n'
STR_POST_ACCESS_RULE_DEVICE_BULK_OK     = '\n[->] access rules with bulk method for device %s were created successfully\n'
STR_POST_ACCESS_RULE_DEVICE_BULK_NOK    = '\n[!!] access rules with bulk method for device %s  could not be created.\n[!!] Error: %s\n'
STR_POST_ACCESS_RULE_TEMPLATE_OK        = '[->] access rule %s for template %s was created with status code %s'
STR_POST_ACCESS_RULE_TEMPLATE_NOK       = '[!!] access rule %s for template %s was not created. Verify the rule attributes. Status code %s.\n[!!] Error: %s\n' 
STR_POST_ACCESS_RULE_TEMPLATE_BULK_OK   = '\n[->] access rules with bulk method for template %s were created successfully\n'
STR_POST_ACCESS_RULE_TEMPLATE_BULK_NOK  = '\n[!!] access rules with bulk method for template %s could not be created.\n[!!] Error: %s\n'
STR_CONNEXION_ERROR                     = '\n[!!] Could not connect to %s\n'
STR_FILE_ERROR                          = '\n[!!] Could not find the file %s\n'

URL_POST_ACCESS_RULE_DEVICE             = 'https://%s:9182/api/config/devices/device/%s/config/orgs/org-services/%s/security/access-policies/access-policy-group/%s/rules'
URL_POST_ACCESS_RULE_TEMPLATE           = 'https://%s:9182/api/config/devices/template/%s/config/orgs/org-services/%s/security/access-policies/access-policy-group/%s/rules'
URL_POST_BULK_ACCESS_RULE_DEVICE        = 'https://%s:9182/api/config/devices/device/%s/config/orgs/org-services/%s/security/access-policies'
URL_POST_BULK_ACCESS_RULE_TEMPLATE      = 'https://%s:9182/api/config/devices/template/%s/config/orgs/org-services/%s/security/access-policies'

HTTP_HEADER                             = {"Content-Type": "application/json", "Accept": "application/json"}
SINGLE_RULE_ENVELOPPE                   = '{"access-policy": %s }'
BULK_RULES_ENVELOPPE                    = '{"access-policy-group": {"name": "%s", "rules":{"access-policy": [%s] }}}'
PREDEF_APPLICATION_ENVELOPPE            = '"predefined-application-list": ["%s"]'
ZONE_LIST_ENVELOPPE                     = '"zone-list": ["%s"]'



def post_bulk_access_rule(payload):
    try:
        bulk_payload = BULK_RULES_ENVELOPPE %(args.group, payload)
        if re.match('device\:.*',args.target):
            device_name = args.target.split(':',1)[1]

            url             = URL_POST_BULK_ACCESS_RULE_DEVICE % (args.ip, device_name, args.org)
            api_request     = requests.post(url, auth=(args.user, args.password), headers=HTTP_HEADER, data=bulk_payload.encode('utf-8'), verify=False)
            api_response    = api_request.text
            api_status_code = api_request.status_code

            if re.match('2\d\d', str(api_status_code)):       
                print(STR_POST_ACCESS_RULE_DEVICE_BULK_OK % (device_name))
            else:
                error_message = api_request.json()
                print(STR_POST_ACCESS_RULE_DEVICE_BULK_NOK % (device_name, error_message))

        if re.match('template\:.*',args.target):
            template_name = args.target.split(':',1)[1]

            url             = URL_POST_BULK_ACCESS_RULE_TEMPLATE % (args.ip, template_name, args.org)
            api_request     = requests.post(url, auth=(args.user, args.password), headers=HTTP_HEADER, data=bulk_payload.encode('utf-8'), verify=False)
            api_response    = api_request.text
            api_status_code = api_request.status_code

            if re.match('2\d\d', str(api_status_code)):
                print(STR_POST_ACCESS_RULE_TEMPLATE_BULK_OK % (template_name))
            else:
                error_message = api_request.json()
                print(STR_POST_ACCESS_RULE_TEMPLATE_BULK_NOK % (template_name, error_message))

    except (requests.exceptions.Timeout, requests.ConnectionError):
        sys.exit(STR_CONNEXION_ERROR % (args.ip))

def post_access_rule(payload):
    try:
        if re.match('device\:.*',args.target):
            device_name = args.target.split(':',1)[1]

            rule_payload    = SINGLE_RULE_ENVELOPPE % (payload)
            url             = URL_POST_ACCESS_RULE_DEVICE % (args.ip, device_name, args.org, args.group)
            api_request     = requests.post(url, auth=(args.user, args.password), headers=HTTP_HEADER, data=rule_payload.encode('utf-8'), verify=False)
            api_response    = api_request.text
            api_status_code = api_request.status_code
            rule_name       = json.loads(payload)['name']

            if re.match('2\d\d', str(api_status_code)):
                print(STR_POST_ACCESS_RULE_DEVICE_OK % (rule_name, device_name, api_status_code))
            else:
                error_message = api_request.json()
                print(STR_POST_ACCESS_RULE_DEVICE_NOK % (rule_name, device_name, api_status_code, error_message))


        if re.match('template\:.*',args.target):
            template_name = args.target.split(':',1)[1]

            rule_payload    = SINGLE_RULE_ENVELOPPE % (payload)
            url             = URL_POST_ACCESS_RULE_TEMPLATE % (args.ip, template_name, args.org, args.group)
            api_request     = requests.post(url, auth=(args.user, args.password), headers=HTTP_HEADER, data=rule_payload.encode('utf-8'), verify=False)
            api_response    = api_request.text
            api_status_code = api_request.status_code
            rule_name       = json.loads(payload)['name']

            if re.match('2\d\d', str(api_status_code)):
                print(STR_POST_ACCESS_RULE_TEMPLATE_OK % (rule_name, template_name, api_status_code))
            else:
                error_message = api_request.json()
                print(STR_POST_ACCESS_RULE_TEMPLATE_NOK % (rule_name, template_name, api_status_code, error_message))

    except (requests.exceptions.Timeout, requests.ConnectionError):
        sys.exit(STR_CONNEXION_ERROR % (args.ip))



if __name__ == '__main__':

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, description='Script to load access policies from a CSV file')
    parser.add_argument('--ip', default='xxx.versa-networks.com', type=str,help='IP address of Director')
    parser.add_argument('--target', default='device:BRANCH-11', type=str,help='Device (device:XXX) or Device Template (template:XXX) where the rules must be applied.')
    parser.add_argument('--org', default='Versa', type=str,help='Organization name')
    parser.add_argument('--group', default='Default-Policy', type=str,help='Policy Group Name')
    parser.add_argument('--user', default='Administrator', type=str,help='GUI username of Director')
    parser.add_argument('--password', default='xxxx', type=str,help='GUI password of Director')
    parser.add_argument('--csv_file', default='rules-create.csv', type=str,help='CSV File including the access policy rules')
    parser.add_argument('--bulk', default='no', type=str,help='Bulk the rules in a single API call for faster execution. !!! This mode only works with new Access Policy Group !!!')

    args            = parser.parse_args()

    try:
        csv_file        = open(args.csv_file, 'r')
        csv_reader      = csv.reader(csv_file, delimiter=';')
        payload_list    = []
    except:
        print(STR_FILE_ERROR %(args.csv_file))
        exit(1)
    
    next(csv_reader)
    for row in csv_reader:

        rule_name                      = row[0]
        rule_source_z                  = row[1]
        rule_source_address            = row[2]
        rule_source_address_group      = row[3]
        rule_destination_z             = row[4]
        rule_destination_address       = row[5]
        rule_destination_group         = row[6]
        rule_predefined_service        = row[7]
        rule_custom_service            = row[8]
        rule_application               = row[9]
        rule_action                    = row[10]
        json_template                  = open('./rules-create.json')
        
        payload = json_template.read()
        payload = payload.replace('RULE_NAME',rule_name)
        payload = payload.replace('RULE_SRC_ADDRESS_LIST', rule_source_address .replace(',','", "'))
        payload = payload.replace('RULE_SRC_GROUP_ADDRESS_LIST', rule_source_address_group.replace(',','", "'))
        payload = payload.replace('RULE_DST_ADDRESS_LIST', rule_destination_address  .replace(',','", "'))
        payload = payload.replace('RULE_DST_GROUP_ADDRESS_LIST', rule_destination_group  .replace(',','", "'))
        payload = payload.replace('RULE_PREDEFINED_SERVICES', rule_predefined_service.replace(',','", "'))
        payload = payload.replace('RULE_CUSTOM_SERVICES', rule_custom_service.replace(',','", "'))
 
        if rule_application != "":
            payload = payload.replace('RULE_APPLICATIONS', PREDEF_APPLICATION_ENVELOPPE % (rule_application.replace(',','", "')))
        else:
            payload = payload.replace('RULE_APPLICATIONS', "")

        if rule_source_z != "":
            payload = payload.replace('RULE_SRC_ZONE', ZONE_LIST_ENVELOPPE % (rule_source_z.replace(',','", "')))
        else:
            payload = payload.replace('RULE_SRC_ZONE', "")

        if rule_destination_z != "":
            payload = payload.replace('RULE_DST_ZONE', ZONE_LIST_ENVELOPPE % (rule_destination_z.replace(',','", "')))
        else:
            payload = payload.replace('RULE_DST_ZONE', "")

        payload = payload.replace('RULE_ACTION',rule_action)
        payload_list.append(payload)


    if args.bulk == "no":
        for rule in payload_list:
            post_access_rule(rule)

    if args.bulk == "yes":
        rule_list   = ""     
        rule_index  = 0
        
        for rule in payload_list:
            rule_index = rule_index + 1
            if rule_index < len(payload_list):
                rule_list = rule_list+ rule + ','
            else:
                rule_list = rule_list+ rule

        post_bulk_access_rule(rule_list)
