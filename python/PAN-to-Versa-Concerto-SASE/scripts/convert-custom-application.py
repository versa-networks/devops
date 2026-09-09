import json
import logging
import os
import re
import shutil
import sys
import uuid
from collections import OrderedDict
from typing import List, Optional

import requests
from requests.packages import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))

FINAL_CUSTOM_APP_FILE = os.path.join(BASE_DIR, "final-data", "final-custom-application.txt")
TEMP_CUSTOM_APP_FILE = os.path.join(BASE_DIR, "temp", "temp-custom-application.txt")
CUSTOM_APP_UUID_MAP = os.path.join(BASE_DIR, "temp", "custom-application-uuid.txt")
GENERAL_FILE = os.path.join(BASE_DIR, "temp", "general.txt")
LOG_DIR = os.path.join(BASE_DIR, "log")
LOG_FILE = os.path.join(LOG_DIR, "convert-custom-application.log")

CONST_APPLICATION_TYPE = "INTERNET_APPLICATION"
CONST_PRODUCTIVITY = "5"
CONST_FAMILY = "networking"
CONST_SUBFAMILY = "unknown"
CONST_SDWAN_TAGS = []
CONST_PARENT_NAME = "Custom Application"
CONST_PARENT_NODE_LABEL = "Custom Application"
CONST_PARENT_FEDERATED_PATH = (
    "ConfigurationLifecycleGraph/PROFILE_ELEMENTS/Elements/Application/Custom Application//"
)

os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("convert-custom-application")


def read_general_file(path: str) -> dict:
    data = {}
    if not os.path.isfile(path):
        log.error("general.txt not found at %s", path)
        sys.exit(1)
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ">>" in line:
                key, _, value = line.partition(">>")
                data[key.strip()] = value.strip()
    return data


def build_session_and_headers(general: dict):
    bearer_token = general.get("bearer-token", "")
    csrf_token = general.get("csrf-token", "")
    cookies_str = general.get("cookies", "")
    if not bearer_token:
        log.error("Missing required key in general.txt: {bearer-token}")
        sys.exit(1)
    if not csrf_token:
        log.error("Missing required key in general.txt: {csrf-token}")
        sys.exit(1)

    session = requests.Session()
    if cookies_str:
        for chunk in cookies_str.split(";"):
            chunk = chunk.strip()
            if "=" in chunk:
                k, _, v = chunk.partition("=")
                session.cookies.set(k.strip(), v.strip())

    headers = {
        "X-CSRF-Token": csrf_token,
        "Authorization": "Bearer " + bearer_token,
        "Content-Type": "application/json",
    }
    return session, headers


def find_uuid_by_name(nodes, target_name: str) -> Optional[str]:
    for node in nodes:
        if node.get("name") == target_name:
            return node.get("uuid")
        children = node.get("nodes", [])
        if children:
            result = find_uuid_by_name(children, target_name)
            if result:
                return result
    return None


def fetch_parent_ref_uuid(session, headers, concerto_url: str, tenant_uuid: str) -> Optional[str]:
    endpoint = (
        concerto_url + "/portalapi/v1/tenants/" + tenant_uuid +
        "/configuration/perspective/profile-elements"
    )
    log.info("Discovering '%s' folder UUID: GET %s", CONST_PARENT_NAME, endpoint)
    resp = session.get(endpoint, verify=False, cookies=session.cookies, headers=headers)
    if not resp.ok:
        log.error("Perspective lookup failed - HTTP %s - %s", resp.status_code, resp.text[:300])
        return None
    nodes = resp.json().get("perspective", [])
    return find_uuid_by_name(nodes, CONST_PARENT_NAME)


def tokenize_value_list(raw: str) -> List[str]:
    raw = raw.strip()
    if not raw:
        return []
    if raw.startswith("["):
        raw = raw[1:]
        end = raw.rfind("]")
        if end != -1:
            raw = raw[:end]
    out: List[str] = []
    i = 0
    n = len(raw)
    while i < n:
        c = raw[i]
        if c.isspace():
            i += 1
            continue
        if c == '"':
            j = raw.find('"', i + 1)
            if j == -1:
                out.append(raw[i + 1:].strip())
                break
            out.append(raw[i + 1:j])
            i = j + 1
        else:
            j = i
            while j < n and not raw[j].isspace():
                j += 1
            out.append(raw[i:j])
            i = j
    return [t for t in out if t]


def sanitize_name(name: str) -> str:
    return re.sub(r'[^A-Za-z0-9]', "_", name)


