#!/usr/bin/env python3
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

GENERAL_FILE     = os.path.join(BASE_DIR, "temp", "general.txt")
FINAL_URLF_FILE  = os.path.join(BASE_DIR, "final-data", "final-urlf-profile.txt")
TEMP_URLF_FILE   = os.path.join(BASE_DIR, "temp", "temp-urlf-profile.txt")
TEMPLATE_JSON    = os.path.join(BASE_DIR, "json", "urlf-profile", "post-urlf-profile.json")
TEMP_JSON_FILE   = os.path.join(BASE_DIR, "temp", "post-urlf-profile.json")
CUSTOM_URLF_FILE = os.path.join(BASE_DIR, "final-data", "final-custom-urlf-profile.txt")
CUSTOM_UUID_FILE = os.path.join(BASE_DIR, "temp", "csutom-urlf-profile-uuid.txt")
FORTI_VERSA_FILE = os.path.join(BASE_DIR, "miscellaneous", "Forti-to-Versa-urlf-categories.txt")
UNKNOWN_FILE          = os.path.join(BASE_DIR, "unknown-urlf-category.txt")
DUPLICATE_REPORT_FILE = os.path.join(BASE_DIR, "urlf-prof-duplicates-removed.txt")

# Fortinet native flat-line prefixes produced by step-6 flattening
PREFIX_URLF   = "webfilter profile"
PREFIX_CUSTOM = "webfilter urlfilter"

# Fortinet action -> Versa action
FORTI_ACTION_MAP = {
    "allow":        "allow",
    "exempt":       "allow",
    "block":        "block",
    "monitor":      "alert",
    "warning":      "justify",
    "authenticate": "justify",
}


# ── General config ────────────────────────────────────────────────────────────

