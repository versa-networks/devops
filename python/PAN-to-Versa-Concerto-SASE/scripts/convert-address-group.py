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
BASE_DIR   = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
LOG_DIR    = os.path.join(BASE_DIR, "log")
TEMP_DIR   = os.path.join(BASE_DIR, "temp")
DATA_DIR   = os.path.join(BASE_DIR, "final-data")
JSON_DIR   = os.path.join(BASE_DIR, "json/address-group")

FINAL_ADDR_GROUP = os.path.join(DATA_DIR, "final-address-group.txt")
FINAL_ADDR       = os.path.join(DATA_DIR, "final-address.txt")
TEMP_ADDR_GROUP  = os.path.join(TEMP_DIR, "temp-address-group.txt")
GENERAL_TXT      = os.path.join(TEMP_DIR, "general.txt")
JSON_TEMPLATE    = os.path.join(JSON_DIR, "post-address-config.json")
MERGED_JSON      = os.path.join(TEMP_DIR, "merged-address-group.json")
LOG_FILE         = os.path.join(LOG_DIR, "step-8.log")

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

def read_general_txt(path: str) -> Dict[str, str]:
    cfg: Dict[str, str] = {}
    if not os.path.isfile(path):
        log.error("general.txt not found: %s", path)
        return cfg
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if ">>" in line:
                key, _, val = line.partition(">>")
                cfg[key.strip()] = val.strip()
            elif "=" in line:
                key, _, val = line.partition("=")
                cfg[key.strip()] = val.strip()
    log.debug("general.txt loaded – keys: %s", list(cfg.keys()))
    return cfg

def parse_address_group_file(path: str) -> Dict[str, dict]:
    objects: Dict[str, dict] = {}
    if not os.path.isfile(path):
        log.error("Address-group file not found: %s", path)
        return objects
    with open(path, encoding="utf-8") as fh:
        lines = fh.readlines()

    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        m = re.match(
            r"^set\s+shared\s+address-group\s+(\S+)\s+(static|tag|description)\s+(.*)",
            line,
            re.IGNORECASE,
        )
        if not m:
            log.warning("Unrecognised / non-matching line (skipped): %s", line)
            continue

        name    = m.group(1)
        keyword = m.group(2).lower()
        rest    = m.group(3).strip()

        if name not in objects:
            objects[name] = {"static": [], "tag": None, "description": None}

        if keyword == "static":
            inner = re.search(r"\[(.+?)\]", rest)
            words = inner.group(1).split() if inner else rest.split()
            objects[name]["static"].extend(words)

        elif keyword == "tag":
            tokens = rest.split()
            if tokens:
                objects[name]["tag"] = tokens[0]

        elif keyword == "description":
            objects[name]["description"] = rest

    log.info("Parsed %d address-group object(s) from %s", len(objects), path)
    return objects

def parse_address_file(path: str) -> Dict[str, dict]:
    addrs: Dict[str, dict] = {}
    if not os.path.isfile(path):
        log.error("Address file not found: %s", path)
        return addrs
    with open(path, encoding="utf-8") as fh:
        lines = fh.readlines()

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        m = re.match(
            r"^set\s+shared\s+address\s+(\S+)\s+(ip-netmask|ip-range|fqdn)\s+(\S+)",
            line,
            re.IGNORECASE,
        )
        if m:
            name, atype, value = m.group(1), m.group(2).lower(), m.group(3)
            addrs[name] = {"type": atype, "value": value}

    log.info("Parsed %d address object(s) from %s", len(addrs), path)
    return addrs

def resolve_group(
    name: str,
    all_groups: Dict[str, dict],
    visited: Optional[set] = None,
) -> List[str]:
    if visited is None:
        visited = set()
    if name in visited:
        log.warning("Circular reference detected for group '%s' – breaking cycle", name)
        return []

    visited = visited | {name}

    if name not in all_groups:
        return [name]

    result: List[str] = []
    for word in all_groups[name].get("static", []):
        if word in all_groups:
            log.debug("  Expanding nested group '%s' → inside '%s'", word, name)
            result.extend(resolve_group(word, all_groups, visited))
        else:
            result.append(word)

    seen: set = set()
    deduped: List[str] = []
    for item in result:
        if item not in seen:
            seen.add(item)
            deduped.append(item)

    return deduped

