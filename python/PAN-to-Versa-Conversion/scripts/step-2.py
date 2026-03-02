#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from __future__ import annotations

import os
import re
import sys
import shutil
import threading
import time
import unicodedata
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set

class TeeIO:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, s: str) -> int:
        n = 0
        for st in self.streams:
            try:
                n = st.write(s)
                st.flush()
            except Exception:
                pass
        return n

    def flush(self) -> None:
        for st in self.streams:
            try:
                st.flush()
            except Exception:
                pass

def resolve_main_dir(cwd: str) -> str:
    base = os.path.basename(os.path.abspath(cwd)).lower()
    if base == "scripts":
        return os.path.abspath(os.path.join(cwd, ".."))
    return os.path.abspath(cwd)

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def copy_file(src: str, dst: str) -> None:
    ensure_dir(os.path.dirname(dst))
    shutil.copy2(src, dst)

def file_exists_and_nonempty(path: str) -> bool:
    return os.path.isfile(path) and os.path.getsize(path) > 0

def input_with_timeout(prompt: str, timeout_sec: int) -> Optional[str]:
    # No threads: avoids interpreter shutdown crashes when stdin is used from daemon threads.
    try:
        import select  # POSIX
    except Exception:
        select = None

    try:
        sys.stdout.write(prompt)
        sys.stdout.flush()
    except Exception:
        pass

    if select is None:
        # Fallback: no timeout support without select; proceed as if no input was provided.
        time.sleep(timeout_sec)
        return None

    try:
        rlist, _, _ = select.select([sys.stdin], [], [], timeout_sec)
    except Exception:
        time.sleep(timeout_sec)
        return None

    if not rlist:
        return None

    try:
        s = sys.stdin.readline()
    except Exception:
        return None

    if s is None:
        return None
    return s.rstrip("")
def is_visible_char(ch: str) -> bool:
    if ch in ("\u200b", "\u200c", "\u200d", "\ufeff"):
        return False
    cat = unicodedata.category(ch)
    if cat and cat[0] == "C":
        return False
    return True

def sanitize_line(line: str) -> str:
    line = line.replace("\r", "")
    line = line.replace("\t", " ")
    out = []
    for ch in line:
        if is_visible_char(ch):
            out.append(ch)
    return "".join(out).rstrip()

def read_text_file_normalized(path: str) -> List[str]:
    with open(path, "rb") as f:
        raw = f.read()
    txt = raw.decode("utf-8", errors="replace")
    txt = txt.replace("\r\n", "\n").replace("\r", "")
    return txt.split("\n")

def write_lines(path: str, lines: List[str]) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for ln in lines:
            f.write(ln + "\n")

def append_lines(path: str, lines: List[str]) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        for ln in lines:
            f.write(ln + "\n")

ADDR_RE = re.compile(r'^\s*set\s+shared\s+address\s+(?:"([^"]+)"|(\S+))\s*(.*)$')
GRP_RE  = re.compile(r'^\s*set\s+shared\s+address-group\s+(?:"([^"]+)"|(\S+))\s*(.*)$')

def parse_object_line(line: str, kind: str) -> Optional[Tuple[str, str, str, bool]]:

    if kind == "address":
        m = ADDR_RE.match(line)
        if not m:
            return None
        was_quoted = m.group(1) is not None
        name = m.group(1) if was_quoted else m.group(2)
        rest = (m.group(3) or "").strip()
        return ("set shared address", name, rest, was_quoted)
    else:
        m = GRP_RE.match(line)
        if not m:
            return None
        was_quoted = m.group(1) is not None
        name = m.group(1) if was_quoted else m.group(2)
        rest = (m.group(3) or "").strip()
        return ("set shared address-group", name, rest, was_quoted)

def render_name_token(raw_name: str, was_quoted: bool) -> str:
    return f'"{raw_name}"' if was_quoted else raw_name

ALLOWED_NAME_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
ALLOWED_FQDN_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")

def collapse_underscores_keep_edges(s: str) -> str:

    s = re.sub(r"_+", "_", s)
    return s if s else "_"

def sanitize_token_to_allowed(token: str, allowed: set) -> str:

    token = token.replace('"', "").replace("'", "")
    out = []
    for ch in token:
        out.append(ch if ch in allowed else "_")
    return collapse_underscores_keep_edges("".join(out))

def sanitize_object_name(raw_name: str) -> str:

    raw_name = re.sub(r"\s+", "_", raw_name.strip())
    return sanitize_token_to_allowed(raw_name, ALLOWED_NAME_CHARS)

class TruncAllocator:
    def __init__(self, max_len: int):
        self.max_len = max_len
        self.used: Set[str] = set()
        self.counters: Dict[str, int] = {}

    def _truncate_with_suffix(self, base: str, counter: int) -> str:
        suffix = f"_{counter}"
        keep = self.max_len - len(suffix)
        if keep < 1:
            return suffix[-self.max_len:]
        return base[:keep] + suffix

    def allocate(self, base: str) -> str:

        if len(base) <= self.max_len:
            self.used.add(base)
            return base

        n = self.counters.get(base, 1)
        while True:
            cand = self._truncate_with_suffix(base, n)
            if cand not in self.used:
                self.used.add(cand)
                self.counters[base] = n + 1
                return cand
            n += 1

