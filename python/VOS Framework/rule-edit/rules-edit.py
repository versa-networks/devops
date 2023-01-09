from os import device_encoding
import ssl
import re
import sys
import json
import requests
import urllib3
import argparse
import concurrent
from itertools import repeat
from concurrent.futures import ThreadPoolExecutor

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HTTP_HEADER = {"Content-Type": "application/json", "Accept": "application/json"}

def help_filter():
    print()
    print('has.no.log           : Match rules with no log settings')
    print('has.log              : Match rules with log settings')
    print('has.no.log.profile   : Match rules with no log-profile settings')
    print('has.log.profile      : Match rules if a log-profile exist')
    print('has.tag:XXX          : Match rules with the tag value XXX')
    print('has.action.allow     : Match rules with the action allow')
    print('has.zone.src:XXX     : Match rules with the source zone XXX')
    print('has.zone.dst:XXX     : Match rules with the destination zone XXX')
    print('is.enable            : Match enabled rules')
    print('is.disable           : Match disabled rules')
    print('none                 : Match any rules')
    print()
    exit()

def help_action():
    print()
    print('display           : Display the rule name')
    print('delete            : Delete the rule')
    print('set.log           : Set traffic logging on the rule ')
    print('set.log.profile   : Set a traffic log profile on the rule')
    print('set.rule.disable  : Disable the rule')
    print('set.rule.enable   : Enable the rule')
    print('set.tag:XXX       : Override the rule tags with the tag value XXX')
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
    elif filter == 'has.action.allow' and str(rule_json['set']['action']) == 'allow':
        return True

    elif re.match('has.tag\:.*',filter) and 'tag' in rule_json:
        for tag_value in rule_json['tag']:
            if tag_value == filter.split(':',1)[1]:
                return True

    elif re.match('has.zone.src\:.*',filter) and 'source' in rule_json['match']:
        if 'zone' in rule_json['match']['source']:
            for zone_value in rule_json['match']['source']['zone']['zone-list']:
                if zone_value == filter.split(':',1)[1]:
                    return True

    elif re.match('has.zone.dst\:.*',filter) and 'destination' in rule_json['match']:
        if 'zone' in rule_json['match']['destination']:
            for zone_value in rule_json['match']['destination']['zone']['zone-list']:
                if zone_value == filter.split(':',1)[1]:
                    return True

    elif filter == 'none':
        return True
    
    if not re.match('has.zone.dst\:.*',filter) and not re.match('has.zone.src\:.*',filter) and not re.match('has.tag\:.*',filter) and filter != 'has.no.log' and filter != 'has.log' and filter != 'has.no.log.profile' and filter != 'has.log.profile' and filter != 'is.enable' and filter != 'is.disable' and filter != 'has.action.allow':
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
    elif args.action == "delete" and filter_match_rule(rule_json , filter):
        delete_rule(rule_json['name'])

    elif re.match('set.tag\:.*',args.action) and filter_match_rule(rule_json , filter):
        if not 'tag' in rule_json:
            set_tag(rule_json['name'], args.action.split(':',1)[1])
        else:
            rule_json['tag'].append(args.action.split(':',1)[1])
            set_tag(rule_json['name'],rule_json['tag'])
            
    
    if not re.match('set.tag\:.*',args.action) and args.action != "display" and args.action != "set.log" and args.action != "set.log.profile" and args.action != "set.rule.disable" and args.action != "set.rule.enable" and args.action != "delete":
        print()
        print('The action is incorrect. Use --action help for details on how to use filters')
        print()
        exit()

def set_log(rule_name):
    url_log     = 'https://%s:9182/api/config/devices/device/%s/config/orgs/org-services/%s/security/access-policies/access-policy-group/%s/rules/access-policy/%s/set/lef/event' % (args.ip, args.device, args.org, args.group, rule_name)
    api_request     = requests.put(url_log, auth=(args.user, args.password), headers=HTTP_HEADER, data=payload_event, verify=False)
    print("--> setting log on rule "+rule_name)

def set_tag(rule_name,tag_value):
    url_log     = 'https://%s:9182/api/config/devices/device/%s/config/orgs/org-services/%s/security/access-policies/access-policy-group/%s/rules/access-policy/%s/tag' % (args.ip, args.device, args.org, args.group, rule_name)
    api_request     = requests.put(url_log, auth=(args.user, args.password), headers=HTTP_HEADER, data=json.dumps({ "tag": tag_value }), verify=False)
    print("--> setting tag "+str(tag_value)+" on rule "+rule_name)

def delete_tag(rule_name,tag_value):
    url_log     = 'https://%s:9182/api/config/devices/device/%s/config/orgs/org-services/%s/security/access-policies/access-policy-group/%s/rules/access-policy/%s/tag' % (args.ip, args.device, args.org, args.group, rule_name)
    api_request     = requests.delete(url_log, auth=(args.user, args.password), headers=HTTP_HEADER, data=json.dumps({ "tag": tag_value }), verify=False)
    print("--> setting tag "+tag_value+" on rule "+rule_name)

