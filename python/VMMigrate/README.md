GENERAL:
The automation scripts are written in python and are meant to be executed on the Old or New Director.

PREQUISITE:
1) Validate if proper packages are present on Old Director and New Director:
	Check required packages for python2: dpkg -l | grep -E "jinja2|requests" | grep python-  
	Check required packages for python3: dpkg -l | grep -E "jinja2|requests" | grep python3-  
   e.g.
    Case1: Both packages are present for python3: 
    	dpkg -l | grep -E "jinja2|requests" | grep python3-
        ii  python3-jinja2   2.10-1ubuntu0.18.04.1  all          small but fast and easy to use stand-alone template engine
        ii  python3-requests 2.18.4-2ubuntu0.1  all          elegant and simple HTTP library for Python3, built for human beings

    Case2: Both packages are present for python2: 
    	dpkg -l | grep -E "jinja2|requests" | grep python-
        ii  python-jinja2   2.7.2-2ubuntu0.1~esm1 all  small but fast and easy to use stand-alone template engine
	ii  python-requests 2.2.1-1ubuntu0.4      all          elegant and simple HTTP library for Python, built for human beings
        ii  python-requests-whl 2.2.1-1ubuntu0.4  all          elegant and simple HTTP library for Python, built for human beings

    Case3: One or more packages are missing for both python2 and python3
    
   Resolution:
    Case1: NO changes are Needed.
    Case2: Issue the following command:
           sed -i 's/#!\/usr\/bin\/env python3/#!\/usr\/bin\/env python2/g' *.py
    Case3: Download the latest OSSPACK Director bin file from site: https://download.versa-networks.com/index.php/s/nEkF9xOO3e7BA9Z
           on New Director and retry the 2 dpkg commands again. If they are still missing contact Product Engineering.

2) Validate Connectivity: The scripts need access to both the Directors using Rest API. This must be verified before execution:
   Local RestAPI port:
       telnet 192.168.236.2 9182 
       Trying 192.168.236.2...
       Connected to 192.168.236.2.
   Remote RestAPI port:
       telnet 192.168.236.146 9182
       Trying 192.168.236.146...
       Connected to 192.168.236.146.
3) Access to admin user: 
   The user of the scripts must have ssh access to the Director and Director must not be using TACACS Authentation for the user.
   See details in the document.
4) Intallation of the scripts:
   cd $HOME
   tar zxvf VMMigrate.tar.gz
   cd VMMigr
   cat README
   Verify the following:
    a) Presence of python files: 
       ls *.py
       common.py  glbl.py  test_single.py  VMMigr_phase1.py  VMMigr_phase2.py  VMMigr_phase3.py
    b) Presence of python files: 
       ls *.json
       example_vm_phase2.json  example_vm_phase3.json  vm_phase1.json
    c) Presence of Directory:
       ls -d */
       in_phase1/
    d) Presence of file in in_phase1 directory:
       ls -l in_phase1/ | wc -l
       35


EXECUTION:

1) Open Terminal (preferably xterm) and Log onto the Director and change Directory.
2) Export variables: This is optional
   export LINES=$(LINES) 
   export COLUMNS=$(COLUMNS)
3) Change vm_phase1.json. Please read document. THIS IS AN IMPORTANT STEP. Please do this carefully. 
4) Run various phases:
    ./VMMigr_phase1.py -f vm_phase1.json
5) Proceed with directions from Document
