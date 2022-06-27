#!/bin/bash
username="<<username>>" 
password="<<password>>"
client_id="<<client_id>>" # For concerto-demo.versa-networks.com is "concerto"
client_secret="<<client_secret>>" # For concerto-demo.versa-networks.com is "Concerto123@"
concerto_url="<<https://concert-fqdn>>" # For concerto-demo.versa-networks.com is "https://concerto-demo.versa-networks.com"
file_dir="<<directory>>" #format "/tmp/"
cookies_file="cookies.txt"
access_token_file="access_token"
cookies=${file_dir}${cookies_file} #No need to edit
access_token=${file_dir}${access_token_file} #No need to edit

curl -k -X GET "$concerto_url" -c "${cookies}" -s

curl -k -b "${cookies}" -X POST "${concerto_url}/v1/auth/login" -H "accept: application/json" -H "Content-Type: application/json" -H "X-CSRF-TOKEN: $(grep -w ECP-CSRF-TOKEN ${cookies} | cut -f 7)" -d "{ \"password\": \"${password}\", \"username\": \"${username}\"}" -c "${cookies}" -s

curl -k -b "${cookies}" -X POST "${concerto_url}/portalapi/v1/auth/token" -H "accept: application/json" -H "Content-Type: application/json" -H "X-CSRF-TOKEN: $(grep -w ECP-CSRF-TOKEN ${cookies} | cut -f 7)" -d "{ \"client_id\": \"${client_id}\", \"client_secret\": \"${client_secret}\", \"grant_type\": \"password\", \"password\": \"${password}\", \"username\": \"${username}\"}" > ${access_token}

sed -i -e 's/{"access_token":"//'  -e 's/".*$//' ${access_token}