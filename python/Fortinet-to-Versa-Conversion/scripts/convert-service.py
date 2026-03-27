#!/usr/bin/env python3
"""
convert-service.py

Final instruction (UPDATED):
- Delete complete lines that CONTAIN either of these substrings:
    /*begin main-section objects*/
    /*end main-section objects*/

Other behavior unchanged:
- Step 0: dedupe ../final-data/final-service.txt by EXACT full line text only
- Convert services into ../final-data/svt-temp.cfg
- Step 33 cleanup for service/address delimiters
- Collapse blank runs at end
"""

import os
import re
import sys
import shutil
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple

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


class StreamToLogger:
    def __init__(self, logger: logging.Logger, level: int):
        self.logger = logger
        self.level = level
        self.buf = ""

    def write(self, msg: str) -> None:
        if not msg:
            return
        self.buf += msg
        while "\n" in self.buf:
            line, self.buf = self.buf.split("\n", 1)
            if line != "":
                self.logger.log(self.level, line)

    def flush(self) -> None:
        if self.buf.strip():
            self.logger.log(self.level, self.buf.strip())
        self.buf = ""

def setup_logger(log_path: str) -> logging.Logger:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    logger = logging.getLogger("convert-service")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")

    fh = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    ch = logging.StreamHandler(sys.__stdout__)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    sys.stdout = StreamToLogger(logger, logging.INFO)
    sys.stderr = StreamToLogger(logger, logging.ERROR)

    logger.info("============================================================")
    logger.info("Started convert-service.py at %s", datetime.now().isoformat(timespec="seconds"))
    logger.info("Log file: %s", log_path)
    logger.info("============================================================")
    return logger

