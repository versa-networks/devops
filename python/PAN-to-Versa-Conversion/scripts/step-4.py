#!/usr/bin/env python3
import re
import sys
import shutil
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple, Optional, List


# =========================
# Helpers: logging / tee
# =========================
class TeeWriter:
    def __init__(self, original_stream, log_fh):
        self.original = original_stream
        self.log_fh = log_fh

    def write(self, s):
        try:
            self.original.write(s)
        except Exception:
            pass
        try:
            self.log_fh.write(s)
        except Exception:
            pass

    def flush(self):
        try:
            self.original.flush()
        except Exception:
            pass
        try:
            self.log_fh.flush()
        except Exception:
            pass


def ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(msg: str = ""):
    print(f"[{ts()}] {msg}")


def prompt_with_timeout(prompt: str, timeout_sec: int = 30, default: str = "") -> str:
    """
    Wait for user input up to timeout_sec. If no input, return default.
    Works on macOS/Linux terminals. If select fails, falls back to blocking input.
    """
    sys.stdout.write(prompt)
    sys.stdout.flush()

    try:
        import select
        rlist, _, _ = select.select([sys.stdin], [], [], timeout_sec)
        if rlist:
            line = sys.stdin.readline()
            return line.rstrip("\n")
        return default
    except Exception:
        # fallback: blocking
        try:
            line = input()
            return line.strip()
        except Exception:
            return default


# =========================
# Helpers: text parsing
# =========================
ALLOWED_NAME_CHARS_RE = re.compile(r"[^A-Za-z0-9_-]+")


def strip_invisible(s: str) -> str:
    # Step-8 / Step-18: remove carriage returns, remove non-visible characters
    s = s.replace("\r", "")
    # keep newline handling outside; here we clean line body
    return "".join(ch for ch in s if ch.isprintable() or ch in ("\t", " "))


def parse_name_token_span(line: str, keyword_prefix: str) -> Optional[Tuple[int, int, str]]:
    """
    Find the object name token after a given prefix, returning (start_idx, end_idx, token_raw).
    token_raw includes quotes if original was quoted.
    """
    if not line.startswith(keyword_prefix):
        return None

    i = len(keyword_prefix)

    # keyword_prefix may or may not include the required trailing space.
    # If caller included trailing space, we're already positioned after it.
    # Otherwise, skip whitespace.
    if i < len(line) and line[i].isspace():
        while i < len(line) and line[i].isspace():
            i += 1

    if i >= len(line):
        return None

    start = i
    if line[i] == '"':
        # quoted name
        j = i + 1
        while j < len(line) and line[j] != '"':
            j += 1
        if j >= len(line):
            return None
        end = j + 1
        token = line[start:end]
        return (start, end, token)
    else:
        # unquoted: token until whitespace
        j = i
        while j < len(line) and not line[j].isspace():
            j += 1
        end = j
        token = line[start:end]
        return (start, end, token)


def sanitize_object_name(raw_token: str) -> str:
    """
    Allowed characters: alnum, _, -
    - If quoted and contains spaces: spaces -> _ and remove quotes
    - Any disallowed char -> _
    """
    if raw_token.startswith('"') and raw_token.endswith('"') and len(raw_token) >= 2:
        inner = raw_token[1:-1]
        inner = inner.replace(" ", "_")
        inner = ALLOWED_NAME_CHARS_RE.sub("_", inner)
        return inner
    else:
        s = raw_token
        s = ALLOWED_NAME_CHARS_RE.sub("_", s)
        return s


def truncate_with_increment_suffix(name: str, max_len: int, counter: int, used: set) -> Tuple[str, int]:
    """
    If name > max_len, truncate and add suffix _<counter>.
    Ensure total length <= max_len, and unique in 'used'.
    """
    if len(name) <= max_len and name not in used:
        used.add(name)
        return name, counter

    while True:
        suffix = f"_{counter}"  # "_x" where x is incrementing number
        keep_len = max_len - len(suffix)
        if keep_len < 1:
            keep_len = 1
        base = name[:keep_len]
        candidate = base + suffix
        if len(candidate) > max_len:
            candidate = candidate[:max_len]
        if candidate not in used:
            used.add(candidate)
            counter += 1
            return candidate, counter
        counter += 1


