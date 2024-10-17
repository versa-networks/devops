import requests
import json
import getpass

director = input("Enter the Versa Director fqdn or IP address: ")
username = input("Username: ")
password = getpass.getpass()
client_id = input("Client ID: ")
client_secret = input("Client Secret: ")
grant_type = "password"

# Strip leading and trailing spaces in the variable
n_director = director.strip()
n_username = username.strip()
n_client_id = client_id.strip()
n_client_secret = client_secret.strip()

headers = {'Content-type': 'application/json', 'Accept': 'application/json'}

#Create the Versa API URL request
https = "https://"
auth_token__part = ':9182/auth/token'

data = json.dumps({
    "grant_type": grant_type,
    "client_id": n_client_id,
    "client_secret": n_client_secret,
    "username": n_username,
    "password": password
})


versa_auth_token_api = (https + n_director + auth_token__part )

#Send the API to get the token
try:
   auth_response = requests.post(versa_auth_token_api, headers=headers, data=data)
   auth_response.raise_for_status()  # Raise an exception for HTTP errors

except Exception as e:
   print('Request failed with error: ', str(e))

# Read token from auth response
if auth_response.status_code == 200:
   auth_response_json = auth_response.json()
   auth_token = auth_response_json["access_token"]
   refresh_token = auth_response_json["refresh_token"]
   print ()
   print ('Access token: ', auth_token)
   print ()
   print ('Refresh token: ', refresh_token)
   print ()
   print ('Full output of API response in json format is: ')
   print (json.dumps(auth_response_json, indent=4))

  
