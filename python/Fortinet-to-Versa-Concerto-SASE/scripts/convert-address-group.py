#!/usr/bin/env python3
import copy
import glob
import ipaddress
import uuid as uuidlib
import json
import logging
import os
import re
import shutil
import sys
from typing import Dict, List, Optional, Tuple

import requests
from requests.packages import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
LOG_DIR = os.path.join(BASE_DIR, "log")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
DATA_DIR = os.path.join(BASE_DIR, "final-data")
JSON_DIR = os.path.join(BASE_DIR, "json", "address-group")

FINAL_ADDR_GROUP = os.path.join(DATA_DIR, "final-address-group.txt")
FINAL_ADDR = os.path.join(DATA_DIR, "final-address.txt")
TEMP_ADDR_GROUP = os.path.join(TEMP_DIR, "temp-address-group.txt")
GENERAL_TXT = os.path.join(TEMP_DIR, "general.txt")
JSON_TEMPLATE = os.path.join(JSON_DIR, "post-address-config.json")
MERGED_JSON = os.path.join(TEMP_DIR, "merged-address-group.json")
LOG_FILE = os.path.join(LOG_DIR, "step-8.log")

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

GRP_RE = re.compile(r'^\s*firewall\s+addrgrp\s+("([^"]+)"|(\S+))\s+(\S+)\s*(.*)\s*$')
ADDR_RE = re.compile(r'^\s*firewall\s+address\s+("([^"]+)"|(\S+))\s+(\S+)\s*(.*)\s*$')


def read_general_txt(path):
    cfg = {}
    if not os.path.isfile(path):
        log.error("general.txt not found: %s", path)
        return cfg
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if " >> " in line:
                key, _, val = line.partition(" >> ")
                cfg[key.strip()] = val.strip()
    return cfg


def parse_quoted_tokens(text):
    tokens = []
    i = 0
    text = text.strip()
    while i < len(text):
        if text[i] == '"':
            end = text.find('"', i + 1)
            if end == -1:
                tokens.append(text[i + 1:])
                break
            tokens.append(text[i + 1:end])
            i = end + 1
        elif text[i] in (' ', '\t', '[', ']'):
            i += 1
        else:
            end = i
            while end < len(text) and text[end] not in (' ', '\t', '[', ']', '"'):
                end += 1
            tokens.append(text[i:end])
            i = end
    return tokens


def parse_address_group_file(path):
    objects = {}
    if not os.path.isfile(path):
        log.error("Address-group file not found: %s", path)
        return objects
    with open(path, encoding="utf-8") as fh:
        lines = fh.readlines()
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        m = GRP_RE.match(line)
        if not m:
            continue
        name = m.group(2) if m.group(2) else m.group(3)
        keyword = m.group(4).lower()
        rest = m.group(5).strip() if m.group(5) else ""
        if name not in objects:
            objects[name] = {"static": [], "tag": None, "description": None}
        if keyword == "member":
            members = parse_quoted_tokens(rest)
            objects[name]["static"].extend(members)
        elif keyword in ("tag", "tagging"):
            tokens = parse_quoted_tokens(rest)
            if tokens:
                objects[name]["tag"] = tokens[0]
        elif keyword == "comment":
            objects[name]["description"] = rest.strip('"')
    log.info("Parsed %d address-group object(s) from %s", len(objects), path)
    return objects


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


def parse_address_file(path):
    addrs = {}
    if not os.path.isfile(path):
        log.error("Address file not found: %s", path)
        return addrs
    with open(path, encoding="utf-8") as fh:
        lines = fh.readlines()
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        m = ADDR_RE.match(line)
        if not m:
            continue
        name = m.group(2) if m.group(2) else m.group(3)
        keyword = m.group(4).lower()
        rest = m.group(5).strip() if m.group(5) else ""
        if name not in addrs:
            addrs[name] = {"type": None, "value": None, "start_ip": None, "end_ip": None}
        if keyword == "subnet":
            addrs[name]["type"] = "ip-netmask"
            addrs[name]["value"] = forti_subnet_to_cidr(rest)
        elif keyword == "fqdn":
            addrs[name]["type"] = "fqdn"
            addrs[name]["value"] = rest.strip('"')
        elif keyword == "start-ip":
            addrs[name]["start_ip"] = rest
        elif keyword == "end-ip":
            addrs[name]["end_ip"] = rest
    for name in addrs:
        a = addrs[name]
        if a["start_ip"] and a["end_ip"] and a["type"] is None:
            a["type"] = "ip-range"
            a["value"] = "{}-{}".format(a["start_ip"], a["end_ip"])
    log.info("Parsed %d address object(s) from %s", len(addrs), path)
    return addrs


def resolve_group(name, all_groups, visited=None):
    if visited is None:
        visited = set()
    if name in visited:
        return []
    visited.add(name)
    result = []
    if name not in all_groups:
        return [name]
    for member in all_groups[name]["static"]:
        if member in all_groups:
            result.extend(resolve_group(member, all_groups, visited))
        else:
            result.append(member)
    return result


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
                return str(ipaddress.ip_network(value, strict=False))
        else:
            ip = ipaddress.ip_address(value)
            sfx = "/32" if ip.version == 4 else "/128"
            return "{}{}".format(value, sfx)
    except ValueError:
        return value


