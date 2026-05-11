#!/usr/bin/env python3
import os
import re
import sys

DEFAULT_MODE = "double_backslash"
REMOVE_ILLEGAL_XML_CONTROLS = True


def remove_illegal_xml_controls(s: str) -> tuple:
    pattern = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")
    found = pattern.findall(s)
    if not found:
        return s, 0
    return pattern.sub("", s), len(found)


def remove_comment_markers(s: str) -> tuple:
    pattern = re.compile(r"^[ \t]*/\*.*?\*/[ \t]*\n?", re.MULTILINE)
    found = pattern.findall(s)
    if not found:
        return s, 0
    return pattern.sub("", s), len(found)


def fix_literal_backslash_f(s: str, mode: str) -> tuple:
    occurrences = s.count(r"\f")
    if occurrences == 0:
        return s, 0
    if mode == "double_backslash":
        return s.replace(r"\f", r"\\f"), occurrences
    elif mode == "space":
        return s.replace(r"\f", " "), occurrences
    else:
        raise ValueError(f"Unknown mode: {mode}")


def deduplicate_list_sections(s: str) -> tuple:
    pattern = re.compile(r"(?<![\w-])([\w-]+-list)(\s*\[\s*)([^\[\]]*?)(\s*\])")
    counter = [0]
    affected = [0]

    def repl(m):
        keyword = m.group(1)
        opening = m.group(2)
        content = m.group(3)
        closing = m.group(4)
        tokens = content.split()
        if not tokens:
            return m.group(0)
        seen = set()
        unique_tokens = []
        for t in tokens:
            if t not in seen:
                seen.add(t)
                unique_tokens.append(t)
        removed = len(tokens) - len(unique_tokens)
        if removed == 0:
            return m.group(0)
        counter[0] += removed
        affected[0] += 1
        return keyword + opening + " ".join(unique_tokens) + closing

    new_s = pattern.sub(repl, s)
    return new_s, counter[0], affected[0]


def ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)


def default_output_path(input_path: str) -> str:
    return os.path.abspath(input_path)


def default_input_path() -> str:
    return os.path.abspath(os.path.join(os.getcwd(), "..", "final-data", "your-final-template.cfg"))


def main():
    in_path = default_input_path() if len(sys.argv) < 2 else sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) >= 3 else default_output_path(in_path)
    mode = sys.argv[3].strip() if len(sys.argv) >= 4 else DEFAULT_MODE

    if not os.path.isfile(in_path):
        print(f"ERROR: input file not found: {in_path}", file=sys.stderr)
        print("CWD  :", os.getcwd(), file=sys.stderr)
        print("Hint : run with an explicit path, e.g.:", file=sys.stderr)
        print('  python3 post-conversion-optional.py "/full/path/to/input.cfg"', file=sys.stderr)
        sys.exit(2)

    raw = open(in_path, "rb").read()
    text = raw.decode("utf-8", errors="replace")

    actual_formfeed_count = text.count("\x0c")
    literal_backslash_f_count = text.count(r"\f")

    text2, replaced_backslash_f = fix_literal_backslash_f(text, mode=mode)

    text2b, removed_comments = remove_comment_markers(text2)

    removed_controls = 0
    if REMOVE_ILLEGAL_XML_CONTROLS:
        text3, removed_controls = remove_illegal_xml_controls(text2b)
    else:
        text3 = text2b

    text4, dedup_removed_tokens, dedup_affected_lists = deduplicate_list_sections(text3)

    ensure_parent_dir(out_path)

    with open(out_path, "wb") as f:
        f.write(text4.encode("utf-8"))

    print("---- Fix Summary ----")
    print(f"CWD   : {os.getcwd()}")
    print(f"Input : {in_path}")
    print(f"Output: {out_path}")
    print(f"Mode  : {mode}")
    print("")
    print(f"Found actual form-feed (\\x0c) chars         : {actual_formfeed_count}")
    print(f"Found literal backslash-f sequences ('\\\\f') : {literal_backslash_f_count}")
    print(f"Replaced literal '\\\\f' occurrences          : {replaced_backslash_f}")
    print(f"Removed /* ... */ comment marker lines      : {removed_comments}")
    print(f"Removed illegal XML control chars           : {removed_controls}")
    print(f"Deduped *-list sections (lines affected)    : {dedup_affected_lists}")
    print(f"Removed duplicate tokens in *-list sections : {dedup_removed_tokens}")
    print(f"Post-check remaining actual form-feed (\\x0c): {text4.count(chr(12))}")
    print("\nDone.")


if __name__ == "__main__":
    main()
