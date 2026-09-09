import os
import sys
import tarfile
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
LOG_DIR = os.path.join(MAIN_DIR, "log")

SET_SOURCE_PATH = os.path.join(MAIN_DIR, "source-pan-rules.txt")
LOG_PATH = os.path.join(LOG_DIR, "convert-xml-to-set.log")

XML_CANDIDATES = [
    os.path.join(MAIN_DIR, "sp-config.xml"),
    os.path.join(MAIN_DIR, "sp", "vsys1", "sp-config.xml"),
    os.path.join(MAIN_DIR, "sp", "shared", "sp-config.xml"),
]

RULE_LIST_FIELDS = ["from", "to", "source", "destination", "source-user",
                    "application", "service", "category", "tag", "source-hip", "destination-hip"]
RULE_SCALAR_FIELDS = ["action", "log-setting", "log-start", "log-end",
                      "negate-source", "negate-destination", "disabled",
                      "rule-type", "icmp-unreachable", "schedule"]


def log(msg: str) -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = "[" + ts + "] " + msg
    print(line)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def quote(value: str) -> str:
    if value is None:
        return ""
    if value == "" or " " in value or "\t" in value:
        return '"' + value + '"'
    return value


def members_of(element: ET.Element) -> List[str]:
    return [m.text for m in element.findall("member") if m.text is not None]


def emit_value_list(values: List[str]) -> str:
    if not values:
        return ""
    if len(values) == 1:
        return quote(values[0])
    return "[ " + " ".join(quote(v) for v in values) + " ]"


def find_blocks(root: ET.Element, tag: str) -> List[ET.Element]:
    blocks = []
    for el in root.iter():
        for child in el:
            if child.tag == tag:
                blocks.append(child)
    return blocks


def collect_entries(root: ET.Element, container_tag: str) -> "List[ET.Element]":
    seen = set()
    entries = []
    for block in find_blocks(root, container_tag):
        for entry in block.findall("entry"):
            name = entry.get("name")
            if name is None or name in seen:
                continue
            seen.add(name)
            entries.append(entry)
    return entries


def convert_address(root: ET.Element, out: List[str]) -> int:
    count = 0
    for e in collect_entries(root, "address"):
        name = e.get("name")
        prefix = "set shared address " + quote(name)
        wrote = False
        for kind in ["ip-netmask", "ip-range", "ip-wildcard", "fqdn"]:
            v = e.findtext(kind)
            if v:
                out.append(prefix + " " + kind + " " + v)
                wrote = True
        desc = e.findtext("description")
        if desc:
            out.append(prefix + ' description "' + desc + '"')
        tag_el = e.find("tag")
        if tag_el is not None:
            tv = members_of(tag_el)
            if tv:
                out.append(prefix + " tag " + emit_value_list(tv))
        if wrote:
            count += 1
    return count


def convert_address_group(root: ET.Element, out: List[str]) -> int:
    count = 0
    for e in collect_entries(root, "address-group"):
        name = e.get("name")
        prefix = "set shared address-group " + quote(name)
        static = e.find("static")
        if static is not None:
            mem = members_of(static)
            if mem:
                out.append(prefix + " static " + emit_value_list(mem))
                count += 1
        dynamic = e.find("dynamic")
        if dynamic is not None:
            flt = dynamic.findtext("filter")
            if flt:
                out.append(prefix + ' dynamic filter "' + flt + '"')
                count += 1
        desc = e.findtext("description")
        if desc:
            out.append(prefix + ' description "' + desc + '"')
    return count


def convert_service(root: ET.Element, out: List[str]) -> int:
    count = 0
    for e in collect_entries(root, "service"):
        name = e.get("name")
        prefix = "set shared service " + quote(name)
        proto = e.find("protocol")
        wrote = False
        if proto is not None:
            for p in ["tcp", "udp"]:
                pe = proto.find(p)
                if pe is not None:
                    port = pe.findtext("port")
                    sport = pe.findtext("source-port")
                    if port:
                        out.append(prefix + " protocol " + p + " port " + port)
                        wrote = True
                    if sport:
                        out.append(prefix + " protocol " + p + " source-port " + sport)
                        wrote = True
        desc = e.findtext("description")
        if desc:
            out.append(prefix + ' description "' + desc + '"')
        tag_el = e.find("tag")
        if tag_el is not None:
            tv = members_of(tag_el)
            if tv:
                out.append(prefix + " tag " + emit_value_list(tv))
        if wrote:
            count += 1
    return count