def group_application_objects(lines: List[str]) -> "OrderedDict[str, List[str]]":
    groups: "OrderedDict[str, List[str]]" = OrderedDict()
    pattern = re.compile(r'^\s*set\s+shared\s+application\s+("([^"]+)"|(\S+))\s')
    for line in lines:
        line = line.rstrip("\n")
        if not line.strip():
            continue
        m = pattern.match(line)
        if not m:
            log.warning("Unrecognised config line (skipped): %s", line)
            continue
        obj_name = m.group(2) if m.group(2) is not None else m.group(3)
        groups.setdefault(obj_name, []).append(line)
    return groups


def split_protocol_port(member: str):
    member = member.strip()
    m = re.match(r'^(tcp|udp)/(.+)$', member, re.IGNORECASE)
    if m:
        return m.group(1).upper(), m.group(2)
    return None, None


def extract_app_params(obj_name: str, config_lines: List[str]) -> dict:
    params = {
        "port_members": [],
        "risk": None,
        "description": None,
        "tag": None,
        "ip_prefix": None,
        "host_pattern": None,
        "source_port": None,
    }
    for line in config_lines:
        m = re.search(r'\bdefault\s+port\s+(.*)$', line, re.IGNORECASE)
        if m:
            for member in tokenize_value_list(m.group(1)):
                proto, port = split_protocol_port(member)
                if proto:
                    params["port_members"].append((proto, port))
            continue

        m = re.search(r'\brisk\s+(\d+)', line, re.IGNORECASE)
        if m:
            params["risk"] = m.group(1)
            continue

        m = re.search(r'\bdescription\s+"([^"]*)"', line, re.IGNORECASE)
        if m:
            params["description"] = m.group(1)
            continue
        m = re.search(r'\bdescription\s+(\S+)', line, re.IGNORECASE)
        if m:
            params["description"] = m.group(1)
            continue

        m = re.search(r'\btag\s+\[([^\]]+)\]', line, re.IGNORECASE)
        if m:
            params["tag"] = m.group(1).strip().split()
            continue
        m = re.search(r'\btag\s+"([^"]+)"', line, re.IGNORECASE)
        if m:
            params["tag"] = [m.group(1)]
            continue
        m = re.search(r'\btag\s+(\S+)', line, re.IGNORECASE)
        if m:
            params["tag"] = [m.group(1)]
            continue

        m = re.search(r'\bip-prefix\s+(\S+)', line, re.IGNORECASE)
        if m:
            params["ip_prefix"] = m.group(1)
            continue

        m = re.search(r'\bhost\s+"([^"]+)"', line, re.IGNORECASE)
        if m:
            params["host_pattern"] = m.group(1)
            continue

        m = re.search(r'\bsource-port\s+(\S+)', line, re.IGNORECASE)
        if m:
            params["source_port"] = m.group(1)
            continue

    return params


def build_application_info_entry(proto: Optional[str], dest_port: Optional[str], params: dict) -> dict:
    entry = OrderedDict()
    if params["ip_prefix"]:
        entry["ipAddress"] = {"value": params["ip_prefix"]}
    if proto:
        entry["protocol"] = proto
    if params["risk"]:
        entry["risk"] = params["risk"]
    entry["productivity"] = CONST_PRODUCTIVITY
    entry["sdwanTags"] = list(CONST_SDWAN_TAGS)
    entry["family"] = CONST_FAMILY
    entry["subFamily"] = CONST_SUBFAMILY
    if params["host_pattern"]:
        entry["fqdn"] = {"value": params["host_pattern"]}
    ports_value = OrderedDict()
    if params["source_port"]:
        ports_value["sourcePort"] = {"value": params["source_port"]}
    if dest_port:
        ports_value["destinationPort"] = {"value": dest_port}
    if ports_value:
        entry["ports"] = {"value": ports_value}
    return entry


def build_payload(obj_name: str, params: dict, parent_ref_uuid: str) -> dict:
    info_list: List[dict] = []
    if params["port_members"]:
        for proto, port in params["port_members"]:
            info_list.append(build_application_info_entry(proto, port, params))
    else:
        info_list.append(build_application_info_entry(None, None, params))

    attributes = OrderedDict()
    attributes["applicationType"] = {"value": CONST_APPLICATION_TYPE}
    attributes["applicationInfo"] = {"value": info_list}

    entity = OrderedDict()
    entity["attributes"] = attributes
    entity["name"] = sanitize_name(obj_name)
    entity["description"] = params["description"] if params["description"] else ""
    entity["tags"] = params["tag"] if params["tag"] else []
    entity["uuid"] = str(uuid.uuid4())
    entity["type"] = "ELEMENTS"
    entity["subtype"] = "APPLICATION"
    entity["category"] = "CUSTOM_APPLICATION"

    parent_reference = OrderedDict()
    parent_reference["uuid"] = parent_ref_uuid
    parent_reference["name"] = CONST_PARENT_NAME
    parent_reference["type"] = "FOLDER"
    parent_reference["subtype"] = None
    parent_reference["category"] = None
    parent_reference["version"] = "V1"
    parent_reference["originId"] = None
    parent_reference["nodeLabel"] = CONST_PARENT_NODE_LABEL
    parent_reference["federatedPath"] = CONST_PARENT_FEDERATED_PATH

    return {"entity": entity, "parentReference": parent_reference}


