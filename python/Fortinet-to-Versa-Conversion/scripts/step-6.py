import re
import sys
import shutil
from pathlib import Path
from datetime import datetime

ALLOWED_CHARS_RE = re.compile(r"[^A-Za-z0-9_-]")

PREFIX_URLF   = "webfilter profile"          # CHANGED: was "set shared profiles url-filtering"
PREFIX_CUSTOM = "webfilter urlfilter"         # CHANGED: was "set shared profiles custom-url-category"

FORTI_RULES_SRC_DEFAULT_REL = Path("step-5") / "step-5_cleaned-forti-rules.txt"  # CHANGED: was pan-rules

URLF_DROP_SUBSTRINGS = []   # CHANGED: was PAN-specific keywords; flattener controls Fortinet output

ACTIONS = {"allow", "block", "alert", "reject"}   # kept (unused after urlf_line_references_name rewrite)
PROFILE_SETTING_PHRASE = "webfilter-profile"       # CHANGED: was "profile-setting profiles url-filtering"


class TeeStream:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            try:
                s.write(data)
            except Exception:
                pass

    def flush(self):
        for s in self.streams:
            try:
                s.flush()
            except Exception:
                pass


def now_ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def read_text_lines(p: Path):
    with p.open("r", encoding="utf-8", errors="replace", newline="") as f:
        return f.readlines()


def write_text_lines(p: Path, lines):
    with p.open("w", encoding="utf-8", errors="replace", newline="\n") as f:
        for line in lines:
            if line.endswith("\n"):
                f.write(line)
            else:
                f.write(line + "\n")


def strip_non_visible_and_cr(s: str) -> str:
    s = s.replace("\r", "")
    out = []
    for ch in s:
        o = ord(ch)
        if ch in ("\n", "\t"):
            out.append(ch)
        elif 32 <= o <= 126:
            out.append(ch)
        elif o >= 128:
            out.append(ch)
        else:
            pass
    return "".join(out)


def sanitize_description_inner_quotes(line: str) -> tuple[str, bool]:
    if 'comment "' not in line:          # CHANGED: was 'description "'
        return line, False

    kw = "comment"                        # CHANGED: was "description"
    kidx = line.find(kw)
    if kidx == -1:
        return line, False

    q1 = line.find('"', kidx)
    if q1 == -1:
        return line, False

    q2 = line.rfind('"')
    if q2 == -1 or q2 <= q1:
        return line, False

    content = line[q1 + 1:q2]
    if '"' not in content:
        return line, False

    new_content = content.replace('"', "")
    return line[:q1 + 1] + new_content + line[q2:], True


def sanitize_description_file(path: Path) -> int:
    if not path.exists():
        print(f"[{now_ts()}] Description-scan: file missing, skip: {path}")
        return 0

    lines = read_text_lines(path)
    out = []
    changed = 0
    for line in lines:
        new_line, did = sanitize_description_inner_quotes(line)
        if did:
            changed += 1
        out.append(new_line)

    if changed:
        write_text_lines(path, out)
    return changed


def parse_object_token_after_prefix(line: str, prefix: str):
    lstripped = line.lstrip()
    lead = len(line) - len(lstripped)
    if not lstripped.startswith(prefix):
        return (None, None, None)

    start = lead + len(prefix)
    while start < len(line) and line[start].isspace():
        start += 1
    if start >= len(line):
        return (None, None, None)

    if line[start] == '"':
        endq = line.find('"', start + 1)
        if endq == -1:
            end = start
            while end < len(line) and not line[end].isspace():
                end += 1
            return (line[start:end], start, end)
        else:
            return (line[start:endq + 1], start, endq + 1)
    else:
        end = start
        while end < len(line) and not line[end].isspace():
            end += 1
        return (line[start:end], start, end)


