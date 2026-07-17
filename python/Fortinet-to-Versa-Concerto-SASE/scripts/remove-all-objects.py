#!/usr/bin/env python3
import os
import re
import sys
import json
import time
import threading
import getpass
import urllib.parse
import requests
from requests.packages import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
PYTHONWARNINGS = "ignore:InsecureRequestWarning"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GENERAL_FILE = os.path.join(SCRIPT_DIR, "../temp/general.txt")

# ---------------------------------------------------------------------------
# CLI flags — parsed once at startup, used throughout
# ---------------------------------------------------------------------------
QUICK_MODE  = "--quick"  in sys.argv   # fire DEL without waiting for server response
BOTTOM_MODE = "--bottom" in sys.argv   # process temp-file objects bottom-to-top


def read_general_file():
    with open(GENERAL_FILE, "r") as f:
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


def run_login():
    print("\n[1/6] Gathering configuration\n")
    fqdn = input("Concerto FQDN: ").strip()
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
    body = {
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
    for line in read_general_file():
        print(f"  {line}", end="")


def load_config():
    lines        = read_general_file()
    fqdn         = get_value_from_file(lines, "concerto-fqdn")
    port         = get_value_from_file(lines, "concerto-port") or "443"
    tenant_uuid  = get_value_from_file(lines, "tenant-uuid")
    bearer_token = get_value_from_file(lines, "bearer-token")
    csrf_token   = get_value_from_file(lines, "csrf-token")
    cookies_str  = get_value_from_file(lines, "cookies")
    base_url     = f"https://{fqdn}:{port}"
    return base_url, tenant_uuid, bearer_token, csrf_token, cookies_str


def build_headers(bearer_token, csrf_token):
    return {
        "X-CSRF-Token":  csrf_token,
        "Authorization": f"Bearer {bearer_token}",
        "Accept":        "application/json",
        "Content-Type":  "application/json",
    }


def parse_cookies_str(cookies_str):
    cookies = {}
    if not cookies_str:
        return cookies
    for part in cookies_str.split(";"):
        part = part.strip()
        if "=" in part:
            k, _, v = part.partition("=")
            cookies[k.strip()] = v.strip()
    return cookies


def print_box(msg_lines):
    max_len = max(len(l) for l in msg_lines)
    inner   = max_len + 4
    border  = "═" * inner
    print(f"\n╔{border}╗")
    for line in msg_lines:
        print(f"║  {line.ljust(max_len)}  ║")
    print(f"╚{border}╝\n")


def confirm_delete(temp_file, label):
    rel = os.path.relpath(temp_file, SCRIPT_DIR)
    print_box([
        f"WARNING: ALL {label} objects will be PERMANENTLY DELETED!",
        "",
        "If there are objects you want to keep on Concerto,",
        f"open this file and remove those lines BEFORE typing DELETE:",
        f"  {rel}",
        "",
        "Type DELETE to proceed, or anything else to cancel.",
    ])
    answer = input("→ ").strip()
    return answer == "DELETE"


def save_objects_to_file(objects, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        for name, uuid in objects.items():
            f.write(f"{name} >> {uuid}\n")
    print(f"  Saved {len(objects)} object(s) to {filepath}")


def read_objects_from_file(filepath):
    """Parse a name >> uuid temp file into an ordered dict.

    When the global BOTTOM_MODE flag is set, the file lines are reversed so
    the last entry in the file is processed first.
    """
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        raw_lines = f.readlines()
    if BOTTOM_MODE:
        raw_lines = list(reversed(raw_lines))
    objects = {}
    for raw_line in raw_lines:
        line = raw_line.strip().strip("\r").strip()
        if not line or " >> " not in line:
            continue
        name, _, uuid = line.partition(" >> ")
        name = name.strip().strip("\r").strip()
        uuid = uuid.strip().strip("\r").strip()
        if name and uuid:
            objects[name] = uuid
    return objects


def got_401():
    print("\n  [ERROR] Server returned 401 Unauthorized.")
    print("  Your token has expired. Select option R from the menu to refresh it.\n")


# ---------------------------------------------------------------------------
# DELETE helpers
# ---------------------------------------------------------------------------

def _fire_delete(url, headers, cookies, name):
    """Background worker for --quick mode — response is intentionally discarded."""
    try:
        requests.delete(url, headers=headers, cookies=cookies, verify=False, timeout=30)
    except Exception:
        pass  # fire-and-forget: errors are silently dropped


def safe_delete(url, headers, cookies, name, delay=0.500, retries=2):
    """Issue a DELETE request with throttle delay and retry on connection errors.

    Behaviour is controlled by the global QUICK_MODE flag set via --quick:
      QUICK_MODE=False  blocks until the server responds and prints the status.
      QUICK_MODE=True   spawns a daemon thread and returns immediately without
                        waiting for the server reply (fire-and-forget).
    """
    time.sleep(delay)
    if QUICK_MODE:
        t = threading.Thread(
            target=_fire_delete,
            args=(url, headers, cookies, name),
            daemon=True,
        )
        t.start()
        print(f"  SENT   DELETE  {name}  (no response wait)")
        return None

    for attempt in range(1, retries + 1):
        try:
            resp   = requests.delete(url, headers=headers, cookies=cookies, verify=False, timeout=30)
            status = "OK" if resp.ok else "FAILED"
            print(f"  DELETE [{resp.status_code}] {status}  {name}")
            return resp
        except requests.exceptions.ConnectionError as exc:
            if attempt < retries:
                print(f"  [WARN] Connection reset on '{name}', retrying in 2s...")
                time.sleep(2)
            else:
                print(f"  [ERROR] Connection failed on '{name}' after {retries} attempts: {exc}")
                return None


# ---------------------------------------------------------------------------
# Per-object-type delete functions
# ---------------------------------------------------------------------------

def delete_address_groups(skip_confirm=False):
    base_url, tenant_uuid, bearer_token, csrf_token, cookies_str = load_config()
    headers   = build_headers(bearer_token, csrf_token)
    cookies   = parse_cookies_str(cookies_str)
    summ_url  = f"{base_url}/portalapi/v1/tenants/{tenant_uuid}/elements/endpoint/summarize"
    temp_file = os.path.join(SCRIPT_DIR, "../temp/temp-address-group.txt")

    print("\n  Fetching address group objects from Concerto...")
    objects = {}
    window  = 0
    while True:
        url  = f"{summ_url}?windowSize=100&nextWindowNumber={window}&category=ADDRESS_GROUP&ecpScope=SASE"
        resp = requests.get(url, headers=headers, cookies=cookies, verify=False)
        if resp.status_code == 401:
            got_401()
            return
        if not resp.ok:
            print(f"  [ERROR] GET failed: {resp.status_code}")
            break
        data = resp.json().get("data", [])
        if not data:
            break
        count_before = len(objects)
        for item in data:
            entity = item.get("entity", item)
            name   = entity.get("name")
            uuid   = entity.get("uuid")
            if name and uuid:
                objects[name] = uuid
        if len(objects) == count_before:
            break
        print(f"  Window {window}: {len(objects)} object(s) collected so far")
        window += 1

    if not objects:
        print("  No address group objects found.")
        return

    save_objects_to_file(objects, temp_file)

    if not skip_confirm and not confirm_delete(temp_file, "Address Group"):
        print("  Cancelled. No objects were deleted.")
        return

    objects = read_objects_from_file(temp_file)
    print(f"\n  Deleting {len(objects)} address group object(s)...")
    for name, uuid in objects.items():
        encoded = urllib.parse.quote(name, safe="")
        url = (
            f"{base_url}/portalapi/v1/tenants/{tenant_uuid}/elements/endpoint/"
            f"ConfigurationLifecycleGraph%252FPROFILE_ELEMENTS%252FElements%252FEndpoint"
            f"%252FAddress%2520Group%252F%252F{encoded}-1"
        )
        safe_delete(url, headers, cookies, name)

    os.remove(temp_file)
    print(f"\n  Done. Temp file removed.")


def delete_custom_services(skip_confirm=False):
    base_url, tenant_uuid, bearer_token, csrf_token, cookies_str = load_config()
    headers   = build_headers(bearer_token, csrf_token)
    cookies   = parse_cookies_str(cookies_str)
    summ_url  = f"{base_url}/portalapi/v1/tenants/{tenant_uuid}/elements/services/summary"
    temp_file = os.path.join(SCRIPT_DIR, "../temp/temp-cust-service.txt")

    print("\n  Fetching custom service objects from Concerto...")
    objects = {}
    window  = 0
    while True:
        url  = f"{summ_url}?windowSize=100&nextWindowNumber={window}&ecpScope=SASE&filter=all"
        resp = requests.get(url, headers=headers, cookies=cookies, verify=False)
        if resp.status_code == 401:
            got_401()
            return
        if not resp.ok:
            print(f"  [ERROR] GET failed: {resp.status_code}")
            break
        data = resp.json().get("data", [])
        if not data:
            break
        count_before = len(objects)
        for item in data:
            ecp_user_defined = item.get("ecpUserDefined", {})
            for svc_name, svc_list in ecp_user_defined.items():
                if svc_list:
                    name = svc_list[0].get("name") or svc_name
                    uuid = svc_list[0].get("uuid")
                    if name and uuid:
                        objects[name] = uuid
        if len(objects) == count_before:
            break
        print(f"  Window {window}: {len(objects)} object(s) collected so far")
        window += 1

    if not objects:
        print("  No custom service objects found.")
        return

    save_objects_to_file(objects, temp_file)

    if not skip_confirm and not confirm_delete(temp_file, "Custom Service"):
        print("  Cancelled. No objects were deleted.")
        return

    objects = read_objects_from_file(temp_file)
    print(f"\n  Deleting {len(objects)} custom service object(s)...")
    for name, uuid in objects.items():
        encoded = urllib.parse.quote(name, safe="")
        url = (
            f"{base_url}/portalapi/v1/tenants/{tenant_uuid}/elements/services/"
            f"ConfigurationLifecycleGraph%252FPROFILE_ELEMENTS%252FElements%252FEndpoint"
            f"%252FServices%252F%252F{encoded}-1"
        )
        safe_delete(url, headers, cookies, name)

    os.remove(temp_file)
    print(f"\n  Done. Temp file removed.")


def delete_url_categories(skip_confirm=False):
    base_url, tenant_uuid, bearer_token, csrf_token, cookies_str = load_config()
    headers   = build_headers(bearer_token, csrf_token)
    cookies   = parse_cookies_str(cookies_str)
    summ_url  = f"{base_url}/portalapi/v1/tenants/{tenant_uuid}/sase/settings/urlCategory/summarize"
    temp_file = os.path.join(SCRIPT_DIR, "../temp/temp-url-category.txt")

    print("\n  Fetching custom URL category objects from Concerto...")
    objects = {}
    window  = 0
    while True:
        url  = f"{summ_url}?windowSize=100&nextWindowNumber={window}&category=URL_CATEGORY&ecpScope=SASE"
        resp = requests.get(url, headers=headers, cookies=cookies, verify=False)
        if resp.status_code == 401:
            got_401()
            return
        if not resp.ok:
            print(f"  [ERROR] GET failed: {resp.status_code}")
            break
        data = resp.json().get("data", [])
        if not data:
            break
        count_before = len(objects)
        for item in data:
            name = item.get("name")
            uuid = item.get("uuid")
            if name and uuid:
                objects[name] = uuid
        if len(objects) == count_before:
            break
        print(f"  Window {window}: {len(objects)} object(s) collected so far")
        window += 1

    if not objects:
        print("  No custom URL category objects found.")
        return

    save_objects_to_file(objects, temp_file)

    if not skip_confirm and not confirm_delete(temp_file, "Custom URL Category"):
        print("  Cancelled. No objects were deleted.")
        return

    objects = read_objects_from_file(temp_file)
    print(f"\n  Deleting {len(objects)} custom URL category object(s)...")
    for name, uuid in objects.items():
        url = f"{base_url}/portalapi/v1/tenants/{tenant_uuid}/sase/settings/urlCategory/{uuid}"
        safe_delete(url, headers, cookies, name)

    os.remove(temp_file)
    print(f"\n  Done. Temp file removed.")


def delete_urlf_profiles(skip_confirm=False):
    base_url, tenant_uuid, bearer_token, csrf_token, cookies_str = load_config()
    headers   = build_headers(bearer_token, csrf_token)
    cookies   = parse_cookies_str(cookies_str)
    summ_url  = f"{base_url}/portalapi/v1/tenants/{tenant_uuid}/sase/real-time/profile/urlf/summarize"
    temp_file = os.path.join(SCRIPT_DIR, "../temp/temp-urlf-profile.txt")

    print("\n  Fetching URLF profile objects from Concerto...")
    objects = {}
    window  = 0
    while True:
        url  = f"{summ_url}?nextWindowNumber={window}&windowSize=100"
        resp = requests.get(url, headers=headers, cookies=cookies, verify=False)
        if resp.status_code == 401:
            got_401()
            return
        if not resp.ok:
            print(f"  [ERROR] GET failed: {resp.status_code}")
            break
        data = resp.json().get("data", [])
        if not data:
            break
        count_before = len(objects)
        for item in data:
            name = item.get("name")
            uuid = item.get("uuid")
            if name and uuid:
                objects[name] = uuid
        if len(objects) == count_before:
            break
        print(f"  Window {window}: {len(objects)} object(s) collected so far")
        window += 1

    if not objects:
        print("  No URLF profile objects found.")
        return

    save_objects_to_file(objects, temp_file)

    if not skip_confirm and not confirm_delete(temp_file, "URLF Profile"):
        print("  Cancelled. No objects were deleted.")
        return

    objects = read_objects_from_file(temp_file)
    print(f"\n  Deleting {len(objects)} URLF profile object(s)...")
    for name, uuid in objects.items():
        url = f"{base_url}/portalapi/v1/tenants/{tenant_uuid}/sase/real-time/profile/urlf/{uuid}"
        safe_delete(url, headers, cookies, name)

    os.remove(temp_file)
    print(f"\n  Done. Temp file removed.")


def delete_firewall_policies(skip_confirm=False):
    base_url, tenant_uuid, bearer_token, csrf_token, cookies_str = load_config()
    headers   = build_headers(bearer_token, csrf_token)
    cookies   = parse_cookies_str(cookies_str)
    summ_url  = f"{base_url}/portalapi/v1/tenants/{tenant_uuid}/sase/real-time/internet-protection/summarize"
    temp_file = os.path.join(SCRIPT_DIR, "../temp/temp-policy.txt")

    print("\n  Fetching firewall policy objects from Concerto...")
    objects = {}
    window  = 0
    while True:
        url  = f"{summ_url}?nextWindowNumber={window}&windowSize=100"
        resp = requests.get(url, headers=headers, cookies=cookies, verify=False)
        if resp.status_code == 401:
            got_401()
            return
        if not resp.ok:
            print(f"  [ERROR] GET failed: {resp.status_code}")
            break
        data = resp.json().get("data", [])
        if not data:
            break
        count_before = len(objects)
        for item in data:
            name = item.get("name")
            uuid = item.get("uuid")
            if name and uuid:
                objects[name] = uuid
        if len(objects) == count_before:
            break
        print(f"  Window {window}: {len(objects)} object(s) collected so far")
        window += 1

    if not objects:
        print("  No firewall policy objects found.")
        return

    save_objects_to_file(objects, temp_file)

    if not skip_confirm and not confirm_delete(temp_file, "Firewall Policy"):
        print("  Cancelled. No objects were deleted.")
        return

    objects = read_objects_from_file(temp_file)
    print(f"\n  Deleting {len(objects)} firewall policy object(s)...")
    for name, uuid in objects.items():
        url = f"{base_url}/portalapi/v1/tenants/{tenant_uuid}/sase/real-time/internet-protection/{uuid}"
        safe_delete(url, headers, cookies, name)

    os.remove(temp_file)
    print(f"\n  Done. Temp file removed.")


def delete_all_objects():
    extra = []
    if QUICK_MODE:
        extra += ["", "  Mode: QUICK  — DEL requests fired without waiting for response."]
    if BOTTOM_MODE:
        extra += ["", "  Mode: BOTTOM — objects processed bottom-to-top from temp file."]

    print_box([
        "WARNING: THIS WILL DELETE ALL OBJECTS FROM CONCERTO!",
        "",
        "  Sequence: Firewall Policies → URLF Profiles →",
        "            URL Categories → Custom Services →",
        "            Address Groups",
        *extra,
        "",
        "This action is IRREVERSIBLE.",
        "Type DELETE to confirm (first confirmation).",
    ])
    first = input("→ First confirmation:  ").strip()
    if first != "DELETE":
        print("  Cancelled.")
        return

    print_box([
        "FINAL WARNING — this is your last chance to abort.",
        "Type DELETE again to confirm and begin deletion.",
    ])
    second = input("→ Second confirmation: ").strip()
    if second != "DELETE":
        print("  Cancelled.")
        return

    print("\n  Starting full deletion sequence...\n")

    print("━" * 54)
    print("  [1/5] Firewall Policies")
    print("━" * 54)
    delete_firewall_policies(skip_confirm=True)

    print("\n" + "━" * 54)
    print("  [2/5] URLF Profiles")
    print("━" * 54)
    delete_urlf_profiles(skip_confirm=True)

    print("\n" + "━" * 54)
    print("  [3/5] Custom URL Categories")
    print("━" * 54)
    delete_url_categories(skip_confirm=True)

    print("\n" + "━" * 54)
    print("  [4/5] Custom Services")
    print("━" * 54)
    delete_custom_services(skip_confirm=True)

    print("\n" + "━" * 54)
    print("  [5/5] Address Groups")
    print("━" * 54)
    delete_address_groups(skip_confirm=True)

    print("\n  All object types processed.")


def print_menu():
    flags = []
    if QUICK_MODE:
        flags.append("QUICK")
    if BOTTOM_MODE:
        flags.append("BOTTOM")
    flags_line = f"  Active flags: [{', '.join(flags)}]" if flags else ""

    print("\n╔══════════════════════════════════════════════════════╗")
    print("║          Concerto Object Deletion Tool               ║")
    if flags_line:
        print(f"║{flags_line.ljust(54)}║")
    print("╠══════════════════════════════════════════════════════╣")
    print("║   1  -  Delete all address-group objects             ║")
    print("║   2  -  Delete all custom service objects            ║")
    print("║   3  -  Delete all custom URL category objects       ║")
    print("║   4  -  Delete all URLF profile objects              ║")
    print("║   5  -  Delete all firewall policy objects           ║")
    print("║   6  -  Remove ALL of the above (5 → 4 → 3 → 2 → 1)  ║")
    print("║   R  -  Refresh token (use if you get 401 errors)    ║")
    print("║   0  -  Exit                                         ║")
    print("╚══════════════════════════════════════════════════════╝")


def main():
    if not os.path.exists(GENERAL_FILE):
        print("\n  general.txt not found. Running initial login setup...")
        run_login()

    while True:
        print_menu()
        choice = input("\n  Select option: ").strip().lower()

        if choice == "0":
            print("\n  Exiting.\n")
            sys.exit(0)
        elif choice == "1":
            delete_address_groups()
        elif choice == "2":
            delete_custom_services()
        elif choice == "3":
            delete_url_categories()
        elif choice == "4":
            delete_urlf_profiles()
        elif choice == "5":
            delete_firewall_policies()
        elif choice == "6":
            delete_all_objects()
        elif choice == "r":
            print("\n  Refreshing token...")
            run_login()
        else:
            print("\n  Invalid option. Please try again.")


if __name__ == "__main__":
    main()
