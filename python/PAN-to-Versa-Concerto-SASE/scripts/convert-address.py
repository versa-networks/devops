import ipaddress
import json
import logging
import os
import re
import shutil
import sys
import uuid
from typing import Dict, List, Optional, Tuple

import requests
from requests.packages import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
BASE_DIR     = os.path.dirname(SCRIPT_DIR)

LOG_DIR      = os.path.join(BASE_DIR, "log")
TEMP_DIR     = os.path.join(BASE_DIR, "temp")
JSON_DIR     = os.path.join(BASE_DIR, "json")
FINAL_DIR    = os.path.join(BASE_DIR, "final-data")

os.makedirs(LOG_DIR,  exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

LOG_FILE       = os.path.join(LOG_DIR,   "step-8.log")
SRC_FILE       = os.path.join(FINAL_DIR, "final-address.txt")
TEMP_FILE      = os.path.join(TEMP_DIR,  "temp-address.txt")
TEMPLATE_JSON  = os.path.join(JSON_DIR,  "post-address-config.json")
GENERAL_TXT    = os.path.join(TEMP_DIR,  "general.txt")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

def load_general_config(filepath: str) -> dict:
    config: dict = {}
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if ">>" in line:
                    key, _, value = line.partition(">>")
                else:
                    key, _, value = line.partition(":")
                config[key.strip()] = value.strip()
    except FileNotFoundError:
        log.error(f"general.txt not found: {filepath}")
        sys.exit(1)
    return config

def fix_cidr(value: str) -> str:
    value = value.strip()
    if not re.match(r'^[\d.:a-fA-F/]+$', value):
        return value

    try:
        if "/" in value:
            try:
                ipaddress.ip_network(value, strict=True)
                return value
            except ValueError:
                fixed = str(ipaddress.ip_network(value, strict=False))
                log.warning(f"  CIDR fix: {value!r} → {fixed!r}")
                return fixed
        else:
            ip  = ipaddress.ip_address(value)
            sfx = "/32" if ip.version == 4 else "/128"
            fixed = f"{value}{sfx}"
            log.warning(f"  CIDR fix: missing mask {value!r} → {fixed!r}")
            return fixed
    except ValueError:
        log.warning(f"  Cannot parse as IP, leaving as-is: {value!r}")
        return value

def parse_address_objects(filepath: str) -> Tuple[Dict, List]:
    objects: dict   = {}
    obj_order: list = []
    PATTERN = re.compile(
        r'^set\s+shared\s+address\s+'
        r'(?:"([^"]+)"|(\S+))'           # group 1=quoted name, group 2=plain name
        r'\s+(\S+)'                       # group 3=keyword
        r'(?:\s+(.+))?$',                 # group 4=value (optional)
        re.IGNORECASE,
    )

    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
    except FileNotFoundError:
        log.error(f"File not found: {filepath}")
        return objects, obj_order

    for raw in lines:
        line = raw.rstrip("\n").strip()
        if not line:
            continue

        m = PATTERN.match(line)
        if not m:
            log.warning(f"  Unrecognised line, skipped: {line!r}")
            continue

        obj_name = m.group(1) if m.group(1) else m.group(2)
        keyword  = m.group(3).lower()
        value    = m.group(4).strip() if m.group(4) else ""

        if obj_name not in objects:
            objects[obj_name] = {
                "ip_netmask":  None,
                "ip_range":    None,
                "fqdn":        None,
                "tag":         None,
                "description": None,
            }
            obj_order.append(obj_name)

        kw_map = {
            "ip-netmask":  "ip_netmask",
            "ip-range":    "ip_range",
            "fqdn":        "fqdn",
            "tag":         "tag",
            "description": "description",
        }
        if keyword in kw_map:
            objects[obj_name][kw_map[keyword]] = value
        else:
            log.debug(f"  Unknown keyword '{keyword}' for '{obj_name}', ignoring.")

    return objects, obj_order

def next_temp_payload_path(temp_dir: str) -> Tuple[str, int]:
    x = 1
    while True:
        path = os.path.join(temp_dir, f"post-address-config-{x}.json")
        if not os.path.exists(path):
            return path, x
        x += 1

def build_payload(
    obj_name: str,
    obj_data: dict,
    parent_ref_uuid: str,
) -> Optional[Dict]:
    tag = obj_data.get("tag")
    if tag:
        log.info(f"  Tag: {tag!r}")
    else:
        log.info(f"  No tag found; 'tags' field will be omitted.")

    if obj_data.get("ip_netmask"):
        raw_value       = obj_data["ip_netmask"]
        addr_value      = fix_cidr(raw_value)
        addr_type_label = "Subnet"
        addr_value_type = "IP_SUBNET"
        log.info(f"  ip-netmask: {raw_value!r} → {addr_value!r}")

    elif obj_data.get("ip_range"):
        addr_value      = obj_data["ip_range"]
        addr_type_label = "IP range"
        addr_value_type = "IP_RANGE"
        log.info(f"  ip-range: {addr_value!r}")

    elif obj_data.get("fqdn"):
        addr_value      = obj_data["fqdn"]
        addr_type_label = "FQDN"
        addr_value_type = "FQDN"
        log.info(f"  fqdn: {addr_value!r}")

    else:
        log.warning(f"  '{obj_name}' has no ip-netmask / ip-range / fqdn – skipping.")
        return None

    entity: Dict = {
        "attributes": {
            "addressCollection": {
                "value": [
                    {
                        "addressType":  {"value": addr_type_label},
                        "addressValue": [{"type": addr_value_type, "value": addr_value}],
                    }
                ]
            }
        },
        "name":     obj_name,
        "uuid":     str(uuid.uuid4()),
        "type":     "ELEMENTS",
        "subtype":  "ENDPOINT",
        "category": "ADDRESS_GROUP",
    }

    if tag:
        entity["tags"] = [tag]

    payload: Dict = {
        "entity": entity,
        "parentReference": {
            "uuid":          parent_ref_uuid,
            "name":          "Address Group",
            "type":          "FOLDER",
            "subtype":       None,
            "category":      None,
            "version":       "V1",
            "originId":      None,
            "nodeLabel":     "Address Group",
            "federatedPath": "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Elements/Endpoint/Address Group//",
        },
    }

    return payload

def post_to_concerto(
    session: requests.Session,
    concerto_url: str,
    tenant_uuid: str,
    headers: dict,
    payload: dict,
) -> Optional[requests.Response]:
    url = f"{concerto_url}/portalapi/v1/tenants/{tenant_uuid}/elements/endpoint"
    log.info(f"  POST → {url}")
    try:
        return session.post(url, verify=False, headers=headers, json=payload)
    except requests.RequestException as exc:
        log.error(f"  Request exception: {exc}")
        return None

def main() -> None:
    log.info("=" * 65)
    log.info("  Step 8 – Convert address-ip objects – START")
    log.info("=" * 65)

    config          = load_general_config(GENERAL_TXT)
    concerto_fqdn   = config.get("concerto-fqdn", "").strip().rstrip("/")
    tenant_uuid     = config.get("tenant-uuid", "")
    parent_ref_uuid = config.get("address-group-parent-ref-uuid", "")
    bearer_token    = config.get("bearer-token", "")
    csrf_token      = config.get("csrf-token", "")

    concerto_url = concerto_fqdn if concerto_fqdn.startswith("http") \
                   else f"https://{concerto_fqdn}"

    missing = [k for k, v in {
        "concerto-fqdn":                   concerto_url,
        "tenant-uuid":                     tenant_uuid,
        "address-group-parent-ref-uuid":   parent_ref_uuid,
        "bearer-token":                    bearer_token,
    }.items() if not v]
    if missing:
        log.error(f"Missing required keys in general.txt: {missing}")
        sys.exit(1)

    log.info(f"  Concerto URL : {concerto_url}")
    log.info(f"  Tenant UUID  : {tenant_uuid}")

    for path in (SRC_FILE,):
        if not os.path.isfile(path):
            log.error(f"Required file not found: {path}")
            sys.exit(1)

    shutil.copy2(SRC_FILE, TEMP_FILE)
    log.info(f"Step 3 : Copied {SRC_FILE} → {TEMP_FILE}")

    log.info("Step 4-5 : Parsing address objects…")
    objects, obj_order = parse_address_objects(TEMP_FILE)
    log.info(f"  Found {len(obj_order)} object(s): {obj_order}")

    if not obj_order:
        log.info("  No objects to process. Exiting.")
        if os.path.exists(TEMP_FILE):
            os.remove(TEMP_FILE)
        sys.exit(0)

    session = requests.Session()
    api_headers = {
        "X-CSRF-Token":  csrf_token,
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type":  "application/json",
    }

    success_count = 0
    fail_count    = 0

    for obj_name in obj_order:
        obj_data = objects[obj_name]
        log.info("-" * 65)
        log.info(f"Processing : '{obj_name}'")

        temp_payload_path, x = next_temp_payload_path(TEMP_DIR)
        log.info(f"Step 6a : Will save payload to {temp_payload_path}")

        payload = build_payload(obj_name, obj_data, parent_ref_uuid)

        if payload is None:
            log.error(f"  Could not build payload for '{obj_name}'. Skipping.")
            os.remove(temp_payload_path)
            fail_count += 1
            continue

        with open(temp_payload_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=4)
        log.info(f"  Payload saved to {temp_payload_path}")

        response = post_to_concerto(
            session, concerto_url, tenant_uuid, api_headers, payload
        )

        if response is not None:
            status = response.status_code
            snippet = response.text[:300].replace("\n", " ")
            log.info(f"Step 10b : '{obj_name}' | HTTP {status} | {snippet}")
            if status in (200, 201):
                success_count += 1
                log.info(f"  ✓ SUCCESS: '{obj_name}' created (HTTP {status})")
            else:
                fail_count += 1
                log.error(f"  ✗ FAILED : '{obj_name}' HTTP {status} – {response.text}")
        else:
            fail_count += 1
            log.error(f"  ✗ FAILED : '{obj_name}' – no response from server")

        if os.path.exists(temp_payload_path):
            os.remove(temp_payload_path)
            log.info(f"Step 11 : Deleted {temp_payload_path}")

    if os.path.exists(TEMP_FILE):
        os.remove(TEMP_FILE)
        log.info(f"Step 13 : Deleted {TEMP_FILE}")

    log.info("=" * 65)
    log.info(f"  Step 8 COMPLETE  –  Success: {success_count}  |  Failed: {fail_count}")
    log.info("=" * 65)

if __name__ == "__main__":
    main()