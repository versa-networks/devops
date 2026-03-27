#!/usr/bin/env python3
"""
convert-group.py (Step-8): Convert Fortinet address-group (addrgrp) objects -> Versa config markers in ../final-data/svt-temp.cfg

Directory model:
- Script runs from:          ../scripts/
- Main working directory:    one level above ../scripts/ (../)
- Log directory:             ../log/
- Temp directory:            ../temp/
- Final data directory:      ../final-data/
- Template source:           ../miscellaneous/base-template.cfg

Logging:
- EVERYTHING is logged (stdout + stderr) to: ../log/step-8.log

Key logic:
- CASE-SENSITIVE correlation.
- member can be:  member target-word  OR  member [ w1 w2 ... ]
- tagging can be: tagging target-word OR  tagging [ t1 t2 ... ]
- Description copied with quotes (add quotes if missing).
- Duplicate template block objects-address-group-definition_x to objects-address-group-definition_n.
- If NO resolved members (no address-list AND no address-group-list matches) => SKIP inserting block.
- Cleanup per step 26b/26c/26d.

CRITICAL FIX (your orphan '}' issue):
- When writing updated_block back, replace the ENTIRE original block range:
    svt_lines[block_start:block_end+1] = updated_block
  Not:
    svt_lines[block_start:block_start+len(updated_block)] = updated_block
"""

from __future__ import annotations

import sys
import re
import shlex
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class StreamToLogger:
    def __init__(self, logger: logging.Logger, level: int):
        self.logger = logger
        self.level = level
        self._buf = ""

    def write(self, msg: str) -> None:
        if not msg:
            return
        self._buf += msg
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            if line != "":
                self.logger.log(self.level, line)

    def flush(self) -> None:
        if self._buf.strip():
            self.logger.log(self.level, self._buf.strip())
        self._buf = ""

def setup_logger(log_path: Path) -> logging.Logger:
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("step-8")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    ch = logging.StreamHandler(sys.__stdout__)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)

    sys.stdout = StreamToLogger(logger, logging.INFO)
    sys.stderr = StreamToLogger(logger, logging.ERROR)

    return logger

RE_ADDR_GRP_NAME = re.compile(r'^\s*firewall\s+addrgrp\s+(".*?"|\S+)\b')
RE_ADDR_NAME = re.compile(r'^\s*firewall\s+address\s+(".*?"|\S+)\b')

RE_STATIC_LIST = re.compile(r'\bmember\s+\[(.*?)\]\s*$', re.IGNORECASE)
RE_STATIC_SINGLE = re.compile(r'\bmember\s+(".*?"|\S+)\s*$', re.IGNORECASE)
RE_STATIC_MULTI = re.compile(r'\bmember\s+(.+)\s*$', re.IGNORECASE)

RE_TAG_LIST = re.compile(r'\btagging\s+\[(.*?)\]\s*$', re.IGNORECASE)
RE_TAG_SINGLE = re.compile(r'\btagging\s+(".*?"|\S+)\s*$', re.IGNORECASE)
RE_TAG_MULTI = re.compile(r'\btagging\s+(.+)\s*$', re.IGNORECASE)

RE_DESC = re.compile(r'\bcomment\s+(.+)\s*$', re.IGNORECASE)

BEGIN_ORI = "/*begin sub-section objects-address-group-ori*/"
END_ORI = "/*end sub-section objects-address-group-ori*/"

BEGIN_DEF_X = "/*begin sub-section objects-address-group-definition_x*/"
END_DEF_X = "/*end sub-section objects-address-group-definition_x*/"

BEGIN_DEF_N_RE = re.compile(r"^\s*/\*begin sub-section objects-address-group-definition_(\d+)\*/\s*$")
END_DEF_N_RE = re.compile(r"^\s*/\*end sub-section objects-address-group-definition_(\d+)\*/\s*$")

