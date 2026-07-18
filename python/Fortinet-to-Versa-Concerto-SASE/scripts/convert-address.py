#!/usr/bin/env python3
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

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
LOG_DIR = os.path.join(BASE_DIR, "log")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
FINAL_DIR = os.path.join(BASE_DIR, "final-data")

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "step-8.log")
SRC_FILE = os.path.join(FINAL_DIR, "final-address.txt")
TEMP_FILE = os.path.join(TEMP_DIR, "temp-address.txt")
GENERAL_TXT = os.path.join(TEMP_DIR, "general.txt")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


def load_general_config(filepath):
    config = {}
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if " >> " in line:
                    key, _, value = line.partition(" >> ")
                    config[key.strip()] = value.strip()
                elif ":" in line and ">>" not in line:
                    pass
    except FileNotFoundError:
        log.error("general.txt not found: %s", filepath)
        sys.exit(1)
    return config


def netmask_to_prefix(netmask):
    bits = 0
    for octet in netmask.split("."):
        bits += bin(int(octet)).count("1")
    return bits


def forti_subnet_to_cidr(value):
    value = value.strip()
    if "/" in value:
        return value
    parts = value.split()
    if len(parts) == 2:
        return "{}/{}".format(parts[0], netmask_to_prefix(parts[1]))
    return value


def fix_cidr(value):
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
                log.warning("  CIDR fix: %r -> %r", value, fixed)
                return fixed
        else:
            ip = ipaddress.ip_address(value)
            sfx = "/32" if ip.version == 4 else "/128"
            fixed = "{}{}".format(value, sfx)
            log.warning("  CIDR fix: missing mask %r -> %r", value, fixed)
            return fixed
    except ValueError:
        log.warning("  Cannot parse as IP, leaving as-is: %r", value)
        return value


ADDR_RE = re.compile(
    r'^\s*firewall\s+address\s+("([^"]+)"|(\S+))\s+(\S+)\s*(.*)\s*$'
)


def parse_address_objects(filepath):
    objects = {}
    obj_order = []

    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
    except FileNotFoundError:
        log.error("File not found: %s", filepath)
        return objects, obj_order

    for raw in lines:
        line = raw.rstrip("\n").strip()
        if not line:
            continue

        m = ADDR_RE.match(line)
        if not m:
            continue

        obj_name = m.group(2) if m.group(2) else m.group(3)
        keyword = m.group(4).lower()
        rest = m.group(5).strip() if m.group(5) else ""

        if obj_name not in objects:
            objects[obj_name] = {
                "ip_netmask": None, "ip_range": None, "fqdn": None,
                "tag": None, "description": None,
                "start_ip": None, "end_ip": None,
            }
            obj_order.append(obj_name)

        if keyword == "subnet":
            objects[obj_name]["ip_netmask"] = forti_subnet_to_cidr(rest)
        elif keyword == "fqdn":
            objects[obj_name]["fqdn"] = rest.strip('"')
        elif keyword == "start-ip":
            objects[obj_name]["start_ip"] = rest
        elif keyword == "end-ip":
            objects[obj_name]["end_ip"] = rest
        elif keyword == "comment":
            objects[obj_name]["description"] = rest.strip('"')
        elif keyword in ("tag", "tagging"):
            objects[obj_name]["tag"] = rest.strip('"')
        elif keyword == "type":
            pass

    for name in obj_order:
        obj = objects[name]
        if obj["start_ip"] and obj["end_ip"] and not obj["ip_range"]:
            obj["ip_range"] = "{}-{}".format(obj["start_ip"], obj["end_ip"])

    return objects, obj_order


