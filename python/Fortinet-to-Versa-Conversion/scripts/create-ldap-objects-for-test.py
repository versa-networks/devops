#!/usr/bin/env python3
"""
AD Import Script
================
Reads an LDAP input file containing users and groups,
transforms DNs (DC=corp,DC=local → DC=acme,DC=com, OU prefixed with TEST_),
then creates the corresponding objects in a Microsoft Active Directory server.

Defaults:
    Server  : 10.78.250.14
    Port    : 20389  (plain LDAP, no SSL)
    Bind DN : cn=binduser,ou=research,dc=acme,dc=com
    Password: Versa@123  (also set as the default user password)

Requirements:
    pip install ldap3

Usage:
    # Dry-run (no changes made to AD)
    python ad_import.py --input ldap-source-input.txt --dry-run

    # Live run with all defaults
    python ad_import.py --input ldap-source-input.txt

    # Override any default
    python ad_import.py --input ldap-source-input.txt --server 10.0.0.1 --port 389

NOTE: Setting unicodePwd over plain LDAP requires the AD domain controller to
      allow unencrypted password changes (disabled by default on most DCs).
      If password-set fails with error 53 "Unwilling to Perform", enable the
      policy "Domain controller: LDAP server signing requirements = None" on the
      DC, or use LDAPS (--use-ssl --port 636).
"""

import argparse
import logging
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

try:
    from ldap3 import (
        MODIFY_REPLACE,
        SIMPLE,
        Connection,
        Server,
    )
    from ldap3.core.exceptions import LDAPException
except ImportError:
    sys.exit(
        "[ERROR] ldap3 is not installed. Run:  pip install ldap3"
    )

# ---------------------------------------------------------------------------
# Defaults — change here or override via CLI flags
# ---------------------------------------------------------------------------
DEFAULT_SERVER   = "10.78.250.14"
DEFAULT_PORT     = 20389
DEFAULT_USE_SSL  = False
DEFAULT_BIND_DN  = "cn=binduser,ou=research,dc=acme,dc=com"
DEFAULT_BIND_PW  = "Versa@123"
DEFAULT_USER_PW  = "Versa@123"   # password set on every newly created user

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("ad_import")


# ---------------------------------------------------------------------------
# DN transformation helpers
# ---------------------------------------------------------------------------
OLD_DC = "DC=corp,DC=local"
NEW_DC = "DC=acme,DC=com"

_dn_split_re = re.compile(r',\s*(?=[A-Za-z]+=)')   # split on commas that start an attr=


def split_dn(dn: str) -> list[str]:
    """Split a DN string into its RDN components."""
    dn = dn.strip().strip('"')
    return [part.strip() for part in _dn_split_re.split(dn)]


def join_dn(parts: list[str]) -> str:
    return ",".join(parts)


def transform_dn(raw_dn: str) -> str:
    """
    1. Strip leading/trailing whitespace and quotes.
    2. Replace OLD_DC suffix with NEW_DC.
    3. Prefix every OU= component with TEST_.
    """
    dn = raw_dn.strip().strip('"')

    # Step 1 – replace DC suffix (case-insensitive)
    dn = re.sub(re.escape(OLD_DC), NEW_DC, dn, flags=re.IGNORECASE)

    # Step 2 – prefix every OU value with TEST_  (skip if already prefixed)
    def prefix_ou(m):
        val = m.group(1)
        if val.startswith("TEST_"):
            return f"OU={val}"
        return f"OU=TEST_{val}"

    dn = re.sub(r'OU=([^,]+)', prefix_ou, dn, flags=re.IGNORECASE)

    return dn


def get_cn(dn: str) -> str:
    """Return the CN value from the first RDN of a DN."""
    parts = split_dn(dn)
    first = parts[0]
    if "=" in first:
        return first.split("=", 1)[1]
    return first


def get_parent_dn(dn: str) -> str:
    """Return everything after the first RDN component."""
    parts = split_dn(dn)
    return join_dn(parts[1:])


