#!/usr/bin/env python3

import logging
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

SCRIPT_DIR = Path(__file__).resolve().parent
MAIN_DIR = SCRIPT_DIR.parent

LOG_DIR = MAIN_DIR / "log"
LOG_FILE = LOG_DIR / "step-0.log"

DEFAULT_SOURCE = MAIN_DIR / "source-forti-config.conf"            # CHANGED: FortiGate config file

STEP0_DIR = MAIN_DIR / "step-0"
CLEANED_FILE = STEP0_DIR / "step-0_cleaned-forti-rules.txt"       # CHANGED: reflects FortiGate source

ZONE_OUT = MAIN_DIR / "zone-conversion.txt"
APP_OUT = STEP0_DIR / "predef-application-conversion.txt"
PROFILES_OUT = MAIN_DIR / "used-policy-security-profiles.txt"

def setup_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("step-0")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    fmt = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")

    fh = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    fh.setFormatter(fmt)
    fh.setLevel(logging.INFO)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    sh.setLevel(logging.INFO)

    logger.addHandler(fh)
    logger.addHandler(sh)

    logger.info("============================================================")
    logger.info("Step-0 start: %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("Script dir: %s", SCRIPT_DIR)
    logger.info("Main dir:   %s", MAIN_DIR)
    logger.info("Log file:   %s", LOG_FILE)
    logger.info("============================================================")

    return logger

def install_excepthook(logger: logging.Logger) -> None:
    def _hook(exc_type, exc, tb):
        logger.exception("Unhandled exception", exc_info=(exc_type, exc, tb))
    sys.excepthook = _hook

def input_with_timeout(prompt: str, timeout_sec: int, logger: logging.Logger) -> Optional[str]:


    logger.info(prompt)

    try:
        import msvcrt

        logger.info("Waiting up to %d seconds for input...", timeout_sec)
        start = time.time()
        buf = []

        while True:
            if msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch in ("\r", "\n"):
                    sys.stdout.write("\n")
                    sys.stdout.flush()
                    return "".join(buf)
                if ch == "\b":
                    if buf:
                        buf.pop()
                        sys.stdout.write("\b \b")
                        sys.stdout.flush()
                    continue
                buf.append(ch)
                sys.stdout.write(ch)
                sys.stdout.flush()

            if (time.time() - start) >= timeout_sec:
                sys.stdout.write("\n")
                sys.stdout.flush()
                return None

            time.sleep(0.05)

    except Exception:

        pass

    try:
        import select

        logger.info("Waiting up to %d seconds for input...", timeout_sec)
        sys.stdout.flush()

        rlist, _, _ = select.select([sys.stdin], [], [], timeout_sec)
        if rlist:
            return sys.stdin.readline().rstrip("\n")
        return None

    except Exception as e:

        logger.warning("Timed input not supported in this environment (%s). Falling back to blocking input().", e)
        try:
            return input().rstrip("\n")
        except EOFError:
            return None

def resolve_source_path(user_entry: Optional[str], logger: logging.Logger) -> Path:

    if user_entry is None:
        logger.info("No input received (timeout). Using default source: %s", DEFAULT_SOURCE)
        return DEFAULT_SOURCE

    entry = user_entry.strip()
    if entry == "":
        logger.info("User pressed Enter. Using default source: %s", DEFAULT_SOURCE)
        return DEFAULT_SOURCE

    p = Path(entry)
    if not p.is_absolute():
        p = (MAIN_DIR / p).resolve()

    logger.info("User provided source path: %s", p)
    return p

# CHANGED: matches FortiGate flattened format: firewall policy "NAME" <remainder>
#          was: r'\bsecurity rules\s+("([^"]+)"|(\S+))'
SEC_RULE_RE = re.compile(r'\bfirewall policy\s+("([^"]+)"|(\S+))')

# CHANGED: Fortinet UTM/security profile attribute keywords
#          was: r'^profile-setting profiles (file-blocking|virus|spyware|vulnerability)\b'
PROFILE_RE = re.compile(r'^(av-profile|webfilter-profile|ips-sensor|application-list|dnsfilter-profile|ssl-ssh-profile|profile-group)\b')

# CHANGED: Fortinet uses 'logtraffic' where PAN uses 'log-setting'
#          was: r'\blog-setting\b'
LOG_SETTING_RE = re.compile(r'\blogtraffic\b')

ALLOWED_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]+$")

