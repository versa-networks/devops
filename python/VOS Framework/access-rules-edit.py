from os import device_encoding
import ssl
import json
import requests
import urllib3
import argparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Script to change the log settings of a VOS CPEs accross ALL its access policies')
    parser.add_argument('--ip', default='10.43.43.254', type=str,help='IP address of Director')
    parser.add_argument('--device', default='BRANCH', type=str,help='Branch Device name')
    parser.add_argument('--org', default='Versa', type=str,help='Organization name')
    parser.add_argument('--group', default='Default-Policy', type=str,help='Policy Group Name')
    parser.add_argument('--user', default='Administrator', type=str,help='GUI username of Director')
    parser.add_argument('--password', default='versa123', type=str,help='GUI password of Director')
    parser.add_argument('--action', default='display', type=str,help='Action to be taken on the offending rules (display / set-log / set-log-profile)')


    args = parser.parse_args()

    payload_event = json.dumps({ "event" : "end" })
    payload_profile = json.dumps({ "profile": "Default-Logging-Profile" })

    url_all_rules   = 'https://%s:9182/api/config/devices/device/%s/config/orgs/org-services/%s/security/access-policies/access-policy-group/%s/rules/access-policy' % (args.ip, args.device, args.org, args.group)
    api_request     = requests.get(url_all_rules, auth=(args.user, args.password), headers={"Accept": "application/json"}, verify=False)
    api_response    = api_request.text
    json_output     = json.loads(api_response)

    for rule in json_output['access-policy']:

        rule_name   = rule['name']
        url_log     = 'https://%s:9182/api/config/devices/device/%s/config/orgs/org-services/%s/security/access-policies/access-policy-group/%s/rules/access-policy/%s/set/lef/event' % (args.ip, args.device, args.org, args.group, rule_name)
        url_profile = 'https://%s:9182/api/config/devices/device/%s/config/orgs/org-services/%s/security/access-policies/access-policy-group/%s/rules/access-policy/%s/set/lef/profile' % (args.ip, args.device, args.org, args.group, rule_name)
   

        if rule['set']['lef']['event'] == 'never':
            if args.action == "set-log":
                api_request     = requests.put(url_log, auth=(args.user, args.password), headers={"Content-Type": "application/vnd.yang.data+json"}, data=payload_event, verify=False)
                print("--> setting log on rule "+rule_name)
            if args.action == "display":
                print("--> "+rule_name+" has NO log enable")

        if 'profile' not in rule['set']['lef']:
            if args.action == "set-log-profile":
                api_request     = requests.put(url_profile, auth=(args.user, args.password), headers={"Content-Type": "application/vnd.yang.data+json"}, data=payload_profile, verify=False)
                print("--> setting log profile on "+rule_name)
            if args.action == "display":
                print("--> "+rule_name+" has NO log profile")
