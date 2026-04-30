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

            if len(toks) >= 4 and toks[0] == "firewall" and toks[1] == "service" and toks[2] == object_kind_token:
                names.append(toks[3])
    return names

def find_security_rules_policy_and_rest(tokens: List[str]) -> Tuple[str, List[str]]:
    for i in range(len(tokens) - 2):
        if tokens[i] == "firewall" and tokens[i + 1] == "policy":
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

    for t in tokens_after_keyword:
        t_clean = strip_brackets(t)
        if t_clean:
            vals.append(t_clean)
    return vals

def sanitize_description_inner_quotes_line(line: str) -> str:
    key = 'comments "'
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

def build_app_list_ids_map(rules_file: str) -> Dict[str, List[str]]:
    app_map: Dict[str, List[str]] = {}
    with open(rules_file, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            toks = shlex_tokens(raw.strip())
            if len(toks) < 3:
                continue
            if toks[0] != "application" or toks[1] != "list":
                continue
            list_name = toks[2]
            if list_name not in app_map:
                app_map[list_name] = []
            try:
                entry_idx = toks.index("entry")
            except ValueError:
                continue
            after_entry = toks[entry_idx + 2:]
            try:
                app_kw_idx = after_entry.index("application")
            except ValueError:
                continue
            for t in after_entry[app_kw_idx + 1:]:
                if t == "action":
                    break
                if t.isdigit():
                    app_map[list_name].append(t)
    return app_map


def replace_app_ids_in_line(line: str, id_to_versa: Dict[str, str]) -> str:
    marker = 'application-list "'
    idx = line.find(marker)
    if idx == -1:
        return line
    val_start = idx + len(marker)
    val_end = line.find('"', val_start)
    if val_end == -1:
        return line
    ids = line[val_start:val_end].split()
    mapped = [id_to_versa.get(i, i) for i in ids]
    return line[:val_start] + " ".join(mapped) + line[val_end:]


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

    pending_warnings: List[str] = []

    step5_dir = os.path.join(main_dir, "step-5")
    ensure_dir(step5_dir)
    print(f"OK: ensured directory exists: {step5_dir}")

    step4_dir = os.path.join(main_dir, "step-4")
    default_rules_src = os.path.join(step4_dir, "step-4_cleaned-forti-rules.txt")
    rules_dst = os.path.join(step5_dir, "step-5_cleaned-forti-rules.txt")

    if os.path.isfile(default_rules_src):
        shutil.copy2(default_rules_src, rules_dst)
        print(f"OK: copied rules file:\n  SRC: {default_rules_src}\n  DST: {rules_dst}")
    else:
        print(f"WARNING: default rules source not found: {default_rules_src}")
        if sys.stdin.isatty():
            custom_src = prompt_path("Enter the name+location of the Fortinet rules source file to copy: ")
            shutil.copy2(custom_src, rules_dst)
            print(f"OK: copied custom rules file:\n  SRC: {custom_src}\n  DST: {rules_dst}")
        else:
            print("ERROR: Non-interactive shell and default source missing. Cannot prompt for file path.")
            print("       Put the file at ../step-4/step-4_cleaned-forti-rules.txt and rerun.")
            return 2

    _IGNORED_SERVICES = {"ALL", "ANY", "NONE"}
    all_removed = 0
    kept_lines = []
    with open(rules_dst, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.rstrip("\n")
            toks = shlex_tokens(line)
            policy, rest = find_security_rules_policy_and_rest(toks)
            if policy and rest and rest[0] == "service":
                values = parse_value_list(rest[1:])
                if values and all(v.upper() in _IGNORED_SERVICES for v in values if v):
                    all_removed += 1
                    continue
            kept_lines.append(raw)
    with open(rules_dst, "w", encoding="utf-8") as f:
        f.writelines(kept_lines)
    print(f"OK: removed {all_removed} 'service ALL/ANY/NONE' line(s) from: {rules_dst}")

    step4_service = os.path.join(step4_dir, "step-4_cleaned-service.txt")
    step5_service_out = os.path.join(step5_dir, "step-5_extracted-service.txt")

    svc_map_candidates_early = [
        os.path.join(main_dir, "miscellaneous", "Forti-to-Versa-services.txt"),
        os.path.join(main_dir, "miscellaneous", "Fortinet-to-Versa-services.txt"),
    ]
    svc_map_file_early = next((p for p in svc_map_candidates_early if os.path.isfile(p)), "")
    forti_predefined_services: set = set()
    if svc_map_file_early:
        forti_predefined_map = load_pan_to_versa_map(svc_map_file_early)
        forti_predefined_services = {k.upper() for k in forti_predefined_map}
        print(f"OK: loaded {len(forti_predefined_services)} predefined service name(s) from: {svc_map_file_early}")
    else:
        print("WARNING: Forti-to-Versa-services.txt not found; predefined services may be misclassified as custom.")

    service_names_set = set()
    if os.path.isfile(step4_service):
        names = extract_shared_object_names(step4_service, "custom")
        for n in names:
            if n and n.upper() not in _IGNORED_SERVICES and n.upper() not in forti_predefined_services:
                service_names_set.add(n)
        with open(step5_service_out, "w", encoding="utf-8") as f:
            for n in sorted(service_names_set):
                f.write(n + "\n")
        print(f"OK: extracted {len(service_names_set)} unique custom service name(s) to: {step5_service_out}")
    else:
        print(f"WARNING: service file not found (skipping extraction): {step4_service}")

    step4_svc_group = os.path.join(step4_dir, "step-4_cleaned-service-group.txt")
    step5_svc_group_out = os.path.join(step5_dir, "step-5_extracted-service-group.txt")

    svc_group_names_set = set()
    if os.path.isfile(step4_svc_group):
        names = extract_shared_object_names(step4_svc_group, "group")
        for n in names:
            if n and n.upper() not in _IGNORED_SERVICES:
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
                if v.upper() in _IGNORED_SERVICES:
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
            'Convert Fortinet predefined services to Versa predefined policy services using "../miscellaneous/Forti-to-Versa-services.txt"?',
            default_yes=True,
        )
        if do_map_services:
            svc_map_candidates = [
                os.path.join(main_dir, "miscellaneous", "Forti-to-Versa-services.txt"),
                os.path.join(main_dir, "miscellaneous", "Fortinet-to-Versa-services.txt"),
            ]
            svc_map_file = next((p for p in svc_map_candidates if os.path.isfile(p)), "")
            if svc_map_file:
                apply_mapping_to_conversion_file(predef_service_conv, svc_map_file)
            else:
                print("WARNING: service mapping file not found, skipping auto-mapping. Checked:")
                for p in svc_map_candidates:
                    print(f"  - {p}")

            if conversion_file_has_blanks(predef_service_conv):
                pending_warnings.append(
                    "WARNING: There are Fortinet predefined services that weren't matched to Versa equivalent. "
                    'You should review the file "predef-service-conversion.txt" and manually fill in the blank, '
                    "else other conversion scripts will use Fortinet's service name in Versa configuration. It will likely FAIL!"
                )
    else:
        print("INFO: predef-service-conversion.txt does not exist or is empty; skipping service mapping prompt.")

    print("INFO: scanning application list definitions...")
    app_list_ids = build_app_list_ids_map(rules_dst)
    print(f"OK: found {len(app_list_ids)} application list definition(s).")

    rewrite1 = []
    policies_resolved = 0
    policies_dropped  = 0
    defn_lines_removed = 0
    seen_ids: set = set()
    all_referenced_ids: List[str] = []

    with open(rules_dst, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.rstrip("\n")
            toks = shlex_tokens(line)

            if len(toks) >= 2 and toks[0] == "application" and toks[1] == "list":
                defn_lines_removed += 1
                continue

            policy, rest = find_security_rules_policy_and_rest(toks)
            if policy and rest and rest[0] == "application-list" and len(rest) >= 2:
                list_name = rest[1]
                ids = app_list_ids.get(list_name, [])
                if not ids:
                    policies_dropped += 1
                    print(f"  DROP: policy '{policy}' application-list '{list_name}' "
                          f"has no app IDs (category-only or unknown) - line removed")
                    continue
                old_marker = f'application-list "{list_name}"'
                new_marker = f'application-list "{" ".join(ids)}"'
                new_line   = line.replace(old_marker, new_marker, 1)
                rewrite1.append(new_line + "\n")
                policies_resolved += 1
                for id_ in ids:
                    if id_ not in seen_ids:
                        seen_ids.add(id_)
                        all_referenced_ids.append(id_)
                continue

            rewrite1.append(raw if raw.endswith("\n") else raw + "\n")

    with open(rules_dst, "w", encoding="utf-8") as f:
        f.writelines(rewrite1)
    print(f"OK: rules file rewritten:")
    print(f"  - {policies_resolved} application-list line(s) resolved to numeric IDs")
    print(f"  - {policies_dropped} application-list line(s) dropped (no app IDs)")
    print(f"  - {defn_lines_removed} application list definition line(s) removed")

    predef_app_conv = os.path.join(main_dir, "predef-application-conversion.txt")
    order_app, cur_app = read_conversion_file(predef_app_conv)

    new_ids_added = 0
    for id_ in all_referenced_ids:
        if id_ not in cur_app:
            cur_app[id_] = ""
            order_app.append(id_)
            new_ids_added += 1

    if all_referenced_ids:
        write_conversion_file(predef_app_conv, order_app, cur_app)
        print(f"OK: wrote {len(order_app)} unique app ID(s) to: {predef_app_conv}")
    else:
        print("INFO: no application IDs found in any policy rule; predef-application-conversion.txt not created.")

    if is_file_nonempty(predef_app_conv):
        do_map_apps = prompt_yes_no(
            'Convert Fortinet application IDs to Versa predefined applications using '
            '"../miscellaneous/Forti-to-Versa-application.txt"?',
            default_yes=True,
        )
        if not do_map_apps:
            print("INFO: user chose not to map applications. Exiting as instructed.")
            print(f"[{now_str()}] Step-5 END")
            return 0

        app_map_candidates = [
            os.path.join(main_dir, "miscellaneous", "Forti-to-Versa-applications.txt"),
            os.path.join(main_dir, "miscellaneous", "Forti-to-Versa-application.txt"),
        ]
        app_map_file = next((p for p in app_map_candidates if os.path.isfile(p)), "")

        if app_map_file:
            apply_mapping_to_conversion_file(predef_app_conv, app_map_file)
        else:
            print("WARNING: Forti-to-Versa application mapping file not found. Checked:")
            for p in app_map_candidates:
                print(f"  - {p}")

        _, id_to_versa = read_conversion_file(predef_app_conv)
        id_to_versa_mapped = {k: v for k, v in id_to_versa.items() if v.strip()}

        rewrite2 = []
        with open(rules_dst, "r", encoding="utf-8", errors="replace") as f:
            for raw in f:
                line = raw.rstrip("\n")
                toks = shlex_tokens(line)
                policy, rest = find_security_rules_policy_and_rest(toks)
                if policy and rest and rest[0] == "application-list":
                    line = replace_app_ids_in_line(line, id_to_versa_mapped)
                rewrite2.append(line + "\n")

        with open(rules_dst, "w", encoding="utf-8") as f:
            f.writelines(rewrite2)
        print(f"OK: replaced numeric application IDs with Versa names in: {rules_dst}")

        if conversion_file_has_blanks(predef_app_conv):
            pending_warnings.append(
                "WARNING: There are Fortinet predefined applications that weren't matched to Versa equivalent. "
                'You should review the file "predef-application-conversion.txt" and manually fill in the blank, '
                "else other conversion scripts will use Fortinet's application ID in Versa configuration. It will likely FAIL!"
            )
    else:
        print("INFO: no application IDs to map; skipping application mapping prompt.")


    changed_desc = sanitize_file_description_quotes(rules_dst)
    if changed_desc:
        print(f"OK: sanitized {changed_desc} comments line(s) in: {rules_dst}")
    else:
        print(f"OK: no comments inner-quote issues found in: {rules_dst}")

    print("=" * 80)
    print(f"[{now_str()}] Step-5 END (SUCCESS)")
    print("=" * 80)

    for warning in pending_warnings:
        warn_and_wait(warning)

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