_IPV4_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")
_IPV4_MASK_RE = re.compile(r"^(\d{1,3}(?:\.\d{1,3}){3})/(\d{1,2})$")

def is_valid_ipv4(ip: str) -> bool:
    if not _IPV4_RE.match(ip):
        return False
    parts = ip.split(".")
    for p in parts:
        try:
            v = int(p)
        except ValueError:
            return False
        if v < 0 or v > 255:
            return False
    return True

def is_valid_ipv4_or_mask(token: str) -> bool:
    if is_valid_ipv4(token):
        return True
    m = _IPV4_MASK_RE.match(token)
    if not m:
        return False
    ip = m.group(1)
    ms = m.group(2)
    if not is_valid_ipv4(ip):
        return False
    try:
        mv = int(ms)
    except ValueError:
        return False
    return 0 <= mv <= 32

def ipv4_to_int(ip: str) -> int:
    a, b, c, d = [int(x) for x in ip.split(".")]
    return (a << 24) | (b << 16) | (c << 8) | d

def is_valid_ip_range(token: str) -> bool:
    if "-" not in token:
        return False
    a, b = token.split("-", 1)
    a = a.strip()
    b = b.strip()
    if not (is_valid_ipv4(a) and is_valid_ipv4(b)):
        return False
    return ipv4_to_int(a) <= ipv4_to_int(b)

def is_valid_fqdn_token(token: str) -> bool:
    if token == "":
        return False
    for ch in token:
        if ch not in ALLOWED_FQDN_CHARS:
            return False
    if "." not in token:
        return False
    if token.startswith(".") or token.endswith("."):
        return False
    labels = token.split(".")
    for lab in labels:
        if lab == "" or len(lab) > 63:
            return False
    return True

def split_bracket_content(content: str) -> List[Tuple[str, bool]]:

    out: List[Tuple[str, bool]] = []
    i = 0
    n = len(content)

    while i < n:
        while i < n and (content[i].isspace() or content[i] == ","):
            i += 1
        if i >= n:
            break

        if content[i] == '"':
            i += 1
            start = i
            while i < n and content[i] != '"':
                i += 1
            if i >= n:
                token = content[start:].strip()
                if token:
                    out.append((token, True))
                break
            token = content[start:i]
            out.append((token, True))
            i += 1
        else:
            start = i
            while i < n and (not content[i].isspace()) and content[i] != ",":
                i += 1
            token = content[start:i].strip()
            if token:
                out.append((token, False))

    return out

def find_description_quote_ranges(line: str) -> List[Tuple[int, int]]:

    ranges: List[Tuple[int, int]] = []
    i = 0
    n = len(line)

    while i < n:
        m = re.search(r"\bdescription\b", line[i:], flags=re.IGNORECASE)
        if not m:
            break
        j = i + m.start()
        k = i + m.end()

        q1 = line.find('"', k)
        if q1 == -1:
            i = k
            continue
        q2 = line.find('"', q1 + 1)
        if q2 == -1:
            i = q1 + 1
            continue

        ranges.append((q1, q2 + 1))
        i = q2 + 1

    return ranges

_BOUNDARY_LEFT = r'(^|[\s\[\],\(\)\{\}])'
_BOUNDARY_RIGHT = r'(?=$|[\s\[\],\(\)\{\}])'

def apply_mapping_chunk(chunk: str, mapping: Dict[str, str]) -> str:

    for k, v in mapping.items():
        if k.startswith('"') and k.endswith('"'):
            if k in chunk:
                chunk = chunk.replace(k, v)

    for k, v in mapping.items():
        if k.startswith('"') and k.endswith('"'):
            continue
        pat = re.compile(_BOUNDARY_LEFT + re.escape(k) + _BOUNDARY_RIGHT)
        chunk = pat.sub(lambda m: m.group(1) + v, chunk)

    return chunk

def apply_mapping_outside_description(line: str, mapping: Dict[str, str]) -> str:
    ranges = find_description_quote_ranges(line)
    if not ranges:
        return apply_mapping_chunk(line, mapping)

    out = []
    last = 0
    for a, b in ranges:
        out.append(apply_mapping_chunk(line[last:a], mapping))
        out.append(line[a:b])
        last = b
    out.append(apply_mapping_chunk(line[last:], mapping))
    return "".join(out)

def extract_cut_lines(pan_path: str, prefix: str, out_path: str) -> Tuple[int, int]:
    raw_lines = read_text_file_normalized(pan_path)
    kept: List[str] = []
    cut: List[str] = []

    for ln in raw_lines:
        s = sanitize_line(ln)
        if not s:
            continue
        sl = s.lstrip()
        if sl.startswith(prefix):
            cut.append(sl)
        else:
            kept.append(s)

    write_lines(out_path, cut)
    write_lines(pan_path, kept)
    return (len(kept), len(cut))

