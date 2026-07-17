import os
import re
import json
import requests
from requests.packages import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
GENERAL_FILE = os.path.join(BASE_DIR, "temp", "general.txt")
OUTPUT_FILE = os.path.join(BASE_DIR, "temp", "concerto-ldap-users.txt")

def read_general(path):
    result = {}
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if ">>" in line:
                key, val = re.split(r'\s*>>\s*', line, 1)
                result[key.strip()] = val.strip()
    return result

general = read_general(GENERAL_FILE)

fqdn = "https://" + general["concerto-fqdn"]
tenant_uuid = general["tenant-uuid"]
bearer_token = general["bearer-token"]
csrf_token = general["csrf-token"]
cookies_str = general["cookies"]
ldap_profile = general["ldap-profile"]

session = requests.Session()
for part in cookies_str.split(";"):
    part = part.strip()
    if "=" in part:
        k, _, v = part.partition("=")
        session.cookies.set(k.strip(), v.strip())

headers = {
    "Authorization": "Bearer " + bearer_token,
    "X-CSRF-Token": csrf_token,
    "Accept": "application/json",
    "Content-Type": "application/json",
}

window_number = 0
window_size = 100
all_results = []

while True:
    url = (
        fqdn
        + f"/portalapi/v1/tenants/{tenant_uuid}/sd-wan/policies/authentication"
        + f"/profile/ldap-users/{ldap_profile}"
        + f"?nextWindowNumber={window_number}&windowSize={window_size}"
    )
    print("GET " + url)
    resp = session.get(url, verify=False, headers=headers)
    print("Status: " + str(resp.status_code))

    if not resp.ok:
        print("ERROR: " + resp.text[:500])
        break

    data = resp.json()

    if isinstance(data, list):
        page_items = data
    elif isinstance(data, dict):
        page_items = next((v for v in data.values() if isinstance(v, list)), [])
    else:
        page_items = []

    count = len(page_items)
    print("Records in this page: " + str(count))
    all_results.extend(page_items)

    if count < window_size:
        break

    window_number += 1

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
with open(OUTPUT_FILE, "w") as f:
    json.dump(all_results, f, indent=4)

print("Total LDAP users fetched: " + str(len(all_results)))
print("Saved to " + OUTPUT_FILE)
