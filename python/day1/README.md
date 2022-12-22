# GENERAL

The automation scripts are written in python and are meant to be executed on a Director. The scripts allow you to provision the Director and the Controller.


# PRE-REQUISITE

1. Validate if proper packages are present on Old Director and New Director:
        Check required packages for python2: `dpkg -l | grep -E "jinja2|requests" | grep python-`
        Check required packages for `python3: dpkg -l | grep -E "jinja2|requests" | grep python3-`
       Case1: Both packages are present for python3:
        `dpkg -l | grep -E "jinja2|requests" | grep python3-
        ii  python3-jinja2   2.10-1ubuntu0.18.04.1  all          small but fast and easy to use stand-alone template engine
        ii  python3-requests 2.18.4-2ubuntu0.1  all          elegant and simple HTTP library for Python3, built for human beings`

	    Case2: Both packages are present for python2:
        `dpkg -l | grep -E "jinja2|requests" | grep python-
        ii  python-jinja2   2.7.2-2ubuntu0.1~esm1 all  small but fast and easy to use stand-alone template engine
        ii  python-requests 2.2.1-1ubuntu0.4      all          elegant and simple HTTP library for Python, built for human beings
        ii  python-requests-whl 2.2.1-1ubuntu0.4  all          elegant and simple HTTP library for Python, built for human beings`

	    Case3: One or more packages are missing for both python2 and python3

   Resolution:
    Case1: NO changes are Needed.
    Case2: Issue the following command:
           `sed -i 's/#!\/usr\/bin\/env python3/#!\/usr\/bin\/env python2/g' *.py`
    Case3: Download the latest OSSPACK Director bin file from Versa site on New Director and retry the 2 `dpkg` commands again. If they are still missing contact Versa.

2. Validate Connectivity:
 The scripts need access to both the Directors using Rest API. This must be verified before execution:
   Local RestAPI port:
   `telnet 192.168.236.2 9182
       Trying 192.168.236.2...
       Connected to 192.168.236.2...`

# Installation of Files
Download the repository.
1. Checks the presence of file: 
	`ls *.py *.json  
   day1.py example_day1.json`
   2. Presence of Directory:
       `ls -d */
       21.2.2`
   3. Presence of Directory:
        `ls -l 21.2.2/ | wc -l
        55``
    4. Carefully change the `example_day1.json` file with appropriate values. This is very **Important**
  
# DESIGN:
The program reads files from the directory 21.2.2 and executes corresponding RESTAPI to the Director for provisioning.
The files in the directory are named in a particular way to allow sequencing of the RestAPI. So a change in the naming 
easily allows one to alter the sequencing to the RestAPIs. If there are files that do not follow the naming convention
then they are ignored -- this is done purposefully so the user can manipulate the inputs. The program uses Jinja 
templating techniques to fill in required values provided in the json file.  Logging to stdout and files are provided.   

# EXECUTION:
  `./day1.py -f example_day1.json
  ./day1.py -h ` For help
  
