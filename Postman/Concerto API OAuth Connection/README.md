# Automation Script that creates an Access Token for logging in to Concerto API

```
Author Rob Kauffman
```

```
Purpose
```

This article will help to connect to the Concerto API and give you an access token to be used with future Concerto API connections

```
Requisites:
```

The following requisites should be met:

1. Postman Installed Installed
2. Concerto reachable over port 443

```
Tested on
Windows 11
Postman 9.23.0
Concerto 11.2.1
```

Working:

Concerto requires OAuth authentication with a Bearer Access token for most actions. This script will log you in and create the access token for use with out API methods.

```
Vairables
```

You will edit these variable in Postman under environments
{
"key": "Concerto_Username",
"value": "<<username>>",
"enabled": true
},
{
"key": "Concerto_Password",
"value": "<<password>>",
"type": "secret",
"enabled": true
},
{
"key": "client_id",
"value": "<<client_id>>", # For concerto-demo.versa-networks.com is ""
"type": "default",
"enabled": true
},
{
"key": "client_secret",
"value": "<<client_secret>>", # For concerto-demo.versa-networks.com is ""
"type": "secret",
"enabled": true
},
{
"key": "Concerto_URL",
"value": "<<https://concerto-fqdn>>", # For concerto-demo.versa-networks.com is "https://concerto-demo.versa-networks.com"
"type": "default",
"enabled": true
}

Use of Access Token
The access token needs to be passed to the server as a header. Key:Authorization Value: Bearer<<contents of access_token file>>. Cookies from the the script allso need to be passed to the server.

```
Import
```

1. Open Postman (This was tested on 9.22.3)
2. Create a workspace (skip this if you want it in an existing workspace)
3. Click Import
   a. Click “Upload Files” then select “Versa-Cloud-Demo.postman_environment.json” and click “Import”
4. Double Click “Versa-Cloud-Demo” (you can rename this)
   a. Change the passwords for Concerto_Password (do this in initial and current value)
   b. If you are not connecting to https://concerto-demo.versa-networks.com, then you will need to verify
   i. Concerto_URL
   ii. client_id
   iii. client_secret
   c. Click Save (Don’t forget to do this, save is in the upper right corner
5. Click Import
   a. Click “Upload Files” then select “Concerto API.postman_collection.json” and click “Import”
   b. This is a large collection, and you most likely will get an error. Ignore the error and wait 5 minutes. The collection should be there; if it isn’t, switch to a different workspace and change back.
6. Place the collection in the same environment that contains the variables.

Testing

1. Click on “Console” in the bottom left.
2. Click “Concerto API”
3. Click “1 – Log On”
4. Click “Run”
5. Make sure that the following are checked and, in this order:
   a. CSRF Token
   b. Login
   c. Get-Oauth-Access-Token
   d. Save Response
   i. Default is unchecked
6. Click “Run Concerto API”
7. In the Console at the bottom, you can see if it was completed successfully by verifying there is no red on the last three (3) tasks.
   a. The warning of “Unable to verify the first certificate” can be ignored
8. Click on Environment -> Versa-Cloud-Demo
9. If access_token Current Value has a value, you are ready to go.

Moving forward
The folder “Concerto” can be ignored or deleted.
The folder “v1” is an import from https://concerto-demo.versa-networks.com/portalapi/swagger-ui.html.