def set_log_profile(rule_name):
    url_profile = 'https://%s:9182/api/config/devices/device/%s/config/orgs/org-services/%s/security/access-policies/access-policy-group/%s/rules/access-policy/%s/set/lef/profile' % (args.ip, args.device, args.org, args.group, rule_name)
    api_request     = requests.put(url_profile, auth=(args.user, args.password), headers=HTTP_HEADER, data=payload_log_profile, verify=False)
    print("--> setting log profile on "+rule_name)

def disable_rule(rule_name):
    url_disable = 'https://%s:9182/api/config/devices/device/%s/config/orgs/org-services/%s/security/access-policies/access-policy-group/%s/rules/access-policy/%s/rule-disable' % (args.ip, args.device, args.org, args.group, rule_name)
    api_request     = requests.put(url_disable, auth=(args.user, args.password), headers=HTTP_HEADER, data=payload_rule_disable, verify=False)
    print("--> disabling rule "+rule_name)

def enable_rule(rule_name):
    url_enable = 'https://%s:9182/api/config/devices/device/%s/config/orgs/org-services/%s/security/access-policies/access-policy-group/%s/rules/access-policy/%s/rule-disable' % (args.ip, args.device, args.org, args.group, rule_name)
    api_request     = requests.put(url_enable, auth=(args.user, args.password), headers=HTTP_HEADER, data=payload_rule_enable, verify=False)
    print("--> enabling rule "+rule_name)

def delete_rule(rule_name):
    url_enable = 'https://%s:9182/api/config/devices/device/%s/config/orgs/org-services/%s/security/access-policies/access-policy-group/%s/rules/access-policy/%s' % (args.ip, args.device, args.org, args.group, rule_name)
    api_request     = requests.delete(url_enable, auth=(args.user, args.password), headers=HTTP_HEADER, verify=False)
    print("--> deleting rule "+rule_name)

def analyze_response_code(reponse_code , api_response):
    if not re.match('2\d\d',str(reponse_code)):
        print('')
        print('-> There is a problem with an API request')
        print('-> '+str(api_response))
        print('')
        exit()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, description='Script to change the settings of a VOS CPEs accross ALL its access policies')
    parser.add_argument('--ip', default='cloud221.versa-networks.com', type=str,help='IP address of Director')
    parser.add_argument('--device', default='BRANCH', type=str,help='Branch Device name')
    parser.add_argument('--org', default='Versa', type=str,help='Organization name')
    parser.add_argument('--group', default='Default-Policy', type=str,help='Policy Group Name')
    parser.add_argument('--user', default='*****', type=str,help='GUI username of Director')
    parser.add_argument('--password', default='*****', type=str,help='GUI password of Director')
    parser.add_argument('--action', default='display', type=str,help='Action to be taken on the offending rules. Use --action help for details')
    parser.add_argument('--filter', default='none', type=str,help='Filter to be applied to limit the scope of the action. Use --filter help for details')

    args = parser.parse_args()

    if args.filter == 'help':
        help_filter()

    if args.action == 'help':
        help_action()

    payload_event           = json.dumps({ "event" : "end" })
    payload_log_profile     = json.dumps({ "profile": "Default-Logging-Profile" })
    payload_no_log_profile  = json.dumps({ "profile": "" })
    payload_rule_disable    = json.dumps({ "rule-disable": "true" })
    payload_rule_enable     = json.dumps({ "rule-disable": "false" })

    url_all_rules   = 'https://%s:9182/api/config/devices/device/%s/config/orgs/org-services/%s/security/access-policies/access-policy-group/%s/rules/access-policy' % (args.ip, args.device, args.org, args.group)
    
    try:
        api_request     = requests.get(url_all_rules, auth=(args.user, args.password), headers=HTTP_HEADER, verify=False)
    except:
        print('')
        print('-> There is a problem reaching the API. Please verify your Credentials and:')
        print('--> The URL: '+ args.ip)
        print('--> The Organization Name: '+ args.org)
        print('--> The Device Name: '+ args.device)
        print('--> The Policy Group Name: '+ args.group)
        print('')      
        print('-> Use the help menu if needed:')
        print('--> python3 rules-edit.py -h')
        print('--> python3 rules-edit.py --action help')
        print('--> python3 rules-edit.py --filter help')
        print('')
        exit() 

    api_request     = requests.get(url_all_rules, auth=(args.user, args.password), headers=HTTP_HEADER, verify=False)
    api_response    = api_request.text
    reponse_code    = api_request.status_code
    analyze_response_code(reponse_code, api_response )

    json_output     = json.loads(api_response)
    filter          = args.filter

    for rule in json_output['access-policy']:
        exec_action(rule,filter)
