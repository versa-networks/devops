# GENERAL:

The automation scripts are written in python and are meant to be executed on the Old or New Director.
The scripts rely on certain packages to be present for it to work (see detail in the PRE-REQUISITE section).
Finally, the script needs access to both the OLD-Director and the NEW-Director. The script has some limitations which are listed below:

# PRE-REQUISITE:

1.  Validate if proper packages are present on Old Director and New Director:
    Check required packages for python2: dpkg -l | grep -E "jinja2|requests" | grep python-
    Check required packages for python3: dpkg -l | grep -E "jinja2|requests" | grep python3-
    e.g.
    Case1: Both packages are present for python3:

        dpkg -l | grep -E "jinja2|requests" | grep python3-
        ii  python3-jinja2   2.10-1ubuntu0.18.04.1  all          small but fast and easy to use stand-alone template engine
        ii  python3-requests 2.18.4-2ubuntu0.1  all          elegant and simple HTTP library for Python3, built for human beings

    Case2: Both packages are present for python2:
    dpkg -l | grep -E "jinja2|requests" | grep python-
    ii python-jinja2 2.7.2-2ubuntu0.1~esm1 all small but fast and easy to use stand-alone template engine
    ii python-requests 2.2.1-1ubuntu0.4 all elegant and simple HTTP library for Python, built for human beings
    ii python-requests-whl 2.2.1-1ubuntu0.4 all elegant and simple HTTP library for Python, built for human beings

    Case3: One or more packages are missing for both python2 and python3

## Resolution:

    Case1: NO changes are Needed.
    Case2: Issue the following command:
        sed -i 's/#!\/usr\/bin\/env python3/#!\/usr\/bin\/env python2/g' *.py
    Case3: Download the latest OSSPACK Director bin file from site: https://download.versa-networks.com/index.php/s/nEkF9xOO3e7BA9Z
                   on New Director and retry the 2 dpkg commands again. If they are still missing contact Versa

2. Validate Connectivity: The scripts need access to both the Directors using Rest API. This must be verified before execution:
   Local RestAPI port:
   telnet 192.168.236.2 9182
   Trying 192.168.236.2
   Connected to 192.168.236.2

   Remote RestAPI port:
   telnet 192.168.236.146 9182
   Trying 192.168.236.146
   Connected to 192.168.236.146.

3. Access to admin user:
   The user of the scripts must have ssh access to the Director and Director must not be using TACACS Authentation for the user.

4. Installation of the scripts:
   cd $HOME
   tar zxvf VMMigrate.tar.gz
   cd VMMigr
   cat README
   Verify the following:
   a. Presence of python files:
   ls _.py
   common.py glbl.py test_single.py VMMigr_phase1.py VMMigr_phase2.py VMMigr_phase3.py
   b. Presence of python files:
   ls _.json
   example_vm_phase2.json example_vm_phase3.json vm_phase1.json
   c. Presence of Directory:
   ls -d \*/
   in_phase1/
   d. Presence of file in in_phase1 directory:
   ls -l in_phase1/ | wc -l
   35

# DESIGN:

The execution of the scripts is broken down into 3 phases:

## Phase1 :

In this phase, the script works on both the NEW-Dir and OLD-Dir. On the NEW-Dir, the script gathers all the details of the already instantiated Controller Complex e.g. the DNS servers, NTP data etc. It also gathers the detailed configuration of the Controllers. It uses GET RestAPIs to gather each of this information and creates files (a separate file for each such query). These file are store in a directory called in_phase2 and are used by the script in the next phase. Finally, the script creates a backup of the NEW-Dir which can be used in case of a disaster.

## Phase2 :

In this phase the script ONLY works on the NEW-Dir. In this phase the primary tasks are to
a. Delete the Controllers that have been created by the OLD Directors backup
b. Create the Controllers that were originally present on the NEW-Dir. Verification that a device is in sync and adding
additional configuration (e.g. org-services data that was originally present)
c. Deploy the Workflow Templates (with the New Controller present) for each template. It goes through the Workflow templates
and deploys them. In case there are errors, they are shown clearly to the end user
d. Deploy the Device Workflow for each device. For each of the valid devices the script deploys the Device Workflow. In case
there are errors, they are shown clearly to the end user.
If (c) or (d) results in errors, the user must fix those errors and then MUST re-run the scripts even though the end-user has fixed the details on the Director. This is needed such that the variables in the scripts are also updated and it is in sync with the Director.
The directions on how to re-run the script is also provided. At the end of the run, the user is provided with a table showing the
current status.

## Phase3 :

In this phase the script works on BOTH the New-Dir and the OLD-Dir. In this phase the primary tasks are to:

a. OLD-Dir: Provide a list of devices the are not in SYNC or are not reachable. The user must then fix the status of the devices
on the Director (not automated by the script). While the device(s) statuses are being fixed, the user can either exit the script
or refresh the screen to get the updated status.

b. OLD-Dir: Next the script asks a series of questions to the user:
i. Does the user want to migrate all devices in on go.
ii. Does the user wants to migrate a batch of devices in one go and if the user does, then the user must provide the number devices in one batch.
iii. If the user does not want to choose i) or ii) then it is assumed that the user wants to migrate one device at a time. This is the fallback option.

c. Depending on the choices provided to the script the script moves to the next step. The script then tries to migrate the Controller-2 information from one or more devices (depending on the choices provided earlier). Once the migration of Controller-2 is complete for a device the script then performs a connect from the NEW-Dir to the device. The script does this for each device and on successful completion mark the device migration status to be C2-Complete.

d. Then the script tries to migrate and the migrate the Controller-1 information for one or more devices (depending on the choices provided earlier). Once the migration of Controller-1 is complete for a device the script then performs a connect from the NEW-Dir to the device. In addition the script performs 4 tests on each of the device:
i. Check the device connectivity to the Controller over BGP.
ii. Check the SLA status between the device and the Controller-2
iii. Check the SLA status between the device and Controller-1
iv. Check the LEF status between the device and the Controller.
Upon successful completion, the script marks the status of the device as C12-Complete. If there are errors, the device status the script simply provides logs. is The script does this for each device.

# EXECUTION:

1. Open Terminal (preferably xterm) and Log onto the Director and change Directory.
2. Export variables: This is optional
   export LINES=$(echo $LINES)
        export COLUMNS=$(echo $COLUMNS)
3. Change vm_phase1.json. Please read document. THIS IS AN IMPORTANT STEP. Please do this carefully.
4. Run various phases:
   ./VMMigr_phase1.py -f vm_phase1.json (Phase 1)
   ./VMMigr_phase2.py -f vm_phase2.json (Phase 2)
   ./VMMigr_phase2.py -f vm_phase3.json -r (Phase 2. Re-run option)
   ./VMMigr_phase3.py -f vm_phase3.json (Phase 3)
   cp vm_phase4.json vm_phase3.json (Phase 3 re-run)
   ./VMMigr_phase3.py -f vm_phase3.json (Phase 3 re-run )

# CURRENT LIMITATIONS:

1. Only one sub-org of a Parent org can be used. There can not be multiple orgs or sub-orgs
2. Presence of Hub-controllers in the deployment is supported. Usage of hub-controllers causes additional level of complexity in that the hub-controllers needed to be migrated before branches subtending the hub-controller are migrated. The user must accordingly plan the order of migration of devices.
3. As of current writing on release 20.2.4 and 21.2.2 releases are supported.
4. If there are external Authentication (e.g. TACACS ) present, then the recommendation is the disable them during the Migration process and re-enable them later.
