import os
import sys
import re
import json
import shutil
import requests
from typing import Optional, List, Dict, Tuple
from requests.packages import urllib3

def prompt_with_timeout(prompt_text, default_value, timeout=15):
    import signal
    
    def print_box(text):
        lines = text.split('\n')
        max_len = max(len(line) for line in lines)
        print('╔' + '═' * (max_len + 2) + '╗')
        for line in lines:
            print('║ ' + line.ljust(max_len) + ' ║')
        print('╚' + '═' * (max_len + 2) + '╝')
    
    def timeout_handler(signum, frame):
        raise TimeoutError()
    
    print_box(prompt_text + f'\n(Default: {default_value} - auto-continue in {timeout}s)')
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)
    
    try:
        user_input = input('> ').strip()
        signal.alarm(0)
        return user_input if user_input else default_value
    except TimeoutError:
        signal.alarm(0)
        print(f'\nTimeout - using default: {default_value}')
        return default_value
    except Exception:
        signal.alarm(0)
        return default_value

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
FINAL_DATA_DIR = os.path.join(BASE_DIR, "final-data")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
LOG_DIR = os.path.join(BASE_DIR, "log")
MISC_DIR = os.path.join(BASE_DIR, "miscellaneous")
JSON_DIR = os.path.join(BASE_DIR, "json", "policy")
STEP6_DIR = os.path.join(BASE_DIR, "step-6")
FAILED_POLICY_JSON_DIR = os.path.join(BASE_DIR, "failed-policy-json")

CLEANED_RULES = os.path.join(FINAL_DATA_DIR, "cleaned-pan-rules.txt")
STEP6_RULES = os.path.join(STEP6_DIR, "step-6_cleaned-pan-rules.txt")
TEMP_RULES = os.path.join(TEMP_DIR, "temp-cleaned-pan-rules.txt")
GENERAL_TXT = os.path.join(TEMP_DIR, "general.txt")
ZONE_CONV = os.path.join(BASE_DIR, "zone-conversion.txt")
PREDEF_APP_CONV = os.path.join(BASE_DIR, "predef-application-conversion.txt")
PREDEF_SVC_CONV = os.path.join(BASE_DIR, "predef-service-conversion.txt")
PAN_URLF_CAT = os.path.join(MISC_DIR, "PAN-to-Versa-urlf-categories.txt")
CUSTOM_URLF_NAMES = os.path.join(FINAL_DATA_DIR, "final-custom-urlf-profile.txt")
FINAL_URLF_PROFILE = os.path.join(FINAL_DATA_DIR, "final-urlf-profile.txt")
LDAP_SOURCE_INPUT = os.path.join(BASE_DIR, "ldap-source-input.txt")
SCIM_USER_INPUT = os.path.join(BASE_DIR, "scim-source-user-input.txt")
SCIM_GROUP_INPUT = os.path.join(BASE_DIR, "scim-groups-dump.txt")
SCIM_USERS_DUMP = os.path.join(BASE_DIR, "scim-users-dump.txt")
LDAP_GROUPS_UUID = os.path.join(TEMP_DIR, "ldap-groups-uuid.txt")
LDAP_USERS_FILE = os.path.join(TEMP_DIR, "concerto-ldap-users.txt")
ADDR_GROUP_CACHE = os.path.join(TEMP_DIR, "adddress-group.txt")
CUST_SVC_CACHE = os.path.join(TEMP_DIR, "cust-service.txt")
CUSTOM_URL_CAT_CACHE = os.path.join(TEMP_DIR, "custom-url-category.txt")
URLF_PROFILE_CACHE = os.path.join(TEMP_DIR, "urlf-profile.txt")
LDAP_PROFILE_CACHE = os.path.join(TEMP_DIR, "ldap-profile.txt")
SCIM_PROFILE_CACHE = os.path.join(TEMP_DIR, "scim-profile.txt")
UNRESOLVED_OBJ = os.path.join(BASE_DIR, "unresolved-objects-configuration.txt")
UNRESOLVED_URL = os.path.join(BASE_DIR, "unresolved-url-configuration.txt")
UNDEFINED_SVC = os.path.join(BASE_DIR, "undefined-service.txt")
UNKNOWN_URLF = os.path.join(BASE_DIR, "unresolved-urlf-profile.txt")
UNRESOLVED_SCIM_USERS = os.path.join(BASE_DIR, "unresolved-scim-users.txt")
UNRESOLVED_SCIM_GROUPS = os.path.join(BASE_DIR, "unresolved-scim-groups.txt")
POST_RESULTS = os.path.join(BASE_DIR, "post-policy-results.txt")
FAILED_POST_RESPONSES = os.path.join(BASE_DIR, "failed-policy-post-response.txt")
LOG_FILE = os.path.join(LOG_DIR, "step-8.log")

DEDUP_FIELDS = {"to", "from", "source", "destination", "source-user", "application", "tag", "category", "service"}

log_fh = None
policy_enabled = True

def log(msg):
    print(msg)
    if log_fh:
        log_fh.write(msg + "\n")
        log_fh.flush()

def read_general():
    result = {}
    with open(GENERAL_TXT, "r") as f:
        for line in f:
            line = line.strip()
            if ">>" in line:
                key, val = re.split(r'\s*>>\s*', line, 1)
                result[key.strip()] = val.strip()
    return result

def get_session(general):
    base_url = "https://" + general["concerto-fqdn"]
    bearer = general["bearer-token"]
    csrf = general["csrf-token"]
    cookies_str = general["cookies"]
    session = requests.Session()
    for part in cookies_str.split("; "):
        if "=" in part:
            name, val = part.split("=", 1)
            session.cookies.set(name, val)
    headers = {
        "Authorization": "Bearer " + bearer,
        "X-CSRF-Token": csrf,
        "Content-Type": "application/json"
    }
    return session, headers, base_url

def paginated_get(session, headers, base_url, url_template, window_size=100):
    all_data = []
    window = 0
    while True:
        url = base_url + url_template.format(window_number=window, window_size=window_size)
        log("GET " + url)
        resp = session.get(url, verify=False, headers=headers)
        log("Response: " + str(resp.status_code))
        if resp.status_code != 200:
            log("Error response: " + resp.text[:500])
            break
        body = resp.json()
        data = body.get("data", [])
        if data is None:
            data = []
        count = len(data)
        log("Received " + str(count) + " items in window " + str(window))
        if count == 0:
            break
        all_data.extend(data)
        if count < window_size:
            break
        window += 1
    log("Total items fetched: " + str(len(all_data)))
    return all_data

