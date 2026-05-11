
import os
import re
import sys
import time
import shutil
import logging
import traceback
from datetime import datetime
from typing import List, Tuple, Dict, Optional
from queue import Queue
from threading import Thread


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

LOG_DIR = os.path.join(MAIN_DIR, "log")
FINAL_DATA_DIR = os.path.join(MAIN_DIR, "final-data")
TEMP_DIR = os.path.join(MAIN_DIR, "temp")

LOG_FILE = os.path.join(LOG_DIR, "step-8.log")

PAN_INPUT = os.path.join(FINAL_DATA_DIR, "cleaned-pan-rules.txt")
TEMP_PAN = os.path.join(TEMP_DIR, "temp-pan-rules.txt")

SVT_TEMPLATE = os.path.join(FINAL_DATA_DIR, "svt-temp.cfg")

ZONE_CONV_FILE = os.path.join(MAIN_DIR, "zone-conversion.txt")
PREDEF_SVC_CONV_FILE = os.path.join(MAIN_DIR, "predef-service-conversion.txt")
PREDEF_APP_CONV_FILE = os.path.join(MAIN_DIR, "predef-application-conversion.txt")

FINAL_ADDR_GRP_FILE = os.path.join(FINAL_DATA_DIR, "final-address-group.txt")
LDAP_GROUPS_FILE = os.path.join(FINAL_DATA_DIR, "final-ldap-groups.txt")
LDAP_USERS_FILE = os.path.join(FINAL_DATA_DIR, "final-ldap-users.txt")

FINAL_CUSTOM_URLF_PROFILE = os.path.join(FINAL_DATA_DIR, "final-custom-urlf-profile.txt")
UNRESOLVED_CUSTOM_URL_CFG = os.path.join(MAIN_DIR, "unresolved-custom-url-configuration.txt")

UNSUPPORTED_APPS_FILE = os.path.join(MAIN_DIR, "unsupported-predef-application.txt")


class StreamToLogger:
    def __init__(self, logger: logging.Logger, level: int):
        self.logger = logger
        self.level = level
        self._buf = ""

    def write(self, msg: str):
        if not msg:
            return
        self._buf += msg
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip("\r")
            if line:
                self.logger.log(self.level, line)

    def flush(self):
        if self._buf.strip():
            self.logger.log(self.level, self._buf.strip())
        self._buf = ""


def setup_logger() -> logging.Logger:
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger("step-8")
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")

    fh = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    ch = logging.StreamHandler(sys.__stdout__)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    logger.info("------------------------------------------------------------")
    logger.info("Step-8 start: %s", datetime.now().isoformat(timespec="seconds"))
    logger.info("MAIN_DIR=%s", MAIN_DIR)
    logger.info("SCRIPT_DIR=%s", SCRIPT_DIR)
    logger.info("LOG_FILE=%s", LOG_FILE)
    return logger


def input_with_timeout(prompt: str, timeout_sec: int, logger: logging.Logger, default: str = "") -> str:
    q: Queue = Queue()

    def _reader():
        try:
            ans = input(prompt)
            q.put(ans)
        except Exception as e:
            logger.error("Input error: %s", e)
            q.put(default)

    t = Thread(target=_reader, daemon=True)
    t.start()

    start = time.time()
    while time.time() - start < timeout_sec:
        if not q.empty():
            return q.get()
        time.sleep(0.1)

    logger.info("Input timeout after %ss. Using default.", timeout_sec)
    return default


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def read_lines(path: str) -> List[str]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read().splitlines(True)