def process_tag_rest(rest: str) -> Tuple[str, Optional[str]]:

    parts = rest.split(None, 1)
    if len(parts) == 1:
        return ("delete", None)

    arg = parts[1].strip()
    if arg == "":
        return ("delete", None)

    if arg.startswith("["):
        close = arg.rfind("]")
        if close == -1:
            return ("unsupported", None)
        after = arg[close+1:].strip()
        if after != "":
            return ("unsupported", None)

        inside = arg[1:close].strip()
        toks = split_bracket_content(inside)
        out_toks: List[str] = []
        for tok, was_quoted in toks:
            if was_quoted:
                tok = re.sub(r"\s+", "_", tok.strip())
            tok2 = sanitize_token_to_allowed(tok, ALLOWED_NAME_CHARS)
            if tok2:
                out_toks.append(tok2)

        if not out_toks:
            return ("delete", None)

        return ("keep", "tag [ " + " ".join(out_toks) + " ]")

    if arg.startswith('"'):
        end = arg.find('"', 1)
        if end == -1:
            return ("unsupported", None)
        inner = arg[1:end]
        after = arg[end+1:].strip()
        if after != "":
            return ("unsupported", None)
        inner = re.sub(r"\s+", "_", inner.strip())
        tok = sanitize_token_to_allowed(inner, ALLOWED_NAME_CHARS)
        return ("keep", f"tag {tok}")

    toks = arg.split()
    if len(toks) != 1:
        return ("unsupported", None)

    tok = sanitize_token_to_allowed(toks[0], ALLOWED_NAME_CHARS)
    return ("keep", f"tag {tok}")

def process_static_rest(rest: str) -> Tuple[bool, Optional[str], bool]:

    s = rest.strip()

    if re.match(r"^static\s+\[", s, flags=re.IGNORECASE):
        lb = s.find("[")
        rb = s.rfind("]")
        if rb == -1 or rb < lb:
            return (False, None, False)
        after = s[rb+1:].strip()
        if after != "":
            return (False, None, False)

        inside = s[lb+1:rb].strip()
        toks = split_bracket_content(inside)
        if not toks:
            return (False, None, False)

        out_toks: List[str] = []
        changed = False

        for tok, was_quoted in toks:
            original_render = tok
            if was_quoted:
                tok = re.sub(r"\s+", "_", tok.strip())
                changed = True
            tok2 = sanitize_token_to_allowed(tok, ALLOWED_NAME_CHARS)

            if tok2 != sanitize_token_to_allowed(original_render, ALLOWED_NAME_CHARS):
                changed = True

            if tok2:
                out_toks.append(tok2)

        if not out_toks:
            return (False, None, False)

        return (True, "static [ " + " ".join(out_toks) + " ]", changed)

    parts = s.split()
    if len(parts) != 2:
        return (False, None, False)

    tok = parts[1]
    tok2 = sanitize_token_to_allowed(tok, ALLOWED_NAME_CHARS)
    changed = (tok2 != tok.replace('"', "").replace("'", ""))
    return (True, f"static {tok2}", changed)

def process_dynamic_filter_rest(rest: str) -> Tuple[str, Optional[str]]:

    s = rest.strip()
    low = s.lower()
    if not low.startswith("dynamic filter"):
        return ("unsupported", None)

    arg = s[len("dynamic filter"):].strip()
    if arg == "":
        return ("unsupported", None)

    if arg.startswith("["):
        rb = arg.rfind("]")
        if rb == -1:
            return ("unsupported", None)
        after = arg[rb+1:].strip()
        if after != "":
            return ("unsupported", None)

        inside = arg[1:rb].strip()
        toks = split_bracket_content(inside)
        out_toks: List[str] = []
        for tok, was_quoted in toks:
            if was_quoted:
                tok = re.sub(r"\s+", "_", tok.strip())
            tok2 = sanitize_token_to_allowed(tok, ALLOWED_NAME_CHARS)
            if tok2:
                out_toks.append(tok2)

        if not out_toks:
            return ("unsupported", None)

        return ("keep", "dynamic filter [ " + " ".join(out_toks) + " ]")

    if arg.startswith('"') or arg.startswith("'"):
        q = arg[0]
        end = arg.find(q, 1)
        if end == -1:
            return ("unsupported", None)
        inner = arg[1:end]
        after = arg[end+1:].strip()
        if after != "":
            return ("unsupported", None)
        inner = re.sub(r"\s+", "_", inner.strip())
        tok = sanitize_token_to_allowed(inner, ALLOWED_NAME_CHARS)
        return ("keep", f"dynamic filter {tok}")

    toks = arg.split()
    if len(toks) != 1:
        return ("unsupported", None)

    tok = sanitize_token_to_allowed(toks[0], ALLOWED_NAME_CHARS)
    return ("keep", f"dynamic filter {tok}")

ADDR_ALLOWED_KW = {"ip-netmask", "ip-range", "fqdn", "tag", "description"}

