import json
import re
import requests
from requests.packages import urllib3
import getpass

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
PYTHONWARNINGS = "ignore:InsecureRequestWarning"

import os
GENERAL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../temp/general.txt")


def read_general_file(filepath):
    with open(filepath, "r") as f:
        return f.readlines()


def get_value_from_file(lines, key):
    for line in lines:
        if line.strip().startswith(key):
            match = re.search(r">>\s*(.+)", line)
            if match:
                return match.group(1).strip()
    return None


def update_value_in_file(filepath, key, new_value):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    if not os.path.exists(filepath):
        open(filepath, "w").close()

    with open(filepath, "r") as f:
        lines = f.readlines()

    updated = False
    for i, line in enumerate(lines):
        if line.strip().startswith(key):
            prefix = line[: line.index(key)]
            lines[i] = f"{prefix}{key} >> {new_value}\n"
            updated = True
            break

    if not updated:
        lines.append(f"{key} >> {new_value}\n")

    with open(filepath, "w") as f:
        f.writelines(lines)


def parse_all_cookies(response):
    cookies = {}
    raw = response.headers.get("Set-Cookie", "")
    if not raw:
        return cookies

    for segment in re.split(r",\s*(?=[A-Za-z0-9_\-]+=)", raw):
        first_part = segment.strip().split(";")[0]
        if "=" in first_part:
            name, _, value = first_part.partition("=")
            cookies[name.strip()] = value.strip()
    return cookies


def find_uuid_by_name(nodes, target_name):
    for node in nodes:
        if node.get("name") == target_name:
            return node.get("uuid")
        children = node.get("nodes", [])
        if children:
            result = find_uuid_by_name(children, target_name)
            if result:
                return result
    return None


print("\n[1/6] Gathering configuration\n")

fqdn = input("Concerto FQDN: ").strip().replace(",", ".")
update_value_in_file(GENERAL_FILE, "concerto-fqdn", fqdn)

port_input = input("Concerto port [443]: ").strip()
port = port_input if port_input else "443"
update_value_in_file(GENERAL_FILE, "concerto-port", port)

USERNAME = input("Concerto username: ").strip()
update_value_in_file(GENERAL_FILE, "concerto-user", USERNAME)

PASSWORD = getpass.getpass("Concerto password: ")

tenant_name = input("Tenant name: ").strip()
update_value_in_file(GENERAL_FILE, "tenant-name", tenant_name)

client_id_input = input("REST API client_id [concerto]: ").strip()
CLIENT_ID = client_id_input if client_id_input else "concerto"
update_value_in_file(GENERAL_FILE, "concerto-clientid", CLIENT_ID)

client_secret_input = getpass.getpass("REST API client_id password (press Enter for default): ")
CLIENT_SECRET = client_secret_input if client_secret_input else "Concerto123@"

print("\nIf you are using LDAP in your firewall policies, enter the LDAP profile name.")
print("Press Enter for none.")
ldap_profile = input("LDAP profile: ").strip()
if ldap_profile:
    update_value_in_file(GENERAL_FILE, "ldap-profile", ldap_profile)

print("\nIf you want to convert LDAP in your firewall policies to SCIM, enter the SCIM profile name.")
print("Press Enter for none.")
scim_profile = input("SCIM profile: ").strip()
if scim_profile:
    update_value_in_file(GENERAL_FILE, "scim-profile", scim_profile)

ldap_format = None
if ldap_profile and not scim_profile:
    print("\nWhich LDAP username format is Concerto using?")
    print("  1 = UPN format              (e.g. user@domain.com)")
    print("  2 = LDAP DN format          (e.g. CN=user,DC=domain,DC=com)")
    print("  3 = LDAP DN format with UUID (e.g. CN=user,DC=domain,DC=com|S-1-2-3-456893)")
    ldap_format = input("Enter 1, 2, or 3: ").strip()
    if ldap_format == "1":
        update_value_in_file(GENERAL_FILE, "ldap-upn", "true")
    if ldap_format == "3":
        update_value_in_file(GENERAL_FILE, "ldap-groups-uuid", "true")