def find_keyword_outside_quotes(line: str, keyword: str) -> List[int]:
    """
    Return list of indices where keyword token occurs outside double quotes.
    Token boundary: preceded/followed by whitespace or common separators.
    """
    idxs = []
    in_q = False
    i = 0
    n = len(line)
    kw = keyword

    def is_boundary(ch: str) -> bool:
        return ch.isspace() or ch in "[](){}," or ch == ""

    while i < n:
        ch = line[i]
        if ch == '"':
            in_q = not in_q
            i += 1
            continue
        if not in_q:
            if line.startswith(kw, i):
                before = line[i - 1] if i > 0 else ""
                after = line[i + len(kw)] if i + len(kw) < n else ""
                if is_boundary(before) and is_boundary(after):
                    idxs.append(i)
                    i += len(kw)
                    continue
        i += 1
    return idxs


def parse_bracket_content(segment: str) -> Optional[Tuple[str, str, str]]:
    """
    Parse first [...] block, respecting quotes.
    Returns (before_including_[, inside_without_brackets, after_including_]).
    """
    lb = segment.find("[")
    if lb < 0:
        return None

    in_q = False
    i = lb + 1
    while i < len(segment):
        ch = segment[i]
        if ch == '"':
            in_q = not in_q
        elif ch == "]" and not in_q:
            inside = segment[lb + 1 : i]
            before = segment[: lb + 1]
            after = segment[i:]
            return before, inside, after
        i += 1
    return None


def tokenize_respecting_quotes(s: str) -> List[Tuple[str, bool]]:
    """
    Tokenize by whitespace; keep quoted substrings as a single token.
    Returns (token, was_quoted). Quotes removed from token.
    """
    out = []
    i = 0
    n = len(s)
    while i < n:
        while i < n and s[i].isspace():
            i += 1
        if i >= n:
            break

        if s[i] == '"':
            j = i + 1
            while j < n and s[j] != '"':
                j += 1
            if j >= n:
                return []
            out.append((s[i + 1 : j], True))
            i = j + 1
        else:
            j = i
            while j < n and not s[j].isspace():
                j += 1
            out.append((s[i:j], False))
            i = j
    return out


def sanitize_tag_value_token(token: str, was_quoted: bool) -> str:
    if was_quoted:
        token = token.replace(" ", "_")
    token = ALLOWED_NAME_CHARS_RE.sub("_", token)
    return token


def process_tag_in_line(line: str) -> Tuple[str, Optional[str]]:
    """
    Steps 11a-11e:
      - If tag exists:
          - if no value -> delete line
          - if value is quoted multiword -> spaces->_ and remove quotes
          - if value is bracket list: sanitize each token; quoted tokens spaces->_
          - otherwise single token sanitize
      - If can't parse -> unsupported
    Returns:
      ("ok", new_line) or ("delete", None) or ("unsupported", None)
    """
    tag_idxs = find_keyword_outside_quotes(line, "tag")
    if not tag_idxs:
        return "ok", line

    ti = tag_idxs[0]
    before = line[:ti]
    after = line[ti + 3 :]  # after 'tag'
    after_stripped = after.lstrip(" \t")
    ws_prefix_len = len(after) - len(after_stripped)
    ws_prefix = after[:ws_prefix_len]

    if after_stripped == "" or after_stripped == "\n":
        # Step 11d
        return "delete", None

    if after_stripped.startswith("["):
        parsed = parse_bracket_content(after_stripped)
        if not parsed:
            return "unsupported", None
        _b_before, inside, b_after = parsed
        tokens = tokenize_respecting_quotes(inside)
        if tokens == [] and inside.strip() != "":
            return "unsupported", None
        if len(tokens) == 0:
            return "unsupported", None
        new_tokens = [sanitize_tag_value_token(tok, was_q) for tok, was_q in tokens]
        new_inside = " ".join(new_tokens)
        rebuilt = "tag" + ws_prefix + "[" + new_inside + "]" + b_after[len("]") :]
        return "ok", before + rebuilt

    if after_stripped.startswith('"'):
        j = 1
        while j < len(after_stripped) and after_stripped[j] != '"':
            j += 1
        if j >= len(after_stripped):
            return "unsupported", None
        inner = after_stripped[1:j]
        tail = after_stripped[j + 1 :]
        newv = sanitize_tag_value_token(inner, True)
        rebuilt = "tag" + ws_prefix + newv + tail
        return "ok", before + rebuilt

    m = re.match(r"^(\S+)(.*)$", after_stripped)
    if not m:
        return "unsupported", None
    tok = m.group(1)
    tail = m.group(2)
    newv = sanitize_tag_value_token(tok, False)
    rebuilt = "tag" + ws_prefix + newv + tail
    return "ok", before + rebuilt


