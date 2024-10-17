# Automation Script to fire Bulk APIs to Director Templates

# /Devices

```
Author Arun Chandar
```
Purpose

This article will help to fire Bulk APIs to Director at one go with minimalistic effort.

Requisites:

The following requisites should be met:

1. Python installed
2. Python subprocess module installed
3. curl installed
4. Director reachable over port 9182
5. Ubuntu Machine/Windows
6. Replace Password in the Code with your password @<<Enter Password>>

Working:

Lets take an example to import a list of local user database information on to the Template. To achieve this, we
need to identify the right API data that would be used while creating users on the Director. For example, when
the POST request gets triggered, the following data would be triggered for the local database creation:

```
API Data
```
```
{"user":{"name":"test5","passwd":"Test1234@","status":"CREATED"}}
```
To automate with multiple bulk requests use the attached csv file userdatabase-conversion.csv. Fill in the
required user name in column - B and Password in column F as below:


Once the required data is created, copy paste all the contents of the csv file to a text file:

Save the file, the rest of the formatting and firing of APIs will be taken care by the Script.

Next, download the script bulk-api-automation.py. On Ubuntu or Windows place the txt file and the script (.py)
file on to the same directory:

Change the credentials of your Director in the script as below:


Now, we can run the script. When executed, the script will ask for the API data filename. This filename is the
file that actually contents the data to be created when the APIs gets triggered as below.

Once the file name is triggered, the script will sanitise and format into the correct format which can then be
used as data feeds while triggering post requests to the director as below:

Next input the API URL associated to your director. For example, the below url would be used to create local
user-database on to a particular template:

```
API URL for Local User Database
```
```
https://<<Director-IP>>:9182/api/config/devices/template/<<Template-Name>/config/orgs/org-services/<<ORG-NAME>>
/user-identification/local-database/users
```
Press enter and the script will start to construct the API requests based on the no.of data inputs available on
the txt file and the script will start firing Bulk APIs based on the inputs given. The HTTP- 201 code indicates
that the user has been successfully created on the Director:


Now, we can check the same in the Director to verify if all the users has been successfully created on the
respective templates:

The same logic can be applied for other use cases as well with minimal effort spent on identifying the correct
APIs to construct the csv file and then using it as a txt file. This approach has been successfully used while
creating multiple QoS configurations, creating huge list of services, Addresses, Firewall rules etc in SCB & AMP
deployments.
