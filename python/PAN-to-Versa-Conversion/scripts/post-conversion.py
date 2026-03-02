#!/usr/bin/env python3
import os
import re
import sys

DEFAULT_MODE = "double_backslash"
REMOVE_ILLEGAL_XML_CONTROLS = True


def remove_illegal_xml_controls(s: str) -> tuple[str, int]:
    pattern = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")
    found = pattern.findall(s)
    if not found:
        return s, 0
    return pattern.sub("", s), len(found)


def fix_literal_backslash_f(s: str, mode: str) -> tuple[str, int]:
    occurrences = s.count(r"\f")
    if occurrences == 0:
        return s, 0

    if mode == "double_backslash":
        return s.replace(r"\f", r"\\f"), occurrences
    elif mode == "space":
        return s.replace(r"\f", " "), occurrences
    else:
        raise ValueError(f"Unknown mode: {mode}")


def ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)


def default_input_path() -> str:
    return os.path.abspath(os.path.join(os.getcwd(), "..", "final-data", "pre-final.cfg"))


def default_output_path() -> str:
    return os.path.abspath(os.path.join(os.getcwd(), "..", "final-data", "your-final-template.cfg"))


def main():
    in_path = default_input_path() if len(sys.argv) < 2 else sys.argv[1]
    out_path = default_output_path() if len(sys.argv) < 3 else sys.argv[2]
    mode = sys.argv[3].strip() if len(sys.argv) >= 4 else DEFAULT_MODE

    if not os.path.isfile(in_path):
        print(f"ERROR: input file not found: {in_path}", file=sys.stderr)
        print("CWD  :", os.getcwd(), file=sys.stderr)
        print("Hint : run with an explicit path, e.g.:", file=sys.stderr)
        print('  python3 post-conversion.py "/full/path/to/pre-final.cfg"', file=sys.stderr)
        sys.exit(2)

    raw = open(in_path, "rb").read()
    text = raw.decode("utf-8", errors="replace")

    actual_formfeed_count = text.count("\x0c")
    literal_backslash_f_count = text.count(r"\f")

    text2, replaced_backslash_f = fix_literal_backslash_f(text, mode=mode)

    removed_controls = 0
    if REMOVE_ILLEGAL_XML_CONTROLS:
        text3, removed_controls = remove_illegal_xml_controls(text2)
    else:
        text3 = text2

    ensure_parent_dir(out_path)

    with open(out_path, "wb") as f:
        f.write(text3.encode("utf-8"))

    print("---- Fix Summary ----")
    print(f"CWD   : {os.getcwd()}")
    print(f"Input : {in_path}")
    print(f"Output: {out_path}")
    print(f"Mode  : {mode}")
    print("")
    print(f"Found actual form-feed (\\x0c) chars         : {actual_formfeed_count}")
    print(f"Found literal backslash-f sequences ('\\\\f') : {literal_backslash_f_count}")
    print(f"Replaced literal '\\\\f' occurrences          : {replaced_backslash_f}")
    print(f"Removed illegal XML control chars           : {removed_controls}")
    print(f"Post-check remaining actual form-feed (\\x0c): {text3.count(chr(12))}")
    print("\nDone.")


if __name__ == "__main__":
    main()