def sanitize_object_name(token: str) -> str:
    t = token
    if len(t) >= 2 and t[0] == '"' and t[-1] == '"':
        t = t[1:-1]
        t = t.replace(" ", "_")
    t = t.replace(" ", "_")
    t = ALLOWED_CHARS_RE.sub("_", t)
    return t


def file_has_nonempty_content(p: Path) -> bool:
    if not p.exists():
        return False
    try:
        data = p.read_text(encoding="utf-8", errors="replace")
        return bool(data.strip())
    except Exception:
        return False


def wait_for_enter_or_timeout(timeout_sec: int = 15):
    print(f"[{now_ts()}] ******* Press ENTER to continue, or wait {timeout_sec}s... *******")
    try:
        import select

        rlist, _, _ = select.select([sys.stdin], [], [], timeout_sec)
        if rlist:
            sys.stdin.readline()
            print(f"[{now_ts()}] Continue (ENTER pressed).")
            return
        print(f"[{now_ts()}] Continue (timeout).")
        return
    except Exception:
        import threading

        done = {"v": False}

        def _reader():
            try:
                input()
            except Exception:
                pass
            done["v"] = True

        t = threading.Thread(target=_reader, daemon=True)
        t.start()
        t.join(timeout_sec)
        if done["v"]:
            print(f"[{now_ts()}] Continue (ENTER pressed).")
        else:
            print(f"[{now_ts()}] Continue (timeout).")


def prompt_for_existing_file(prompt_text: str) -> Path:
    while True:
        resp = input(prompt_text).strip()
        if not resp:
            print(f"[{now_ts()}] Empty input. Please provide a valid file path.")
            continue
        p = Path(resp).expanduser()
        if not p.is_absolute():
            p = (Path.cwd() / p).resolve()
        if p.exists() and p.is_file():
            return p
        print(f"[{now_ts()}] File not found: {p}")


def build_unique_preserve_order(items):
    seen = set()
    out = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def extract_object_names_from_file(lines, prefix: str):
    names = []
    for line in lines:
        token, _, _ = parse_object_token_after_prefix(line, prefix)
        if token is None:
            continue
        name = token
        if len(name) >= 2 and name[0] == '"' and name[-1] == '"':
            name = name[1:-1].replace(" ", "_")
        names.append(name)
    return build_unique_preserve_order(names)


def extract_first_token_after_phrase(line: str, phrase: str):
    idx = line.find(phrase)
    if idx == -1:
        return None
    rest = line[idx + len(phrase):].strip()
    if not rest:
        return None
    if rest[0] == '"':
        endq = rest.find('"', 1)
        if endq == -1:
            parts = rest.split()
            return parts[0] if parts else None
        return rest[:endq + 1]
    parts = rest.split()
    return parts[0] if parts else None


def urlf_line_references_name(line: str, name: str) -> bool:
    # CHANGED: Fortinet webfilter profiles reference urlfilter tables via
    # "urlfilter-table <name>" instead of PAN's allow/block/alert/reject lists.
    norm = line.replace("[", " [ ").replace("]", " ] ")
    toks = norm.split()
    n = len(toks)
    for i in range(n):
        if toks[i] == "urlfilter-table":
            j = i + 1
            if j < n:
                tok = toks[j].strip('"')
                if tok == name:
                    return True
    return False


def cut_lines_by_prefix(src_lines, prefix: str):
    kept = []
    cut = []
    for line in src_lines:
        if line.lstrip().startswith(prefix):
            cut.append(line)
        else:
            kept.append(line)
    return kept, cut


def cut_object_blocks(clean_lines, prefix: str, unused_names_set):
    kept = []
    cut = []
    for line in clean_lines:
        token, _, _ = parse_object_token_after_prefix(line, prefix)
        if token is None:
            kept.append(line)
            continue
        obj = token
        if len(obj) >= 2 and obj[0] == '"' and obj[-1] == '"':
            obj = obj[1:-1].replace(" ", "_")
        if obj in unused_names_set:
            cut.append(line)
        else:
            kept.append(line)
    return kept, cut


