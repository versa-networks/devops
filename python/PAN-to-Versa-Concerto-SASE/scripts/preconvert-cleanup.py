import ipaddress
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Set, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
MAIN_DIR = SCRIPT_DIR.parent
FINAL_DATA_DIR = MAIN_DIR / "final-data"
LOG_DIR = MAIN_DIR / "log"

CLEANED_RULES_PATH = FINAL_DATA_DIR / "cleaned-pan-rules.txt"
ADDR_GRP_PATH = FINAL_DATA_DIR / "final-address-group.txt"
ADDR_PATH = FINAL_DATA_DIR / "final-address.txt"

UNRESOLVED_OUT_PATH = MAIN_DIR / "unresolved-objects-configuration.txt"
CREATED_IP_OUT_PATH = MAIN_DIR / "created-ip-address-object.txt"
LOG_PATH = LOG_DIR / "pre-convert-object-cleanup.log"

RE_ADDR_GRP = re.compile(r'^\s*set\s+shared\s+address-group\s+("([^"]+)"|(\S+))')
RE_ADDR = re.compile(r'^\s*set\s+shared\s+address\s+("([^"]+)"|(\S+))')

RE_POLICY = re.compile(r'\bsecurity\s+rules\s+("([^"]+)"|(\S+))')

RE_DISABLED = re.compile(r'\bdisabled\b\s+(\S+)')

RE_TAIL_SOURCE = re.compile(r'^source(\s+|$)')
RE_TAIL_DEST = re.compile(r'^destination(\s+|$)')

RE_TAIL_VALUE = re.compile(r'^(\s*)(source|destination)(\s+)(\[.*?\]|\S+)(.*)$', re.DOTALL)