MARK_ADDR_LIST = "@address-object-group-address-list"
MARK_GRP_LIST = "@address-object-group-address-group-list"
MARK_DESC = "@address-object-group-description"
MARK_TAG = "@address-object-group-tag"
MARK_NAME = "@address-object-group-name"

EXACT_ADDR_LIST_LINE = "address-list       [ @address-object-group-address-list ];"
EXACT_GRP_LIST_LINE = "address-group-list [ @address-object-group-address-group-list ];"

def read_lines(p: Path) -> List[str]:
    return p.read_text(encoding="utf-8", errors="replace").splitlines(True)

def write_lines(p: Path, lines: List[str]) -> None:
    p.write_text("".join(lines), encoding="utf-8")

def missing_or_empty(p: Path) -> bool:
    return (not p.exists()) or (p.exists() and p.stat().st_size == 0)

def strip_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return s[1:-1]
    return s

def shlex_words(s: str) -> List[str]:
    s = s.strip()
    if not s:
        return []
    try:
        parts = shlex.split(s)
        return [strip_quotes(x) for x in parts]
    except Exception:
        return [strip_quotes(x) for x in s.split() if x.strip()]

def extract_name_from_line(line: str, is_group: bool) -> Optional[str]:
    m = RE_ADDR_GRP_NAME.match(line) if is_group else RE_ADDR_NAME.match(line)
    if not m:
        return None
    return strip_quotes(m.group(1))

def parse_static_targets(line: str) -> List[str]:
    m = RE_STATIC_LIST.search(line)
    if m:
        return shlex_words(m.group(1))
    m = RE_STATIC_SINGLE.search(line)
    if m:
        return [strip_quotes(m.group(1))]
    # Fortinet flattened format: member word1 word2 word3 (no brackets)
    m = RE_STATIC_MULTI.search(line)
    if m:
        return shlex_words(m.group(1))
    return []

def parse_tag_targets(line: str) -> List[str]:
    m = RE_TAG_LIST.search(line)
    if m:
        return shlex_words(m.group(1))
    m = RE_TAG_SINGLE.search(line)
    if m:
        return [strip_quotes(m.group(1))]
    # Fortinet flattened format: tagging word1 word2 (no brackets)
    m = RE_TAG_MULTI.search(line)
    if m:
        return shlex_words(m.group(1))
    return []

def parse_description(line: str) -> Optional[str]:
    m = RE_DESC.search(line)
    if not m:
        return None
    desc = m.group(1).strip()
    if not desc:
        return None
    if not (len(desc) >= 2 and desc[0] == '"' and desc[-1] == '"'):
        desc = f"\"{desc}\""
    return desc

def group_pan_address_group_objects(lines: List[str], logger: logging.Logger) -> List[Tuple[str, List[str]]]:
    grouped: Dict[str, List[str]] = {}
    order: List[str] = []

    for ln in lines:
        name = extract_name_from_line(ln, is_group=True)
        if not name:
            continue
        if name not in grouped:
            grouped[name] = []
            order.append(name)
        grouped[name].append(ln)

    logger.info(f"Grouped {len(order)} address-group object(s).")
    return [(n, grouped[n]) for n in order]

def extract_fields_for_one_object(obj_name: str, obj_lines: List[str], logger: logging.Logger) -> Tuple[List[str], Optional[str], List[str]]:
    static_targets: List[str] = []
    desc: Optional[str] = None
    tag_targets: List[str] = []

    for ln in obj_lines:
        lnl = ln.lower()

        if " member " in f" {lnl} ":
            st = parse_static_targets(ln)
            if st:
                static_targets = st

        if " comment " in f" {lnl} ":
            d = parse_description(ln)
            if d is not None:
                desc = d

        if " tagging " in f" {lnl} ":
            tg = parse_tag_targets(ln)
            if tg:
                tag_targets.extend(tg)

    if tag_targets:
        seen = set()
        deduped = []
        for t in tag_targets:
            if t in seen:
                continue
            seen.add(t)
            deduped.append(t)
        tag_targets = deduped

    logger.info(
        f"Extracted '{obj_name}': static_targets={len(static_targets)}, desc={'yes' if desc else 'no'}, tags={len(tag_targets)}"
    )
    return static_targets, desc, tag_targets

