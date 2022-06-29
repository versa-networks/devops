#!/bin/bash
username="<<username>>"
password="<<password>>"
client_id="<<client_id>>"              # For concerto-demo.versa-networks.com is ""
client_secret="<<client_secret"        # For concerto-demo.versa-networks.com is ""
concerto_url="https://concerto-fqdn>>" # For concerto-demo.versa-networks.com is "https://concerto-demo.versa-networks.com"
file_dir="/tmp/"                       # format "/tmp/"
cookies_file="cookies.txt"
access_token_file="access_token"

while getopts n:p:i:s:u:d:c:a: flag; do
    case "${flag}" in
    n) username=${OPTARG} ;;
    p) password=${OPTARG} ;;
    i) client_id=${OPTARG} ;;
    s) client_secret=${OPTARG} ;;
    u) concerto_url=${OPTARG} ;;
    d) file_dir=${OPTARG} ;;
    c) cookies_file=${OPTARG} ;;
    a) access_token_file=${OPTARG} ;;
    \?)
        echo "Invalid Option: -$OPTARG" 1>&2
        exit 1
        ;;
    esac
done

printf "Username:                     %s\n" "$username"
printf "Password:                     ********\n"
printf "Client ID:                    %s\n" "$client_id"
printf "Client Secret:                %s\n" "$client_secret"
printf "Concerto URL:                 %s\n" "$concerto_url"
printf "File Directory:               %s\n" "$file_dir"
printf "Cookies Filename:             %s\n" "$cookies_file"
printf "Access Token Filename:        %s\n" "$access_token_file"
printf "\n\n"

cookies=${file_dir}${cookies_file}             #No need to edit
access_token="${file_dir}${access_token_file}" #No need to edit

curl -k -X GET "$concerto_url" -c "${cookies}" -s
printf "\n\n"

curl -k -b "${cookies}" -X POST "${concerto_url}/v1/auth/login" -H "accept: application/json" -H "Content-Type: application/json" -H "X-CSRF-TOKEN: $(grep -w ECP-CSRF-TOKEN "${cookies}" | cut -f 7)" -d "{ \"password\": \"${password}\", \"username\": \"${username}\"}" -c "${cookies}" -s
printf "\n\n"

curl -k -b "${cookies}" -X POST "${concerto_url}/portalapi/v1/auth/token" -H "accept: application/json" -H "Content-Type: application/json" -H "X-CSRF-TOKEN: $(grep -w ECP-CSRF-TOKEN "${cookies}" | cut -f 7)" -d "{ \"client_id\": \"${client_id}\", \"client_secret\": \"${client_secret}\", \"grant_type\": \"password\", \"password\": \"${password}\", \"username\": \"${username}\"}" >"${access_token}"
printf "\n\n"

sed -i -e 's/{"access_token":"//' -e 's/".*$//' "${access_token}"

printf "\n\nCookies and Access Token can be found in %s\n\n" "${file_dir}"