# ── NEW: Fortinet webfilter flattening functions ───────────────────────────────

def find_forti_source_conf(main_dir: Path) -> Path:
    """Locate source-forti-config.conf relative to main_dir."""
    for candidate in [
        main_dir / "source-forti-config.conf",
        main_dir.parent / "source-forti-config.conf",
    ]:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"source-forti-config.conf not found near {main_dir}"
    )


def flatten_forti_webfilter_sections(source_path: Path, dst_rules: Path) -> int:
    """
    Read source-forti-config.conf and flatten two block types:
      - config webfilter urlfilter  -->  webfilter urlfilter "Name" entry N url ... action ...
      - config webfilter profile    -->  webfilter profile "Name" comment/urlfilter-table/ftgd-wf ...
    Resolves numeric urlfilter-table IDs to names using the urlfilter section.
    Appends all flattened lines to dst_rules.  Returns count of lines appended.
    """
    raw = read_text_lines(source_path)

    # Join backslash line-continuations (Fortinet long-line convention)
    joined: list[str] = []
    buf = ""
    for ln in raw:
        s = ln.rstrip("\r\n")
        if s.endswith("\\"):
            buf += s[:-1] + " "
        else:
            buf += s
            joined.append(buf)
            buf = ""
    if buf:
        joined.append(buf)

    # ── Pass 1: build urlfilter numeric-ID → name map ─────────────────────────
    id_to_name: dict[int, str] = {}
    in_urlf = in_table = False
    cur_id: int | None = None
    cur_name: str | None = None
    depth = 0  # tracks nested "config" blocks inside a table entry

    for line in joined:
        s = line.strip()
        if not in_urlf:
            if s == "config webfilter urlfilter":
                in_urlf = True
            continue
        if in_table:
            if s.startswith("config "):
                depth += 1
            elif s == "end" and depth > 0:
                depth -= 1
            elif s == "end":
                # end of config webfilter urlfilter
                in_urlf = False
            elif s == "next" and depth == 0:
                if cur_id is not None and cur_name is not None:
                    id_to_name[cur_id] = cur_name
                cur_id = cur_name = None
                in_table = False
            elif s.startswith("set name ") and depth == 0:
                cur_name = s[9:].strip().strip('"')
            continue
        # in_urlf, not in_table
        if s.startswith("edit "):
            tok = s.split(None, 1)
            if len(tok) == 2:
                try:
                    cur_id = int(tok[1])
                    in_table = True
                    cur_name = None
                    depth = 0
                except ValueError:
                    pass
        elif s == "end":
            in_urlf = False

    # ── Pass 2: flatten config webfilter urlfilter ────────────────────────────
    urlf_flat: list[str] = []
    in_urlf = in_table = in_entries = in_entry = False
    table_name: str | None = None
    entry_id: int | None = None
    entry_attrs: dict[str, str] = {}

    for line in joined:
        s = line.strip()
        if not in_urlf:
            if s == "config webfilter urlfilter":
                in_urlf = True
            continue

        if in_entry:
            if s == "next":
                if table_name and entry_id is not None:
                    parts = [f'webfilter urlfilter "{table_name}" entry {entry_id}']
                    for k in ("url", "type", "action", "status"):
                        if k in entry_attrs:
                            parts.append(f"{k} {entry_attrs[k]}")
                    urlf_flat.append(" ".join(parts))
                in_entry = False
                entry_id = None
                entry_attrs = {}
            elif s.startswith("set "):
                tok = s.split(None, 2)
                if len(tok) >= 3:
                    entry_attrs[tok[1]] = tok[2].strip('"')
                elif len(tok) == 2:
                    entry_attrs[tok[1]] = ""
            continue

        if in_entries:
            if s.startswith("edit "):
                tok = s.split(None, 1)
                if len(tok) == 2:
                    try:
                        entry_id = int(tok[1])
                        in_entry = True
                        entry_attrs = {}
                    except ValueError:
                        pass
            elif s == "end":
                in_entries = False
            continue

        if in_table:
            if s.startswith("set name "):
                table_name = s[9:].strip().strip('"')
            elif s == "config entries":
                in_entries = True
            elif s == "next":
                in_table = False
                table_name = None
            continue

        # in_urlf, not in_table
        if s.startswith("edit "):
            tok = s.split(None, 1)
            if len(tok) == 2:
                try:
                    int(tok[1])  # must be numeric
                    in_table = True
                    table_name = None
                except ValueError:
                    pass
        elif s == "end":
            in_urlf = False

    # ── Pass 3: flatten config webfilter profile ──────────────────────────────
    profile_flat: list[str] = []
    ST_OUTSIDE   = 0
    ST_IN_BLOCK  = 1   # inside config webfilter profile
    ST_IN_PROF   = 2   # inside edit "name"
    ST_IN_WEB    = 3   # inside config web
    ST_IN_FTGD   = 4   # inside config ftgd-wf
    ST_IN_FILTERS = 5  # inside config filters
    ST_IN_FILTER  = 6  # inside edit N (filter entry)

    state = ST_OUTSIDE
    prof_name: str | None = None
    filt_id: int | None = None
    filt_attrs: dict[str, str] = {}

    for line in joined:
        s = line.strip()

        if state == ST_OUTSIDE:
            if s == "config webfilter profile":
                state = ST_IN_BLOCK

        elif state == ST_IN_BLOCK:
            if s == "end":
                state = ST_OUTSIDE
            elif s.startswith("edit "):
                rest = s[5:].strip()
                prof_name = rest.strip('"')
                state = ST_IN_PROF

        elif state == ST_IN_PROF:
            if s == "next":
                prof_name = None
                state = ST_IN_BLOCK
            elif s == "config web":
                state = ST_IN_WEB
            elif s == "config ftgd-wf":
                state = ST_IN_FTGD
            elif s.startswith("set comment "):
                val = s[12:].strip()
                profile_flat.append(f'webfilter profile "{prof_name}" comment {val}')
            elif s.startswith("set feature-set "):
                val = s[16:].strip()
                profile_flat.append(f'webfilter profile "{prof_name}" feature-set {val}')

        elif state == ST_IN_WEB:
            if s == "end":
                state = ST_IN_PROF
            elif s.startswith("set urlfilter-table "):
                parts = s.split()
                if len(parts) == 3:
                    try:
                        tid = int(parts[2])
                        tname = id_to_name.get(tid, str(tid))
                        profile_flat.append(
                            f'webfilter profile "{prof_name}" urlfilter-table "{tname}"'
                        )
                    except ValueError:
                        pass

        elif state == ST_IN_FTGD:
            if s == "end":
                state = ST_IN_PROF
            elif s == "config filters":
                state = ST_IN_FILTERS

        elif state == ST_IN_FILTERS:
            if s == "end":
                state = ST_IN_FTGD
            elif s.startswith("edit "):
                tok = s.split(None, 1)
                if len(tok) == 2:
                    try:
                        filt_id = int(tok[1])
                        filt_attrs = {}
                        state = ST_IN_FILTER
                    except ValueError:
                        pass

        elif state == ST_IN_FILTER:
            if s == "next":
                if filt_id is not None and "category" in filt_attrs and "action" in filt_attrs:
                    profile_flat.append(
                        f'webfilter profile "{prof_name}" ftgd-wf filter {filt_id}'
                        f' category {filt_attrs["category"]} action {filt_attrs["action"]}'
                    )
                filt_id = None
                filt_attrs = {}
                state = ST_IN_FILTERS
            elif s.startswith("set "):
                tok = s.split(None, 2)
                if len(tok) >= 3:
                    filt_attrs[tok[1]] = tok[2].strip('"')
                elif len(tok) == 2:
                    filt_attrs[tok[1]] = ""

    # Append all flattened lines to dst_rules
    all_flat = urlf_flat + profile_flat
    if all_flat:
        with dst_rules.open("a", encoding="utf-8", errors="replace") as f:
            for fl in all_flat:
                f.write(fl + "\n")
    return len(all_flat)