def protocol_is_valid(line: str) -> bool:
    """
    Step-12: protocol format must be one of:
      protocol tcp port <n or n-n>
      protocol udp port <n or n-n>
      protocol tcp source-port <n or n-n>
      protocol udp source-port <n or n-n>
    """
    idxs = find_keyword_outside_quotes(line, "protocol")
    if not idxs:
        return True

    pi = idxs[0]
    tail = line[pi:]
    m = re.search(r"\bprotocol\s+(tcp|udp)\s+(port|source-port)\s+(\d+)(?:-(\d+))?\b", tail)
    return bool(m)


def next_keyword_after_name(line: str, name_end_idx: int) -> str:
    s = line[name_end_idx:]
    s = s.lstrip(" \t")
    if not s:
        return ""
    j = 0
    while j < len(s) and not s[j].isspace():
        j += 1
    return s[:j]


def apply_replacements_tokenwise(text: str, replacements: Dict[str, str]) -> str:
    """
    Case-sensitive replacements.
    - quoted keys: direct string replace
    - unquoted: boundary-aware regex replace
    """
    keys = sorted(replacements.keys(), key=len, reverse=True)
    for k in keys:
        v = replacements[k]
        if k.startswith('"') and k.endswith('"'):
            text = text.replace(k, v)
        else:
            pattern = r"(?:(?<=^)|(?<=[\s\[\]\(\)\{\},]))" + re.escape(k) + r"(?:(?=$)|(?=[\s\[\]\(\)\{\},]))"
            text = re.sub(pattern, v, text)
    return text


def replace_group_name_with_members(text: str, group_name: str, members_phrase: str) -> str:
    pattern = r"(?:(?<=^)|(?<=[\s\[\]\(\)\{\},]))" + re.escape(group_name) + r"(?:(?=$)|(?=[\s\[\]\(\)\{\},]))"
    return re.sub(pattern, members_phrase, text)