def parse_bracket_list(content):
    items = []
    i = 0
    content = content.strip()
    while i < len(content):
        if content[i] == '"':
            close = content.find('"', i + 1)
            if close == -1:
                rest = content[i + 1:].strip()
                for token in rest.split():
                    if token:
                        items.append(token)
                break
            items.append(content[i + 1:close])
            i = close + 1
        elif content[i].isspace():
            i += 1
        else:
            if content[i:i+3].upper() == 'CN=':
                end = i
                while end < len(content) and content[end] != ']' and content[end] != '"':
                    if content[end] == ' ':
                        look = end + 1
                        while look < len(content) and content[look] == ' ':
                            look += 1
                        if look >= len(content) or content[look] == ']' or content[look:look+3].upper() == 'CN=':
                            break
                    end += 1
                token = content[i:end].rstrip()
                if token:
                    items.append(token)
                i = end
            else:
                end = i
                while end < len(content) and not content[end].isspace():
                    end += 1
                items.append(content[i:end])
                i = end
    return items

def get_policy_name_and_remainder(line):
    match = re.search(r'security rules\s+', line)
    if not match:
        return None, None
    pos = match.end()
    rest = line[pos:]
    if rest.startswith('"'):
        eq = rest.index('"', 1)
        name = rest[1:eq]
        remainder = rest[eq + 1:].strip()
    else:
        sp = rest.find(' ')
        if sp == -1:
            name = rest.strip()
            remainder = ""
        else:
            name = rest[:sp]
            remainder = rest[sp + 1:].strip()
    return name, remainder

def mask_quoted(s):
    return re.sub(r'"[^"]*"', lambda m: '"' + 'X' * (len(m.group()) - 2) + '"', s)

def extract_values_from_remainder(remainder, keyword):
    kw = keyword.strip()
    masked = mask_quoted(remainder)
    idx = -1
    for m in re.finditer(r'^\s*' + re.escape(kw) + r'(?:\s|$)', masked):
        idx = m.start()
        break
    if idx == -1:
        return None
    after = remainder[idx:].strip()
    after = after[len(kw):].strip()
    if not after:
        return None
    if after.startswith('['):
        if ']' not in after:
            return parse_bracket_list(after[1:])
        bracket_end = after.index(']')
        return parse_bracket_list(after[1:bracket_end])
    elif after.startswith('"'):
        eq = after.index('"', 1)
        return [after[1:eq]]
    else:
        return [after.split()[0]]

def remainder_has_keyword(remainder, keyword):
    masked = mask_quoted(remainder)
    return bool(re.search(r'^\s*' + re.escape(keyword) + r'(?:\s|$)', masked))

def load_conversion_file(filepath, delimiter=r'\s*>>\s*'):
    result = {}
    if not os.path.exists(filepath):
        return result
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if ">>" in line:
                parts = re.split(delimiter, line, 1)
                result[parts[0].strip()] = parts[1].strip()
    return result

def load_name_list_file(filepath, keyword=None):
    names = set()
    if not os.path.exists(filepath):
        return names
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if keyword:
                match = re.search(re.escape(keyword) + r'\s+', line)
                if match:
                    rest = line[match.end():].strip()
                    if rest.startswith('"'):
                        eq = rest.index('"', 1)
                        names.add(rest[1:eq])
                    else:
                        sp = rest.find(' ')
                        if sp == -1:
                            names.add(rest)
                        else:
                            names.add(rest[:sp])
            else:
                names.add(line)
    return names

def load_colon_cache(filepath):
    result = {}
    if not os.path.exists(filepath):
        return result
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if ":" in line:
                parts = line.split(":", 1)
                result[parts[0].strip()] = parts[1].strip()
    return result

def load_arrow_cache(filepath):
    result = {}
    if not os.path.exists(filepath):
        return result
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if ">>" in line:
                parts = re.split(r'\s*>>\s*', line, 1)
                result[parts[0].strip()] = parts[1].strip()
    return result

def save_colon_cache(filepath, data):
    with open(filepath, "w") as f:
        for name, uuid in data.items():
            f.write(name + ":" + uuid + "\n")

def save_arrow_cache(filepath, data):
    with open(filepath, "w") as f:
        for name, uuid in data.items():
            f.write(name + " >> " + uuid + "\n")

def append_line(filepath, line):
    with open(filepath, "a") as f:
        f.write(line + "\n")

def write_unresolved_urlf(line_text):
    global policy_enabled
    policy_enabled = False
    header = (
        "╔═══════════════════════════════════════════════════════════════════════════════════════╗\n"
        "║                               !!  ATTENTION  !!                                       ║\n"
        "╠═══════════════════════════════════════════════════════════════════════════════════════╣\n"
        "║  These security URL filtering profiles are being referred to by your source           ║\n"
        "║  configuration. Either the configuration for that URL filtering profile wasn't        ║\n"
        "║  included in your source configuration file or there was an error during processing.  ║\n"
        "║  The firewall policy mentioned below were converted and transferred to Concerto in     ║\n"
        "║  DISABLED status. Please remediate the configuration and manually enable the          ║\n"
        "║  affected policies.                                                                   ║\n"
        "╚═══════════════════════════════════════════════════════════════════════════════════════╝\n"
        "\n"
    )
    if not os.path.exists(UNKNOWN_URLF):
        with open(UNKNOWN_URLF, "w") as f:
            f.write(header)
    with open(UNKNOWN_URLF, "a") as f:
        f.write(line_text + "\n")

def write_unresolved_url(line_text):
    global policy_enabled
    policy_enabled = False
    header = (
        "╔═══════════════════════════════════════════════════════════════════════════════════════╗\n"
        "║                               !!  ATTENTION  !!                                       ║\n"
        "╠═══════════════════════════════════════════════════════════════════════════════════════╣\n"
        "║  These URL categories are being referred by your source configuration, firewall       ║\n"
        "║  policies configuration. If it's meant to be custom URL categories, it wasn't         ║\n"
        "║  included in your source configuration. If it's meant to be pre-defined URL           ║\n"
        "║  categories, they're not compatible with Versa URL categories.                        ║\n"
        "║  The firewall policies affected were converted and transferred to Concerto in          ║\n"
        "║  DISABLED status. Please remediate the configuration and manually enable the          ║\n"
        "║  affected policies.                                                                   ║\n"
        "╚═══════════════════════════════════════════════════════════════════════════════════════╝\n"
        "\n"
    )
    if not os.path.exists(UNRESOLVED_URL):
        with open(UNRESOLVED_URL, "w") as f:
            f.write(header)
    with open(UNRESOLVED_URL, "a") as f:
        f.write(line_text + "\n")