def address_cleanup(step2_dir: str, cleaned_addr_path: str, max_len: int) -> Dict[Tuple[str, bool], str]:
    corrected_path = os.path.join(step2_dir, "step-2_corrected-address-name.txt")
    unsupported_path = os.path.join(step2_dir, "step-2_unsupported-address-config.txt")
    added_netmask_path = os.path.join(step2_dir, "step-2_added-netmask.txt")

    write_lines(corrected_path, [])
    write_lines(unsupported_path, [])
    write_lines(added_netmask_path, [])

    lines_in = [sanitize_line(x).lstrip() for x in read_text_file_normalized(cleaned_addr_path)]
    lines_in = [x for x in lines_in if x]

    records: List[Tuple[str, str, str, str, bool]] = []
    for ln in lines_in:
        p = parse_object_line(ln, "address")
        if not p:
            records.append((ln, "", "", "", False))
        else:
            prefix, raw_name, rest, was_quoted = p
            records.append((ln, prefix, raw_name, rest, was_quoted))

    allocator = TruncAllocator(max_len)

    name_map: Dict[Tuple[str, bool], str] = {}
    for _orig, prefix, raw_name, _rest, was_quoted in records:
        if not prefix or not raw_name:
            continue
        key = (raw_name, was_quoted)
        if key in name_map:
            continue
        base = sanitize_object_name(raw_name)
        final = allocator.allocate(base)
        name_map[key] = final

    invalid_group: Set[str] = set()
    for _orig, prefix, raw_name, rest, _q in records:
        if not prefix or not raw_name:
            continue
        if raw_name in invalid_group:
            continue
        if not rest:
            invalid_group.add(raw_name)
            continue

        parts = rest.split()
        kw = parts[0].lower()

        if kw == "ip-range":
            if len(parts) < 2 or not is_valid_ip_range(parts[1]):
                invalid_group.add(raw_name)
        elif kw == "fqdn":
            if len(parts) < 2 or not is_valid_fqdn_token(parts[1]):
                invalid_group.add(raw_name)
        elif kw == "ip-netmask":
            if len(parts) < 2 or not is_valid_ipv4_or_mask(parts[1]):
                invalid_group.add(raw_name)

    out_cleaned: List[str] = []
    out_unsupported: List[str] = []
    out_corrected: List[str] = []
    out_added32: List[str] = []

    for orig, prefix, raw_name, rest, was_quoted in records:
        if not prefix or not raw_name:
            out_unsupported.append(orig)
            continue

        final_name = name_map.get((raw_name, was_quoted), sanitize_object_name(raw_name))

        if render_name_token(raw_name, was_quoted) != final_name:
            out_corrected.append(orig)

        if raw_name in invalid_group:
            out_unsupported.append(orig)
            continue

        if not rest:
            out_unsupported.append(orig)
            continue

        parts = rest.split()
        kw = parts[0].lower()

        if kw not in ADDR_ALLOWED_KW:
            out_unsupported.append(orig)
            continue

        new_rest = rest

        if kw == "tag":
            status, newtag = process_tag_rest(rest)
            if status == "delete":
                continue
            if status == "unsupported":
                out_unsupported.append(orig)
                continue
            new_rest = newtag

        elif kw == "ip-netmask":
            token = parts[1] if len(parts) >= 2 else ""
            if is_valid_ipv4(token):
                parts2 = parts[:]
                parts2[1] = token + "/32"
                new_rest = " ".join(parts2)
                out_added32.append(orig)

        out_cleaned.append(f"{prefix} {final_name} {new_rest}".rstrip())

    write_lines(cleaned_addr_path, out_cleaned)
    write_lines(unsupported_path, out_unsupported)
    write_lines(corrected_path, out_corrected)
    write_lines(added_netmask_path, out_added32)

    print("\n[Address] Results:")
    print(f"  cleaned:     {cleaned_addr_path}  (lines={len(out_cleaned)})")
    print(f"  corrected:   {corrected_path}     (lines={len(out_corrected)})")
    print(f"  unsupported: {unsupported_path}   (lines={len(out_unsupported)})")
    print(f"  added /32:   {added_netmask_path} (lines={len(out_added32)})")

    return name_map

GRP_ALLOWED_FIRST = {"tag", "static", "description"}