# ── END NEW functions ──────────────────────────────────────────────────────────


def main():
    script_dir = Path(__file__).resolve().parent
    main_dir = script_dir.parent
    log_dir = main_dir / "log"
    ensure_dir(log_dir)

    log_file = log_dir / "step-6.log"

    lf = log_file.open("a", encoding="utf-8", errors="replace")
    sys.stdout = TeeStream(sys.__stdout__, lf)
    sys.stderr = TeeStream(sys.__stderr__, lf)

    print("=" * 80)
    print(f"[{now_ts()}] Step-6 START")
    print(f"[{now_ts()}] script_dir: {script_dir}")
    print(f"[{now_ts()}] main_dir  : {main_dir}")
    print(f"[{now_ts()}] log_file  : {log_file}")
    print("=" * 80)

    step6_dir = main_dir / "step-6"
    ensure_dir(step6_dir)
    print(f"[{now_ts()}] Ensured/created directory: {step6_dir}")

    src_default = main_dir / FORTI_RULES_SRC_DEFAULT_REL   # CHANGED: FORTI_RULES_SRC_DEFAULT_REL
    dst_rules   = step6_dir / "step-6_cleaned-forti-rules.txt"  # CHANGED: forti-rules

    if src_default.exists():
        shutil.copy2(src_default, dst_rules)
        print(f"[{now_ts()}] Copied: {src_default} -> {dst_rules}")
    else:
        print(f"[{now_ts()}] Default source not found: {src_default}")
        print(f"[{now_ts()}] Please provide the name/location of the source file to copy.")
        user_src = prompt_for_existing_file(
            "Enter full path (or relative path) to source Fortinet rules file: "  # CHANGED
        )
        if not user_src.exists():
            alt = (main_dir / user_src).resolve()
            if alt.exists():
                user_src = alt
        shutil.copy2(user_src, dst_rules)
        print(f"[{now_ts()}] Copied: {user_src} -> {dst_rules}")

    # NEW: flatten webfilter urlfilter and webfilter profile blocks from source config
    try:
        source_conf = find_forti_source_conf(main_dir)
        n_flat = flatten_forti_webfilter_sections(source_conf, dst_rules)
        print(f"[{now_ts()}] Appended {n_flat} flattened webfilter lines from: {source_conf}")
    except FileNotFoundError as exc:
        print(f"[{now_ts()}] WARNING: {exc} - webfilter sections will not be processed")

    print()
    print(f"[{now_ts()}] ******* Allowed characters in object names: alphanumeric, '_' and '-' *******")
    print(f"[{now_ts()}] ******* Any unacceptable characters in object names will be replaced by '_' *******")
    wait_for_enter_or_timeout(15)
    print()

    rules_lines = read_text_lines(dst_rules)

    urlf_extracted = step6_dir / "step-6_extracted-urlf-profile.txt"
    urlf_cleaned   = step6_dir / "step-6_cleaned-urlf-profile.txt"
    urlf_corrected = step6_dir / "step-6_corrected-urlf-profile-name.txt"

    rules_kept, urlf_cut_lines = cut_lines_by_prefix(rules_lines, PREFIX_URLF)
    write_text_lines(urlf_extracted, urlf_cut_lines)
    write_text_lines(dst_rules, rules_kept)
    print(f"[{now_ts()}] CUT {len(urlf_cut_lines)} URLF lines with prefix '{PREFIX_URLF}' -> {urlf_extracted}")
    print(f"[{now_ts()}] forti-rules updated (URLF lines removed): {dst_rules} (kept {len(rules_kept)} lines)")  # CHANGED

    rules_lines = read_text_lines(dst_rules)

    shutil.copy2(urlf_extracted, urlf_cleaned)
    print(f"[{now_ts()}] Copied: {urlf_extracted} -> {urlf_cleaned}")

    cleaned_in  = read_text_lines(urlf_cleaned)
    corrected_lines = []
    sanitized_out   = []

    for line in cleaned_in:
        line2 = strip_non_visible_and_cr(line)

        token, sidx, eidx = parse_object_token_after_prefix(line2, PREFIX_URLF)
        if token is None:
            sanitized_out.append(line2)
            continue

        sanitized_name = sanitize_object_name(token)
        if token != sanitized_name:
            corrected_lines.append(line2.rstrip("\n"))
            line2 = line2[:sidx] + sanitized_name + line2[eidx:]

        sanitized_out.append(line2)

    write_text_lines(urlf_corrected, corrected_lines)
    write_text_lines(urlf_cleaned,   sanitized_out)
    print(f"[{now_ts()}] URLF sanitize complete -> {urlf_cleaned}")
    print(f"[{now_ts()}] Wrote {len(corrected_lines)} pre-modification lines to -> {urlf_corrected}")

    urlf_after = read_text_lines(urlf_cleaned)
    kept = []
    dropped = 0
    for line in urlf_after:
        if any(sub in line for sub in URLF_DROP_SUBSTRINGS):
            dropped += 1
            continue
        kept.append(line)
    write_text_lines(urlf_cleaned, kept)
    print(f"[{now_ts()}] URLF removed {dropped} lines containing: {URLF_DROP_SUBSTRINGS}")

    if file_has_nonempty_content(urlf_corrected):
        corr_lines = read_text_lines(urlf_corrected)
        mapping = {}
        for cl in corr_lines:
            cl2 = strip_non_visible_and_cr(cl)
            tok, _, _ = parse_object_token_after_prefix(cl2, PREFIX_URLF)
            if tok is None:
                continue
            mapping[tok] = sanitize_object_name(tok)

        if mapping:
            rules_lines2 = read_text_lines(dst_rules)
            changed = 0
            new_rules = []
            for line in rules_lines2:
                line2 = line
                for orig, san in mapping.items():
                    if orig in line2:
                        line2 = line2.replace(orig, san)
                if line2 != line:
                    changed += 1
                new_rules.append(line2)
            write_text_lines(dst_rules, new_rules)
            print(f"[{now_ts()}] Updated forti-rules references for URLF profile names: {len(mapping)} names, {changed} lines changed")  # CHANGED
        else:
            print(f"[{now_ts()}] URLF corrected file non-empty but no mappings parsed (unexpected).")
    else:
        print(f"[{now_ts()}] URLF corrected file empty -> skip forti-rules URLF name correlation (step 11)")  # CHANGED

    rules_lines = read_text_lines(dst_rules)

    custom_extracted = step6_dir / "step-6_extracted-custom-urlf-profile.txt"
    custom_cleaned   = step6_dir / "step-6_cleaned-custom-urlf-profile.txt"
    custom_corrected = step6_dir / "step-6_corrected-custom-urlf-profile-name.txt"

    rules_kept, custom_cut_lines = cut_lines_by_prefix(rules_lines, PREFIX_CUSTOM)
    write_text_lines(custom_extracted, custom_cut_lines)
    write_text_lines(dst_rules, rules_kept)
    print(f"[{now_ts()}] CUT {len(custom_cut_lines)} CUSTOM lines with prefix '{PREFIX_CUSTOM}' -> {custom_extracted}")
    print(f"[{now_ts()}] forti-rules updated (CUSTOM lines removed): {dst_rules} (kept {len(rules_kept)} lines)")  # CHANGED

    rules_lines = read_text_lines(dst_rules)

    shutil.copy2(custom_extracted, custom_cleaned)
    print(f"[{now_ts()}] Copied: {custom_extracted} -> {custom_cleaned}")

    cleaned_in  = read_text_lines(custom_cleaned)
    corrected_lines = []
    sanitized_out   = []

    for line in cleaned_in:
        line2 = strip_non_visible_and_cr(line)

        token, sidx, eidx = parse_object_token_after_prefix(line2, PREFIX_CUSTOM)
        if token is None:
            sanitized_out.append(line2)
            continue

        sanitized_name = sanitize_object_name(token)
        if token != sanitized_name:
            corrected_lines.append(line2.rstrip("\n"))
            line2 = line2[:sidx] + sanitized_name + line2[eidx:]

        sanitized_out.append(line2)

    write_text_lines(custom_corrected, corrected_lines)
    write_text_lines(custom_cleaned,   sanitized_out)
    print(f"[{now_ts()}] CUSTOM sanitize complete -> {custom_cleaned}")
    print(f"[{now_ts()}] Wrote {len(corrected_lines)} pre-modification lines to -> {custom_corrected}")

    if file_has_nonempty_content(custom_corrected):
        corr_lines = read_text_lines(custom_corrected)
        mapping = {}
        for cl in corr_lines:
            cl2 = strip_non_visible_and_cr(cl)
            tok, _, _ = parse_object_token_after_prefix(cl2, PREFIX_CUSTOM)
            if tok is None:
                continue
            mapping[tok] = sanitize_object_name(tok)

        if mapping:
            rules_lines2 = read_text_lines(dst_rules)
            changed = 0
            new_rules = []
            for line in rules_lines2:
                line2 = line
                for orig, san in mapping.items():
                    if orig in line2:
                        line2 = line2.replace(orig, san)
                if line2 != line:
                    changed += 1
                new_rules.append(line2)
            write_text_lines(dst_rules, new_rules)
            print(f"[{now_ts()}] Updated forti-rules references for CUSTOM category names: {len(mapping)} names, {changed} lines changed")
        else:
            print(f"[{now_ts()}] CUSTOM corrected file non-empty but no mappings parsed (unexpected).")
    else:
        print(f"[{now_ts()}] CUSTOM corrected file empty -> skip forti-rules CUSTOM name correlation (step 17)")  # CHANGED

    rules_lines = read_text_lines(dst_rules)

    custom_name_file  = step6_dir / "step-6_extracted-custom-urlf-profile-name.txt"
    custom_clean_lines = read_text_lines(custom_cleaned)

    custom_names = extract_object_names_from_file(custom_clean_lines, PREFIX_CUSTOM)
    write_text_lines(custom_name_file, custom_names)
    print(f"[{now_ts()}] Extracted {len(custom_names)} unique CUSTOM names -> {custom_name_file}")

    urlf_clean_lines = read_text_lines(urlf_cleaned)

    used_custom = set()
    for name in custom_names:
        in_pan = False
        for line in rules_lines:
            tok = extract_first_token_after_phrase(line, PROFILE_SETTING_PHRASE)
            if tok is None:
                continue
            if len(tok) >= 2 and tok[0] == '"' and tok[-1] == '"':
                tok_norm = tok[1:-1].replace(" ", "_")
            else:
                tok_norm = tok
            if tok_norm == name:
                in_pan = True
                break

        in_urlf = False
        if not in_pan:
            for line in urlf_clean_lines:
                if urlf_line_references_name(line, name):
                    in_urlf = True
                    break
        else:
            in_urlf = True

        if in_pan or in_urlf:
            used_custom.add(name)

    unused_custom_names = [n for n in custom_names if n not in used_custom]
    print(f"[{now_ts()}] CUSTOM correlation: used={len(used_custom)} unused={len(unused_custom_names)}")

    unused_custom_file = step6_dir / "step-6_unused-custom-urlf-profile.txt"
    if unused_custom_names:
        keep, cut = cut_object_blocks(custom_clean_lines, PREFIX_CUSTOM, set(unused_custom_names))
        write_text_lines(custom_cleaned,   keep)
        write_text_lines(unused_custom_file, cut)
        print(f"[{now_ts()}] Moved UNUSED CUSTOM objects: {len(unused_custom_names)} names")
        print(f"[{now_ts()}]   kept lines={len(keep)} in {custom_cleaned}")
        print(f"[{now_ts()}]   cut  lines={len(cut)}  -> {unused_custom_file}")
    else:
        write_text_lines(unused_custom_file, [])
        print(f"[{now_ts()}] No unused CUSTOM objects found. Wrote empty file -> {unused_custom_file}")

    urlf_name_file   = step6_dir / "step-6_extracted-urlf-profile-name.txt"
    urlf_clean_lines = read_text_lines(urlf_cleaned)

    urlf_names = extract_object_names_from_file(urlf_clean_lines, PREFIX_URLF)
    write_text_lines(urlf_name_file, urlf_names)
    print(f"[{now_ts()}] Extracted {len(urlf_names)} unique URLF profile names -> {urlf_name_file}")

    used_urlf = set()
    for name in urlf_names:
        for line in rules_lines:
            tok = extract_first_token_after_phrase(line, PROFILE_SETTING_PHRASE)
            if tok is None:
                continue
            if len(tok) >= 2 and tok[0] == '"' and tok[-1] == '"':
                tok_norm = tok[1:-1].replace(" ", "_")
            else:
                tok_norm = tok
            if tok_norm == name:
                used_urlf.add(name)
                break

    unused_urlf_names = [n for n in urlf_names if n not in used_urlf]
    print(f"[{now_ts()}] URLF correlation: used={len(used_urlf)} unused={len(unused_urlf_names)}")

    unused_urlf_file = step6_dir / "step-6_unused-urlf-profile.txt"
    if unused_urlf_names:
        keep, cut = cut_object_blocks(urlf_clean_lines, PREFIX_URLF, set(unused_urlf_names))
        write_text_lines(urlf_cleaned,   keep)
        write_text_lines(unused_urlf_file, cut)
        print(f"[{now_ts()}] Moved UNUSED URLF profiles: {len(unused_urlf_names)} names")
        print(f"[{now_ts()}]   kept lines={len(keep)} in {urlf_cleaned}")
        print(f"[{now_ts()}]   cut  lines={len(cut)}  -> {unused_urlf_file}")
    else:
        write_text_lines(unused_urlf_file, [])
        print(f"[{now_ts()}] No unused URLF profiles found. Wrote empty file -> {unused_urlf_file}")

    final_dir = main_dir / "final-data"
    ensure_dir(final_dir)

    final_custom_dst = final_dir / "final-custom-urlf-profile.txt"
    final_urlf_dst   = final_dir / "final-urlf-profile.txt"

    shutil.copy2(custom_cleaned, final_custom_dst)
    shutil.copy2(urlf_cleaned,   final_urlf_dst)

    print(f"[{now_ts()}] Final outputs written to ../final-data/:")
    print(f"[{now_ts()}]   {custom_cleaned} -> {final_custom_dst}")
    print(f"[{now_ts()}]   {urlf_cleaned} -> {final_urlf_dst}")

    print(f"[{now_ts()}] Running end-of-script description inner-quote sanitation...")
    targets = [
        dst_rules,
        urlf_cleaned,
        custom_cleaned,
        final_custom_dst,
        final_urlf_dst,
    ]
    total_changed = 0
    for t in targets:
        c = sanitize_description_file(t)
        total_changed += c
        print(f"[{now_ts()}] Description-scan: changed {c} lines in {t}")
    print(f"[{now_ts()}] Description-scan summary: total changed lines = {total_changed}")

    print("=" * 80)
    print(f"[{now_ts()}] Step-6 DONE")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n[{now_ts()}] Interrupted by user (Ctrl+C).")
        raise
    except Exception as e:
        print(f"\n[{now_ts()}] ERROR: {e}")
        raise