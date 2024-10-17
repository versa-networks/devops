# PLEASE NOTE THAT THIS TOOL/SCRIPT HAS NO WARRANTY AND NO SUPPORT OBLIGATIONS ASSOCIATED WITH
# IT. THIS TOOL/SCRIPT IS NOT OFFICIALLY SUPPORTED AND THE USER ASSUMES ALL LIABILITY FOR THE
# USE OF THIS TOOL AND ANY SUBSEQUENT LOSSES
#
# IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR
# CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
# WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
# CONNECTION WITH THE USE OR PERFORMANCE OF THIS TOOL/SCRIPT.

#VERSION=03172023

import requests
import re
import hashlib
import getpass
import os
import json
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#Function to get the list of the available spack Packages
def check_available_spack():
    url ="https://spack.versanetworks.com/versa-updates?action=get-list-of-available-upgrades&current-version=&current-api-version=11&flavor=premium&update-type=full"
    print("\n#  Fetching the list of available spack packages...")
    timeout = 60
    response = requests.get(url, timeout=timeout)
    if response.status_code == 200:
        versions = re.findall(r'<version>(\d+)</version>', response.text)
        check_available_spack.default_version = re.search(r'<version>(\d+)</version>', response.text).group(1)
        print("#  List of Available Spack Packages:\n")
        for i in range(0, len(versions), 30):
            print('|'.join(versions[i:i+30]))
            print(' ')
    else:
        print(f"#  Failed to get available spack list file: {response.status_code};  {response.text}")
        exit("#  Existing the script")



#Function to download the Spack file from spack-server
def download_spack(directorip, username, password):
    spackversion = input(f"#  Enter the spack package number or press 'ENTER' to download latest spack'{check_available_spack.default_version}': ") or check_available_spack.default_version
    
    #Verifying if spack already exist on director
    verifyurl = f"https://{directorip}:9182/nextgen/spack/downloads?offset=0&limit=100"
    print(f"#  Verifying if package '{spackversion}' already exist on '{directorip}'")
    response = requests.get(verifyurl, auth=(username, password), verify=False)
    if response.status_code == 200:
            data = response.json()
            if any(package['packageVersion'] == spackversion for package in data):
                print(f"#  Spack version '{spackversion}' already exist on '{directorip}'. Provide the correct spack number")
                spackversion = input("#  Enter the spack package number: ")
            else:
                print(f"#  Spack version '{spackversion}' is not found on '{directorip}', proceeding further")
    else:
        print(f"#  Failed to get available spack list file: {response.status_code};  {response.text}")
        exit("#  Existing the script")
    
    #Spack file URL
    url = f"https://spack.versanetworks.com/versa-updates?action=download-spack-version-ex&current-api-version=11&current-version={spackversion}&flavor=premium&update-type=full"
    download_spack.filename = f"versa-security-package-{spackversion}.tbz2"
    
    #Spack file Download
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024 #1 Kilobyte
        progress = 0
        with open(download_spack.filename, 'wb') as f:
            for data in response.iter_content(block_size):
                progress += len(data)
                f.write(data)
                percent = progress * 100 // total_size
                print(f"\r#  Downloading spack file '{download_spack.filename}': {percent}% ({progress}/{total_size})", end='', flush=True)
            print(f"\n#  Spack package file downloaded and saved to: '{download_spack.filename}'")
    else:
        print(f"#  Failed to download spack file '{download_spack.filename}': {response.status_code};  {response.text}")
        exit("#  Existing the script")
    
    
    #Spack hash file URL
    sha1url = f"https://spack.versanetworks.com/versa-updates?action=download-spack-version-ex&current-api-version=11&current-version={spackversion}&flavor=premium&update-type=full&type=sha1"
    download_spack.sha1filename = f"versa-security-package-{spackversion}.tbz2.sha1"
    
    #Spack hash file Download   
    response = requests.get(sha1url, stream=True)
    if response.status_code == 200:
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024 #1 Kilobyte
        progress = 0
        with open(download_spack.sha1filename, 'wb') as f:
            for data in response.iter_content(block_size):
                progress += len(data)
                f.write(data)
                percent = progress * 100 // total_size
                print(f"\r#  Downloading spack hash file '{download_spack.sha1filename}': {percent}% ({progress}/{total_size})", end='', flush=True)
            print(f"\n#  Spack package hash file downloaded and saved to: '{download_spack.sha1filename}'")
    else:
        print(f"#  Failed to download spack hash file '{download_spack.sha1filename}': {response.status_code};  {response.text}")
        exit("#  Existing the script")
        
    #Calculate the SHA1 hash of the downloaded file
    print(f"#  Calculating the hash of downloaded spack file: '{download_spack.filename}' and verifying with: '{download_spack.sha1filename}'")
    with open(download_spack.filename, 'rb') as f:
        sha1 = hashlib.sha1()
        while True:
            data = f.read(8192)
            if not data:
                break
            sha1.update(data)
        downloaded_hash = sha1.hexdigest()
    
    #Read the SHA1 hash from the hash file
    with open(download_spack.sha1filename, 'r') as f:
        hash_from_file = f.read().strip()
    
    #Compare the hashes
    if downloaded_hash == hash_from_file:
        print (f"#  Hash in file '{download_spack.sha1filename}': '{downloaded_hash}'")
        print (f"#  Hash calculated on file '{download_spack.filename}': '{hash_from_file}'")
        print(f"#  Downloaded Spack file '{download_spack.filename}' hash is Good")
    else:
        print (f"#  Hash in file '{download_spack.sha1filename}': '{downloaded_hash}'")
        print (f"#  Hash calculated on file '{download_spack.filename}': '{hash_from_file}'")
        print(f"#  Downloaded Spack file '{download_spack.filename}' hash is Bad")
        exit("#  Existing the script")