def write_unresolved_scim_user(entry_text):
    global policy_enabled
    policy_enabled = False
    header = (
        "╔═══════════════════════════════════════════════════════════════════════════════════════╗\n"
        "║                               !!  ATTENTION  !!                                       ║\n"
        "╠═══════════════════════════════════════════════════════════════════════════════════════╣\n"
        "║  The users listed below could not be resolved during policy conversion. They are      ║\n"
        "║  referenced in your source firewall configuration but could not be matched against    ║\n"
        "║  the SCIM or LDAP data provided. Firewall policies referring to these users have      ║\n"
        "║  been converted and transferred to Concerto in DISABLED status. Please remediate      ║\n"
        "║  the configuration and manually enable the affected policies.                         ║\n"
        "╚═══════════════════════════════════════════════════════════════════════════════════════╝\n"
        "\n"
    )
    if not os.path.exists(UNRESOLVED_SCIM_USERS):
        with open(UNRESOLVED_SCIM_USERS, "w") as f:
            f.write(header)
    with open(UNRESOLVED_SCIM_USERS, "a") as f:
        f.write(entry_text + "\n")

def write_unresolved_scim_group(entry_text):
    global policy_enabled
    policy_enabled = False
    header = (
        "╔═══════════════════════════════════════════════════════════════════════════════════════╗\n"
        "║                               !!  ATTENTION  !!                                       ║\n"
        "╠═══════════════════════════════════════════════════════════════════════════════════════╣\n"
        "║  The groups listed below could not be resolved during policy conversion. They are     ║\n"
        "║  referenced in your source firewall configuration but could not be matched against    ║\n"
        "║  the SCIM or LDAP data provided. Firewall policies referring to these groups have     ║\n"
        "║  been converted and transferred to Concerto in DISABLED status. Please remediate      ║\n"
        "║  the configuration and manually enable the affected policies.                         ║\n"
        "╚═══════════════════════════════════════════════════════════════════════════════════════╝\n"
        "\n"
    )
    if not os.path.exists(UNRESOLVED_SCIM_GROUPS):
        with open(UNRESOLVED_SCIM_GROUPS, "w") as f:
            f.write(header)
    with open(UNRESOLVED_SCIM_GROUPS, "a") as f:
        f.write(entry_text + "\n")

def write_unresolved_obj(line_text):
    global policy_enabled
    policy_enabled = False
    header = (
        "╔═══════════════════════════════════════════════════════════════════════════════════════╗\n"
        "║                               !!  ATTENTION  !!                                       ║\n"
        "╠═══════════════════════════════════════════════════════════════════════════════════════╣\n"
        "║  These address objects are being referred to by your source firewall configuration    ║\n"
        "║  but could not be resolved in Concerto. Either the objects were not migrated yet      ║\n"
        "║  or there was an error during processing. The valid address objects in the same       ║\n"
        "║  rule have been included. The affected policies were converted and transferred to      ║\n"
        "║  Concerto in DISABLED status. Please remediate the configuration and manually         ║\n"
        "║  enable the affected policies.                                                        ║\n"
        "╚═══════════════════════════════════════════════════════════════════════════════════════╝\n"
        "\n"
    )
    if not os.path.exists(UNRESOLVED_OBJ):
        with open(UNRESOLVED_OBJ, "w") as f:
            f.write(header)
    with open(UNRESOLVED_OBJ, "a") as f:
        f.write(line_text + "\n")

def fetch_address_groups(session, headers, base_url, general):
    if os.path.exists(ADDR_GROUP_CACHE):
        return load_colon_cache(ADDR_GROUP_CACHE)
    tenant = general["tenant-uuid"]
    url_tpl = "/portalapi/v1/tenants/" + tenant + "/elements/endpoint/summarize?windowSize={window_size}&nextWindowNumber={window_number}&category=ADDRESS_GROUP&ecpScope=SASE"
    data = paginated_get(session, headers, base_url, url_tpl)
    result = {}
    for item in data:
        entity = item.get("entity", item)
        name = entity.get("name", "")
        uuid = entity.get("uuid", "")
        if name and uuid:
            result[name] = uuid
    save_colon_cache(ADDR_GROUP_CACHE, result)
    log("Fetched " + str(len(result)) + " address groups")
    return result

def fetch_custom_services(session, headers, base_url, general):
    if os.path.exists(CUST_SVC_CACHE):
        return load_arrow_cache(CUST_SVC_CACHE)
    tenant = general["tenant-uuid"]
    url_tpl = "/portalapi/v1/tenants/" + tenant + "/elements/services/summary?windowSize={window_size}&nextWindowNumber={window_number}&ecpScope=SASE&filter=all"
    data = paginated_get(session, headers, base_url, url_tpl)
    result = {}
    for item in data:
        ecp = item.get("ecpUserDefined", {})
        for svc_name, svc_list in ecp.items():
            if isinstance(svc_list, list):
                for entry in svc_list:
                    name = entry.get("name", "")
                    uuid = entry.get("uuid", "")
                    if name and uuid:
                        result[name] = uuid
    save_arrow_cache(CUST_SVC_CACHE, result)
    log("Fetched " + str(len(result)) + " custom services")
    return result

def fetch_custom_url_categories(session, headers, base_url, general):
    if os.path.exists(CUSTOM_URL_CAT_CACHE):
        return load_arrow_cache(CUSTOM_URL_CAT_CACHE)
    tenant = general["tenant-uuid"]
    url_tpl = "/portalapi/v1/tenants/" + tenant + "/sase/settings/urlCategory/summarize?windowSize={window_size}&nextWindowNumber={window_number}&category=URL_CATEGORY&ecpScope=SASE"
    data = paginated_get(session, headers, base_url, url_tpl)
    result = {}
    for item in data:
        name = item.get("name", "")
        uuid = item.get("uuid", "")
        if name and uuid:
            result[name] = uuid
    save_arrow_cache(CUSTOM_URL_CAT_CACHE, result)
    log("Fetched " + str(len(result)) + " custom URL categories")
    return result

def fetch_urlf_profiles(session, headers, base_url, general):
    if os.path.exists(URLF_PROFILE_CACHE):
        return load_arrow_cache(URLF_PROFILE_CACHE)
    tenant = general["tenant-uuid"]
    url_tpl = "/portalapi/v1/tenants/" + tenant + "/sase/real-time/profile/urlf/summarize?nextWindowNumber={window_number}&windowSize={window_size}"
    data = paginated_get(session, headers, base_url, url_tpl)
    result = {}
    for item in data:
        name = item.get("name", "")
        uuid = item.get("uuid", "")
        if name and uuid:
            result[name] = uuid
    save_arrow_cache(URLF_PROFILE_CACHE, result)
    log("Fetched " + str(len(result)) + " URLF profiles")
    return result

