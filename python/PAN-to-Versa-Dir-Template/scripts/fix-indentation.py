#!/usr/bin/env python3
import os
import re
import statistics
import collections



def _is_ambiguous_token_line(stripped: str) -> bool:

    s = stripped.strip()
    if not s:
        return True

   
    if s.startswith(("/*", "//", "#")):
        return True

   
    if not re.search(r"[A-Za-z0-9_]", s):
        return True

   
    if re.fullmatch(r"[{};\s]+", s):
        return True
    if re.fullmatch(r"}\s*;?", s):
        return True
    if re.fullmatch(r"{\s*;?", s):
        return True

    return False


def detect_indent_unit(lines):
    indents = []
    for ln in lines:
        if ln.strip() == "" or ln.lstrip().startswith(("/*", "//", "#")):
            continue
        m = re.match(r"[ \t]+", ln)
        if m:
            s = m.group(0).replace("\t", "    ")  # treat tabs as 4 spaces
            indents.append(len(s))

    if not indents:
        return 4

    uniq = sorted(set(indents))
    diffs = [b - a for a, b in zip(uniq, uniq[1:]) if (b - a) > 0]
    if not diffs:
        return 4

    cnt = collections.Counter(diffs)
    unit = cnt.most_common(1)[0][0]

   
    if unit <= 0 or unit > 12:
        unit = int(statistics.median(diffs)) if diffs else 4

    return unit if unit > 0 else 4


def build_reference_indent_stats(base_lines):
   
    mp = collections.defaultdict(list)

    for ln in base_lines:
        raw = ln.rstrip("\n")
        stripped = raw.lstrip(" \t").rstrip()
        if stripped == "":
            continue

        lead_ws = raw[: len(raw) - len(raw.lstrip(" \t"))]
        lead_len = len(lead_ws.replace("\t", "    "))
        mp[stripped].append(lead_len)

    # Build stats: count and distribution per line
    stats = {}
    for k, vals in mp.items():
        c = collections.Counter(vals)
        stats[k] = {
            "count": len(vals),
            "distinct_indents": len(c),
            "mode_indent": c.most_common(1)[0][0],
            "mode_freq": c.most_common(1)[0][1],
        }
    return stats


def brace_depth_change(line):

    s = re.sub(r"/\*.*?\*/", "", line)
    depth = 0
    in_q = False
    esc = False

    for ch in s:
        if in_q:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_q = False
            continue
        else:
            if ch == '"':
                in_q = True
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1

    return depth


def safe_backup(path):
    bak = path + ".bak"
    # overwrite previous bak each run (simple and predictable)
    with open(path, "rb") as fsrc:
        data = fsrc.read()
    with open(bak, "wb") as fdst:
        fdst.write(data)
    return bak



def fix_indentation(base_path, target_path, out_path):
    with open(base_path, "r", encoding="utf-8", errors="replace") as f:
        base_lines = f.readlines()

    with open(target_path, "r", encoding="utf-8", errors="replace") as f:
        tgt_lines = f.readlines()

    indent_unit = detect_indent_unit(base_lines)
    ref_stats = build_reference_indent_stats(base_lines)

    fixed = []
    depth = 0

    for ln in tgt_lines:
        nl = "\n" if ln.endswith("\n") else ""
        raw = ln.rstrip("\n")
        stripped = raw.lstrip(" \t")

       
        if stripped.strip() == "":
            fixed.append(raw.rstrip() + nl)
            continue

        key = stripped.rstrip()

      
        eff_depth = depth
        if stripped.lstrip().startswith("}"):
            eff_depth = max(depth - 1, 0)

       
        desired_indent = eff_depth * indent_unit

       
        if (not _is_ambiguous_token_line(key)) and (key in ref_stats):
            st = ref_stats[key]
           
            if st["distinct_indents"] == 1:
                desired_indent = st["mode_indent"]
            else:
               
                dominance = st["mode_freq"] / max(st["count"], 1)
                if dominance >= 0.95:
                    desired_indent = st["mode_indent"]

       
        content = stripped.rstrip()
        fixed.append((" " * desired_indent) + content + nl)

       
        depth += brace_depth_change(stripped)
        if depth < 0:
            depth = 0

    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(fixed)

    changed = sum(1 for o, n in zip(tgt_lines, fixed) if o != n)
    return indent_unit, changed


def main():
   
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_dir = os.path.abspath(os.path.join(script_dir, ".."))

    base_path = os.path.join(main_dir, "miscellaneous", "base-template.cfg")
    target_path = os.path.join(main_dir, "final-data", "your-final-template.cfg")
    out_path = target_path  # overwrite in-place

    if not os.path.isfile(base_path):
        raise SystemExit(f"ERROR: missing base template: {base_path}")
    if not os.path.isfile(target_path):
        raise SystemExit(f"ERROR: missing target template: {target_path}")

    bak = safe_backup(target_path)

    indent_unit, changed = fix_indentation(base_path, target_path, out_path)

    print(f"OK: indentation fixed using brace-depth + safe base-reference")
    print(f"Backup: {bak}")
    print(f"Indent unit: {indent_unit} spaces")
    print(f"Lines changed: {changed}")
    print(f"Output: {out_path}")


if __name__ == "__main__":
    main()