def find_block(lines: List[str], begin_marker: str, end_marker: str) -> Optional[Tuple[int, int]]:
    s = None
    e = None
    for i, ln in enumerate(lines):
        if begin_marker in ln:
            s = i
            break
    if s is None:
        return None
    for i in range(s, len(lines)):
        if end_marker in lines[i]:
            e = i
            break
    if e is None:
        return None
    return (s, e)

def delete_block_inclusive(lines: List[str], begin_marker: str, end_marker: str, logger: logging.Logger) -> List[str]:
    blk = find_block(lines, begin_marker, end_marker)
    if not blk:
        logger.info(f"Block not found for delete: {begin_marker} ... {end_marker}")
        return lines
    s, e = blk
    logger.info(f"Deleting block inclusive lines {s+1}-{e+1}: {begin_marker} ... {end_marker}")
    return lines[:s] + lines[e + 1 :]

def remove_exact_delimiter_lines(lines: List[str], delimiters: List[str], logger: logging.Logger) -> List[str]:
    dset = set([d.strip() for d in delimiters])
    out: List[str] = []
    removed = 0
    for ln in lines:
        if ln.strip() in dset:
            removed += 1
            continue
        out.append(ln)
    logger.info(f"Removed {removed} exact delimiter line(s): {delimiters}")
    return out

def max_existing_definition_n(lines: List[str], logger: logging.Logger) -> int:
    mx = 0
    for ln in lines:
        m1 = BEGIN_DEF_N_RE.match(ln.strip())
        m2 = END_DEF_N_RE.match(ln.strip())
        if m1:
            mx = max(mx, int(m1.group(1)))
        if m2:
            mx = max(mx, int(m2.group(1)))
    logger.info(f"Max existing definition_n delimiter number found: {mx}")
    return mx

def find_last_definition_end(lines: List[str]) -> Optional[int]:
    last = None
    for i, ln in enumerate(lines):
        if END_DEF_X in ln:
            last = i
        elif END_DEF_N_RE.match(ln.strip()):
            last = i
    return last

def remove_definition_n_delimiters_keep_content(lines: List[str], logger: logging.Logger) -> List[str]:
    out: List[str] = []
    removed = 0
    for ln in lines:
        if BEGIN_DEF_N_RE.match(ln.strip()) or END_DEF_N_RE.match(ln.strip()):
            removed += 1
            continue
        out.append(ln)
    logger.info(f"Removed {removed} definition_n delimiter line(s), kept content.")
    return out

def load_object_names(path: Path, is_group: bool, logger: logging.Logger) -> set:
    names = set()
    if not path.exists():
        logger.warning(f"Reference file not found: {path}")
        return names
    for ln in read_lines(path):
        nm = extract_name_from_line(ln, is_group=is_group)
        if nm:
            names.add(nm)
    logger.info(f"Loaded {len(names)} {'address-group' if is_group else 'address'} names from {path.name}")
    return names

def classify_static_targets(static_targets: List[str], addr_grp_names: set, addr_names: set, logger: logging.Logger) -> Tuple[List[str], List[str], List[str]]:
    grp_members: List[str] = []
    addr_members: List[str] = []
    unmatched: List[str] = []

    for tw in static_targets:
        if tw in addr_grp_names:
            grp_members.append(tw)
            logger.info(f"static target-word matched ADDRESS-GROUP: {tw}")
        elif tw in addr_names:
            addr_members.append(tw)
            logger.info(f"static target-word matched ADDRESS: {tw}")
        else:
            unmatched.append(tw)
            logger.warning(f"static target-word NOT FOUND in address-group or address refs: {tw}")

    return addr_members, grp_members, unmatched