CONCERTO_URL = f"https://{fqdn}:{port}"

print(f"\n[2/6] CSRF token fetch ...")

session = requests.Session()
response = session.get(CONCERTO_URL, verify=False)
print(f"      Status: {response.status_code} {'OK' if response.ok else 'FAILED'}")

all_cookies = parse_all_cookies(response)
print(f"      Cookies found in Set-Cookie header: {list(all_cookies.keys())}")

csrf_token = all_cookies.get("ECP-CSRF-TOKEN")
print(f"      ECP-CSRF-TOKEN : {csrf_token or 'NOT FOUND'}")

if not csrf_token:
    print("\n      [ERROR] ECP-CSRF-TOKEN not found. Cannot proceed.")
    raise SystemExit(1)

domain = fqdn.split(":")[0]
for name, value in all_cookies.items():
    session.cookies.set(name, value, domain=domain)

headers = {"X-CSRF-Token": csrf_token}
body    = {
    "username":      USERNAME,
    "password":      PASSWORD,
    "grant_type":    "password",
    "client_id":     CLIENT_ID,
    "client_secret": CLIENT_SECRET,
}

print(f"\n[3/6] Requesting Bearer token ...")
response = session.post(
    CONCERTO_URL + "/portalapi/v1/auth/token",
    verify=False,
    cookies=session.cookies,
    headers=headers,
    json=body,
)
print(f"      Status: {response.status_code} {'OK' if response.ok else 'FAILED'}")
if not response.ok:
    print(f"      Response: {response.text}")
response.raise_for_status()

token_cookies = parse_all_cookies(response)
for name, value in token_cookies.items():
    session.cookies.set(name, value, domain=domain)
    all_cookies[name] = value

csrf_token   = all_cookies.get("ECP-CSRF-TOKEN", csrf_token)
bearer_token = response.json()["access_token"]
cookies_str  = "; ".join([f"{k}={v}" for k, v in all_cookies.items()])

print(f"\n      All cookies saved: {list(all_cookies.keys())}")

update_value_in_file(GENERAL_FILE, "bearer-token", bearer_token)
update_value_in_file(GENERAL_FILE, "csrf-token",   csrf_token)
update_value_in_file(GENERAL_FILE, "cookies",      cookies_str)

print(f"      Tokens saved to {GENERAL_FILE}")

print(f"\n[4/6] Fetching tenant UUID for '{tenant_name}' ...")

api_headers = {
    "X-CSRF-Token":  csrf_token,
    "Authorization": f"Bearer {bearer_token}",
    "Accept":        "application/json",
    "Content-Type":  "application/json",
}

endpoint = f"/portalapi/v1/tenants/tenant/name/{tenant_name}"
print(f"      GET {endpoint}")

response = session.get(
    CONCERTO_URL + endpoint,
    verify=False,
    cookies=session.cookies,
    headers=api_headers,
)
print(f"      Status: {response.status_code} {'OK' if response.ok else 'FAILED'}")

if not response.ok:
    print(f"      [ERROR] {response.text[:500]}")
    raise SystemExit(1)

data        = response.json()
tenant_info = data.get("tenantInfo", data)
tenant_uuid = (
    tenant_info.get("uuid")
    or tenant_info.get("id")
    or tenant_info.get("tenantId")
)

if not tenant_uuid:
    print(f"      [WARN] UUID field not found. Full response:")
    print(json.dumps(data, indent=4))
    raise SystemExit(1)

update_value_in_file(GENERAL_FILE, "tenant-uuid", tenant_uuid)
print(f"      tenant-uuid saved: {tenant_uuid}")

print(f"\n[5/6] Fetching profile elements for tenant '{tenant_name}' ...")

endpoint = f"/portalapi/v1/tenants/{tenant_uuid}/configuration/perspective/profile-elements"
print(f"      GET {endpoint}")

response = session.get(
    CONCERTO_URL + endpoint,
    verify=False,
    cookies=session.cookies,
    headers=api_headers,
)
print(f"      Status: {response.status_code} {'OK' if response.ok else 'FAILED'}")

