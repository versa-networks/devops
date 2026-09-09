#!/usr/bin/env python3
import ipaddress
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
SOURCE_FILE = os.path.join(MAIN_DIR, "source-pan-rules.txt")
CREATED_IP_OUT_PATH = os.path.join(MAIN_DIR, "created-ip-address-object.txt")

RULE_LINE_RE = re.compile(r'^set\s+\S+\s+(pre|post)-rulebase\s+security\s+rules\s+')
FIELD_RE = re.compile(r'\b(source|destination)\s+(\[([^\]]*)\]|(\S+))')
ADDR_DEF_RE = re.compile(r'^\s*set\s+shared\s+address\s+(?:"([^"]+)"|(\S+))\s')
ADDR_GRP_DEF_RE = re.compile(r'^\s*set\s+shared\s+address-group\s+(?:"([^"]+)"|(\S+))\s')

CREATED_HEADER = (
    "╔═══════════════════════════════════════════════════════════════════════════════════════╗\n"
    "║                          AUTO-CREATED IP ADDRESS OBJECTS                              ║\n"
    "╠═══════════════════════════════════════════════════════════════════════════════════════╣\n"
    "║  Versa does not allow a literal IP address inside a policy rule.                      ║\n"
    "║  The IP addresses below were found directly in the source/destination of a policy     ║\n"
    "║  rule. An address object was created for each one and appended to                     ║\n"
    "║  'source-pan-rules.txt'. The policy rule now references the object name.              ║\n"
    "║  These policies remain ENABLED. No action is required.                                ║\n"
    "╚═══════════════════════════════════════════════════════════════════════════════════════╝\n"
    "\n"
)


def unquote_token(tok):
    if len(tok) >= 2 and tok[0] == tok[-1] and tok[0] in ('"', "'"):
        return tok[1:-1]
    return tok


def classify_ip_token(tok):
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


def base_object_name(kind, value):
    if kind == "host":
        return "ip_" + value.replace(".", "_")
    addr_part, _, mask_part = value.partition("/")
    return "ip_sub_" + addr_part.replace(".", "_") + "_" + mask_part


def collect_existing_names(lines):
    names = set()
    for raw in lines:
        for pattern in (ADDR_DEF_RE, ADDR_GRP_DEF_RE):
            m = pattern.match(raw)
            if m:
                names.add(m.group(1) if m.group(1) is not None else m.group(2))
    return names


class IpObjectFactory:
    def __init__(self, taken_names):
        self.taken = set(taken_names)
        self.by_value = {}
        self.created = []
        self.refs = {}

    def get_or_create(self, kind, value, policy, keyword):
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
        self.refs.setdefault(name, set()).add(f"{policy} {keyword}")
        return name

    def _sorted_rows(self):
        rows = []
        for name, kind, value in self.created:
            addr_part = value.split("/")[0]
            mask = 32 if kind == "host" else int(value.split("/")[1])
            rows.append((int(ipaddress.IPv4Address(addr_part)), mask, name, kind, value))
        rows.sort()
        return rows

    def config_lines(self):
        out = []
        for _, _, name, kind, value in self._sorted_rows():
            netmask = f"{value}/32" if kind == "host" else value
            out.append(f"set shared address {name} ip-netmask {netmask}\n")
            out.append(f'set shared address {name} description "Created by PAN Conversion scripts"\n')
        return out

    def report_lines(self):
        out = []
        for _, _, name, kind, value in self._sorted_rows():
            netmask = f"{value}/32" if kind == "host" else value
            out.append(f"{name}  ->  {netmask}\n")
            for ref in sorted(self.refs.get(name, set())):
                out.append(f"        referenced by: security rules {ref}\n")
        return out


POLICY_NAME_RE = re.compile(r'security\s+rules\s+(?:"([^"]+)"|(\S+))')


def policy_name_of(line):
    m = POLICY_NAME_RE.search(line)
    if not m:
        return "unknown"
    return m.group(1) if m.group(1) is not None else m.group(2)


def split_tokens_respecting_quotes(s):
    out = []
    cur = ""
    quote = None
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


def main():
    with open(SOURCE_FILE, "r", encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()

    existing_names = collect_existing_names(lines)
    factory = IpObjectFactory(existing_names)

    modified_lines = []
    rewritten = 0

    for line in lines:
        stripped = line.rstrip("\n")
        if not RULE_LINE_RE.match(stripped):
            modified_lines.append(line)
            continue

        policy = policy_name_of(stripped)
        changed_flag = [False]

        def replacer(m):
            field = m.group(1)
            full_val = m.group(2).strip()
            if full_val.startswith("["):
                inner = m.group(3).strip() if m.group(3) else ""
                tokens = split_tokens_respecting_quotes(inner)
                bracketed = True
            else:
                single = m.group(4)
                if not single:
                    return m.group(0)
                tokens = [single]
                bracketed = False

            new_tokens = []
            for token in tokens:
                plain = unquote_token(token)
                if plain in existing_names:
                    new_tokens.append(token)
                    continue
                classified = classify_ip_token(token)
                if classified is None:
                    new_tokens.append(token)
                    continue
                kind, value = classified
                new_tokens.append(factory.get_or_create(kind, value, policy, field))
                changed_flag[0] = True

            if not changed_flag[0]:
                return m.group(0)
            if bracketed:
                return field + " [ " + " ".join(new_tokens) + " ]"
            return field + " " + new_tokens[0]

        new_line = FIELD_RE.sub(replacer, stripped)
        if changed_flag[0]:
            rewritten += 1
        modified_lines.append(new_line + "\n")

    address_lines = factory.config_lines()

    with open(SOURCE_FILE, "w", encoding="utf-8") as fh:
        fh.writelines(modified_lines)
        if address_lines:
            fh.write("\n")
            fh.writelines(address_lines)

    if factory.created:
        with open(CREATED_IP_OUT_PATH, "w", encoding="utf-8") as fh:
            fh.write(CREATED_HEADER)
            fh.writelines(factory.report_lines())

    print(f"Done. {len(factory.created)} address object(s) created, {rewritten} policy line(s) rewritten.")
    if factory.created:
        print(f"Report: {CREATED_IP_OUT_PATH}")


main()
