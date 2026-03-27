import os
import re
import sys
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

def sanitize_description_lines_in_cfg(cfg: str) -> str:
    out_lines = []
    for ln in cfg.splitlines():
        if 'description "' in ln and ";" in ln:
            sem_i = ln.rfind(";")
            first_q = ln.find('"', ln.find('description "') + len('description '))
            last_q = ln.rfind('"', 0, sem_i)
            if first_q != -1 and last_q != -1 and last_q > first_q:
                inner = ln[first_q + 1:last_q]
                if '"' in inner:
                    inner = inner.replace('"', "")
                    ln = ln[:first_q + 1] + inner + ln[last_q:]
        out_lines.append(ln)
    return "\n".join(out_lines) + ("\n" if cfg.endswith("\n") else "")


class TeeToFile:
    def __init__(self, logfile_path: str):
        self._fh = open(logfile_path, "a", encoding="utf-8", errors="replace")

    def write(self, msg: str) -> None:
        if msg:
            msg = sanitize_description_lines_in_cfg(msg)
            sys.__stdout__.write(msg)
            sys.__stdout__.flush()
            msg = sanitize_description_lines_in_cfg(msg)
            self._fh.write(msg)
            self._fh.flush()

    def flush(self) -> None:
        sys.__stdout__.flush()
        self._fh.flush()

    def close(self) -> None:
        try:
            self._fh.close()
        except Exception:
            pass

def now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log(msg: str) -> None:
    print(f"[{now_stamp()}] {msg}")

def script_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))

def main_dir() -> str:
    return os.path.abspath(os.path.join(script_dir(), ".."))

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def file_exists_and_not_empty(path: str) -> bool:
    return os.path.isfile(path) and os.path.getsize(path) > 0

