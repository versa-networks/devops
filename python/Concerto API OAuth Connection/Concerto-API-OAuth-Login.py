# Connects to Concerto API and obtains an access token
import json
import re
import requests
from requests.packages import urllib3

# Surpresses an cert error that I was too lazy to fix
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
PYTHONWARNINGS = "ignore:InsecureRequestWarning"

# variables - change any that are different. Clear text passwords are bad.
# Replace everything inside of <<>>, with the correct information
username = "<<username>>"
password = "<<password>>"
client_id = "<<client_id>>"  # For concerto-demo.versa-networks.com is "concerto"
# For concerto-demo.versa-networks.com is "Concerto123@"
client_secret = "<<client_secret>>"
# For concerto-demo.versa-networks.com is "https://concerto-demo.versa-networks.com"
concerto_url = "<<https://concerto-fqdn>>"

body = {
    'username': username,
    'password': password
}

session = requests.Session()
# Gets X-CSRF-TOKEN (ECP-CSRF-TOKEN)
session.get(concerto_url, verify=False)
headers = {'X-CSRF-Token': session.cookies['ECP-CSRF-TOKEN']}

# Logs in to the site
response = session.post(concerto_url+"/v1/auth/login", verify=False,
                        cookies=session.cookies, headers=headers, json=body)
headers = {'X-CSRF-Token': session.cookies['ECP-CSRF-TOKEN']}

body.update({
    'grant_type': "password",
    'client_id': client_id,
    'client_secret': client_secret
})

# Gets the access token and saves it to the authorization key in headers
response = session.post(concerto_url+"/portalapi/v1/auth/token",
                        verify=False, cookies=session.cookies, headers=headers, json=body)
headers.update({'Authorization': "Bearer "+response.json()["access_token"]})

# example get command using the access_token
response = session.get(concerto_url+"/portalapi/v1/inventory/view",
                       verify=False, cookies=session.cookies, headers=headers)
print(json.dumps(response.json(), sort_keys=False, indent=4))
