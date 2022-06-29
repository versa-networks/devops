#! /bin/bash
username="rkauffman"
password="8nBvDA5jVd9RDcx%"
client_id="concerto" # For concerto-demo.versa-networks.com is "concerto"
client_secret="Concerto123@" # For concerto-demo.versa-networks.com is "Concerto123@"
concerto_url="https://concerto-demo.versa-networks.com" # For concerto-demo.versa-networks.com is "https://concerto-demo.versa-networks.com"
file_dir="/tmp/" #format "/tmp/"
cookies_file="cookies.txt"
access_token_file="access_token"

while getopts u:p:ci:cs:url:d:c:at: flag
do
   case "${flag}" in
        u) username=${OPTARG};;
        p) password=${OPTARG};;
       ci) client_id=${OPTARG} ;;
       cs) client_secret=${OPTARG};;
        u) concerto_url=${OPTARG};;
        d) file_dir=${OPTARG};;
        c) cookies_file=${OPTARG};;
        a) access_token_file=${OPTARG};;
   esac
done

echo "Username:                     $username";
echo "Password:                     ********";
echo "Client ID:                    $client_id";
echo "Client Secret:                $client_secret";
echo "Concerto URL:                 $concerto_url";
echo "File Directory:               $file_dir";
echo "Cookies Filename:             $cookies_file";
echo "Access Token Filename:        $access_token_file";
printf "\n\n"

cookies=${file_dir}${cookies_file} #No need to edit
access_token="${file_dir}${access_token_file}" #No need to edit

curl -k -X GET "$concerto_url" -c "${cookies}" -s
printf "\n\n";

curl -k -b "${cookies}" -X POST "${concerto_url}/v1/auth/login" -H "accept: application/json" -H "Content-Type: application/json" -H "X-CSRF-TOKEN: $(grep -w ECP-CSRF-TOKEN "${cookies}" | cut -f 7)" -d "{ \"password\": \"${password}\", \"username\": \"${username}\"}" -c "${cookies}" -s
printf "\n\n";

curl -k -b "${cookies}" -X POST "${concerto_url}/portalapi/v1/auth/token" -H "accept: application/json" -H "Content-Type: application/json" -H "X-CSRF-TOKEN: $(grep -w ECP-CSRF-TOKEN "${cookies}" | cut -f 7)" -d "{ \"client_id\": \"${client_id}\", \"client_secret\": \"${client_secret}\", \"grant_type\": \"password\", \"password\": \"${password}\", \"username\": \"${username}\"}" > "${access_token}"
printf "\n\n";

sed -i -e 's/{"access_token":"//'  -e 's/".*$//' "${access_token}"

printf "\n\nCookies and Access Token can be found in ${file_dir}\n\n";