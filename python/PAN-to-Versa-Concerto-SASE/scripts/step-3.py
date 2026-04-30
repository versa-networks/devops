

from __future__ import annotations

import sys
import ipaddress
import re
import shlex
import shutil
import logging
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Set, Tuple

class _StreamToLogger:
    def __init__(self, logger: logging.Logger, level: int):
        self.logger = logger
        self.level = level
        self._buffer = ""
    def write(self, message: str) -> None:
        if not message:
            return
        self._buffer += message
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            if line.strip():
                self.logger.log(self.level, line.rstrip())

    def flush(self) -> None:
        if self._buffer.strip():
            self.logger.log(self.level, self._buffer.rstrip())
        self._buffer = ""

def setup_logging(log_path: Path) -> logging.Logger:
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("step-3")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    fh = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
    logger.addHandler(fh)

    ch = logging.StreamHandler(stream=sys.__stdout__)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(ch)

    sys.stdout = _StreamToLogger(logger, logging.INFO)
    sys.stderr = _StreamToLogger(logger, logging.ERROR)

    logger.info("=== Step-3 starting ===")
    logger.info(f"Logging to: {log_path}")
    return logger

_RG_ADDR_GROUP = re.compile(r'^set\s+shared\s+address-group\s+(".*?"|\S+)')
_RG_ADDR       = re.compile(r'^set\s+shared\s+address\s+(".*?"|\S+)')

def _strip_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return s[1:-1]
    return s

def extract_addr_group_name(line: str) -> Optional[str]:
    m = _RG_ADDR_GROUP.match(line.strip())
    if not m:
        return None
    return _strip_quotes(m.group(1))

def extract_addr_name(line: str) -> Optional[str]:
    m = _RG_ADDR.match(line.strip())
    if not m:
        return None
    return _strip_quotes(m.group(1))

