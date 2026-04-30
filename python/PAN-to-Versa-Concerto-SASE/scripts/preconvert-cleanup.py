import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Set, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
MAIN_DIR = SCRIPT_DIR.parent
FINAL_DATA_DIR = MAIN_DIR / "final-data"
LOG_DIR = MAIN_DIR / "log"

CLEANED_RULES_PATH = FINAL_DATA_DIR / "cleaned-pan-rules.txt"
ADDR_GRP_PATH = FINAL_DATA_DIR / "final-address-group.txt"
ADDR_PATH = FINAL_DATA_DIR / "final-address.txt"

UNRESOLVED_OUT_PATH = MAIN_DIR / "unresolved-objects-configuration.txt"
LOG_PATH = LOG_DIR / "pre-convert-object-cleanup.log"

RE_ADDR_GRP = re.compile(r'^\s*set\s+shared\s+address-group\s+("([^"]+)"|(\S+))')
RE_ADDR = re.compile(r'^\s*set\s+shared\s+address\s+("([^"]+)"|(\S+))')

RE_POLICY = re.compile(r'\bsecurity\s+rules\s+("([^"]+)"|(\S+))')

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
    tail = line[policy_m.end():].lstrip()
    if RE_TAIL_SOURCE.match(tail):
        return "source"
    if RE_TAIL_DEST.match(tail):
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

def set_policy_disabled_yes(
    lines: List[str],
    policy_indices: List[int],
    disabled_inserts: Dict[int, str],
) -> None:
    for idx in policy_indices:
        if re.search(r'\bdisabled\b', lines[idx]):
            old = lines[idx]
            lines[idx] = re.sub(r'(\bdisabled\b\s+)\S+', r'\1yes', lines[idx])
            if lines[idx] != old:
                log(f"Policy disabled set to yes (existing line): idx={idx}")
            return

    first_idx = min(policy_indices)
    first_line = lines[first_idx]

    pol_m = RE_POLICY.search(first_line)
    if not pol_m:
        log(f"WARNING: could not construct disabled line for idx={first_idx}, line={first_line!r}")
        return

    prefix = first_line[:pol_m.end()].rstrip()
    new_line = prefix + " disabled yes\n"
    disabled_inserts[first_idx] = new_line
    log(f"Policy disabled queued for insert after idx={first_idx}: {new_line.rstrip()}")

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
    disabled_inserts: Dict[int, str] = {}

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
        valid_targets: List[str] = []
        for t in targets:
            if (t not in addr_groups) and (t not in addrs):
                unresolved_targets.add(t)
            else:
                valid_targets.append(t)

        if not unresolved_targets:
            continue

        annotated = annotate_unresolved_in_line(line, unresolved_targets)
        if not annotated.endswith("\n"):
            annotated += "\n"
        unresolved_lines_out.append(annotated)

        if valid_targets:
            new_value = "[ " + " ".join(valid_targets) + " ]"
            new_line = re.sub(
                r'(' + re.escape(keyword) + r'\s+)(\[.*?\]|\S+)',
                lambda m: m.group(1) + new_value,
                line,
                count=1
            )
            lines[idx] = new_line if new_line.endswith("\n") else new_line + "\n"
        else:
            delete_indices.add(idx)

        set_policy_disabled_yes(lines, policy_map.get(pol, [idx]), disabled_inserts)

        log(f"UNRESOLVED found: policy='{pol}' idx={idx} keyword={keyword} targets={sorted(list(unresolved_targets))} valid_kept={valid_targets}")

    if unresolved_lines_out:
        HEADER = (
            "╔═══════════════════════════════════════════════════════════════════════════════════════╗\n"
            "║                               !!  ATTENTION  !!                                       ║\n"
            "╠═══════════════════════════════════════════════════════════════════════════════════════╣\n"
            "║  These objects are being referred to, but were not found in the source configuration  ║\n"
            "║  file. The policy configuration has been transferred without the missing objects.     ║\n"
            "║  The policies affected are therefore intentionally disabled.                          ║\n"
            "║  Please remedy the situation and manually re-enable the policies.                     ║\n"
            "╚═══════════════════════════════════════════════════════════════════════════════════════╝\n"
            "\n"
        )
        file_is_new = not UNRESOLVED_OUT_PATH.exists() or UNRESOLVED_OUT_PATH.stat().st_size == 0
        with open(UNRESOLVED_OUT_PATH, "a", encoding="utf-8") as f:
            if file_is_new:
                f.write(HEADER)
            f.write("".join(unresolved_lines_out))
        log(f"Wrote {len(unresolved_lines_out)} unresolved lines to {UNRESOLVED_OUT_PATH}")
    else:
        log("No unresolved lines found.")

    if unresolved_lines_out or delete_indices or disabled_inserts:
        new_lines: List[str] = []
        for i, ln in enumerate(lines):
            if i not in delete_indices:
                new_lines.append(ln)
            if i in disabled_inserts:
                new_lines.append(disabled_inserts[i])
        with open(CLEANED_RULES_PATH, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        log(f"Wrote updated cleaned-pan-rules.txt (deleted={len(delete_indices)}, inserted_disabled={len(disabled_inserts)})")
    else:
        log("No changes to cleaned-pan-rules.txt")

    log("----- END pre-convert object cleanup (STRICT source/destination token) -----")
    print("Done.")
    print(f"Updated: {CLEANED_RULES_PATH}")
    print(f"Unresolved output: {UNRESOLVED_OUT_PATH}")
    print(f"Log: {LOG_PATH}")

if __name__ == "__main__":
    main()
