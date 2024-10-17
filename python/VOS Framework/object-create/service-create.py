import ssl
import re
import json
import requests
import csv
import urllib3
import argparse
import sys

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

STR_POST_SERVICE_TEMPLATE_OK            = '[->] service %s for template %s was created with status code %s'
STR_POST_SERVICE_TEMPLATE_NOK           = '[!!] service %s for template %s was not created. Verify the service attributes. Status code %s.\n[!!] Error: %s\n' 
STR_POST_SERVICE_DEVICE_OK              = '[->] service %s for device %s was created with status code %s'
STR_POST_SERVICE_DEVICE_NOK             = '[!!] service %s for device %s was not created. Verify the service attributes. Status code %s.\n[!!] Error: %s\n'

STR_CONNEXION_ERROR                     = '\n[!!] Could not connect to %s\n'
STR_FILE_ERROR                          = '\n[!!] Could not find the file %s\n'

URL_POST_SERVICE_DEVICE                 = 'https://%s:9182/api/config/devices/device/%s/config/orgs/org-services/%s/objects/services'
URL_POST_SERVICE_TEMPLATE               = 'https://%s:9182/api/config/devices/template/%s/config/orgs/org-services/%s/objects/services'
URL_GET_SERVICE_TEMPLATE                = 'https://%s:9182/api/config/devices/template/%s/config/orgs/org-services/%s/objects/services/service'

HTTP_HEADER                             = {"Content-Type": "application/json", "Accept": "application/json"}
JSON_PAYLOAD                            = '{"service":{"name":"%s","protocol":"%s","%s":"%s"}}'

def get_get_service_list():
  template_name = args.target.split(':',1)[1]
  url_get_template      = URL_GET_SERVICE_TEMPLATE % (args.ip, template_name, args.org)
  api_request           = requests.get(url_get_template, auth=(args.user, args.password), headers=HTTP_HEADER, verify=False)
  template_json         = api_request.text
  print(template_json)


def post_service(payload):
    try:
        if re.match('device\:.*',args.target):
            device_name         = args.target.split(':',1)[1]
            url                 = URL_POST_SERVICE_DEVICE % (args.ip, device_name, args.org)
            api_request         = requests.post(url, auth=(args.user, args.password), headers=HTTP_HEADER, data=payload.encode('utf-8'), verify=False)
            api_response        = api_request.text
            api_status_code     = api_request.status_code
            service_name        = json.loads(payload)['service']['name']

            if re.match('2\d\d', str(api_status_code)):
                print(STR_POST_SERVICE_DEVICE_OK % (service_name, device_name, api_status_code))
            else:
                error_message = api_request.json()
                print(STR_POST_SERVICE_DEVICE_NOK % (service_name, device_name, api_status_code, error_message))


        if re.match('template\:.*',args.target):
            template_name       = args.target.split(':',1)[1]
            url                 = URL_POST_SERVICE_TEMPLATE % (args.ip, template_name, args.org)
            api_request         = requests.post(url, auth=(args.user, args.password), headers=HTTP_HEADER, data=payload.encode('utf-8'), verify=False)
            api_response        = api_request.text
            api_status_code     = api_request.status_code
            service_name        = json.loads(payload)['service']['name']
            
            if re.match('2\d\d', str(api_status_code)):
                print(STR_POST_SERVICE_TEMPLATE_OK % (service_name, template_name, api_status_code))
            else:
                error_message = api_request.json()
                print(STR_POST_SERVICE_TEMPLATE_NOK % (service_name, template_name, api_status_code, error_message))
            

    except (requests.exceptions.Timeout, requests.ConnectionError):
        sys.exit(STR_CONNEXION_ERROR % (args.ip))

if __name__ == '__main__':

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, description='A script to create service objects on Versa Director from a CSV file')
    parser.add_argument('--ip', default='xxxx.versa-networks.com', type=str,help='IP address of Director')
    parser.add_argument('--target', default='device:BRANCH-11', type=str,help='Device (device:XXX) or Device Template (template:XXX) where the service must be created.')
    parser.add_argument('--org', default='Versa', type=str,help='Organization name')
    parser.add_argument('--user', default='Administrator', type=str,help='GUI username of Director')
    parser.add_argument('--password', default='xxxx', type=str,help='GUI password of Director')
    parser.add_argument('--csv_file', default='service-create.csv', type=str,help='CSV File including the services')
    
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

        service_name           = row[0]
        service_protocol       = row[1]
        service_port           = row[2]

        if re.match('[0-9]+\-[0-9]+',service_port):
            payload = JSON_PAYLOAD % (service_name,service_protocol,'port',service_port)
        elif re.match('[0-9]+\,[0-9]+',service_port):
            payload = JSON_PAYLOAD % (service_name,service_protocol,'port',service_port)
        else:
            payload = JSON_PAYLOAD % (service_name,service_protocol,'destination-port',service_port)

        payload_list.append(payload)

    for service in payload_list:
        post_service(service)