def extract_unique_names(lines: Iterable[str], extractor: Callable[[str], Optional[str]]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for ln in lines:
        name = extractor(ln)
        if name is None:
            continue
        if name not in seen:
            seen.add(name)
            out.append(name)
    return out

def extract_keyword_values(line: str, keyword: str) -> List[str]:

    vals: List[str] = []

    bracket_pat = re.compile(rf'\b{re.escape(keyword)}\b\s+\[\s*([^\]]*)\s*\]')
    for m in bracket_pat.finditer(line):
        inside = (m.group(1) or "").strip()
        if inside:
            vals.extend(shlex.split(inside, posix=True))

    single_pat = re.compile(rf'\b{re.escape(keyword)}\b\s+(".*?"|\S+)')
    for m in single_pat.finditer(line):
        raw = m.group(1).strip()
        if raw == "[" or raw.startswith("["):
            continue
        vals.append(_strip_quotes(raw))

    return vals

def referenced_in_rules(obj_name: str, rules_lines: List[str]) -> bool:
    
    for ln in rules_lines:
        if "source" not in ln and "destination" not in ln:
            continue
        if obj_name in extract_keyword_values(ln, "source"):
            return True
        if obj_name in extract_keyword_values(ln, "destination"):
            return True
    return False

def referenced_in_group_static(obj_name: str, group_lines: List[str]) -> bool:
    for ln in group_lines:
        if "static" not in ln:
            continue
        if obj_name in extract_keyword_values(ln, "static"):
            return True
    return False

def partition_definition_lines(
    lines: List[str],
    extractor: Callable[[str], Optional[str]],
    unused_names: Set[str]
) -> Tuple[List[str], List[str]]:

    kept: List[str] = []
    moved: List[str] = []
    for ln in lines:
        nm = extractor(ln)
        if nm is not None and nm in unused_names:
            moved.append(ln)
        else:
            kept.append(ln)
    return kept, moved

_RG_IPV4_CIDR = re.compile(r'\b(\d{1,3}(?:\.\d{1,3}){3})/(3[0-2]|[12]?\d)\b')
_RG_IP_NETMASK = re.compile(r'(\bip-netmask\b)(\s+)(".*?"|\S+)')

def normalize_ipv4_cidr_strict(cidr: str) -> str:

    try:
        iface = ipaddress.IPv4Interface(cidr)
    except Exception:
        return cidr

    ip = iface.ip
    prefix = iface.network.prefixlen
    net = iface.network

    if prefix == 32:
        return f"{ip}/32"

    if ip != net.network_address:
        return f"{ip}/32"

    return f"{net.network_address}/{prefix}"

def fix_ipv4_cidr_after_ip_netmask(line: str) -> Tuple[str, int]:

    replacements = 0

    def _repl(m: re.Match) -> str:
        nonlocal replacements
        token = m.group(1)
        ws = m.group(2)
        raw_val = m.group(3)

        was_quoted = len(raw_val) >= 2 and raw_val[0] == '"' and raw_val[-1] == '"'
        val = raw_val[1:-1] if was_quoted else raw_val

        if not _RG_IPV4_CIDR.fullmatch(val):
            return m.group(0)

        fixed = normalize_ipv4_cidr_strict(val)
        if fixed != val:
            replacements += 1

        new_val = f'"{fixed}"' if was_quoted else fixed
        return f"{token}{ws}{new_val}"

    new_line = _RG_IP_NETMASK.sub(_repl, line)
    return new_line, replacements

def sanitize_description_line(line: str) -> Tuple[str, int]:

    s = line
    if "description" not in s or '"' not in s:
        return s, 0

    m = re.search(r'\bdescription\b', s)
    if not m:
        return s, 0

    first_q = s.find('"', m.end())
    if first_q == -1:
        return s, 0

    last_q = s.rfind('"')
    if last_q <= first_q:
        return s, 0

    inner = s[first_q + 1:last_q]
    if '"' not in inner:
        return s, 0

    cleaned = inner.replace('"', '')
    removed = inner.count('"')

    new_s = s[:first_q + 1] + cleaned + s[last_q:]
    return new_s, removed

def read_lines(path: Path) -> List[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)

def write_lines(path: Path, lines: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")

def post_process_config_file(path: Path, logger: logging.Logger, max_example_logs: int = 50) -> None:

    if not path.exists():
        logger.info(f"Post-process: file not found, skipping: {path}")
        return

    lines = read_lines(path)
    changed = False

    cidr_fix_count = 0
    desc_fix_count = 0
    example_logs = 0

    new_lines: List[str] = []
    for i, ln in enumerate(lines, start=1):
        original = ln

        ln2, r1 = fix_ipv4_cidr_after_ip_netmask(ln)
        cidr_fix_count += r1

        ln3, r2 = sanitize_description_line(ln2)
        desc_fix_count += r2

        if ln3 != original:
            changed = True
            if example_logs < max_example_logs:
                logger.info(f"Post-process change in {path.name} line {i}:")
                logger.info(f"  - {original.rstrip()}")
                logger.info(f"  + {ln3.rstrip()}")
                example_logs += 1

        new_lines.append(ln3)

    if changed:
        write_lines(path, new_lines)
        logger.info(
            f"Post-process updated {path.name}: ip-netmask_cidr_fixes={cidr_fix_count}, "
            f"description_inner_quotes_removed={desc_fix_count}"
        )
    else:
        logger.info(f"Post-process: no changes needed for {path.name}")

def write_name_list(path: Path, names: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(names) + ("\n" if names else "")
    path.write_text(content, encoding="utf-8")

def copy_file(src: Path, dst: Path, logger: logging.Logger) -> None:
    if not src.exists():
        raise FileNotFoundError(f"Missing required input file: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    logger.info(f"Copied: {src} -> {dst}")

def main() -> int:
    script_dir = Path(__file__).resolve().parent
    main_dir = script_dir.parent

    log_dir = main_dir / "log"
    step2_dir = main_dir / "step-2"
    step3_dir = main_dir / "step-3"
    final_dir = main_dir / "final-data"

    logger = setup_logging(log_dir / "step-3.log")
    logger.info(f"Script dir: {script_dir}")
    logger.info(f"Main dir:   {main_dir}")
    logger.info("NOTE: Correlation is CASE-SENSITIVE (exact match).")

    src_rules = step2_dir / "step-2_cleaned-pan-rules.txt"
    src_ag    = step2_dir / "step-2_cleaned-address-group.txt"
    src_a     = step2_dir / "step-2_cleaned-address.txt"

    dst_rules = step3_dir / "step-3_cleaned-pan-rules.txt"
    dst_ag    = step3_dir / "step-3_cleaned-address-group.txt"
    dst_a     = step3_dir / "step-3_cleaned-address.txt"

    logger.info("--- Copying Step-2 files into Step-3 ---")
    copy_file(src_rules, dst_rules, logger)
    copy_file(src_ag,    dst_ag,    logger)
    copy_file(src_a,     dst_a,     logger)

    rules_lines = read_lines(dst_rules)
    logger.info(f"Loaded rules lines: {len(rules_lines)} from {dst_rules.name}")

    logger.info("\n=== Address-GROUP correlation ===")
    group_lines_original = read_lines(dst_ag)
    logger.info(f"Loaded address-group lines: {len(group_lines_original)} from {dst_ag.name}")

    group_names = extract_unique_names(group_lines_original, extract_addr_group_name)
    logger.info(f"Extracted unique address-group names: {len(group_names)}")

    extracted_group_names_path = step3_dir / "step-3_extracted-address-group-name.txt"
    write_name_list(extracted_group_names_path, group_names)
    logger.info(f"Wrote extracted address-group names -> {extracted_group_names_path}")

    unused_group_names: List[str] = []
    used_in_rules_cnt = 0
    used_in_static_cnt = 0

    for nm in group_names:
        in_rules = referenced_in_rules(nm, rules_lines)
        in_static = referenced_in_group_static(nm, group_lines_original)

        if in_rules:
            used_in_rules_cnt += 1
        if in_static:
            used_in_static_cnt += 1

        if (not in_rules) and (not in_static):
            unused_group_names.append(nm)
            logger.info(f"UNUSED group (not in rules source/dest AND not in any static): {nm}")

    logger.info(f"Groups used in rules (source/destination): {used_in_rules_cnt}")
    logger.info(f"Groups referenced in address-group static: {used_in_static_cnt}")
    logger.info(f"Groups to cut (unused): {len(unused_group_names)}")

    unused_group_file = step3_dir / "step-3_unused-address-group.txt"

    if unused_group_names:
        unused_set = set(unused_group_names)
        kept_ag, moved_ag = partition_definition_lines(group_lines_original, extract_addr_group_name, unused_set)

        write_lines(unused_group_file, moved_ag)
        write_lines(dst_ag, kept_ag)

        logger.info(f"Wrote cut (unused) address-group lines -> {unused_group_file} (lines={len(moved_ag)})")
        logger.info(f"Rewrote {dst_ag.name} without unused groups (remaining lines={len(kept_ag)})")
    else:
        write_lines(unused_group_file, [])
        logger.info(f"No unused address-groups found. Created empty -> {unused_group_file}")

    group_lines_pruned = read_lines(dst_ag)
    logger.info(f"Loaded pruned address-group lines: {len(group_lines_pruned)} from {dst_ag.name}")

    logger.info("\n=== Address correlation ===")
    addr_lines_original = read_lines(dst_a)
    logger.info(f"Loaded address lines: {len(addr_lines_original)} from {dst_a.name}")

    addr_names = extract_unique_names(addr_lines_original, extract_addr_name)
    logger.info(f"Extracted unique address names: {len(addr_names)}")

    extracted_addr_names_path = step3_dir / "step-3_extracted-address-name.txt"
    write_name_list(extracted_addr_names_path, addr_names)
    logger.info(f"Wrote extracted address names -> {extracted_addr_names_path}")

    unused_addr_names: List[str] = []
    used_in_rules_cnt = 0
    used_in_static_cnt = 0

    for nm in addr_names:
        in_rules = referenced_in_rules(nm, rules_lines)
        in_static = referenced_in_group_static(nm, group_lines_pruned)

        if in_rules:
            used_in_rules_cnt += 1
        if in_static:
            used_in_static_cnt += 1

        if (not in_rules) and (not in_static):
            unused_addr_names.append(nm)
            logger.info(f"UNUSED address (not in rules source/dest AND not in any group static): {nm}")

    logger.info(f"Addresses used in rules (source/destination): {used_in_rules_cnt}")
    logger.info(f"Addresses referenced in address-group static: {used_in_static_cnt}")
    logger.info(f"Addresses to cut (unused): {len(unused_addr_names)}")

    unused_addr_file = step3_dir / "step-3_unused-address.txt"

    if unused_addr_names:
        unused_set = set(unused_addr_names)
        kept_a, moved_a = partition_definition_lines(addr_lines_original, extract_addr_name, unused_set)

        write_lines(unused_addr_file, moved_a)
        write_lines(dst_a, kept_a)

        logger.info(f"Wrote cut (unused) address lines -> {unused_addr_file} (lines={len(moved_a)})")
        logger.info(f"Rewrote {dst_a.name} without unused addresses (remaining lines={len(kept_a)})")
    else:
        write_lines(unused_addr_file, [])
        logger.info(f"No unused addresses found. Created empty -> {unused_addr_file}")

    logger.info("\n=== End-of-script fixes ===")
    post_process_config_file(dst_a, logger)
    post_process_config_file(dst_ag, logger)
    post_process_config_file(step3_dir / "step-3_unused-address.txt", logger)
    post_process_config_file(step3_dir / "step-3_unused-address-group.txt", logger)

    logger.info("\n=== Final export (Step 14) ===")
    if not final_dir.exists():
        final_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {final_dir}")
    else:
        logger.info(f"Directory already exists: {final_dir}")

    final_addr = final_dir / "final-address.txt"
    final_ag   = final_dir / "final-address-group.txt"

    shutil.copy2(dst_a, final_addr)
    logger.info(f"Copied: {dst_a} -> {final_addr}")

    shutil.copy2(dst_ag, final_ag)
    logger.info(f"Copied: {dst_ag} -> {final_ag}")

    logger.info("\n=== Step-3 complete ===")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"FATAL: {e}")
        raise