def fetch_ldap_profiles(session, headers, base_url, general):
    if os.path.exists(LDAP_PROFILE_CACHE):
        return load_colon_cache(LDAP_PROFILE_CACHE)
    tenant = general["tenant-uuid"]
    url = base_url + "/portalapi/v1/tenants/" + tenant + "/sase/authentication/profile/summarize?nextWindowNumber=0&windowSize=100&searchKeyword="
    log("GET " + url)
    resp = session.get(url, verify=False, headers=headers)
    log("Response: " + str(resp.status_code))
    result = {}
    if resp.status_code == 200:
        data = resp.json().get("data", [])
        for item in data:
            name = item.get("name", "")
            uuid = item.get("uuid", "")
            if name and uuid:
                result[name] = uuid
    save_colon_cache(LDAP_PROFILE_CACHE, result)
    log("Fetched " + str(len(result)) + " LDAP profiles")
    return result

def fetch_scim_profiles(session, headers, base_url, general):
    if os.path.exists(SCIM_PROFILE_CACHE):
        return load_colon_cache(SCIM_PROFILE_CACHE)
    tenant = general["tenant-uuid"]
    url = base_url + "/portalapi/v1/tenants/" + tenant + "/sase/scim/summarize?nextWindowNumber=0&windowSize=25"
    log("GET " + url)
    resp = session.get(url, verify=False, headers=headers)
    log("Response: " + str(resp.status_code))
    result = {}
    if resp.status_code == 200:
        data = resp.json().get("data", [])
        for item in data:
            name = item.get("name", "")
            uuid = item.get("uuid", "")
            if name and uuid:
                result[name] = uuid
    save_colon_cache(SCIM_PROFILE_CACHE, result)
    log("Fetched " + str(len(result)) + " SCIM profiles")
    return result

def get_version_control(session, headers, base_url, general):
    tenant = general["tenant-uuid"]
    url = base_url + "/portalapi/v1/tenants/" + tenant + "/sase/real-time/internet-protection/summarize?nextWindowNumber=0&windowSize=10"
    log("GET " + url)
    resp = session.get(url, verify=False, headers=headers)
    log("Response: " + str(resp.status_code))
    if resp.status_code == 200:
        body = resp.json()
        vc = body.get("versionControl", None)
        log("versionControl: " + str(vc))
        return vc
    return None

def convert_zone(word, zone_conv):
    if word in zone_conv:
        converted = zone_conv[word]
        if converted:
            return converted
    return word

def extract_cn_name(dn_string):
    dn = dn_string.strip().strip('"')
    match = re.match(r'CN=([^,]+)', dn, re.IGNORECASE)
    if match:
        return match.group(1)
    return dn

def extract_domain_from_dn(dn_string):
    dn = dn_string.strip().strip('"')
    parts = re.findall(r'DC=([^,]+)', dn, re.IGNORECASE)
    if parts:
        return ".".join(parts)
    return ""

def extract_username_from_object(obj_str):
    obj = obj_str.strip().strip('"')
    if re.match(r'CN=', obj, re.IGNORECASE):
        return extract_cn_name(obj)
    elif '\\' in obj:
        return obj.split('\\', 1)[1]
    elif '@' in obj:
        return obj.split('@', 1)[0]
    else:
        parts = obj.rsplit('/', 1)
        if len(parts) > 1:
            return parts[1]
        return obj

def parse_source_user_list(remainders):
    for rem in remainders:
        vals = extract_values_from_remainder(rem, "source-user")
        if vals is not None:
            return vals
    return None

def _parse_ldap_section_lines(lines, section):
    result = []
    block = "\n".join(lines).strip()
    if block.startswith("["):
        try:
            entries = json.loads(block)
            for entry in entries:
                obj = entry.get("object", "").strip().strip('"')
                if obj:
                    result.append(obj)
            return result
        except Exception:
            pass
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if section == "users":
            dn = line.strip('"').strip()
            if dn and re.match(r'CN=', dn, re.IGNORECASE):
                result.append(dn)
        elif section == "groups":
            match = re.search(r'(CN=[^"]+)', line)
            if match:
                dn = match.group(1).strip().strip('"')
                if dn:
                    result.append(dn)
    return result

def load_ldap_source_input():
    users = []
    groups = []
    if not os.path.exists(LDAP_SOURCE_INPUT):
        return users, groups
    section = None
    section_lines = []
    with open(LDAP_SOURCE_INPUT, "r") as f:
        for line in f:
            stripped = line.strip()
            if stripped == "----BEGIN USERS----":
                section = "users"
                section_lines = []
                continue
            elif stripped == "----END USERS----":
                users = _parse_ldap_section_lines(section_lines, "users")
                section = None
                section_lines = []
                continue
            elif stripped == "----BEGIN GROUPS----":
                section = "groups"
                section_lines = []
                continue
            elif stripped == "----END GROUPS----":
                groups = _parse_ldap_section_lines(section_lines, "groups")
                section = None
                section_lines = []
                continue
            if section:
                section_lines.append(line.rstrip("\n\r"))
    return users, groups

def find_ldap_match(simple_name, ldap_entries, case_sensitive=True):
    for entry in ldap_entries:
        cn = extract_cn_name(entry)
        if case_sensitive:
            if cn == simple_name:
                return entry
        else:
            if cn.lower() == simple_name.lower():
                return entry
    return None

def process_zones(remainders, zone_conv):
    source_zones = []
    dest_zones = []
    skip_source = False
    skip_dest = False
    for rem in remainders:
        vals = extract_values_from_remainder(rem, "from")
        if vals is not None:
            if len(vals) == 1 and vals[0].lower() in ("any", "all"):
                skip_source = True
            else:
                for v in vals:
                    if v.lower() not in ("any", "all"):
                        source_zones.append(convert_zone(v, zone_conv))
        vals = extract_values_from_remainder(rem, "to")
        if vals is not None:
            if len(vals) == 1 and vals[0].lower() in ("any", "all"):
                skip_dest = True
            else:
                for v in vals:
                    if v.lower() not in ("any", "all"):
                        dest_zones.append(convert_zone(v, zone_conv))
    if skip_source:
        source_zones = []
    if skip_dest:
        dest_zones = []
    return source_zones, dest_zones

