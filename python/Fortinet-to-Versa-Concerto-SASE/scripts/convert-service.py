#!/usr/bin/env python3
import json
import logging
import os
import re
import shutil
import sys
import uuid
from collections import defaultdict
from pathlib import Path

import requests
from requests.packages import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent

FINAL_SERVICE_FILE = BASE_DIR / "final-data" / "final-service.txt"
TEMP_SERVICE_FILE = BASE_DIR / "temp" / "temp-service.txt"
TEMP_POST_JSON = BASE_DIR / "temp" / "post-service.json"
TEMPLATE_JSON = BASE_DIR / "json" / "service" / "post-service.json"
GENERAL_FILE = BASE_DIR / "temp" / "general.txt"
CUST_SVC_CACHE = BASE_DIR / "temp" / "cust-service.txt"
LOG_DIR = BASE_DIR / "log"
LOG_FILE = LOG_DIR / "step-8.log"

LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


def read_general_file(path):
    data = {}
    if not path.exists():
        log.error("general.txt not found at %s", path)
        sys.exit(1)
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ">>" in line:
                parts = re.split(r'\s*>>\s*', line, 1)
                if len(parts) == 2:
                    data[parts[0].strip()] = parts[1].strip()
    return data


def build_session_and_headers(general):
    bearer_token = general.get("bearer-token", "")
    csrf_token = general.get("csrf-token", "")
    cookies_str = general.get("cookies", "")

    if not bearer_token:
        log.error("Missing required key in general.txt: bearer-token")
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


SVC_NAME_RE = re.compile(r'^\s*firewall\s+service\s+custom\s+("([^"]+)"|(\S+))\s', re.IGNORECASE)


def group_service_objects(lines):
    groups = defaultdict(list)
    order = []

    for line in lines:
        line = line.rstrip("\n")
        if not line.strip():
            continue
        m = SVC_NAME_RE.match(line)
        if not m:
            log.warning("Unrecognised config line (skipped): %s", line)
            continue
        obj_name = m.group(2) if m.group(2) else m.group(3)
        if obj_name not in groups:
            order.append(obj_name)
        groups[obj_name].append(line)

    return {name: groups[name] for name in order}


_SQL_KEYWORDS = re.compile(
    r'\b(?:SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TABLE|DATABASE|FROM|WHERE'
    r'|AND|OR|NOT|IN|IS|NULL|JOIN|HAVING|GROUP|ORDER|BY|LIKE|BETWEEN|EXISTS'
    r'|UNION|ALL|SET|EXEC|EXECUTE|CAST|CONVERT|DECLARE|VALUES|INTO|TOP|DISTINCT'
    r'|AS|ON|CASE|WHEN|THEN|ELSE|END|WITH|INDEX)\b',
    re.IGNORECASE
)
_SQL_SPECIAL = re.compile(r'[+;\'\"\\\\]|--')


def sanitize_description(text):
    """Strip SQL-injection chars and double-dashes rejected by Concerto
    in entity.description. Mirrors sanitize_description_tags in convert-policy.py."""
    if not text:
        return text
    text = _SQL_KEYWORDS.sub('', text)
    text = _SQL_SPECIAL.sub('', text)
    text = re.sub(r'\s{2,}', ' ', text).strip()
    return text