if not response.ok:
    print(f"      [ERROR] {response.text[:500]}")
    raise SystemExit(1)

nodes = response.json().get("perspective", [])

print(f"\n[6/6] Extracting and saving profile element UUIDs ...")

targets = {
    "URL Categories":         "url-categories-parent-ref-uuid",
    "Address Group":          "address-group-parent-ref-uuid",
    "Predefined Application": "predef-application-parent-ref-uuid",
    "Application Group":      "application-group-parent-ref-uuid",
    "Services":               "services-parent-ref-uuid",
}

for name, key in targets.items():
    uuid = find_uuid_by_name(nodes, name)
    if uuid:
        update_value_in_file(GENERAL_FILE, key, uuid)
        print(f"      {key} >> {uuid}")
    else:
        print(f"      [WARN] '{name}' not found in response")

print(f"\nDone. Updated {GENERAL_FILE}:")
for line in read_general_file(GENERAL_FILE):
    print(f"  {line}", end="")

if ldap_profile:
    ldap_users_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../temp/concerto-ldap-users.txt")
    window_number   = 0
    window_size     = 100
    all_results     = []

    print(f"\n[8/6] Fetching LDAP users for profile '{ldap_profile}' ...")

    while True:
        endpoint = (
            f"/portalapi/v1/tenants/{tenant_uuid}/sd-wan/policies/authentication"
            f"/profile/ldap-users/{ldap_profile}"
            f"?nextWindowNumber={window_number}&windowSize={window_size}"
        )
        print(f"      GET {endpoint}")

        response = session.get(
            CONCERTO_URL + endpoint,
            verify=False,
            cookies=session.cookies,
            headers=api_headers,
        )
        print(f"      Status: {response.status_code} {'OK' if response.ok else 'FAILED'}")

        if not response.ok:
            print(f"      [ERROR] {response.text[:500]}")
            break

        data = response.json()

        if isinstance(data, list):
            page_items = data
        elif isinstance(data, dict):
            page_items = next((v for v in data.values() if isinstance(v, list)), [])
        else:
            page_items = []

        count = len(page_items)
        print(f"      Records in this page: {count}")
        all_results.extend(page_items)

        if count < window_size:
            break

        window_number += 1

    os.makedirs(os.path.dirname(ldap_users_file), exist_ok=True)
    with open(ldap_users_file, "w") as f:
        json.dump(all_results, f, indent=4)

    print(f"      Total LDAP users fetched: {len(all_results)}")
    print(f"      Saved to {ldap_users_file}")

    ldap_groups_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../temp/ldap-groups-uuid.txt")
    window_number    = 0
    window_size      = 100
    all_results      = []

    print(f"\n[9/6] Fetching LDAP groups for profile '{ldap_profile}' ...")

    while True:
        endpoint = (
            f"/portalapi/v1/tenants/{tenant_uuid}/sd-wan/policies/authentication"
            f"/profile/ldap-groups/{ldap_profile}"
            f"?nextWindowNumber={window_number}&windowSize={window_size}"
        )
        print(f"      GET {endpoint}")

        response = session.get(
            CONCERTO_URL + endpoint,
            verify=False,
            cookies=session.cookies,
            headers=api_headers,
        )
        print(f"      Status: {response.status_code} {'OK' if response.ok else 'FAILED'}")

        if not response.ok:
            print(f"      [ERROR] {response.text[:500]}")
            break

        data = response.json()

        if isinstance(data, list):
            page_items = data
        elif isinstance(data, dict):
            page_items = next((v for v in data.values() if isinstance(v, list)), [])
        else:
            page_items = []

        count = len(page_items)
        print(f"      Records in this page: {count}")
        all_results.extend(page_items)

        if count < window_size:
            break

        window_number += 1

    os.makedirs(os.path.dirname(ldap_groups_file), exist_ok=True)
    with open(ldap_groups_file, "w") as f:
        json.dump(all_results, f, indent=4)

    print(f"      Total LDAP groups fetched: {len(all_results)}")
    print(f"      Saved to {ldap_groups_file}")