#!/usr/bin/env python3

import requests
import json
from pprint import pprint
import ssl
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

van_ip=""

#Change IP and username/password(GUI): this can be any analytics IP 
login_url = "https://"+str(van_ip)+":8443/versa/login?username=admin&password=versa123"
logout_url = "https://"+str(van_ip)+":8443/versa/logout"

session = requests.session()
session.headers.update(
    {"Content-type": "application/json", "Accept": "application/json"}
)
response = session.get(login_url, verify=False)
token = response.headers.get("x-csrf-token", "")

if token != "":
    session.headers.update({"X-CSRF-TOKEN": token,})

response = session.post(login_url, verify=False)

url1 = "https://"+str(van_ip)+":8443/versa/analytics/nodes/status"

response1 = session.get( url1 )
data = json.loads(response1.content)
pprint(data)

response = session.get(logout_url)

#Now you are logged in to analyatics node.