def extract_policy_remainder(line: str):
    # Unchanged — SEC_RULE_RE update above is all that is needed here
    m = SEC_RULE_RE.search(line)
    if not m:
        return None, None
    policy_name = m.group(2) if m.group(2) is not None else m.group(3)
    remainder = line[m.end():].strip()
    return policy_name, remainder

def tokenize_list_tail(tail: str):
    # CHANGED: also strip surrounding quotes from each token (FortiGate quotes values)
    out = []
    for tok in tail.split():
        if tok == "[" or tok == "]":
            continue
        t = tok.strip().strip("[]\"'")      # added strip of " and '
        if t:
            out.append(t)
    return out

def warn_if_undesirable(logger: logging.Logger, token: str, context: str, lineno: int) -> None:
    if not ALLOWED_TOKEN_RE.match(token):
        logger.warning(
            "Undesirable chars detected in %s token at line %d: '%s' (allowed: alnum, '-', '_')",
            context, lineno, token
        )

def normalize_tokens(tokens):
    # CHANGED: also strip surrounding quotes (FortiGate quotes values e.g. "always", "ALL")
    return [t.strip().strip("[]\"'") for t in tokens if t.strip().strip("[]\"'")]

def should_remove_security_rules_line(remainder: str):

    # CHANGED: 'logtraffic' is Fortinet's equivalent of PAN's 'log-setting' (step-9)
    if LOG_SETTING_RE.search(remainder):
        return True, "step-9 contains logtraffic"

    toks = normalize_tokens(remainder.split())
    if not toks:
        return False, ""

    # CHANGED: Fortinet uses "all" where PAN uses "any" (catch-all / default value)
    if toks[-1] == "all":
        return True, "step-8 endswith all"

    # CHANGED: 'service ALL' is Fortinet's equivalent of PAN's 'service application-default'
    if len(toks) >= 2 and toks[-2:] == ["service", "ALL"]:
        return True, "step-8 endswith service ALL"

    # CHANGED: 'utm-status disable' = no security profiles applied
    #          equivalent of PAN's 'profile-setting group Drop_Default'
    if len(toks) >= 2 and toks[-2:] == ["utm-status", "disable"]:
        return True, "step-8 endswith utm-status disable"

    # CHANGED: 'status enable' is the default enabled state
    #          equivalent of PAN's 'target negate no'
    if len(toks) >= 2 and toks[-2:] == ["status", "enable"]:
        return True, "step-8 endswith status enable"

    # CHANGED: 'schedule always' = always-on / universal schedule
    #          equivalent of PAN's 'rule-type universal'
    if len(toks) >= 2 and toks[-2:] == ["schedule", "always"]:
        return True, "step-8 endswith schedule always"

    return False, ""