_TYPE_MAP = {
    "ip-netmask": {"value_type": "IP_SUBNET", "display_type": "Subnet"},
    "ip-range":   {"value_type": "IP_RANGE",  "display_type": "IP range"},
    "fqdn":       {"value_type": "FQDN",      "display_type": "FQDN"},
}

def fix_cidr(value: str) -> str:
    original = value
    try:
        if "/" not in value:
            value = value + "/32"
            log.debug("CIDR fix: '%s' → '%s' (added /32)", original, value)
            return value
        network = ipaddress.IPv4Network(value, strict=False)
        fixed = str(network)
        if fixed != value:
            log.warning("CIDR fix: '%s' → '%s' (host bits zeroed)", value, fixed)
        return fixed

    except ValueError as exc:
        log.error("CIDR validation error for '%s': %s – keeping original", original, exc)
        return original

def get_address_entry(ip_name: str, addresses: Dict[str, dict]) -> Optional[dict]:
    if ip_name not in addresses:
        log.warning("IP object '%s' not found in address file – skipping", ip_name)
        return None
    addr  = addresses[ip_name]
    atype = addr["type"]
    meta  = _TYPE_MAP.get(atype, {"value_type": "IP_SUBNET", "display_type": "Subnet"})

    value = addr["value"]
    if atype == "ip-netmask":
        value = fix_cidr(value)

    log.debug("    Resolved '%s' → type=%s  value=%s", ip_name, atype, value)
    return {
        "name":         ip_name,
        "value":        value,
        "value_type":   meta["value_type"],
        "display_type": meta["display_type"],
    }

def fill_group_markers(template_str: str, grp_name: str, tag: Optional[str], parent_uuid: str) -> str:
    result = template_str
    result = result.replace("@address-group-parent-reference-uuid", parent_uuid)
    result = result.replace("@address-group-name",                  grp_name)
    result = result.replace("@address-group-uuid",                  str(uuidlib.uuid4()))
    if tag:
        result = result.replace("@address-group-tag", tag)
    else:
        result = re.sub(
            r'[ \t]*"tags"\s*:\s*\["[^"]*"\]\s*,?\s*\n',
            "",
            result,
        )

    return result

def replace_address_markers(obj, addr: dict):
    if isinstance(obj, dict):
        for key in list(obj.keys()):
            val = obj[key]
            if isinstance(val, str):
                val = val.replace("@address-group-value-type",  addr["value_type"])
                val = val.replace("@address-group-valuetype",   addr["value_type"])   # alt spelling
                val = val.replace("@address-group-value",       addr["value"])
                val = val.replace("@address-group-type",        addr["display_type"])
                obj[key] = val
            elif isinstance(val, (dict, list)):
                replace_address_markers(val, addr)
    elif isinstance(obj, list):
        for item in obj:
            replace_address_markers(item, addr)

def inject_address_entries(payload, entries: List[dict]):
    if isinstance(payload, dict):
        for key, val in list(payload.items()):
            if isinstance(val, list):
                new_list: List = []
                for item in val:
                    if isinstance(item, dict) and _has_address_marker(item):
                        for addr in entries:
                            cloned = copy.deepcopy(item)
                            replace_address_markers(cloned, addr)
                            new_list.append(cloned)
                    else:
                        inject_address_entries(item, entries)
                        new_list.append(item)
                payload[key] = new_list
            elif isinstance(val, (dict, list)):
                inject_address_entries(val, entries)
    elif isinstance(payload, list):
        for item in payload:
            inject_address_entries(item, entries)

