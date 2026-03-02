#!/usr/bin/env python3
from __future__ import annotations

import logging
import re
import shutil
import signal
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

ACCEPTED_NAME_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
DEFAULT_MAX_NAME_LEN = 63

DEFAULT_SOURCE_REL = "../step-0/step-0_cleaned-pan-rules.txt"

LOG_FILENAME = "step-1.log"

OUT_COPY_FILENAME = "step-1_cleaned-pan-rules.txt"
OUT_MODIFIED_POLICIES_FILENAME = "step-1_modified-policy-name.txt"
OUT_POLICY_EXCEPTIONS_FILENAME = "step-1_policy-exceptions.txt"

RE_SEC_RULES = re.compile(r"(?i)\bsecurity\s+rules\b")
RE_DESC_OPEN = re.compile(r'(?i)\bdescription\b\s+"')
RE_DESC_QUOTED = re.compile(r'(?i)\bdescription\b\s+"[^"]*"')

@dataclass
class Paths:
    script_path: Path
    scripts_dir: Path
    main_dir: Path
    log_dir: Path
    step1_dir: Path
    log_path: Path

    source_path: Path
    working_copy_path: Path

    modified_policies_path: Path
    policy_exceptions_path: Path

@dataclass
class PolicyLineInfo:
    policy_name: str
    is_quoted: bool
    name_span: Tuple[int, int]

def setup_logger(log_path: Path) -> logging.Logger:
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("step-1")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    fh = logging.FileHandler(log_path, encoding="utf-8", mode="w")
    fh.setLevel(logging.INFO)
    fh.setFormatter(fmt)

    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger

def echo(logger: logging.Logger, msg: str) -> None:
    logger.info(msg)

class _InputTimeout(Exception):
    pass

def _alarm_handler(signum, frame):
    raise _InputTimeout()

def timed_input(logger: logging.Logger, prompt_msg: str, default: str, timeout_sec: int) -> str:

    echo(logger, prompt_msg)
    echo(logger, f"(Waiting 15s. Default: {default})")

    if not sys.stdin.isatty():
        echo(logger, "STDIN is not interactive; using default.")
        return default

    old = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, _alarm_handler)
    signal.alarm(15)
    try:
        s = input("> ").strip()
        if not s:
            echo(logger, "No input (Enter). Using default.")
            return default
        return s
    except _InputTimeout:
        echo(logger, "Timed out. Using default.")
        return default
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)

def normalize_user_path(s: str) -> str:
    return s.strip().replace("\\", "/")

def resolve_user_path(user_str: str, scripts_dir: Path) -> Path:
    p = Path(normalize_user_path(user_str)).expanduser()
    if not p.is_absolute():
        p = (scripts_dir / p)
    return p.resolve()

def build_paths(source_path: Path) -> Paths:
    script_path = Path(__file__).resolve()
    scripts_dir = script_path.parent
    main_dir = scripts_dir.parent

    log_dir = main_dir / "log"
    step1_dir = main_dir / "step-1"

    log_path = log_dir / LOG_FILENAME

    working_copy_path = step1_dir / OUT_COPY_FILENAME
    modified_policies_path = step1_dir / OUT_MODIFIED_POLICIES_FILENAME
    policy_exceptions_path = step1_dir / OUT_POLICY_EXCEPTIONS_FILENAME

    return Paths(
        script_path=script_path,
        scripts_dir=scripts_dir,
        main_dir=main_dir,
        log_dir=log_dir,
        step1_dir=step1_dir,
        log_path=log_path,
        source_path=source_path,
        working_copy_path=working_copy_path,
        modified_policies_path=modified_policies_path,
        policy_exceptions_path=policy_exceptions_path,
    )

def parse_policy_info(line: str) -> Optional[PolicyLineInfo]:

    m = RE_SEC_RULES.search(line)
    if not m:
        return None

    idx = m.end()
    n = len(line)

    while idx < n and line[idx].isspace():
        idx += 1
    if idx >= n:
        return None

    if line[idx] == '"':
        start = idx
        idx += 1
        end_quote = line.find('"', idx)
        if end_quote == -1:
            return None
        name = line[idx:end_quote]
        span = (start, end_quote + 1)
        return PolicyLineInfo(policy_name=name, is_quoted=True, name_span=span)

    start = idx
    while idx < n and not line[idx].isspace():
        idx += 1
    name = line[start:idx]
    span = (start, idx)
    return PolicyLineInfo(policy_name=name, is_quoted=False, name_span=span)