# NEW FUNCTION: converts FortiGate block-style policy config into flat per-attribute lines.
#
# FortiGate 'config firewall policy' blocks look like:
#     config firewall policy
#         edit 1
#             set name "PolicyName"
#             set srcintf "wan1"
#             set dstintf "internal"
#             ...
#         next
#     end
#
# Each block is expanded into one flat line per attribute:
#     firewall policy "PolicyName" srcintf wan1
#     firewall policy "PolicyName" dstintf internal
#     ...
#
# This allows all downstream functions (clean_in_place, extract_outputs) to work
# exactly as before without structural changes.
def flatten_fortigate_config(source_path: Path, flat_path: Path, logger: logging.Logger) -> None:

    logger.info("Flattening FortiGate block config: %s -> %s", source_path, flat_path)

    with source_path.open("r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    flat_lines = []
    in_policy_block = False
    current_name = None        # policy name (from 'set name'); falls back to edit id
    policy_attrs = []          # accumulated (keyword, raw_value) pairs for current policy

    for raw in lines:
        stripped = raw.strip()

        if stripped == "config firewall policy":
            in_policy_block = True
            continue

        if not in_policy_block:
            continue

        if stripped.startswith("edit "):
            # Start of a new policy entry; use edit-id as name until 'set name' is seen
            current_name = stripped[5:].strip().strip('"')
            policy_attrs = []

        elif stripped == "next":
            # End of policy entry — emit one flat line per collected attribute
            if current_name is not None:
                for kw, val in policy_attrs:
                    flat_lines.append('firewall policy "{}" {} {}\n'.format(current_name, kw, val))
            current_name = None
            policy_attrs = []

        elif stripped == "end":
            in_policy_block = False

        elif stripped.startswith("set "):
            rest = stripped[4:]
            parts = rest.split(None, 1)
            if not parts:
                continue
            keyword = parts[0]
            value = parts[1] if len(parts) > 1 else ""
            if keyword == "name":
                # Override edit-id with the real policy name
                current_name = value.strip('"')
            else:
                policy_attrs.append((keyword, value))

    with flat_path.open("w", encoding="utf-8") as out:
        for line in flat_lines:
            out.write(line)

    logger.info("Flattening complete: %d policy attribute lines written.", len(flat_lines))

# NEW FUNCTION: converts 'config application list' blocks into flat per-entry lines,
# then APPENDS them to the same flat_path already written by flatten_fortigate_config.
#
# FortiGate 'config application list' blocks have two nesting levels:
#
#     config application list
#         edit "App_Control_Standard"           <- list name
#             set comment "..."
#             set unknown-application-action block
#             config entries                    <- sub-block
#                 edit 1                        <- entry id
#                     set category 2 6
#                     set action block
#                     set log enable
#                 next
#                 edit 2
#                     set application 15832
#                     set action block
#                 next
#             end                               <- exit sub-block
#         next                                  <- exit list entry
#     end                                       <- exit config block
#
# Each entry is emitted as one flat line combining category/application + action:
#   application list "App_Control_Standard" comment "..."
#   application list "App_Control_Standard" unknown-application-action block
#   application list "App_Control_Standard" entry 1 category 2 6 action block
#   application list "App_Control_Standard" entry 2 application 15832 action block
#
# Lines are APPENDed so they follow the firewall policy lines in the cleaned file.
# They do NOT match SEC_RULE_RE so they pass through clean_in_place unchanged (kept).
def flatten_application_list(source_path: Path, flat_path: Path, logger: logging.Logger) -> None:

    logger.info("Appending 'config application list' entries from: %s", source_path)

    with source_path.open("r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    flat_lines = []

    in_applist_block  = False   # inside 'config application list'
    in_entries_block  = False   # inside nested 'config entries'
    current_list_name = None    # name from 'edit "name"' at list level
    list_top_attrs    = []      # top-level set attrs (comment, unknown-application-action, ...)
    current_entry_id  = None    # edit N inside 'config entries'
    entry_attrs       = {}      # accumulates set keyword->value for current entry

    for raw in lines:
        stripped = raw.strip()

        # Skip comment lines
        if stripped.startswith("#"):
            continue

        # ---- detect block start ----
        if stripped == "config application list":
            in_applist_block = True
            in_entries_block = False
            current_list_name = None
            list_top_attrs = []
            continue

        if not in_applist_block:
            continue

        # ---- inside application list block ----

        if stripped == "config entries":
            # Enter the nested entries sub-block
            in_entries_block = True
            current_entry_id = None
            entry_attrs = {}
            continue

        if in_entries_block:

            if stripped.startswith("edit "):
                # New entry inside 'config entries'
                current_entry_id = stripped[5:].strip().strip('"')
                entry_attrs = {}

            elif stripped == "next":
                # Emit one flat line per entry, combining category/application + action
                if current_entry_id is not None and current_list_name is not None:
                    # Build the entry summary: prefer 'category' over 'application'
                    subject = entry_attrs.get("category") or entry_attrs.get("application", "")
                    kw      = "category" if "category" in entry_attrs else "application"
                    action  = entry_attrs.get("action", "")
                    parts   = [kw, subject]
                    if action:
                        parts += ["action", action]
                    flat_lines.append(
                        'application list "{}" entry {} {}\n'.format(
                            current_list_name,
                            current_entry_id,
                            " ".join(parts)
                        )
                    )
                current_entry_id = None
                entry_attrs = {}

            elif stripped == "end":
                # Exit the nested entries sub-block, back to list level
                in_entries_block = False
                current_entry_id = None
                entry_attrs = {}

            elif stripped.startswith("set "):
                rest  = stripped[4:]
                parts = rest.split(None, 1)
                if parts:
                    kw  = parts[0]
                    val = parts[1] if len(parts) > 1 else ""
                    entry_attrs[kw] = val

        else:
            # Top level of the list entry (outside 'config entries')

            if stripped.startswith("edit "):
                # Start of a new named list entry
                current_list_name = stripped[5:].strip().strip('"')
                list_top_attrs = []

            elif stripped == "next":
                # Emit top-level attribute lines, then reset for next list entry
                for kw, val in list_top_attrs:
                    flat_lines.append(
                        'application list "{}" {} {}\n'.format(current_list_name, kw, val)
                    )
                current_list_name = None
                list_top_attrs = []

            elif stripped == "end":
                # Exit the entire 'config application list' block
                in_applist_block = False

            elif stripped.startswith("set "):
                rest  = stripped[4:]
                parts = rest.split(None, 1)
                if parts:
                    kw  = parts[0]
                    val = parts[1] if len(parts) > 1 else ""
                    list_top_attrs.append((kw, val))

    if not flat_lines:
        logger.info("No 'config application list' entries found — nothing appended.")
        return

    # APPEND to the existing flat file (firewall policy lines already written there)
    with flat_path.open("a", encoding="utf-8") as out:
        for line in flat_lines:
            out.write(line)

    logger.info(
        "Application list flattening complete: %d entry lines appended.", len(flat_lines)
    )

def copy_source_to_step0(source_path: Path, logger: logging.Logger) -> None:
    STEP0_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Ensured step directory exists: %s", STEP0_DIR)

    logger.info("Flattening FortiGate source to cleaned working file...")
    logger.info("  from: %s", source_path)
    logger.info("  to:   %s", CLEANED_FILE)

    # CHANGED: call flatten instead of shutil.copy2 — FortiGate blocks must be
    #          converted to flat lines before clean_in_place / extract_outputs can run.
    #          was: shutil.copy2(source_path, CLEANED_FILE)
    flatten_fortigate_config(source_path, CLEANED_FILE, logger)

    # NEW: also flatten 'config application list' blocks and append to same cleaned file
    flatten_application_list(source_path, CLEANED_FILE, logger)

    logger.info("Flatten complete.")

def clean_in_place(logger: logging.Logger) -> None:

    logger.info("Cleaning file in place (steps 8 & 9): %s", CLEANED_FILE)

    if not CLEANED_FILE.exists():
        logger.error("Cleaned working file not found: %s", CLEANED_FILE)
        raise FileNotFoundError(str(CLEANED_FILE))

    kept_lines = []
    total = 0
    sec_rules = 0
    removed = 0
    reasons = {}

    with CLEANED_FILE.open("r", encoding="utf-8", errors="replace") as f:
        for lineno, raw in enumerate(f, start=1):
            total += 1
            line = raw.rstrip("\r\n")

            policy_name, remainder = extract_policy_remainder(line)
            if policy_name is None:
                kept_lines.append(line)
                continue

            sec_rules += 1
            do_remove, reason = should_remove_security_rules_line(remainder)
            if do_remove:
                removed += 1
                reasons[reason] = reasons.get(reason, 0) + 1
                logger.info("REMOVED line %d (policy='%s') reason=%s :: %s", lineno, policy_name, reason, line)
                continue

            kept_lines.append(line)

    with CLEANED_FILE.open("w", encoding="utf-8") as out:
        for l in kept_lines:
            out.write(l + "\n")

    logger.info("Cleaning summary:")
    logger.info("  Total lines read:               %d", total)
    logger.info("  Lines with 'firewall policy':   %d", sec_rules)  # CHANGED label
    logger.info("  Lines removed:                  %d", removed)
    for k in sorted(reasons.keys()):
        logger.info("    %s: %d", k, reasons[k])

def extract_outputs(logger: logging.Logger) -> None:

    logger.info("Extracting zone/service/security-profile info from: %s", CLEANED_FILE)

    if not CLEANED_FILE.exists():
        logger.error("Cleaned working file not found: %s", CLEANED_FILE)
        raise FileNotFoundError(str(CLEANED_FILE))

    zones_seen = {}
    apps_seen = {}
    profile_lines = []

    total = 0
    sec_rules = 0
    zone_lines = 0
    app_lines = 0
    prof_lines = 0
    zone_dupes = 0
    app_dupes = 0

    with CLEANED_FILE.open("r", encoding="utf-8", errors="replace") as f:
        for lineno, raw in enumerate(f, start=1):
            total += 1
            line = raw.rstrip("\r\n")

            policy_name, remainder = extract_policy_remainder(line)
            if policy_name is None:
                continue

            sec_rules += 1

            # CHANGED: FortiGate uses 'dstintf' / 'srcintf' instead of PAN's 'to' / 'from'
            if remainder.startswith("dstintf ") or remainder.startswith("srcintf "):
                zone_lines += 1
                kw = remainder.split(None, 1)[0]
                tail = remainder[len(kw):].strip()
                tokens = tokenize_list_tail(tail)   # quotes already stripped by tokenize_list_tail

                logger.info("Line %d: policy='%s' keyword='%s' zoneTokens=%s", lineno, policy_name, kw, tokens)
                for t in tokens:
                    warn_if_undesirable(logger, t, "zone", lineno)
                    if t in zones_seen:
                        zone_dupes += 1
                        continue
                    zones_seen[t] = None

            # CHANGED: FortiGate uses 'service' where PAN used 'application'
            #          (service objects are the closest FortiGate equivalent)
            if remainder.startswith("service "):
                app_lines += 1
                tail = remainder[len("service"):].strip()
                tokens = tokenize_list_tail(tail)   # quotes already stripped by tokenize_list_tail

                logger.info("Line %d: policy='%s' keyword='service' serviceTokens=%s", lineno, policy_name, tokens)
                for t in tokens:
                    warn_if_undesirable(logger, t, "service", lineno)
                    if t in apps_seen:
                        app_dupes += 1
                        continue
                    apps_seen[t] = None

            if PROFILE_RE.match(remainder):
                prof_lines += 1
                profile_lines.append(line)
                logger.info("Line %d: policy='%s' matched security profile line", lineno, policy_name)

    logger.info("Writing: %s", ZONE_OUT)
    with ZONE_OUT.open("w", encoding="utf-8") as outz:
        for z in zones_seen.keys():
            outz.write("{} >>\n".format(z))

    logger.info("Writing: %s", APP_OUT)
    with APP_OUT.open("w", encoding="utf-8") as outa:
        for a in apps_seen.keys():
            outa.write("{} >>\n".format(a))

    logger.info("Writing: %s", PROFILES_OUT)
    with PROFILES_OUT.open("w", encoding="utf-8") as outp:
        for pl in profile_lines:
            outp.write(pl + "\n")

    logger.info("Extraction summary:")
    logger.info("  Total lines read:               %d", total)
    logger.info("  Lines with 'firewall policy':   %d", sec_rules)  # CHANGED label
    logger.info("  Zone lines matched:             %d", zone_lines)
    logger.info("  Unique zones written:           %d", len(zones_seen))
    logger.info("  Zone duplicates skipped:        %d", zone_dupes)
    logger.info("  Service lines matched:          %d", app_lines)  # CHANGED label
    logger.info("  Unique services written:        %d", len(apps_seen))
    logger.info("  Service duplicates skipped:     %d", app_dupes)
    logger.info("  Security profile lines:         %d", prof_lines)

def main() -> int:
    logger = setup_logging()
    install_excepthook(logger)

    prompt = (
        "Enter source file path (default: {}).\n"
        "- Press Enter to use default.\n"
        "- Or type a different path (absolute or relative to MAIN dir).\n"
        "Waiting 60 seconds...".format(DEFAULT_SOURCE)
    )
    user_in = input_with_timeout(prompt, 15, logger)
    source_path = resolve_source_path(user_in, logger)

    if not source_path.exists():
        logger.error("Source file not found: %s", source_path)
        return 1
    if not source_path.is_file():
        logger.error("Source path is not a file: %s", source_path)
        return 1

    copy_source_to_step0(source_path, logger)

    clean_in_place(logger)

    extract_outputs(logger)

    msg = (
        "All FortiGate policy security profiles will be converted to Versa default security profile. "
        "Please review the information in used-policy-security-profiles.txt"
    )
    logger.info(msg)

    logger.info("Step-0 complete.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())