def _has_address_marker(obj) -> bool:
    if isinstance(obj, str):
        return "@address-group-value" in obj or "@address-group-type" in obj
    if isinstance(obj, dict):
        return any(_has_address_marker(v) for v in obj.values())
    if isinstance(obj, list):
        return any(_has_address_marker(i) for i in obj)
    return False

def build_payload(
    grp_name: str,
    grp_data: dict,
    resolved_ips: List[str],
    addresses: Dict[str, dict],
    template_str: str,
    parent_uuid: str,
) -> Optional[dict]:
    tag = grp_data.get("tag")
    filled = fill_group_markers(template_str, grp_name, tag, parent_uuid)

    json_start = filled.find("{")
    if json_start == -1:
        log.error("No JSON object found in template for group '%s'", grp_name)
        return None
    json_str = filled[json_start:]

    try:
        payload = json.loads(json_str)
    except json.JSONDecodeError as exc:
        log.error("JSON parse error for group '%s': %s", grp_name, exc)
        log.debug("Filled template content:\n%s", json_str)
        return None

    addr_entries: List[dict] = []
    for ip_name in resolved_ips:
        entry = get_address_entry(ip_name, addresses)
        if entry:
            addr_entries.append(entry)

    if not addr_entries:
        log.warning("No resolvable IP entries for group '%s'", grp_name)

    inject_address_entries(payload, addr_entries)

    return payload

def build_session(cfg: Dict[str, str]) -> requests.Session:
    session = requests.Session()
    bearer = cfg.get("bearer-token", "")
    csrf   = cfg.get("csrf-token", "")
    raw_cookies = cfg.get("cookies", "")
    session.headers.update(
        {
            "Authorization": f"Bearer {bearer}",
            "X-CSRF-Token":  csrf,
            "Content-Type":  "application/json",
        }
    )
    if raw_cookies:
        for pair in raw_cookies.split(";"):
            pair = pair.strip()
            if "=" in pair:
                k, _, v = pair.partition("=")
                session.cookies.set(k.strip(), v.strip())

    log.debug("Session configured – bearer: %s…", bearer[:12] if bearer else "(empty)")
    return session

def post_to_concerto(
    session: requests.Session,
    url: str,
    payload: dict,
    grp_name: str,
) -> Tuple[Optional[int], str]:
    log.info("POST → %s  [group: %s]", url, grp_name)
    try:
        resp = session.post(url, json=payload, verify=False, timeout=30)
        log.info(
            "Response for '%s': HTTP %s  body: %s",
            grp_name,
            resp.status_code,
            resp.text[:400],
        )
        return resp.status_code, resp.text
    except requests.RequestException as exc:
        log.error("Request exception for group '%s': %s", grp_name, exc)
        return None, str(exc)