def post_application(session, headers, concerto_url: str, tenant_uuid: str,
                     obj_name: str, payload: dict) -> bool:
    url = (
        concerto_url + "/portalapi/v1/tenants/" + tenant_uuid + "/elements/application"
    )
    log.info("[%s] POST -> %s", obj_name, url)
    resp = session.post(
        url,
        verify=False,
        cookies=session.cookies,
        headers=headers,
        data=json.dumps(payload),
    )
    if resp.ok:
        log.info("[%s] POST success - HTTP %s", obj_name, resp.status_code)
        return True
    log.error("[%s] POST failed - HTTP %s - %s", obj_name, resp.status_code, resp.text)
    return False


def main() -> int:
    log.info("=" * 70)
    log.info("Convert custom application objects -> Concerto API")
    log.info("=" * 70)

    if not os.path.isfile(FINAL_CUSTOM_APP_FILE) or os.path.getsize(FINAL_CUSTOM_APP_FILE) == 0:
        log.warning("Source file not found or empty: %s - nothing to do.", FINAL_CUSTOM_APP_FILE)
        return 0

    os.makedirs(os.path.dirname(TEMP_CUSTOM_APP_FILE), exist_ok=True)
    shutil.copy2(FINAL_CUSTOM_APP_FILE, TEMP_CUSTOM_APP_FILE)

    general = read_general_file(GENERAL_FILE)
    for key in ["concerto-fqdn", "tenant-uuid", "bearer-token", "csrf-token"]:
        if key not in general:
            log.error("Missing required key in general.txt: {%s}", key)
            sys.exit(1)

    concerto_url = general["concerto-fqdn"].rstrip("/")
    if not concerto_url.startswith("http://") and not concerto_url.startswith("https://"):
        concerto_url = "https://" + concerto_url
    tenant_uuid = general["tenant-uuid"]

    session, headers = build_session_and_headers(general)

    parent_ref_uuid = fetch_parent_ref_uuid(session, headers, concerto_url, tenant_uuid)
    if not parent_ref_uuid:
        log.error("Could not resolve the '%s' folder UUID from the perspective tree. Aborting.",
                  CONST_PARENT_NAME)
        return 1
    log.info("Resolved '%s' folder UUID: %s", CONST_PARENT_NAME, parent_ref_uuid)

    with open(TEMP_CUSTOM_APP_FILE, "r", encoding="utf-8") as f:
        raw_lines = f.read().splitlines()

    app_groups = group_application_objects(raw_lines)
    total = len(app_groups)
    log.info("Found %d custom application object(s) to process.", total)

    success_count = 0
    fail_count = 0
    created_map = OrderedDict()
    for idx, (obj_name, config_lines) in enumerate(app_groups.items(), start=1):
        log.info("-" * 60)
        log.info("Processing [%d/%d]: %s", idx, total, obj_name)
        params = extract_app_params(obj_name, config_lines)
        payload = build_payload(obj_name, params, parent_ref_uuid)
        ok = post_application(session, headers, concerto_url, tenant_uuid, obj_name, payload)
        if ok:
            success_count += 1
            created_map[obj_name] = payload["entity"]["uuid"]
        else:
            fail_count += 1

    os.makedirs(os.path.dirname(CUSTOM_APP_UUID_MAP), exist_ok=True)
    with open(CUSTOM_APP_UUID_MAP, "w", encoding="utf-8") as f:
        for name, app_uuid in created_map.items():
            f.write(name + " >> " + app_uuid + "\n")
    log.info("Wrote %d custom-application name->uuid mapping(s) to: %s",
             len(created_map), CUSTOM_APP_UUID_MAP)

    if os.path.isfile(TEMP_CUSTOM_APP_FILE):
        os.remove(TEMP_CUSTOM_APP_FILE)

    log.info("=" * 70)
    log.info("Done. Success: %d  |  Failed: %d  |  Total: %d",
             success_count, fail_count, total)
    log.info("=" * 70)
    return 0


if __name__ == "__main__":
    main()