#Function to upload the Spack file to Versa-Director        
def upload_spack(directorip, username, password):
    timeout = 300  # seconds
    filespack = download_spack.filename
    filesize  = os.path.getsize(download_spack.filename)
    chunksize = 1024 * 1024  # read 1MB at a time
    readsofar = 0
    print(f"#  Creating HTTPS post request to upload spack and hash file to '{directorip}'")
    upload_url = f"https://{directorip}:9182/vnms/spack/upload?flavour=premium&updatetype=full"
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Connection': 'keep-alive',
    }
    data = {
        'spackChecksumFile': (download_spack.sha1filename, open(download_spack.sha1filename, 'rb')),
        'spackFile': (download_spack.filename, open(download_spack.filename, 'rb')),
    }
    print(f"#  Sending HTTPS post request to upload spack and hash file to '{directorip}, may take sometime (2-3min) depending on spack file size'")
    r = requests.post(upload_url, headers=headers, files=data, auth=(username, password), timeout=timeout, verify=False, stream=True)
    if r.status_code == 202:
        print(f"#  HTTPS status code received: {r.status_code}")
        post_response = r.json()['TaskResponse']
        taskid = post_response['link']['href']
        task_url = f"https://{directorip}:9182/{taskid}"
        print(f"#  HTTPS response from '{directorip}': Task-ID={r.json()['TaskResponse']['task-id']} Task-URL={task_url}")
        response = requests.get(task_url, auth=(username, password), verify=False)
        if response.json()['versa-tasks.task']['versa-tasks.task-status'] == "PENDING":
            print(f"#  Fetching taskid status from '{directorip}': \n   Versa-Tasks-id: {response.json()['versa-tasks.task']['versa-tasks.id']}\n   Versa-Task-Status: {response.json()['versa-tasks.task']['versa-tasks.task-status']}\n   Versa-Task-Percentage-Completion: {response.json()['versa-tasks.task']['versa-tasks.percentage-completion']}")
            time.sleep(1)
            response = requests.get(task_url, auth=(username, password), verify=False)
        else:
            print(f"#  Fetching Task-id progress from '{directorip}': \n   Versa-Tasks-id: {response.json()['versa-tasks.task']['versa-tasks.id']}\n   Versa-Task-Status: {response.json()['versa-tasks.task']['versa-tasks.task-status']}\n   Versa-Task-Description: {response.json()['versa-tasks.task']['versa-tasks.task-description']}")
        while response.json()['versa-tasks.task']['versa-tasks.percentage-completion'] != 100:
            response = requests.get(task_url, auth=(username, password), verify=False)
            print(f"\r#  Spack file upload progress: {response.json()['versa-tasks.task']['versa-tasks.percentage-completion']}", end='', flush=True)
            time.sleep(2) 
        #task_response = json.loads(response.text)
        #task_status = task_response["versa-tasks.task"]["versa-tasks.task-status"]
        if response.json()['versa-tasks.task']['versa-tasks.task-status'] == "UPLOAD_COMPLETE" or response.json()['versa-tasks.task']['versa-tasks.task-status'] == "COMPLETED":
            response = requests.get(task_url, auth=(username, password), verify=False)
            print(f"\n#  Spack upload Task completed on {directorip}: \n   Versa-Tasks-id: {response.json()['versa-tasks.task']['versa-tasks.id']}\n   Versa-Task-Status: {response.json()['versa-tasks.task']['versa-tasks.task-status']}\n   Versa-Task-Description: {response.json()['versa-tasks.task']['versa-tasks.task-description']}\n   Versa-Task-Percentage-Completion: {response.json()['versa-tasks.task']['versa-tasks.percentage-completion']}")
            print(f"#  Spack package file uploaded {response.json()['versa-tasks.task']['versa-tasks.percentage-completion']}% successfully!")
        else:
            print(f"\n#  Error uploading file: \n   Versa-Task-Status: {response.json()['versa-tasks.task']['versa-tasks.task-status']}\n   Versa-Task-Description: {response.json()['versa-tasks.task']['versa-tasks.task-description']}")
            exit("#  Existing the script")            
    else:
        print(f"#  Error, HTTPS Post request failed: {r.status_code};  {r.text}") 
        exit("#  Existing the script")  

print('''
# PLEASE NOTE THAT THIS TOOL/SCRIPT HAS NO WARRANTY AND NO SUPPORT OBLIGATIONS ASSOCIATED WITH
# IT. THIS TOOL/SCRIPT IS NOT OFFICIALLY SUPPORTED AND THE USER ASSUMES ALL LIABILITY FOR THE
# USE OF THIS TOOL AND ANY SUBSEQUENT LOSSES
#
# IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR
# CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
# WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
# CONNECTION WITH THE USE OR PERFORMANCE OF THIS TOOL/SCRIPT.
''')
print('')
directorip = input("#  Enter the Versa Director Management IP: ")
username = input("#  Enter the Versa Director PDSA Username: ")
password = getpass.getpass("#  Enter the Versa Director PDSA Password: ")
check_available_spack()
download_spack(directorip, username, password)
upload_spack(directorip, username, password)