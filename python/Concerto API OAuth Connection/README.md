# **Concerto API OAuth Connection**

## Description

Automation Script that creates an Access Token for logging in to Concerto API

<!-- ## Getting Started-->

## Dependencies

1. Python Installed
2. Concerto reachable over port 443

<!-- ### Installing-->

<!-- ### Executing program-->

<!-- ## Help-->

## Purpose

This article will help to connect to the Concerto API and give you an access token to be used with future Concerto API connections

## Tested on

- Windows 11
- Python 3.10.5
- Concerto 11.2.1

## What it does

Concerto requires OAuth authentication with a Bearer Access token for most actions. This script will log you in and create the access token for use with out API methods.

## Variables

Replace everything inside of << >>, with the correct information

```Python3

username="<<username>>"
password="<<password>>"
client_id="<< client_id >>" # For concerto-demo.versa-networks.com is ""
client_secret="<< client_secret >>" # For concerto-demo.versa-networks.com is ""
concerto_url="<< https://concerto-fqdn >>" # For concerto-demo.versa-networks.com is "https://concerto-demo.versa-networks.com"

```

## Use of Access Token

The access token needs to be passed to the server as a header.

> Key:Authorization  
> Value: Bearer << contents of access_token file >>  
> Cookies from the the script also need to be passed to the server.

## Example get command using the access_token

```Python3

response = session.get(concerto_url+"/portalapi/v1/inventory/view", verify=False, cookies=session.cookies, headers=headers)
print(json.dumps(response.json(), sort_keys=False, indent=4))

```

## Authors

Rob Kauffman (rkauffman@versa-networks.com)

## Version History

- 0.1
  - Initial Release
  - Date 06/29/2022

## License

No license

## Acknowledgments