def read_lines(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.readlines()

def write_lines(path: str, lines: List[str]) -> None:
    with open(path, "w", encoding="utf-8", errors="replace") as f:
        f.writelines(lines)

def append_unique_line(path: str, line: str) -> None:
    line = line.strip()
    if not line:
        return
    existing: Set[str] = set()
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for l in f:
                existing.add(l.strip())
    if line not in existing:
        with open(path, "a", encoding="utf-8", errors="replace") as f:
            f.write(line + "\n")

def strip_nl(s: str) -> str:
    return s[:-1] if s.endswith("\n") else s

def dedup_preserve_order(items: List[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

def find_block_by_delims_stripped(lines: List[str],
                                 begin_stripped: str,
                                 end_stripped: str,
                                 start_idx: int = 0,
                                 end_limit: Optional[int] = None) -> Optional[Tuple[int, int]]:
    if end_limit is None:
        end_limit = len(lines) - 1

    b = None
    for i in range(start_idx, end_limit + 1):
        if lines[i].strip() == begin_stripped:
            b = i
            break
    if b is None:
        return None

    for j in range(b + 1, end_limit + 1):
        if lines[j].strip() == end_stripped:
            return (b, j)
    return None

def delete_block_by_delims_stripped(lines: List[str],
                                   begin_stripped: str,
                                   end_stripped: str) -> bool:
    span = find_block_by_delims_stripped(lines, begin_stripped, end_stripped)
    if not span:
        return False
    b, e = span
    del lines[b:e+1]
    return True

def delete_all_blocks_by_delims_stripped(lines: List[str],
                                        begin_stripped: str,
                                        end_stripped: str) -> int:
    cnt = 0
    while delete_block_by_delims_stripped(lines, begin_stripped, end_stripped):
        cnt += 1
    return cnt

def copy_block_lines(lines: List[str], b: int, e: int) -> List[str]:
    return lines[b:e+1]

def find_max_indexed_delim(lines: List[str],
                          begin_prefix: str,
                          within: Tuple[int, int]) -> int:
    lo, hi = within
    mx = -1
    rx = re.compile(rf"^{re.escape(begin_prefix)}_(\d+)\*/$")
    for i in range(lo, hi + 1):
        m = rx.match(lines[i].strip())
        if m:
            mx = max(mx, int(m.group(1)))
    return mx

def find_last_end_delim_idx(lines: List[str],
                            end_prefix: str,
                            within: Tuple[int, int]) -> Optional[int]:
    lo, hi = within
    rx_n = re.compile(rf"^{re.escape(end_prefix)}_(\d+)\*/$")
    target_x = f"{end_prefix}_x*/"
    last = None
    for i in range(lo, hi + 1):
        s = lines[i].strip()
        if s == target_x or rx_n.match(s):
            last = i
    return last

def renumber_x_to_n(block: List[str],
                    begin_prefix: str,
                    end_prefix: str,
                    n: int) -> List[str]:
    begin_x = f"{begin_prefix}_x*/"
    end_x = f"{end_prefix}_x*/"
    begin_n = f"{begin_prefix}_{n}*/"
    end_n = f"{end_prefix}_{n}*/"

    out = []
    for ln in block:
        s = ln.strip()
        if s == begin_x:
            indent = ln[:len(ln) - len(ln.lstrip())]
            out.append(indent + begin_n + ("\n" if ln.endswith("\n") else ""))
        elif s == end_x:
            indent = ln[:len(ln) - len(ln.lstrip())]
            out.append(indent + end_n + ("\n" if ln.endswith("\n") else ""))
        else:
            out.append(ln)
    return out

def tokenize_pan_tail(tail: str) -> List[str]:
    tokens: List[str] = []
    i = 0
    n = len(tail)
    while i < n:
        c = tail[i]
        if c.isspace():
            i += 1
            continue
        if c in "[]":
            i += 1
            continue
        if c == '"':
            j = i + 1
            out = []
            while j < n:
                if tail[j] == '"' and tail[j - 1] != "\\":
                    break
                out.append(tail[j])
                j += 1
            tokens.append("".join(out))
            i = j + 1
            continue
        j = i
        while j < n and (not tail[j].isspace()) and tail[j] not in "[]":
            j += 1
        tokens.append(tail[i:j])
        i = j

    return [t.strip() for t in tokens if t.strip()]

# ─── CHANGED: prefix from "set shared profiles url-filtering" ───
def parse_urlf_object_name(line: str) -> Optional[str]:
    prefix = "webfilter profile"                                     # CHANGED
    if not line.startswith(prefix):
        return None
    rest = line[len(prefix):].lstrip()
    if not rest:
        return None
    if rest.startswith('"'):
        m = re.match(r'"((?:[^"\\]|\\.)*)"\s*(.*)$', rest)
        if not m:
            return None
        return m.group(1).replace('\\"', '"')
    parts = rest.split(None, 1)
    return parts[0] if parts else None

# ─── CHANGED: keyword from "description" to "comment" ───
MAX_DESC_LEN = 63

def clean_and_truncate_description(raw: str) -> str:
    """Strip outer quotes, remove non-printable chars, collapse whitespace,
       truncate inner text to MAX_DESC_LEN chars, re-wrap in double-quotes."""
    # strip outer double-quotes if present
    inner = raw.strip()
    if inner.startswith('"') and inner.endswith('"'):
        inner = inner[1:-1]
    # remove embedded double-quotes
    inner = inner.replace('"', '')
    # remove non-printable / control characters (keep printable ASCII + common extended)
    inner = re.sub(r'[^\x20-\x7E]', '', inner)
    # collapse multiple spaces into one and strip
    inner = re.sub(r'\s+', ' ', inner).strip()
    # truncate to max length
    if len(inner) > MAX_DESC_LEN:
        inner = inner[:MAX_DESC_LEN]
    # return wrapped in double-quotes
    if not inner:
        return None
    return '"' + inner + '"'

def parse_description_value(line: str) -> Optional[str]:
    if " comment" not in line:                                       # CHANGED
        return None
    m = re.search(r"\scomment\s+(.*)$", line)                       # CHANGED
    if not m:
        return None
    tail = m.group(1).strip()
    if not tail:
        return None
    if tail.startswith('"'):
        m2 = re.match(r'"((?:[^"\\]|\\.)*)"', tail)
        if m2:
            return clean_and_truncate_description('"' + m2.group(1).replace('\\"', '"') + '"')
        return clean_and_truncate_description('"' + tail.replace('"', '\\"') + '"')
    return clean_and_truncate_description('"' + tail.replace('"', '\\"') + '"')

def parse_tag_value(line: str) -> Optional[str]:
    if " tag " not in line:
        return None
    m = re.search(r"\stag\s+(.*)$", line)
    if not m:
        return None
    tail = m.group(1).strip()
    if not tail:
        return None
    if tail.startswith('"'):
        m2 = re.match(r'"((?:[^"\\]|\\.)*)"', tail)
        if m2:
            return m2.group(1).replace('\\"', '"')
    return tail.split()[0]

# ─── CHANGED: rewritten for Fortinet ftgd-wf + urlfilter-table format ───
# Fortinet action-to-Versa action mapping:
#   Fortinet "allow"   -> Versa "allow"
#   Fortinet "block"   -> Versa "block"
#   Fortinet "monitor" -> Versa "alert"
#   Fortinet "warning" -> Versa "justify"
# Fortinet urlfilter-table references -> Versa "block" user-defined
FORTI_ACTION_MAP = {
    "allow":   "allow",
    "block":   "block",
    "monitor": "alert",
    "warning": "justify",
}

def classify_action_line(line: str, obj_name: str) -> Optional[Tuple[str, List[str]]]:
    # ─── Fortinet ftgd-wf line ───
    # Format: webfilter profile <name> ftgd-wf filter <N> category <id> action <action>
    m = re.search(r"\sftgd-wf\s+filter\s+\d+\s+category\s+(\S+)\s+action\s+(\S+)", line)
    if m:
        cat_id = m.group(1)
        forti_action = m.group(2).lower()
        versa_action = FORTI_ACTION_MAP.get(forti_action)
        if versa_action:
            return (versa_action, [cat_id])
        return None

    # ─── Fortinet urlfilter-table line ───
    # Format: webfilter profile <name> urlfilter-table "<table-name>"
    #         or: webfilter profile <name> urlfilter-table <table-name>
    m = re.search(r"\surlfilter-table\s+(.+)$", line)
    if m:
        tail = m.group(1).strip()
        if tail.startswith('"'):
            m2 = re.match(r'"((?:[^"\\]|\\.)*)"', tail)
            if m2:
                table_name = m2.group(1).replace('\\"', '"')
            else:
                table_name = tail.strip('"')
        else:
            table_name = tail.split()[0]
        if table_name:
            return ("block", [table_name])
        return None

    return None

# ─── CHANGED: prefix from "set shared profiles custom-url-category" ───
def load_custom_category_names(path: str) -> Set[str]:
    names: Set[str] = set()
    if not os.path.isfile(path):
        return names
    prefix = "webfilter urlfilter"                                   # CHANGED
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.strip()
            if not line.startswith(prefix):
                continue
            rest = line[len(prefix):].lstrip()
            if not rest:
                continue
            if rest.startswith('"'):
                m = re.match(r'"((?:[^"\\]|\\.)*)"', rest)
                if m:
                    names.add(m.group(1).replace('\\"', '"'))
            else:
                parts = rest.split()
                if parts:
                    names.add(parts[0])
    return names

# ─── UNCHANGED: mapping file format stays the same (key >> value) ───
def load_pan_to_versa_mapping(path: str) -> Dict[str, str]:
    mp: Dict[str, str] = {}
    if not os.path.isfile(path):
        return mp
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or ">>" not in line:
                continue
            parts = line.split(">>")                                 # CHANGED: was split(">>", 1)
            if len(parts) < 2:
                continue
            key = parts[0].strip().split()[0]                        # category ID (e.g. "1")
            right = parts[-1].strip()                                # CHANGED: last segment = Versa name
            if key and right:
                mp[key] = right
    return mp

def aggregate_actions_for_object(obj_name: str, obj_lines: List[str]) -> Dict[str, List[str]]:
    actions: Dict[str, List[str]] = {"justify": [], "allow": [], "alert": [], "block": []}
    for ln in obj_lines:
        cl = classify_action_line(ln, obj_name)
        if not cl:
            continue
        action, toks = cl
        if not toks:
            continue
        actions[action].extend(toks)
    for k in actions:
        actions[k] = dedup_preserve_order(actions[k])
    return actions

def map_tokens(tokens: List[str],
               custom_names: Set[str],
               pan_to_versa: Dict[str, str],
               unknown_path: str) -> Tuple[List[str], List[str]]:
    predefined: List[str] = []
    userdef: List[str] = []
    for tok in tokens:
        if tok in custom_names:
            userdef.append(tok)
        elif tok in pan_to_versa:
            predefined.append(pan_to_versa[tok])
        else:
            append_unique_line(unknown_path, tok)
    return dedup_preserve_order(predefined), dedup_preserve_order(userdef)

def replace_marker_in_range(lines: List[str], rng: Tuple[int, int], marker: str, value: str) -> None:
    lo, hi = rng
    for i in range(lo, hi + 1):
        if marker in lines[i]:
            lines[i] = lines[i].replace(marker, value)

def delete_line_containing_marker_in_range(lines: List[str], rng: Tuple[int, int], marker: str) -> None:
    lo, hi = rng
    del_idx = []
    for i in range(lo, min(hi, len(lines) - 1) + 1):
        if marker in lines[i]:
            del_idx.append(i)
    for i in reversed(del_idx):
        del lines[i]

def delete_placeholder_list_lines_in_range(lines: List[str], rng: Tuple[int, int]) -> None:
    rx_pre = re.compile(r"^\s*predefined\s+\[\s*@urlf-profiles-predefined-category\s*\]\s*;\s*$")
    rx_usr = re.compile(r"^\s*user-defined\s+\[\s*@urlf-profiles-user-category\s*\]\s*;\s*$")

    lo, hi = rng
    del_idx = []
    for i in range(lo, min(hi, len(lines) - 1) + 1):
        s = strip_nl(lines[i])
        if rx_pre.match(s) or rx_usr.match(s):
            del_idx.append(i)
    for i in reversed(del_idx):
        del lines[i]

def write_list_line_in_range(lines: List[str], rng: Tuple[int, int], which: str, values: List[str]) -> None:
    lo, hi = rng
    prefix_key = "predefined" if which == "predefined" else "user-defined"
    rx = re.compile(rf"^(\s*)({re.escape(prefix_key)}\s+\[)\s*(.*?)\s*\]\s*;\s*$")

    for i in range(lo, hi + 1):
        s = strip_nl(lines[i])
        m = rx.match(s)
        if not m:
            continue

        if not values:
            del lines[i]
            return

        indent = m.group(1)
        head = m.group(2)
        content = " ".join(values)
        new_line = f"{indent}{head} {content} ];"
        lines[i] = new_line + ("\n" if lines[i].endswith("\n") else "")
        return

def remove_unused_markers_only(lines: List[str]) -> None:
    markers = ["@urlf-profiles-predefined-category", "@urlf-profiles-user-category"]
    for i in range(len(lines)):
        for m in markers:
            if m in lines[i]:
                lines[i] = lines[i].replace(m, "")

def remove_category_n_delimiter_lines(lines: List[str]) -> None:
    rx_begin = re.compile(r"^\s*/\*begin sub-sub-section urlf-profiles-definition-category_\d+\*/\s*$")
    rx_end = re.compile(r"^\s*/\*end sub-sub-section urlf-profiles-definition-category_\d+\*/\s*$")
    out = []
    for ln in lines:
        s = strip_nl(ln)
        if rx_begin.match(s) or rx_end.match(s):
            continue
        out.append(ln)
    lines[:] = out

def remove_subsection_n_delimiter_lines(lines: List[str]) -> None:
    rx_begin = re.compile(r"^\s*/\*begin sub-section urlf-profiles-definition_\d+\*/\s*$")
    rx_end = re.compile(r"^\s*/\*end sub-section urlf-profiles-definition_\d+\*/\s*$")
    out = []
    for ln in lines:
        s = strip_nl(ln)
        if rx_begin.match(s) or rx_end.match(s):
            continue
        out.append(ln)
    lines[:] = out

def remove_category_x_blocks_and_content(lines: List[str]) -> int:
    return delete_all_blocks_by_delims_stripped(
        lines,
        "/*begin sub-sub-section urlf-profiles-definition-category_x*/",
        "/*end sub-sub-section urlf-profiles-definition-category_x*/",
    )

def remove_template_subsection_x_blocks_and_content(lines: List[str]) -> int:
    return delete_all_blocks_by_delims_stripped(
        lines,
        "/*begin sub-section urlf-profiles-definition_x*/",
        "/*end sub-section urlf-profiles-definition_x*/",
    )

def remove_main_section_delimiter_lines_only(lines: List[str]) -> None:
    out = []
    for ln in lines:
        s = ln.strip()
        if s == "/*begin main-section urlf-profiles*/":
            continue
        if s == "/*end main-section urlf-profiles*/":
            continue
        out.append(ln)
    lines[:] = out

def main() -> int:
    base = main_dir()

    log_dir = os.path.join(base, "log")
    ensure_dir(log_dir)
    log_path = os.path.join(log_dir, "step-8.log")

    tee = TeeToFile(log_path)
    sys.stdout = tee
    sys.stderr = tee

    try:
        log("=== Convert security urlf-profile: START ===")
        log(f"Main dir: {base}")
        log(f"Log file: {log_path}")

        cfg_path = os.path.join(base, "final-data", "svt-temp.cfg")
        final_urlf = os.path.join(base, "final-data", "final-urlf-profile.txt")
        final_custom = os.path.join(base, "final-data", "final-custom-urlf-profile.txt")
        # ─── CHANGED: mapping file name from PAN-to-Versa to Forti-to-Versa ───
        pan_to_versa_path = os.path.join(base, "miscellaneous", "Forti-to-Versa-urlf-categories.txt")
        unknown_path = os.path.join(base, "unknown-urlf-category.txt")

        temp_dir = os.path.join(base, "temp")
        ensure_dir(temp_dir)
        temp_urlf = os.path.join(temp_dir, "temp-urlf-profile.txt")

        if file_exists_and_not_empty(final_urlf):
            log(f"Step #50: copying {final_urlf} -> {temp_urlf}")
            shutil.copyfile(final_urlf, temp_urlf)
        else:
            log(f"Step #50: {final_urlf} missing/empty -> deleting main-section urlf-profiles block in {cfg_path}")
            lines = read_lines(cfg_path)
            delete_block_by_delims_stripped(lines, "/*begin main-section urlf-profiles*/", "/*end main-section urlf-profiles*/")
            write_lines(cfg_path, lines)
            log("=== DONE (no urlf profiles) ===")
            return 0

        if not file_exists_and_not_empty(temp_urlf):
            log("Step #51a: temp urlf file empty -> deleting main-section urlf-profiles block")
            lines = read_lines(cfg_path)
            delete_block_by_delims_stripped(lines, "/*begin main-section urlf-profiles*/", "/*end main-section urlf-profiles*/")
            write_lines(cfg_path, lines)
            log("=== DONE (temp empty) ===")
            return 0

        cfg_lines = read_lines(cfg_path)

        main_span = find_block_by_delims_stripped(cfg_lines, "/*begin main-section urlf-profiles*/", "/*end main-section urlf-profiles*/")
        if not main_span:
            raise RuntimeError("Missing main-section urlf-profiles delimiters.")

        custom_names = load_custom_category_names(final_custom)
        pan_to_versa = load_pan_to_versa_mapping(pan_to_versa_path)
        log(f"Loaded custom-url-category names: {len(custom_names)}")
        log(f"Loaded Forti->Versa mappings: {len(pan_to_versa)}")           # CHANGED log text

        sub_x_span = find_block_by_delims_stripped(
            cfg_lines,
            "/*begin sub-section urlf-profiles-definition_x*/",
            "/*end sub-section urlf-profiles-definition_x*/",
            start_idx=main_span[0],
            end_limit=main_span[1]
        )
        if not sub_x_span:
            raise RuntimeError("Template sub-section _x not found in cfg.")
        sub_x_block = copy_block_lines(cfg_lines, sub_x_span[0], sub_x_span[1])

        with open(temp_urlf, "r", encoding="utf-8", errors="replace") as f:
            pan_lines = [ln.rstrip("\n") for ln in f if ln.strip()]

        objects: Dict[str, List[str]] = {}
        for ln in pan_lines:
            name = parse_urlf_object_name(ln)
            if name:
                objects.setdefault(name, []).append(ln)

        log(f"Found url-filtering objects: {len(objects)}")

        sub_begin_prefix = "/*begin sub-section urlf-profiles-definition"
        sub_end_prefix = "/*end sub-section urlf-profiles-definition"
        max_sub = find_max_indexed_delim(cfg_lines, sub_begin_prefix, main_span)
        next_sub_n = max_sub + 1 if max_sub >= 0 else 0

        for obj_name, obj_lines in objects.items():

            main_span = find_block_by_delims_stripped(cfg_lines, "/*begin main-section urlf-profiles*/", "/*end main-section urlf-profiles*/")
            if not main_span:
                raise RuntimeError("Main section disappeared unexpectedly.")

            last_end_idx = find_last_end_delim_idx(cfg_lines, sub_end_prefix, main_span)
            if last_end_idx is None:
                last_end_idx = sub_x_span[1]

            new_sub_n = next_sub_n
            next_sub_n += 1

            new_sub_block = renumber_x_to_n(sub_x_block, sub_begin_prefix, sub_end_prefix, new_sub_n)
            insert_at = last_end_idx + 1
            cfg_lines[insert_at:insert_at] = new_sub_block

            new_sub_span = find_block_by_delims_stripped(
                cfg_lines,
                f"{sub_begin_prefix}_{new_sub_n}*/",
                f"{sub_end_prefix}_{new_sub_n}*/",
                start_idx=insert_at,
                end_limit=min(len(cfg_lines)-1, insert_at + len(new_sub_block) + 20000)
            )
            if not new_sub_span:
                raise RuntimeError(f"Failed to locate new sub-section {new_sub_n}")

            replace_marker_in_range(cfg_lines, new_sub_span, "@urlf-profiles-name", obj_name)

            desc_val = None
            for ln in obj_lines:
                d = parse_description_value(ln)
                if d:
                    desc_val = d
                    break
            if desc_val:
                replace_marker_in_range(cfg_lines, new_sub_span, "@urlf-profiles-description", desc_val)

            tag_val = None
            for ln in obj_lines:
                t = parse_tag_value(ln)
                if t:
                    tag_val = t
                    break
            if tag_val:
                replace_marker_in_range(cfg_lines, new_sub_span, "@urlf-profiles-tag-name", tag_val)

            delete_line_containing_marker_in_range(cfg_lines, new_sub_span, "@urlf-profiles-description")
            delete_line_containing_marker_in_range(cfg_lines, new_sub_span, "@urlf-profiles-tag-name")

            cat_begin_prefix = "/*begin sub-sub-section urlf-profiles-definition-category"
            cat_end_prefix = "/*end sub-sub-section urlf-profiles-definition-category"

            cat_x_span = find_block_by_delims_stripped(
                cfg_lines,
                "/*begin sub-sub-section urlf-profiles-definition-category_x*/",
                "/*end sub-sub-section urlf-profiles-definition-category_x*/",
                start_idx=new_sub_span[0],
                end_limit=new_sub_span[1]
            )
            if not cat_x_span:
                raise RuntimeError("Missing category template _x inside new profile.")
            cat_x_block = copy_block_lines(cfg_lines, cat_x_span[0], cat_x_span[1])

            max_cat = find_max_indexed_delim(cfg_lines, cat_begin_prefix, new_sub_span)
            next_cat_n = max_cat + 1 if max_cat >= 0 else 0

            actions = aggregate_actions_for_object(obj_name, obj_lines)

            for action in ["justify", "allow", "alert", "block"]:
                tokens = actions.get(action, [])
                if not tokens:
                    continue

                pre_vals, usr_vals = map_tokens(tokens, custom_names, pan_to_versa, unknown_path)

                new_cat_n = next_cat_n
                next_cat_n += 1

                new_sub_span = find_block_by_delims_stripped(
                    cfg_lines,
                    f"{sub_begin_prefix}_{new_sub_n}*/",
                    f"{sub_end_prefix}_{new_sub_n}*/",
                    start_idx=new_sub_span[0],
                    end_limit=min(len(cfg_lines)-1, new_sub_span[1] + 200000)
                )
                if not new_sub_span:
                    raise RuntimeError("Failed to re-locate profile block during category inserts.")

                last_cat_end = find_last_end_delim_idx(cfg_lines, cat_end_prefix, new_sub_span)
                if last_cat_end is None:
                    last_cat_end = cat_x_span[1]

                new_cat_block = renumber_x_to_n(cat_x_block, cat_begin_prefix, cat_end_prefix, new_cat_n)
                insert_cat_at = last_cat_end + 1
                cfg_lines[insert_cat_at:insert_cat_at] = new_cat_block

                new_cat_span = find_block_by_delims_stripped(
                    cfg_lines,
                    f"{cat_begin_prefix}_{new_cat_n}*/",
                    f"{cat_end_prefix}_{new_cat_n}*/",
                    start_idx=insert_cat_at,
                    end_limit=min(len(cfg_lines)-1, insert_cat_at + len(new_cat_block) + 20000)
                )
                if not new_cat_span:
                    raise RuntimeError(f"Failed to locate new category block {new_cat_n}")

                replace_marker_in_range(cfg_lines, new_cat_span, "@urlf-cust-profile-action", action)

                suffix = {
                    "justify": "_action_justify",
                    "allow": "_action_allow",
                    "alert": "_action_alert",
                    "block": "_action_block",
                }[action]
                replace_marker_in_range(cfg_lines, new_cat_span, "@urlf-profiles-category-action-name", obj_name + suffix)

                write_list_line_in_range(cfg_lines, new_cat_span, "predefined", pre_vals)
                write_list_line_in_range(cfg_lines, new_cat_span, "user-defined", usr_vals)

                delete_placeholder_list_lines_in_range(cfg_lines, new_cat_span)

        remove_category_n_delimiter_lines(cfg_lines)
        remove_subsection_n_delimiter_lines(cfg_lines)

        removed_cat_x = remove_category_x_blocks_and_content(cfg_lines)
        log(f"Removed category_x blocks (with content): {removed_cat_x}")

        removed_sub_x = remove_template_subsection_x_blocks_and_content(cfg_lines)
        log(f"Removed sub-section_x template blocks (with content): {removed_sub_x}")

        remove_main_section_delimiter_lines_only(cfg_lines)

        remove_unused_markers_only(cfg_lines)

        write_lines(cfg_path, cfg_lines)
        log(f"Saved updated cfg: {cfg_path}")
        log("=== Convert security urlf-profile: DONE ===")
        return 0

    except Exception as e:
        log(f"ERROR: {e}")
        return 2

    finally:
        try:
            sys.stdout.flush()
            sys.stderr.flush()
        except Exception:
            pass
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        try:
            tee.close()
        except Exception:
            pass

if __name__ == "__main__":
    raise SystemExit(main())