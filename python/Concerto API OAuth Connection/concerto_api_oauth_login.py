#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script to connect to Concerto API and obtain an access token."""

# Connects to Concerto API and obtains an access token
import json
import re  # pylint: disable=unused-import
import requests
from requests.packages import urllib3

# Surpresses an cert error that I was too lazy to fix
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
PYTHONWARNINGS = "ignore:InsecureRequestWarning"

# variables - change any that are different. Clear text passwords are bad.
# Replace everything inside of <<>>, with the correct information
USERNAME = "<<username>>"
PASSWORD = "<<password>>"
CLIENT_ID = "<<client_id>>"  # For concerto-demo.versa-networks.com is ""
CLIENT_SECRET = "<<client_secret>>"  # For concerto-demo.versa-networks.com is ""
# For concerto-demo.versa-networks.com is "https://concerto-demo.versa-networks.com"
CONCERTO_URL = "<<https://concerto-fqdn>>"


body = {"USERNAME": USERNAME, "PASSWORD": PASSWORD}

session = requests.Session()
# Gets X-CSRF-TOKEN (ECP-CSRF-TOKEN)
session.get(CONCERTO_URL, verify=False)
headers = {"X-CSRF-Token": session.cookies["ECP-CSRF-TOKEN"]}

# Logs in to the site
response = session.post(
    CONCERTO_URL + "/v1/auth/login",
    verify=False,
    cookies=session.cookies,
    headers=headers,
    json=body,
)
headers = {"X-CSRF-Token": session.cookies["ECP-CSRF-TOKEN"]}

body.update({"grant_type": "password", "CLIENT_ID": CLIENT_ID,
            "CLIENT_SECRET": CLIENT_SECRET})

# Gets the access token and saves it to the authorization key in headers
response = session.post(
    CONCERTO_URL + "/portalapi/v1/auth/token",
    verify=False,
    cookies=session.cookies,
    headers=headers,
    json=body,
)
headers.update({"Authorization": "Bearer " + response.json()["access_token"]})

# example get command using the access_token
response = session.get(
    CONCERTO_URL + "/portalapi/v1/inventory/view",
    verify=False,
    cookies=session.cookies,
    headers=headers,
)
print(json.dumps(response.json(), sort_keys=False, indent=4))