def replace_markers_in_section(
    section_lines: List[str],
    obj_name: str,
    addr_members: List[str],
    grp_members: List[str],
    description: Optional[str],
    tag_targets: List[str],
    logger: logging.Logger,
) -> List[str]:
    out: List[str] = []
    tag_inside = " ".join(tag_targets).strip() if tag_targets else ""

    for ln in section_lines:
        if MARK_NAME in ln:
            out.append(ln.replace(MARK_NAME, obj_name))
            continue

        if MARK_DESC in ln:
            if description is None:
                logger.info("No description -> deleting description line in this sub-section.")
                continue
            out.append(ln.replace(MARK_DESC, description))
            continue

        if MARK_TAG in ln:
            if not tag_inside:
                logger.info("No tag -> deleting tag line in this sub-section.")
                continue
            out.append(ln.replace(MARK_TAG, tag_inside))
            continue

        if MARK_ADDR_LIST in ln:
            if not addr_members and ln.strip() == EXACT_ADDR_LIST_LINE:
                logger.info("No address members -> deleting address-list line in this sub-section.")
                continue
            out.append(ln.replace(MARK_ADDR_LIST, " ".join(addr_members)))
            continue

        if MARK_GRP_LIST in ln:
            if not grp_members and ln.strip() == EXACT_GRP_LIST_LINE:
                logger.info("No address-group members -> deleting address-group-list line in this sub-section.")
                continue
            out.append(ln.replace(MARK_GRP_LIST, " ".join(grp_members)))
            continue

        out.append(ln)

    return out

def normalize_blank_lines(lines: List[str]) -> List[str]:
    out: List[str] = []
    blank_run = 0
    for ln in lines:
        if ln.strip() == "":
            blank_run += 1
            if blank_run <= 1:
                out.append("\n")
            continue
        blank_run = 0
        out.append(ln)
    return out

