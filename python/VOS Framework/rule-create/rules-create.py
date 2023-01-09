import ssl
import re
import json
import requests
import csv
import urllib3
import argparse
import concurrent
from concurrent.futures import ThreadPoolExecutor

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def post_access_rule(payload):
    url             = 'https://%s:9182/api/config/devices/device/%s/config/orgs/org-services/%s/security/access-policies/access-policy-group/%s/rules' % (args.ip, args.device, args.org, args.group)
    api_request     = requests.post(url, auth=(args.user, args.password), headers={"Content-Type": "application/json", "Accept": "application/json"}, data=payload.encode('utf-8'), verify=False)
    api_response    = api_request.text
    api_status_code = api_request.status_code
    rule_name       = json.loads(payload)['access-policy']['name']
    return_str      = ''

    if re.match('2\d\d', str(api_status_code)):
        return_str      = '[->] access rule '+rule_name+' was created with status code ' + str(api_status_code) 
    else:
        return_str      = '[!!] access rule '+rule_name+' was not created. Verify the rule attributes. Status code ' + str(api_status_code) 
    
    print(return_str)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, description='Script to load access policies from a CSV file')
    parser.add_argument('--ip', default='cloud221.versa-networks.com', type=str,help='IP address of Director')
    parser.add_argument('--device', default='BRANCH-11', type=str,help='Branch Device name')
    parser.add_argument('--org', default='Versa', type=str,help='Organization name')
    parser.add_argument('--group', default='Default-Policy', type=str,help='Policy Group Name')
    parser.add_argument('--user', default='*****', type=str,help='GUI username of Director')
    parser.add_argument('--password', default='*****', type=str,help='GUI password of Director')
    parser.add_argument('--csv_file', default='rules-create.csv', type=str,help='CSV File including the access policy rules')

    args            = parser.parse_args()
    csv_file        = open(args.csv_file, 'r')
    csv_reader      = csv.reader(csv_file, delimiter=';')
    payload_list    = []
    
    next(csv_reader)
    for row in csv_reader:

        rule_name           = row[0]
        rule_source         = row[1]
        rule_destination    = row[2]
        rule_service        = row[3]
        rule_action         = row[4]
        json_template       = open('./rules-create.json')
        
        payload = json_template.read()
        payload = payload.replace('RULE_NAME',rule_name)
        payload = payload.replace('RULE_SRC_LIST', rule_source.replace(',','", "'))
        payload = payload.replace('RULE_DST_LIST', rule_destination.replace(',','", "'))
        payload = payload.replace('RULE_SERVICES', rule_service.replace(',','", "'))
        payload = payload.replace('RULE_ACTION',rule_action)
        payload_list.append(payload)
 
    for rule in payload_list:
        post_access_rule(rule)