def main() -> None:
    log.info("=" * 70)
    log.info("Step 8 – Address-group converter  START")
    log.info("=" * 70)

    required = {
        "final-address-group": FINAL_ADDR_GROUP,
        "final-address":       FINAL_ADDR,
        "JSON template":       JSON_TEMPLATE,
        "general.txt":         GENERAL_TXT,
    }
    missing = [label for label, path in required.items() if not os.path.isfile(path)]
    if missing:
        for label in missing:
            log.error("Required file missing: %s  (%s)", label, required[label])
        sys.exit(1)

    shutil.copy2(FINAL_ADDR_GROUP, TEMP_ADDR_GROUP)
    log.info("Step 1: %s  →  %s", FINAL_ADDR_GROUP, TEMP_ADDR_GROUP)

    cfg           = read_general_txt(GENERAL_TXT)
    parent_uuid   = cfg.get("address-group-parent-ref-uuid", "")
    concerto_fqdn = cfg.get("concerto-fqdn", "")
    tenant_uuid   = cfg.get("tenant-uuid", "")

    log.debug("general.txt full contents:")
    for k, v in cfg.items():
        log.debug("  KEY='%s'  VALUE='%s'", k, v)
    log.debug("concerto_fqdn resolved to: '%s'", concerto_fqdn)
    log.debug("tenant_uuid   resolved to: '%s'", tenant_uuid)

    post_url = f"https://{concerto_fqdn}/portalapi/v1/tenants/{tenant_uuid}/elements/endpoint"
    log.info("Concerto endpoint: %s", post_url)

    all_groups   = parse_address_group_file(FINAL_ADDR_GROUP)
    addresses    = parse_address_file(FINAL_ADDR)
    template_str = open(JSON_TEMPLATE, encoding="utf-8").read()

    for old in glob.glob(os.path.join(TEMP_DIR, "post-address-config-*.json")):
        os.remove(old)
        log.debug("Removed stale temp file: %s", old)

    session      = build_session(cfg)
    json_counter = 1
    all_payloads: List[Tuple[str, dict]] = []

    grp_names = list(all_groups.keys())
    log.info("Total address-group objects to process: %d", len(grp_names))

    for grp_name in grp_names:
        log.info("-" * 60)
        log.info("Step 2: Processing group '%s'", grp_name)
        grp_data = all_groups[grp_name]

        raw_words = grp_data.get("static", [])
        has_nested = any(w in all_groups for w in raw_words)

        if has_nested:
            log.info(
                "Step 3: Nested group(s) detected in '%s' – expanding: %s",
                grp_name,
                [w for w in raw_words if w in all_groups],
            )

        resolved: List[str] = []
        for word in raw_words:
            if word in all_groups:
                expanded = resolve_group(word, all_groups)
                log.info("Step 4: '%s' expanded → %s", word, expanded)
                resolved.extend(expanded)
            else:
                resolved.append(word)

        seen: set = set()
        deduped: List[str] = []
        for item in resolved:
            if item not in seen:
                seen.add(item)
                deduped.append(item)

        removed_dups = len(resolved) - len(deduped)
        if removed_dups:
            log.info("Step 5: Removed %d duplicate(s) from '%s'", removed_dups, grp_name)
        log.info("Step 5: Final IP list for '%s': %s", grp_name, deduped)

        out_json = os.path.join(TEMP_DIR, f"post-address-config-{json_counter}.json")

        payload = build_payload(
            grp_name, grp_data, deduped, addresses, template_str, parent_uuid
        )
        if payload is None:
            log.error("Skipping group '%s' – could not build payload", grp_name)
            json_counter += 1
            continue

        with open(out_json, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        log.info("Step 6a: Wrote %s", out_json)

        json_counter += 1

        tmp_files = sorted(glob.glob(os.path.join(TEMP_DIR, "post-address-config-*.json")))
        log.info("Step 12: Merging %d temp file(s) into %s", len(tmp_files), MERGED_JSON)
        merged_list = []
        for tf in tmp_files:
            with open(tf, encoding="utf-8") as fh:
                merged_list.append(json.load(fh))
        with open(MERGED_JSON, "w", encoding="utf-8") as fh:
            json.dump(merged_list, fh, indent=2)
        log.info("Step 12: Merged JSON written → %s", MERGED_JSON)

        status, body = post_to_concerto(session, post_url, payload, grp_name)
        log.info("Step 13b result | group='%s' | status=%s", grp_name, status)

        for tmp in glob.glob(os.path.join(TEMP_DIR, "post-address-config-*.json")):
            os.remove(tmp)
            log.debug("Cleaned up temp file: %s", tmp)
        if os.path.isfile(MERGED_JSON):
            os.remove(MERGED_JSON)
            log.debug("Cleaned up merged file: %s", MERGED_JSON)

    if os.path.isfile(TEMP_ADDR_GROUP):
        os.remove(TEMP_ADDR_GROUP)
        log.info("Deleted temp file: %s", TEMP_ADDR_GROUP)

    log.info("=" * 70)
    log.info("Step 8 – Address-group converter  COMPLETE")
    log.info("=" * 70)

if __name__ == "__main__":
    main()