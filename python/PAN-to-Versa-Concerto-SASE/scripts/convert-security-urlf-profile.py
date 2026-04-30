import os
import re
import json
import uuid
import shutil
import logging
import requests
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

disable_warnings(InsecureRequestWarning)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

LOG_PATH = os.path.join(BASE_DIR, "log", "step-8.log")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

GENERAL_FILE = os.path.join(BASE_DIR, "temp", "general.txt")
FINAL_URLF_FILE = os.path.join(BASE_DIR, "final-data", "final-urlf-profile.txt")
TEMP_URLF_FILE = os.path.join(BASE_DIR, "temp", "temp-urlf-profile.txt")
TEMPLATE_JSON_PATH = os.path.join(BASE_DIR, "json", "urlf-profile", "post-urlf-profile.json")
TEMP_JSON_PATH = os.path.join(BASE_DIR, "temp", "post-urlf-profile.json")
CUSTOM_URLF_FILE = os.path.join(BASE_DIR, "final-data", "final-custom-urlf-profile.txt")
CUSTOM_UUID_FILE = os.path.join(BASE_DIR, "temp", "csutom-urlf-profile-uuid.txt")
PAN_VERSA_FILE = os.path.join(BASE_DIR, "miscellaneous", "PAN-to-Versa-urlf-categories.txt")
UNKNOWN_FILE = os.path.join(BASE_DIR, "unknown-urlf-category.txt")
DUPLICATE_REPORT_FILE = os.path.join(BASE_DIR, "urlf-prof-duplicates-removed.txt")

OBJ_PREFIX_RE = r'set\s+shared\s+profiles\s+url-filtering\s+(?:"(?:[^"]+)"|(?:\S+))'

UNKNOWN_HEADER = (
    "╔═══════════════════════════════════════════════════════════════════════════════════════╗\n"
    "║                               !!  ATTENTION  !!                                       ║\n"
    "╠═══════════════════════════════════════════════════════════════════════════════════════╣\n"
    "║  These URL categories are being referred by your source configuration, security URL   ║\n"
    "║  filtering profiles. If it's meant to be custom URL categories, it wasn't included    ║\n"
    "║  in your source configuration. If it's meant to be pre-defined URL categories,        ║\n"
    "║  they're not compatible with Versa URL categories.                                    ║\n"
    "╚═══════════════════════════════════════════════════════════════════════════════════════╝\n"
    "\n"
)