def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_text(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        text = sanitize_description_lines_in_cfg(text)
        f.write(text)

def file_nonempty(path: str) -> bool:
    return os.path.isfile(path) and os.path.getsize(path) > 0

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def copy_file(src: str, dst: str, logger: logging.Logger) -> None:
    ensure_dir(os.path.dirname(dst))
    shutil.copy2(src, dst)
    logger.info("Copied: %s -> %s", src, dst)

def collapse_blank_runs(text: str, max_blank_lines: int = 1) -> str:
    """
    Collapse runs of blank lines. Default: 2+ blank lines -> 1 blank line.
    """
    lines = text.splitlines(True)
    out: List[str] = []
    blank_run = 0

    for ln in lines:
        if ln.strip() == "":
            blank_run += 1
            if blank_run <= max_blank_lines:
                out.append(ln if ln.endswith("\n") or ln.endswith("\r\n") else ln + "\n")
        else:
            blank_run = 0
            out.append(ln)
    return "".join(out)

def delete_lines_containing_main_section_delimiters(text: str, logger: logging.Logger) -> str:
    """
    Delete complete lines that CONTAIN either:
      /*begin main-section objects*/
      /*end main-section objects*/
    anywhere on the line.
    """
    lines = text.splitlines(True)
    out: List[str] = []
    removed = 0

    needle_begin = "/*begin main-section objects*/"
    needle_end   = "/*end main-section objects*/"

    for ln in lines:
        if needle_begin in ln or needle_end in ln:
            removed += 1
            continue
        out.append(ln)

    if removed:
        logger.info("Final cleanup: removed %d line(s) containing main-section objects delimiters.", removed)
    return "".join(out)

def dedupe_final_service_file_exact_lines(path: str, logger: logging.Logger) -> None:
    """
    Remove duplicated lines by EXACT full line text only.
    - Comparison is exact after stripping only trailing newline chars.
    - Keeps first occurrence, removes later duplicates.
    """
    if not file_nonempty(path):
        logger.info("Step 0: %s missing or empty; nothing to dedupe.", path)
        return

    raw_lines = read_text(path).splitlines(True)
    seen = set()
    kept: List[str] = []
    removed_count = 0

    for ln in raw_lines:
        key = ln.rstrip("\r\n")
        if key in seen:
            removed_count += 1
            logger.info("Step 0: removed duplicate line: %s", key)
            continue
        seen.add(key)
        kept.append(ln)

    if removed_count > 0:
        write_text(path, "".join(kept))
        logger.info("Step 0: dedupe complete. Removed %d duplicate lines. Updated file: %s", removed_count, path)
    else:
        logger.info("Step 0: no duplicates found in %s", path)

def find_block(text: str, begin_re: str, end_re: str) -> Optional[Tuple[int, int, str]]:
    m1 = re.search(begin_re, text, flags=re.MULTILINE)
    if not m1:
        return None

    m2 = re.search(end_re, text[m1.end():], flags=re.MULTILINE)
    if not m2:
        return None

    start = m1.start()
    end = m1.end() + m2.end()
    return (start, end, text[start:end])

def list_existing_nums(text: str, prefix: str) -> List[int]:
    nums = set()
    for m in re.finditer(r"/\*begin sub-section\s+" + re.escape(prefix) + r"(\d+)\*/", text):
        nums.add(int(m.group(1)))
    return sorted(nums)

def replace_prefix_x_or_num(block: str, prefix: str, new_n: int) -> str:
    block = re.sub(
        r"(/\*begin sub-section\s+" + re.escape(prefix) + r")(x|\d+)(\*/)",
        r"\g<1>" + str(new_n) + r"\3",
        block
    )
    block = re.sub(
        r"(/\*end sub-section\s+" + re.escape(prefix) + r")(x|\d+)(\*/)",
        r"\g<1>" + str(new_n) + r"\3",
        block
    )
    return block

def get_template_x_block(text: str, prefix: str, logger: logging.Logger) -> str:
    bx = find_block(
        text,
        r"^[ \t]*/\*begin sub-section\s+" + re.escape(prefix) + r"x\*/[ \t]*$",
        r"^[ \t]*/\*end sub-section\s+" + re.escape(prefix) + r"x\*/[ \t]*$",
    )
    if bx:
        logger.info("Using _x template block for %s", prefix)
        return bx[2]

    bn = find_block(
        text,
        r"^[ \t]*/\*begin sub-section\s+" + re.escape(prefix) + r"\d+\*/[ \t]*$",
        r"^[ \t]*/\*end sub-section\s+" + re.escape(prefix) + r"\d+\*/[ \t]*$",
    )
    if bn:
        logger.info("Using first numbered block as template for %s", prefix)
        return bn[2]

    raise RuntimeError(f"No template block found for prefix: {prefix}")

def remove_entire_line_containing_marker(block: str, marker: str) -> str:
    return re.sub(r"^.*" + re.escape(marker) + r".*\r?\n?", "", block, flags=re.MULTILINE)

def apply_markers_and_optionals(block: str, marker_map: Dict[str, str]) -> str:
    tag_markers = [
        "@custom-service-dest-port-tag",
        "@custom-service-src-port-tag",
        "@custom-service-port-range-tag",
    ]
    desc_markers = [
        "@custom-service-dest-port-description",
        "@custom-service-src-port-description",
        "@custom-service-port-range-description",
    ]

    for tm in tag_markers:
        if tm in block and tm not in marker_map:
            block = remove_entire_line_containing_marker(block, tm)

    for dm in desc_markers:
        if dm in block and dm not in marker_map:
            block = remove_entire_line_containing_marker(block, dm)

    for k, v in marker_map.items():
        block = block.replace(k, v)

    return block

def insert_after_last_end_clean(text: str, prefix: str, new_block: str, logger: logging.Logger) -> str:
    block = new_block.strip("\r\n")
    block_lines = block.splitlines(True)
    while block_lines and block_lines[0].strip() == "":
        block_lines.pop(0)
    while block_lines and block_lines[-1].strip() == "":
        block_lines.pop()
    block = "".join(block_lines).rstrip("\r\n")

    ends_num = list(re.finditer(r"/\*end sub-section\s+" + re.escape(prefix) + r"(\d+)\*/", text))
    if ends_num:
        idx = ends_num[-1].end()
        logger.info("Insert after last numbered end delimiter for %s at char %d", prefix, idx)
        left = text[:idx]
        right = text[idx:]
        if not left.endswith("\n"):
            left += "\n"
        return left + block + "\n" + right.lstrip("\n")

    end_x = re.search(r"/\*end sub-section\s+" + re.escape(prefix) + r"x\*/", text)
    if end_x:
        idx = end_x.end()
        logger.info("Insert after _x end delimiter for %s at char %d", prefix, idx)
        left = text[:idx]
        right = text[idx:]
        if not left.endswith("\n"):
            left += "\n"
        return left + block + "\n" + right.lstrip("\n")

    raise RuntimeError(f"Could not find insertion point for prefix: {prefix}")

def extract_service_name_from_line(line: str) -> Optional[str]:
    m = re.match(r'^\s*firewall\s+service\s+custom\s+("([^"]+)"|\S+)\b', line)
    if not m:
        return None
    if m.group(2) is not None:
        return m.group(2)
    return m.group(1)

def group_first_object(lines: List[str], logger: logging.Logger) -> Tuple[Optional[str], List[str], List[str]]:
    first_name = None
    for ln in lines:
        nm = extract_service_name_from_line(ln)
        if nm:
            first_name = nm
            break

    if not first_name:
        return None, [], lines

    group = []
    remain = []
    for ln in lines:
        nm = extract_service_name_from_line(ln)
        if nm == first_name:
            group.append(ln.rstrip("\n"))
        else:
            remain.append(ln)

    logger.info("Cut group for service object '%s' with %d lines", first_name, len(group))
    return first_name, group, remain

def parse_group(group_lines: List[str], logger: logging.Logger) -> List[Dict[str, str]]:
    """Return a list of parsed dicts — one per port entry.

    Fortinet lines:
      firewall service custom <name> tcp-portrange 80
      firewall service custom <name> tcp-portrange 3389:1024-65535
      firewall service custom <name> udp-portrange 33434-33534:32768-65535
      firewall service custom <name> tcp-portrange 25 587        (multi-port)
      firewall service custom <name> comment "description text"
      firewall service custom <name> protocol TCP                (ignored; protocol derived from portrange keyword)
    """
    base: Dict[str, str] = {}

    for ln in group_lines:
        nm = extract_service_name_from_line(ln)
        if nm:
            base["name"] = nm
            break

    tag_re = re.compile(r'^\s*firewall\s+service\s+custom\s+("([^"]+)"|\S+)\s+tag\s+(.*)\s*$')
    for ln in group_lines:
        m = tag_re.match(ln)
        if not m:
            continue
        rest = (m.group(3) or "").strip()
        if not rest:
            continue
        if rest.startswith("[") and rest.endswith("]"):
            base["tag_value"] = rest[1:-1].strip()
        else:
            base["tag_value"] = rest
        break

    desc_re = re.compile(r'^\s*firewall\s+service\s+custom\s+("([^"]+)"|\S+)\s+comment\s+(.*)\s*$')
    for ln in group_lines:
        m = desc_re.match(ln)
        if not m:
            continue
        rest = (m.group(3) or "").strip()
        if not rest:
            continue
        if not (rest.startswith('"') and rest.endswith('"')):
            rest = '"' + rest.strip('"') + '"'
        base["desc_value"] = rest
        break

    # Fortinet portrange regex: protocol is embedded in the keyword (tcp-portrange / udp-portrange)
    portrange_re = re.compile(
        r'^\s*firewall\s+service\s+custom\s+("([^"]+)"|\S+)\s+(tcp|udp)-portrange\s+(.*)\s*$',
        re.IGNORECASE,
    )

    results: List[Dict[str, str]] = []
    for ln in group_lines:
        m = portrange_re.match(ln)
        if not m:
            continue
        protocol = m.group(3).lower()
        port_spec = m.group(4).strip()

        # port_spec may contain multiple space-separated port tokens (e.g. "25 587")
        for token in port_spec.split():
            # Each token may be "dst" or "dst:src"; we only use the dst portion
            dst_part = token.split(":")[0]
            entry = dict(base)  # copy shared fields (name, tag, desc)
            entry["protocol"] = protocol
            entry["port_value"] = dst_part
            entry["kind"] = "range-port" if "-" in dst_part else "dest-port"
            results.append(entry)

    if not results:
        logger.warning("No tcp-portrange/udp-portrange line found for group. name=%s", base.get("name", ""))
    return results

def cleanup_step_33_line_based(cfg_text: str, logger: logging.Logger) -> str:
    lines = cfg_text.splitlines(True)
    out: List[str] = []

    begin_service_ori = re.compile(r'^[ \t]*/\*begin sub-section\s+objects-service-ori\*/[ \t]*\r?\n?$')
    end_service_ori   = re.compile(r'^[ \t]*/\*end sub-section\s+objects-service-ori\*/[ \t]*\r?\n?$')

    begin_dest_x = re.compile(r'^[ \t]*/\*begin sub-section\s+objects-service-dest-port_x\*/[ \t]*\r?\n?$')
    end_dest_x   = re.compile(r'^[ \t]*/\*end sub-section\s+objects-service-dest-port_x\*/[ \t]*\r?\n?$')

    begin_src_x = re.compile(r'^[ \t]*/\*begin sub-section\s+objects-service-src-port_x\*/[ \t]*\r?\n?$')
    end_src_x   = re.compile(r'^[ \t]*/\*end sub-section\s+objects-service-src-port_x\*/[ \t]*\r?\n?$')

    begin_rng_x = re.compile(r'^[ \t]*/\*begin sub-section\s+objects-service-range-port_x\*/[ \t]*\r?\n?$')
    end_rng_x   = re.compile(r'^[ \t]*/\*end sub-section\s+objects-service-range-port_x\*/[ \t]*\r?\n?$')

    del_dest_n_begin = re.compile(r'^[ \t]*/\*begin sub-section\s+objects-service-dest-port_\d+\*/[ \t]*\r?\n?$')
    del_dest_n_end   = re.compile(r'^[ \t]*/\*end sub-section\s+objects-service-dest-port_\d+\*/[ \t]*\r?\n?$')

    del_src_n_begin = re.compile(r'^[ \t]*/\*begin sub-section\s+objects-service-src-port_\d+\*/[ \t]*\r?\n?$')
    del_src_n_end   = re.compile(r'^[ \t]*/\*end sub-section\s+objects-service-src-port_\d+\*/[ \t]*\r?\n?$')

    del_rng_n_begin = re.compile(r'^[ \t]*/\*begin sub-section\s+objects-service-range-port_\d+\*/[ \t]*\r?\n?$')
    del_rng_n_end   = re.compile(r'^[ \t]*/\*end sub-section\s+objects-service-range-port_\d+\*/[ \t]*\r?\n?$')

    del_addr_ip_begin   = re.compile(r'^[ \t]*/\*begin sub-section\s+objects-address-ip_\d+\*/[ \t]*\r?\n?$')
    del_addr_ip_end     = re.compile(r'^[ \t]*/\*end sub-section\s+objects-address-ip_\d+\*/[ \t]*\r?\n?$')
    del_addr_fqdn_begin = re.compile(r'^[ \t]*/\*begin sub-section\s+objects-address-fqdn_\d+\*/[ \t]*\r?\n?$')
    del_addr_fqdn_end   = re.compile(r'^[ \t]*/\*end sub-section\s+objects-address-fqdn_\d+\*/[ \t]*\r?\n?$')
    del_addr_rng_begin  = re.compile(r'^[ \t]*/\*begin sub-section\s+objects-address-range_\d+\*/[ \t]*\r?\n?$')
    del_addr_rng_end    = re.compile(r'^[ \t]*/\*end sub-section\s+objects-address-range_\d+\*/[ \t]*\r?\n?$')

    mode = None

    for ln in lines:
        if mode == "dest_x":
            if end_dest_x.match(ln):
                mode = None
            continue
        if mode == "src_x":
            if end_src_x.match(ln):
                mode = None
            continue
        if mode == "rng_x":
            if end_rng_x.match(ln):
                mode = None
            continue

        if begin_service_ori.match(ln) or end_service_ori.match(ln):
            continue

        if begin_dest_x.match(ln):
            mode = "dest_x"
            continue
        if begin_src_x.match(ln):
            mode = "src_x"
            continue
        if begin_rng_x.match(ln):
            mode = "rng_x"
            continue

        if del_dest_n_begin.match(ln) or del_dest_n_end.match(ln):
            continue
        if del_src_n_begin.match(ln) or del_src_n_end.match(ln):
            continue
        if del_rng_n_begin.match(ln) or del_rng_n_end.match(ln):
            continue

        if del_addr_ip_begin.match(ln) or del_addr_ip_end.match(ln):
            continue
        if del_addr_fqdn_begin.match(ln) or del_addr_fqdn_end.match(ln):
            continue
        if del_addr_rng_begin.match(ln) or del_addr_rng_end.match(ln):
            continue

        out.append(ln)

    logger.info("Step 33 (line-based) cleanup applied.")
    return "".join(out)


def capitalize_protocol_keywords_in_cfg(text: str, logger: logging.Logger) -> str:
    """
    Capitalize protocol keywords in lines like:
      protocol         udp;  -> protocol         UDP;
      protocol         tcp;  -> protocol         TCP;

    Only touches standalone protocol statements ending with ';'.
    """
    def _repl(m: re.Match) -> str:
        return f"{m.group(1)}{m.group(2).upper()}{m.group(3)}"

    new_text, n = re.subn(
        r'(^[ \t]*protocol[ \t]+)(udp|tcp)([ \t]*;[ \t]*$)',
        _repl,
        text,
        flags=re.MULTILINE
    )
    if n:
        logger.info("Final protocol normalization: uppercased %d protocol line(s).", n)
    return new_text


def main() -> int:
    scripts_dir = os.getcwd()
    main_dir = os.path.abspath(os.path.join(scripts_dir, ".."))

    log_path = os.path.join(main_dir, "log", "step-8.log")
    logger = setup_logger(log_path)

    final_service = os.path.join(main_dir, "final-data", "final-service.txt")
    cfg_path = os.path.join(main_dir, "final-data", "svt-temp.cfg")
    temp_dir = os.path.join(main_dir, "temp")
    temp_service = os.path.join(temp_dir, "temp-service.txt")

    logger.info("Main dir: %s", main_dir)
    logger.info("Input:    %s", final_service)
    logger.info("Temp:     %s", temp_service)
    logger.info("CFG:      %s", cfg_path)

    if not os.path.isfile(cfg_path):
        logger.error("Required file not found: %s", cfg_path)
        return 1

    logger.info("Step 0: de-duplicating EXACT lines in %s", final_service)
    dedupe_final_service_file_exact_lines(final_service, logger)

    if file_nonempty(final_service):
        logger.info("Step 26: final-service.txt exists and is non-empty => copy to ../temp/temp-service.txt")
        ensure_dir(temp_dir)
        copy_file(final_service, temp_service, logger)
    else:
        logger.info("Step 26: final-service.txt missing/empty => delete WHOLE objects-service-ori section in svt-temp.cfg then exit (step #40).")
        cfg_text = read_text(cfg_path)
        blk = find_block(
            cfg_text,
            r"^[ \t]*/\*begin sub-section\s+objects-service-ori\*/[ \t]*$",
            r"^[ \t]*/\*end sub-section\s+objects-service-ori\*/[ \t]*$"
        )
        if blk:
            s, e, _ = blk
            cfg_text = cfg_text[:s] + cfg_text[e:]
            cfg_text = collapse_blank_runs(cfg_text, max_blank_lines=1)
            cfg_text = delete_lines_containing_main_section_delimiters(cfg_text, logger)
            cfg_text = sanitize_description_lines_in_cfg(cfg_text)
            write_text(cfg_path, cfg_text)
            logger.info("Saved: %s", cfg_path)
        else:
            logger.warning("Could not find objects-service-ori block; no changes.")
        return 0

    if not file_nonempty(temp_service):
        logger.info("Step 28b: temp-service.txt is empty => run step 33 cleanup and exit.")
        cfg_text = read_text(cfg_path)
        cfg_text = cleanup_step_33_line_based(cfg_text, logger)
        cfg_text = collapse_blank_runs(cfg_text, max_blank_lines=1)
        cfg_text = delete_lines_containing_main_section_delimiters(cfg_text, logger)
        cfg_text = sanitize_description_lines_in_cfg(cfg_text)
        write_text(cfg_path, cfg_text)
        logger.info("Saved: %s", cfg_path)
        return 0

    while True:
        if not file_nonempty(temp_service):
            logger.info("All service objects processed; temp-service.txt is now empty.")
            break

        all_lines = read_text(temp_service).splitlines(True)
        obj_name, group_lines, remaining_lines = group_first_object(all_lines, logger)

        if not obj_name:
            logger.warning("No more valid service object lines found; clearing temp-service.txt to prevent loop.")
            write_text(temp_service, "")
            break

        write_text(temp_service, "".join(remaining_lines))
        logger.info("Wrote remaining lines back to temp-service.txt: %d lines", len(remaining_lines))

        parsed_list = parse_group(group_lines, logger)
        if not parsed_list:
            logger.warning("Skipping object '%s' due to missing required fields.", obj_name)
            continue

        for parsed in parsed_list:
            if not parsed.get("name") or not parsed.get("kind") or not parsed.get("protocol") or not parsed.get("port_value"):
                logger.warning("Skipping entry for object '%s' due to missing required fields.", obj_name)
                continue

            kind = parsed["kind"]
            name = parsed["name"]
            protocol = parsed["protocol"]
            port_value = parsed["port_value"]
            tag_value = parsed.get("tag_value", "").strip()
            desc_value = parsed.get("desc_value", "").strip()

            cfg_text = read_text(cfg_path)

            if kind == "dest-port":
                prefix = "objects-service-dest-port_"
                tmpl_block = get_template_x_block(cfg_text, prefix, logger)
                existing = list_existing_nums(cfg_text, prefix)
                next_n = (max(existing) + 1) if existing else 1
                new_block = replace_prefix_x_or_num(tmpl_block, prefix, next_n)

                marker_map: Dict[str, str] = {
                    "@custom-service-dest-port-name": name,
                    "@custom-service-dest-port-protocol": protocol,
                    "@custom-service-dest-port-number": port_value,
                }
                if tag_value:
                    marker_map["@custom-service-dest-port-tag"] = tag_value
                if desc_value:
                    marker_map["@custom-service-dest-port-description"] = desc_value

                new_block = apply_markers_and_optionals(new_block, marker_map)
                cfg_text = insert_after_last_end_clean(cfg_text, prefix, new_block, logger)

            elif kind == "src-port":
                prefix = "objects-service-src-port_"
                tmpl_block = get_template_x_block(cfg_text, prefix, logger)
                existing = list_existing_nums(cfg_text, prefix)
                next_n = (max(existing) + 1) if existing else 1
                new_block = replace_prefix_x_or_num(tmpl_block, prefix, next_n)

                marker_map = {
                    "@custom-service-src-port-name": name,
                    "@custom-service-src-port-protocol": protocol,
                    "@custom-service-src-port-number": port_value,
                }
                if tag_value:
                    marker_map["@custom-service-src-port-tag"] = tag_value
                if desc_value:
                    marker_map["@custom-service-src-port-description"] = desc_value

                new_block = apply_markers_and_optionals(new_block, marker_map)
                cfg_text = insert_after_last_end_clean(cfg_text, prefix, new_block, logger)

            else:
                prefix = "objects-service-range-port_"
                tmpl_block = get_template_x_block(cfg_text, prefix, logger)
                existing = list_existing_nums(cfg_text, prefix)
                next_n = (max(existing) + 1) if existing else 1
                new_block = replace_prefix_x_or_num(tmpl_block, prefix, next_n)

                marker_map = {
                    "@custom-service-port-range-name": name,
                    "@custom-service-port-range-protocol": protocol,
                    "@custom-service-port-range-number": port_value,
                }
                if tag_value:
                    marker_map["@custom-service-port-range-tag"] = tag_value
                if desc_value:
                    marker_map["@custom-service-port-range-description"] = desc_value

                new_block = apply_markers_and_optionals(new_block, marker_map)
                cfg_text = insert_after_last_end_clean(cfg_text, prefix, new_block, logger)

            cfg_text = sanitize_description_lines_in_cfg(cfg_text)
            write_text(cfg_path, cfg_text)
            logger.info("Updated svt-temp.cfg saved after processing '%s'", name)

    cfg_text = read_text(cfg_path)
    cfg_text = cleanup_step_33_line_based(cfg_text, logger)
    cfg_text = collapse_blank_runs(cfg_text, max_blank_lines=1)
    cfg_text = delete_lines_containing_main_section_delimiters(cfg_text, logger)
    cfg_text = sanitize_description_lines_in_cfg(cfg_text)
    cfg_text = capitalize_protocol_keywords_in_cfg(cfg_text, logger)
    write_text(cfg_path, cfg_text)
    logger.info("Final cleanup complete. Saved: %s", cfg_path)

    logger.info("DONE.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())