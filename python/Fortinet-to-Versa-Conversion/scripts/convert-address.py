import os
import re
import sys
import shutil
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

LOG_DIR = os.path.join(MAIN_DIR, "log")
LOG_FILE = os.path.join(LOG_DIR, "step-8.log")

FINAL_DATA_DIR = os.path.join(MAIN_DIR, "final-data")
MISC_DIR = os.path.join(MAIN_DIR, "miscellaneous")
TEMP_DIR = os.path.join(MAIN_DIR, "temp")

SVT_TEMP_CFG = os.path.join(FINAL_DATA_DIR, "svt-temp.cfg")
BASE_TEMPLATE_CFG = os.path.join(MISC_DIR, "base-template.cfg")

FINAL_ADDRESS_TXT = os.path.join(FINAL_DATA_DIR, "final-address.txt")
TEMP_ADDRESS_TXT = os.path.join(TEMP_DIR, "temp-address.txt")

class TeeStdoutToLogger:
    def __init__(self, logger: logging.Logger, level: int):
        self.logger = logger
        self.level = level
        self._buffer = ""

    def write(self, msg: str):
        if msg is None:
            return
        self._buffer += msg
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            if line.strip() != "":
                self.logger.log(self.level, line)

    def flush(self):
        if self._buffer.strip() != "":
            self.logger.log(self.level, self._buffer.strip())
        self._buffer = ""

def setup_logging() -> logging.Logger:
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger("step-8")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    fh = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    sh = logging.StreamHandler(sys.__stdout__)
    sh.setLevel(logging.INFO)
    sh.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(sh)

    sys.stdout = TeeStdoutToLogger(logger, logging.INFO)
    sys.stderr = TeeStdoutToLogger(logger, logging.ERROR)

    logger.info("========================================")
    logger.info("Step-8 started: %s", datetime.now().isoformat(timespec="seconds"))
    logger.info("MAIN_DIR: %s", MAIN_DIR)
    return logger

