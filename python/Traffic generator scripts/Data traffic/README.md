This Python script simulates various types of network traffic in a multithreaded environment. It is designed for testing, monitoring, or validating network behavior, intrusion detection systems (IDS), or traffic analysis tools by generating realistic traffic patterns across different protocols and services.

Features
- Simulates multiple types of network traffic, including:
  - FTP
  - SMB
  - Web browsing (e.g., SharePoint, OneDrive, Teams, Salesforce, Oracle, Outlook, etc.)
- Multi-threaded execution with random timers configured to keep the traffic pattern non-deterministic.

Requirements
- Tested in Python 3.10.12.
- The script accepts multiple source and destination IPs to create more unique 5-tuple traffic flows.  (Tip: You can increase the number of  IP addresses on the host by configuring loopback addresses.
- VSFTP (FTP) and Samba (SMB) must be installed on the source and destination Linux servers. 
- Update the script to include:
  - FTP and SMB credentials
  - File name and location
- The script has files named "ftp-1MB-file.txt" & "smb-1MB-file.txt" which must be present in the same folder where the script is being executed from.  The files can be created using the following linux command 
	- dd if=/dev/zero of=ftp-1MB-file.txt bs=1M count=1
	- dd if=/dev/zero of=smb-1MB-file.txt bs=1M count=1
- Update the script with the name and location of the log file.