def extract_service_params(obj_name, config_lines):
    """
    Parses Fortinet firewall service custom config lines and extracts:

      Protocol (case-insensitive):
        set protocol TCP            -> protocol = "TCP"
        set protocol UDP            -> protocol = "UDP"
        set protocol TCP UDP        -> protocol = "TCP_OR_UDP"
        set protocol UDP TCP        -> protocol = "TCP_OR_UDP"  (token order ignored)

      Destination port (case-insensitive):
        set tcp-portrange <port>    -> dst_port = "<port>", protocol inferred "TCP"
        set udp-portrange <port>    -> dst_port = "<port>", protocol inferred "UDP"

      Source port (case-insensitive):
        set tcp-src-port <port>     -> src_port = "<port>", protocol inferred "TCP"
        set udp-src-port <port>     -> src_port = "<port>", protocol inferred "UDP"
        set tcp-port <port>         -> src_port = "<port>", protocol inferred "TCP"

      Both dst_port and src_port are captured independently; an object that carries
      both a portrange line AND a src-port line will have both fields populated.

      Port values may be a single port (e.g. 1024) or a range (e.g. 1024-65535).
      For portrange entries, only the destination portion is used
      (i.e. everything before the first ":" is taken as the port value).

      A protocol set explicitly via "set protocol" always takes precedence over
      the protocol inferred from a portrange/src-port keyword.
    """
    params = {
        "protocol": None,       # "TCP" | "UDP" | "TCP_OR_UDP"
        "dst_port": None,       # destinationPort value, e.g. "443" or "1024-65535"
        "src_port": None,       # sourcePort value,      e.g. "1024-65535"
        "tag": None,
        "description": None,
    }

    for line in config_lines:

        # ── protocol TCP / UDP / TCP UDP / UDP TCP ────────────────────────────
        # Capture one or two whitespace-separated TCP/UDP tokens after "protocol".
        m = re.search(r'\bprotocol\s+((?:TCP|UDP)(?:\s+(?:TCP|UDP))?)\b', line, re.IGNORECASE)
        if m:
            tokens = m.group(1).upper().split()
            params["protocol"] = "TCP_OR_UDP" if len(tokens) >= 2 else tokens[0]
            continue

        # ── tcp-portrange / udp-portrange  ->  dst_port ───────────────────────
        m = re.search(r'\b(tcp|udp)-portrange\s+(\S+)', line, re.IGNORECASE)
        if m:
            if params["protocol"] is None:
                params["protocol"] = m.group(1).upper()
            # First portrange wins; do not overwrite if already set by an earlier line.
            if params["dst_port"] is None:
                # Strip any "src-range" suffix separated by ":"
                params["dst_port"] = m.group(2).split(":")[0]
            continue

        # ── tcp-src-port / udp-src-port / tcp-port  ->  src_port ─────────────
        m = re.search(r'\b(tcp-src-port|udp-src-port|tcp-port)\s+(\S+)', line, re.IGNORECASE)
        if m:
            keyword = m.group(1).lower()
            if params["protocol"] is None:
                params["protocol"] = "UDP" if keyword.startswith("udp") else "TCP"
            params["src_port"] = m.group(2)
            continue

        # ── tag / tagging ─────────────────────────────────────────────────────
        m = re.search(r'\b(?:tag|tagging)\s+\[([^\]]+)\]', line, re.IGNORECASE)
        if m:
            params["tag"] = " ".join(m.group(1).strip().split())
            continue

        m = re.search(r'\b(?:tag|tagging)\s+(\S+)', line, re.IGNORECASE)
        if m:
            params["tag"] = m.group(1).strip('"')
            continue

        # ── comment ───────────────────────────────────────────────────────────
        m = re.search(r'\bcomment\s+"([^"]*)"', line, re.IGNORECASE)
        if m:
            params["description"] = m.group(1)
            continue

        m = re.search(r'\bcomment\s+(\S+)', line, re.IGNORECASE)
        if m:
            params["description"] = m.group(1)

    if params["description"]:
        params["description"] = sanitize_description(params["description"])
    return params


def replace_or_delete_marker(content, marker, value):
    if value is not None:
        return content.replace(marker, str(value))
    lines = content.splitlines(keepends=True)
    cleaned = [ln for ln in lines if marker not in ln]
    return "".join(cleaned)


def build_post_json(obj_name, params, parent_ref_uuid, new_uuid):
    if not TEMPLATE_JSON.exists():
        log.error("Template not found: %s", TEMPLATE_JSON)
        sys.exit(1)

    content = TEMPLATE_JSON.read_text(encoding="utf-8")
    content = content.replace("@service-object-name", obj_name)
    content = content.replace("@service-object-uuid", new_uuid)
    content = content.replace("@service-parent-ref-uuid", parent_ref_uuid)

    # Protocol: value may be "TCP", "UDP", or "TCP_OR_UDP"
    if params["protocol"]:
        content = content.replace("@service-protocol-value", params["protocol"])
    else:
        content = replace_or_delete_marker(content, "@service-protocol-value", None)

    # Tag and description live in plain string values — safe to line-delete when absent.
    content = replace_or_delete_marker(content, "@service-tag", params["tag"])
    content = replace_or_delete_marker(content, "@service-description", params["description"])

    # Parse the template now.  Any remaining @service-* port markers (old or new) are
    # valid JSON string literals at this point, so parsing succeeds.  We clean them out
    # of entity.attributes below rather than deleting lines (line deletion breaks JSON
    # by leaving trailing commas).
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        log.error("[%s] Template produced invalid JSON after marker substitution: %s", obj_name, exc)
        sys.exit(1)

    # --- Rebuild entity.attributes port section --------------------------------
    # 1. Remove every stale @service-* key that the template may have left behind.
    # 2. Inject destinationPort / sourcePort with the values extracted from config.
    #
    # The Concerto API expects:
    #   "destinationPort": {"value": "<range>"}
    #   "sourcePort":      {"value": "<range>"}
    attributes = payload.get("entity", {}).get("attributes", {})

    # Strip any marker-style keys/nested marker values left by the template
    for key in list(attributes.keys()):
        if key.startswith("@service-"):
            del attributes[key]
            continue
        val = attributes[key]
        if isinstance(val, dict):
            for vk in list(val.keys()):
                if isinstance(val[vk], str) and val[vk].startswith("@service-"):
                    del val[vk]

    # Inject real port values (or ensure the fields are absent when not applicable)
    if params["dst_port"] is not None:
        attributes["destinationPort"] = {"value": params["dst_port"]}
    else:
        attributes.pop("destinationPort", None)

    if params["src_port"] is not None:
        attributes["sourcePort"] = {"value": params["src_port"]}
    else:
        attributes.pop("sourcePort", None)

    if "entity" in payload and "attributes" in payload["entity"]:
        payload["entity"]["attributes"] = attributes

    log.debug("[%s] attributes -> %s", obj_name, attributes)
    return json.dumps(payload, indent=2)