def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_text(path: str, content: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def remove_subsection_including_delims(content: str, begin_marker: str, end_marker: str, logger: logging.Logger) -> str:
    pattern = re.compile(
        r"^[ \t]*" + re.escape(begin_marker) + r"[ \t]*\r?\n"
        r".*?"
        r"^[ \t]*" + re.escape(end_marker) + r"[ \t]*\r?\n",
        flags=re.MULTILINE | re.DOTALL,
    )
    new_content, n = pattern.subn("", content)
    logger.info("Removed subsection [%s .. %s] occurrences: %d", begin_marker, end_marker, n)
    return new_content

def remove_delimiter_lines_any_indent(content: str, exact_marker: str, logger: logging.Logger) -> str:
    pattern = re.compile(r"^[ \t]*" + re.escape(exact_marker) + r"[ \t]*\r?\n", flags=re.MULTILINE)
    new_content, n = pattern.subn("", content)
    logger.info("Removed delimiter line '%s' occurrences: %d", exact_marker, n)
    return new_content

def remove_numbered_delimiters(content: str, sub_name: str, logger: logging.Logger) -> str:
    begin_pat = re.compile(
        r"^[ \t]*/\*begin sub-section " + re.escape(sub_name) + r"_(\d+)\*/[ \t]*\r?\n",
        flags=re.MULTILINE,
    )
    end_pat = re.compile(
        r"^[ \t]*/\*end sub-section " + re.escape(sub_name) + r"_(\d+)\*/[ \t]*\r?\n",
        flags=re.MULTILINE,
    )
    content, n1 = begin_pat.subn("", content)
    content, n2 = end_pat.subn("", content)
    logger.info("Removed numbered delimiter lines for %s: begin=%d end=%d", sub_name, n1, n2)
    return content

def extract_first_subsection_block(content: str, begin_marker: str, end_marker: str) -> Optional[Tuple[str, int, int]]:
    m_begin = re.search(r"^[ \t]*" + re.escape(begin_marker) + r"[ \t]*\r?\n", content, flags=re.MULTILINE)
    if not m_begin:
        return None
    start = m_begin.start()

    m_end = re.search(r"^[ \t]*" + re.escape(end_marker) + r"[ \t]*\r?\n", content[m_begin.end():], flags=re.MULTILINE)
    if not m_end:
        return None
    end = m_begin.end() + m_end.end()

    return content[start:end], start, end

def find_last_end_marker_pos(content: str, end_marker_prefix: str) -> Optional[int]:
    pattern = re.compile(r"^[ \t]*" + re.escape(end_marker_prefix) + r"(x|\d+)\*/[ \t]*\r?\n", flags=re.MULTILINE)
    last = None
    for m in pattern.finditer(content):
        last = m
    if not last:
        return None
    return last.end()

def replace_or_delete_line_with_marker(block: str, marker: str, replacement: Optional[str]) -> str:
    if replacement is None:
        block = re.sub(r"^.*" + re.escape(marker) + r".*\r?\n", "", block, flags=re.MULTILINE)
        return block
    return block.replace(marker, replacement)

def _netmask_to_prefix(netmask: str) -> int:
    bits = 0
    for octet in netmask.split("."):
        bits += bin(int(octet)).count("1")
    return bits

def _forti_subnet_to_cidr(value: str) -> str:
    value = value.strip()
    if "/" in value:
        return value
    parts = value.split()
    if len(parts) == 2:
        return f"{parts[0]}/{_netmask_to_prefix(parts[1])}"
    return value

def ensure_quoted_description(desc: str) -> str:
    desc = desc.strip()
    if desc == "":
        return desc

    if desc.startswith('"'):
        inner = desc[1:-1] if desc.endswith('"') else desc[1:]
        inner = inner.replace('"', '')
        return f"\"{inner}\""

    inner = desc.replace('"', '')
    return f"\"{inner}\""

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

def parse_address_objects(lines: List[str], logger: logging.Logger) -> List[Dict[str, Optional[str]]]:
    cleaned = [ln.rstrip("\n") for ln in lines if ln.strip() != ""]

    obj_names: List[str] = []
    re_head = re.compile(r'^\s*firewall\s+address\s+(".*?"|\S+)\s+(\S+)\s+(.*)\s*$')

    for ln in cleaned:
        m = re_head.match(ln)
        if m:
            name_raw = m.group(1)
            name = name_raw[1:-1] if (name_raw.startswith('"') and name_raw.endswith('"')) else name_raw
            if name not in obj_names:
                obj_names.append(name)

    logger.info("Detected address object names: %d", len(obj_names))

    obj_lines: Dict[str, List[str]] = {n: [] for n in obj_names}
    for ln in cleaned:
        m = re_head.match(ln)
        if m:
            name_raw = m.group(1)
            name = name_raw[1:-1] if (name_raw.startswith('"') and name_raw.endswith('"')) else name_raw
            if name in obj_lines:
                obj_lines[name].append(ln)

    results: List[Dict[str, Optional[str]]] = []

    for name, lns in obj_lines.items():
        obj_type = None
        ip_value = None
        fqdn_value = None
        range_value = None
        desc = None
        tag_content = None
        _start_ip = None
        _end_ip = None

        for ln in lns:
            m = re_head.match(ln)
            if not m:
                continue
            keyword = m.group(2).strip()
            rest = m.group(3).strip()

            if keyword == "subnet" and obj_type is None:
                obj_type = "ip-netmask"
            elif keyword == "fqdn" and obj_type is None:
                obj_type = "fqdn"
            elif keyword == "start-ip" and obj_type is None:
                obj_type = "ip-range"

            if keyword == "subnet":
                raw = rest.split()[0] if rest else None
                ip_value = _forti_subnet_to_cidr(rest) if rest else None
            elif keyword == "fqdn":
                fqdn_value = rest if rest else None
            elif keyword == "start-ip":
                _start_ip = rest.strip() if rest else None
            elif keyword == "end-ip":
                _end_ip = rest.strip() if rest else None
            elif keyword == "comment":
                desc = ensure_quoted_description(rest)
            elif keyword == "tagging":
                mtag = re.search(r"\[(.*)\]", rest)
                if mtag:
                    tag_content = mtag.group(1).strip()
                else:
                    tag_content = rest.strip() if rest else None

        if obj_type == "ip-range" and _start_ip and _end_ip:
            range_value = f"{_start_ip}-{_end_ip}"
        elif obj_type == "ip-range" and _start_ip:
            range_value = _start_ip

        if obj_type is None:
            logger.warning("Skipping object '%s' (no subnet/fqdn/start-ip found).", name)
            continue

        results.append(
            {
                "name": name,
                "type": obj_type,
                "ip": ip_value,
                "fqdn": fqdn_value,
                "range": range_value,
                "description": desc,
                "tag": tag_content,
            }
        )

    logger.info("Parsed actionable address objects: %d", len(results))
    return results

def instantiate_subsection(
    template_content: str,
    sub_name: str,
    global_counter: int,
    replacements: Dict[str, Optional[str]],
    logger: logging.Logger,
) -> Tuple[str, int]:
    begin_x = f"/*begin sub-section {sub_name}_x*/"
    end_x = f"/*end sub-section {sub_name}_x*/"

    extracted = extract_first_subsection_block(template_content, begin_x, end_x)
    if not extracted:
        raise RuntimeError(f"Template sub-section not found for {sub_name}: {begin_x} .. {end_x}")

    block_x, _, _ = extracted

    begin_n = f"/*begin sub-section {sub_name}_{global_counter}*/"
    end_n = f"/*end sub-section {sub_name}_{global_counter}*/"
    block_n = block_x.replace(begin_x, begin_n).replace(end_x, end_n)

    for marker, value in replacements.items():
        block_n = replace_or_delete_line_with_marker(block_n, marker, value)

    end_prefix = f"/*end sub-section {sub_name}_"
    insert_pos = find_last_end_marker_pos(template_content, end_prefix)
    if insert_pos is None:
        logger.warning("Could not find end marker prefix %s; appending to end of file.", end_prefix)
        template_content = template_content.rstrip("\n") + "\n" + block_n
    else:
        template_content = template_content[:insert_pos] + block_n + template_content[insert_pos:]

    logger.info("Instantiated sub-section %s as #%d", sub_name, global_counter)
    global_counter += 1
    return template_content, global_counter

def main():
    logger = setup_logging()

    os.makedirs(FINAL_DATA_DIR, exist_ok=True)
    if not os.path.isfile(SVT_TEMP_CFG):
        logger.info("svt-temp.cfg not found. Copying base template to: %s", SVT_TEMP_CFG)
        if not os.path.isfile(BASE_TEMPLATE_CFG):
            raise FileNotFoundError(f"Missing base template: {BASE_TEMPLATE_CFG}")
        shutil.copy2(BASE_TEMPLATE_CFG, SVT_TEMP_CFG)
    else:
        logger.info("svt-temp.cfg exists: %s", SVT_TEMP_CFG)

    os.makedirs(TEMP_DIR, exist_ok=True)
    logger.info("Temp directory ensured: %s", TEMP_DIR)

    if os.path.isfile(FINAL_ADDRESS_TXT) and os.path.getsize(FINAL_ADDRESS_TXT) > 0:
        shutil.copy2(FINAL_ADDRESS_TXT, TEMP_ADDRESS_TXT)
        logger.info("Copied %s -> %s", FINAL_ADDRESS_TXT, TEMP_ADDRESS_TXT)
    else:
        logger.info("final-address.txt missing or empty. Performing template cleanup of objects-address-ori subsection and exiting (step #14 not provided).")
        cfg = read_text(SVT_TEMP_CFG)

        cfg = remove_subsection_including_delims(
            cfg,
            "/*begin sub-section objects-address-ori*/",
            "/*end sub-section objects-address-ori*/",
            logger,
        )

        cfg = sanitize_description_lines_in_cfg(cfg)
        write_text(SVT_TEMP_CFG, cfg)
        logger.info("Wrote updated svt-temp.cfg and exiting.")
        return

    with open(TEMP_ADDRESS_TXT, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    full_temp_text = "".join(raw_lines)
    has_ipnet = "subnet" in full_temp_text
    has_fqdn = "fqdn" in full_temp_text
    has_range = "start-ip" in full_temp_text

    logger.info("Keyword presence: subnet=%s fqdn=%s start-ip=%s", has_ipnet, has_fqdn, has_range)

    cfg = read_text(SVT_TEMP_CFG)

    if not has_ipnet:
        cfg = remove_subsection_including_delims(
            cfg,
            "/*begin sub-section objects-address-ip_x*/",
            "/*end sub-section objects-address-ip_x*/",
            logger,
        )
    if not has_fqdn:
        cfg = remove_subsection_including_delims(
            cfg,
            "/*begin sub-section objects-address-fqdn_x*/",
            "/*end sub-section objects-address-fqdn_x*/",
            logger,
        )
    if not has_range:
        cfg = remove_subsection_including_delims(
            cfg,
            "/*begin sub-section objects-address-range_x*/",
            "/*end sub-section objects-address-range_x*/",
            logger,
        )

    objects = parse_address_objects(raw_lines, logger)

    global_inc = 1

    for obj in objects:
        otype = obj["type"]
        name = obj["name"] or ""

        if otype == "ip-netmask":
            ip = obj["ip"]
            desc = obj["description"]
            tag = obj["tag"]

            replacements = {
                "@address-object-ip-address": ip,
                "@address-object-ip-description": desc if desc and desc.strip() != "" else None,
                "@address-object-ip-tag": tag if tag and tag.strip() != "" else None,
                "@address-object-ip-name": name,
            }

            cfg, global_inc = instantiate_subsection(
                cfg,
                "objects-address-ip",
                global_inc,
                replacements,
                logger,
            )

        elif otype == "fqdn":
            fqdn = obj["fqdn"]
            desc = obj["description"]
            tag = obj["tag"]

            replacements = {
                "@address-object-fqdn-server": fqdn,
                "@address-object-fqdn-description": desc if desc and desc.strip() != "" else None,
                "@address-object-fqdn-tag": tag if tag and tag.strip() != "" else None,
                "@address-object-fqdn": name,
            }

            cfg, global_inc = instantiate_subsection(
                cfg,
                "objects-address-fqdn",
                global_inc,
                replacements,
                logger,
            )

        elif otype == "ip-range":
            rng = obj["range"]
            desc = obj["description"]
            tag = obj["tag"]

            replacements = {
                "@address-object-range-description": desc if desc and desc.strip() != "" else None,
                "@address-object-range-tag": tag if tag and tag.strip() != "" else None,
                "@address-object-range-ip-range": rng,
                "@address-object-range": name,
            }

            cfg, global_inc = instantiate_subsection(
                cfg,
                "objects-address-range",
                global_inc,
                replacements,
                logger,
            )
        else:
            logger.warning("Unknown object type '%s' for name '%s' - skipping.", otype, name)

    cfg = remove_delimiter_lines_any_indent(cfg, "/*begin sub-section objects-address-ori*/", logger)
    cfg = remove_delimiter_lines_any_indent(cfg, "/*end sub-section objects-address-ori*/", logger)

    cfg = remove_subsection_including_delims(cfg, "/*begin sub-section objects-address-ip_x*/", "/*end sub-section objects-address-ip_x*/", logger)
    cfg = remove_subsection_including_delims(cfg, "/*begin sub-section objects-address-fqdn_x*/", "/*end sub-section objects-address-fqdn_x*/", logger)
    cfg = remove_subsection_including_delims(cfg, "/*begin sub-section objects-address-range_x*/", "/*end sub-section objects-address-range_x*/", logger)

    cfg = remove_numbered_delimiters(cfg, "objects-address-ip", logger)
    cfg = remove_numbered_delimiters(cfg, "objects-address-fqdn", logger)
    cfg = remove_numbered_delimiters(cfg, "objects-address-range", logger)

    cfg = sanitize_description_lines_in_cfg(cfg)
    write_text(SVT_TEMP_CFG, cfg)
    logger.info("Updated template written: %s", SVT_TEMP_CFG)

    try:
        write_text(TEMP_ADDRESS_TXT, "")
        logger.info("Cleared temp file (cut semantics): %s", TEMP_ADDRESS_TXT)
    except Exception as e:
        logger.error("Failed to clear temp-address.txt (non-fatal): %s", e)

    logger.info("Step-8 completed successfully.")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FATAL ERROR: {exc}")
        raise