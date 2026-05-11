
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Set




SCRIPT_DIR = Path.cwd().resolve()
MAIN_DIR = SCRIPT_DIR.parent
FINAL_DATA_DIR = MAIN_DIR / "final-data"
LOG_DIR = MAIN_DIR / "log"

CLEANED_RULES_PATH = FINAL_DATA_DIR / "cleaned-pan-rules.txt"
ADDR_GRP_PATH = FINAL_DATA_DIR / "final-address-group.txt"
ADDR_PATH = FINAL_DATA_DIR / "final-address.txt"

UNRESOLVED_OUT_PATH = MAIN_DIR / "unresolved-objects-configuration.txt"
LOG_PATH = LOG_DIR / "pre-convert-object-cleanup.log"




RE_ADDR_GRP = re.compile(r'^\s*set\s+shared\s+address-group\s+("([^"]+)"|(\S+))\b')
RE_ADDR = re.compile(r'^\s*set\s+shared\s+address\s+("([^"]+)"|(\S+))\b')


RE_POLICY = re.compile(r'\bsecurity\s+rules\s+("([^"]+)"|(\S+))\b')

RE_DISABLED = re.compile(r'\bdisabled\b\s+(\S+)')



RE_TAIL_SOURCE = re.compile(r'^source(\s+|$)')
RE_TAIL_DEST = re.compile(r'^destination(\s+|$)')





def log(msg: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")





def load_object_names(path: Path, regex: re.Pattern) -> Set[str]:
    names: Set[str] = set()
    if not path.exists():
        log(f"ERROR: missing file: {path}")
        return names

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            m = regex.match(line)
            if m:
                nm = m.group(2) if m.group(2) is not None else m.group(3)
                if nm:
                    names.add(nm)
    return names





def extract_policy_name(line: str) -> Optional[str]:
    m = RE_POLICY.search(line)
    if not m:
        return None
    return m.group(2) if m.group(2) is not None else m.group(3)

def extract_policy_match(line: str) -> Optional[re.Match]:
    return RE_POLICY.search(line)





def get_immediate_keyword_after_policy(line: str, policy_m: re.Match) -> Optional[str]:
    tail = line[policy_m.end():]


    tail_l = tail.lstrip()

    if RE_TAIL_SOURCE.match(tail_l):
        return "source"
    if RE_TAIL_DEST.match(tail_l):
        return "destination"
    return None


def extract_targets_from_tail(tail_after_policy: str, keyword: str) -> List[str]:
    tail = tail_after_policy.lstrip()
    if not tail.startswith(keyword):
        return []

    tail = tail[len(keyword):].strip()
    if not tail:
        return []

    if tail.startswith('['):
        m = re.search(r'\[\s*(.*?)\s*\]', tail)
        if not m:
            return []
        content = m.group(1).strip()
        if not content:
            return []
        return content.split()

    return [tail.split()[0]]


def annotate_unresolved_in_line(line: str, unresolved_targets: Set[str]) -> str:
    tokens_sorted = sorted(unresolved_targets, key=len, reverse=True)
    out = line
    for tok in tokens_sorted:
        pattern = re.compile(rf'(?<!\S)({re.escape(tok)})(?!\S)')
        out = pattern.sub(r'\1 <<UNRESOLVED', out)
    return out





def set_policy_disabled_yes(lines: List[str], policy_indices: List[int]) -> None:

    for idx in policy_indices:
        if re.search(r'\bdisabled\b', lines[idx]):
            old = lines[idx]
            lines[idx] = re.sub(r'(\bdisabled\b\s+)\S+', r'\1yes', lines[idx])
            if lines[idx] != old:
                log(f"Policy disabled set to yes (existing line): idx={idx}")
            return


    first_idx = min(policy_indices)
    first_line = lines[first_idx]
    m = RE_POLICY.search(first_line)
    if not m:
        indent = re.match(r'^\s*', first_line).group(0)
        lines.insert(first_idx + 1, indent + "disabled yes\n")
        log(f"Policy disabled set to yes (inserted fallback line) after idx={first_idx}")
        return

    prefix = first_line[:m.end()]
    newline = "" if prefix.endswith("\n") else "\n"
    lines.insert(first_idx + 1, prefix + " disabled yes" + newline)
    log(f"Policy disabled set to yes (inserted new disabled line) after idx={first_idx}")





def main() -> None:
    log("----- START pre-convert object cleanup (STRICT source/destination token) -----")

    if not CLEANED_RULES_PATH.exists():
        log(f"ERROR: missing cleaned rules file: {CLEANED_RULES_PATH}")
        print(f"ERROR: missing file: {CLEANED_RULES_PATH}", file=sys.stderr)
        sys.exit(1)

    addr_groups = load_object_names(ADDR_GRP_PATH, RE_ADDR_GRP)
    addrs = load_object_names(ADDR_PATH, RE_ADDR)

    log(f"Loaded address-groups: {len(addr_groups)} from {ADDR_GRP_PATH}")
    log(f"Loaded addresses:      {len(addrs)} from {ADDR_PATH}")

    with open(CLEANED_RULES_PATH, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()


    policy_map: Dict[str, List[int]] = {}
    for i, line in enumerate(lines):
        pol = extract_policy_name(line)
        if pol:
            policy_map.setdefault(pol, []).append(i)

    log(f"Detected policies: {len(policy_map)}")

    unresolved_lines_out: List[str] = []
    delete_indices: Set[int] = set()

    for idx, line in enumerate(lines):
        policy_m = extract_policy_match(line)
        if not policy_m:
            continue

        pol = extract_policy_name(line)
        if not pol:
            continue


        keyword = get_immediate_keyword_after_policy(line, policy_m)
        if keyword not in ("source", "destination"):
            continue

        tail_after_policy = line[policy_m.end():]
        targets = extract_targets_from_tail(tail_after_policy, keyword)
        if not targets:
            continue

        unresolved_targets: Set[str] = set()
        for t in targets:
            if (t not in addr_groups) and (t not in addrs):
                unresolved_targets.add(t)

        if not unresolved_targets:
            continue

        annotated = annotate_unresolved_in_line(line, unresolved_targets)
        if not annotated.endswith("\n"):
            annotated += "\n"
        unresolved_lines_out.append(annotated)

        delete_indices.add(idx)

        set_policy_disabled_yes(lines, policy_map.get(pol, [idx]))

        log(f"UNRESOLVED found: policy='{pol}' idx={idx} keyword={keyword} targets={sorted(list(unresolved_targets))}")


    if unresolved_lines_out:
        with open(UNRESOLVED_OUT_PATH, "a", encoding="utf-8") as f:
            f.write("".join(unresolved_lines_out))
        log(f"Wrote {len(unresolved_lines_out)} unresolved lines to {UNRESOLVED_OUT_PATH}")
    else:
        log("No unresolved lines found.")


    if delete_indices:
        new_lines = [ln for i, ln in enumerate(lines) if i not in delete_indices]
        with open(CLEANED_RULES_PATH, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        log(f"Deleted {len(delete_indices)} lines from {CLEANED_RULES_PATH}")
    else:
        log("No lines deleted from cleaned-pan-rules.txt")

    log("----- END pre-convert object cleanup (STRICT source/destination token) -----")
    print("Done.")
    print(f"Updated: {CLEANED_RULES_PATH}")
    print(f"Unresolved output: {UNRESOLVED_OUT_PATH}")
    print(f"Log: {LOG_PATH}")


if __name__ == "__main__":
    main()