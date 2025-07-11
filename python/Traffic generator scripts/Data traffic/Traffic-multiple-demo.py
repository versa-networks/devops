#This script is to simulate traffic flows for the SD-WAN demo setup.  

import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import subprocess
import ftplib
import random
from datetime import datetime

#List of categorized URL's 

URLList_browsing = [
        'https://www.google.com/',
        'https://www.youtube.com/',
        'https://www.facebook.com/',
        'https://www.instagram.com/',
        'https://www.x.com/',
        'https://www.whatsapp.com/',
        'https://www.wikipedia.org/',
        'https://www.yahoo.com/',
        'https://www.reddit.com/',
        'https://www.amazon.com/',
        'https://www.chatgpt.com/',
        'https://www.tiktok.com/',
        'https://www.netflix.com/',
        'https://www.outreach.io/'
];

URLList_teams = [
        'https://teams.office.com/'
        'https://teams.microsoft.com/'
        'https://teams.live.com/'
];

URLList_onedrive = [
        'https://www.onedrive.com/'
        'https://onedrive.live.com/'
        'https://storage.live.com/'
];


URLList_sharepoint = [
        'https://www.sharepoint.com/'
];


URLList_box = [
        'https://www.box.com/'
];


URLList_sap = [
        'https://www.sap.com/'
];


URLList_salesforce = [
        'https://www.salesforce.com/'
];


URLList_oracle = [
        'https://www.oracle.com/'
];


URLList_office = [
        'https://www.office.com/'
        'https://login.microsoftonline.com/'   
];

URLList_outlook = [
        'https://www.outlook.com/'
];

URLList_enttech = [
        'https://www.jira.com/',
        'https://www.github.com/'
        'https://www.bitbucket.org/',
        'https://www.gitlab.com/'
        'https://www.confluence.atlassian.com/',
        'https://www.postmant.com/'
        'https://www.figma.com/',
        'https://www.workday.com/'
];

#Additional source IP's on the host can be created using loopback IP addresses.  
#Additional destination IP's on the remote host can be created using loopback IP addresses.  

SourceIP = ["10.1.4.1","10.1.4.2","10.1.4.3","10.1.4.4","10.1.4.5","10.1.4.6","10.1.4.7","10.1.4.8","10.1.4.9","10.1.4.10"]
DestinationIP = ["10.0.4.1","10.0.4.2","10.0.4.3","10.0.4.4","10.0.4.5","10.0.4.6","10.0.4.7","10.0.4.8","10.0.4.9","10.0.4.10","10.2.4.1","10.2.4.2","10.2.4.3","10.2.4.4","10.2.4.5","10.2.4.6","10.2.4.7","10.2.4.8","10.2.4.9","10.2.4.10"]  # List of IPs
password = "password123"
ftp_username = "jbrown"
ftp_filenames = ["ftp-1MB-file.txt"]  # List of FTP files to download
smb_filenames = ["smb-1MB-file.txt"]  # List of SMB files to download
log_file = "/home/azureuser/log/script_errors.log"

# Define a function for FTP
def ActFTP(stop_event, threadName, dstIP, username, password, filenames, srcIP):
    while not stop_event.is_set():
        try:
            ftp = ftplib.FTP(dstIP)
            ftp.login(user=username, passwd=password)
            ftp.cwd('ftp/files')
            for filename in filenames:
                with open(filename, 'wb') as local_file:
                    ftp.retrbinary('RETR {}'.format(filename), local_file.write)
            ftp.quit()
        except Exception as e:
            try:
#                with open(log_file, 'a') as log:
#                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#                    log.write(f"[{timestamp}] [{threadName}] Error with {dstIP}: {e}\n")
                pass
            except:
                pass
        if stop_event.is_set():
            break
        time.sleep(random.uniform(1, 10))


# Define a function for SMB 
def SMB(stop_event, threadName, dstIP, password, filenames):
    while not stop_event.is_set():
        for filename in filenames:
            try:
                subprocess.check_call(["smbclient", "//{}/samba-files".format(dstIP), "-U", "jbrown%{}".format(password), "-c", "get {}".format(filename)])
                print("{}: Downloaded {} from {}".format(threadName, filename, dstIP))
            except subprocess.CalledProcessError as e:
#                with open(log_file, 'a') as log:
#                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#                    log.write(f"[{timestamp}] [{threadName}] Error downloading {filename} from {dstIP}: {e}\n")
                pass
            if stop_event.is_set():
                break
            time.sleep(random.uniform(1, 10))

# Define URL browsing functions with stop event
def URL_browsing(stop_event, threadName, srcIP):
    while not stop_event.is_set():
        for URL in URLList_browsing:
            os.system('wget -q {} --no-check-certificate --delete-after -T 3 -t 1 --bind-address={} > /dev/null 2>&1'.format(URL, srcIP))
            if stop_event.is_set():
                break
            time.sleep(random.uniform(1, 5))
            
def URL_browsing(stop_event, threadName, srcIP):
    while not stop_event.is_set():
        for URL in URLList_browsing:
            os.system('wget -q {} --no-check-certificate --delete-after -T 3 -t 1 --bind-address={} > /dev/null 2>&1'.format(URL, srcIP))
            if stop_event.is_set():
                break
            time.sleep(random.uniform(1, 5))

