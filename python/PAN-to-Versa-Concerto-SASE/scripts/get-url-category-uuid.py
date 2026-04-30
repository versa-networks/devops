import os
import re
import sys
import requests
import logging
from requests.packages import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

FINAL_DATA_FILE = os.path.join(BASE_DIR, "final-data", "final-custom-urlf-profile.txt")
GENERAL_FILE = os.path.join(BASE_DIR, "temp", "general.txt")
LOG_FILE = os.path.join(BASE_DIR, "log", "step-get_urlf_uuid.log")

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s"
)

def read_general(path):
    config = {}
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if ">>" in line:
                key, value = re.split(r'\s*>>\s*', line, 1)
                config[key.strip()] = value.strip()
    return config

def parse_cookies(cookie_str):
    cookies = {}
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            cookies[k.strip()] = v.strip()
    return cookies

def main():
    if not os.path.isfile(FINAL_DATA_FILE):
        print(f"File not found: {FINAL_DATA_FILE}")
        logging.error("Required file not found: %s", FINAL_DATA_FILE)
        sys.exit(1)

    config = read_general(GENERAL_FILE)
    fqdn = "https://" + config["concerto-fqdn"]
    tenant_uuid = config["tenant-uuid"]
    bearer_token = config["bearer-token"]
    csrf_token = config["csrf-token"]
    cookies = parse_cookies(config["cookies"])

    headers = {
        "Authorization": "Bearer " + bearer_token,
        "X-CSRF-Token": csrf_token,
        "Content-Type": "application/json"
    }

    window_number = 0
    results = []

    while True:
        url = (
            f"{fqdn}/portalapi/v1/tenants/{tenant_uuid}"
            f"/sase/settings/urlCategory/summarize"
            f"?windowSize=100&nextWindowNumber={window_number}&category=URL_CATEGORY&ecpScope=SASE"
        )
        logging.info("GET %s", url)
        response = requests.get(url, headers=headers, cookies=cookies, verify=False)
        logging.debug("Status: %s", response.status_code)

        if response.status_code != 200:
            logging.error("Non-200 response: %s %s", response.status_code, response.text)
            print(f"Error: received status {response.status_code}")
            sys.exit(1)

        data = response.json().get("data", [])
        logging.info("Window %d: received %d entries", window_number, len(data))

        if not data:
            logging.info("Empty data response, stopping pagination.")
            break

        for item in data:
            name = item.get("name")
            uuid = item.get("uuid")
            if name and uuid:
                results.append(f"{name}:{uuid}")
                logging.debug("Found: %s:%s", name, uuid)

        window_number += 1

    with open(GENERAL_FILE, "a") as f:
        for entry in results:
            f.write(entry + "\n")

    logging.info("Wrote %d urlf entries to %s", len(results), GENERAL_FILE)
    print(f"Done. Wrote {len(results)} urlf entries to {GENERAL_FILE}")

if __name__ == "__main__":
    main()