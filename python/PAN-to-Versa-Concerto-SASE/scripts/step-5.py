import os
import sys
import shutil
import time
import shlex
import select
from typing import Dict, List, Tuple

class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            try:
                s.write(data)
                s.flush()
            except Exception:
                pass
        return len(data)

    def flush(self):
        for s in self.streams:
            try:
                s.flush()
            except Exception:
                pass

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def now_str() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")

def is_file_nonempty(path: str) -> bool:
    return os.path.isfile(path) and os.path.getsize(path) > 0

def input_with_timeout(prompt: str, timeout_sec: int = 15, default: str = "") -> str:
    if not sys.stdin.isatty():
        return default
    try:
        sys.stdout.write(prompt)
        sys.stdout.flush()
        r, _, _ = select.select([sys.stdin], [], [], timeout_sec)
        if r:
            return sys.stdin.readline().rstrip("\n")
        return default
    except Exception:
        return default

def prompt_path(prompt: str, timeout_sec: int = 15, default: str = "") -> str:
    while True:
        p = input_with_timeout(prompt, timeout_sec=timeout_sec, default=default).strip()
        if not p:
            return default
        if os.path.isfile(p):
            return p
        print(f"ERROR: File not found: {p}")

def prompt_yes_no(prompt: str, default_yes: bool = True, timeout_sec: int = 15) -> bool:
    if not sys.stdin.isatty():
        return default_yes

    default_hint = "Y/n" if default_yes else "y/N"
    default_char = "y" if default_yes else "n"
    while True:
        ans = input_with_timeout(f"{prompt} [{default_hint}]: ", timeout_sec=timeout_sec, default="").strip()
        if ans == "":
            return default_yes
        ans_l = ans.lower()
        if ans_l in ("y", "yes"):
            return True
        if ans_l in ("n", "no"):
            return False
        print("Please answer 'y' or 'n' (or press Enter for default).")
def _box_print(*msg_lines: str, width: int = 90) -> None:
    border = "*" * width
    inner_w = width - 4
    print(border)
    for raw in msg_lines:
        raw = (raw or "").replace("\t", "    ")
        while len(raw) > inner_w:
            chunk, raw = raw[:inner_w], raw[inner_w:]
            print(f"* {chunk:<{inner_w}} *")
        print(f"* {raw:<{inner_w}} *")
    print(f"* {'':<{inner_w}} *")
    print(border)

def warn_and_wait(message: str, seconds: int = 15) -> None:
    _box_print(message, f"Press Enter to continue immediately or wait {seconds} seconds...")
    sys.stdout.flush()

    if sys.stdin.isatty():
        try:
            r, _, _ = select.select([sys.stdin], [], [], seconds)
            if r:
                sys.stdin.readline()
        except Exception:
            time.sleep(seconds)
    else:
        time.sleep(seconds)

def warn_and_wait(message: str, seconds: int = 15) -> None:
    print(message)
    print(f"Press Enter to continue immediately or wait {seconds} seconds...")
    sys.stdout.flush()

    if sys.stdin.isatty():
        try:
            r, _, _ = select.select([sys.stdin], [], [], seconds)
            if r:
                sys.stdin.readline()
        except Exception:
            time.sleep(seconds)
    else:
        time.sleep(seconds)

def shlex_tokens(line: str) -> List[str]:
    try:
        return shlex.split(line, posix=True)
    except Exception:

        return line.strip().split()