def URL_teams(stop_event, threadName, srcIP):
    while not stop_event.is_set():
        for URL in URLList_teams:
            os.system('wget -q {} --no-check-certificate --delete-after -T 3 -t 1 --bind-address={} > /dev/null 2>&1'.format(URL, srcIP))
            if stop_event.is_set():
                break
            time.sleep(random.uniform(1, 5))

def URL_onedrive(stop_event, threadName, srcIP):
    while not stop_event.is_set():
        for URL in URLList_onedrive:
            os.system('wget -q {} --no-check-certificate --delete-after -T 3 -t 1 --bind-address={} > /dev/null 2>&1'.format(URL, srcIP))
            if stop_event.is_set():
                break
            time.sleep(random.uniform(1, 5))

def URL_sharepoint(stop_event, threadName, srcIP):
    while not stop_event.is_set():
        for URL in URLList_sharepoint:
            os.system('wget -q {} --no-check-certificate --delete-after -T 3 -t 1 --bind-address={} > /dev/null 2>&1'.format(URL, srcIP))
            if stop_event.is_set():
                break
            time.sleep(random.uniform(1, 5))

def URL_box(stop_event, threadName, srcIP):
    while not stop_event.is_set():
        for URL in URLList_box:
            os.system('wget -q {} --no-check-certificate --delete-after -T 3 -t 1 --bind-address={} > /dev/null 2>&1'.format(URL, srcIP))
            if stop_event.is_set():
                break
            time.sleep(random.uniform(1, 5))

def URL_sap(stop_event, threadName, srcIP):
    while not stop_event.is_set():
        for URL in URLList_sap:
            os.system('wget -q {} --no-check-certificate --delete-after -T 3 -t 1 --bind-address={} > /dev/null 2>&1'.format(URL, srcIP))
            if stop_event.is_set():
                break
            time.sleep(random.uniform(1, 5))

def URL_salesforce(stop_event, threadName, srcIP):
    while not stop_event.is_set():
        for URL in URLList_salesforce:
            os.system('wget -q {} --no-check-certificate --delete-after -T 3 -t 1 --bind-address={} > /dev/null 2>&1'.format(URL, srcIP))
            if stop_event.is_set():
                break
            time.sleep(random.uniform(1, 5))

def URL_oracle(stop_event, threadName, srcIP):
    while not stop_event.is_set():
        for URL in URLList_oracle:
            os.system('wget -q {} --no-check-certificate --delete-after -T 3 -t 1 --bind-address={} > /dev/null 2>&1'.format(URL, srcIP))
            if stop_event.is_set():
                break
            time.sleep(random.uniform(1, 5))

def URL_office(stop_event, threadName, srcIP):
    while not stop_event.is_set():
        for URL in URLList_office:
            os.system('wget -q {} --no-check-certificate --delete-after -T 3 -t 1 --bind-address={} > /dev/null 2>&1'.format(URL, srcIP))
            if stop_event.is_set():
                break
            time.sleep(random.uniform(1, 5))

def URL_outlook(stop_event, threadName, srcIP):
    while not stop_event.is_set():
        for URL in URLList_outlook:
            os.system('wget -q {} --no-check-certificate --delete-after -T 3 -t 1 --bind-address={} > /dev/null 2>&1'.format(URL, srcIP))
            if stop_event.is_set():
                break
            time.sleep(random.uniform(1, 5))

def URL_enttech(stop_event, threadName, srcIP):
    while not stop_event.is_set():
        for URL in URLList_enttech:
            os.system('wget -q {} --no-check-certificate --delete-after -T 3 -t 1 --bind-address={} > /dev/null 2>&1'.format(URL, srcIP))
            if stop_event.is_set():
                break
            time.sleep(random.uniform(1, 5))

    
def run_with_timeout(target, timeout, *args):
    stop_event = threading.Event()
    thread = threading.Thread(target=target, args=(stop_event,) + args)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        print("Thread for {} timed out and will be terminated.".format(target.__name__))
        stop_event.set()
        thread.join()  # Wait for the thread to exit cleanly

# List of traffic types (functions or callable objects)
trafficType = [ActFTP,URL_browsing,URL_teams,URL_onedrive,URL_sharepoint,URL_box,URL_sap,SMB,URL_salesforce,URL_oracle,URL_office,URL_outlook,URL_enttech]
with ThreadPoolExecutor(max_workers=5) as executor:
    while True:
        futures = []
        for traffic in trafficType:
            srcIP = random.choice(SourceIP)
            dstIP = random.choice(DestinationIP)
            timeout = random.randint(1, 20)
            if traffic == ActFTP:
                timeout = random.randint(1, 20)
                future = executor.submit(run_with_timeout, ActFTP, timeout, "Thread-ActFTP", dstIP, ftp_username, password, ftp_filenames, srcIP)
            elif traffic == SMB:
                timeout = random.randint(1, 20)
                future = executor.submit(run_with_timeout, SMB, timeout, "Thread-SMB", dstIP, password, smb_filenames)
            else:
                future = executor.submit(run_with_timeout, traffic, timeout, "Thread-URL", srcIP)
            futures.append(future)
        for future in futures:
            future.result()
        time.sleep(1)

