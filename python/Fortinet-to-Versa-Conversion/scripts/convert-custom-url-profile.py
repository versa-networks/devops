import os
import re
import sys
import shlex
import shutil
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional






class StreamToLogger:
    def __init__(self, logger: logging.Logger, level: int):
        self.logger = logger
        self.level = level
        self._buf = ""

    def write(self, message: str) -> None:
        if not message:
            return
        self._buf += message
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            if line.strip() != "":
                self.logger.log(self.level, line)

    def flush(self) -> None:
        if self._buf.strip() != "":
            self.logger.log(self.level, self._buf.strip())
        self._buf = ""


def setup_logger(log_path: str) -> logging.Logger:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logger = logging.getLogger("step-8-custom-urlf")
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    fh = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    sh = logging.StreamHandler(sys.__stdout__)
    sh.setLevel(logging.INFO)
    sh.setFormatter(fmt)

    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(sh)

    sys.stdout = StreamToLogger(logger, logging.INFO)
    sys.stderr = StreamToLogger(logger, logging.ERROR)

    logger.info("============================================================")
    logger.info("START step-8 custom-urlf conversion")
    logger.info(f"Timestamp: {datetime.now().isoformat(timespec='seconds')}")
    logger.info("============================================================")
    return logger






def read_lines(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.readlines()


def write_lines(path: str, lines: List[str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def file_nonempty(path: str) -> bool:
    return os.path.isfile(path) and os.path.getsize(path) > 0


def safe_copy(src: str, dst: str, logger: logging.Logger) -> None:
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    logger.info(f"Copied: {src} -> {dst}")






def transform_pattern_for_versa_regex(src: str) -> str:
    out: List[str] = []
    did_escape = False

    for ch in src:
        if ch == ".":
            out.append(".")
            continue

        if ch.isalnum() or ch in "-_":
            out.append(ch)
            continue

        if ch == "*":
            out.append(".*")
            continue

        if ch == "\\":
            out.append("\\\\")
            did_escape = True
            continue

        out.append("\\" + ch)
        did_escape = True

    s = "".join(out)
    return f"\"{s}\"" if did_escape else s






def normalize_description_always_quoted(desc: str) -> str:
    d = desc.strip()
    if len(d) >= 2 and d[0] == '"' and d[-1] == '"':
        d = d[1:-1]
    d = d.replace('"', r'\"')
    return f"\"{d}\""






FORTI_PREFIX = "webfilter urlfilter"                    # CHANGED: was "set shared profiles custom-url-category"

def parse_forti_custom_urlf_objects(forti_lines: List[str], logger: logging.Logger) -> Dict[str, List[str]]:
    grouped: Dict[str, List[str]] = {}
    skipped = 0

    for raw in forti_lines:
        line = raw.strip()
        if not line:
            continue
        if not line.startswith(FORTI_PREFIX):            # CHANGED: was PAN_PREFIX
            skipped += 1
            continue

        try:
            toks = shlex.split(line)
        except Exception as e:
            logger.error(f"shlex parse failed for line: {line!r} | err={e}")
            skipped += 1
            continue

        if len(toks) < 3:                                # CHANGED: was < 5
            skipped += 1
            continue

        obj = toks[2]                                    # CHANGED: was toks[4]
        grouped.setdefault(obj, []).append(line)

    logger.info(f"Parsed Fortinet custom-url-category objects: {len(grouped)} objects")   # CHANGED: was "PAN"
    if skipped:
        logger.info(f"Skipped non-matching/invalid lines: {skipped}")
    return grouped


def extract_description(lines: List[str]) -> Optional[str]:
    for line in lines:
        m = re.search(r"\bdescription\b\s+(.*)$", line)
        if m:
            return m.group(1).strip()
    return None


def _split_bracket_token(tok: str) -> Tuple[Optional[str], Optional[str], str]:
    lead = "[" if tok.startswith("[") else None
    trail = "]" if tok.endswith("]") else None
    core = tok
    if lead:
        core = core[1:]
    if trail and core:
        core = core[:-1]
    return lead, trail, core


def extract_patterns(lines: List[str], object_name: str, logger: logging.Logger) -> List[str]:
    """Extract URL patterns from Fortinet urlfilter lines.
    Fortinet format: webfilter urlfilter <name> entry <N> url <value> type ...
    CHANGED: was PAN format with 'list [ url1 url2 ... ]'
    """
    patterns: List[str] = []

    for line in lines:
        if " url " not in f" {line} ":                   # CHANGED: was " list "
            continue

        try:
            toks = shlex.split(line)
        except Exception:
            continue

        # find the 'url' keyword after the object name       # CHANGED: was 'list' keyword
        url_i = -1
        for i in range(len(toks)):
            if toks[i] == "url":                             # CHANGED: was "list"
                url_i = i
                break
        if url_i < 0 or url_i + 1 >= len(toks):
            continue

        # Fortinet has exactly one URL value after 'url'     # CHANGED: was bracket-list parsing
        url_val = toks[url_i + 1]
        if url_val and url_val not in ("[", "]"):
            patterns.append(url_val)

    return [p for p in (x.strip() for x in patterns) if p]






_CAT = r"(?:category|catergory)"

MAIN_BEGIN_RE = re.compile(rf"^\s*/\*begin main-section custom-url-{_CAT}-ori\*/\s*$")
MAIN_END_RE   = re.compile(rf"^\s*/\*end main-section custom-url-{_CAT}-ori\*/\s*$")

SEC_BEGIN_X_RE = re.compile(rf"^\s*/\*begin section custom-url-{_CAT}-definition_x\*/\s*$")
SEC_END_X_RE   = re.compile(rf"^\s*/\*end section custom-url-{_CAT}-definition_x\*/\s*$")

SEC_BEGIN_N_RE = re.compile(rf"^\s*/\*begin section custom-url-{_CAT}-definition_\d+\*/\s*$")
SEC_END_N_RE   = re.compile(rf"^\s*/\*end section custom-url-{_CAT}-definition_\d+\*/\s*$")


def remove_block_inclusive_regex(lines: List[str],
                                 begin_re: re.Pattern,
                                 end_re: re.Pattern,
                                 logger: logging.Logger) -> Tuple[List[str], bool]:
    start = end = None
    for i, ln in enumerate(lines):
        if start is None and begin_re.match(ln):
            start = i
            continue
        if start is not None and end_re.match(ln):
            end = i
            break

    if start is None or end is None or end < start:
        logger.warning(f"Could not find inclusive block for regex: {begin_re.pattern} .. {end_re.pattern}")
        return lines, False

    logger.info(f"Deleting block inclusive: lines {start}-{end}")
    return lines[:start] + lines[end + 1:], True


def remove_only_lines_matching(lines: List[str], patterns: List[re.Pattern]) -> List[str]:
    out: List[str] = []
    for ln in lines:
        if any(p.match(ln) for p in patterns):
            continue
        out.append(ln)
    return out






SEC_END_ANY_RE = re.compile(rf"/\*end section custom-url-{_CAT}-definition_(\d+|x)\*/")

def find_template_section(lines: List[str], logger: logging.Logger) -> List[str]:

    begin_idx = end_idx = -1
    for i, ln in enumerate(lines):
        if SEC_BEGIN_X_RE.match(ln):
            begin_idx = i
            break
    if begin_idx >= 0:
        for j in range(begin_idx + 1, len(lines)):
            if SEC_END_X_RE.match(lines[j]):
                end_idx = j
                break
        if end_idx < 0:
            raise RuntimeError("Found begin *_definition_x but missing end *_definition_x")
        return lines[begin_idx:end_idx + 1]


    for i, ln in enumerate(lines):
        if SEC_BEGIN_N_RE.match(ln):
            begin_idx = i
            break
    if begin_idx < 0:
        raise RuntimeError("No custom-url-*-definition section delimiters found")
    for j in range(begin_idx + 1, len(lines)):
        if SEC_END_N_RE.match(lines[j]):
            end_idx = j
            break
    if end_idx < 0:
        raise RuntimeError("Begin numeric section found but missing end numeric section")
    return lines[begin_idx:end_idx + 1]


def current_max_section_n(lines: List[str]) -> int:
    max_n = 0
    for ln in lines:
        m = re.search(rf"/\*begin section custom-url-{_CAT}-definition_(\d+)\*/", ln)
        if m:
            max_n = max(max_n, int(m.group(1)))
        m2 = re.search(rf"/\*end section custom-url-{_CAT}-definition_(\d+)\*/", ln)
        if m2:
            max_n = max(max_n, int(m2.group(1)))
    return max_n


def find_last_section_end_index(lines: List[str]) -> int:
    last = -1
    for i, ln in enumerate(lines):
        if SEC_END_ANY_RE.search(ln):
            last = i
    return last


def render_section_for_object(template_section: List[str], n: int, obj_name: str,
                              desc: Optional[str], patterns: List[str],
                              logger: logging.Logger) -> List[str]:
    sec = template_section.copy()


    sec = [re.sub(r"definition_(\d+|x)\*/", f"definition_{n}*/", ln) for ln in sec]

    sec = [ln.replace("@urlf-category-custom-name", obj_name) for ln in sec]

    if desc is not None:
        desc_q = normalize_description_always_quoted(desc)
        sec = [ln.replace("@urlf-category-custom-description", desc_q) for ln in sec]
    else:
        sec = [ln for ln in sec if "@urlf-category-custom-description" not in ln]

    marker_idx = -1
    marker_indent = ""
    for i, ln in enumerate(sec):
        if "@urlf-category-custom-pattern" in ln:
            marker_idx = i
            m = re.match(r"^(\s*)", ln)
            marker_indent = m.group(1) if m else ""
            break

    t_patterns = [transform_pattern_for_versa_regex(p) for p in patterns]

    if t_patterns:
        if marker_idx >= 0:
            new_lines = [f"{marker_indent}patterns {t_patterns[0]};\n"]
            for p in t_patterns[1:]:
                new_lines.append(f"{marker_indent}patterns {p};\n")
            sec = sec[:marker_idx] + new_lines + sec[marker_idx + 1:]
        else:
            insert_at = max(0, len(sec) - 1)
            indent = marker_indent or "    "
            sec = sec[:insert_at] + [f"{indent}patterns {p};\n" for p in t_patterns] + sec[insert_at:]
    else:
        if marker_idx >= 0:
            sec = sec[:marker_idx] + sec[marker_idx + 1:]

    logger.info(f"Built section n={n} for object={obj_name!r} | desc={'yes' if desc else 'no'} | patterns={len(patterns)}")
    return sec






def main() -> int:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_dir = os.path.abspath(os.path.join(script_dir, ".."))

    logger = setup_logger(os.path.join(main_dir, "log", "step-8.log"))

    final_data_dir = os.path.join(main_dir, "final-data")
    final_step_dir = os.path.join(main_dir, "final-step")

    src_final_custom = os.path.join(final_data_dir, "final-custom-urlf-profile.txt")
    dst_final_custom = os.path.join(final_step_dir, "final-custom-urlf-profile.txt")
    tmp_custom = os.path.join(final_step_dir, "temp-custom-urlf-profile.txt")

    svt_path = os.path.join(final_data_dir, "svt-temp.cfg")

    if not os.path.isfile(svt_path):
        logger.error(f"Required file missing: {svt_path}")
        return 2


    if file_nonempty(src_final_custom):
        logger.info("Step #40: final-custom-urlf-profile.txt exists+non-empty -> copy and CONTINUE.")
        safe_copy(src_final_custom, dst_final_custom, logger)
    else:
        logger.info("Step #40: source missing/empty -> delete whole main section and END this script.")
        svt_lines = read_lines(svt_path)
        svt_lines, _ = remove_block_inclusive_regex(svt_lines, MAIN_BEGIN_RE, MAIN_END_RE, logger)
        write_lines(svt_path, svt_lines)
        logger.info("Proceed to step #50. End.")
        return 0


    safe_copy(src_final_custom, tmp_custom, logger)


    forti_lines = read_lines(tmp_custom)                   # CHANGED: was pan_lines
    objects = parse_forti_custom_urlf_objects(forti_lines, logger)  # CHANGED: was parse_pan_custom_urlf_objects
    if not objects:
        logger.warning("No objects found; cleanup and exit.")
        svt_lines = read_lines(svt_path)

        svt_lines, _ = remove_block_inclusive_regex(svt_lines, SEC_BEGIN_X_RE, SEC_END_X_RE, logger)

        svt_lines = remove_only_lines_matching(svt_lines, [MAIN_BEGIN_RE, MAIN_END_RE])

        svt_lines = remove_only_lines_matching(svt_lines, [SEC_BEGIN_N_RE, SEC_END_N_RE])
        write_lines(svt_path, svt_lines)
        return 0


    svt_lines = read_lines(svt_path)
    template_section = find_template_section(svt_lines, logger)
    n = current_max_section_n(svt_lines)
    logger.info(f"Current max section n in svt-temp.cfg: {n}")

    insert_after = find_last_section_end_index(svt_lines)
    if insert_after < 0:
        insert_after = len(svt_lines) - 1

    new_sections_all: List[str] = []
    for obj_name in sorted(objects.keys()):
        n += 1
        obj_lines = objects[obj_name]
        desc = extract_description(obj_lines)
        patterns = extract_patterns(obj_lines, obj_name, logger)
        new_sections_all.extend(render_section_for_object(template_section, n, obj_name, desc, patterns, logger))

    insert_pos = insert_after + 1
    svt_lines = svt_lines[:insert_pos] + new_sections_all + svt_lines[insert_pos:]
    write_lines(svt_path, svt_lines)
    logger.info(f"Inserted {len(objects)} duplicated sections into svt-temp.cfg")


    svt_lines = read_lines(svt_path)


    svt_lines, _ = remove_block_inclusive_regex(svt_lines, SEC_BEGIN_X_RE, SEC_END_X_RE, logger)


    svt_lines = remove_only_lines_matching(svt_lines, [MAIN_BEGIN_RE, MAIN_END_RE])


    svt_lines = remove_only_lines_matching(svt_lines, [SEC_BEGIN_N_RE, SEC_END_N_RE])

    write_lines(svt_path, svt_lines)

    logger.info("Complete. Proceed to step #50. End.")
    return 0


if __name__ == "__main__":
    sys.exit(main())