def build_payload(obj_name, obj_data, parent_ref_uuid):
    tag = obj_data.get("tag")
    if obj_data.get("ip_netmask"):
        raw_value = obj_data["ip_netmask"]
        addr_value = fix_cidr(raw_value)
        addr_type_label = "Subnet"
        addr_value_type = "IP_SUBNET"
        log.info("  ip-netmask: %r -> %r", raw_value, addr_value)
    elif obj_data.get("ip_range"):
        addr_value = obj_data["ip_range"]
        addr_type_label = "IP range"
        addr_value_type = "IP_RANGE"
        log.info("  ip-range: %r", addr_value)
    elif obj_data.get("fqdn"):
        addr_value = obj_data["fqdn"]
        addr_type_label = "FQDN"
        addr_value_type = "FQDN"
        log.info("  fqdn: %r", addr_value)
    else:
        log.warning("  '%s' has no subnet/fqdn/range - skipping.", obj_name)
        return None

    entity = {
        "attributes": {
            "addressCollection": {
                "value": [
                    {
                        "addressType": {"value": addr_type_label},
                        "addressValue": [{"type": addr_value_type, "value": addr_value}],
                    }
                ]
            }
        },
        "name": obj_name,
        "uuid": str(uuid.uuid4()),
        "type": "ELEMENTS",
        "subtype": "ENDPOINT",
        "category": "ADDRESS_GROUP",
    }
    if tag:
        entity["tags"] = [tag]

    payload = {
        "entity": entity,
        "parentReference": {
            "uuid": parent_ref_uuid,
            "name": "Address Group",
            "type": "FOLDER",
            "subtype": None,
            "category": None,
            "version": "V1",
            "originId": None,
            "nodeLabel": "Address Group",
            "federatedPath": "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Elements/Endpoint/Address Group//",
        },
    }
    return payload


def post_to_concerto(session, concerto_url, tenant_uuid, headers, payload):
    url = "{}/portalapi/v1/tenants/{}/elements/endpoint".format(concerto_url, tenant_uuid)
    log.info("  POST -> %s", url)
    try:
        return session.post(url, verify=False, headers=headers, json=payload)
    except requests.RequestException as exc:
        log.error("  Request exception: %s", exc)
        return None


def main():
    log.info("=" * 65)
    log.info("  Convert Fortinet address objects -> Concerto API")
    log.info("=" * 65)

    config = load_general_config(GENERAL_TXT)
    concerto_fqdn = config.get("concerto-fqdn", "").strip().rstrip("/")
    tenant_uuid = config.get("tenant-uuid", "")
    parent_ref_uuid = config.get("address-group-parent-ref-uuid", "")
    bearer_token = config.get("bearer-token", "")
    csrf_token = config.get("csrf-token", "")

    concerto_url = concerto_fqdn if concerto_fqdn.startswith("http") else "https://{}".format(concerto_fqdn)

    missing = [k for k, v in {
        "concerto-fqdn": concerto_url,
        "tenant-uuid": tenant_uuid,
        "address-group-parent-ref-uuid": parent_ref_uuid,
        "bearer-token": bearer_token,
    }.items() if not v]
    if missing:
        log.error("Missing required keys in general.txt: %s", missing)
        sys.exit(1)

    if not os.path.isfile(SRC_FILE) or os.path.getsize(SRC_FILE) == 0:
        log.info("Source file not found or empty: %s - nothing to do.", SRC_FILE)
        sys.exit(0)

    shutil.copy2(SRC_FILE, TEMP_FILE)
    log.info("Copied %s -> %s", SRC_FILE, TEMP_FILE)

    objects, obj_order = parse_address_objects(TEMP_FILE)
    log.info("Found %d address object(s): %s", len(obj_order), obj_order)

    if not obj_order:
        log.info("No objects to process. Exiting.")
        if os.path.exists(TEMP_FILE):
            os.remove(TEMP_FILE)
        sys.exit(0)

    session = requests.Session()
    api_headers = {
        "X-CSRF-Token": csrf_token,
        "Authorization": "Bearer " + bearer_token,
        "Content-Type": "application/json",
    }

    success_count = 0
    fail_count = 0

    for obj_name in obj_order:
        obj_data = objects[obj_name]
        log.info("-" * 65)
        log.info("Processing: '%s'", obj_name)

        payload = build_payload(obj_name, obj_data, parent_ref_uuid)
        if payload is None:
            fail_count += 1
            continue

        temp_payload_path = os.path.join(TEMP_DIR, "post-address-config.json")
        with open(temp_payload_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=4)

        response = post_to_concerto(session, concerto_url, tenant_uuid, api_headers, payload)

        if response is not None:
            status = response.status_code
            snippet = response.text[:300].replace("\n", " ")
            log.info("  '%s' | HTTP %s | %s", obj_name, status, snippet)
            if status in (200, 201):
                success_count += 1
            else:
                fail_count += 1
        else:
            fail_count += 1

        if os.path.exists(temp_payload_path):
            os.remove(temp_payload_path)

    if os.path.exists(TEMP_FILE):
        os.remove(TEMP_FILE)

    log.info("=" * 65)
    log.info("  COMPLETE - Success: %d | Failed: %d", success_count, fail_count)
    log.info("=" * 65)


if __name__ == "__main__":
    main()
