Purpose:
 The purpose of this script is to get the OAuth access token and refresh token from the Versa Director for a specified user.
 
 Usage:
 The script requires the following information -
 1. Versa Director FQDN or IP address
 2. Username
 3. Password
 4. Client ID
 5. Client Secret
 
 On the Versa Director, a new OAuth client can be created by navigating to navigating to Administration --> System --> Authorization --> Clients.  Once the new client is created, the client id and secret will be displayed that you can also download as a json file.
 
 On entering the required information, the script will print the access token and refresh token.  In addition, the script will also print the complete output in json format.
 
 The script was tested on python3.5 and Versa Director version 22.1.2.
 
 For more details about OAuth tokens and how they can be used in REST API's, refer the following documentation - https://docs.versa-networks.com/Management_and_Orchestration/Versa_Director/Director_REST_APIs/01_Versa_Director_REST_API_Overview