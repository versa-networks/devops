from os import device_encoding
import ssl
import sys
import json
import requests
import urllib3
import argparse
from threading import Thread


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def help_filter():
    print()
    print('has.no.log           : Match rules with no log settings')
    print('has.log              : Match rules with log settings')
    print('has.no.log.profile   : Match rules with no log-profile settings')
    print('has.log.profile      : Match rules if a log-profile exist')
    print('is.enable            : Match enabled rules')
    print('is.disable           : Match disabled rules')
    print('none                 : Match any rules')
    print()
    exit()

def help_action():
    print()
    print('display           : Display the rule name')
    print('set.log           : Set a traffic logging on the rule ')
    print('set.log.profile   : Set a traffic log profile on the rule')
    print('set.rule.disable  : Disable the rule')
    print('set.rule.enable   : Enable the rule')
    print()
    exit()

def display_rule_name(rule_name):
    print("--> "+rule_name)

def filter_match_rule(rule_json , filter):
    if filter == 'has.no.log' and rule_json['set']['lef']['event'] == 'never':
        return True
    elif filter == 'has.log' and rule_json['set']['lef']['event'] != 'never':
        return True
    elif filter == 'has.no.log.profile' and 'profile' not in rule_json['set']['lef']:
        return True
    elif filter == 'has.log.profile' and 'profile' in rule_json['set']['lef']:
        return True
    elif filter == 'is.enable' and str(rule_json['rule-disable']) == 'False':
        return True
    elif filter == 'is.disable' and str(rule_json['rule-disable']) == 'True':
        return True
    elif filter == 'none':
        return True
    
    if filter != 'has.no.log' and filter != 'has.log' and filter != 'has.no.log.profile' and filter != 'has.log.profile' and filter != 'is.enable' and filter != 'is.disable':
        print()
        print('The filter is incorrect. Use --filter help for details on how to use filters')
        print()
        exit()

def exec_action(rule_json , filter):
    if args.action == "display" and filter_match_rule(rule_json , filter):
        display_rule_name(rule_json['name'])
    elif args.action == "set.log" and filter_match_rule(rule_json , filter):
        set_log(rule_json['name'])
    elif args.action == "set.log.profile" and filter_match_rule(rule_json , filter):
        set_log_profile(rule_json['name'])
    elif args.action == "set.rule.disable" and filter_match_rule(rule_json , filter):
        disable_rule(rule_json['name'])
    elif args.action == "set.rule.enable" and filter_match_rule(rule_json , filter):
        enable_rule(rule_json['name'])
    
    if args.action != "display" and args.action != "set.log" and args.action != "set.log.profile" and args.action != "set.rule.disable" and args.action != "set.rule.enable":
        print()
        print('The action is incorrect. Use --action help for details on how to use filters')
        print()
        exit()


def set_log(rule_name):
    url_log     = 'https://%s:9182/api/config/devices/device/%s/config/orgs/org-services/%s/security/access-policies/access-policy-group/%s/rules/access-policy/%s/set/lef/event' % (args.ip, args.device, args.org, args.group, rule_name)
    api_request     = requests.put(url_log, auth=(args.user, args.password), headers={"Content-Type": "application/vnd.yang.data+json"}, data=payload_event, verify=False)
    print("--> setting log on rule "+rule_name)

def set_log_profile(rule_name):
    url_profile = 'https://%s:9182/api/config/devices/device/%s/config/orgs/org-services/%s/security/access-policies/access-policy-group/%s/rules/access-policy/%s/set/lef/profile' % (args.ip, args.device, args.org, args.group, rule_name)
    api_request     = requests.put(url_profile, auth=(args.user, args.password), headers={"Content-Type": "application/vnd.yang.data+json"}, data=payload_log_profile, verify=False)
    print("--> setting log profile on "+rule_name)

def disable_rule(rule_name):
    url_disable = 'https://%s:9182/api/config/devices/device/%s/config/orgs/org-services/%s/security/access-policies/access-policy-group/%s/rules/access-policy/%s/rule-disable' % (args.ip, args.device, args.org, args.group, rule_name)
    api_request     = requests.put(url_disable, auth=(args.user, args.password), headers={"Content-Type": "application/vnd.yang.data+json"}, data=payload_rule_disable, verify=False)
    print("--> disabling rule "+rule_name)

def enable_rule(rule_name):
    url_enable = 'https://%s:9182/api/config/devices/device/%s/config/orgs/org-services/%s/security/access-policies/access-policy-group/%s/rules/access-policy/%s/rule-disable' % (args.ip, args.device, args.org, args.group, rule_name)
    api_request     = requests.put(url_enable, auth=(args.user, args.password), headers={"Content-Type": "application/vnd.yang.data+json"}, data=payload_rule_enable, verify=False)
    print("--> enabling rule "+rule_name)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Script to change the settings of a VOS CPEs accross ALL its access policies')
    parser.add_argument('--ip', default='10.43.43.254', type=str,help='IP address of Director')
    parser.add_argument('--device', default='BRANCH', type=str,help='Branch Device name')
    parser.add_argument('--org', default='Versa', type=str,help='Organization name')
    parser.add_argument('--group', default='Default-Policy', type=str,help='Policy Group Name')
    parser.add_argument('--user', default='Administrator', type=str,help='GUI username of Director')
    parser.add_argument('--password', default='versa123', type=str,help='GUI password of Director')
    parser.add_argument('--action', default='display', type=str,help='Action to be taken on the offending rules. Use --action help for details')
    parser.add_argument('--filter', default='none', type=str,help='Filter to be applied to limit the scope of the action. Use --filter help for details')


    args = parser.parse_args()

    payload_event           = json.dumps({ "event" : "end" })
    payload_log_profile     = json.dumps({ "profile": "Default-Logging-Profile" })
    payload_no_log_profile  = json.dumps({ "profile": "" })
    payload_rule_disable    = json.dumps({ "rule-disable": "true" })
    payload_rule_enable     = json.dumps({ "rule-disable": "false" })

    url_all_rules   = 'https://%s:9182/api/config/devices/device/%s/config/orgs/org-services/%s/security/access-policies/access-policy-group/%s/rules/access-policy' % (args.ip, args.device, args.org, args.group)
    api_request     = requests.get(url_all_rules, auth=(args.user, args.password), headers={"Accept": "application/json"}, verify=False)
    api_response    = api_request.text
    json_output     = json.loads(api_response)
    filter          = args.filter

    if args.filter == 'help':
        help_filter()

    if args.action == 'help':
        help_action()

    for rule in json_output['access-policy']:
        exec_action(rule,filter)
        #Multi Thread : Does not work very well
        #new_thread = Thread(target=exec_action, args=(rule,filter))
        #new_thread.start()