def extract_shared_object_names(src_file: str, object_kind_token: str) -> List[str]:
    names = []
    with open(src_file, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            toks = shlex_tokens(line)
            for i in range(len(toks) - 3):
                if toks[i] == "set" and toks[i + 1] == "shared" and toks[i + 2] == object_kind_token:
                    names.append(toks[i + 3])
                    break
    return names

def find_security_rules_policy_and_rest(tokens: List[str]) -> Tuple[str, List[str]]:
    for i in range(len(tokens) - 2):
        if tokens[i] == "security" and tokens[i + 1] == "rules":
            if i + 2 < len(tokens):
                policy = tokens[i + 2]
                rest = tokens[i + 3 :] if (i + 3) <= len(tokens) else []
                return policy, rest
    return "", []
def parse_value_list(tokens_after_keyword: List[str]) -> List[str]:
    if not tokens_after_keyword:
        return []
    t0 = tokens_after_keyword[0]
    vals: List[str] = []

    def strip_brackets(tok: str) -> str:
        return tok.strip().lstrip("[").rstrip("]").strip()

    if t0 == "[" or t0.startswith("["):
        for t in tokens_after_keyword:
            if t == "[":
                continue
            if t == "]":
                break

            t_clean = t
            end_list = False

            if t_clean.startswith("["):
                t_clean = t_clean[1:]

            if t_clean.endswith("]"):
                t_clean = t_clean[:-1]
                end_list = True

            t_clean = t_clean.strip()
            if t_clean:
                vals.append(t_clean)

            if end_list:
                break
        return vals

    single = strip_brackets(t0)
    if single:
        vals.append(single)
    return vals

def sanitize_description_inner_quotes_line(line: str) -> str:
    key = 'description "'
    if key not in line:
        return line
    start = line.find(key)
    if start == -1:
        return line

    content_start = start + len(key)

    last_quote = line.rfind('"')
    if last_quote == -1 or last_quote <= content_start:
        return line

    content = line[content_start:last_quote]
    if '"' not in content:
        return line

    cleaned = content.replace('"', '')
    return line[:content_start] + cleaned + line[last_quote:]

def sanitize_file_description_quotes(path: str) -> int:
    if not os.path.isfile(path):
        return 0
    changed = 0
    out_lines = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            new_line = sanitize_description_inner_quotes_line(raw)
            if new_line != raw:
                changed += 1
            out_lines.append(new_line)

    if changed:
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(out_lines)

    return changed

def read_conversion_file(path: str) -> Tuple[List[str], Dict[str, str]]:
    order: List[str] = []
    cur: Dict[str, str] = {}
    if not os.path.isfile(path):
        return order, cur
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.strip("\n")
            if not line.strip():
                continue
            if ">>" in line:
                left, right = line.split(">>", 1)
                key = left.strip()
                val = right.strip()
            else:
                key = line.strip()
                val = ""
            if not key:
                continue
            if key not in cur:
                order.append(key)
            cur[key] = val
    return order, cur

def write_conversion_file(path: str, order: List[str], cur: Dict[str, str]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for k in order:
            v = cur.get(k, "")
            if v:
                f.write(f"{k} >> {v}\n")
            else:
                f.write(f"{k} >> \n")

def load_pan_to_versa_map(map_path: str) -> Dict[str, str]:
    m: Dict[str, str] = {}
    with open(map_path, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.strip("\n").strip()
            if not line or line.startswith("#"):
                continue
            if ">>" not in line:
                continue
            left, right = line.split(">>", 1)
            pan = left.strip()
            versa = right.strip()
            if pan:
                m[pan] = versa
    return m
def apply_mapping_to_conversion_file(conv_path: str, map_path: str) -> None:
    order, cur = read_conversion_file(conv_path)
    pan2versa = load_pan_to_versa_map(map_path)

    changed = 0
    for k in order:
        if k in pan2versa:
            mapped = pan2versa[k].strip()

            if (not cur.get(k, "").strip()) and mapped:
                cur[k] = mapped
                changed += 1

    write_conversion_file(conv_path, order, cur)
    print(f"Applied mapping from: {map_path}")
    print(f"Updated {changed} line(s) in: {conv_path}")

def conversion_file_has_blanks(conv_path: str) -> bool:
    _, cur = read_conversion_file(conv_path)
    for k, v in cur.items():
        if not v.strip():
            return True
    return False

def main() -> int:

    cwd = os.path.abspath(os.getcwd())
    main_dir = cwd if os.path.basename(cwd) != "scripts" else os.path.abspath(os.path.join(cwd, ".."))

    log_dir = os.path.join(main_dir, "log")
    ensure_dir(log_dir)

    log_path = os.path.join(log_dir, "step-5.log")
    log_fh = open(log_path, "a", encoding="utf-8")

    sys.stdout = Tee(sys.__stdout__, log_fh)
    sys.stderr = Tee(sys.__stderr__, log_fh)

    print("=" * 80)
    print(f"[{now_str()}] Step-5 START")
    print(f"CWD      : {cwd}")
    print(f"MAIN DIR : {main_dir}")
    print(f"LOG FILE : {log_path}")
    print("=" * 80)

    step5_dir = os.path.join(main_dir, "step-5")
    ensure_dir(step5_dir)
    print(f"OK: ensured directory exists: {step5_dir}")

    step4_dir = os.path.join(main_dir, "step-4")
    default_rules_src = os.path.join(step4_dir, "step-4/step-4_cleaned-pan-rules.txt")

    default_rules_src = os.path.join(step4_dir, "step-4_cleaned-pan-rules.txt")

    rules_dst = os.path.join(step5_dir, "step-5_cleaned-pan-rules.txt")

    if os.path.isfile(default_rules_src):
        shutil.copy2(default_rules_src, rules_dst)
        print(f"OK: copied rules file:\n  SRC: {default_rules_src}\n  DST: {rules_dst}")
    else:
        print(f"WARNING: default rules source not found: {default_rules_src}")
        if sys.stdin.isatty():
            custom_src = prompt_path("Enter the name+location of the PAN rules source file to copy: ")
            shutil.copy2(custom_src, rules_dst)
            print(f"OK: copied custom rules file:\n  SRC: {custom_src}\n  DST: {rules_dst}")
        else:
            print("ERROR: Non-interactive shell and default source missing. Cannot prompt for file path.")
            print("       Put the file at ../step-4/step-4_cleaned-pan-rules.txt and rerun.")
            return 2

    step4_service = os.path.join(step4_dir, "step-4_cleaned-service.txt")
    step5_service_out = os.path.join(step5_dir, "step-5_extracted-service.txt")

    service_names_set = set()
    if os.path.isfile(step4_service):
        names = extract_shared_object_names(step4_service, "service")
        for n in names:
            if n:
                service_names_set.add(n)
        with open(step5_service_out, "w", encoding="utf-8") as f:
            for n in sorted(service_names_set):
                f.write(n + "\n")
        print(f"OK: extracted {len(service_names_set)} unique service name(s) to: {step5_service_out}")
    else:
        print(f"WARNING: service file not found (skipping extraction): {step4_service}")

    step4_svc_group = os.path.join(step4_dir, "step-4_cleaned-service-group.txt")
    step5_svc_group_out = os.path.join(step5_dir, "step-5_extracted-service-group.txt")

    svc_group_names_set = set()
    if os.path.isfile(step4_svc_group):
        names = extract_shared_object_names(step4_svc_group, "service-group")
        for n in names:
            if n:
                svc_group_names_set.add(n)
        with open(step5_svc_group_out, "w", encoding="utf-8") as f:
            for n in sorted(svc_group_names_set):
                f.write(n + "\n")
        print(f"OK: extracted {len(svc_group_names_set)} unique service-group name(s) to: {step5_svc_group_out}")
    else:
        print(f"WARNING: service-group file not found (skipping extraction): {step4_svc_group}")

    predef_service_conv = os.path.join(main_dir, "predef-service-conversion.txt")
    order_svc, cur_svc = read_conversion_file(predef_service_conv)

    missing_services_added = 0
    total_service_refs = 0

    with open(rules_dst, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            toks = shlex_tokens(line)
            policy, rest = find_security_rules_policy_and_rest(toks)
            if not policy or not rest:
                continue

            if rest[0] != "service":
                continue

            values = parse_value_list(rest[1:])
            for v in values:
                if not v:
                    continue
                total_service_refs += 1

                if (v in service_names_set) or (v in svc_group_names_set):
                    continue
                if v not in cur_svc:
                    cur_svc[v] = ""
                    order_svc.append(v)
                    missing_services_added += 1

    if missing_services_added > 0:
        write_conversion_file(predef_service_conv, order_svc, cur_svc)
        print(f"OK: added {missing_services_added} missing service name(s) to: {predef_service_conv}")
    else:

        if os.path.isfile(predef_service_conv):
            print(f"OK: no new missing services found (service refs scanned: {total_service_refs}).")
        else:
            print(f"OK: no missing services found and conversion file does not exist (service refs scanned: {total_service_refs}).")

    if is_file_nonempty(predef_service_conv):
        do_map_services = prompt_yes_no(
            'Convert PAN predefined services to Versa predefined policy services using "../miscellaneous/PAN-to-Versa-services.txt"?',
            default_yes=True,
        )
        if do_map_services:
            svc_map_file = os.path.join(main_dir, "miscellaneous", "PAN-to-Versa-services.txt")
            if os.path.isfile(svc_map_file):
                apply_mapping_to_conversion_file(predef_service_conv, svc_map_file)
            else:
                print(f"WARNING: mapping file not found, skipping auto-mapping: {svc_map_file}")

            if conversion_file_has_blanks(predef_service_conv):
                warn_and_wait(
                    'WARNING: There are PAN predefined services that weren\'t matched to Versa equivalent. '
                    'You should review the file "predef-service-conversion.txt" and manually fill in the blank, '
                    "else other conversion scripts will use PAN's service name in Versa configuration. It will likely FAIL!"
                )
    else:
        print("INFO: predef-service-conversion.txt does not exist or is empty; skipping service mapping prompt.")

    predef_app_conv = os.path.join(main_dir, "predef-application-conversion.txt")
    order_app, cur_app = read_conversion_file(predef_app_conv)

    missing_apps_added = 0
    total_app_refs = 0

    with open(rules_dst, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            toks = shlex_tokens(line)
            policy, rest = find_security_rules_policy_and_rest(toks)
            if not policy or not rest:
                continue

            if rest[0] != "application":
                continue

            values = parse_value_list(rest[1:])
            for v in values:
                if not v:
                    continue
                total_app_refs += 1
                if v not in cur_app:
                    cur_app[v] = ""
                    order_app.append(v)
                    missing_apps_added += 1

    if missing_apps_added > 0:
        write_conversion_file(predef_app_conv, order_app, cur_app)
        print(f"OK: added {missing_apps_added} application name(s) to: {predef_app_conv}")
    else:
        if os.path.isfile(predef_app_conv):
            print(f"OK: no new applications found (application refs scanned: {total_app_refs}).")
        else:
            print(f"OK: no applications found and conversion file does not exist (application refs scanned: {total_app_refs}).")

    if is_file_nonempty(predef_app_conv):
        do_map_apps = prompt_yes_no(
            'Convert PAN predefined applications to Versa predefined policy services using "../miscellaneous/PAN-to-Versa-applications.txt"?',
            default_yes=True,
        )
        if not do_map_apps:
            print("INFO: user chose not to map applications. Exiting as instructed.")
            print(f"[{now_str()}] Step-5 END")
            return 0

        app_map_candidates = [
            os.path.join(main_dir, "miscellaneous", "PAN-to-Versa-applications.txt"),
            os.path.join(main_dir, "miscellaneous", "PAN-to-Versa-application.txt"),
        ]
        app_map_file = next((p for p in app_map_candidates if os.path.isfile(p)), "")

        if app_map_file:
            apply_mapping_to_conversion_file(predef_app_conv, app_map_file)
        else:
            print("WARNING: application mapping file not found. Checked:")
            for p in app_map_candidates:
                print(f"  - {p}")

        if conversion_file_has_blanks(predef_app_conv):
            warn_and_wait(
                'WARNING: There are PAN predefined applications that weren\'t matched to Versa equivalent. '
                'You should review the file "predef-application-conversion.txt" and manually fill in the blank, '
                "else other conversion scripts will use PAN's application name in Versa configuration. It will likely FAIL!"
            )
    else:
        print("INFO: predef-application-conversion.txt does not exist or is empty; skipping application mapping prompt.")

    changed_desc = sanitize_file_description_quotes(rules_dst)
    if changed_desc:
        print(f"OK: sanitized {changed_desc} description line(s) in: {rules_dst}")
    else:
        print(f"OK: no description inner-quote issues found in: {rules_dst}")

    print("=" * 80)
    print(f"[{now_str()}] Step-5 END (SUCCESS)")
    print("=" * 80)
    return 0

if __name__ == "__main__":
    try:
        rc = main()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        rc = 130
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        rc = 1
    sys.exit(rc)