def read_general():
    config = {}
    with open(GENERAL_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if ">>" in line:
                key, val = re.split(r'\s*>>\s*', line, 1)
                config[key.strip()] = val.strip()
    return config

def parse_words_from_content(content):
    words = []
    for m in re.finditer(r'"([^"]+)"|(\S+)', content):
        if m.group(1):
            words.append(m.group(1))
        else:
            words.append(m.group(2))
    return words

def extract_object_name_from_line(line):
    m = re.match(r'set\s+shared\s+profiles\s+url-filtering\s+("([^"]+)"|(\S+))', line)
    if not m:
        return None
    return m.group(2) if m.group(2) else m.group(3)

def group_lines_by_object(filepath):
    objects = {}
    order = []
    with open(filepath, "r") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n")
            if not line.strip():
                continue
            name = extract_object_name_from_line(line)
            if name:
                if name not in objects:
                    objects[name] = []
                    order.append(name)
                objects[name].append(line)
    return objects, order

def extract_description(lines):
    for line in lines:
        m = re.search(
            OBJ_PREFIX_RE + r'\s+description\s+"([^"]*)"',
            line
        )
        if m:
            return m.group(1)
        m = re.search(
            OBJ_PREFIX_RE + r'\s+description\s+(\S+)',
            line
        )
        if m:
            return m.group(1)
    return None

def extract_tag(lines):
    for line in lines:
        m = re.search(
            OBJ_PREFIX_RE + r'\s+tag\s+(\S+)',
            line
        )
        if m:
            return m.group(1)
    return None

def extract_words_for_keyword(lines, keyword, is_cred_enforcement=False):
    words = []

    if is_cred_enforcement:
        prefix = OBJ_PREFIX_RE + r'\s+credential-enforcement\s+' + re.escape(keyword)
    else:
        prefix = OBJ_PREFIX_RE + r'\s+' + re.escape(keyword)

    re_list = re.compile(prefix + r'\s+\[([^\]]*)\]')
    re_single = re.compile(prefix + r'\s+("(?:[^"]+)"|(\S+))\s*$')

    for line in lines:
        has_cred = "credential-enforcement" in line
        if is_cred_enforcement and not has_cred:
            continue
        if not is_cred_enforcement and has_cred:
            continue

        m = re_list.search(line)
        if m:
            content = m.group(1).strip()
            if content:
                words.extend(parse_words_from_content(content))
            continue

        m = re_single.search(line)
        if m:
            w = m.group(1).strip()
            if w.startswith('"') and w.endswith('"'):
                w = w[1:-1]
            if w:
                words.append(w)

    return words

def load_custom_urlf_names():
    names = set()
    if not os.path.exists(CUSTOM_URLF_FILE):
        log.warning(f"Custom URLF file not found: {CUSTOM_URLF_FILE}")
        return names
    with open(CUSTOM_URLF_FILE, "r") as f:
        for line in f:
            m = re.match(
                r'set\s+shared\s+profiles\s+custom-url-category\s+("([^"]+)"|(\S+))',
                line.strip()
            )
            if m:
                name = m.group(2) if m.group(2) else m.group(3)
                names.add(name)
    return names

def load_custom_uuids():
    uuids = {}
    for filepath in [GENERAL_FILE, CUSTOM_UUID_FILE]:
        if not os.path.exists(filepath):
            log.warning(f"UUID source file not found: {filepath}")
            continue
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if not line or ">>" in line:
                    continue
                if ":" in line:
                    name, u = line.split(":", 1)
                    name = name.strip()
                    u = u.strip()
                    if name and u:
                        uuids[name] = u
    return uuids

def load_pan_versa_mapping():
    mapping = {}
    if not os.path.exists(PAN_VERSA_FILE):
        log.warning(f"PAN-to-Versa mapping file not found: {PAN_VERSA_FILE}")
        return mapping
    with open(PAN_VERSA_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if ">>" in line:
                pan_cat, versa_cat = re.split(r'\s*>>\s*', line, 1)
                mapping[pan_cat.strip()] = versa_cat.strip()
    return mapping

def append_unknown(word):
    existing = set()
    file_exists = os.path.exists(UNKNOWN_FILE)
    if file_exists:
        with open(UNKNOWN_FILE, "r") as f:
            existing = {l.strip() for l in f if l.strip()}
    if word not in existing:
        with open(UNKNOWN_FILE, "a") as f:
            if not file_exists:
                f.write(UNKNOWN_HEADER)
            f.write(word + "\n")
        log.warning(f"Unknown URLF category added to unknown file: {word}")

def build_action_entry(action_name, words, custom_names, custom_uuids, pan_versa_map):
    if not words:
        return None

    custom_entries = []
    predefined_cats = []

    for word in words:
        if word in custom_names:
            u = custom_uuids.get(word, "")
            custom_entries.append({"name": word, "uuid": u})
            log.info(f"  [{action_name}] Matched custom URLF category: {word}")
        elif word in pan_versa_map:
            versa_cat = pan_versa_map[word]
            predefined_cats.append(versa_cat)
            log.info(f"  [{action_name}] Matched PAN category '{word}' -> Versa '{versa_cat}'")
        else:
            log.warning(f"  [{action_name}] No match for '{word}', writing to unknown file")
            append_unknown(word)

    if not custom_entries and not predefined_cats:
        return None

    entry = {"actionCombo": {"predefined": action_name}}
    if custom_entries:
        entry["ecpUserDefinedCombo"] = custom_entries
    if predefined_cats:
        entry["predefined"] = predefined_cats

    return entry

def deduplicate_category_list(obj_name, category_list):
    seen_predefined = set()
    seen_custom = set()
    report_lines = []
    cleaned_list = []

    for entry in category_list:
        action_name = entry.get("actionCombo", {}).get("predefined", "unknown")
        removed_predefined = []
        removed_custom = []

        new_predefined = []
        for cat in entry.get("predefined", []):
            if cat in seen_predefined:
                removed_predefined.append(cat)
            else:
                seen_predefined.add(cat)
                new_predefined.append(cat)

        new_custom = []
        for item in entry.get("ecpUserDefinedCombo", []):
            cat_name = item.get("name", "")
            if cat_name in seen_custom:
                removed_custom.append(cat_name)
            else:
                seen_custom.add(cat_name)
                new_custom.append(item)

        if removed_predefined or removed_custom:
            report_lines.append(
                f"Profile: {obj_name}  |  Action: {action_name}"
            )
            for cat in removed_predefined:
                report_lines.append(f"    [PREDEFINED REMOVED] {cat}")
                log.warning(
                    "Duplicate predefined cat %r removed from action %r in profile %r",
                    cat, action_name, obj_name
                )
            for cat in removed_custom:
                report_lines.append(f"    [CUSTOM REMOVED]     {cat}")
                log.warning(
                    "Duplicate custom cat %r removed from action %r in profile %r",
                    cat, action_name, obj_name
                )

        new_entry = dict(entry)
        if new_predefined:
            new_entry["predefined"] = new_predefined
        elif "predefined" in new_entry:
            del new_entry["predefined"]
        if new_custom:
            new_entry["ecpUserDefinedCombo"] = new_custom
        elif "ecpUserDefinedCombo" in new_entry:
            del new_entry["ecpUserDefinedCombo"]

        has_predefined = bool(new_entry.get("predefined"))
        has_custom = bool(new_entry.get("ecpUserDefinedCombo"))
        if has_predefined or has_custom:
            cleaned_list.append(new_entry)
        else:
            log.warning(
                "Action %r in profile %r is empty after dedup, dropping it",
                action_name, obj_name
            )
            report_lines.append(
                f"    [ACTION DROPPED - empty after dedup] {action_name}"
            )

    if report_lines:
        with open(DUPLICATE_REPORT_FILE, "a", encoding="utf-8") as fh:
            fh.write("\n".join(report_lines) + "\n")
            fh.write("-" * 60 + "\n")

    return cleaned_list

def process_object(obj_name, lines, custom_names, custom_uuids, pan_versa_map):
    log.info(f"Processing URLF profile object: {obj_name}")

    with open(TEMPLATE_JSON_PATH, "r") as f:
        template_text = f.read()

    try:
        data = json.loads(template_text)
    except json.JSONDecodeError as e:
        log.error(f"Failed to parse template JSON for object '{obj_name}': {e}")
        return None

    data["name"] = obj_name
    log.info(f"  Set name: {obj_name}")

    desc = extract_description(lines)
    if desc:
        data["description"] = desc
        log.info(f"  Set description: {desc}")
    else:
        data.pop("description", None)
        log.info("  No description found, removed from JSON")

    tag = extract_tag(lines)
    if tag:
        data["tags"] = [tag]
        log.info(f"  Set tag: {tag}")
    else:
        data.pop("tags", None)
        log.info("  No tag found, removed from JSON")

    data["attributes"]["criteria"]["uuid"] = str(uuid.uuid4())

    justify_words = extract_words_for_keyword(lines, "allow", is_cred_enforcement=True)
    log.info(f"  justify words (cred-enforcement allow): {justify_words}")

    alert_words = extract_words_for_keyword(lines, "alert", is_cred_enforcement=False)
    log.info(f"  alert words: {alert_words}")

    allow_words = extract_words_for_keyword(lines, "allow", is_cred_enforcement=False)
    log.info(f"  allow words: {allow_words}")

    cred_block_words = extract_words_for_keyword(lines, "block", is_cred_enforcement=True)
    direct_block_words = extract_words_for_keyword(lines, "block", is_cred_enforcement=False)
    seen = set()
    all_block_words = []
    for w in cred_block_words + direct_block_words:
        if w not in seen:
            seen.add(w)
            all_block_words.append(w)
    log.info(f"  block words (cred-enforcement block + direct block, deduped): {all_block_words}")

    category_list = []

    justify_entry = build_action_entry("justify", justify_words, custom_names, custom_uuids, pan_versa_map)
    if justify_entry:
        category_list.append(justify_entry)

    alert_entry = build_action_entry("alert", alert_words, custom_names, custom_uuids, pan_versa_map)
    if alert_entry:
        category_list.append(alert_entry)

    block_entry = build_action_entry("block", all_block_words, custom_names, custom_uuids, pan_versa_map)
    if block_entry:
        category_list.append(block_entry)

    allow_entry = build_action_entry("allow", allow_words, custom_names, custom_uuids, pan_versa_map)
    if allow_entry:
        category_list.append(allow_entry)

    log.info(f"  Built {len(category_list)} action entries for categoryList")

    category_list = deduplicate_category_list(obj_name, category_list)
    log.info(f"  After cross-action dedup: {len(category_list)} action entries remain")

    data["attributes"]["criteria"]["value"]["categoryList"] = category_list

    return data

def post_to_api(config, json_data):
    fqdn = config.get("concerto-fqdn", "")
    if not fqdn.startswith("http"):
        fqdn = "https://" + fqdn
    port = config.get("concerto-port", "443")
    tenant_uuid = config.get("tenant-uuid", "")
    bearer = config.get("bearer-token", "")
    csrf = config.get("csrf-token", "")
    cookies_str = config.get("cookies", "")

    url = f"{fqdn}/portalapi/v1/tenants/{tenant_uuid}/sase/real-time/profile/urlf"

    cookies = {}
    for part in cookies_str.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            cookies[k.strip()] = v.strip()

    headers = {
        "Authorization": f"Bearer {bearer}",
        "X-CSRF-Token": csrf,
        "Content-Type": "application/json"
    }

    log.info(f"POSTing to: {url}")
    log.debug(f"Payload: {json.dumps(json_data, indent=2)}")

    try:
        resp = requests.post(url, headers=headers, cookies=cookies, json=json_data, verify=False)
        log.info(f"Response status: {resp.status_code}")
        log.info(f"Response body: {resp.text}")
        return resp
    except Exception as e:
        log.error(f"POST request failed: {e}")
        return None

def main():
    log.info("=== Starting URLF profile conversion ===")

    if os.path.exists(DUPLICATE_REPORT_FILE):
        os.remove(DUPLICATE_REPORT_FILE)
        log.info("Cleared previous duplicate report: %s", DUPLICATE_REPORT_FILE)

    if not os.path.exists(FINAL_URLF_FILE) or os.path.getsize(FINAL_URLF_FILE) == 0:
        log.info("final-urlf-profile.txt does not exist or is empty. Exiting.")
        return

    shutil.copy2(FINAL_URLF_FILE, TEMP_URLF_FILE)
    log.info(f"Copied {FINAL_URLF_FILE} to {TEMP_URLF_FILE}")

    if os.path.getsize(TEMP_URLF_FILE) == 0:
        log.info("temp-urlf-profile.txt is empty. Exiting.")
        return

    config = read_general()
    log.info(f"Loaded general config keys: {list(config.keys())}")

    custom_names = load_custom_urlf_names()
    log.info(f"Loaded {len(custom_names)} custom URLF category names")

    custom_uuids = load_custom_uuids()
    log.info(f"Loaded {len(custom_uuids)} custom URLF UUIDs")

    pan_versa_map = load_pan_versa_mapping()
    log.info(f"Loaded {len(pan_versa_map)} PAN-to-Versa category mappings")

    objects, order = group_lines_by_object(TEMP_URLF_FILE)
    log.info(f"Found {len(objects)} URLF profile objects to process")

    for obj_name in order:
        lines = objects[obj_name]
        log.info(f"--- Processing object: {obj_name} ({len(lines)} config lines) ---")

        json_data = process_object(obj_name, lines, custom_names, custom_uuids, pan_versa_map)
        if json_data is None:
            log.error(f"Failed to build JSON for object: {obj_name}, skipping")
            continue

        with open(TEMP_JSON_PATH, "w") as f:
            json.dump(json_data, f, indent=4)
        log.info(f"Written temp JSON to {TEMP_JSON_PATH}")

        resp = post_to_api(config, json_data)
        if resp is not None and resp.status_code in (200, 201):
            log.info(f"Successfully POSTed URLF profile: {obj_name}")
        else:
            status = resp.status_code if resp is not None else "N/A"
            log.error(f"Failed to POST URLF profile: {obj_name}, status: {status}")

    for cleanup_path in [TEMP_JSON_PATH, TEMP_URLF_FILE]:
        if os.path.exists(cleanup_path):
            os.remove(cleanup_path)
            log.info(f"Deleted temp file: {cleanup_path}")

    log.info("=== URLF profile conversion complete ===")

if __name__ == "__main__":
    main()