def convert_service_group(root: ET.Element, out: List[str]) -> int:
    count = 0
    for e in collect_entries(root, "service-group"):
        name = e.get("name")
        prefix = "set shared service-group " + quote(name)
        members_el = e.find("members")
        if members_el is not None:
            mem = members_of(members_el)
            if mem:
                out.append(prefix + " members " + emit_value_list(mem))
                count += 1
        tag_el = e.find("tag")
        if tag_el is not None:
            tv = members_of(tag_el)
            if tv:
                out.append(prefix + " tag " + emit_value_list(tv))
    return count


def convert_application(root: ET.Element, out: List[str]) -> int:
    count = 0
    for e in collect_entries(root, "application"):
        name = e.get("name")
        prefix = "set shared application " + quote(name)
        default = e.find("default")
        if default is not None:
            port = default.find("port")
            if port is not None:
                mem = members_of(port)
                if mem:
                    out.append(prefix + " default port " + emit_value_list(mem))
            ipproto = default.findtext("ident-by-ip-protocol")
            if ipproto:
                out.append(prefix + " default ident-by-ip-protocol " + ipproto)
        for kind in ["category", "subcategory", "technology", "risk", "parent-app"]:
            v = e.findtext(kind)
            if v:
                out.append(prefix + " " + kind + " " + v)
        desc = e.findtext("description")
        if desc:
            out.append(prefix + ' description "' + desc + '"')
        tag_el = e.find("tag")
        if tag_el is not None:
            tv = members_of(tag_el)
            if tv:
                out.append(prefix + " tag " + emit_value_list(tv))
        count += 1
    return count


def convert_application_group(root: ET.Element, out: List[str]) -> int:
    count = 0
    for e in collect_entries(root, "application-group"):
        name = e.get("name")
        members_el = e.find("members")
        mem = members_of(members_el) if members_el is not None else members_of(e)
        if mem:
            out.append("set shared application-group " + quote(name) +
                       " members " + emit_value_list(mem))
            count += 1
    return count


def convert_application_filter(root: ET.Element, out: List[str]) -> int:
    count = 0
    for e in collect_entries(root, "application-filter"):
        name = e.get("name")
        prefix = "set shared application-filter " + quote(name)
        for kind in ["category", "subcategory", "technology", "risk"]:
            sub = e.find(kind)
            if sub is not None:
                mem = members_of(sub)
                if mem:
                    out.append(prefix + " " + kind + " " + emit_value_list(mem))
        count += 1
    return count


def convert_custom_url_category(root: ET.Element, out: List[str]) -> int:
    count = 0
    for e in collect_entries(root, "custom-url-category"):
        name = e.get("name")
        prefix = "set shared profiles custom-url-category " + quote(name)
        lst = e.find("list")
        if lst is not None:
            mem = members_of(lst)
            if mem:
                out.append(prefix + " list " + emit_value_list(mem))
        ctype = e.findtext("type")
        if ctype:
            out.append(prefix + " type " + quote(ctype))
        count += 1
    return count


def convert_tag(root: ET.Element, out: List[str]) -> int:
    count = 0
    for e in collect_entries(root, "tag"):
        name = e.get("name")
        prefix = "set shared tag " + quote(name)
        color = e.findtext("color")
        if color:
            out.append(prefix + " color " + color)
        comments = e.findtext("comments")
        if comments:
            out.append(prefix + ' comments "' + comments + '"')
        if not color and not comments:
            out.append(prefix)
        count += 1
    return count


def emit_profile_setting(prefix: str, ps: ET.Element, out: List[str]) -> None:
    group = ps.find("group")
    if group is not None:
        mem = members_of(group)
        if mem:
            out.append(prefix + " profile-setting group " + emit_value_list(mem))
            return
    profiles = ps.find("profiles")
    if profiles is not None:
        for prof in profiles:
            mem = members_of(prof)
            if mem:
                out.append(prefix + " profile-setting profiles " + prof.tag + " " + emit_value_list(mem))


def convert_rule_entry(rulebase: str, entry: ET.Element, out: List[str]) -> None:
    name = entry.get("name")
    prefix = "set shared " + rulebase + " security rules " + quote(name)
    for field in RULE_LIST_FIELDS:
        el = entry.find(field)
        if el is not None:
            mem = members_of(el)
            if mem:
                out.append(prefix + " " + field + " " + emit_value_list(mem))
    for field in RULE_SCALAR_FIELDS:
        v = entry.findtext(field)
        if v is not None and v != "":
            out.append(prefix + " " + field + " " + quote(v))
    desc = entry.findtext("description")
    if desc:
        out.append(prefix + ' description "' + desc + '"')
    option = entry.find("option")
    if option is not None:
        for opt in option:
            if opt.text is not None and opt.text != "":
                out.append(prefix + " option " + opt.tag + " " + quote(opt.text))
    ps = entry.find("profile-setting")
    if ps is not None:
        emit_profile_setting(prefix, ps, out)


