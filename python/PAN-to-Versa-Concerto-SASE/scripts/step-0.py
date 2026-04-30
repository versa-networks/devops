
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

DEFAULT_SOURCE = MAIN_DIR / "source-pan-rules.txt"

STEP0_DIR = MAIN_DIR / "step-0"
CLEANED_FILE = STEP0_DIR / "step-0_cleaned-pan-rules.txt"

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

def print_box(text):
    lines = text.split('\n')
    max_len = max(len(line) for line in lines)
    print('╔' + '═' * (max_len + 2) + '╗')
    for line in lines:
        print('║ ' + line.ljust(max_len) + ' ║')
    print('╚' + '═' * (max_len + 2) + '╝')

def input_with_timeout(prompt: str, timeout_sec: int, logger: logging.Logger) -> Optional[str]:

    print_box(prompt + f'\n(auto-continue in {timeout_sec}s if no input)')

    try:
        import msvcrt

        logger.info("Waiting up to %d seconds for input...", timeout_sec)
        sys.stdout.write('> ')
        sys.stdout.flush()
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
        sys.stdout.write('> ')
        sys.stdout.flush()

        rlist, _, _ = select.select([sys.stdin], [], [], timeout_sec)
        if rlist:
            return sys.stdin.readline().rstrip("\n")
        return None

    except Exception as e:

        logger.warning("Timed input not supported in this environment (%s). Falling back to blocking input().", e)
        try:
            sys.stdout.write('> ')
            sys.stdout.flush()
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

SEC_RULE_RE = re.compile(r'\bsecurity rules\s+("([^"]+)"|(\S+))')
PROFILE_RE = re.compile(r'^profile-setting profiles (file-blocking|virus|spyware|vulnerability)\b')
LOG_SETTING_RE = re.compile(r'\blog-setting\b')
ALLOWED_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]+$")

def extract_policy_remainder(line: str):

    m = SEC_RULE_RE.search(line)
    if not m:
        return None, None
    policy_name = m.group(2) if m.group(2) is not None else m.group(3)
    remainder = line[m.end():].strip()
    return policy_name, remainder

def tokenize_list_tail(tail: str):

    out = []
    for tok in tail.split():
        if tok == "[" or tok == "]":
            continue
        t = tok.strip().strip("[]")
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
    return [t.strip().strip("[]") for t in tokens if t.strip().strip("[]")]

def should_remove_security_rules_line(remainder: str):

    if LOG_SETTING_RE.search(remainder):
        return True, "step-9 contains log-setting"

    toks = normalize_tokens(remainder.split())
    if not toks:
        return False, ""

    if toks[-1] == "any":
        return True, "step-8 endswith any"

    if len(toks) >= 2 and toks[-2:] == ["service", "application-default"]:
        return True, "step-8 endswith service application-default"

    if len(toks) >= 3 and toks[-3:] == ["profile-setting", "group", "Drop_Default"]:
        return True, "step-8 endswith profile-setting group Drop_Default"

    if len(toks) >= 3 and toks[-3:] == ["target", "negate", "no"]:
        return True, "step-8 endswith target negate no"

    if len(toks) >= 2 and toks[-2:] == ["rule-type", "universal"]:
        return True, "step-8 endswith rule-type universal"

    return False, ""

def copy_source_to_step0(source_path: Path, logger: logging.Logger) -> None:
    STEP0_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Ensured step directory exists: %s", STEP0_DIR)

    logger.info("Copying source file to cleaned working file...")
    logger.info("  from: %s", source_path)
    logger.info("  to:   %s", CLEANED_FILE)

    shutil.copy2(source_path, CLEANED_FILE)
    logger.info("Copy complete.")

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
            line = raw.rstrip("\n")

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
    logger.info("  Total lines read:            %d", total)
    logger.info("  Lines with 'security rules': %d", sec_rules)
    logger.info("  Lines removed:               %d", removed)
    for k in sorted(reasons.keys()):
        logger.info("    %s: %d", k, reasons[k])

def extract_outputs(logger: logging.Logger) -> None:

    logger.info("Extracting zone/application/security-profile info from: %s", CLEANED_FILE)

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
            line = raw.rstrip("\n")

            policy_name, remainder = extract_policy_remainder(line)
            if policy_name is None:
                continue

            sec_rules += 1

            if remainder.startswith("to ") or remainder.startswith("from "):
                zone_lines += 1
                kw = remainder.split(None, 1)[0]
                tail = remainder[len(kw):].strip()
                tokens = tokenize_list_tail(tail)

                logger.info("Line %d: policy='%s' keyword='%s' zoneTokens=%s", lineno, policy_name, kw, tokens)
                for t in tokens:
                    warn_if_undesirable(logger, t, "zone", lineno)
                    if t in zones_seen:
                        zone_dupes += 1
                        continue
                    zones_seen[t] = None

            if remainder.startswith("application "):
                app_lines += 1
                tail = remainder[len("application"):].strip()
                tokens = tokenize_list_tail(tail)

                logger.info("Line %d: policy='%s' keyword='application' appTokens=%s", lineno, policy_name, tokens)
                for t in tokens:
                    warn_if_undesirable(logger, t, "application", lineno)
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
    logger.info("  Total lines read:            %d", total)
    logger.info("  Lines with 'security rules': %d", sec_rules)
    logger.info("  Zone lines matched:          %d", zone_lines)
    logger.info("  Unique zones written:        %d", len(zones_seen))
    logger.info("  Zone duplicates skipped:     %d", zone_dupes)
    logger.info("  Application lines matched:   %d", app_lines)
    logger.info("  Unique apps written:         %d", len(apps_seen))
    logger.info("  App duplicates skipped:      %d", app_dupes)
    logger.info("  Security profile lines:      %d", prof_lines)

def main() -> int:
    logger = setup_logging()
    install_excepthook(logger)

    prompt = (
        "Enter source file path (default: {}).\n"
        "- Press Enter to use default.\n"
        "- Or type a different path (absolute or relative to MAIN dir).".format(DEFAULT_SOURCE)
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
        "All PAN policy sercurity profiles will be converted to Versa default securoity profile. "
        "Please review the information in used-policy-security-profiles.txt"
    )
    logger.info(msg)

    logger.info("Step-0 complete.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