def group_cleanup(step2_dir: str, cleaned_grp_path: str, max_len: int) -> Dict[Tuple[str, bool], str]:
    corrected_path = os.path.join(step2_dir, "step-2_corrected-address-group-name.txt")
    unsupported_path = os.path.join(step2_dir, "step-2_unsupported-address-group-config.txt")

    write_lines(corrected_path, [])
    write_lines(unsupported_path, [])

    lines_in = [sanitize_line(x).lstrip() for x in read_text_file_normalized(cleaned_grp_path)]
    lines_in = [x for x in lines_in if x]

    records: List[Tuple[str, str, str, str, bool]] = []
    for ln in lines_in:
        p = parse_object_line(ln, "group")
        if not p:
            records.append((ln, "", "", "", False))
        else:
            prefix, raw_name, rest, was_quoted = p
            records.append((ln, prefix, raw_name, rest, was_quoted))

    allocator = TruncAllocator(max_len)

    name_map: Dict[Tuple[str, bool], str] = {}
    for _orig, prefix, raw_name, _rest, was_quoted in records:
        if not prefix or not raw_name:
            continue
        key = (raw_name, was_quoted)
        if key in name_map:
            continue
        base = sanitize_object_name(raw_name)
        final = allocator.allocate(base)
        name_map[key] = final

    invalid_group: Set[str] = set()

    static_lines_changed: Set[str] = set()

    for orig, prefix, raw_name, rest, _q in records:
        if not prefix or not raw_name:
            continue
        if raw_name in invalid_group:
            continue
        if not rest:
            invalid_group.add(raw_name)
            continue

        low = rest.lower()
        if low.startswith("dynamic filter"):
            continue

        parts = rest.split()
        kw = parts[0].lower()
        if kw == "static":
            ok, _newr, changed = process_static_rest(rest)
            if not ok:
                invalid_group.add(raw_name)
            elif changed:
                static_lines_changed.add(orig)

    out_cleaned: List[str] = []
    out_unsupported: List[str] = []
    out_corrected: List[str] = []

    for orig, prefix, raw_name, rest, was_quoted in records:
        if not prefix or not raw_name:
            out_unsupported.append(orig)
            continue

        final_name = name_map.get((raw_name, was_quoted), sanitize_object_name(raw_name))

        if render_name_token(raw_name, was_quoted) != final_name or (orig in static_lines_changed):
            out_corrected.append(orig)

        if raw_name in invalid_group:
            out_unsupported.append(orig)
            continue

        if not rest:
            out_unsupported.append(orig)
            continue

        low = rest.lower()
        new_rest: Optional[str] = None

        if low.startswith("dynamic filter"):
            status, newr = process_dynamic_filter_rest(rest)
            if status != "keep":
                out_unsupported.append(orig)
                continue
            new_rest = newr

        else:
            parts = rest.split()
            kw = parts[0].lower()

            if kw not in GRP_ALLOWED_FIRST:
                out_unsupported.append(orig)
                continue

            if kw == "tag":
                status, newtag = process_tag_rest(rest)
                if status == "delete":

                    continue
                if status == "unsupported":

                    out_unsupported.append(orig)
                    continue
                new_rest = newtag

            elif kw == "static":
                ok, newr, _changed = process_static_rest(rest)
                if not ok:

                    out_unsupported.append(orig)
                    continue
                new_rest = newr

            else:

                new_rest = rest

        out_cleaned.append(f"{prefix} {final_name} {new_rest}".rstrip())

    write_lines(cleaned_grp_path, out_cleaned)
    write_lines(unsupported_path, out_unsupported)
    write_lines(corrected_path, out_corrected)

    print("\n[Address-Group] Results:")
    print(f"  cleaned:     {cleaned_grp_path}  (lines={len(out_cleaned)})")
    print(f"  corrected:   {corrected_path}    (lines={len(out_corrected)})")
    print(f"  unsupported: {unsupported_path}  (lines={len(out_unsupported)})")

    return name_map

def update_pan_rules_with_corrected_names(pan_path: str, corrected_lines_path: str,
                                         kind: str,
                                         name_map: Dict[Tuple[str, bool], str],
                                         parse_kind: str) -> int:

    if not os.path.isfile(corrected_lines_path):
        return 0

    corr_lines = [sanitize_line(x).lstrip() for x in read_text_file_normalized(corrected_lines_path)]
    corr_lines = [x for x in corr_lines if x.strip()]

    if not corr_lines:
        print(f"\n[{kind}] Step update: corrected file is empty => skip.")
        return 0

    mapping: Dict[str, str] = {}
    for ln in corr_lines:
        p = parse_object_line(ln, parse_kind)
        if not p:
            continue
        _prefix, raw_name, _rest, was_quoted = p
        final = name_map.get((raw_name, was_quoted), sanitize_object_name(raw_name))
        raw_tok = render_name_token(raw_name, was_quoted)

        mapping[raw_tok] = final
        if not was_quoted:
            mapping[raw_name] = final

    if not mapping:
        print(f"\n[{kind}] Step update: no usable names found => skip.")
        return 0

    lines = read_text_file_normalized(pan_path)
    changed = 0
    out_lines: List[str] = []

    for ln in lines:
        s = sanitize_line(ln)
        if not s:
            out_lines.append("")
            continue
        new_s = apply_mapping_outside_description(s, mapping)
        if new_s != s:
            changed += 1
        out_lines.append(new_s)

    write_lines(pan_path, out_lines)

    print(f"\n[{kind}] Updated references in pan-rules file: {pan_path}")
    print(f"  corrected-file: {corrected_lines_path}")
    print(f"  changed lines : {changed}")
    return changed

SEC_RULES_RE = re.compile(r"\bsecurity\s+rules\b", flags=re.IGNORECASE)