def convert_rulebase(root: ET.Element, rb_tag: str, out: List[str]) -> int:
    count = 0
    for el in root.iter():
        if el.tag != rb_tag:
            continue
        security = el.find("security")
        if security is None:
            continue
        rules = security.find("rules")
        if rules is None:
            continue
        for entry in rules.findall("entry"):
            convert_rule_entry(rb_tag, entry, out)
            count += 1
    return count


def find_source_xml() -> Optional[str]:
    for cand in XML_CANDIDATES:
        if os.path.isfile(cand):
            return cand
    for fname in os.listdir(MAIN_DIR):
        if fname.endswith(".tgz") and "device_state" in fname:
            return os.path.join(MAIN_DIR, fname)
    return None


def load_xml_text(path: str) -> Optional[str]:
    if path.endswith(".tgz"):
        try:
            with tarfile.open(path, "r:gz") as tar:
                wanted = None
                for member in tar.getmembers():
                    if member.name.endswith("sp/vsys1/sp-config.xml"):
                        wanted = member
                        break
                if wanted is None:
                    for member in tar.getmembers():
                        if member.name.endswith("sp-config.xml"):
                            wanted = member
                            break
                if wanted is None:
                    log("ERROR: no sp-config.xml found inside archive: " + path)
                    return None
                extracted = tar.extractfile(wanted)
                if extracted is None:
                    return None
                return extracted.read().decode("utf-8", errors="replace")
        except Exception as exc:
            log("ERROR: failed to read archive " + path + " : " + str(exc))
            return None
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def main() -> int:
    os.makedirs(LOG_DIR, exist_ok=True)
    log("=" * 70)
    log("convert-xml-to-set START")
    log("MAIN DIR : " + MAIN_DIR)

    if os.path.isfile(SET_SOURCE_PATH) and os.path.getsize(SET_SOURCE_PATH) > 0:
        log("source-pan-rules.txt already present and non-empty; using set-command source as-is.")
        return 0
    if os.path.isfile(SET_SOURCE_PATH):
        log("source-pan-rules.txt exists but is EMPTY; will try to regenerate from XML.")

    log("Searching for an XML source. Locations checked:")
    for cand in XML_CANDIDATES:
        log("  - " + cand + ("  [FOUND]" if os.path.isfile(cand) else ""))
    log("  - " + MAIN_DIR + os.sep + "*device_state*.tgz")

    xml_path = find_source_xml()
    if xml_path is None:
        log("No XML source found in any of the above locations.")
        log("Provide source-pan-rules.txt (set format) OR place sp-config.xml / device_state_*.tgz "
            "in the working directory, then rerun.")
        return 1

    log("Detected XML source: " + xml_path)
    xml_text = load_xml_text(xml_path)
    if not xml_text:
        log("ERROR: could not load XML content.")
        return 1

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        log("ERROR: XML parse failed: " + str(exc))
        return 1

    out: List[str] = []
    counts: Dict[str, int] = {}
    counts["tag"] = convert_tag(root, out)
    counts["address"] = convert_address(root, out)
    counts["address-group"] = convert_address_group(root, out)
    counts["service"] = convert_service(root, out)
    counts["service-group"] = convert_service_group(root, out)
    counts["application"] = convert_application(root, out)
    counts["application-group"] = convert_application_group(root, out)
    counts["application-filter"] = convert_application_filter(root, out)
    counts["custom-url-category"] = convert_custom_url_category(root, out)
    counts["pre-rulebase rules"] = convert_rulebase(root, "pre-rulebase", out)
    counts["post-rulebase rules"] = convert_rulebase(root, "post-rulebase", out)

    total_objects = sum(counts.values())
    if total_objects == 0 or len(out) == 0:
        log("ERROR: XML parsed but produced 0 objects and 0 rules.")
        log("       The XML at '" + xml_path + "' may have an unexpected structure "
            "(e.g. a running-config.xml rather than a device-state sp-config.xml).")
        log("       NOT writing an empty source-pan-rules.txt. Pipeline halted so this is visible.")
        return 1

    with open(SET_SOURCE_PATH, "w", encoding="utf-8") as f:
        for line in out:
            f.write(line + "\n")

    log("Wrote set-format source: " + SET_SOURCE_PATH)
    for k in ["tag", "address", "address-group", "service", "service-group",
              "application", "application-group", "application-filter",
              "custom-url-category", "pre-rulebase rules", "post-rulebase rules"]:
        log("  " + k + ": " + str(counts.get(k, 0)))
    log("Total lines written: " + str(len(out)))
    log("convert-xml-to-set END (SUCCESS)")
    log("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