def process_addresses(remainders, full_lines, addr_groups, session, headers, base_url, general):
    if not addr_groups:
        addr_groups = fetch_address_groups(session, headers, base_url, general)
    source_addrs = []
    dest_addrs = []
    skip_source = False
    skip_dest = False
    for i, rem in enumerate(remainders):
        src_vals = extract_values_from_remainder(rem, "source")
        if src_vals is not None:
            if len(src_vals) == 1 and src_vals[0].lower() in ("any", "all"):
                skip_source = True
            else:
                for v in src_vals:
                    if v.lower() in ("any", "all"):
                        continue
                    if v in addr_groups:
                        source_addrs.append({"uuid": addr_groups[v], "name": v})
                    else:
                        write_unresolved_obj(full_lines[i] + " << UNRESOLVED " + v)
                        log("UNRESOLVED source address: " + v)
        dst_vals = extract_values_from_remainder(rem, "destination")
        if dst_vals is not None:
            if len(dst_vals) == 1 and dst_vals[0].lower() in ("any", "all"):
                skip_dest = True
            else:
                for v in dst_vals:
                    if v.lower() in ("any", "all"):
                        continue
                    if v in addr_groups:
                        dest_addrs.append({"uuid": addr_groups[v], "name": v})
                    else:
                        write_unresolved_obj(full_lines[i] + " << UNRESOLVED " + v)
                        log("UNRESOLVED destination address: " + v)
    if skip_source:
        source_addrs = []
    if skip_dest:
        dest_addrs = []
    return source_addrs, dest_addrs, addr_groups

def process_applications(remainders, full_lines):
    app_conv = load_conversion_file(PREDEF_APP_CONV)
    all_caps_apps = []
    mixed_apps = []
    for i, rem in enumerate(remainders):
        vals = extract_values_from_remainder(rem, "application")
        if vals is not None:
            if len(vals) == 1 and vals[0].lower() in ("any", "all"):
                continue
            for v in vals:
                if v.lower() in ("any", "all"):
                    continue
                if v in app_conv:
                    converted = app_conv[v]
                    app_name = converted if converted else v
                else:
                    app_name = v
                if app_name == app_name.upper():
                    all_caps_apps.append(app_name)
                else:
                    mixed_apps.append(app_name)
    return all_caps_apps, mixed_apps

def process_services(remainders, full_lines, cust_svc_cache, session, headers, base_url, general):
    predef_conv = load_conversion_file(PREDEF_SVC_CONV)
    predefined = []
    custom = []
    for i, rem in enumerate(remainders):
        vals = extract_values_from_remainder(rem, "service")
        if vals is not None:
            if len(vals) == 1 and vals[0].lower() in ("any", "all"):
                continue
            for v in vals:
                if v.lower() in ("any", "all"):
                    continue
                if v in predef_conv:
                    converted = predef_conv[v]
                    predefined.append(converted if converted else v)
                else:
                    if not cust_svc_cache:
                        cust_svc_cache.update(fetch_custom_services(session, headers, base_url, general))
                    if v in cust_svc_cache:
                        custom.append({"uuid": cust_svc_cache[v], "name": v})
                    else:
                        append_line(UNDEFINED_SVC, full_lines[i])
                        log("UNDEFINED service: " + v)
    return predefined, custom, cust_svc_cache

def process_url_categories(remainders, full_lines, custom_url_cache, session, headers, base_url, general):
    predef_conv = load_conversion_file(PAN_URLF_CAT)
    predefined = []
    custom_cats = []
    for i, rem in enumerate(remainders):
        vals = extract_values_from_remainder(rem, "category")
        if vals is not None:
            if len(vals) == 1 and vals[0].lower() in ("any", "all"):
                continue
            for v in vals:
                if v.lower() in ("any", "all"):
                    continue
                if v in predef_conv:
                    converted = predef_conv[v]
                    if converted:
                        predefined.append(converted)
                    else:
                        predefined.append(v)
                else:
                    if not custom_url_cache:
                        custom_url_cache.update(fetch_custom_url_categories(session, headers, base_url, general))
                    if v in custom_url_cache:
                        custom_cats.append({"uuid": custom_url_cache[v], "name": v})
                    else:
                        write_unresolved_url(full_lines[i] + " << UNRESOLVED " + v)
                        log("UNRESOLVED URL category: " + v)
    return predefined, custom_cats, custom_url_cache