def scan_tokens_loose(s: str) -> List[Tuple[str, bool]]:

    out: List[Tuple[str, bool]] = []
    i = 0
    n = len(s)

    while i < n:
        ch = s[i]
        if ch.isspace() or ch == ",":
            i += 1
            continue
        if ch in ("[", "]"):
            out.append((ch, False))
            i += 1
            continue
        if ch == '"':
            i += 1
            start = i
            while i < n and s[i] != '"':
                i += 1
            token = s[start:i]
            out.append((token, True))
            if i < n and s[i] == '"':
                i += 1
            continue

        start = i
        while i < n and (not s[i].isspace()) and s[i] not in [",", "[", "]", '"']:
            i += 1
        token = s[start:i]
        out.append((token, False))
    return out

def extract_source_dest_tokens_from_security_rules_lines(pan_path: str) -> Set[str]:

    tokens_used: Set[str] = set()
    lines = [sanitize_line(x) for x in read_text_file_normalized(pan_path)]
    for ln in lines:
        if not ln.strip():
            continue
        if not SEC_RULES_RE.search(ln):
            continue

        toks = scan_tokens_loose(ln)

        for key in ("source", "destination"):
            for idx, (t, _q) in enumerate(toks):
                if t.lower() != key:
                    continue
                if idx + 1 >= len(toks):
                    continue
                nxt, nq = toks[idx + 1]
                if nxt == "[":

                    j = idx + 2
                    while j < len(toks):
                        tt, tq = toks[j]
                        if tt == "]":
                            break
                        if tt not in ("[", "]"):
                            tokens_used.add(tt)
                        j += 1
                else:
                    tokens_used.add(nxt)
    return tokens_used

def extract_all_tokens_from_cleaned_group_file(group_path: str) -> Set[str]:

    tokens_used: Set[str] = set()
    lines = [sanitize_line(x) for x in read_text_file_normalized(group_path)]
    for ln in lines:
        if not ln.strip():
            continue

        ranges = find_description_quote_ranges(ln)
        if ranges:
            out = []
            last = 0
            for a, b in ranges:
                out.append(ln[last:a])
                out.append('""')
                last = b
            out.append(ln[last:])
            ln2 = "".join(out)
        else:
            ln2 = ln

        toks = scan_tokens_loose(ln2)
        for t, _q in toks:
            if t in ("[", "]"):
                continue
            tokens_used.add(t)
    return tokens_used

MUST_FIX_PATH_COMMENT = (
    '*******************************************************************************************************************'
    'You must fix the address object configuration from this file and add the configuration back '
    'into the file located in "../final-data/final-address.txt". Do that after Step #3 if you ran these script manually.'
    '*******************************************************************************************************************'
)

WARNING_MSG = (
    '*********************************************************************************************************************************'
    'WARNING: There were unsupported addresses/groups configuration that are either not supported or it\'s beyond the capability '
    'of this scrips to rectify. But, those addresses/groups are being used in the firewall policies. You must fix the address object '
    'configuration from this file and add the configuration back into the file located in "../final-data/final-address.txt" or '
    '../final-data/final-address-group.txt". Do that after Step #3 if you ran these script manually.'
    '*********************************************************************************************************************************'
)

def ensure_must_fix_header(path: str) -> None:
    if not os.path.isfile(path):
        return
    lines = read_text_file_normalized(path)
    if not lines:
        return
    first = lines[0].rstrip("\n")
    if first == MUST_FIX_PATH_COMMENT:
        return

    new_lines = [MUST_FIX_PATH_COMMENT] + lines
    write_lines(path, [sanitize_line(x) for x in new_lines if x is not None])

def must_fix_has_payload(path: str) -> bool:
    if not os.path.isfile(path):
        return False
    lines = [sanitize_line(x) for x in read_text_file_normalized(path)]
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if s == MUST_FIX_PATH_COMMENT:
            continue

        return True
    return False

def append_lines_dedup(path: str, new_lines: List[str]) -> int:
    """
    Append unique lines only (avoid duplicates across runs).
    Returns count appended.
    """
    existing = set()
    if os.path.isfile(path):
        for ln in read_text_file_normalized(path):
            s = sanitize_line(ln).strip()
            if s:
                existing.add(s)

    to_add = []
    for ln in new_lines:
        s = sanitize_line(ln).strip()
        if not s:
            continue
        if s not in existing:
            to_add.append(s)
            existing.add(s)

    if to_add:
        append_lines(path, to_add)
    return len(to_add)