def build_payload(grp_name, grp_data, ip_names, addresses, template_str, parent_uuid):
    addr_entries = []
    for ip_name in ip_names:
        if ip_name not in addresses:
            log.warning("  IP object '%s' not found in address file - skipping member", ip_name)
            continue
        a = addresses[ip_name]
        atype = a.get("type")
        avalue = a.get("value", "")
        if not atype or not avalue:
            continue
        if atype == "ip-netmask":
            addr_entries.append({
                "addressType": {"value": "Subnet"},
                "addressValue": [{"type": "IP_SUBNET", "value": fix_cidr(avalue)}],
            })
        elif atype == "ip-range":
            addr_entries.append({
                "addressType": {"value": "IP range"},
                "addressValue": [{"type": "IP_RANGE", "value": avalue}],
            })
        elif atype == "fqdn":
            addr_entries.append({
                "addressType": {"value": "FQDN"},
                "addressValue": [{"type": "FQDN", "value": avalue}],
            })

    if not addr_entries:
        log.warning("  No valid address entries for group '%s'", grp_name)
        return None

    entity = {
        "attributes": {
            "addressCollection": {
                "value": addr_entries
            }
        },
        "name": grp_name,
        "uuid": str(uuidlib.uuid4()),
        "type": "ELEMENTS",
        "subtype": "ENDPOINT",
        "category": "ADDRESS_GROUP",
    }

    tag = grp_data.get("tag")
    if tag:
        entity["tags"] = [tag]

    payload = {
        "entity": entity,
        "parentReference": {
            "uuid": parent_uuid,
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


def build_session(cfg):
    session = requests.Session()
    bearer = cfg.get("bearer-token", "")
    csrf = cfg.get("csrf-token", "")
    raw_cookies = cfg.get("cookies", "")
    session.headers.update({
        "Authorization": "Bearer {}".format(bearer),
        "X-CSRF-Token": csrf,
        "Content-Type": "application/json",
    })
    if raw_cookies:
        for pair in raw_cookies.split(";"):
            pair = pair.strip()
            if "=" in pair:
                k, _, v = pair.partition("=")
                session.cookies.set(k.strip(), v.strip())
    return session


def post_to_concerto(session, url, payload, grp_name):
    log.info("POST -> %s  [group: %s]", url, grp_name)
    try:
        resp = session.post(url, json=payload, verify=False, timeout=30)
        log.info("Response for '%s': HTTP %s  body: %s", grp_name, resp.status_code, resp.text[:400])
        return resp.status_code, resp.text
    except requests.RequestException as exc:
        log.error("Request exception for group '%s': %s", grp_name, exc)
        return None, str(exc)


def main():
    log.info("=" * 70)
    log.info("Convert Fortinet address-group objects -> Concerto API")
    log.info("=" * 70)

    required = {
        "final-address-group": FINAL_ADDR_GROUP,
        "final-address": FINAL_ADDR,
        "JSON template": JSON_TEMPLATE,
        "general.txt": GENERAL_TXT,
    }
    missing = [label for label, path in required.items() if not os.path.isfile(path)]
    if missing:
        for label in missing:
            log.error("Required file missing: %s (%s)", label, required[label])
        sys.exit(1)

    shutil.copy2(FINAL_ADDR_GROUP, TEMP_ADDR_GROUP)
    log.info("Copied %s -> %s", FINAL_ADDR_GROUP, TEMP_ADDR_GROUP)

    cfg = read_general_txt(GENERAL_TXT)
    parent_uuid = cfg.get("address-group-parent-ref-uuid", "")
    concerto_fqdn = cfg.get("concerto-fqdn", "")
    tenant_uuid = cfg.get("tenant-uuid", "")
    post_url = "https://{}/portalapi/v1/tenants/{}/elements/endpoint".format(concerto_fqdn, tenant_uuid)

    all_groups = parse_address_group_file(FINAL_ADDR_GROUP)
    addresses = parse_address_file(FINAL_ADDR)
    template_str = open(JSON_TEMPLATE, encoding="utf-8").read()

    for old in glob.glob(os.path.join(TEMP_DIR, "post-address-config-*.json")):
        os.remove(old)

    session = build_session(cfg)
    json_counter = 1
    grp_names = list(all_groups.keys())
    log.info("Total address-group objects to process: %d", len(grp_names))

    for grp_name in grp_names:
        log.info("-" * 60)
        log.info("Processing group '%s'", grp_name)
        grp_data = all_groups[grp_name]

        raw_words = grp_data.get("static", [])
        resolved = []
        for word in raw_words:
            if word in all_groups:
                expanded = resolve_group(word, all_groups)
                resolved.extend(expanded)
            else:
                resolved.append(word)

        seen = set()
        deduped = []
        for item in resolved:
            if item not in seen:
                seen.add(item)
                deduped.append(item)
        log.info("Final IP list for '%s': %s", grp_name, deduped)

        payload = build_payload(grp_name, grp_data, deduped, addresses, template_str, parent_uuid)
        if payload is None:
            log.error("Skipping group '%s' - could not build payload", grp_name)
            json_counter += 1
            continue

        out_json = os.path.join(TEMP_DIR, "post-address-config-{}.json".format(json_counter))
        with open(out_json, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)

        json_counter += 1
        status, body = post_to_concerto(session, post_url, payload, grp_name)
        log.info("Result | group='%s' | status=%s", grp_name, status)

        for tmp in glob.glob(os.path.join(TEMP_DIR, "post-address-config-*.json")):
            os.remove(tmp)

    if os.path.isfile(TEMP_ADDR_GROUP):
        os.remove(TEMP_ADDR_GROUP)

    log.info("=" * 70)
    log.info("Address-group converter COMPLETE")
    log.info("=" * 70)


if __name__ == "__main__":
    main()