def load_urlf_profile_names():
    names = set()
    if not os.path.exists(FINAL_URLF_PROFILE):
        return names
    with open(FINAL_URLF_PROFILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            match = re.search(r'profiles url-filtering\s+', line)
            if match:
                rest = line[match.end():].strip()
                if rest.startswith('"'):
                    eq = rest.index('"', 1)
                    names.add(rest[1:eq])
                else:
                    sp = rest.find(' ')
                    names.add(rest[:sp] if sp != -1 else rest)
            else:
                names.add(line)
    return names

def process_security_profiles(remainders, full_lines, session, headers, base_url, general):
    has_action_allow = False
    has_action_deny = False
    has_virus = False
    has_spyware = False
    has_vulnerability = False
    has_file_blocking = False
    has_url_filtering = False
    url_filtering_name = None
    for rem in remainders:
        if remainder_has_keyword(rem, "action"):
            vals = extract_values_from_remainder(rem, "action")
            if vals:
                if vals[0].lower() == "allow":
                    has_action_allow = True
                elif vals[0].lower() == "deny":
                    has_action_deny = True
        if "profile-setting profiles" in rem:
            if "profile-setting profiles virus" in rem:
                has_virus = True
            if "profile-setting profiles spyware" in rem:
                has_spyware = True
            if "profile-setting profiles vulnerability" in rem:
                has_vulnerability = True
            if "profile-setting profiles file-blocking" in rem:
                has_file_blocking = True
            if "profile-setting profiles url-filtering" in rem:
                has_url_filtering = True
                parts = rem.split("profile-setting profiles url-filtering", 1)[1].strip()
                if parts.startswith('"'):
                    eq = parts.index('"', 1)
                    url_filtering_name = parts[1:eq]
                else:
                    url_filtering_name = parts.split()[0] if parts.split() else None
    set_value = {}
    has_threat_profiles = has_virus or has_spyware or has_vulnerability or has_file_blocking
    if has_url_filtering and url_filtering_name:
        urlf_known_names = load_urlf_profile_names()
        matched = url_filtering_name in urlf_known_names
        if matched:
            urlf_cache = fetch_urlf_profiles(session, headers, base_url, general)
            if url_filtering_name in urlf_cache:
                set_value["action"] = "security-profile"
                set_value["urlFiltering"] = {
                    "ecpUserDefinedCombo": {
                        "uuid": urlf_cache[url_filtering_name],
                        "name": url_filtering_name
                    }
                }
            else:
                for i, rem in enumerate(remainders):
                    if "profile-setting profiles url-filtering" in rem:
                        write_unresolved_urlf(full_lines[i] + " << UNRESOLVED " + url_filtering_name)
                        break
                log("UNRESOLVED URLF profile (not on server): " + url_filtering_name)
        else:
            for i, rem in enumerate(remainders):
                if "profile-setting profiles url-filtering" in rem:
                    write_unresolved_urlf(full_lines[i] + " << UNRESOLVED " + url_filtering_name)
                    break
            log("UNRESOLVED URLF profile (not in known list): " + url_filtering_name)
    if has_threat_profiles:
        set_value["action"] = "security-profile"
        if has_virus:
            set_value["av"] = {"predefined": "Scan Web and Email Traffic"}
        if has_spyware or has_vulnerability:
            set_value["ips"] = {"predefined": "Versa Recommended Profile"}
        if has_file_blocking:
            set_value["fileFiltering"] = {"predefined": "Versa_Corporate_Profile"}
    if not set_value:
        if has_action_allow:
            set_value = {"action": "Allow", "tcpSessionKeepAlive": False}
        elif has_action_deny:
            set_value = {"action": "Deny", "tcpSessionKeepAlive": False}
        else:
            set_value = {"action": "Allow", "tcpSessionKeepAlive": False}
    return set_value

def load_ldap_groups_uuid():
    result = {}
    if not os.path.exists(LDAP_GROUPS_UUID):
        return result
    with open(LDAP_GROUPS_UUID, "r") as f:
        data = json.load(f)
    for entry in data:
        name = entry.get("name", "")
        obj = entry.get("object", "")
        if name and obj:
            result[name] = obj
    return result

def load_ldap_users_file():
    result = {}
    if not os.path.exists(LDAP_USERS_FILE):
        return result
    with open(LDAP_USERS_FILE, "r") as f:
        data = json.load(f)
    for entry in data:
        name = entry.get("name", "")
        obj = entry.get("object", "")
        if obj:
            cn = extract_cn_name(obj)
            if cn:
                result[cn] = {"name": name, "object": obj}
    return result

def process_ldap_source_user(remainders, full_lines, general, session, headers, base_url):
    su_list = parse_source_user_list(remainders)
    if su_list is None:
        return None
    if len(su_list) == 1 and su_list[0].lower() in ("any", "all"):
        return None
    ldap_profile_name = general.get("ldap-profile", "")
    ldap_profiles = fetch_ldap_profiles(session, headers, base_url, general)
    ldap_profile_uuid = ldap_profiles.get(ldap_profile_name, "")
    ldap_users, ldap_groups = load_ldap_source_input()
    user_section = {
        "userMatchType": "selected",
        "profile": {
            "uuid": ldap_profile_uuid,
            "name": ldap_profile_name,
            "type": "SASE_LDAP_AUTHENTICATION",
            "subtype": "SASE_LDAP_AUTHENTICATION"
        }
    }
    users_list = []
    groups_list = []
    for obj in su_list:
        if obj.lower() in ("any", "all"):
            continue
        simple_name = extract_username_from_object(obj)
        matched_user = find_ldap_match(simple_name, ldap_users)
        matched_group = find_ldap_match(simple_name, ldap_groups)
        if matched_user:
            cn = extract_cn_name(matched_user)
            ldap_users_map = load_ldap_users_file()
            entry = ldap_users_map.get(cn)
            if entry:
                users_list.append({"name": entry["object"], "id": entry["name"]})
            else:
                write_unresolved_scim_user(cn)
                log("UNRESOLVED LDAP user (not in concerto-ldap-users.txt): " + cn)
        elif matched_group:
            cn = extract_cn_name(matched_group)
            use_groups_uuid = general.get("ldap-groups-uuid", "").strip().lower() == "true"
            if use_groups_uuid:
                groups_uuid_map = load_ldap_groups_uuid()
                uuid_object = groups_uuid_map.get(cn)
                if uuid_object:
                    log("LDAP groups UUID: matched group " + cn + " -> " + uuid_object)
                    groups_list.append({"name": uuid_object, "description": cn, "id": cn})
                else:
                    log("LDAP groups UUID: no UUID match for group: " + cn + ", falling back to DN")
                    groups_list.append({"description": cn, "name": matched_group, "id": cn})
            else:
                groups_list.append({"description": cn, "name": matched_group, "id": cn})
        else:
            write_unresolved_scim_user(obj)
            log("UNRESOLVED LDAP source-user: " + obj)
    if users_list:
        user_section["users"] = users_list
    if groups_list:
        user_section["userGroups"] = groups_list
    if not users_list and not groups_list:
        return None
    return user_section

def load_scim_users_dump():
    result = {}
    if not os.path.exists(SCIM_USERS_DUMP):
        return result
    with open(SCIM_USERS_DUMP, "r") as f:
        data = json.load(f)
    entries = data if isinstance(data, list) else data.get("data", [])
    for user in entries:
        username = user.get("userName", "")
        display_name = user.get("displayName", "")
        if username:
            record = {
                "userName": username,
                "displayName": display_name
            }
            result[username.lower()] = record
            if "@" in username:
                prefix = username.split("@")[0].lower()
                if prefix not in result:
                    result[prefix] = record
            if display_name and display_name.lower() not in result:
                result[display_name.lower()] = record
    return result

def load_scim_source_groups():
    result = set()
    if not os.path.exists(SCIM_GROUP_INPUT):
        return result
    with open(SCIM_GROUP_INPUT, "r") as f:
        data = json.load(f)
    for entry in data:
        display_name = entry.get("displayName", "")
        if display_name:
            result.add(display_name)
    return result

def process_scim_source_user(remainders, full_lines, general, session, headers, base_url):
    su_list = parse_source_user_list(remainders)
    if su_list is None:
        return None
    if len(su_list) == 1 and su_list[0].lower() in ("any", "all"):
        return None
    scim_profile_name = general.get("scim-profile", "")
    fetch_scim_profiles(session, headers, base_url, general)
    ldap_users, ldap_groups = load_ldap_source_input()
    scim_lookup = load_scim_users_dump()
    scim_groups = load_scim_source_groups()
    user_section = {
        "userMatchType": "selected",
        "profile": {
            "type": "SASE_SCIM_AUTHENTICATION",
            "subtype": "SASE_SCIM_AUTHENTICATION"
        }
    }
    users_list = []
    groups_list = []
    for obj in su_list:
        if obj.lower() in ("any", "all"):
            continue
        simple_name = extract_username_from_object(obj)
        matched_in_users = find_ldap_match(simple_name, ldap_users, case_sensitive=False)
        matched_in_groups = find_ldap_match(simple_name, ldap_groups, case_sensitive=False)
        if matched_in_users:
            user_simple = extract_cn_name(matched_in_users)
            scim_record = scim_lookup.get(user_simple.lower())
            if scim_record:
                users_list.append({
                    "name": scim_record["displayName"] or user_simple,
                    "id": scim_record["userName"],
                    "description": scim_profile_name
                })
            else:
                write_unresolved_scim_user(user_simple)
                log("UNRESOLVED SCIM user: " + user_simple)
        elif matched_in_groups:
            group_simple = extract_cn_name(matched_in_groups)
            use_groups_uuid = general.get("ldap-groups-uuid", "").strip().lower() == "true"
            if use_groups_uuid:
                groups_uuid_map = load_ldap_groups_uuid()
                uuid_object = groups_uuid_map.get(group_simple)
                if uuid_object:
                    log("LDAP groups UUID: matched group " + group_simple + " -> " + uuid_object)
                    groups_list.append({"name": uuid_object, "description": scim_profile_name, "id": group_simple})
                else:
                    log("LDAP groups UUID: no UUID match for group: " + group_simple + ", falling back to DN")
                    groups_list.append({"name": group_simple, "description": scim_profile_name, "id": group_simple})
            else:
                groups_list.append({
                    "name": group_simple,
                    "description": scim_profile_name,
                    "id": group_simple
                })
        else:
            scim_record = scim_lookup.get(simple_name.lower())
            if scim_record:
                users_list.append({
                    "name": scim_record["displayName"] or simple_name,
                    "id": scim_record["userName"],
                    "description": scim_profile_name
                })
            elif simple_name in scim_groups:
                log("SCIM group match: " + simple_name)
                groups_list.append({"name": simple_name, "description": scim_profile_name, "id": simple_name})
            else:
                write_unresolved_scim_group(obj)
                log("UNRESOLVED SCIM group (no match): " + obj)
    if users_list:
        user_section["users"] = users_list
    if groups_list:
        user_section["userGroups"] = groups_list
    if not users_list and not groups_list:
        return None
    return user_section

def build_policy_json(policy_name, description, tags, match_value, set_value, version_control, username):
    global policy_enabled
    policy = {
        "lastModifiedUser": username,
        "description": description,
        "attributes": {
            "match": {
                "value": match_value
            },
            "set": {
                "value": set_value
            }
        },
        "enabled": policy_enabled,
        "uncloneable": False,
        "name": policy_name,
        "version": None,
        "originId": None,
        "type": "REAL_TIME_PROTECTION",
        "subtype": "INTERNET_PROTECTION",
        "category": None,
        "federatedPath": None,
        "isDefault": None,
        "isReusable": None,
        "tags": tags if tags else [],
        "order": {
            "bottom": True
        },
        "formMode": "CREATE",
        "deploy": False,
        "versionControl": version_control
    }
    return policy

def parse_bracket_tokens_raw(bracket_content):
    tokens = []
    i = 0
    content = bracket_content.strip()
    while i < len(content):
        if content[i] == '"':
            try:
                end = content.index('"', i + 1)
            except ValueError:
                remainder = content[i + 1:].strip()
                if remainder:
                    tokens.append(remainder)
                break
            tokens.append(content[i:end + 1])
            i = end + 1
        elif content[i].isspace():
            i += 1
        else:
            end = i
            while end < len(content) and not content[end].isspace():
                end += 1
            tokens.append(content[i:end])
            i = end
    return tokens

def dedup_tokens_preserve_order(tokens):
    seen = []
    dupes = []
    result = []
    for token in tokens:
        norm = token.strip('"').strip()
        if norm not in seen:
            seen.append(norm)
            result.append(token)
        else:
            dupes.append(token)
    return result, dupes

def check_and_dedup_lines(lines):
    cleaned = []
    total_dupes = 0
    rules_affected = set()
    log("Running duplicate field check on all policy lines...")
    for line in lines:
        name, remainder = get_policy_name_and_remainder(line)
        if name is None or not remainder:
            cleaned.append(line)
            continue
        matched_field = None
        for field in DEDUP_FIELDS:
            if remainder == field or remainder.startswith(field + " "):
                matched_field = field
                break
        if matched_field is None:
            cleaned.append(line)
            continue
        after_field = remainder[len(matched_field):].strip()
        if not after_field.startswith("["):
            cleaned.append(line)
            continue
        try:
            bracket_end_idx = after_field.index("]")
        except ValueError:
            cleaned.append(line)
            continue
        bracket_content = after_field[1:bracket_end_idx]
        try:
            tokens = parse_bracket_tokens_raw(bracket_content)
        except Exception as e:
            log("  WARNING: could not parse bracket in rule [" + str(name) + "] field [" + str(matched_field) + "]: " + str(e) + " — skipping dedup for this line")
            cleaned.append(line)
            continue
        deduped, dupes = dedup_tokens_preserve_order(tokens)
        if not dupes:
            cleaned.append(line)
            continue
        rules_affected.add(name)
        total_dupes += len(dupes)
        log("  DEDUP rule [" + name + "] field [" + matched_field + "]: removed " + str([d.strip('"') for d in dupes]))
        bracket_start = line.index("[")
        bracket_end = line.rindex("]")
        new_bracket = "[ " + " ".join(deduped) + " ]"
        new_line = line[:bracket_start] + new_bracket + line[bracket_end + 1:]
        cleaned.append(new_line)
    if total_dupes > 0:
        log("Dedup summary: " + str(len(rules_affected)) + " rule(s) affected, " + str(total_dupes) + " duplicate value(s) removed")
    else:
        log("Dedup check complete: no duplicates found")
    return cleaned

def group_config_by_policy(lines):
    policies = {}
    policy_order = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        name, remainder = get_policy_name_and_remainder(line)
        if name is None:
            continue
        if name not in policies:
            policies[name] = {"remainders": [], "full_lines": []}
            policy_order.append(name)
        policies[name]["remainders"].append(remainder)
        policies[name]["full_lines"].append(line)
    return policies, policy_order

def main():
    global log_fh
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(FINAL_DATA_DIR, exist_ok=True)
    os.makedirs(FAILED_POLICY_JSON_DIR, exist_ok=True)
    log_fh = open(LOG_FILE, "w")
    log("=" * 60)
    log("Starting policy conversion script")
    log("=" * 60)
    if not os.path.exists(CLEANED_RULES):
        if os.path.exists(STEP6_RULES):
            shutil.copy2(STEP6_RULES, CLEANED_RULES)
            log("Copied " + STEP6_RULES + " to " + CLEANED_RULES)
        else:
            log("ERROR: Neither " + CLEANED_RULES + " nor " + STEP6_RULES + " exist. Exiting.")
            log_fh.close()
            sys.exit(1)
    shutil.copy2(CLEANED_RULES, TEMP_RULES)
    log("Copied " + CLEANED_RULES + " to " + TEMP_RULES)
    with open(TEMP_RULES, "r") as f:
        all_lines = f.readlines()
    all_lines = [l.rstrip("\n\r") for l in all_lines if l.strip()]
    if not all_lines:
        log("Input file is empty. Exiting.")
        log_fh.close()
        sys.exit(0)
    all_lines = check_and_dedup_lines(all_lines)
    general = read_general()
    log("General config loaded: " + str(list(general.keys())))
    username = general.get("concerto-user", "")
    session, headers, base_url = get_session(general)
    policies, policy_order = group_config_by_policy(all_lines)
    log("Found " + str(len(policy_order)) + " policies to process")
    addr_groups = {}
    cust_svc_cache = {}
    custom_url_cache = {}
    has_ldap = "ldap-profile" in general and general["ldap-profile"]
    has_scim = "scim-profile" in general and general["scim-profile"]
    for policy_name in policy_order:
        log("-" * 60)
        log("Processing policy: " + policy_name)
        remainders = policies[policy_name]["remainders"]
        full_lines = policies[policy_name]["full_lines"]
        description = ""
        for rem in remainders:
            vals = extract_values_from_remainder(rem, "description")
            if vals is not None:
                description = vals[0].strip('"')
                break
        tags = []
        for rem in remainders:
            vals = extract_values_from_remainder(rem, "tag")
            if vals is not None:
                for v in vals:
                    v = v.strip('"')
                    if v not in tags:
                        tags.append(v)
        global policy_enabled
        policy_enabled = True
        for rem in remainders:
            if remainder_has_keyword(rem, "disabled"):
                vals = extract_values_from_remainder(rem, "disabled")
                if vals and vals[0].lower() == "yes":
                    policy_enabled = False
        zone_conv = load_conversion_file(ZONE_CONV)
        source_zones, dest_zones = process_zones(remainders, zone_conv)
        log("Source zones: " + str(source_zones))
        log("Dest zones: " + str(dest_zones))
        has_source_addr = False
        has_dest_addr = False
        for rem in remainders:
            sv = extract_values_from_remainder(rem, "source")
            if sv is not None and not (len(sv) == 1 and sv[0].lower() in ("any", "all")):
                has_source_addr = True
            dv = extract_values_from_remainder(rem, "destination")
            if dv is not None and not (len(dv) == 1 and dv[0].lower() in ("any", "all")):
                has_dest_addr = True
        source_addrs = []
        dest_addrs = []
        if has_source_addr or has_dest_addr:
            if not addr_groups:
                addr_groups = fetch_address_groups(session, headers, base_url, general)
            source_addrs, dest_addrs, addr_groups = process_addresses(
                remainders, full_lines, addr_groups, session, headers, base_url, general
            )
        log("Source addresses: " + str(len(source_addrs)))
        log("Dest addresses: " + str(len(dest_addrs)))
        all_caps_apps, mixed_apps = process_applications(remainders, full_lines)
        log("Applications all-caps: " + str(all_caps_apps))
        log("Applications mixed: " + str(mixed_apps))
        predef_svcs, custom_svcs, cust_svc_cache = process_services(
            remainders, full_lines, cust_svc_cache, session, headers, base_url, general
        )
        log("Predefined services: " + str(predef_svcs))
        log("Custom services: " + str(len(custom_svcs)))
        predef_url_cats, custom_url_cats, custom_url_cache = process_url_categories(
            remainders, full_lines, custom_url_cache, session, headers, base_url, general
        )
        log("Predefined URL categories: " + str(predef_url_cats))
        log("Custom URL categories: " + str(len(custom_url_cats)))
        set_value = process_security_profiles(remainders, full_lines, session, headers, base_url, general)
        log("Set value: " + str(set_value))
        user_section = None
        if has_scim:
            user_section = process_scim_source_user(remainders, full_lines, general, session, headers, base_url)
        elif has_ldap:
            user_section = process_ldap_source_user(remainders, full_lines, general, session, headers, base_url)
        if user_section:
            log("User section: " + str(list(user_section.keys())))
        else:
            log("No user section")
        match_value = {}
        if all_caps_apps or mixed_apps:
            app_entry = {}
            if all_caps_apps:
                app_entry["application"] = {"predefined": all_caps_apps}
            if mixed_apps:
                app_entry["applicationGroup"] = {"predefined": mixed_apps}
            match_value["application"] = app_entry
        if predef_url_cats or custom_url_cats:
            url_cat = {}
            if predef_url_cats:
                url_cat["predefined"] = predef_url_cats
            if custom_url_cats:
                url_cat["ecpUserDefinedCombo"] = custom_url_cats
            match_value["urlCategory"] = url_cat
        if user_section:
            match_value["user"] = user_section
        if source_zones or dest_zones:
            zone = {"enabled": True}
            if source_zones:
                zone["source"] = source_zones
            if dest_zones:
                zone["destination"] = dest_zones
            match_value["zone"] = zone
        if source_addrs or dest_addrs:
            address = {}
            if source_addrs:
                address["source"] = {
                    "addressGroupCombo": source_addrs,
                    "addressNegate": False
                }
            if dest_addrs:
                address["destination"] = {
                    "addressGroupCombo": dest_addrs,
                    "addressNegate": False
                }
            match_value["address"] = address
        if predef_svcs or custom_svcs:
            service = {"enabled": False}
            if predef_svcs:
                service["predefined"] = predef_svcs
            if custom_svcs:
                service["ecpUserDefinedCombo"] = custom_svcs
            match_value["service"] = service
        version_control = get_version_control(session, headers, base_url, general)
        policy_json = build_policy_json(
            policy_name, description, tags,
            match_value, set_value, version_control, username
        )
        temp_json_path = os.path.join(TEMP_DIR, "post-policy-base.json")
        with open(temp_json_path, "w") as f:
            json.dump(policy_json, f, indent=4)
        log("JSON written to " + temp_json_path)
        post_url = base_url + "/portalapi/v1/tenants/" + general["tenant-uuid"] + "/sase/real-time/internet-protection"
        log("POST " + post_url)
        try:
            resp = session.post(post_url, verify=False, headers=headers, json=policy_json)
            log("Response: " + str(resp.status_code))
            log("Response body: " + resp.text[:500])
            append_line(POST_RESULTS, policy_name + " >> " + str(resp.status_code))
            if resp.status_code != 201:
                safe_name = re.sub(r'[^\w\-. ]', '_', policy_name).strip()
                failed_json_path = os.path.join(FAILED_POLICY_JSON_DIR, safe_name + ".json")
                shutil.copy2(temp_json_path, failed_json_path)
                log("Saved failed policy JSON to " + failed_json_path)
                with open(FAILED_POST_RESPONSES, "a") as fail_fh:
                    fail_fh.write("Policy: " + policy_name + " | HTTP " + str(resp.status_code) + "\n")
                    fail_fh.write(resp.text + "\n")
                    fail_fh.write("\n\n\n")
        except Exception as e:
            log("ERROR posting policy: " + str(e))
            append_line(POST_RESULTS, policy_name + " >> ERROR: " + str(e))
        log("Policy " + policy_name + " processed")
    log("=" * 60)
    log("Script completed. Processed " + str(len(policy_order)) + " policies.")
    log("=" * 60)
    log_fh.close()

if __name__ == "__main__":
    main()