def step_26_process_unsupported_addresses(main_dir: str,
                                         step2_dir: str,
                                         pan_path: str,
                                         cleaned_group_path: str,
                                         addr_name_map: Dict[Tuple[str, bool], str],
                                         max_len: int) -> int:
    """
    26a/26b
    """
    unsupported_addr = os.path.join(step2_dir, "step-2_unsupported-address-config.txt")
    must_fix_path = os.path.join(main_dir, "must-fix-address-object.txt")

    if not file_exists_and_nonempty(unsupported_addr):
        print("\n[Step 26] No unsupported address config file, or it is empty => skip.")
        return 0

    policy_tokens = extract_source_dest_tokens_from_security_rules_lines(pan_path)
    group_tokens = extract_all_tokens_from_cleaned_group_file(cleaned_group_path) if os.path.isfile(cleaned_group_path) else set()

    lines = [sanitize_line(x).lstrip() for x in read_text_file_normalized(unsupported_addr)]
    lines = [x for x in lines if x.strip()]

    hits: List[str] = []

    for ln in lines:
        p = parse_object_line(ln, "address")
        if not p:
            continue
        _prefix, raw_name, _rest, was_quoted = p

        final = addr_name_map.get((raw_name, was_quoted), sanitize_object_name(raw_name))
        candidates = {raw_name, final}

        used_in_policies = any(c in policy_tokens for c in candidates)
        used_in_groups = any(c in group_tokens for c in candidates)

        if used_in_policies or used_in_groups:
            hits.append(ln)

    if not hits:
        print("\n[Step 26] Unsupported address configs exist, but none appear used in policies/groups => no must-fix additions.")
        return 0

    appended = append_lines_dedup(must_fix_path, hits)
    if appended > 0:
        ensure_must_fix_header(must_fix_path)
        print(f"\n[Step 26] Added {appended} unsupported address lines to: {must_fix_path}")
    else:
        print(f"\n[Step 26] Matching unsupported address lines already present in: {must_fix_path}")

    return appended

def step_27_process_unsupported_address_groups(main_dir: str,
                                               step2_dir: str,
                                               pan_path: str,
                                               cleaned_group_path: str,
                                               grp_name_map: Dict[Tuple[str, bool], str],
                                               max_len: int) -> int:

    unsupported_grp = os.path.join(step2_dir, "step-2_unsupported-address-group-config.txt")
    must_fix_path = os.path.join(main_dir, "must-fix-address-object.txt")

    if not file_exists_and_nonempty(unsupported_grp):
        print("\n[Step 27] No unsupported address-group config file, or it is empty => skip.")
        return 0

    policy_tokens = extract_source_dest_tokens_from_security_rules_lines(pan_path)
    group_tokens = extract_all_tokens_from_cleaned_group_file(cleaned_group_path) if os.path.isfile(cleaned_group_path) else set()

    lines = [sanitize_line(x).lstrip() for x in read_text_file_normalized(unsupported_grp)]
    lines = [x for x in lines if x.strip()]

    hits: List[str] = []

    for ln in lines:
        p = parse_object_line(ln, "group")
        if not p:
            continue
        _prefix, raw_name, _rest, was_quoted = p

        final = grp_name_map.get((raw_name, was_quoted), sanitize_object_name(raw_name))
        candidates = {raw_name, final}

        used_in_policies = any(c in policy_tokens for c in candidates)
        used_in_groups = any(c in group_tokens for c in candidates)

        if used_in_policies or used_in_groups:
            hits.append(ln)

    if not hits:
        print("\n[Step 27] Unsupported address-group configs exist, but none appear used in policies/groups => no must-fix additions.")
        return 0

    appended = append_lines_dedup(must_fix_path, hits)
    if appended > 0:
        ensure_must_fix_header(must_fix_path)
        print(f"\n[Step 27] Added {appended} unsupported address-group lines to: {must_fix_path}")
    else:
        print(f"\n[Step 27] Matching unsupported address-group lines already present in: {must_fix_path}")

    return appended

