#!/usr/bin/env python3
"""
get_services_summary.py
Paginates GET requests to the Versa Concerto elements/services/summary endpoint
until an empty data response is returned.
Reads connection variables from ../temp/general.txt
"""

import requests
import json
import sys
import urllib3

# Suppress SSL warnings for self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

GENERAL_TXT = "../temp/general.txt"
DEBUG       = True   # Set False to suppress raw response dumps


def load_general(filepath):
    """Parse key >> value pairs from general.txt into a dict."""
    config = {}
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or ">>" not in line:
                continue
            key, _, value = line.partition(">>")
            config[key.strip()] = value.strip()
    return config


def build_headers(config):
    """Build request headers using bearer token, CSRF token, and cookies."""
    return {
        "Authorization":  f"Bearer {config['bearer-token']}",
        "X-CSRF-TOKEN":   config["csrf-token"],
        "Cookie":         config["cookies"],
        "Accept":         "application/json",
        "Content-Type":   "application/json",
    }


def fetch_page(session, fqdn, port, tenant_uuid, headers, window_number):
    """Fetch a single page from the API. Returns the parsed JSON body."""
    url = (
        f"https://{fqdn}:{port}"
        f"/portalapi/v1/tenants/{tenant_uuid}/elements/services/summary"
        f"?windowSize=100"
        f"&nextWindowNumber={window_number}"
        f"&ecpScope=SASE"
        f"&filter=user"
    )
    print(f"[INFO] GET {url}")
    response = session.get(url, headers=headers, verify=False, timeout=30)
    response.raise_for_status()
    return response.json()


def extract_records(body, window_number):
    """
    Extract the list of records from the response body.
    Prints the raw structure on window 0 so we can diagnose shape issues.
    """
    if DEBUG and window_number == 0:
        print("\n[DEBUG] Raw response (window 0):")
        print(json.dumps(body, indent=2))
        print("[DEBUG] Top-level type  :", type(body).__name__)
        if isinstance(body, dict):
            print("[DEBUG] Top-level keys  :", list(body.keys()))
        print()

    if isinstance(body, list):
        return body

    if isinstance(body, dict):
        # Walk common wrapper patterns
        for key in ("data", "services", "items", "results", "content"):
            val = body.get(key)
            if isinstance(val, list):
                return val

    return []


def main():
    # ── Load config ──────────────────────────────────────────────────────────
    try:
        config = load_general(GENERAL_TXT)
    except FileNotFoundError:
        print(f"[ERROR] Cannot find config file: {GENERAL_TXT}", file=sys.stderr)
        sys.exit(1)

    required_keys = ["concerto-fqdn", "concerto-port", "tenant-uuid", "bearer-token", "csrf-token", "cookies"]
    missing = [k for k in required_keys if k not in config]
    if missing:
        print(f"[ERROR] Missing keys in general.txt: {missing}", file=sys.stderr)
        sys.exit(1)

    fqdn        = config["concerto-fqdn"]
    port        = config["concerto-port"]
    tenant_uuid = config["tenant-uuid"]
    headers     = build_headers(config)

    # ── Paginate ─────────────────────────────────────────────────────────────
    all_services = []
    window_number = 0

    print(f"[INFO] Tenant : {tenant_uuid}")
    print("-" * 60)

    with requests.Session() as session:
        while True:
            print(f"[INFO] Fetching window {window_number} ...", end=" ", flush=True)

            try:
                body = fetch_page(session, fqdn, port, tenant_uuid, headers, window_number)
            except requests.HTTPError as e:
                print(f"\n[ERROR] HTTP {e.response.status_code}: {e.response.text}")
                sys.exit(1)
            except requests.RequestException as e:
                print(f"\n[ERROR] Request failed: {e}")
                sys.exit(1)

            page_data = extract_records(body, window_number)
            count = len(page_data)
            print(f"{count} records")

            if count == 0:
                print(f"[INFO] Empty response at window {window_number} — done.")
                break

            all_services.extend(page_data)
            window_number += 1

    # ── Output ────────────────────────────────────────────────────────────────
    print("-" * 60)
    print(f"[INFO] Total services collected : {len(all_services)}")

    output_file = "services_summary.json"
    with open(output_file, "w") as f:
        json.dump(all_services, f, indent=2)
    print(f"[INFO] Results saved to          : {output_file}")


if __name__ == "__main__":
    main()