def main() -> int:
    scripts_dir = Path(__file__).resolve().parent
    main_dir = scripts_dir.parent

    log_dir = main_dir / "log"
    temp_dir = main_dir / "temp"
    final_dir = main_dir / "final-data"
    misc_dir = main_dir / "miscellaneous"

    logger = setup_logger(log_dir / "step-8.log")

    print("========== START: Convert address-group objects ==========")
    print(f"scripts_dir = {scripts_dir}")
    print(f"main_dir    = {main_dir}")

    final_dir.mkdir(parents=True, exist_ok=True)
    svt_temp = final_dir / "svt-temp.cfg"
    base_tpl = misc_dir / "base-template.cfg"

    if not svt_temp.exists():
        print(f"{svt_temp} does not exist -> copying {base_tpl} to {svt_temp}")
        if not base_tpl.exists():
            print(f"ERROR: missing base template: {base_tpl}")
            return 2
        shutil.copy2(base_tpl, svt_temp)
        print("Copy done.")
    else:
        print(f"{svt_temp} already exists -> not overwriting.")

    temp_dir.mkdir(parents=True, exist_ok=True)
    print(f"Ensured temp dir exists: {temp_dir}")

    final_addr_grp = final_dir / "final-address-group.txt"
    temp_addr_grp = temp_dir / "temp-address-group.txt"

    if missing_or_empty(final_addr_grp):
        print(f"{final_addr_grp} missing/empty -> delete ORI section then go to step #26")
        svt_lines = read_lines(svt_temp)
        svt_lines = delete_block_inclusive(svt_lines, BEGIN_ORI, END_ORI, logger)
        write_lines(svt_temp, svt_lines)

        svt_lines = read_lines(svt_temp)
        svt_lines = remove_exact_delimiter_lines(svt_lines, [BEGIN_ORI, END_ORI], logger)
        svt_lines = delete_block_inclusive(svt_lines, BEGIN_DEF_X, END_DEF_X, logger)
        svt_lines = remove_definition_n_delimiters_keep_content(svt_lines, logger)
        svt_lines = normalize_blank_lines(svt_lines)
        write_lines(svt_temp, svt_lines)

        print("========== DONE (no address-group input) ==========")
        return 0

    shutil.copy2(final_addr_grp, temp_addr_grp)
    print(f"Copied {final_addr_grp} -> {temp_addr_grp}")

    final_addr = final_dir / "final-address.txt"
    addr_grp_names = load_object_names(final_addr_grp, is_group=True, logger=logger)
    addr_names = load_object_names(final_addr, is_group=False, logger=logger)

    temp_lines = read_lines(temp_addr_grp)
    objects = group_pan_address_group_objects(temp_lines, logger)

    svt_lines = read_lines(svt_temp)
    tpl = find_block(svt_lines, BEGIN_DEF_X, END_DEF_X)
    if not tpl:
        print(f"ERROR: could not find template block: {BEGIN_DEF_X} ... {END_DEF_X}")
        return 3

    tpl_s, tpl_e = tpl
    template_block = svt_lines[tpl_s:tpl_e + 1]

    last_end = find_last_definition_end(svt_lines)
    insert_at = (tpl_e + 1) if last_end is None else (last_end + 1)

    next_n = max_existing_definition_n(svt_lines, logger) + 1
    if next_n < 1:
        next_n = 1

    inserted_count = 0
    skipped_empty_count = 0

    for idx, (obj_name, obj_lines) in enumerate(objects, start=1):
        print(f"----- Processing {idx}/{len(objects)}: {obj_name} -----")

        static_targets, desc, tag_targets = extract_fields_for_one_object(obj_name, obj_lines, logger)
        addr_members, grp_members, unmatched = classify_static_targets(static_targets, addr_grp_names, addr_names, logger)

        if len(addr_members) == 0 and len(grp_members) == 0:
            skipped_empty_count += 1
            print(f"SKIP (no resolved members): {obj_name}")
            if unmatched:
                print(f"  Unmatched static target-word(s): {unmatched}")
            continue

        n = next_n
        next_n += 1

        new_block = [ln.replace("objects-address-group-definition_x", f"objects-address-group-definition_{n}")
                     for ln in template_block]

        svt_lines[insert_at:insert_at] = new_block
        block_start = insert_at
        block_end = insert_at + len(new_block) - 1
        insert_at += len(new_block)
        inserted_count += 1

        current_block = svt_lines[block_start:block_end + 1]
        updated_block = replace_markers_in_section(
            current_block,
            obj_name=obj_name,
            addr_members=addr_members,
            grp_members=grp_members,
            description=desc,
            tag_targets=tag_targets,
            logger=logger,
        )

        original_len = len(current_block)
        svt_lines[block_start:block_end + 1] = updated_block
        delta = len(updated_block) - original_len
        insert_at += delta

        print(f"Inserted/updated definition_{n}. delta_lines={delta}")

    write_lines(svt_temp, svt_lines)
    print(f"Wrote updated {svt_temp}")
    print(f"Inserted blocks: {inserted_count}, skipped empty objects: {skipped_empty_count}")

    try:
        if temp_addr_grp.exists():
            temp_addr_grp.unlink()
            print(f"Deleted temp file: {temp_addr_grp}")
    except Exception as e:
        print(f"ERROR deleting temp file {temp_addr_grp}: {e}")

    svt_lines = read_lines(svt_temp)
    svt_lines = remove_exact_delimiter_lines(svt_lines, [BEGIN_ORI, END_ORI], logger)
    svt_lines = delete_block_inclusive(svt_lines, BEGIN_DEF_X, END_DEF_X, logger)
    svt_lines = remove_definition_n_delimiters_keep_content(svt_lines, logger)
    svt_lines = normalize_blank_lines(svt_lines)

    write_lines(svt_temp, svt_lines)
    print("Cleanup complete. Final svt-temp.cfg written.")
    print("========== DONE: Convert address-group objects ==========")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"FATAL ERROR: {exc!r}")
        sys.exit(99)