def iter_logical_lines_join_description(path: Path, logger: logging.Logger) -> Iterable[str]:

    merges = 0
    buf = ""
    in_desc = False
    desc_open_end = -1

    with open(path, "rb") as f:
        while True:
            bline = f.readline()
            if not bline:
                break

            if bline.endswith(b"\n"):
                bline = bline[:-1]
            if bline.endswith(b"\r"):
                bline = bline[:-1]

            seg = bline.decode("utf-8", errors="surrogateescape")

            if buf == "":
                buf = seg
            else:
                merges += 1
                buf += " " + seg

            if not in_desc:
                m = RE_DESC_OPEN.search(buf)
                if m:
                    close_idx = buf.find('"', m.end())
                    if close_idx == -1:
                        in_desc = True
                        desc_open_end = m.end()
            else:
                close_idx = buf.find('"', desc_open_end)
                if close_idx != -1:
                    in_desc = False
                    desc_open_end = -1

            if not in_desc:
                yield buf
                buf = ""

    if buf:
        logger.warning("EOF while still inside an open description quote; emitting last buffered line.")
        yield buf

    logger.info(f"Logical-line join summary: merged {merges} physical line(s) into description line(s).")

def _remove_nonvisible_outside_desc_segment(s: str) -> str:
    out = []
    for ch in s:
        if ch in (" ", "\t"):
            out.append(ch)
        elif ch.isprintable():
            out.append(ch)

    return "".join(out)

def remove_invisible_outside_description(line: str) -> str:

    if not line:
        return line

    line = line.replace("\r", "")

    parts: List[str] = []
    last = 0
    for m in RE_DESC_QUOTED.finditer(line):
        parts.append(_remove_nonvisible_outside_desc_segment(line[last:m.start()]))
        parts.append(line[m.start():m.end()])
        last = m.end()
    parts.append(_remove_nonvisible_outside_desc_segment(line[last:]))

    return "".join(parts)

def transform_policy_name(name: str, was_quoted: bool, max_len: int) -> Tuple[str, bool, List[str]]:

    reasons: List[str] = []
    changed = False
    new_name = name

    if was_quoted:
        changed = True
        reasons.append("remove_quotes")
        if " " in new_name:
            new_name2 = new_name.replace(" ", "_")
            if new_name2 != new_name:
                new_name = new_name2
                reasons.append("spaces_to_underscores")

    rebuilt = []
    invalid_hit = False
    for ch in new_name:
        if ch in ACCEPTED_NAME_CHARS:
            rebuilt.append(ch)
        else:
            rebuilt.append("_")
            invalid_hit = True
    if invalid_hit:
        changed = True
        reasons.append("replace_invalid_chars")

    new_name = "".join(rebuilt)

    if len(new_name) > max_len:
        changed = True
        reasons.append(f"truncate_to_{max_len}")
        new_name = new_name[:max_len]

    return new_name, changed, reasons

def is_policy_name_valid_no_replace(name: str, was_quoted: bool, max_len: int) -> Tuple[bool, str]:

    if not name:
        return False, "empty_name"
    if was_quoted:
        return False, "quoted_name_not_allowed"
    if " " in name:
        return False, "spaces_not_allowed"
    if len(name) > max_len:
        return False, f"length_{len(name)}_exceeds_{max_len}"
    if any(ch not in ACCEPTED_NAME_CHARS for ch in name):
        return False, "contains_invalid_chars"
    return True, "ok"

def replace_policy_name_in_line(line: str, info: PolicyLineInfo, new_name: str) -> str:

    a, b = info.name_span
    return line[:a] + new_name + line[b:]

def sanitize_working_copy_in_place(paths: Paths, logger: logging.Logger) -> List[str]:

    lines: List[str] = []
    for logical in iter_logical_lines_join_description(paths.working_copy_path, logger):
        lines.append(remove_invisible_outside_description(logical))

    tmp = paths.working_copy_path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8", errors="surrogateescape", newline="\n") as out:
        for l in lines:
            out.write(l + "\n")
    tmp.replace(paths.working_copy_path)

    echo(logger, f"Step-8: sanitized and rewrote: {paths.working_copy_path}")
    echo(logger, f"Step-8: logical lines count: {len(lines)}")
    return lines

