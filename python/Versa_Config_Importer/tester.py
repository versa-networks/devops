#!/usr/bin/python
#  tester.py - Versa Tenant definition
#
#  Versa configuration supports full multi-tenancy.
#  This file has the definition of Tenant in the Versa configuration.
#
#  Copyright (c) 2023, Versa Networks, Inc.
#  All rights reserved.
#

import sys

def main():
    print("asa ")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)
