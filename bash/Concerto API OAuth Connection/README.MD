# Automation Script that creates an Access Token for logging in to Concerto API

```
Author Rob Kauffman
```

Purpose

This article will help to connect to the Concerto API and give you an access token to be used with future Concerto API connections

Requisites:

The following requisites should be met:

1. curl installed
2. Concerto reachable over port 443
3. Ubuntu Machine/Windows

Tested on
Ubuntu 20.04 LTS
Curl 7.68.0
Concerto 11.2.1

Working:

Concerto requires OAuth authentication with a Bearer Access token for most actions. This script will log you in and create the access token for use with out API methods.

```
Vairables
```

Replace everything inside of <<>>, with the correct information
username="<<username>>"
password="<<password>>"
client_id="<<client_id>>" # For concerto-demo.versa-networks.com is "concerto"
client_secret="<<client_secret>>" # For concerto-demo.versa-networks.com is ""
concerto_url="<<https://concerto-fqdn>>" # For concerto-demo.versa-networks.com is "https://concerto-demo.versa-networks.com"
file_dir="<<directory>>" #format "/tmp/"
cookies_file="cookies.txt"
access_token_file="access_token"
cookies=${file_dir}${cookies_file} #No need to edit
access_token=${file_dir}${access_token_file} #No need to edit

Use of Access Token
The access token needs to be passed to the server as a header. Key:Authorization Value: Bearer<<contents of access_token file>>. Cookies from the the script allso need to be passed to the server.

Example
curl -k -b "/tmp/cookies.txt" -H "Authorization: Bearer $(grep -w ".\*" /tmp/access_token)" -X GET "https://concerto-demo.versa-networks.com/portalapi/v1/inventory/view"
