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

SCRIPT_DIR   = Path(__file__).resolve().parent
BASE_DIR     = SCRIPT_DIR.parent

FINAL_SERVICE_FILE   = BASE_DIR / "final-data" / "final-service.txt"
TEMP_SERVICE_FILE    = BASE_DIR / "temp"        / "temp-service.txt"
TEMP_POST_JSON       = BASE_DIR / "temp"        / "post-service.json"
TEMPLATE_JSON        = BASE_DIR / "json"        / "service" / "post-service.json"
GENERAL_FILE         = BASE_DIR / "temp"        / "general.txt"
LOG_DIR              = BASE_DIR / "log"
LOG_FILE             = LOG_DIR  / "step-8.log"

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

def read_general_file(path: Path) -> dict:
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
                key, _, value = line.partition(">>")
                data[key.strip()] = value.strip()
    log.debug("Loaded general.txt: %s", list(data.keys()))
    return data

def build_session_and_headers(general: dict) -> tuple:
    bearer_token = general.get("bearer-token", "")
    csrf_token   = general.get("csrf-token", "")
    cookies_str  = general.get("cookies", "")
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
        "X-CSRF-Token":  csrf_token,
        "Authorization": "Bearer " + bearer_token,
        "Content-Type":  "application/json",
    }

    log.info("Using bearer-token and csrf-token from general.txt.")
    return session, headers

def group_service_objects(lines: list) -> dict:
    groups   = defaultdict(list)
    order    = []
    pattern  = re.compile(r'^set\s+shared\s+service\s+("(?:[^"]+)"|(\S+))\s', re.IGNORECASE)
    for line in lines:
        line = line.rstrip("\n")
        if not line.strip():
            continue
        m = pattern.match(line)
        if not m:
            log.warning("Unrecognised config line (skipped): %s", line)
            continue
        raw_name = m.group(1)
        obj_name = raw_name.strip('"')
        if obj_name not in groups:
            order.append(obj_name)
        groups[obj_name].append(line)

    return {name: groups[name] for name in order}

def extract_service_params(obj_name: str, config_lines: list) -> dict:
    params = {
        "protocol":    None,
        "port_type":   None,
        "port_value":  None,
        "tag":         None,
        "description": None,
    }
    for line in config_lines:
        m = re.search(
            r'protocol\s+(tcp|udp)\s+port\s+(\S+)',
            line, re.IGNORECASE
        )
        if m:
            params["protocol"]   = m.group(1).upper()
            params["port_type"]  = "destinationPort"
            params["port_value"] = m.group(2)
            log.debug("[%s] protocol=%s portType=destinationPort portValue=%s",
                      obj_name, params["protocol"], params["port_value"])
            continue

        m = re.search(
            r'protocol\s+(tcp|udp)\s+source-port\s+(\S+)',
            line, re.IGNORECASE
        )
        if m:
            params["protocol"]   = m.group(1).upper()
            params["port_type"]  = "sourcePort"
            params["port_value"] = m.group(2)
            log.debug("[%s] protocol=%s portType=sourcePort portValue=%s",
                      obj_name, params["protocol"], params["port_value"])
            continue

        m = re.search(r'\btag\s+\[([^\]]+)\]', line, re.IGNORECASE)
        if m:
            tags = m.group(1).strip().split()
            params["tag"] = " ".join(tags)
            log.debug("[%s] tag (list)=%s", obj_name, params["tag"])
            continue

        m = re.search(r'\btag\s+(\S+)', line, re.IGNORECASE)
        if m:
            params["tag"] = m.group(1)
            log.debug("[%s] tag=%s", obj_name, params["tag"])
            continue

        m = re.search(r'\bdescription\s+"([^"]*)"', line, re.IGNORECASE)
        if m:
            params["description"] = m.group(1)
            log.debug("[%s] description=%s", obj_name, params["description"])
            continue

        m = re.search(r'\bdescription\s+(\S+)', line, re.IGNORECASE)
        if m:
            params["description"] = m.group(1)
            log.debug("[%s] description=%s", obj_name, params["description"])

    return params

def replace_or_delete_marker(content: str, marker: str, value) -> str:
    if value is not None:
        return content.replace(marker, str(value))
    lines = content.splitlines(keepends=True)
    cleaned = [ln for ln in lines if marker not in ln]
    return "".join(cleaned)