def post_service(session, headers, concerto_url, tenant_uuid, obj_name, json_content, fallback_uuid):
    url = "{}/portalapi/v1/tenants/{}/elements/services".format(concerto_url, tenant_uuid)
    log.info("[%s] POST -> %s", obj_name, url)

    TEMP_POST_JSON.parent.mkdir(parents=True, exist_ok=True)
    TEMP_POST_JSON.write_text(json_content, encoding="utf-8")

    try:
        payload = json.loads(json_content)
    except json.JSONDecodeError as exc:
        log.error("[%s] JSON parse error: %s", obj_name, exc)
        return False, None

    resp = session.post(url, verify=False, cookies=session.cookies, headers=headers, json=payload)
    if resp.ok:
        log.info("[%s] POST success - HTTP %s", obj_name, resp.status_code)
        try:
            svc_uuid = resp.json().get("uuid") or fallback_uuid
        except Exception:
            svc_uuid = fallback_uuid
        return True, svc_uuid
    else:
        log.error("[%s] POST failed - HTTP %s - %s", obj_name, resp.status_code, resp.text)
        return False, None


def main():
    log.info("=" * 70)
    log.info("Convert Fortinet service objects -> Concerto API")
    log.info("=" * 70)

    if not FINAL_SERVICE_FILE.exists() or FINAL_SERVICE_FILE.stat().st_size == 0:
        log.warning("Source file not found or empty: %s - nothing to do.", FINAL_SERVICE_FILE)
        sys.exit(0)

    TEMP_SERVICE_FILE.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(FINAL_SERVICE_FILE, TEMP_SERVICE_FILE)
    log.info("Copied %s -> %s", FINAL_SERVICE_FILE, TEMP_SERVICE_FILE)

    general = read_general_file(GENERAL_FILE)

    required_keys = ["concerto-fqdn", "tenant-uuid", "services-parent-ref-uuid", "bearer-token", "csrf-token"]
    for key in required_keys:
        if key not in general:
            log.error("Missing required key in general.txt: %s", key)
            sys.exit(1)

    concerto_url = general["concerto-fqdn"].rstrip("/")
    if not concerto_url.startswith("http"):
        concerto_url = "https://" + concerto_url
    tenant_uuid = general["tenant-uuid"]
    parent_ref_uuid = general["services-parent-ref-uuid"]

    session, headers = build_session_and_headers(general)

    raw_lines = TEMP_SERVICE_FILE.read_text(encoding="utf-8").splitlines()
    service_groups = group_service_objects(raw_lines)
    total = len(service_groups)
    log.info("Found %d service object(s) to process.", total)

    success_count = 0
    fail_count = 0

    # Clear the service cache at the start of each run so it reflects only this run's results
    CUST_SVC_CACHE.parent.mkdir(parents=True, exist_ok=True)
    CUST_SVC_CACHE.write_text("", encoding="utf-8")
    log.info("Cleared service cache: %s", CUST_SVC_CACHE)

    for idx, (obj_name, config_lines) in enumerate(service_groups.items(), start=1):
        log.info("-" * 60)
        log.info("Processing [%d/%d]: %s", idx, total, obj_name)

        params = extract_service_params(obj_name, config_lines)
        new_uuid = str(uuid.uuid4())
        json_content = build_post_json(obj_name, params, parent_ref_uuid, new_uuid)
        ok, svc_uuid = post_service(session, headers, concerto_url, tenant_uuid, obj_name, json_content, new_uuid)

        if TEMP_POST_JSON.exists():
            TEMP_POST_JSON.unlink()

        if ok and svc_uuid:
            success_count += 1
            with open(CUST_SVC_CACHE, "a", encoding="utf-8") as cf:
                cf.write("{} >> {}\n".format(obj_name, svc_uuid))
            log.info("[%s] Cached UUID: %s", obj_name, svc_uuid)
        else:
            fail_count += 1

    TEMP_SERVICE_FILE.unlink(missing_ok=True)

    log.info("=" * 70)
    log.info("Done. Success: %d | Failed: %d | Total: %d", success_count, fail_count, total)
    log.info("=" * 70)


if __name__ == "__main__":
    main()