def main() -> int:
    cwd = os.getcwd()
    main_dir = resolve_main_dir(cwd)

    step2_dir = os.path.join(main_dir, "step-2")
    log_dir = os.path.join(main_dir, "log")
    ensure_dir(step2_dir)
    ensure_dir(log_dir)

    log_path = os.path.join(log_dir, "step-2.log")
    with open(log_path, "w", encoding="utf-8") as log_fp:
        sys.stdout = TeeIO(sys.__stdout__, log_fp)
        sys.stderr = TeeIO(sys.__stderr__, log_fp)

        print("=" * 110)
        print("STEP-2 START")
        print(f"Timestamp   : {datetime.now().isoformat(timespec='seconds')}")
        print(f"CWD         : {cwd}")
        print(f"Main dir    : {main_dir}")
        print(f"Step-2 dir  : {step2_dir}")
        print(f"Log file    : {log_path}")
        print("=" * 110)

        step1_default = os.path.join(main_dir, "step-1", "step-1_cleaned-pan-rules.txt")
        step2_pan = os.path.join(step2_dir, "step-2_cleaned-pan-rules.txt")

        if os.path.isfile(step1_default):
            print(f"\n[Step 2] Found input: {step1_default}")
            print(f"[Step 2] Copying to : {step2_pan}")
            copy_file(step1_default, step2_pan)
        else:
            print(f"\n[Step 2] Default input missing: {step1_default}")
            src_in = input_with_timeout("Enter source file path to copy into step-2 (auto-continue in 15s): ", 15)
            src = (src_in or "").strip()
            if src == "":
                print("ERROR: No source path provided.")
                return 1
            src_path = os.path.abspath(os.path.join(cwd, src)) if not os.path.isabs(src) else src
            if not os.path.isfile(src_path):
                print(f"ERROR: Source file not found: {src_path}")
                return 1
            print(f"[Step 2] Copying to : {step2_pan}")
            copy_file(src_path, step2_pan)

        print("\n[Step 3] Max object name length:")
        print("  Recommended maximum is 63.")
        print("  Any object name longer than your max will be truncated and suffixed with _x (x increments).")
        print("Enter max length (press Enter for 63): [auto] waiting 15 seconds, then using default 63.")
        time.sleep(15)
        user_len = ""
        max_len = 63
        if user_len != "":
            try:
                v = int(user_len)
                if 1 <= v <= 63:
                    max_len = v
            except ValueError:
                max_len = 63
        print(f"[Step 3] Using max length: {max_len}")

        print("\n[Step 4] Allowed characters in objects name are alphanumeric, \"_\", \"-\", \".\" and \"/\".")
        print("  HOWEVER: this script is configured so that \"/\" is NOT allowed and will be replaced by \"_\".")
        print("  Any unacceptable characters in the object names will be replaced by \"_\".")
        print("Press Enter to continue or wait 30s to auto-continue.")
        _ = input_with_timeout("Continue (Enter) > ", 15)

        extracted_addr = os.path.join(step2_dir, "step-2_extracted-address.txt")
        print("\n[Step 5] Cutting address lines: prefix 'set shared address '")
        kept, cut = extract_cut_lines(step2_pan, "set shared address ", extracted_addr)
        print(f"[Step 5] Remaining lines in step-2_cleaned-pan-rules.txt: {kept}")
        print(f"[Step 5] Extracted address lines: {cut} -> {extracted_addr}")

        cleaned_addr = os.path.join(step2_dir, "step-2_cleaned-address.txt")
        print(f"\n[Step 6] Copying extracted address -> {cleaned_addr}")
        copy_file(extracted_addr, cleaned_addr)

        print("\n[Steps 7-14] Cleaning address objects...")
        addr_name_map = address_cleanup(step2_dir, cleaned_addr, max_len)

        corrected_addr_file = os.path.join(step2_dir, "step-2_corrected-address-name.txt")
        print("\n[Step 15] Updating references in step-2_cleaned-pan-rules.txt using corrected address names...")
        update_pan_rules_with_corrected_names(
            step2_pan,
            corrected_addr_file,
            kind="Address",
            name_map=addr_name_map,
            parse_kind="address"
        )

        extracted_grp = os.path.join(step2_dir, "step-2_extracted-address-group.txt")
        print("\n[Step 16] Cutting address-group lines: prefix 'set shared address-group '")
        kept2, cut2 = extract_cut_lines(step2_pan, "set shared address-group ", extracted_grp)
        print(f"[Step 16] Remaining lines in step-2_cleaned-pan-rules.txt: {kept2}")
        print(f"[Step 16] Extracted address-group lines: {cut2} -> {extracted_grp}")

        cleaned_grp = os.path.join(step2_dir, "step-2_cleaned-address-group.txt")
        print(f"\n[Step 17] Copying extracted address-group -> {cleaned_grp}")
        copy_file(extracted_grp, cleaned_grp)

        print("\n[Steps 18-24] Cleaning address-group objects...")
        grp_name_map = group_cleanup(step2_dir, cleaned_grp, max_len)

        corrected_grp_file = os.path.join(step2_dir, "step-2_corrected-address-group-name.txt")
        print("\n[Step 25] Updating references in step-2_cleaned-pan-rules.txt using corrected address-group names...")
        update_pan_rules_with_corrected_names(
            step2_pan,
            corrected_grp_file,
            kind="Address-Group",
            name_map=grp_name_map,
            parse_kind="group"
        )

        print("\n[Step 26] Checking unsupported address configs that are used in policies/groups...")
        _a = step_26_process_unsupported_addresses(
            main_dir=main_dir,
            step2_dir=step2_dir,
            pan_path=step2_pan,
            cleaned_group_path=cleaned_grp,
            addr_name_map=addr_name_map,
            max_len=max_len
        )

        print("\n[Step 27] Checking unsupported address-group configs that are used in policies/groups...")
        _g = step_27_process_unsupported_address_groups(
            main_dir=main_dir,
            step2_dir=step2_dir,
            pan_path=step2_pan,
            cleaned_group_path=cleaned_grp,
            grp_name_map=grp_name_map,
            max_len=max_len
        )

        must_fix_path = os.path.join(main_dir, "must-fix-address-object.txt")
        if must_fix_has_payload(must_fix_path):
            print("\n[Step 28] " + WARNING_MSG)
            print("Press Enter to continue or wait 30s to auto-continue.")
            _ = input_with_timeout("Continue (Enter) > ", 15)
        else:
            print("\n[Step 28] No must-fix file with payload detected => no warning pause.")

        print("\nSTEP-2 DONE")
        print(f"Log file: {log_path}")
        return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        raise SystemExit(130)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        raise SystemExit(1)