def build_post_json(obj_name: str, params: dict, parent_ref_uuid: str) -> str:
    if not TEMPLATE_JSON.exists():
        log.error("Template not found: %s", TEMPLATE_JSON)
        sys.exit(1)
    content = TEMPLATE_JSON.read_text(encoding="utf-8")

    new_uuid = str(uuid.uuid4())
    content = content.replace("@service-object-name",  obj_name)
    content = content.replace("@service-object-uuid",  new_uuid)
    content = content.replace("@service-parent-ref-uuid", parent_ref_uuid)

    if params["protocol"]:
        content = content.replace("@service-protocol-value", params["protocol"])
    else:
        content = replace_or_delete_marker(content, "@service-protocol-value", None)

    if params["port_type"]:
        content = content.replace("@service-port-type", params["port_type"])
    else:
        content = replace_or_delete_marker(content, "@service-port-type", None)

    if params["port_value"]:
        content = content.replace("@service-port-value", params["port_value"])
    else:
        content = replace_or_delete_marker(content, "@service-port-value", None)

    content = replace_or_delete_marker(content, "@service-tag",         params["tag"])
    content = replace_or_delete_marker(content, "@service-description", params["description"])

    log.debug("[%s] UUID=%s parentRef=%s", obj_name, new_uuid, parent_ref_uuid)
    return content

def post_service(session, headers, concerto_url: str, tenant_uuid: str,
                 obj_name: str, json_content: str) -> bool:
    url = (
        f"{concerto_url}/portalapi/v1/tenants/{tenant_uuid}/elements/services"
    )
    log.info("[%s] POST → %s", obj_name, url)
    TEMP_POST_JSON.parent.mkdir(parents=True, exist_ok=True)
    TEMP_POST_JSON.write_text(json_content, encoding="utf-8")
    log.debug("[%s] Wrote temp JSON: %s", obj_name, TEMP_POST_JSON)

    try:
        payload = json.loads(json_content)
    except json.JSONDecodeError as exc:
        log.error("[%s] JSON parse error before POST: %s", obj_name, exc)
        log.error("[%s] Content:\n%s", obj_name, json_content)
        return False

    resp = session.post(
        url,
        verify=False,
        cookies=session.cookies,
        headers=headers,
        json=payload,
    )

    if resp.ok:
        log.info("[%s] POST success – HTTP %s", obj_name, resp.status_code)
        log.debug("[%s] Response: %s", obj_name, resp.text)
        return True
    else:
        log.error("[%s] POST failed – HTTP %s – %s", obj_name, resp.status_code, resp.text)
        return False

def main():
    log.info("=" * 70)
    log.info("Step 8 – Convert service objects → Concerto API")
    log.info("=" * 70)

    if not FINAL_SERVICE_FILE.exists() or FINAL_SERVICE_FILE.stat().st_size == 0:
        log.warning("Source file not found or empty: %s – nothing to do.", FINAL_SERVICE_FILE)
        sys.exit(0)

    TEMP_SERVICE_FILE.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(FINAL_SERVICE_FILE, TEMP_SERVICE_FILE)
    log.info("Step 26: Copied %s → %s", FINAL_SERVICE_FILE, TEMP_SERVICE_FILE)

    if not TEMP_SERVICE_FILE.exists() or TEMP_SERVICE_FILE.stat().st_size == 0:
        log.info("Step 28b: temp-service.txt is empty – exiting.")
        sys.exit(0)

    general = read_general_file(GENERAL_FILE)

    required_keys = ["concerto-fqdn", "tenant-uuid", "services-parent-ref-uuid",
                     "bearer-token", "csrf-token"]
    for key in required_keys:
        if key not in general:
            log.error("Missing required key in general.txt: {%s}", key)
            sys.exit(1)

    concerto_url    = general["concerto-fqdn"].rstrip("/")
    if not concerto_url.startswith("http://") and not concerto_url.startswith("https://"):
        concerto_url = "https://" + concerto_url
        log.warning("concerto-fqdn had no scheme – prepended https://: %s", concerto_url)
    tenant_uuid     = general["tenant-uuid"]
    parent_ref_uuid = general["services-parent-ref-uuid"]

    session, headers = build_session_and_headers(general)

    raw_lines = TEMP_SERVICE_FILE.read_text(encoding="utf-8").splitlines()
    service_groups = group_service_objects(raw_lines)
    total = len(service_groups)
    log.info("Found %d service object(s) to process.", total)

    success_count = 0
    fail_count    = 0

    for idx, (obj_name, config_lines) in enumerate(service_groups.items(), start=1):
        log.info("-" * 60)
        log.info("Processing [%d/%d]: %s", idx, total, obj_name)
        for ln in config_lines:
            log.debug("  Config line: %s", ln)

        params = extract_service_params(obj_name, config_lines)

        json_content = build_post_json(obj_name, params, parent_ref_uuid)

        ok = post_service(session, headers, concerto_url, tenant_uuid,
                          obj_name, json_content)

        if TEMP_POST_JSON.exists():
            TEMP_POST_JSON.unlink()
            log.debug("Deleted temp JSON: %s", TEMP_POST_JSON)

        if ok:
            success_count += 1
        else:
            fail_count += 1

    TEMP_SERVICE_FILE.unlink(missing_ok=True)
    log.info("Deleted temp file: %s", TEMP_SERVICE_FILE)

    log.info("=" * 70)
    log.info("Done. Success: %d  |  Failed: %d  |  Total: %d",
             success_count, fail_count, total)
    log.info("=" * 70)

if __name__ == "__main__":
    main()