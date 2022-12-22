# This is a Postman collection to demonstrate the Versa Director REST API capability.

```
Author Rengaramalingam A
```

```
Purpose
```

This collection will help to connect to the Versa Director over REST API and run multiple GET operations

```
Requisites:
```

The following requisites should be met:

1. Postman Installed Installed
2. Versa Director reachable over port 9182

```
Tested on
Windows 11
Postman v9.24.0
Versa Director 21.2.2
```

Working:

We have created a postman collection to showcase Versa Director REST API capability and use cases. The initial version has non-service impacting GET REST API calls with Postman Visualizer [Using HTML, CSS, and JavaScript] to visualize our REST API request responses, custom test scripts to process response data, custom Postman console logging, scripts to support postman runner and much more. 

REST API Calls:
++++++++++++++
•	List Director Package info
•	List ALL Organizations
•	GET ALL Appliance Basic details
•	GET ALL Appliance detailed view
•	GET SPACK details of ALL Appliances
•	GET OssPack details of ALL Appliances
•	GET alarms summary
•	GET Parent-Org Template Names
•	Get System Uptime
•	Get Versa Director Audit logs


```
Vairables
```

You will edit these variable in Postman under environments
	"auth": {
		"type": "basic",
		"basic": {
			"username": "rengar",
			"password": "BestSDWAN1+"
		}
	}
	
Update url with the Versa Director IP address	