# =========================
# Main script
# =========================
def main():
    scripts_dir = Path(__file__).resolve().parent
    main_dir = scripts_dir.parent

    log_dir = main_dir / "log"
    step2_dir = main_dir / "step-2"
    step3_dir = main_dir / "step-3"
    step4_dir = main_dir / "step-4"
    final_dir = main_dir / "final-data"

    # Step-1
    step4_dir.mkdir(parents=True, exist_ok=True)

    # Logging
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file_path = log_dir / "step-4.log"

    with open(log_file_path, "a", encoding="utf-8") as log_fh:
        sys.stdout = TeeWriter(sys.stdout, log_fh)
        sys.stderr = TeeWriter(sys.stderr, log_fh)

        log("========== STEP-4 START ==========")
        log(f"scripts_dir = {scripts_dir}")
        log(f"main_dir    = {main_dir}")
        log(f"log_file    = {log_file_path}")
        log("")
        log("Note: Pre-execution text mentioned step-1.log once; using step-4.log per Step-4 instructions.")
        log("")

        # Step-2
        src_pan_rules_default = step3_dir / "step-3_cleaned-pan-rules.txt"
        dst_pan_rules = step4_dir / "step-4_cleaned-pan-rules.txt"

        if src_pan_rules_default.exists():
            shutil.copy2(src_pan_rules_default, dst_pan_rules)
            log(f"Step-2: Copied {src_pan_rules_default} -> {dst_pan_rules}")
        else:
            log("Step-2: Default source file not found:")
            log(f"        {src_pan_rules_default}")
            for attempt in range(1, 4):
                user_path = input("Enter the FULL path to the source pan-rules file to copy: ").strip()
                if not user_path:
                    log("No input provided. Try again.")
                    continue
                p = Path(user_path).expanduser()
                if p.exists() and p.is_file():
                    shutil.copy2(p, dst_pan_rules)
                    log(f"Copied {p} -> {dst_pan_rules}")
                    break
                else:
                    log(f"Invalid path (attempt {attempt}/3): {p}")
            else:
                raise FileNotFoundError("No valid source file provided for step-4_cleaned-pan-rules.txt")

        # Step-3
        log("")
        log("Step-3: Service object name length policy")
        log("Maximum allowed service object name length is 31 characters.")
        log("Any service object name longer than this will be truncated and suffixed with _<x> (incrementing).")
        log("If you want a SHORTER maximum length, enter it now; press Enter to accept default 31.")
        max_len_in = prompt_with_timeout("Enter max service name length (<=31) [default 31]: ", timeout_sec=15, default="").strip()
        if max_len_in == "":
            max_service_len = 31
        else:
            try:
                max_service_len = int(max_len_in)
                if max_service_len <= 0:
                    max_service_len = 31
                if max_service_len > 31:
                    log(f"Input length {max_service_len} > 31; forcing to 31.")
                    max_service_len = 31
            except ValueError:
                log("Invalid number. Using default 31.")
                max_service_len = 31
        log(f"Using max_service_len = {max_service_len}")

        # Step-4
        log("")
        log("Step-4: Allowed object-name characters are: alphanumeric, underscore '_', hyphen '-'.")
        log("Any unacceptable characters in object names will be replaced with '_'.")
        prompt_with_timeout("Press Enter to continue (or wait 30 seconds)... ", timeout_sec=30, default="")
        log("Continuing...")

        # Files
        extracted_service = step4_dir / "step-4_extracted-service.txt"
        cleaned_service = step4_dir / "step-4_cleaned-service.txt"
        corrected_service = step4_dir / "step-4_corrected-service.txt"
        unsupported_service = step4_dir / "step-4_unsupported-service-config.txt"

        # Step-5a + Step-5
        log("")
        log("Step-5a/5: Removing override lines and extracting 'set shared service ' lines.")
        pan_lines = dst_pan_rules.read_text(encoding="utf-8", errors="replace").splitlines(True)

        # 5a: remove lines starting with "set shared service" and ending in override yes/no
        override_pat = re.compile(r"^set shared service\b.*\boverride\s+(no|yes)\s*$")
        service_extract_prefix = "set shared service "  # NOTE: must match space after service

        keep_pan: List[str] = []
        svc_lines: List[str] = []
        removed_override = 0
        removed_service = 0

        for ln in pan_lines:
            ln2 = ln.rstrip("\n")
            if override_pat.match(ln2.strip()):
                removed_override += 1
                continue

            # 5: extract/cut lines preceded with "set shared service " (with space)
            if ln2.startswith(service_extract_prefix):
                svc_lines.append(ln2 + "\n")
                removed_service += 1
                continue

            keep_pan.append(ln2 + "\n")

        dst_pan_rules.write_text("".join(keep_pan), encoding="utf-8")
        extracted_service.write_text("".join(svc_lines), encoding="utf-8")
        log(f"Removed override service lines: {removed_override}")
        log(f"Extracted service lines:       {removed_service}")
        log(f"Updated pan-rules file:        {dst_pan_rules}")
        log(f"Wrote extracted services:      {extracted_service}")

        # Step-6
        shutil.copy2(extracted_service, cleaned_service)
        log(f"Step-6: Copied {extracted_service} -> {cleaned_service}")

        # Step-7..12
        log("")
        log("Step-7..12: Cleaning service object names, tags, and validating protocol format.")
        corrected_service_lines: List[str] = []
        unsupported_service_lines: List[str] = []
        output_service_lines: List[str] = []

        service_name_map: Dict[str, str] = {}
        used_service_names = set()
        trunc_counter = 1
        allowed_next = {"protocol", "description", "tag"}

        in_lines = cleaned_service.read_text(encoding="utf-8", errors="replace").splitlines(True)
        for raw_ln in in_lines:
            ln = raw_ln.rstrip("\n")
            ln = strip_invisible(ln)  # Step-8

            span = parse_name_token_span(ln, "set shared service")  # name after keyword
            if not span:
                unsupported_service_lines.append(ln + "\n")
                continue

            ns, ne, raw_name_token = span

            # map sanitized name consistently across multiple config lines
            if raw_name_token in service_name_map:
                clean_name = service_name_map[raw_name_token]
            else:
                base = sanitize_object_name(raw_name_token)
                base = ALLOWED_NAME_CHARS_RE.sub("_", base)
                if len(base) > max_service_len or base in used_service_names:
                    base, trunc_counter = truncate_with_increment_suffix(base, max_service_len, trunc_counter, used_service_names)
                else:
                    used_service_names.add(base)
                service_name_map[raw_name_token] = base
                clean_name = base

            # Step-9: capture lines containing undesirable chars in name BEFORE modifying
            changed = False
            if raw_name_token.startswith('"') and raw_name_token.endswith('"'):
                changed = True
            else:
                if ALLOWED_NAME_CHARS_RE.search(raw_name_token):
                    changed = True
            if sanitize_object_name(raw_name_token) != clean_name:
                changed = True

            if changed:
                corrected_service_lines.append(ln + "\n")

            # apply name replacement
            ln2 = ln[:ns] + clean_name + ln[ne:]

            # Step-10: next keyword after name must be protocol/description/tag
            name_end_idx = ns + len(clean_name)
            nxt = next_keyword_after_name(ln2, name_end_idx)
            if nxt == "" or nxt not in allowed_next:
                unsupported_service_lines.append(ln2 + "\n")
                continue

            # Step-11: tag sanitation
            st, new_ln = process_tag_in_line(ln2)
            if st == "delete":
                continue
            if st == "unsupported" or new_ln is None:
                unsupported_service_lines.append(ln2 + "\n")
                continue
            ln3 = new_ln

            # Step-12: protocol validation (port OR source-port)
            if not protocol_is_valid(ln3):
                unsupported_service_lines.append(ln3 + "\n")
                continue

            output_service_lines.append(ln3 + "\n")

        cleaned_service.write_text("".join(output_service_lines), encoding="utf-8")
        corrected_service.write_text("".join(corrected_service_lines), encoding="utf-8")
        unsupported_service.write_text("".join(unsupported_service_lines), encoding="utf-8")

        log(f"Cleaned service lines kept:        {len(output_service_lines)}")
        log(f"Corrected-service lines captured:  {len(corrected_service_lines)}")
        log(f"Unsupported-service lines captured:{len(unsupported_service_lines)}")
        log(f"Wrote: {cleaned_service}")
        log(f"Wrote: {corrected_service}")
        log(f"Wrote: {unsupported_service}")

        # Step-13
        log("")
        log("Step-13: Updating service object references in step-4_cleaned-pan-rules.txt (case-sensitive).")
        if corrected_service.exists() and corrected_service.stat().st_size > 0:
            repl: Dict[str, str] = {}
            corr_lines = corrected_service.read_text(encoding="utf-8", errors="replace").splitlines()
            for cl in corr_lines:
                sp = parse_name_token_span(cl, "set shared service")
                if not sp:
                    continue
                _, __, raw_tok = sp
                clean_name = service_name_map.get(raw_tok)
                if not clean_name:
                    clean_name = sanitize_object_name(raw_tok)
                    clean_name = ALLOWED_NAME_CHARS_RE.sub("_", clean_name)
                    if len(clean_name) > max_service_len:
                        clean_name, trunc_counter = truncate_with_increment_suffix(
                            clean_name, max_service_len, trunc_counter, used_service_names
                        )
                repl[raw_tok] = clean_name

            pan_text = dst_pan_rules.read_text(encoding="utf-8", errors="replace")
            new_text = apply_replacements_tokenwise(pan_text, repl)
            dst_pan_rules.write_text(new_text, encoding="utf-8")
            log(f"Applied {len(repl)} service-name replacement(s) into {dst_pan_rules}")
        else:
            log("Corrected-service file is empty; Step-13 skipped.")

        # =========================
        # Service-group processing
        # =========================
        extracted_sg = step4_dir / "step-4_extracted-service-group.txt"
        cleaned_sg_step4 = step4_dir / "step-4_cleaned-service-group.txt"
        cleaned_sg_step2 = step2_dir / "step-4_cleaned-service-group.txt"  # per Step-16 instruction
        corrected_sg_name = step4_dir / "step-4_corrected-service-group-name.txt"
        corrected_sg = step4_dir / "step-4_corrected-service-group.txt"  # to satisfy Step-20 reference
        temp_sg = step4_dir / "step-4_temp-service-group.txt"

        # Step-15: extract/cut service-group lines from pan-rules
        log("")
        log("Step-15: Extracting 'set shared service-group' lines from pan-rules.")
        pan_lines2 = dst_pan_rules.read_text(encoding="utf-8", errors="replace").splitlines(True)
        sg_prefix = "set shared service-group"
        keep_pan2: List[str] = []
        sg_lines: List[str] = []
        for ln in pan_lines2:
            ln2 = ln.rstrip("\n")
            if ln2.startswith(sg_prefix):
                sg_lines.append(ln2 + "\n")
                continue
            keep_pan2.append(ln2 + "\n")
        dst_pan_rules.write_text("".join(keep_pan2), encoding="utf-8")
        extracted_sg.write_text("".join(sg_lines), encoding="utf-8")
        log(f"Extracted service-group lines: {len(sg_lines)}")
        log(f"Wrote: {extracted_sg}")
        log(f"Updated pan-rules file: {dst_pan_rules}")

        # Step-16: copy extracted sg to ../step-2/... and also to ../step-4/... for subsequent steps
        log("")
        log("Step-16: Copying extracted service-group file per instructions (and keeping step-4 working copy).")
        step2_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(extracted_sg, cleaned_sg_step2)
        shutil.copy2(extracted_sg, cleaned_sg_step4)
        log(f"Copied {extracted_sg} -> {cleaned_sg_step2}")
        log(f"Copied {extracted_sg} -> {cleaned_sg_step4}")

        # Step-17..19: sanitize service-group names
        log("")
        log("Step-17..19: Cleaning service-group object names (allowed chars only).")
        sg_name_map: Dict[str, str] = {}
        corrected_sg_lines: List[str] = []
        cleaned_sg_out: List[str] = []

        sg_in = cleaned_sg_step4.read_text(encoding="utf-8", errors="replace").splitlines(True)
        for raw_ln in sg_in:
            ln = raw_ln.rstrip("\n")
            ln = strip_invisible(ln)  # Step-18

            sp = parse_name_token_span(ln, "set shared service-group")
            if not sp:
                cleaned_sg_out.append(ln + "\n")
                continue
            ns, ne, raw_tok = sp

            if raw_tok in sg_name_map:
                clean_name = sg_name_map[raw_tok]
            else:
                clean_name = sanitize_object_name(raw_tok)
                clean_name = ALLOWED_NAME_CHARS_RE.sub("_", clean_name)
                sg_name_map[raw_tok] = clean_name

            changed = False
            if raw_tok.startswith('"') and raw_tok.endswith('"'):
                changed = True
            else:
                if ALLOWED_NAME_CHARS_RE.search(raw_tok):
                    changed = True
            if sanitize_object_name(raw_tok) != clean_name:
                changed = True

            if changed:
                corrected_sg_lines.append(ln + "\n")

            ln2 = ln[:ns] + clean_name + ln[ne:]
            cleaned_sg_out.append(ln2 + "\n")

        cleaned_sg_step4.write_text("".join(cleaned_sg_out), encoding="utf-8")
        corrected_sg_name.write_text("".join(corrected_sg_lines), encoding="utf-8")
        corrected_sg.write_text("".join(corrected_sg_lines), encoding="utf-8")  # Step-20 refers to this name

        log(f"Wrote: {cleaned_sg_step4}")
        log(f"Wrote: {corrected_sg_name}")
        log(f"Wrote: {corrected_sg}")
        log(f"Corrected service-group lines captured: {len(corrected_sg_lines)}")

        # Step-20: update pan-rules references for corrected service-group names
        log("")
        log("Step-20: Updating service-group references in step-4_cleaned-pan-rules.txt (case-sensitive).")
        if corrected_sg.exists() and corrected_sg.stat().st_size > 0:
            repl_sg: Dict[str, str] = {}
            for cl in corrected_sg.read_text(encoding="utf-8", errors="replace").splitlines():
                sp = parse_name_token_span(cl, "set shared service-group")
                if not sp:
                    continue
                _, __, raw_tok = sp
                repl_sg[raw_tok] = sg_name_map.get(raw_tok, sanitize_object_name(raw_tok))

            pan_text = dst_pan_rules.read_text(encoding="utf-8", errors="replace")
            new_text = apply_replacements_tokenwise(pan_text, repl_sg)
            dst_pan_rules.write_text(new_text, encoding="utf-8")
            log(f"Applied {len(repl_sg)} service-group replacement(s) into {dst_pan_rules}")
        else:
            log("Corrected service-group file is empty; Step-20 skipped.")

        # Step-21: members lines into temp file
        log("")
        log("Step-21: Building temp file of service-group members lines.")
        temp_lines: List[str] = []
        for ln in cleaned_sg_step4.read_text(encoding="utf-8", errors="replace").splitlines():
            sp2 = parse_name_token_span(ln, "set shared service-group")
            if not sp2:
                continue
            ns2, ne2, _tok2 = sp2
            nxt2 = next_keyword_after_name(ln, ne2)
            if nxt2 == "members":
                temp_lines.append(ln + "\n")

        temp_sg.write_text("".join(temp_lines), encoding="utf-8")
        log(f"Wrote {len(temp_lines)} members line(s) to: {temp_sg}")

        # Step-22: expand service-group names with members list inside pan-rules
        log("")
        log("Step-22: Expanding service-group names in pan-rules using members [].")
        pan_text = dst_pan_rules.read_text(encoding="utf-8", errors="replace")

        expanded = 0
        for ln in temp_lines:
            sp = parse_name_token_span(ln, "set shared service-group")
            if not sp:
                continue
            _, __, grp_tok = sp
            grp_name = sanitize_object_name(grp_tok)

            mi_list = find_keyword_outside_quotes(ln, "members")
            if not mi_list:
                continue
            mi = mi_list[0]
            after_members = ln[mi + 7 :].lstrip(" \t")
            if not after_members.startswith("["):
                continue

            parsed = parse_bracket_content(after_members)
            if not parsed:
                continue
            _b_before, inside, _b_after = parsed
            members_tokens = tokenize_respecting_quotes(inside)
            if not members_tokens:
                continue

            member_words = [sanitize_tag_value_token(tok, was_q) for tok, was_q in members_tokens]
            members_phrase = " ".join(member_words).strip()
            if not members_phrase:
                continue

            new_pan_text = replace_group_name_with_members(pan_text, grp_name, members_phrase)
            if new_pan_text != pan_text:
                expanded += 1
                pan_text = new_pan_text

        dst_pan_rules.write_text(pan_text, encoding="utf-8")
        log(f"Expanded {expanded} service-group name(s) in {dst_pan_rules}")

        # Step-22: delete temp file
        try:
            temp_sg.unlink(missing_ok=True)
            log(f"Deleted temp file: {temp_sg}")
        except Exception as e:
            log(f"WARNING: Could not delete temp file {temp_sg}: {e}")

        # Step-23 (final naming)
        log("")
        log("Step-23: Copying final cleaned outputs to ../final-data/ with final names.")
        final_dir.mkdir(parents=True, exist_ok=True)

        final_service_path = final_dir / "final-service.txt"
        final_service_group_path = final_dir / "final-service-group.txt"

        shutil.copy2(cleaned_service, final_service_path)
        shutil.copy2(cleaned_sg_step4, final_service_group_path)

        log(f"Copied -> {final_service_path}")
        log(f"Copied -> {final_service_group_path}")

        log("")
        log("========== STEP-4 COMPLETE ==========")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(f"[{ts()}] ERROR: Step-4 failed with exception:")
        traceback.print_exc()
        sys.exit(1)