def read_general():
    config = {}
    with open(GENERAL_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if " >> " in line:
                key, val = line.split(" >> ", 1)
                config[key.strip()] = val.strip()
    return config


# ── Line parsing ──────────────────────────────────────────────────────────────

def extract_object_name_from_line(line):
    """Return the profile name from a 'webfilter profile "Name" ...' line."""
    line = line.strip()
    if not line.startswith(PREFIX_URLF):
        return None
    rest = line[len(PREFIX_URLF):].lstrip()
    if not rest:
        return None
    if rest.startswith('"'):
        m = re.match(r'"((?:[^"\\]|\\.)*)"', rest)
        return m.group(1) if m else None
    return rest.split()[0] if rest.split() else None


def group_lines_by_object(filepath):
    """Group all lines in filepath by their profile name (preserving order)."""
    objects = {}
    order = []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.rstrip("\n")
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
    """Extract comment text from 'webfilter profile "Name" comment "..."' lines."""
    for line in lines:
        m = re.search(r'\bcomment\s+"((?:[^"\\]|\\.)*)"', line)
        if m:
            return m.group(1)
        m = re.search(r'\bcomment\s+(\S+)', line)
        if m:
            val = m.group(1)
            if val:
                return val
    return None


# ── Action classification ─────────────────────────────────────────────────────

def classify_action_line(line):
    """
    Parse a flattened Fortinet webfilter profile line and return
    (versa_action, [token]) or None.

    Handled formats (produced by step-6 flatten_forti_webfilter_sections):
      webfilter profile "Name" ftgd-wf filter N category <id> action <action>
      webfilter profile "Name" urlfilter-table "TableName"
    """
    # ftgd-wf category filter
    m = re.search(r'\sftgd-wf\s+filter\s+\d+\s+category\s+(\S+)\s+action\s+(\S+)', line)
    if m:
        cat_id       = m.group(1)
        forti_action = m.group(2).lower()
        versa_action = FORTI_ACTION_MAP.get(forti_action)
        if versa_action:
            return (versa_action, [cat_id])
        return None

    # urlfilter-table reference -> custom URL category list under "block"
    m = re.search(r'\surlfilter-table\s+(.+)$', line)
    if m:
        tail = m.group(1).strip()
        if tail.startswith('"'):
            m2 = re.match(r'"((?:[^"\\]|\\.)*)"', tail)
            table_name = m2.group(1) if m2 else tail.strip('"')
        else:
            table_name = tail.split()[0]
        if table_name:
            return ("block", [table_name])
        return None

    return None


def aggregate_actions(obj_lines):
    """Collect all category tokens grouped by Versa action for one profile."""
    actions = {"justify": [], "alert": [], "block": [], "allow": []}
    for ln in obj_lines:
        result = classify_action_line(ln)
        if not result:
            continue
        versa_action, tokens = result
        if versa_action in actions:
            actions[versa_action].extend(tokens)
    # dedup preserving order
    for k in actions:
        seen = set()
        deduped = []
        for t in actions[k]:
            if t not in seen:
                seen.add(t)
                deduped.append(t)
        actions[k] = deduped
    return actions


# ── Mapping loaders ───────────────────────────────────────────────────────────

def load_custom_urlf_names():
    """
    Load custom URL category names from final-custom-urlf-profile.txt.
    Lines are in Fortinet native format:
      webfilter urlfilter "Name" entry N url ...
    """
    names = set()
    if not os.path.exists(CUSTOM_URLF_FILE):
        log.warning("Custom URLF file not found: %s", CUSTOM_URLF_FILE)
        return names
    with open(CUSTOM_URLF_FILE, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line.startswith(PREFIX_CUSTOM):
                continue
            rest = line[len(PREFIX_CUSTOM):].lstrip()
            if not rest:
                continue
            if rest.startswith('"'):
                m = re.match(r'"((?:[^"\\]|\\.)*)"', rest)
                if m:
                    names.add(m.group(1))
            else:
                tok = rest.split()[0] if rest.split() else None
                if tok:
                    names.add(tok)
    return names


def load_custom_uuids():
    """Load UUID mappings for custom URL categories from general.txt and uuid file."""
    uuids = {}
    for filepath in [GENERAL_FILE, CUSTOM_UUID_FILE]:
        if not os.path.exists(filepath):
            continue
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line or " >> " in line:
                    continue
                if ":" in line:
                    name, u = line.split(":", 1)
                    name = name.strip()
                    u = u.strip()
                    if name and u:
                        uuids[name] = u
    return uuids


def load_forti_versa_mapping():
    """
    Load Forti-to-Versa category mapping.
    File format: ID >> FortiName >> VersaName  (3-column)
    Keys the dictionary by numeric ID string (e.g. "26") because
    ftgd-wf filter lines carry the raw numeric category ID.
    Entries with empty VersaName are skipped (no Versa equivalent).
    """
    mapping = {}
    if not os.path.exists(FORTI_VERSA_FILE):
        log.warning("Forti-to-Versa mapping file not found: %s", FORTI_VERSA_FILE)
        return mapping
    with open(FORTI_VERSA_FILE, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if " >> " not in line:
                continue
            parts = [p.strip() for p in line.split(" >> ")]
            if len(parts) >= 3:
                # ID >> FortiName >> VersaName — key by numeric ID
                cat_id    = parts[0]
                versa_cat = parts[2]
                # Skip entries with no Versa equivalent
                if cat_id and versa_cat:
                    mapping[cat_id] = versa_cat
            elif len(parts) == 2:
                # Could be "ID >> FortiName >>" (no trailing space = no Versa mapping)
                # Skip if the value still ends with ">>" indicating empty VersaName
                key, versa_cat = parts[0], parts[1]
                if versa_cat.endswith(">>"):
                    continue
                if key and versa_cat:
                    mapping[key] = versa_cat
    log.info("Loaded %d Forti-to-Versa category mappings (keyed by numeric ID)", len(mapping))
    return mapping


# ── JSON building ─────────────────────────────────────────────────────────────

UNKNOWN_HEADER = (
    "╔═══════════════════════════════════════════════════════════════════════════════════════╗\n"
    "║                               !!  ATTENTION  !!                                       ║\n"
    "╠═══════════════════════════════════════════════════════════════════════════════════════╣\n"
    "║  These URL categories are being referred by your source configuration, security URL   ║\n"
    "║  filtering profiles. If it's meant to be custom URL categories, it wasn't included    ║\n"
    "║  in your source configuration. If it's meant to be pre-defined URL categories,        ║\n"
    "║  they're not compatible with Versa URL categories. It was removed from URLF profile.  ║\n"
    "╚═══════════════════════════════════════════════════════════════════════════════════════╝\n"
    "\n"
)


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
        log.warning("Unknown URLF category added to unknown file: %s", word)


def build_action_entry(action_name, tokens, custom_names, custom_uuids, forti_versa_map):
    """Build a single categoryList entry for the given Versa action."""
    if not tokens:
        return None

    custom_entries = []
    predefined_cats = []

    for token in tokens:
        if token in custom_names:
            u = custom_uuids.get(token, "")
            custom_entries.append({"name": token, "uuid": u})
            log.info("  [%s] Matched custom URLF category: %s", action_name, token)
        elif token in forti_versa_map:
            versa_cat = forti_versa_map[token]
            predefined_cats.append(versa_cat)
            log.info("  [%s] Mapped Forti ID '%s' -> Versa '%s'", action_name, token, versa_cat)
        else:
            log.warning("  [%s] No mapping for '%s' — writing to unknown file", action_name, token)
            append_unknown(token)

    if not custom_entries and not predefined_cats:
        return None

    # Dedup predefined (multiple Fortinet IDs can map to the same Versa name)
    seen = set()
    predefined_cats = [c for c in predefined_cats if not (c in seen or seen.add(c))]

    entry = {"actionCombo": {"predefined": action_name}}
    if custom_entries:
        entry["ecpUserDefinedCombo"] = custom_entries
    if predefined_cats:
        entry["predefined"] = predefined_cats

    return entry


def deduplicate_category_list(obj_name, category_list):
    """
    Walk category_list in order (justify → alert → block → allow).
    The first action to claim a predefined category or custom category keeps it;
    any later action that carries the same one gets it stripped.
    If an action ends up with nothing after stripping, the whole action entry is
    dropped.  Findings are appended to DUPLICATE_REPORT_FILE.
    """
    seen_predefined = set()
    seen_custom     = set()
    report_lines    = []
    cleaned_list    = []

    for entry in category_list:
        action_name       = entry.get("actionCombo", {}).get("predefined", "unknown")
        removed_predefined = []
        removed_custom     = []

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
                "Profile: {}  |  Action: {}".format(obj_name, action_name)
            )
            for cat in removed_predefined:
                report_lines.append("    [PREDEFINED REMOVED] {}".format(cat))
                log.warning(
                    "Duplicate predefined cat %r removed from action %r in profile %r",
                    cat, action_name, obj_name
                )
            for cat in removed_custom:
                report_lines.append("    [CUSTOM REMOVED]     {}".format(cat))
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
        has_custom     = bool(new_entry.get("ecpUserDefinedCombo"))
        if has_predefined or has_custom:
            cleaned_list.append(new_entry)
        else:
            log.warning(
                "Action %r in profile %r is empty after dedup, dropping it",
                action_name, obj_name
            )
            report_lines.append(
                "    [ACTION DROPPED - empty after dedup] {}".format(action_name)
            )

    if report_lines:
        with open(DUPLICATE_REPORT_FILE, "a", encoding="utf-8") as fh:
            fh.write("\n".join(report_lines) + "\n")
            fh.write("-" * 60 + "\n")

    return cleaned_list


def process_object(obj_name, lines, custom_names, custom_uuids, forti_versa_map):
    """Build the full JSON payload for one URLF profile object."""
    log.info("Processing URLF profile object: %s", obj_name)

    with open(TEMPLATE_JSON, "r") as f:
        template_text = f.read()

    try:
        data = json.loads(template_text)
    except json.JSONDecodeError as e:
        log.error("Failed to parse template JSON for '%s': %s", obj_name, e)
        return None

    data["name"] = obj_name

    desc = extract_description(lines)
    if desc:
        data["description"] = desc
    else:
        data.pop("description", None)

    # Fortinet webfilter profiles have no tag concept
    data.pop("tags", None)

    data["attributes"]["criteria"]["uuid"] = str(uuid.uuid4())

    # Aggregate all Fortinet action lines into Versa action buckets
    actions = aggregate_actions(lines)
    log.info("  justify tokens: %s", actions["justify"])
    log.info("  alert tokens:   %s", actions["alert"])
    log.info("  block tokens:   %s", actions["block"])
    log.info("  allow tokens:   %s", actions["allow"])

    category_list = []
    for action_name in ("justify", "alert", "block", "allow"):
        entry = build_action_entry(
            action_name, actions[action_name],
            custom_names, custom_uuids, forti_versa_map
        )
        if entry:
            category_list.append(entry)

    log.info("  Built %d action entries for categoryList", len(category_list))

    category_list = deduplicate_category_list(obj_name, category_list)
    log.info("  After cross-action dedup: %d action entries remain", len(category_list))

    data["attributes"]["criteria"]["value"]["categoryList"] = category_list

    return data


# ── API posting ───────────────────────────────────────────────────────────────

def post_to_api(config, json_data):
    fqdn = config.get("concerto-fqdn", "")
    if not fqdn.startswith("http"):
        fqdn = "https://" + fqdn
    tenant_uuid  = config.get("tenant-uuid", "")
    bearer       = config.get("bearer-token", "")
    csrf         = config.get("csrf-token", "")
    cookies_str  = config.get("cookies", "")

    url = "{}/portalapi/v1/tenants/{}/sase/real-time/profile/urlf".format(fqdn, tenant_uuid)

    cookies = {}
    for part in cookies_str.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            cookies[k.strip()] = v.strip()

    headers = {
        "Authorization": "Bearer {}".format(bearer),
        "X-CSRF-Token": csrf,
        "Content-Type": "application/json"
    }

    log.info("POSTing to: %s", url)
    try:
        resp = requests.post(url, headers=headers, cookies=cookies, json=json_data, verify=False)
        log.info("Response status: %s", resp.status_code)
        log.info("Response body: %s", resp.text)
        return resp
    except Exception as e:
        log.error("POST request failed: %s", e)
        return None


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log.info("=== Starting Fortinet URLF profile conversion ===")

    if os.path.exists(DUPLICATE_REPORT_FILE):
        os.remove(DUPLICATE_REPORT_FILE)
        log.info("Cleared previous duplicate report: %s", DUPLICATE_REPORT_FILE)

    if not os.path.exists(FINAL_URLF_FILE) or os.path.getsize(FINAL_URLF_FILE) == 0:
        log.info("final-urlf-profile.txt does not exist or is empty. Exiting.")
        return

    shutil.copy2(FINAL_URLF_FILE, TEMP_URLF_FILE)
    log.info("Copied %s -> %s", FINAL_URLF_FILE, TEMP_URLF_FILE)

    if os.path.getsize(TEMP_URLF_FILE) == 0:
        log.info("temp-urlf-profile.txt is empty. Exiting.")
        return

    config      = read_general()
    log.info("Loaded general config keys: %s", list(config.keys()))

    custom_names = load_custom_urlf_names()
    log.info("Loaded %d custom URLF category names", len(custom_names))

    custom_uuids = load_custom_uuids()
    log.info("Loaded %d custom URLF UUIDs", len(custom_uuids))

    forti_versa_map = load_forti_versa_mapping()
    log.info("Loaded %d Forti-to-Versa category mappings", len(forti_versa_map))

    objects, order = group_lines_by_object(TEMP_URLF_FILE)
    log.info("Found %d URLF profile objects to process", len(objects))

    for obj_name in order:
        lines = objects[obj_name]
        log.info("--- Processing: %s (%d lines) ---", obj_name, len(lines))

        json_data = process_object(obj_name, lines, custom_names, custom_uuids, forti_versa_map)
        if json_data is None:
            log.error("Failed to build JSON for '%s', skipping", obj_name)
            continue

        with open(TEMP_JSON_FILE, "w") as f:
            json.dump(json_data, f, indent=4)

        resp = post_to_api(config, json_data)
        if resp is not None and resp.status_code in (200, 201):
            log.info("Successfully POSTed URLF profile: %s", obj_name)
        else:
            status = resp.status_code if resp is not None else "N/A"
            log.error("Failed to POST URLF profile: %s, status: %s", obj_name, status)

    for cleanup_path in [TEMP_JSON_FILE, TEMP_URLF_FILE]:
        if os.path.exists(cleanup_path):
            os.remove(cleanup_path)
            log.info("Deleted temp file: %s", cleanup_path)

    log.info("=== URLF profile conversion complete ===")


if __name__ == "__main__":
    main()