def write_text(path: str, text: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def safe_copy(src: str, dst: str, logger: logging.Logger):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    logger.info("Copied: %s -> %s", src, dst)


def safe_remove_dir(path: str, logger: logging.Logger):
    if os.path.isdir(path):
        shutil.rmtree(path)
        logger.info("Deleted directory: %s", path)


def strip_outer_quotes(s: str) -> str:
    t = s.strip()
    if len(t) >= 2 and t[0] == '"' and t[-1] == '"':
        return t[1:-1]
    return t


SEC_RULES_RE = re.compile(r"\bsecurity\s+rules\s+", re.IGNORECASE)


def extract_policy_name_from_line(line: str) -> Optional[str]:
    m = SEC_RULES_RE.search(line)
    if not m:
        return None
    rest = line[m.end():].lstrip()
    if not rest:
        return None
    if rest.startswith('"'):
        endq = rest.find('"', 1)
        if endq == -1:
            return None
        return rest[:endq + 1]
    return rest.split(None, 1)[0]


def line_belongs_to_policy(line: str, policy_name: str) -> bool:
    m = SEC_RULES_RE.search(line)
    if not m:
        return False
    rest = line[m.end():].lstrip()
    if not rest:
        return False
    if policy_name.startswith('"'):
        return rest.startswith(policy_name)
    return rest.split(None, 1)[0] == policy_name


def pop_next_policy(lines: List[str], logger: logging.Logger) -> Tuple[Optional[str], List[str], List[str]]:
    name = None
    for ln in lines:
        name = extract_policy_name_from_line(ln)
        if name:
            break
    if not name:
        return None, [], lines

    block, rem = [], []
    for ln in lines:
        if line_belongs_to_policy(ln, name):
            block.append(ln)
        else:
            rem.append(ln)

    logger.info("Processing policy: %s (lines=%d)", name, len(block))
    return name, block, rem


def load_mapping(path: str, logger: logging.Logger) -> Dict[str, str]:
    mp: Dict[str, str] = {}
    if not os.path.exists(path):
        logger.info("Mapping file missing: %s (treated as empty)", path)
        return mp
    for raw in read_lines(path):
        line = raw.strip()
        if not line or line.startswith("#") or ">>" not in line:
            continue
        left, right = line.split(">>", 1)
        k = left.strip()
        v = right.strip()
        if k:
            mp[k] = v
    logger.info("Loaded mapping: %s (%d entries)", path, len(mp))
    return mp


def load_set(path: str, logger: logging.Logger) -> set:
    st = set()
    if not os.path.exists(path):
        logger.info("Set file missing (treated empty): %s", path)
        return st
    for raw in read_lines(path):
        s = raw.strip()
        if not s:
            continue
        st.add(s)
        st.add(strip_outer_quotes(s))
    logger.info("Loaded set: %s (%d entries)", path, len(st))
    return st


def load_address_group_names(path: str, logger: logging.Logger) -> set:
    st = set()
    if not os.path.exists(path):
        logger.info("Address-group file missing (treated empty): %s", path)
        return st
    prefix = "set shared address-group "
    for raw in read_lines(path):
        line = raw.strip()
        if not line.startswith(prefix):
            continue
        rest = line[len(prefix):].lstrip()
        if not rest:
            continue
        if rest.startswith('"'):
            endq = rest.find('"', 1)
            name = rest[:endq + 1] if endq != -1 else rest
        else:
            name = rest.split(None, 1)[0]
        st.add(name)
        st.add(strip_outer_quotes(name))
    logger.info("Loaded %d address-group names from %s", len(st), path)
    return st


def load_custom_url_categories(path: str, logger: logging.Logger) -> set:
    names = set()
    if not os.path.exists(path):
        logger.info("Custom URLF profile file missing (treated empty): %s", path)
        return names
    prefix = "set shared profiles custom-url-category "
    for raw in read_lines(path):
        line = raw.strip()
        if not line.startswith(prefix):
            continue
        rest = line[len(prefix):].lstrip()
        if not rest:
            continue
        if rest.startswith('"'):
            endq = rest.find('"', 1)
            name = rest[:endq + 1] if endq != -1 else rest
        else:
            name = rest.split(None, 1)[0]
        names.add(name)
        names.add(strip_outer_quotes(name))
    logger.info("Loaded %d custom-url-category names from %s", len(names), path)
    return names


def cleaned_pan_has_urlf_profile_setting(path: str) -> bool:
    if not os.path.exists(path):
        return False
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for ln in f:
            if "profile-setting profiles url-filtering" in ln:
                return True
    return False


def find_block(text: str, begin_delim: str, end_delim: str) -> Optional[Tuple[int, int, str]]:
    s = text.find(begin_delim)
    if s == -1:
        return None
    e = text.find(end_delim, s)
    if e == -1:
        return None
    e2 = e + len(end_delim)
    if e2 < len(text) and text[e2:e2 + 1] == "\n":
        e2 += 1
    return s, e2, text[s:e2]


def delete_block_including(text: str, begin_delim: str, end_delim: str) -> str:
    fb = find_block(text, begin_delim, end_delim)
    if not fb:
        return text
    s, e, _ = fb
    return text[:s] + text[e:]


def delete_only_delim_lines(text: str, begin_delim: str, end_delim: str) -> str:
    out = []
    for ln in text.splitlines(True):
        if begin_delim in ln or end_delim in ln:
            continue
        out.append(ln)
    return "".join(out)


def delete_delimiter_lines_by_regex(text: str, regexes: List[str]) -> str:
    regs = [re.compile(r) for r in regexes]
    out = []
    for ln in text.splitlines(True):
        if any(rx.match(ln) for rx in regs):
            continue
        out.append(ln)
    return "".join(out)


def get_max_numbered_section(text: str, base_name: str) -> int:
    pat = re.compile(r"/\*begin section " + re.escape(base_name) + r"_(\d+)\*/")
    nums = [int(m.group(1)) for m in pat.finditer(text)]
    return max(nums) if nums else 0


def duplicate_section(cfg_text: str, base_name: str, logger: logging.Logger, n: int) -> Tuple[str, int]:
    begin_x = f"/*begin section {base_name}_x*/"
    end_x = f"/*end section {base_name}_x*/"
    fb = find_block(cfg_text, begin_x, end_x)
    if not fb:
        raise RuntimeError(f"Template section not found: {begin_x} .. {end_x}")

    max_n = get_max_numbered_section(cfg_text, base_name)
    insert_at = fb[1]
    if max_n > 0:
        fb_last = find_block(cfg_text, f"/*begin section {base_name}_{max_n}*/", f"/*end section {base_name}_{max_n}*/")
        if fb_last:
            insert_at = fb_last[1]

    _, _, templ = fb
    new_block = templ.replace(f"{base_name}_x", f"{base_name}_{n}")
    cfg_text = cfg_text[:insert_at] + new_block + cfg_text[insert_at:]
    logger.info("Duplicated section %s_x -> %s_%d", base_name, base_name, n)
    return cfg_text, n


def find_numbered_section(cfg_text: str, base_name: str, n: int) -> Tuple[int, int, str]:
    fb = find_block(cfg_text, f"/*begin section {base_name}_{n}*/", f"/*end section {base_name}_{n}*/")
    if not fb:
        raise RuntimeError(f"Numbered section not found: {base_name}_{n}")
    return fb


def replace_rightmost_marker(block: str, marker: str, value: str) -> str:
    idx = block.rfind(marker)
    if idx == -1:
        return block
    return block[:idx] + value + block[idx + len(marker):]


def duplicate_marker_to_right(block: str, marker: str) -> str:
    idx = block.rfind(marker)
    if idx == -1:
        return block
    return block[:idx + len(marker)] + " " + marker + block[idx + len(marker):]


def delete_exact_line_containing(block: str, exact_stripped: str) -> str:
    tgt = exact_stripped.strip()
    out = []
    for ln in block.splitlines(True):
        if ln.strip() == tgt:
            continue
        out.append(ln)
    return "".join(out)


def split_tokens_preserve_quotes(s: str) -> List[str]:
    tokens = []
    i, n = 0, len(s)
    while i < n:
        while i < n and s[i].isspace():
            i += 1
        if i >= n:
            break
        if s[i] == '"':
            j = i + 1
            while j < n and s[j] != '"':
                j += 1
            if j < n:
                tokens.append(s[i:j + 1])
                i = j + 1
            else:
                tokens.append(s[i:])
                break
        else:
            j = i
            while j < n and not s[j].isspace():
                j += 1
            tokens.append(s[i:j])
            i = j
    return [t for t in tokens if t]


def parse_list_or_single(s: str) -> List[str]:
    s = s.strip()
    if not s:
        return []
    if s == "any":
        return ["any"]
    if s.startswith("["):
        rb = s.find("]")
        inside = s[1:rb].strip() if rb != -1 else s[1:].strip()
        return split_tokens_preserve_quotes(inside)
    return split_tokens_preserve_quotes(s)


def find_first_line_with_keyword(lines: List[str], keyword_with_spaces: str) -> Optional[int]:
    for i, ln in enumerate(lines):
        if keyword_with_spaces in ln:
            return i
    return None


def extract_after_keyword(line: str, keyword_with_spaces: str) -> str:
    p = line.find(keyword_with_spaces)
    if p == -1:
        return ""
    return line[p + len(keyword_with_spaces):].lstrip()


def pop_line(lines: List[str], idx: int) -> str:
    ln = lines[idx]
    del lines[idx]
    return ln


def sanitize_policy_tag(tag_raw: str) -> str:
    t = tag_raw.strip()
    if t.startswith("[") and "]" in t:
        t = t[1:t.find("]")].strip()
    if len(t) >= 2 and t[0] == '"' and t[-1] == '"':
        t = t[1:-1]
    t = t.replace('"', "")
    t = re.sub(r"[^A-Za-z0-9._-]", "_", t)
    t = re.sub(r"_+", "_", t).strip("_")
    if len(t) > 63:
        t = t[:63]
    return t


def sanitize_description_inner(inner: str) -> str:


    inner = inner.replace("\f", "_f")
    inner = inner.replace('"', "")
    if len(inner) > 127:
        inner = inner[:127]
    return inner


def sanitize_description_line(line: str) -> str:
    if not line.lstrip(" ").startswith("description"):
        return line

    nl = "\n" if line.endswith("\n") else ""
    base = line[:-1] if nl else line

    first = base.find('"')
    last = base.rfind('"')

    if first != -1 and last != -1 and last > first:
        before = base[:first + 1]
        inner = base[first + 1:last]
        after = base[last:]
        inner = sanitize_description_inner(inner)
        return before + inner + after + nl


    return line


def sanitize_all_description_lines(cfg_text: str) -> str:
    out = []
    for ln in cfg_text.splitlines(True):
        if ln.lstrip(" ").startswith("description"):
            out.append(sanitize_description_line(ln))
        else:
            out.append(ln)
    return "".join(out)


PREDEF_APP_LINE_RE = re.compile(r'^(\s*predefined-application-list\s*\[)(.*?)(\]\s*;.*)$')


def dedupe_predefined_application_list_lines(cfg_text: str) -> str:
    out = []
    for ln in cfg_text.splitlines(True):
        base = ln.rstrip("\n")
        m = PREDEF_APP_LINE_RE.match(base)
        if not m:
            out.append(ln)
            continue
        head, mid, tail = m.group(1), m.group(2), m.group(3)
        tokens = split_tokens_preserve_quotes(mid.strip())
        seen = set()
        uniq = []
        for t in tokens:
            if t not in seen:
                seen.add(t)
                uniq.append(t)
        new_mid = " " + " ".join(uniq) + " " if uniq else " "
        out.append(head + new_mid + tail + ("\n" if ln.endswith("\n") else ""))
    return "".join(out)




# Dedup words in services lists:
#   services-list            [ word1 word1 word1 ];
#   predefined-services-list [ word1 word1 word1 ];
SVC_LIST_LINE_RE = re.compile(r'^(\s*(?:services-list|predefined-services-list)\s*\[)(.*?)(\]\s*;.*)$')

def dedupe_service_list_lines(cfg_text: str) -> str:
    out = []
    for ln in cfg_text.splitlines(True):
        base = ln.rstrip("\n")
        m = SVC_LIST_LINE_RE.match(base)
        if not m:
            out.append(ln)
            continue
        head, mid, tail = m.group(1), m.group(2), m.group(3)
        tokens = split_tokens_preserve_quotes(mid.strip())
        seen = set()
        uniq = []
        for t in tokens:
            if t not in seen:
                seen.add(t)
                uniq.append(t)
        new_mid = " " + " ".join(uniq) + " " if uniq else " "
        out.append(head + new_mid + tail + ("\n" if ln.endswith("\n") else ""))
    return "".join(out)
def remove_empty_list_lines(cfg_text: str) -> str:
    out = []
    for ln in cfg_text.splitlines(True):
        s = ln.strip()
        if re.match(r"^(address-list|address-group-list)\s*\[\s*\]\s*;\s*$", s):
            continue
        if re.match(r"^(predefined-group-list|predefined-application-list|services-list|predefined-services-list)\s*\[\s*\]\s*;\s*$", s):
            continue
        out.append(ln)
    return "".join(out)


def remove_empty_users_groups_blocks(cfg_text: str) -> str:
    lines = cfg_text.splitlines(True)
    out = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if re.match(r'^\s*(users|groups)\s*\{\s*$', ln.strip()):
            start_i = i
            indent = re.match(r'^(\s*)', ln).group(1)
            j = i + 1
            while j < len(lines):
                if re.match(r'^' + re.escape(indent) + r'\}\s*$', lines[j].rstrip("\n")):
                    inner = "".join(lines[i + 1:j]).strip()
                    if inner == "":
                        i = j + 1
                        break
                    out.extend(lines[start_i:j + 1])
                    i = j + 1
                    break
                j += 1
            else:
                out.append(ln)
                i += 1
            continue
        out.append(ln)
        i += 1
    return "".join(out)


def process_zone_match(
    block: str,
    policy_lines: List[str],
    keyword_with_spaces: str,
    subsection_begin: str,
    subsection_end: str,
    marker: str,
    zone_map: Dict[str, str],
) -> Tuple[str, List[str]]:
    idx = find_first_line_with_keyword(policy_lines, keyword_with_spaces)
    if idx is None:
        block = delete_block_including(block, subsection_begin, subsection_end)
        return block, policy_lines

    ln = policy_lines[idx]
    targets = parse_list_or_single(extract_after_keyword(ln, keyword_with_spaces))
    if not targets or (len(targets) == 1 and strip_outer_quotes(targets[0]) == "any"):
        block = delete_block_including(block, subsection_begin, subsection_end)
        pop_line(policy_lines, idx)
        return block, policy_lines

    out_zones = []
    for t in targets:
        t2 = strip_outer_quotes(t)
        if t2 == "any":
            continue
        if t2 in zone_map:
            cv = zone_map[t2]
            out_zones.append(cv if cv else t2)
        else:
            out_zones.append(t2)

    if not out_zones:
        block = delete_block_including(block, subsection_begin, subsection_end)
        pop_line(policy_lines, idx)
        return block, policy_lines

    for j, z in enumerate(out_zones):
        if marker not in block:
            break
        if j > 0:
            block = duplicate_marker_to_right(block, marker)
        block = replace_rightmost_marker(block, marker, z)

    block = block.replace(marker, "")
    block = delete_only_delim_lines(block, subsection_begin, subsection_end)

    pop_line(policy_lines, idx)
    return block, policy_lines


def process_address_split(
    block: str,
    policy_lines: List[str],
    keyword_with_spaces: str,
    subsection_begin: str,
    subsection_end: str,
    marker_addr: str,
    marker_grp: str,
    addr_group_names: set,
    placeholder_addr_line: str,
    placeholder_grp_line: str,
) -> Tuple[str, List[str]]:
    idx = find_first_line_with_keyword(policy_lines, keyword_with_spaces)
    if idx is None:
        block = delete_block_including(block, subsection_begin, subsection_end)
        return block, policy_lines

    ln = policy_lines[idx]
    targets = parse_list_or_single(extract_after_keyword(ln, keyword_with_spaces))

    if not targets or (len(targets) == 1 and strip_outer_quotes(targets[0]) == "any"):
        block = delete_block_including(block, subsection_begin, subsection_end)
        pop_line(policy_lines, idx)
        return block, policy_lines

    wrote_a = False
    wrote_g = False

    for t in targets:
        raw = t.strip()
        cmpv = strip_outer_quotes(raw)
        is_grp = (raw in addr_group_names) or (cmpv in addr_group_names)

        if is_grp:
            if marker_grp in block:
                if wrote_g:
                    block = duplicate_marker_to_right(block, marker_grp)
                block = replace_rightmost_marker(block, marker_grp, cmpv)
                wrote_g = True
        else:
            if marker_addr in block:
                if wrote_a:
                    block = duplicate_marker_to_right(block, marker_addr)
                block = replace_rightmost_marker(block, marker_addr, cmpv)
                wrote_a = True

    block = delete_only_delim_lines(block, subsection_begin, subsection_end)

    if not wrote_a:
        block = delete_exact_line_containing(block, placeholder_addr_line)
    if not wrote_g:
        block = delete_exact_line_containing(block, placeholder_grp_line)

    block = block.replace(marker_addr, "").replace(marker_grp, "")

    pop_line(policy_lines, idx)
    return block, policy_lines


def ldap_extract_cn(dn: str) -> str:
    core = strip_outer_quotes(dn.strip())
    m = re.search(r"\bCN=([^,]+)", core)
    if m:
        return m.group(1)
    if "/" in core:
        return core.split("/")[-1]
    return core


def process_source_user(
    block: str,
    policy_lines: List[str],
    logger: logging.Logger,
    ldap_profile_name: str,
    ldap_groups: set,
    ldap_users: set,
) -> Tuple[str, List[str]]:
    if not ldap_profile_name:
        block = delete_block_including(block, "/*begin sub-section access-policies-source-user*/", "/*end sub-section access-policies-source-user*/")
        return block, policy_lines

    idx = find_first_line_with_keyword(policy_lines, "source-user")
    if idx is None:
        block = delete_block_including(block, "/*begin sub-section access-policies-source-user*/", "/*end sub-section access-policies-source-user*/")
        return block, policy_lines

    ln = policy_lines[idx]
    objs = parse_list_or_single(extract_after_keyword(ln, "source-user"))
    if not objs or (len(objs) == 1 and strip_outer_quotes(objs[0]) == "any"):
        pop_line(policy_lines, idx)
        block = delete_block_including(block, "/*begin sub-section access-policies-source-user*/", "/*end sub-section access-policies-source-user*/")
        return block, policy_lines

    block = block.replace("@access-policy-source-group-ldap-profile", ldap_profile_name)

    def dup_subsub(txt: str, base: str, num: int) -> str:
        bx = f"/*begin sub-sub-section {base}_x*/"
        ex = f"/*end sub-sub-section {base}_x*/"
        fb = find_block(txt, bx, ex)
        if not fb:
            return txt
        _, e, templ = fb

        pat = re.compile(r"/\*begin sub-sub-section " + re.escape(base) + r"_(\d+)\*/")
        nums = [int(m.group(1)) for m in pat.finditer(txt)]
        if nums:
            last = max(nums)
            bl = f"/*begin sub-sub-section {base}_{last}*/"
            el = f"/*end sub-sub-section {base}_{last}*/"
            fb2 = find_block(txt, bl, el)
            insert_at = fb2[1] if fb2 else e
        else:
            insert_at = e

        newb = templ.replace(f"{base}_x", f"{base}_{num}")
        return txt[:insert_at] + newb + txt[insert_at:]

    grp_num = 1
    usr_num = 1

    for obj in objs:
        obj_raw = obj.strip()
        k1 = obj_raw
        k2 = strip_outer_quotes(obj_raw)

        if k1 in ldap_groups or k2 in ldap_groups:
            block = dup_subsub(block, "access-policies-source-group-user", grp_num)
            grp_num += 1
            block = replace_rightmost_marker(block, "@access-policy-source-group-dn", obj_raw)
            cn = ldap_extract_cn(obj_raw)
            block = replace_rightmost_marker(block, "@access-policy-source-group-description", f"\"{cn}\"")
            continue

        if k1 in ldap_users or k2 in ldap_users:
            block = dup_subsub(block, "access-policies-source-each-user", usr_num)
            usr_num += 1
            block = replace_rightmost_marker(block, "@access-policy-source-user-dn", obj_raw)
            cn = ldap_extract_cn(obj_raw)
            dn_noq = strip_outer_quotes(obj_raw)
            combined = f"{cn} {dn_noq}"
            block = replace_rightmost_marker(block, "@access-policy-source-user-id", f"\"{combined}\"")
            continue

    block = delete_block_including(block, "/*begin sub-sub-section access-policies-source-each-user_x*/", "/*end sub-sub-section access-policies-source-each-user_x*/")
    block = delete_block_including(block, "/*begin sub-sub-section access-policies-source-group-user_x*/", "/*end sub-sub-section access-policies-source-group-user_x*/")

    block = delete_delimiter_lines_by_regex(block, [
        r'^[ \t]*/\*begin sub-sub-section access-policies-source-each-user_\d+\*/[ \t]*\r?\n?$',
        r'^[ \t]*/\*end sub-sub-section access-policies-source-each-user_\d+\*/[ \t]*\r?\n?$',
        r'^[ \t]*/\*begin sub-sub-section access-policies-source-group-user_\d+\*/[ \t]*\r?\n?$',
        r'^[ \t]*/\*end sub-sub-section access-policies-source-group-user_\d+\*/[ \t]*\r?\n?$',
    ])

    block = delete_only_delim_lines(block, "/*begin sub-section access-policies-source-user*/", "/*end sub-section access-policies-source-user*/")
    block = delete_only_delim_lines(block, "/*begin sub-section access-policies-match-source*/", "/*end sub-section access-policies-match-source*/")

    pop_line(policy_lines, idx)
    return block, policy_lines


def delete_block_by_delims_inside(section: str, begin: str, end: str) -> str:
    lines = section.splitlines(True)
    b_pat = re.compile(r'^[ \t]*' + re.escape(begin) + r'[ \t]*\r?\n?$')
    e_pat = re.compile(r'^[ \t]*' + re.escape(end) + r'[ \t]*\r?\n?$')
    start = end_i = None
    for i, ln in enumerate(lines):
        if start is None and b_pat.match(ln):
            start = i
            continue
        if start is not None and e_pat.match(ln):
            end_i = i
            break
    if start is None or end_i is None:
        return section
    return "".join(lines[:start] + lines[end_i + 1:])


def process_security_profiles(block: str, policy_lines: List[str], logger: logging.Logger) -> str:
    keys = [
        "profile-setting profiles virus",
        "profile-setting profiles spyware",
        "profile-setting profiles vulnerability",
        "profile-setting profiles file-blocking",
        "profile-setting profiles url-filtering",
    ]
    has_any = any(any(k in ln for ln in policy_lines) for k in keys)

    if not has_any:
        block = delete_block_by_delims_inside(block, "/*begin sub-section access-policies-set-security-profile*/", "/*end sub-section access-policies-set-security-profile*/")
        logger.info("No security profiles found; removed set-security-profile subsection.")
        return block

    if not any("profile-setting profiles virus" in ln for ln in policy_lines):
        block = delete_block_by_delims_inside(block, "/*begin sub-section access-policies-set-av*/", "/*end sub-section access-policies-set-av*/")

    if not (any("profile-setting profiles spyware" in ln for ln in policy_lines) or any("profile-setting profiles vulnerability" in ln for ln in policy_lines)):
        block = delete_block_by_delims_inside(block, "/*begin sub-section access-policies-set-ips*/", "/*end sub-section access-policies-set-ips*/")

    if not any("profile-setting profiles file-blocking" in ln for ln in policy_lines):
        block = delete_block_by_delims_inside(block, "/*begin sub-section access-policies-set-file*/", "/*end sub-section access-policies-set-file*/")

    idx = find_first_line_with_keyword(policy_lines, "profile-setting profiles url-filtering")
    if idx is None:
        block = delete_block_by_delims_inside(block, "/*begin sub-section access-policies-set-urlf*/", "/*end sub-section access-policies-set-urlf*/")
    else:
        ln = policy_lines[idx]
        after = extract_after_keyword(ln, "profile-setting profiles url-filtering")
        prof = after.split(None, 1)[0] if after else ""
        if prof:
            block = block.replace("@access-policy-set-urlf-profile", prof)
        else:
            block = delete_block_by_delims_inside(block, "/*begin sub-section access-policies-set-urlf*/", "/*end sub-section access-policies-set-urlf*/")

    return block


def process_services(block: str, policy_lines: List[str], svc_map: Dict[str, str]) -> Tuple[str, List[str]]:
    idx = find_first_line_with_keyword(policy_lines, " service ")
    if idx is None or (not os.path.exists(PREDEF_SVC_CONV_FILE)) or (not svc_map):
        block = delete_block_including(block, "/*begin sub-section access-policies-match-services*/", "/*end sub-section access-policies-match-services*/")
        return block, policy_lines

    ln = policy_lines[idx]
    targets = parse_list_or_single(extract_after_keyword(ln, " service "))
    if not targets or (len(targets) == 1 and strip_outer_quotes(targets[0]) == "any"):
        pop_line(policy_lines, idx)
        block = delete_block_including(block, "/*begin sub-section access-policies-match-services*/", "/*end sub-section access-policies-match-services*/")
        return block, policy_lines

    predef, custom = [], []
    for t in targets:
        t2 = strip_outer_quotes(t)
        if t2 == "any":
            continue
        if t2 in svc_map:
            cv = svc_map[t2]
            predef.append(cv if cv else t2)
        else:
            custom.append(t2)

    if predef:
        block = block.replace("@access-policy-predef-service", " ".join(predef))
    else:
        block = delete_exact_line_containing(block, "predefined-services-list [ @access-policy-predef-service ];")

    if custom:
        block = block.replace("@access-policy-custom-service", " ".join(custom))
    else:
        block = delete_exact_line_containing(block, "services-list            [ @access-policy-custom-service ];")

    block = block.replace("@access-policy-predef-service", "").replace("@access-policy-custom-service", "")

    block = delete_only_delim_lines(block, "/*begin sub-section access-policies-match-predef-services*/", "/*end sub-section access-policies-match-predef-services*/")
    block = delete_only_delim_lines(block, "/*begin sub-section access-policies-match-custom-services*/", "/*end sub-section access-policies-match-custom-services*/")
    block = delete_only_delim_lines(block, "/*begin sub-section access-policies-match-services*/", "/*end sub-section access-policies-match-services*/")

    pop_line(policy_lines, idx)
    return block, policy_lines


def is_all_caps_word(s: str) -> bool:
    has_alpha = False
    for ch in s:
        if ch.isalpha():
            has_alpha = True
            if not ch.isupper():
                return False
    return has_alpha


def process_applications(block: str, policy_lines: List[str], logger: logging.Logger, app_map: Dict[str, str]) -> Tuple[str, List[str]]:
    idx = find_first_line_with_keyword(policy_lines, " application ")
    if idx is None or (not os.path.exists(PREDEF_APP_CONV_FILE)) or (os.path.getsize(PREDEF_APP_CONV_FILE) == 0) or (not app_map):
        block = delete_block_including(block, "/*begin sub-section access-policies-match-applications*/", "/*end sub-section access-policies-match-applications*/")
        return block, policy_lines

    ln = policy_lines[idx]
    targets = parse_list_or_single(extract_after_keyword(ln, " application "))
    if not targets or (len(targets) == 1 and strip_outer_quotes(targets[0]) == "any"):
        pop_line(policy_lines, idx)
        block = delete_block_including(block, "/*begin sub-section access-policies-match-applications*/", "/*end sub-section access-policies-match-applications*/")
        return block, policy_lines

    predef_apps: List[str] = []
    predef_group_apps: List[str] = []

    os.makedirs(os.path.dirname(UNSUPPORTED_APPS_FILE), exist_ok=True)

    for t in targets:
        t_clean = strip_outer_quotes(t.strip())
        if not t_clean or t_clean == "any":
            continue

        if t_clean in app_map:
            converted = app_map[t_clean].strip()
            if not converted:
                predef_apps.append(t_clean)
            else:
                if is_all_caps_word(converted):
                    predef_apps.append(converted)
                else:
                    predef_group_apps.append(converted)
        else:
            with open(UNSUPPORTED_APPS_FILE, "a", encoding="utf-8") as f:
                f.write(ln if ln.endswith("\n") else ln + "\n")

    for j, val in enumerate(predef_apps):
        if "@access-policy-predef-applications" not in block:
            break
        if j > 0:
            block = duplicate_marker_to_right(block, "@access-policy-predef-applications")
        block = replace_rightmost_marker(block, "@access-policy-predef-applications", val)

    for j, val in enumerate(predef_group_apps):
        if "@access-policy-predef-group-applications" not in block:
            break
        if j > 0:
            block = duplicate_marker_to_right(block, "@access-policy-predef-group-applications")
        block = replace_rightmost_marker(block, "@access-policy-predef-group-applications", val)

    block = delete_exact_line_containing(block, "predefined-application-list [ @access-policy-predef-applications ];")
    block = delete_exact_line_containing(block, "predefined-group-list       [ @access-policy-predef-group-applications ];")

    block = block.replace("@access-policy-predef-applications", "")
    block = block.replace("@access-policy-predef-group-applications", "")

    block = delete_only_delim_lines(block, "/*begin sub-section access-policies-match-applications*/", "/*end sub-section access-policies-match-applications*/")

    pop_line(policy_lines, idx)
    return block, policy_lines


def mark_unresolved_and_disable_policy(policy_name: str, original_line: str, target_word: str, logger: logging.Logger):
    os.makedirs(os.path.dirname(UNRESOLVED_CUSTOM_URL_CFG), exist_ok=True)
    unresolved_line = original_line.rstrip("\n") + f" <<UNRESOLVED {target_word}\n"
    with open(UNRESOLVED_CUSTOM_URL_CFG, "a", encoding="utf-8") as f:
        f.write(unresolved_line)

    if not os.path.exists(PAN_INPUT):
        return

    pan_lines = read_lines(PAN_INPUT)
    new_pan = []
    for ln in pan_lines:
        if ln == original_line:
            continue
        if policy_name and line_belongs_to_policy(ln, policy_name) and " disabled " in ln:
            ln = re.sub(r"\bdisabled\s+\S+", "disabled yes", ln)
        new_pan.append(ln)
    write_text(PAN_INPUT, "".join(new_pan))
    logger.info("UNRESOLVED category %r for policy %r; removed category line and forced disabled yes.", target_word, policy_name)


def process_url_category(block: str, policy_lines: List[str], logger: logging.Logger, policy_name: str, custom_url_categories: set) -> Tuple[str, List[str]]:
    if not cleaned_pan_has_urlf_profile_setting(PAN_INPUT):
        block = delete_block_including(block, "/*begin sub-section access-policies-match-url-category*/", "/*end sub-section access-policies-match-url-category*/")
        return block, policy_lines

    idx = find_first_line_with_keyword(policy_lines, " category ")
    if idx is None:
        block = delete_block_including(block, "/*begin sub-section access-policies-match-url-category*/", "/*end sub-section access-policies-match-url-category*/")
        return block, policy_lines

    ln = policy_lines[idx]
    targets = parse_list_or_single(extract_after_keyword(ln, " category "))
    if not targets or (len(targets) == 1 and strip_outer_quotes(targets[0]) == "any"):
        block = delete_block_including(block, "/*begin sub-section access-policies-match-url-category*/", "/*end sub-section access-policies-match-url-category*/")
        pop_line(policy_lines, idx)
        return block, policy_lines

    for t in targets:
        target = strip_outer_quotes(t.strip())
        if not target or target == "any":
            continue
        if target not in custom_url_categories:
            mark_unresolved_and_disable_policy(policy_name, ln, target, logger)
            pop_line(policy_lines, idx)
            block = delete_block_including(block, "/*begin sub-section access-policies-match-url-category*/", "/*end sub-section access-policies-match-url-category*/")
            return block, policy_lines

    filled = 0
    for t in targets:
        target = strip_outer_quotes(t.strip())
        if not target or target == "any":
            continue
        if "@access-policy-custom-url-category" not in block:
            break
        if filled > 0:
            block = duplicate_marker_to_right(block, "@access-policy-custom-url-category")
        block = replace_rightmost_marker(block, "@access-policy-custom-url-category", target)
        filled += 1

    block = block.replace("@access-policy-custom-url-category", "")
    block = delete_only_delim_lines(block, "/*begin sub-section access-policies-match-url-category*/", "/*end sub-section access-policies-match-url-category*/")
    block = delete_only_delim_lines(block, "/*begin sub-section access-policies-match*/", "/*end sub-section access-policies-match*/")

    pop_line(policy_lines, idx)
    return block, policy_lines


def process_single_policy_into_cfg_section(
    section_text: str,
    policy_name: str,
    policy_lines: List[str],
    logger: logging.Logger,
    ldap_profile_name: str,
    zone_map: Dict[str, str],
    svc_map: Dict[str, str],
    app_map: Dict[str, str],
    addr_group_names: set,
    ldap_groups: set,
    ldap_users: set,
    custom_url_categories: set,
) -> str:
    block = section_text


    block = block.replace("@access-policy-name", policy_name)


    d_idx = find_first_line_with_keyword(policy_lines, " description ")
    if d_idx is not None:
        ln = pop_line(policy_lines, d_idx)
        after = extract_after_keyword(ln, " description ").strip()
        if after:
            if not after.startswith('"'):
                after = '"' + after
            if not after.endswith('"'):
                after = after + '"'
            inner = after[1:-1]
            inner = sanitize_description_inner(inner)
            after2 = '"' + inner + '"'
            block = block.replace("@access-policy-description", after2)
        else:
            block = delete_exact_line_containing(block, "description  @access-policy-description;")
    else:
        block = delete_exact_line_containing(block, "description  @access-policy-description;")


    dis_idx = find_first_line_with_keyword(policy_lines, " disabled yes")
    if dis_idx is not None:
        pop_line(policy_lines, dis_idx)
        block = block.replace("@access-policy-disable", "true")
    else:
        block = delete_exact_line_containing(block, "rule-disable @access-policy-disable;")


    tag_idx = find_first_line_with_keyword(policy_lines, " tag ")
    if tag_idx is not None:
        ln = pop_line(policy_lines, tag_idx)
        after = extract_after_keyword(ln, " tag ").strip()
        if after:
            tag_val = sanitize_policy_tag(after)
            if tag_val:
                block = block.replace("@access-policy-tag", tag_val)
            else:
                block = delete_exact_line_containing(block, "tag          [ @access-policy-tag ];")
        else:
            block = delete_exact_line_containing(block, "tag          [ @access-policy-tag ];")
    else:
        block = delete_exact_line_containing(block, "tag          [ @access-policy-tag ];")


    act_idx = find_first_line_with_keyword(policy_lines, " action ")
    if act_idx is not None:
        ln = pop_line(policy_lines, act_idx)
        word = extract_after_keyword(ln, " action ").split(None, 1)[0] if extract_after_keyword(ln, " action ") else ""
        block = block.replace("@access-policy-action", "allow" if word == "allow" else "deny")
    else:
        block = block.replace("@access-policy-action", "deny")


    block = process_security_profiles(block, policy_lines, logger)


    block, policy_lines = process_zone_match(
        block, policy_lines,
        " from ",
        "/*begin sub-section access-policies-source-zone*/",
        "/*end sub-section access-policies-source-zone*/",
        "@access-policy-source-zone",
        zone_map,
    )


    block, policy_lines = process_address_split(
        block, policy_lines,
        " source ",
        "/*begin sub-section access-policies-source-address*/",
        "/*end sub-section access-policies-source-address*/",
        "@access-policy-source-address",
        "@access-policy-source-group-address",
        addr_group_names,
        "address-list       [ @access-policy-source-address ];",
        "address-group-list [ @access-policy-source-group-address ];",
    )


    block, policy_lines = process_source_user(block, policy_lines, logger, ldap_profile_name, ldap_groups, ldap_users)


    block, policy_lines = process_zone_match(
        block, policy_lines,
        " to ",
        "/*begin sub-section access-policies-destination-zone*/",
        "/*end sub-section access-policies-destination-zone*/",
        "@access-policy-dest-zone",
        zone_map,
    )
    block = block.replace("@access-policy-dest-zone", "")


    block, policy_lines = process_address_split(
        block, policy_lines,
        " destination ",
        "/*begin sub-section access-policies-destination-address*/",
        "/*end sub-section access-policies-destination-address*/",
        "@access-policy-dest-address",
        "@access-policy-dest-group-address",
        addr_group_names,
        "address-list       [ @access-policy-dest-address ];",
        "address-group-list [ @access-policy-dest-group-address ];",
    )
    block = delete_only_delim_lines(block, "/*begin sub-section access-policies-match-destination*/", "/*end sub-section access-policies-match-destination*/")


    block, policy_lines = process_services(block, policy_lines, svc_map)


    block, policy_lines = process_applications(block, policy_lines, logger, app_map)


    block, policy_lines = process_url_category(block, policy_lines, logger, policy_name, custom_url_categories)


    block = re.sub(r"@[\w\-]+", "", block)
    return block


def final_cleanup(cfg_text: str) -> str:
    cfg_text = delete_block_including(cfg_text, "/*begin section access-policies-rules_x*/", "/*end section access-policies-rules_x*/")
    cfg_text = delete_only_delim_lines(cfg_text, "/*begin main-section access-policies*/", "/*end main-section access-policies*/")

    cfg_text = delete_delimiter_lines_by_regex(cfg_text, [
        r'^[ \t]*/\*begin section access-policies-rules_\d+\*/[ \t]*\r?\n?$',
        r'^[ \t]*/\*end section access-policies-rules_\d+\*/[ \t]*\r?\n?$',
        r'^[ \t]*/\*begin sub-section access-policies-match\*/[ \t]*\r?\n?$',
        r'^[ \t]*/\*end sub-section access-policies-match\*/[ \t]*\r?\n?$',
        r'^[ \t]*/\*begin sub-section access-policies-set\*/[ \t]*\r?\n?$',
        r'^[ \t]*/\*end sub-section access-policies-set\*/[ \t]*\r?\n?$',
    ])

    cfg_text = remove_empty_list_lines(cfg_text)
    cfg_text = remove_empty_users_groups_blocks(cfg_text)
    return cfg_text


def main():
    logger = setup_logger()
    sys.stdout = StreamToLogger(logger, logging.INFO)
    sys.stderr = StreamToLogger(logger, logging.ERROR)

    try:
        os.makedirs(TEMP_DIR, exist_ok=True)
        os.makedirs(FINAL_DATA_DIR, exist_ok=True)

        if not os.path.exists(PAN_INPUT):
            raise FileNotFoundError(f"Missing input: {PAN_INPUT}")
        if not os.path.exists(SVT_TEMPLATE):
            raise FileNotFoundError(f"Missing template: {SVT_TEMPLATE}")

        tenant = input("Please enter the TENANT name for the service template: ").strip()
        template_name = input("Please enter the service template: ").strip()
        if not template_name:
            raise RuntimeError("Service template name cannot be empty.")

        ldap_profile_name = input_with_timeout(
            "If you're using LDAP, please enter the LDAP proifile name now. Press Enter if you're not using LDAP.: ",
            30, logger, default=""
        ).strip()
        if ldap_profile_name.lower() in ("no", "n"):
            ldap_profile_name = ""

        logger.info("Inputs: tenant=%r template=%r ldap_profile=%r", tenant, template_name, ldap_profile_name)


        safe_copy(PAN_INPUT, TEMP_PAN, logger)

        zone_map = load_mapping(ZONE_CONV_FILE, logger)
        svc_map = load_mapping(PREDEF_SVC_CONV_FILE, logger)
        app_map = load_mapping(PREDEF_APP_CONV_FILE, logger)

        addr_group_names = load_address_group_names(FINAL_ADDR_GRP_FILE, logger)
        ldap_groups = load_set(LDAP_GROUPS_FILE, logger) if ldap_profile_name else set()
        ldap_users = load_set(LDAP_USERS_FILE, logger) if ldap_profile_name else set()
        custom_url_categories = load_custom_url_categories(FINAL_CUSTOM_URLF_PROFILE, logger)

        cfg_text = read_text(SVT_TEMPLATE)
        cfg_text = cfg_text.replace("@template-name", template_name)
        cfg_text = cfg_text.replace("@tenant", tenant)

        base_section = "access-policies-rules"
        counter = 1

        pan_lines = read_lines(TEMP_PAN)

        while True:
            policy_name, pol_block, remaining = pop_next_policy(pan_lines, logger)
            if not policy_name:
                break

            cfg_text, used_n = duplicate_section(cfg_text, base_section, logger, counter)
            s_start, s_end, s_text = find_numbered_section(cfg_text, base_section, used_n)

            processed = process_single_policy_into_cfg_section(
                s_text,
                policy_name,
                pol_block,
                logger,
                ldap_profile_name,
                zone_map,
                svc_map,
                app_map,
                addr_group_names,
                ldap_groups,
                ldap_users,
                custom_url_categories,
            )
            cfg_text = cfg_text[:s_start] + processed + cfg_text[s_end:]

            pan_lines = remaining
            counter += 1
            write_text(TEMP_PAN, "".join(pan_lines))


        cfg_text = sanitize_all_description_lines(cfg_text)
        cfg_text = dedupe_predefined_application_list_lines(cfg_text)
        cfg_text = dedupe_service_list_lines(cfg_text)
        cfg_text = final_cleanup(cfg_text)

        out_path = os.path.join(FINAL_DATA_DIR, f"your-final-templte.cfg")
        write_text(out_path, cfg_text)
        logger.info("Wrote output: %s", out_path)


        safe_remove_dir(os.path.join(MAIN_DIR, "final-step"), logger)
        safe_remove_dir(TEMP_DIR, logger)

        logger.info("Completed successfully.")

    except Exception as e:
        logger.error("FAILED: %s", e)
        logger.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    main()