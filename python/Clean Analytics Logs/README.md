
Script for deleting archive logs on an Analytics node for a given Organization
------------------------------------------------------------------------------------------

Tested in Python 3.10.5
Tested on Versa Anlaytics 21.2.2

------------------------------------------------------------------------------------------
Purpose

The script deletes the archieve logs on the Analytics nodes. The script gets the organization
name and the number of days which is the reference point for the log deletion. Let's assume we 
want to delete all the archive logs for an organization older than 60 days; in this case 
we should give 60 as an input to the script (the '--days' argument)

------------------------------------------------------------------------------------------
Usage

The script should run on the Analytics nodes !

Copy the script to the Analytics nodes via scp/sftp and run the command below.

[root@versa-analytics: versa]# sudo chmod a+x Analytics-Clear-Archive-Logs-Script.py

[root@versa-analytics: versa]# python ./Analytics-Clear-Archive-Logs-Script.py --help
usage: Analytics-Clear-Archive-Logs-Script.py [-h] [--org ORG] [--days DAYS]

Script for deleting archive logs on an Analytics node for a given Organization

optional arguments:
  -h, --help   show this help message and exit
  --org ORG    Organization Name
  --days DAYS  Number of days back (reference point for the log deletion)
  
[root@versa-analytics: versa]# python ./Analytics-Clear-Archive-Logs-Script.py --org VERSA --days 120
