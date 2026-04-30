import json
import logging
import os
import re
import shutil
import sys
from typing import Dict, List, Optional, Set, Tuple

import requests
from requests.packages import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
PYTHONWARNINGS = "ignore:InsecureRequestWarning"

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
BASE_DIR    = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

LOG_DIR        = os.path.join(BASE_DIR, "log")
TEMP_DIR       = os.path.join(BASE_DIR, "temp")
FINAL_DATA_DIR = os.path.join(BASE_DIR, "final-data")
JSON_DIR       = os.path.join(BASE_DIR, "json", "url-category")

os.makedirs(LOG_DIR,  exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

FINAL_INPUT_FILE = os.path.join(FINAL_DATA_DIR, "final-custom-urlf-profile.txt")
TEMP_INPUT_FILE  = os.path.join(TEMP_DIR,       "temp-custom-urlf-profile.txt")
JSON_TEMPLATE    = os.path.join(JSON_DIR,        "post-url-category.json")
TEMP_JSON_FILE   = os.path.join(TEMP_DIR,        "post-url-category.json")
GENERAL_FILE     = os.path.join(BASE_DIR,        "temp", "general.txt")

LOG_FILE = os.path.join(LOG_DIR, "step-8.log")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

POSIX_REGEX_CHARS = set("^*+?{}[]|()")

def read_general_value(key):
    if not os.path.isfile(GENERAL_FILE):
        log.error("general.txt not found: %s", GENERAL_FILE)
        return None
    with open(GENERAL_FILE, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if ">>" in line:
                parts = re.split(r'\s*>>\s*', line, 1)
                if len(parts) == 2 and parts[0].strip() == key:
                    return parts[1].strip()
    log.warning("Key %r not found in %s", key, GENERAL_FILE)
    return None

def parse_cookies(cookie_str):
    cookies = {}
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            name, _, value = part.partition("=")
            cookies[name.strip()] = value.strip()
    return cookies

_fqdn         = read_general_value("concerto-fqdn") or ""
_port         = read_general_value("concerto-port") or "443"
CONCERTO_URL  = "https://{0}:{1}".format(_fqdn, _port) if _fqdn else "<<concerto-url>>"
TENANT_UUID   = read_general_value("tenant-uuid")   or "<<tenant-uuid>>"
BEARER_TOKEN  = read_general_value("bearer-token")  or "<<bearer-token>>"
_cookie_str   = read_general_value("cookies")       or ""
COOKIES       = parse_cookies(_cookie_str) if _cookie_str else {}

CSRF_TOKEN    = COOKIES.get("ECP-CSRF-TOKEN", "")

def validate_config():
    required = {
        "concerto-fqdn": _fqdn,
        "tenant-uuid":   TENANT_UUID,
        "bearer-token":  BEARER_TOKEN,
        "cookies":       _cookie_str,
    }
    missing = [k for k, v in required.items() if not v or v.startswith("<<")]
    if missing:
        log.error("=" * 60)
        log.error("CONFIGURATION ERROR: the following keys are missing or")
        log.error("not set in general.txt (%s):", GENERAL_FILE)
        for k in missing:
            log.error("  %s", k)
        log.error("Each line must follow the format:  key >> value")
        log.error("=" * 60)
        sys.exit(1)

def build_headers():
    headers = {
        "Authorization": "Bearer " + BEARER_TOKEN,
        "Content-Type":  "application/json",
    }
    if CSRF_TOKEN:
        headers["X-CSRF-Token"] = CSRF_TOKEN
    return headers

def post_url_category(obj_name, json_str):
    url = "{0}/portalapi/v1/tenants/{1}/sase/settings/urlCategory".format(
        CONCERTO_URL, TENANT_UUID
    )
    log.info("POST | Sending object '%s' to %s", obj_name, url)

    resp = requests.post(
        url,
        verify=False,
        cookies=COOKIES,
        headers=build_headers(),
        data=json_str.encode("utf-8"),
    )
    log.info("POST | Status: %s", resp.status_code)
    try:
        log.info("POST | Response body:\n%s", json.dumps(resp.json(), indent=2))
    except Exception:
        log.info("POST | Response body (raw): %s", resp.text)
    return resp

def _obj_name_token(obj_name):
    return '"{0}"'.format(obj_name) if " " in obj_name else obj_name

def parse_objects(lines):
    header = re.compile(
        r'^set\s+shared\s+profiles\s+custom-url-category\s+'
        r'("(?:[^"]+)"|[^\s]+)'
    )
    objects = {}
    order   = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        m = header.match(line)
        if not m:
            continue
        name = m.group(1).strip('"')
        if name not in objects:
            objects[name] = []
            order.append(name)
        objects[name].append(line)
    return objects, order

def get_keyword_value(lines, obj_name, keyword):
    token   = re.escape(_obj_name_token(obj_name))
    kw      = re.escape(keyword)
    pattern = re.compile(
        r'^set\s+shared\s+profiles\s+custom-url-category\s+{0}\s+{1}\s+(.+)$'.format(
            token, kw
        )
    )
    for line in lines:
        m = pattern.match(line.strip())
        if m:
            return m.group(1).strip()
    return None

def extract_list_items(raw):
    raw = raw.strip()
    if raw.startswith("["):
        inner = raw.lstrip("[").rstrip("]").strip()
        if not inner:
            return []
        tokens = re.findall(r'"[^"]*"|\S+', inner)
        return [t.strip('"') for t in tokens]

    return [raw.strip('"')]

def has_regex_chars(word):
    return any(ch in POSIX_REGEX_CHARS for ch in word)

def sanitize_as_pattern(word):
    ALLOWED = re.compile(r'[^a-zA-Z0-9._*+?^${}[\]|()\-&~#%/\\:]')
    cleaned = ALLOWED.sub("", word)
    if cleaned != word:
        log.debug("47b | Removed undesirable chars: %r -> %r", word, cleaned)
    if not cleaned:
        log.warning("47b | Nothing left after sanitisation of %r - skipping", word)
        return None

    CHARS_TO_ESCAPE = set("^$+?{}[]|()")
    out = []
    for ch in cleaned:
        if ch in CHARS_TO_ESCAPE or ch == "/":
            out.append("\\" + ch)
        elif ch == "\\":
            out.append("\\\\")
        else:
            out.append(ch)
    escaped = "".join(out)

    if escaped.startswith("*"):
        escaped = "." + escaped
        log.debug("47d | Added '.' before leading '*': %r", escaped)
    if escaped.endswith("*") and (len(escaped) < 2 or escaped[-2] != "."):
        escaped = escaped[:-1] + ".*"
        log.debug("47d | Added '.' before trailing '*': %r", escaped)

    if " " in escaped:
        log.warning("47e | Space found in sanitised pattern %r - skipping", escaped)
        return None

    log.debug("47  | Final pattern: %r", escaped)
    return escaped

def sanitize_as_url(word):
    VALID_URL = re.compile(r"^[a-zA-Z0-9\-._~:/?#\[\]@!$&'()*+,;=%]+$")
    if not VALID_URL.match(word):
        log.warning("48a | Invalid URL characters in %r - flushing", word)
        return None
    if " " in word:
        log.warning("48b | Space in URL string %r - skipping", word)
        return None
    log.debug("48  | Valid URL string: %r", word)
    return word

def _replace_value_block(raw):
    marker = '"value":{' 
    start = raw.find(marker)
    if start == -1:
        return raw
    brace_pos = start + len(marker) - 1
    depth = 0
    i = brace_pos
    while i < len(raw):
        if raw[i] == '{':
            depth += 1
        elif raw[i] == '}':
            depth -= 1
            if depth == 0:
                return raw[:brace_pos] + '{}' + raw[i + 1:]
        i += 1
    return raw

def build_payload(template_path, obj_name, tag, description, pattern_list, string_list):
    with open(template_path, "r", encoding="utf-8") as fh:
        raw = fh.read()
    raw = raw.replace('"' + "@url-category-name" + '"', json.dumps(obj_name))

    if tag:
        raw = raw.replace('"' + "@url-category-tag" + '"', json.dumps(tag))
        log.debug("44 | Tag set to: %r", tag)
    else:
        raw = raw.replace('"' + "@url-category-tag" + '"', "null")
        log.debug("44 | No tag - marker replaced with null")

    DESC_PATTERN = re.compile(r'"@url-category-descrip\w+"')
    if description:
        raw = DESC_PATTERN.sub(json.dumps(description), raw)
        log.debug("45 | Description set to: %r", description)
    else:
        raw = DESC_PATTERN.sub("null", raw)
        log.debug("45 | No description - marker replaced with null")

    raw = _replace_value_block(raw)

    raw = re.sub(r'"@[^"]+"', "null", raw)

    log.debug("build_payload | Final raw JSON before parse:\n%s", raw)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        log.error("build_payload | JSON parse failed: %s", exc)
        log.error("build_payload | Offending raw string:\n%s", raw)
        raise

    seen_p = set()
    deduped_patterns = []
    for p in pattern_list:
        if p not in seen_p:
            seen_p.add(p)
            deduped_patterns.append(p)
    if len(deduped_patterns) < len(pattern_list):
        log.info("Final dedup | Removed %d duplicate pattern(s)",
                 len(pattern_list) - len(deduped_patterns))
    pattern_list = deduped_patterns

    seen_s = set()
    deduped_strings = []
    for s in string_list:
        if s not in seen_s:
            seen_s.add(s)
            deduped_strings.append(s)
    if len(deduped_strings) < len(string_list):
        log.info("Final dedup | Removed %d duplicate string(s)",
                 len(string_list) - len(deduped_strings))
    string_list = deduped_strings

    value_section = (
        payload
        .setdefault("attributes", {})
        .setdefault("criteria",   {})
        .setdefault("value",      {})
    )

    if pattern_list:
        value_section["pattern"] = [
            {"pattern": p, "reputation": None} for p in pattern_list
        ]
        log.debug("47f | %d pattern element(s) inserted", len(pattern_list))

    if string_list:
        value_section["string"] = [
            {"string": s, "reputation": None} for s in string_list
        ]
        log.debug("48c | %d string element(s) inserted", len(string_list))

    return payload

def main():
    validate_config()

    log.info("=" * 70)
    log.info("Step 8 - Custom URL Filter Profile -> Versa JSON -> Concerto API")
    log.info("=" * 70)
    log.info("Target: %s  |  Tenant: %s", CONCERTO_URL, TENANT_UUID)

    log.info("Step 40 | Checking source file: %s", FINAL_INPUT_FILE)
    if (
        not os.path.isfile(FINAL_INPUT_FILE)
        or os.path.getsize(FINAL_INPUT_FILE) == 0
    ):
        log.warning("Step 40 | File missing or empty - jumping to step 51")
        _step_51()
        return

    shutil.copy2(FINAL_INPUT_FILE, TEMP_INPUT_FILE)
    log.info("Step 40 | Copied to: %s", TEMP_INPUT_FILE)

    log.info("Step 41 | Parsing object blocks from temp file")
    with open(TEMP_INPUT_FILE, "r", encoding="utf-8") as fh:
        all_lines = fh.readlines()

    if not any(line.strip() for line in all_lines):
        log.warning("Step 41 | Temp file is empty - jumping to step 51")
        _step_51()
        return

    objects, order = parse_objects(all_lines)
    log.info("Step 41 | Found %d object(s): %s", len(order), order)

    if not order:
        log.warning("Step 41 | No valid objects found - jumping to step 51")
        _step_51()
        return

    for obj_name in order:
        obj_lines = objects[obj_name]
        log.info("-" * 60)
        log.info("Step 41 | Processing object: %r  (%d config line(s))",
                 obj_name, len(obj_lines))
        for ln in obj_lines:
            log.debug("  CONFIG LINE: %s", ln.strip())

        log.info("Step 42 | Copying JSON template -> %s", TEMP_JSON_FILE)
        if not os.path.isfile(JSON_TEMPLATE):
            log.error("Step 42 | Template not found: %s - skipping object",
                      JSON_TEMPLATE)
            continue
        shutil.copy2(JSON_TEMPLATE, TEMP_JSON_FILE)

        tag_raw = get_keyword_value(obj_lines, obj_name, "tag")
        tag = tag_raw.strip().strip('"') if tag_raw else None
        log.info("Step 44 | tag = %r", tag)

        desc_raw = get_keyword_value(obj_lines, obj_name, "description")
        desc = desc_raw.strip().strip('"') if desc_raw else None
        log.info("Step 45 | description = %r", desc)

        list_raw = get_keyword_value(obj_lines, obj_name, "list")
        if not list_raw:
            log.warning(
                "Step 46a | No 'list' keyword found for %r - back to step 41",
                obj_name,
            )
            continue

        raw_items = extract_list_items(list_raw)

        if not raw_items or raw_items == [""]:
            log.warning("Step 46a | List is empty for %r - back to step 41", obj_name)
            continue

        log.info("Step 46a | Raw URL items (%d): %s", len(raw_items), raw_items)

        seen   = set()
        unique = []
        for item in raw_items:
            if item not in seen:
                seen.add(item)
                unique.append(item)
        if len(unique) < len(raw_items):
            log.info("Step 46b | Removed %d duplicate(s)",
                     len(raw_items) - len(unique))
        items = unique

        stripped = []
        for item in items:
            if item.lower().startswith("https://"):
                clean = item[len("https://"):]
                log.debug("Step 46c | Stripped 'https://' from %r -> %r",
                          item, clean)
                stripped.append(clean)
            else:
                stripped.append(item)
        items = stripped

        pattern_list = []
        string_list  = []

        for item in items:
            log.info("Step 46d | Evaluating: %r", item)

            if has_regex_chars(item):
                log.info("  -> regex chars detected - step 47 path")
                result = sanitize_as_pattern(item)
                if result is not None:
                    pattern_list.append(result)
            else:
                log.info("  -> no regex chars - step 48 path")
                result = sanitize_as_url(item)
                if result is not None:
                    string_list.append(result)

        log.info("Patterns (%d): %s", len(pattern_list), pattern_list)
        log.info("Strings  (%d): %s", len(string_list),  string_list)

        payload = build_payload(
            TEMP_JSON_FILE, obj_name, tag, desc, pattern_list, string_list
        )

        json_str = json.dumps(payload, indent=4)
        json_str = json_str.replace("\\\\/", "\\/")
        with open(TEMP_JSON_FILE, "w", encoding="utf-8") as fh:
            fh.write(json_str)
        log.info("Payload written to: %s", TEMP_JSON_FILE)
        log.debug("Payload:\n%s", json_str)

        post_url_category(obj_name, json_str)

        if os.path.isfile(TEMP_JSON_FILE):
            os.remove(TEMP_JSON_FILE)
            log.info("Step 50 | Deleted temp JSON: %s", TEMP_JSON_FILE)

    _step_51()

def _step_51():
    log.info("Step 51 | Cleaning up and exiting")
    if os.path.isfile(TEMP_INPUT_FILE):
        os.remove(TEMP_INPUT_FILE)
        log.info("Step 51 | Deleted: %s", TEMP_INPUT_FILE)
    log.info("Step 51 | Done.")
    sys.exit(0)

if __name__ == "__main__":
    main()