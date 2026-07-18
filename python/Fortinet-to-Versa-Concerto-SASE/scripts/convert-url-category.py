#!/usr/bin/env python3
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

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

LOG_DIR = os.path.join(BASE_DIR, "log")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
FINAL_DATA_DIR = os.path.join(BASE_DIR, "final-data")
JSON_DIR = os.path.join(BASE_DIR, "json", "url-category")

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

FINAL_INPUT_FILE = os.path.join(FINAL_DATA_DIR, "final-custom-urlf-profile.txt")
TEMP_INPUT_FILE = os.path.join(TEMP_DIR, "temp-custom-urlf-profile.txt")
JSON_TEMPLATE = os.path.join(JSON_DIR, "post-url-category.json")
TEMP_JSON_FILE = os.path.join(TEMP_DIR, "post-url-category.json")
GENERAL_FILE = os.path.join(BASE_DIR, "temp", "general.txt")

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
    delimiter = " >> "
    with open(GENERAL_FILE, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if delimiter in line:
                k, _, v = line.partition(delimiter)
                if k.strip() == key:
                    return v.strip()
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


_fqdn = read_general_value("concerto-fqdn") or ""
_port = read_general_value("concerto-port") or "443"
CONCERTO_URL = "https://{}:{}".format(_fqdn, _port) if _fqdn else "<<concerto-url>>"
TENANT_UUID = read_general_value("tenant-uuid") or "<<tenant-uuid>>"
BEARER_TOKEN = read_general_value("bearer-token") or "<<bearer-token>>"
_cookie_str = read_general_value("cookies") or ""
COOKIES = parse_cookies(_cookie_str) if _cookie_str else {}
CSRF_TOKEN = COOKIES.get("ECP-CSRF-TOKEN", "")


def validate_config():
    required = {
        "concerto-fqdn": _fqdn,
        "tenant-uuid": TENANT_UUID,
        "bearer-token": BEARER_TOKEN,
        "cookies": _cookie_str,
    }
    missing = [k for k, v in required.items() if not v or v.startswith("<<")]
    if missing:
        log.error("CONFIGURATION ERROR: missing keys in general.txt: %s", missing)
        sys.exit(1)


def build_headers():
    headers = {
        "Authorization": "Bearer " + BEARER_TOKEN,
        "Content-Type": "application/json",
    }
    if CSRF_TOKEN:
        headers["X-CSRF-Token"] = CSRF_TOKEN
    return headers


def post_url_category(obj_name, json_str):
    url = "{}/portalapi/v1/tenants/{}/sase/settings/urlCategory".format(CONCERTO_URL, TENANT_UUID)
    log.info("POST | Sending object '%s' to %s", obj_name, url)
    resp = requests.post(url, verify=False, cookies=COOKIES, headers=build_headers(), data=json_str.encode("utf-8"))
    log.info("POST | Status: %s", resp.status_code)
    try:
        log.info("POST | Response body:\n%s", json.dumps(resp.json(), indent=2))
    except Exception:
        log.info("POST | Response body (raw): %s", resp.text)
    return resp


FORTI_CUSTOM_PREFIX = "webfilter urlfilter"


def parse_objects(lines):
    """
    Group Fortinet-format urlfilter lines by object name.
    Input format (one URL per line):
      webfilter urlfilter <n> entry <N> url <url> type <t> action <a> status <s>
    """
    objects = {}
    order = []
    import shlex as _shlex
    for raw in lines:
        line = raw.rstrip("\n")
        if not line.strip():
            continue
        if not line.startswith(FORTI_CUSTOM_PREFIX):
            continue
        try:
            toks = _shlex.split(line)
        except Exception:
            toks = line.split()
        if len(toks) < 3:
            continue
        obj_name = toks[2]
        if obj_name not in objects:
            objects[obj_name] = []
            order.append(obj_name)
        objects[obj_name].append(line)
    return objects, order


def extract_urls_from_forti_lines(obj_lines):
    """
    Extract URL values from Fortinet urlfilter per-entry lines.
    Each line: webfilter urlfilter <n> entry <N> url <value> type ...
    Returns a list of URL strings (one per entry line).
    """
    import shlex as _shlex
    urls = []
    for line in obj_lines:
        try:
            toks = _shlex.split(line)
        except Exception:
            toks = line.split()
        for i, t in enumerate(toks):
            if t == "url" and i + 1 < len(toks):
                url_val = toks[i + 1]
                if url_val and url_val not in ("[", "]"):
                    urls.append(url_val)
                break
    return urls


def has_regex_chars(item):
    return any(ch in POSIX_REGEX_CHARS for ch in item)


def sanitize_as_pattern(item):
    return item


def sanitize_as_url(item):
    return item


def _replace_value_block(raw):
    m = re.search(r'"value"\s*:\s*\{', raw)
    if not m:
        return raw
    start = m.start()
    brace_start = m.end() - 1
    depth = 0
    i = brace_start
    while i < len(raw):
        if raw[i] == '{':
            depth += 1
        elif raw[i] == '}':
            depth -= 1
            if depth == 0:
                before = raw[:m.start()]
                after = raw[i + 1:]
                return before + '"value": {}' + after
        i += 1
    return raw


def build_payload(temp_json, obj_name, tag, desc, pattern_list, string_list):
    with open(temp_json, "r", encoding="utf-8") as fh:
        raw = fh.read()

    start = raw.find("{")
    if start > 0:
        raw = raw[start:]

    raw = raw.replace("@url-category-name", obj_name)

    if tag:
        raw = raw.replace("@url-category-tag", tag)
    else:
        lines = raw.splitlines(keepends=True)
        raw = "".join(ln for ln in lines if "@url-category-tag" not in ln)

    if desc:
        raw = raw.replace("@url-category-descriptiom", desc)
    else:
        lines = raw.splitlines(keepends=True)
        raw = "".join(ln for ln in lines if "@url-category-descriptiom" not in ln)

    raw = _replace_value_block(raw)
    raw = re.sub(r'"@[^"]+"', "null", raw)

    # Remove trailing commas before } or ] (left behind when tag/description lines are stripped)
    raw = re.sub(r',\s*([}\]])', r'\1', raw)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        log.error("build_payload | JSON parse failed: %s", exc)
        raise

    value_section = (
        payload
        .setdefault("attributes", {})
        .setdefault("criteria", {})
        .setdefault("value", {})
    )

    # Final dedup: remove duplicates that survived earlier processing
    seen_p = set()
    deduped_patterns = []
    for p in pattern_list:
        if p not in seen_p:
            seen_p.add(p)
            deduped_patterns.append(p)
    if len(deduped_patterns) < len(pattern_list):
        log.info("Final dedup | Removed %d duplicate pattern(s)", len(pattern_list) - len(deduped_patterns))
    pattern_list = deduped_patterns

    seen_s = set()
    deduped_strings = []
    for s in string_list:
        if s not in seen_s:
            seen_s.add(s)
            deduped_strings.append(s)
    if len(deduped_strings) < len(string_list):
        log.info("Final dedup | Removed %d duplicate string(s)", len(string_list) - len(deduped_strings))
    string_list = deduped_strings

    if pattern_list:
        value_section["pattern"] = [
            {"pattern": p, "reputation": None} for p in pattern_list
        ]

    if string_list:
        value_section["string"] = [
            {"string": s, "reputation": None} for s in string_list
        ]

    return payload


def _step_51():
    log.info("Step 51 | Cleaning up and exiting")
    if os.path.isfile(TEMP_INPUT_FILE):
        os.remove(TEMP_INPUT_FILE)
        log.info("Step 51 | Deleted: %s", TEMP_INPUT_FILE)
    log.info("Step 51 | Done.")
    sys.exit(0)


def main():
    validate_config()

    log.info("=" * 70)
    log.info("Convert Fortinet custom URL categories -> Concerto API")
    log.info("=" * 70)
    log.info("Target: %s | Tenant: %s", CONCERTO_URL, TENANT_UUID)

    if not os.path.isfile(FINAL_INPUT_FILE) or os.path.getsize(FINAL_INPUT_FILE) == 0:
        log.warning("File missing or empty: %s", FINAL_INPUT_FILE)
        _step_51()
        return

    shutil.copy2(FINAL_INPUT_FILE, TEMP_INPUT_FILE)
    log.info("Copied to: %s", TEMP_INPUT_FILE)

    with open(TEMP_INPUT_FILE, "r", encoding="utf-8") as fh:
        all_lines = fh.readlines()

    if not any(line.strip() for line in all_lines):
        log.warning("Temp file is empty")
        _step_51()
        return

    objects, order = parse_objects(all_lines)
    log.info("Found %d object(s): %s", len(order), order)

    if not order:
        _step_51()
        return

    for obj_name in order:
        obj_lines = objects[obj_name]
        log.info("-" * 60)
        log.info("Processing object: %r (%d config line(s))", obj_name, len(obj_lines))

        if not os.path.isfile(JSON_TEMPLATE):
            log.error("Template not found: %s - skipping", JSON_TEMPLATE)
            continue
        shutil.copy2(JSON_TEMPLATE, TEMP_JSON_FILE)

        # Fortinet urlfilter has no tag or description fields
        tag = None
        desc = None

        # Extract one URL per entry line
        raw_items = extract_urls_from_forti_lines(obj_lines)
        if not raw_items:
            log.warning("No URL entries found for %r - skipping", obj_name)
            continue

        log.info("Raw URL items (%d): %s", len(raw_items), raw_items)

        seen = set()
        unique = []
        for item in raw_items:
            if item not in seen:
                seen.add(item)
                unique.append(item)
        items = unique

        stripped = []
        for item in items:
            if item.lower().startswith("https://"):
                stripped.append(item[len("https://"):])
            else:
                stripped.append(item)
        items = stripped

        pattern_list = []
        string_list = []

        for item in items:
            if has_regex_chars(item):
                result = sanitize_as_pattern(item)
                if result is not None:
                    pattern_list.append(result)
            else:
                result = sanitize_as_url(item)
                if result is not None:
                    string_list.append(result)

        log.info("Patterns (%d): %s", len(pattern_list), pattern_list)
        log.info("Strings  (%d): %s", len(string_list), string_list)

        payload = build_payload(TEMP_JSON_FILE, obj_name, tag, desc, pattern_list, string_list)

        json_str = json.dumps(payload, indent=4)
        json_str = json_str.replace("\\\\/", "\\/")
        with open(TEMP_JSON_FILE, "w", encoding="utf-8") as fh:
            fh.write(json_str)

        post_url_category(obj_name, json_str)

        if os.path.isfile(TEMP_JSON_FILE):
            os.remove(TEMP_JSON_FILE)

    _step_51()


if __name__ == "__main__":
    main()
