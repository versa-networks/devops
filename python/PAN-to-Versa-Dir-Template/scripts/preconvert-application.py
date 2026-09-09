import os
import re
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
FINAL_DATA_DIR = os.path.join(MAIN_DIR, "final-data")
LOG_DIR = os.path.join(MAIN_DIR, "log")

CLEANED_RULES_PATH = os.path.join(FINAL_DATA_DIR, "cleaned-pan-rules.txt")
FINAL_CUSTOM_APP_PATH = os.path.join(FINAL_DATA_DIR, "final-custom-application.txt")
FINAL_APP_GROUP_PATH = os.path.join(FINAL_DATA_DIR, "final-application-group.txt")
UNRESOLVED_APP_PATH = os.path.join(MAIN_DIR, "unresolved-application-configuration.txt")
PREDEF_APP_CONV_PATH = os.path.join(MAIN_DIR, "predef-application-conversion.txt")
PAN_TO_VERSA_APP_CANDIDATES = [
    os.path.join(MAIN_DIR, "miscellaneous", "PAN-to-Versa-applications.txt"),
    os.path.join(MAIN_DIR, "miscellaneous", "PAN-to-Versa-application.txt"),
]
UNMAPPED_APP_PATH = os.path.join(MAIN_DIR, "unmapped-application.txt")
LOG_PATH = os.path.join(LOG_DIR, "preconvert-application.log")

RE_APP_GROUP = re.compile(r'^\s*set\s+shared\s+application-group\s+("([^"]+)"|(\S+))\s+members\s+(.*)$')
RE_APP_DEF = re.compile(r'^\s*set\s+shared\s+application\s+("([^"]+)"|(\S+))\s')
RE_POLICY = re.compile(r'security\s+rules\s+("([^"]+)"|(\S+))')


def log(msg: str) -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = "[" + ts + "] " + msg
    print(line)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


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


def quote_if_needed(name: str) -> str:
    if name and (" " in name or "\t" in name):
        return '"' + name + '"'
    return name


def parse_group_definitions(lines: List[str]) -> Dict[str, List[str]]:
    groups: Dict[str, List[str]] = {}
    for line in lines:
        m = RE_APP_GROUP.match(line)
        if not m:
            continue
        name = m.group(2) if m.group(2) is not None else m.group(3)
        members = tokenize_value_list(m.group(4))
        groups[name] = members
    return groups


def parse_custom_app_names(lines: List[str]) -> Set[str]:
    names: Set[str] = set()
    for line in lines:
        m = RE_APP_DEF.match(line)
        if m:
            nm = m.group(2) if m.group(2) is not None else m.group(3)
            if nm:
                names.add(nm)
    return names


def flatten_group(name: str, groups: Dict[str, List[str]],
                  cache: Dict[str, List[str]], stack: Optional[Set[str]] = None) -> List[str]:
    if name in cache:
        return cache[name]
    if stack is None:
        stack = set()
    if name in stack:
        log("WARNING: cycle detected while flattening application-group: " + name)
        return []
    stack = set(stack)
    stack.add(name)
    result: List[str] = []
    seen: Set[str] = set()
    for member in groups.get(name, []):
        if member in groups:
            for leaf in flatten_group(member, groups, cache, stack):
                if leaf not in seen:
                    seen.add(leaf)
                    result.append(leaf)
        else:
            if member not in seen:
                seen.add(member)
                result.append(member)
    cache[name] = result
    return result


