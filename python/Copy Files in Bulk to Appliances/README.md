Tool to push files to devices in Bulk
==========================================================

 **Author**            [Gerardo Melesio (gerardo@versa-networks.com)] 

  ---------------------------------
  -   #### **Purpose and usage**
  
  -   #### **User guide**
  
  -   #### **Future development**
  
  ---------------------------------

#### **Purpose and usage:**

This tool helps you to push a URL File to multiple devices at once. It has a cli interface that lets you run different options and also a Config file when you can set different parameters for the operation.

The tool is coded to run in Python3.


#### **User Guide:**

The tool is compromised by three files:
-   install.sh:  	Excutable file that helps you install all the pip dependancies.

- 	config.yaml: 	Configuration file, where you specify set parameters for the tool's operation. You need to set the following parameters:
	-   director-ip: 	The IP or FQDN of the Director where you intend to perform the operations
	-	disable-ping: 	A flag. If set to true, the Tool will perform an initial validation of the reachability to the Director.
	-   url-file: 		Name of the URL file you intend to push to the devices

- 	main.py:		Main piece of code. When ran, it displays a cli interface, with the following commands:
	-	show_devices <ORG>
		'Show the sites onboarded to Director for a particular Tenant (For up to 200 devices). Expects a value for the Tenant name'
	-	push_urlf_all <ORG>
		'Push the file specified in the CONFIG file to all the Devices in the specified Org (passed as an argument)'
	-	exit
		'Exit to Shell'		


#### **Future developement:**

Some planed improvements for the tool are:
-	Options to push other kinds of files like certificates, IP Files, keys, etc.
-	Options to set a list of devices wher the file wants to be pushed, instead of doing it generally to the ORG.