def ou_chain(dn: str) -> list[str]:
    """
    Return an ordered list of OU (and DC) DNs from the deepest OU
    up to the root, so we can ensure each OU exists before creating
    an object inside it.

    E.g. for  CN=foo,OU=TEST_Users,OU=TEST_Corp,DC=acme,DC=com
    returns:
      ["OU=TEST_Users,OU=TEST_Corp,DC=acme,DC=com",
       "OU=TEST_Corp,DC=acme,DC=com"]
    """
    parts = split_dn(dn)[1:]          # drop the CN= part
    chains = []
    while parts and parts[0].upper().startswith("OU="):
        chains.append(join_dn(parts))
        parts = parts[1:]
    return chains


# ---------------------------------------------------------------------------
# File parser
# ---------------------------------------------------------------------------
@dataclass
class LdapSource:
    users:  list[str] = field(default_factory=list)
    groups: list[str] = field(default_factory=list)


def parse_input_file(path: str) -> LdapSource:
    """Parse ----BEGIN USERS---- / ----BEGIN GROUPS---- blocks."""
    src = LdapSource()
    section: Optional[str] = None

    with open(path, encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            if line == "----BEGIN USERS----":
                section = "users"
                continue
            if line == "----END USERS----":
                section = None
                continue
            if line == "----BEGIN GROUPS----":
                section = "groups"
                continue
            if line == "----END GROUPS----":
                section = None
                continue

            if section == "users":
                src.users.append(line)
            elif section == "groups":
                src.groups.append(line)

    log.info("Parsed  %d user(s) and %d group(s) from %s",
             len(src.users), len(src.groups), path)
    return src


# ---------------------------------------------------------------------------
# AD connector
# ---------------------------------------------------------------------------
class ADClient:
    def __init__(
        self,
        server_host: str,
        bind_dn: str,
        bind_pw: str,
        port: int = 389,
        use_ssl: bool = False,
        dry_run: bool = False,
    ):
        self.dry_run = dry_run
        self._conn: Optional[Connection] = None

        if not dry_run:
            srv = Server(server_host, port=port, use_ssl=use_ssl, get_info="ALL")
            self._conn = Connection(
                srv,
                user=bind_dn,
                password=bind_pw,
                authentication=SIMPLE,
                auto_bind=True,
            )
            log.info("Connected to AD server %s:%s (SSL=%s)", server_host, port, use_ssl)

    # ------------------------------------------------------------------
    def test_connection(self) -> bool:
        """Try a simple search against the root DSE to verify connectivity."""
        if self.dry_run:
            log.info("[DRY-RUN] Skipping connection test.")
            return True
        try:
            self._conn.search(
                search_base="",
                search_filter="(objectClass=*)",
                search_scope="BASE",
                attributes=["serverName", "dnsHostName"],
            )
            log.info("✔  Connection successful  →  %s:%s",
                     self._conn.server.host, self._conn.server.port)
            return True
        except Exception as exc:
            log.error("✘  Connection FAILED  →  %s", exc)
            return False

    # ------------------------------------------------------------------
    def _exists(self, dn: str) -> bool:
        if self.dry_run:
            return False
        self._conn.search(dn, "(objectClass=*)", search_scope="BASE",
                          attributes=["distinguishedName"])
        return bool(self._conn.entries)

    # ------------------------------------------------------------------
    def ensure_ou(self, ou_dn: str) -> None:
        """Create an OU if it does not already exist."""
        ou_name = get_cn(ou_dn)          # value of the OU= RDN
        parent   = get_parent_dn(ou_dn)

        if self.dry_run:
            log.info("[DRY-RUN] Would ensure OU: %s", ou_dn)
            return

        if self._exists(ou_dn):
            log.debug("OU already exists: %s", ou_dn)
            return

        attrs = {
            "objectClass":          ["top", "organizationalUnit"],
            "ou":                   ou_name,
            "distinguishedName":    ou_dn,
        }
        self._conn.add(ou_dn, attributes=attrs)
        if self._conn.result["result"] == 0:
            log.info("Created OU: %s", ou_dn)
        else:
            log.warning("Could not create OU %s — %s", ou_dn, self._conn.result)

    # ------------------------------------------------------------------
    def create_user(self, dn: str, default_password: str = DEFAULT_USER_PW) -> None:
        cn  = get_cn(dn)

        # sAMAccountName: CN value, max 20 chars  (Windows logon: ACME\username)
        sam = cn.replace(" ", "_")[:20]

        # UPN: username@acme.com
        upn = f"{sam}@{NEW_DC.replace('DC=', '').replace(',', '.')}"

        # Final UAC:  512 (enabled) | 65536 (password never expires) = 66048
        UAC_DISABLED       = 514    # used only during initial add
        UAC_ENABLED_NO_EXP = 66048  # applied after password is set

        if self.dry_run:
            log.info(
                "[DRY-RUN] Would create User:\n"
                "          DN            : %s\n"
                "          sAMAccountName: %s  (logon: ACME\\%s)\n"
                "          UPN           : %s\n"
                "          Password      : %s  (never expires, no change required)",
                dn, sam, sam, upn, default_password,
            )
            return

        if self._exists(dn):
            log.info("User already exists, skipping: %s", dn)
            return

        # ── Step 1: create account DISABLED, no pwdLastSet ──────────────────
        # AD refuses userAccountControl with DONT_EXPIRE_PASSWORD and
        # pwdLastSet=-1 on the initial add — they must come after the password.
        attrs = {
            "objectClass":        ["top", "person", "organizationalPerson", "user"],
            "cn":                 cn,
            "sAMAccountName":     sam,
            "userPrincipalName":  upn,
            "displayName":        cn,
            "userAccountControl": UAC_DISABLED,   # disabled during creation
        }
        self._conn.add(dn, attributes=attrs)
        if self._conn.result["result"] != 0:
            log.warning("Could not create User %s — %s", dn, self._conn.result)
            return
        log.info("Created User : %s  (UPN: %s  |  SAM: ACME\\%s)", dn, upn, sam)

        # ── Step 2: set password ─────────────────────────────────────────────
        encoded_pw = f'"{default_password}"'.encode("utf-16-le")
        self._conn.modify(dn, {"unicodePwd": [(MODIFY_REPLACE, [encoded_pw])]})
        if self._conn.result["result"] != 0:
            log.warning(
                "Password NOT set for %s — %s\n"
                "  Hint: plain-LDAP password changes require the DC to allow\n"
                "  unsigned LDAP or use LDAPS (--use-ssl --port 636).",
                dn, self._conn.result,
            )
            return
        log.info("Password set : %s", dn)

        # ── Step 3: enable account + password never expires + no forced change
        self._conn.modify(dn, {
            "userAccountControl": [(MODIFY_REPLACE, [UAC_ENABLED_NO_EXP])],
            "pwdLastSet":         [(MODIFY_REPLACE, [-1])],
        })
        if self._conn.result["result"] == 0:
            log.info("Enabled      : %s  (UAC=%d, pwdLastSet=-1)", dn, UAC_ENABLED_NO_EXP)
        else:
            log.warning("Could not enable/configure User %s — %s", dn, self._conn.result)

    # ------------------------------------------------------------------
    def create_group(self, dn: str) -> None:
        cn  = get_cn(dn)
        sam = cn[:256]   # sAMAccountName for groups can be up to 256 chars

        if self.dry_run:
            log.info("[DRY-RUN] Would create Group: %s  (sAMAccountName=%s)", dn, sam)
            return

        if self._exists(dn):
            log.info("Group already exists, skipping: %s", dn)
            return

        attrs = {
            "objectClass":    ["top", "group"],
            "cn":             cn,
            "sAMAccountName": sam,
            "groupType":      -2147483646,   # Global Security group
            "description":    f"Imported from LDAP source – {cn}",
        }
        self._conn.add(dn, attributes=attrs)
        if self._conn.result["result"] == 0:
            log.info("Created Group: %s", dn)
        else:
            log.warning("Could not create Group %s — %s", dn, self._conn.result)

    # ------------------------------------------------------------------
    def close(self):
        if self._conn:
            self._conn.unbind()
            log.info("Disconnected from AD.")


# ---------------------------------------------------------------------------
# Main import logic
# ---------------------------------------------------------------------------
def import_to_ad(src: LdapSource, client: ADClient, base_dc: str,
                 user_password: str = DEFAULT_USER_PW) -> None:
    """
    Process all objects:
      1. Collect every OU path that needs to exist.
      2. Create OUs from shallowest to deepest.
      3. Create users.
      4. Create groups.
    """

    all_dns: list[tuple[str, str]] = []   # (transformed_dn, kind)

    for raw in src.users:
        # Skip the service-account comment line or blank
        if not raw or raw.startswith("#"):
            continue
        # Skip the bind service account itself (we don't want to recreate it
        # as a regular user – adjust if you need it)
        if "svc-fortigate" in raw.lower():
            log.info("Skipping service account (not imported as regular user): %s", raw)
            continue
        tdn = transform_dn(raw)
        all_dns.append((tdn, "user"))

    for raw in src.groups:
        if not raw or raw.startswith("#"):
            continue
        tdn = transform_dn(raw)
        all_dns.append((tdn, "group"))

    # ---- 1. Collect unique OU paths ----------------------------------------
    ou_set: set[str] = set()
    for dn, _ in all_dns:
        for ou_dn in ou_chain(dn):
            ou_set.add(ou_dn)

    # Sort by depth (fewest components = shallowest = must be created first)
    sorted_ous = sorted(ou_set, key=lambda d: len(split_dn(d)))

    # ---- 2. Ensure OUs exist -------------------------------------------------
    log.info("--- Ensuring %d OU(s) ---", len(sorted_ous))
    for ou_dn in sorted_ous:
        client.ensure_ou(ou_dn)

    # ---- 3. Create users -----------------------------------------------------
    log.info("--- Creating users ---")
    for dn, kind in all_dns:
        if kind == "user":
            client.create_user(dn, default_password=user_password)

    # ---- 4. Create groups ----------------------------------------------------
    log.info("--- Creating groups ---")
    for dn, kind in all_dns:
        if kind == "group":
            client.create_group(dn)

    log.info("Import complete.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Import LDAP users/groups into Microsoft Active Directory.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--input",    required=True,
                   help="Path to the LDAP source input file")
    p.add_argument("--server",   default=DEFAULT_SERVER,
                   help="AD server hostname or IP")
    p.add_argument("--bind-dn",  default=DEFAULT_BIND_DN, dest="bind_dn",
                   help="Bind DN for AD authentication")
    p.add_argument("--bind-pw",  default=DEFAULT_BIND_PW, dest="bind_pw",
                   help="Bind password")
    p.add_argument("--user-pw",  default=DEFAULT_USER_PW, dest="user_pw",
                   help="Default password assigned to every newly created user")
    p.add_argument("--port",     default=DEFAULT_PORT, type=int,
                   help="LDAP port")
    p.add_argument("--use-ssl",  action="store_true", default=DEFAULT_USE_SSL,
                   dest="use_ssl", help="Use LDAPS (SSL)")
    p.add_argument("--base-dc",  default=NEW_DC, dest="base_dc",
                   help="Target AD base DC")
    p.add_argument("--dry-run",  action="store_true", dest="dry_run",
                   help="Print what would be done without touching AD")
    p.add_argument("--debug",    action="store_true",
                   help="Enable debug logging")
    return p


def main():
    parser = build_parser()
    args   = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Parse input file
    src = parse_input_file(args.input)

    # Print DN transformation preview
    log.info("=== DN transformation preview (first 3 users) ===")
    for raw in src.users[:3]:
        if raw and not raw.startswith("#"):
            log.info("  IN : %s", raw.strip().strip('"'))
            log.info("  OUT: %s", transform_dn(raw))

    log.info("=== Connection settings ===")
    log.info("  Server  : %s:%s  SSL=%s", args.server, args.port, args.use_ssl)
    log.info("  Bind DN : %s", args.bind_dn)
    log.info("  Dry-run : %s", args.dry_run)

    # Connect & import
    client = ADClient(
        server_host = args.server,
        bind_dn     = args.bind_dn,
        bind_pw     = args.bind_pw,
        port        = args.port,
        use_ssl     = args.use_ssl,
        dry_run     = args.dry_run,
    )

    try:
        log.info("=== Testing connection to AD server ===")
        if not client.test_connection():
            log.error("Aborting — could not connect to AD server %s:%s", args.server, args.port)
            sys.exit(1)

        import_to_ad(src, client, args.base_dc, user_password=args.user_pw)
    finally:
        client.close()


if __name__ == "__main__":
    main()