def build_policy_index(lines: List[str]) -> Tuple[Dict[str, List[int]], Dict[str, bool]]:

    policy_to_idx: Dict[str, List[int]] = {}
    policy_any_quoted: Dict[str, bool] = {}

    for i, line in enumerate(lines):
        info = parse_policy_info(line)
        if not info:
            continue
        policy_to_idx.setdefault(info.policy_name, []).append(i)
        policy_any_quoted[info.policy_name] = policy_any_quoted.get(info.policy_name, False) or info.is_quoted

    return policy_to_idx, policy_any_quoted

def main() -> int:
    scripts_dir = Path(__file__).resolve().parent
    main_dir = scripts_dir.parent

    default_source_path = (main_dir / "source-pan-rules.txt").resolve()
    paths = build_paths(default_source_path)
    logger = setup_logger(paths.log_path)

    echo(logger, "==== STEP-1 START ====")
    echo(logger, f"Script path:  {paths.script_path}")
    echo(logger, f"Scripts dir:  {scripts_dir}")
    echo(logger, f"Main dir:     {main_dir}")
    echo(logger, f"Log file:     {paths.log_path}")

    echo(logger, "Maximum policy name is 63 characters by default.")
    echo(logger, "Any policy name longer than the chosen max will be truncated.")
    max_len_str = timed_input(
        logger,
        f"******** Enter max policy name length (1-{DEFAULT_MAX_NAME_LEN}) or press Enter for default {DEFAULT_MAX_NAME_LEN}: ********",
        str(DEFAULT_MAX_NAME_LEN),
        60,
    )
    try:
        max_len = int(max_len_str)
    except ValueError:
        max_len = DEFAULT_MAX_NAME_LEN
        echo(logger, f"Invalid number '{max_len_str}', using default {DEFAULT_MAX_NAME_LEN}.")

    if max_len < 1:
        max_len = 1
    if max_len > DEFAULT_MAX_NAME_LEN:
        max_len = DEFAULT_MAX_NAME_LEN

    echo(logger, f"Using max policy name length = {max_len}")

    echo(logger, f'Default source file is "{DEFAULT_SOURCE_REL}" in the main working directory.')
    user_source = timed_input(
        logger,
        f'Enter source file path (press Enter for default "{DEFAULT_SOURCE_REL}")',
        DEFAULT_SOURCE_REL,
        60,
    )
    source_path = resolve_user_path(user_source, scripts_dir)

    paths = build_paths(source_path)
    logger = setup_logger(paths.log_path)

    echo(logger, "---- Resolved Paths ----")
    echo(logger, f"Source file:       {paths.source_path}")
    echo(logger, f"Step-1 directory:  {paths.step1_dir}")
    echo(logger, f"Working copy:      {paths.working_copy_path}")
    echo(logger, f"Log file:          {paths.log_path}")

    if not paths.source_path.exists():
        echo(logger, f"ERROR: source file not found: {paths.source_path}")
        echo(logger, "==== STEP-1 END (ERROR) ====")
        return 2

    paths.step1_dir.mkdir(parents=True, exist_ok=True)
    paths.log_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(paths.source_path, paths.working_copy_path)
    echo(logger, f"Copied source -> {paths.working_copy_path}")

    echo(logger, "Only alphanumeric characters, '_' and '-' are accepted in Versa firewall rule names.")
    ans = timed_input(
        logger,
        '********* Accept replacing any unacceptable characters within policy names with "_" ? (Y/n) *********',
        "Y",
        60,
    ).strip().lower()
    do_replace = not (ans in ("n", "no"))
    echo(logger, f"Replacement mode: {'YES' if do_replace else 'NO'}")

    lines = sanitize_working_copy_in_place(paths, logger)

    policy_to_idx, policy_any_quoted = build_policy_index(lines)
    echo(logger, f"Detected policies: {len(policy_to_idx)}")

    if do_replace:

        mappings: Dict[str, Tuple[str, List[str]]] = {}
        for old_name in policy_to_idx.keys():
            was_quoted = policy_any_quoted.get(old_name, False)
            new_name, changed, reasons = transform_policy_name(old_name, was_quoted, max_len)
            if changed and new_name != old_name:
                mappings[old_name] = (new_name, reasons)

        if not mappings:
            echo(logger, "No policy-name changes required. (No quotes/spaces/invalid chars/overlength detected.)")
            echo(logger, "==== STEP-1 DONE ====")
            return 0

        reverse: Dict[str, List[str]] = {}
        for old, (new, _) in mappings.items():
            reverse.setdefault(new, []).append(old)

        collisions = {new: olds for new, olds in reverse.items() if len(olds) > 1}
        if collisions:
            echo(logger, "ERROR: policy-name collisions detected after normalization/truncation.")
            echo(logger, "These different old names would become the SAME new name:")
            for new in sorted(collisions.keys())[:200]:
                echo(logger, f'  new="{new}"  olds={collisions[new]}')
            echo(logger, "No replacements applied. Please adjust max length or naming strategy.")
            echo(logger, "==== STEP-1 STOPPED (collision) ====")
            return 3

        echo(logger, f"Policy name changes needed: {len(mappings)} policy(ies).")
        echo(logger, f"Writing BEFORE-change configs to: {paths.modified_policies_path}")

        with open(paths.modified_policies_path, "w", encoding="utf-8", errors="surrogateescape", newline="\n") as out:
            for old in sorted(mappings.keys()):
                for idx in policy_to_idx[old]:
                    out.write(lines[idx] + "\n")
                out.write("\n")

        echo(logger, "Applying policy-name replacements into working copy now (after writing the BEFORE-change file).")

        new_lines = lines[:]
        changed_line_count = 0

        for i, line in enumerate(lines):
            info = parse_policy_info(line)
            if not info:
                continue
            if info.policy_name in mappings:
                new_name = mappings[info.policy_name][0]
                replaced = replace_policy_name_in_line(line, info, new_name)
                if replaced != line:
                    new_lines[i] = replaced
                    changed_line_count += 1

        tmp = paths.working_copy_path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8", errors="surrogateescape", newline="\n") as out:
            for l in new_lines:
                out.write(l + "\n")
        tmp.replace(paths.working_copy_path)

        echo(logger, f"Replacements applied. Lines modified: {changed_line_count}")
        echo(logger, f"Updated working copy written to: {paths.working_copy_path}")

        echo(logger, "---- Policy-name mapping (applied) ----")
        for old in sorted(mappings.keys())[:200]:
            new, reasons = mappings[old]
            echo(logger, f'  "{old}"  ->  "{new}"  reasons={",".join(reasons)}')
        if len(mappings) > 200:
            echo(logger, f"  ... {len(mappings) - 200} more mappings not shown")

        echo(logger, "==== STEP-1 STOPPED (after applying replacements per step #12) ====")
        return 0

    else:

        invalid: Dict[str, str] = {}
        for pol in policy_to_idx.keys():
            was_quoted = policy_any_quoted.get(pol, False)
            ok, reason = is_policy_name_valid_no_replace(pol, was_quoted, max_len)
            if not ok:
                invalid[pol] = reason

        echo(logger, f"Invalid policies to move to exceptions: {len(invalid)}")

        exc_lines = 0
        kept_lines = 0

        with open(paths.policy_exceptions_path, "w", encoding="utf-8", errors="surrogateescape", newline="\n") as exc_out:
            tmp = paths.working_copy_path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8", errors="surrogateescape", newline="\n") as ok_out:
                for line in lines:
                    info = parse_policy_info(line)
                    if not info:
                        ok_out.write(line + "\n")
                        kept_lines += 1
                        continue

                    if info.policy_name in invalid:
                        exc_out.write(line + "\n")
                        exc_lines += 1
                    else:
                        ok_out.write(line + "\n")
                        kept_lines += 1
            tmp.replace(paths.working_copy_path)

        echo(logger, f"Wrote exceptions to: {paths.policy_exceptions_path} (lines moved: {exc_lines})")
        echo(logger, f"Rewrote working copy: {paths.working_copy_path} (lines kept: {kept_lines})")

        if invalid:
            echo(logger, "---- Invalid policy reasons ----")
            for pol in sorted(invalid.keys())[:200]:
                echo(logger, f'  "{pol}": {invalid[pol]}')
            if len(invalid) > 200:
                echo(logger, f"  ... {len(invalid) - 200} more not shown")

        echo(logger, "==== STEP-1 DONE ====")
        return 0

if __name__ == "__main__":
    raise SystemExit(main())
