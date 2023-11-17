#!/usr/bin/python
#  validate_versa_config_file.py - Versa definition
#
#  This file is used to check Versa configuration file for correct indentation and parentheses.
#
#  Copyright (c) 2023, Versa Networks, Inc.
#  All rights reserved.
#

def check_indentation(versa_cfg_file_fh):
    """
    Check if each line in the file is indented by 4 spaces relative to the previous line.
    If the last line ends with a semicolon, the following line can have the same indentation.

    Args:
        versa_cfg_file_fh (file): File handler for the Versa configuration file.

    Returns:
        bool: True if indentation is correct, False otherwise.
    """
    prev_indent = None
    last_line_ends_with_semicolon = False
    line_count = 0
    for line in versa_cfg_file_fh:
        line_count += 1
        curr_indent = len(line) - len(line.lstrip(' '))
        if prev_indent is not None:
            if last_line_ends_with_semicolon or curr_indent == prev_indent:
                last_line_ends_with_semicolon = line.strip().endswith(';')
                prev_indent = curr_indent
                continue
            elif abs(curr_indent - prev_indent) != 4 :
                return False
        prev_indent = curr_indent
        last_line_ends_with_semicolon = line.strip().endswith(';')
    return True

def check_parentheses(versa_cfg_file_fh):
    """
    Validates a Versa cfg file by checking if the number of opening and closing braces are equal.

    Args:
        versa_cfg_file_fh (file): File handler for the Versa configuration file.

    Returns:
        bool: True if the number of opening and closing braces are equal, False otherwise.
    """
    open_braces = close_braces = 0
    line_count = 0
    for line in versa_cfg_file_fh:
        line_count += 1
        open_braces += line.count('{')
        close_braces += line.count('}')
    return open_braces == close_braces