def log(msg: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")

def load_object_names(path: Path, regex: re.Pattern) -> Set[str]:
    names: Set[str] = set()
    if not path.exists():
        log(f"ERROR: missing file: {path}")
        return names
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            m = regex.match(line)
            if m:
                nm = m.group(2) if m.group(2) is not None else m.group(3)
                if nm:
                    names.add(nm)
    return names

def extract_policy_name(line: str) -> Optional[str]:
    m = RE_POLICY.search(line)
    if not m:
        return None
    return m.group(2) if m.group(2) is not None else m.group(3)

def extract_policy_match(line: str) -> Optional[re.Match]:
    return RE_POLICY.search(line)

def get_immediate_keyword_after_policy(line: str, policy_m: re.Match) -> Optional[str]:
    tail = line[policy_m.end():].lstrip()
    if RE_TAIL_SOURCE.match(tail):
        return "source"
    if RE_TAIL_DEST.match(tail):
        return "destination"
    return None

def split_tokens_respecting_quotes(s: str) -> List[str]:
    out: List[str] = []
    cur = ""
    quote: Optional[str] = None
    for ch in s:
        if quote is not None:
            cur += ch
            if ch == quote:
                out.append(cur)
                cur = ""
                quote = None
            continue
        if ch in ('"', "'"):
            if cur.strip():
                out.append(cur.strip())
            cur = ch
            quote = ch
            continue
        if ch.isspace():
            if cur.strip():
                out.append(cur.strip())
            cur = ""
            continue
        cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out

def unquote_token(tok: str) -> str:
    if len(tok) >= 2 and tok[0] == tok[-1] and tok[0] in ('"', "'"):
        return tok[1:-1]
    return tok

def extract_targets_from_tail(tail_after_policy: str, keyword: str) -> Tuple[List[str], bool]:
    tail = tail_after_policy.lstrip()
    if not tail.startswith(keyword):
        return [], False
    tail = tail[len(keyword):].strip()
    if not tail:
        return [], False
    if tail.startswith('['):
        m = re.search(r'\[\s*(.*?)\s*\]', tail, re.DOTALL)
        if not m:
            return [], False
        content = m.group(1).strip()
        if not content:
            return [], False
        return split_tokens_respecting_quotes(content), True
    toks = split_tokens_respecting_quotes(tail)
    if not toks:
        return [], False
    return [toks[0]], False

def classify_ip_token(tok: str) -> Optional[Tuple[str, str]]:
    t = unquote_token(tok).strip()
    if not t or ":" in t:
        return None
    if "/" in t:
        addr_part, _, mask_part = t.partition("/")
        if not mask_part.isdigit():
            return None
        try:
            net = ipaddress.IPv4Network(t, strict=False)
        except ValueError:
            return None
        if net.prefixlen == 32:
            return "host", str(net.network_address)
        return "net", str(net)
    try:
        ip = ipaddress.IPv4Address(t)
    except ValueError:
        return None
    return "host", str(ip)

def base_object_name(kind: str, value: str) -> str:
    if kind == "host":
        return "ip_" + value.replace(".", "_")
    addr_part, _, mask_part = value.partition("/")
    return "ip_sub_" + addr_part.replace(".", "_") + "_" + mask_part

class IpObjectFactory:
    def __init__(self, taken_names: Set[str]):
        self.taken = set(taken_names)
        self.by_value: Dict[str, str] = {}
        self.created: List[Tuple[str, str, str]] = []
        self.refs: Dict[str, Set[str]] = {}

    def get_or_create(self, kind: str, value: str, policy: str, keyword: str) -> str:
        name = self.by_value.get(value)
        if name is None:
            name = base_object_name(kind, value)
            if name in self.taken:
                counter = 1
                while f"{name}_{counter}" in self.taken:
                    counter += 1
                name = f"{name}_{counter}"
            self.taken.add(name)
            self.by_value[value] = name
            self.created.append((name, kind, value))
            log(f"CREATED address object: {name} -> {value} (kind={kind})")
        self.refs.setdefault(name, set()).add(f"{policy} {keyword}")
        return name

    def config_lines(self) -> List[str]:
        rows = []
        for name, kind, value in self.created:
            addr_part = value.split("/")[0]
            sort_key = int(ipaddress.IPv4Address(addr_part))
            mask = 32 if kind == "host" else int(value.split("/")[1])
            rows.append((sort_key, mask, name, kind, value))
        rows.sort()
        out = []
        for _, _, name, kind, value in rows:
            netmask = f"{value}/32" if kind == "host" else value
            out.append(f"set shared address {name} ip-netmask {netmask}\n")
        return out

    def report_lines(self) -> List[str]:
        rows = []
        for name, kind, value in self.created:
            addr_part = value.split("/")[0]
            sort_key = int(ipaddress.IPv4Address(addr_part))
            mask = 32 if kind == "host" else int(value.split("/")[1])
            rows.append((sort_key, mask, name, kind, value))
        rows.sort()
        out = []
        for _, _, name, kind, value in rows:
            netmask = f"{value}/32" if kind == "host" else value
            out.append(f"{name}  ->  {netmask}\n")
            for ref in sorted(self.refs.get(name, set())):
                out.append(f"        referenced by: security rules {ref}\n")
        return out

def annotate_unresolved_in_line(line: str, unresolved_targets: Set[str]) -> str:
    tokens_sorted = sorted(unresolved_targets, key=len, reverse=True)
    out = line
    for tok in tokens_sorted:
        pattern = re.compile(rf'(?<!\S)({re.escape(tok)})(?!\S)')
        out = pattern.sub(r'\1 <<UNRESOLVED', out)
    return out

def rebuild_line_with_targets(line: str, policy_m: re.Match, final_targets: List[str],
                              bracketed: bool) -> Optional[str]:
    tail = line[policy_m.end():]
    m = RE_TAIL_VALUE.match(tail)
    if not m:
        return None
    if bracketed or len(final_targets) > 1:
        new_value = "[ " + " ".join(final_targets) + " ]"
    else:
        new_value = final_targets[0]
    new_tail = m.group(1) + m.group(2) + m.group(3) + new_value + m.group(5)
    new_line = line[:policy_m.end()] + new_tail
    if not new_line.endswith("\n"):
        new_line += "\n"
    return new_line

def set_policy_disabled_yes(
    lines: List[str],
    policy_indices: List[int],
    disabled_inserts: Dict[int, str],
) -> None:
    for idx in policy_indices:
        if re.search(r'\bdisabled\b', lines[idx]):
            old = lines[idx]
            lines[idx] = re.sub(r'(\bdisabled\b\s+)\S+', r'\1yes', lines[idx])
            if lines[idx] != old:
                log(f"Policy disabled set to yes (existing line): idx={idx}")
            return

    first_idx = min(policy_indices)
    first_line = lines[first_idx]

    pol_m = RE_POLICY.search(first_line)
    if not pol_m:
        log(f"WARNING: could not construct disabled line for idx={first_idx}, line={first_line!r}")
        return

    prefix = first_line[:pol_m.end()].rstrip()
    new_line = prefix + " disabled yes\n"
    disabled_inserts[first_idx] = new_line
    log(f"Policy disabled queued for insert after idx={first_idx}: {new_line.rstrip()}")

CREATED_HEADER = (
    "╔═══════════════════════════════════════════════════════════════════════════════════════╗\n"
    "║                          AUTO-CREATED IP ADDRESS OBJECTS                              ║\n"
    "╠═══════════════════════════════════════════════════════════════════════════════════════╣\n"
    "║  Versa Concerto does not allow a literal IP address inside a policy rule.              ║\n"
    "║  The IP addresses below were found directly in the source/destination of a policy     ║\n"
    "║  rule. An address object was created for each one and appended to                     ║\n"
    "║  'final-data/final-address.txt'. The policy rule now references the object name.      ║\n"
    "║  These policies remain ENABLED. No action is required.                                ║\n"
    "╚═══════════════════════════════════════════════════════════════════════════════════════╝\n"
    "\n"
)

UNRESOLVED_HEADER = (
    "╔═══════════════════════════════════════════════════════════════════════════════════════╗\n"
    "║                               !!  ATTENTION  !!                                       ║\n"
    "╠═══════════════════════════════════════════════════════════════════════════════════════╣\n"
    "║  These objects are being referred to, but were not found in the source configuration  ║\n"
    "║  file. The policy configuration has been transferred without the missing objects.     ║\n"
    "║  The policies affected are therefore intentionally disabled.                          ║\n"
    "║  Please remedy the situation and manually re-enable the policies.                     ║\n"
    "╚═══════════════════════════════════════════════════════════════════════════════════════╝\n"
    "\n"
)

def main() -> None:
    log("----- START pre-convert object cleanup (inline IP object creation + unresolved check) -----")

    if not CLEANED_RULES_PATH.exists():
        log(f"ERROR: missing cleaned rules file: {CLEANED_RULES_PATH}")
        print(f"ERROR: missing file: {CLEANED_RULES_PATH}", file=sys.stderr)
        sys.exit(1)

    addr_groups = load_object_names(ADDR_GRP_PATH, RE_ADDR_GRP)
    addrs = load_object_names(ADDR_PATH, RE_ADDR)

    log(f"Loaded address-groups: {len(addr_groups)} from {ADDR_GRP_PATH}")
    log(f"Loaded addresses:      {len(addrs)} from {ADDR_PATH}")

    factory = IpObjectFactory(addrs | addr_groups)

    with open(CLEANED_RULES_PATH, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    policy_map: Dict[str, List[int]] = {}
    for i, line in enumerate(lines):
        pol = extract_policy_name(line)
        if pol:
            policy_map.setdefault(pol, []).append(i)

    log(f"Detected policies: {len(policy_map)}")

    unresolved_lines_out: List[str] = []
    delete_indices: Set[int] = set()
    disabled_inserts: Dict[int, str] = {}
    rewritten_lines = 0

    for idx, line in enumerate(lines):
        policy_m = extract_policy_match(line)
        if not policy_m:
            continue

        pol = extract_policy_name(line)
        if not pol:
            continue

        keyword = get_immediate_keyword_after_policy(line, policy_m)
        if keyword not in ("source", "destination"):
            continue

        tail_after_policy = line[policy_m.end():]
        targets, bracketed = extract_targets_from_tail(tail_after_policy, keyword)
        if not targets:
            continue

        unresolved_targets: Set[str] = set()
        final_targets: List[str] = []
        created_any = False

        for t in targets:
            plain = unquote_token(t)
            if plain in addr_groups or plain in addrs:
                final_targets.append(t)
                continue
            classified = classify_ip_token(t)
            if classified is not None:
                kind, value = classified
                obj_name = factory.get_or_create(kind, value, pol, keyword)
                final_targets.append(obj_name)
                created_any = True
                continue
            unresolved_targets.add(t)

        if not created_any and not unresolved_targets:
            continue

        if unresolved_targets:
            annotated = annotate_unresolved_in_line(line, unresolved_targets)
            if not annotated.endswith("\n"):
                annotated += "\n"
            unresolved_lines_out.append(annotated)

        if final_targets:
            new_line = rebuild_line_with_targets(line, policy_m, final_targets, bracketed)
            if new_line is not None:
                lines[idx] = new_line
                rewritten_lines += 1
        elif unresolved_targets:
            delete_indices.add(idx)

        if unresolved_targets:
            set_policy_disabled_yes(lines, policy_map.get(pol, [idx]), disabled_inserts)
            log(f"UNRESOLVED found: policy='{pol}' idx={idx} keyword={keyword} "
                f"targets={sorted(list(unresolved_targets))} kept={final_targets}")
        else:
            log(f"INLINE IP replaced: policy='{pol}' idx={idx} keyword={keyword} kept={final_targets}")

    created_config = factory.config_lines()
    if created_config:
        with open(ADDR_PATH, "a", encoding="utf-8") as f:
            f.writelines(created_config)
        with open(CREATED_IP_OUT_PATH, "w", encoding="utf-8") as f:
            f.write(CREATED_HEADER)
            f.writelines(factory.report_lines())
        log(f"Appended {len(created_config)} address objects to {ADDR_PATH}")
        log(f"Wrote report: {CREATED_IP_OUT_PATH}")
    else:
        log("No inline IP address objects were created.")

    if unresolved_lines_out:
        file_is_new = not UNRESOLVED_OUT_PATH.exists() or UNRESOLVED_OUT_PATH.stat().st_size == 0
        with open(UNRESOLVED_OUT_PATH, "a", encoding="utf-8") as f:
            if file_is_new:
                f.write(UNRESOLVED_HEADER)
            f.write("".join(unresolved_lines_out))
        log(f"Wrote {len(unresolved_lines_out)} unresolved lines to {UNRESOLVED_OUT_PATH}")
    else:
        log("No unresolved lines found.")

    if rewritten_lines or delete_indices or disabled_inserts:
        new_lines: List[str] = []
        for i, ln in enumerate(lines):
            if i not in delete_indices:
                new_lines.append(ln)
            if i in disabled_inserts:
                new_lines.append(disabled_inserts[i])
        with open(CLEANED_RULES_PATH, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        log(f"Wrote updated cleaned-pan-rules.txt (rewritten={rewritten_lines}, "
            f"deleted={len(delete_indices)}, inserted_disabled={len(disabled_inserts)})")
    else:
        log("No changes to cleaned-pan-rules.txt")

    log("----- END pre-convert object cleanup -----")
    print("Done.")
    print(f"Updated: {CLEANED_RULES_PATH}")
    print(f"Created IP address objects: {len(created_config)}")
    if created_config:
        print(f"Created objects report: {CREATED_IP_OUT_PATH}")
    print(f"Unresolved output: {UNRESOLVED_OUT_PATH}")
    print(f"Log: {LOG_PATH}")

if __name__ == "__main__":
    main()