def split_policy_and_field(line: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    m = RE_POLICY.search(line)
    if not m:
        return None, None, None
    prefix = line[:m.end()]
    rest = line[m.end():].strip()
    if not rest:
        return prefix, None, None
    parts = rest.split(None, 1)
    keyword = parts[0]
    value = parts[1] if len(parts) > 1 else ""
    return prefix, keyword, value


def rewrite_application_line(line: str, groups: Dict[str, List[str]],
                             cache: Dict[str, List[str]],
                             unresolved: List[str]) -> Tuple[str, bool]:
    prefix, keyword, value = split_policy_and_field(line)
    if prefix is None or keyword != "application":
        return line, False
    tokens = tokenize_value_list(value)
    if not tokens:
        return line, False
    if len(tokens) == 1 and tokens[0].lower() in ("any", "all"):
        return line, False

    expanded: List[str] = []
    seen: Set[str] = set()
    changed = False
    for tok in tokens:
        if tok in groups:
            changed = True
            for leaf in flatten_group(tok, groups, cache):
                if leaf not in seen:
                    seen.add(leaf)
                    expanded.append(leaf)
        else:
            if tok not in seen:
                seen.add(tok)
                expanded.append(tok)

    if not changed:
        return line, False

    quoted = [quote_if_needed(t) for t in expanded]
    if len(quoted) == 1:
        new_value = quoted[0]
    else:
        new_value = "[ " + " ".join(quoted) + " ]"
    new_line = prefix + " application " + new_value
    return new_line, True


def read_arrow_file(path: str) -> Tuple[List[str], Dict[str, str]]:
    order: List[str] = []
    values: Dict[str, str] = {}
    if not os.path.isfile(path):
        return order, values
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if not line.strip() or ">>" not in line:
                continue
            key, _, val = line.partition(">>")
            key = key.strip()
            if not key:
                continue
            if key not in values:
                order.append(key)
            values[key] = val.strip()
    return order, values


def write_arrow_file(path: str, order: List[str], values: Dict[str, str]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for key in order:
            f.write(key + " >> " + values.get(key, "") + "\n")


def sync_predef_application_conversion(kept_lines: List[str], custom_app_names: Set[str],
                                       group_names: Set[str]) -> None:
    order, values = read_arrow_file(PREDEF_APP_CONV_PATH)

    removed = 0
    for key in list(order):
        if key in custom_app_names:
            order.remove(key)
            values.pop(key, None)
            removed += 1
            log("Removed custom application from predef-application-conversion.txt: " + key)
        elif key in group_names:
            order.remove(key)
            values.pop(key, None)
            removed += 1
            log("Removed flattened application-group from predef-application-conversion.txt: " + key)

    added = 0
    for line in kept_lines:
        prefix, keyword, value = split_policy_and_field(line)
        if prefix is None or keyword != "application":
            continue
        for tok in tokenize_value_list(value):
            if not tok or tok.lower() in ("any", "all"):
                continue
            if tok in custom_app_names:
                continue
            if tok in values:
                continue
            order.append(tok)
            values[tok] = ""
            added += 1
            log("Added flattened application to predef-application-conversion.txt: " + tok)

    mapped = 0
    if added or removed:
        map_path = next((p for p in PAN_TO_VERSA_APP_CANDIDATES if os.path.isfile(p)), "")
        if map_path:
            _, pan2versa = read_arrow_file(map_path)
            for key in order:
                if values.get(key):
                    continue
                versa = pan2versa.get(key, "").strip()
                if versa:
                    values[key] = versa
                    mapped += 1
                    log("Auto-mapped application: " + key + " >> " + versa)
        else:
            log("WARNING: PAN-to-Versa application map not found; skipping auto-mapping.")

    if added or removed or mapped:
        write_arrow_file(PREDEF_APP_CONV_PATH, order, values)
        log("Updated " + PREDEF_APP_CONV_PATH +
            " (added=" + str(added) + ", removed_custom=" + str(removed) +
            ", auto_mapped=" + str(mapped) + ")")

    blanks = [k for k in order if not values.get(k)]
    if blanks:
        with open(UNMAPPED_APP_PATH, "w", encoding="utf-8") as f:
            f.write("*" * 119 + "\n")
            f.write("These PAN predefined applications have no Versa equivalent in "
                    "'predef-application-conversion.txt'.\n")
            f.write("Fill in the blank for each one in that file, otherwise the PAN application name "
                    "is sent to Versa as-is and the policy will likely FAIL.\n")
            f.write("*" * 119 + "\n\n")
            for k in blanks:
                f.write(k + " >>\n")
        log("Wrote " + str(len(blanks)) + " unmapped application name(s) to: " + UNMAPPED_APP_PATH)
    elif os.path.isfile(UNMAPPED_APP_PATH):
        os.remove(UNMAPPED_APP_PATH)


def main() -> int:
    os.makedirs(FINAL_DATA_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    log("=" * 70)
    log("preconvert-application START")
    log("MAIN DIR : " + MAIN_DIR)

    if not os.path.isfile(CLEANED_RULES_PATH):
        log("ERROR: rules file not found: " + CLEANED_RULES_PATH)
        return 2

    with open(CLEANED_RULES_PATH, "r", encoding="utf-8", errors="replace") as f:
        lines = [ln.rstrip("\n") for ln in f]

    groups = parse_group_definitions(lines)
    custom_app_names = parse_custom_app_names(lines)
    log("Found " + str(len(groups)) + " application-group definition(s).")
    log("Found " + str(len(custom_app_names)) + " custom-application definition(s).")

    cache: Dict[str, List[str]] = {}

    custom_def_lines: List[str] = []
    group_def_lines: List[str] = []
    kept_lines: List[str] = []
    unresolved: List[str] = []

    flattened_count = 0
    for line in lines:
        if RE_APP_GROUP.match(line):
            group_def_lines.append(line)
            continue
        if RE_APP_DEF.match(line):
            custom_def_lines.append(line)
            continue

        new_line, changed = rewrite_application_line(line, groups, cache, unresolved)
        if changed:
            flattened_count += 1
            log("FLATTENED: " + line)
            log("      ->   " + new_line)
        kept_lines.append(new_line)

    with open(FINAL_CUSTOM_APP_PATH, "w", encoding="utf-8") as f:
        for ln in custom_def_lines:
            f.write(ln + "\n")
    log("Wrote " + str(len(custom_def_lines)) + " custom-application line(s) to: " + FINAL_CUSTOM_APP_PATH)

    with open(FINAL_APP_GROUP_PATH, "w", encoding="utf-8") as f:
        for ln in group_def_lines:
            f.write(ln + "\n")
    log("Wrote " + str(len(group_def_lines)) + " application-group line(s) to: " + FINAL_APP_GROUP_PATH)

    backup = CLEANED_RULES_PATH + ".bak-preconvert-application"
    shutil.copy2(CLEANED_RULES_PATH, backup)
    log("Backed up original rules to: " + backup)

    with open(CLEANED_RULES_PATH, "w", encoding="utf-8") as f:
        for ln in kept_lines:
            f.write(ln + "\n")
    log("Rewrote rules file. Flattened " + str(flattened_count) + " policy application line(s).")
    log("Removed " + str(len(custom_def_lines) + len(group_def_lines)) +
        " application/application-group definition line(s) from rules.")

    sync_predef_application_conversion(kept_lines, custom_app_names, set(groups.keys()))

    log("preconvert-application END (SUCCESS)")
    log("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
