import json
import os
import requests
from requests.packages import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

script_dir = os.path.dirname(os.path.abspath(__file__))
general_path = os.path.join(script_dir, "..", "temp", "general.txt")
output_dir = os.path.join(script_dir, "..")

config = {}
with open(general_path, "r") as f:
    for line in f:
        line = line.strip()
        if " >> " in line:
            key, value = line.split(" >> ", 1)
            config[key.strip()] = value.strip()

fqdn = config["concerto-fqdn"]
tenant_uuid = config["tenant-uuid"]
bearer_token = config["bearer-token"]
csrf_token = config["csrf-token"]
raw_cookies = config["cookies"]

headers = {
    "Authorization": "Bearer " + bearer_token,
    "X-CSRF-Token": csrf_token,
}

cookie_jar = {}
for part in raw_cookies.split("; "):
    if "=" in part:
        k, v = part.split("=", 1)
        cookie_jar[k.strip()] = v.strip()

window_size = 100

def fetch_all(endpoint_path, output_filename):
    all_resources = []
    window_number = 0
    base_url = f"https://{fqdn}/portalapi/v1/tenants/{tenant_uuid}/sase/{endpoint_path}/summarize"

    while True:
        url = f"{base_url}?nextWindowNumber={window_number}&windowSize={window_size}"
        response = requests.get(url, headers=headers, cookies=cookie_jar, verify=False)
        response.raise_for_status()
        data = response.json()

        resources = []
        if isinstance(data, list):
            resources = data
        elif isinstance(data, dict):
            for key in ("Resources", "resources", "data", "results"):
                if key in data and isinstance(data[key], list):
                    resources = data[key]
                    break
            if not resources:
                for v in data.values():
                    if isinstance(v, list):
                        resources = v
                        break

        all_resources.extend(resources)
        count = len(resources)
        print(f"  [{endpoint_path}] window {window_number}: fetched {count} records")

        if count < window_size:
            break
        window_number += 1

    output_path = os.path.join(output_dir, output_filename)
    with open(output_path, "w") as f:
        json.dump(all_resources, f, indent=2)
    print(f"  Saved {len(all_resources)} total records to {output_filename}")

print("Fetching SCIM groups...")
fetch_all("scim/group", "scim-groups-dump.txt")

print("Fetching SCIM users...")
fetch_all("scim/user", "scim-users-dump.txt")

print("Done.")
