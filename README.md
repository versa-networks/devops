# sdwan-automate

Ansible automation for provisioning and re-deploying Versa SD-WAN sites via the Director REST API.

---

## Directory Structure

```
sdwan-automate/
├── ansible.cfg                       # Global Ansible config (log_path, host_key_checking)
├── playbooks/
│   ├── versa_site_provision.yml      # Main provisioning playbook
│   ├── versa_site_redeploy.yml       # Standalone re-deploy playbook
│   └── tasks/
│       ├── check_director.yml        # Director connectivity check (runs once)
│       ├── log_entry.yml             # Reusable per-device log writer
│       ├── provision_device.yml      # Loads site vars, loops over CPEs
│       ├── provision_cpe.yml         # Steps 2–9 for a single CPE
│       ├── redeploy_device.yml       # Loads site vars, loops over CPEs (re-deploy)
│       ├── redeploy_cpe.yml          # Re-deploy steps A+B for a single CPE
│       └── commit_and_verify_cpe.yml # Steps C–E: commit template + verify (applianceExists=true only)
├── vars/
│   ├── director.yml                  # Director host, port, polling defaults
│   ├── regions/
│   │   ├── AMER.yml                  # AMER regional defaults
│   │   ├── APAC.yml                  # APAC regional defaults
│   │   └── EMEA.yml                  # EMEA regional defaults
│   ├── sites/
│   │   ├── BRANCH-001.yml            # Site definition with devices[] list
│   │   ├── BRANCH-002.yml
│   │   └── BRANCH-003.yml
│   └── templates/
│       └── AMER-HUB-1.yml            # Maps Director var names → Ansible var names
├── vault/
│   └── director_credentials.yml      # Ansible Vault — Director password
└── logs/
    ├── ansible.log                   # Full Ansible run log (all tasks, all devices)
    ├── BRANCH-002-PRIMARY.log        # Per-device milestone log
    └── BRANCH-002-SECONDARY.log
```

---

## Execution Flow

```
versa_site_provision.yml          loops over vars/sites/*.yml
  └── provision_device.yml        loads site + region vars, loops over devices[]
        └── provision_cpe.yml     flattens vars, runs Steps 2–9 per CPE
              └── redeploy_cpe.yml  (branched to when applianceExists=true)

versa_site_redeploy.yml           loops over vars/sites/*.yml
  └── redeploy_device.yml         loads site + region vars, loops over devices[]
        └── redeploy_cpe.yml      flattens vars, triggers re-deploy per CPE (STEP A+B)
              └── commit_and_verify_cpe.yml  (branched to when applianceExists=true)
```

---

## Variable Precedence

Lowest → highest (higher overrides lower):

```
vars/director.yml
  → vars/regions/<REGION>.yml
    → vars/sites/<SITE>.yml
      → CPE-level keys within devices[]
        → -e flags on the command line
```

---

## Template Variable Mappings

Each Versa template has a corresponding file in `vars/templates/` that maps Director template variable names (`{$v_...}`) to Ansible variable names. STEP 5 automatically loads the right file based on `template_name`.

To add support for a new template, create `vars/templates/<template_name>.yml`:

```yaml
template_var_map:
  - director_var: "{$v_MPLS_IPv4__staticaddress}"
    ansible_var:  "inet1_static_address"
    type:         "ipv4_mask"
  - director_var: "{$v_MPLS-Transport-VR_IPv4__vrHopAddress}"
    ansible_var:  "inet1_transport_vr_hop"
    type:         "ipv4"
  - director_var: "{$v_LAN-CORP_IPv4__staticaddress}"
    ansible_var:  "lan_corp_ipv4_address"
    type:         "ipv4_mask"
```

The `type` field is optional — omitting it disables format validation for that variable. If `ansible_var` is not defined at runtime the entry is skipped silently.

**Supported types**

| Type | Validation | Example value |
|------|------------|---------------|
| `ipv4_mask` | Must contain `/` (CIDR notation required) | `1.1.1.1/24` |
| `ipv4` | Must not contain `/` (plain address, no mask) | `1.1.1.1` |

STEP 5 aborts with a clear error message if a value fails its type check, citing both the Director variable name and the Ansible variable name so the offending key in the site file is immediately identifiable.

---

## Logging

Two levels of logging are produced automatically on every run.

**Global run log — `logs/ansible.log`**
Configured via `ansible.cfg`. Captures the full Ansible task output for every device in every run, appended across runs.

**Per-device milestone log — `logs/<device_name>.log`**
Written by `tasks/log_entry.yml` at the key steps below. One file per CPE, appended across runs with UTC timestamps, so you can track the history of each device independently.

```
2026-07-01 14:03:01 UTC | START | site=BRANCH-002, region=AMER, serial=102-1, ...
2026-07-01 14:03:02 UTC | STEP2 | available site_id=103
2026-07-01 14:03:03 UTC | STEP3 | http=404, device_exists=False, workflow_status=NOT_FOUND, appliance_exists=False
2026-07-01 14:03:08 UTC | STEP6 | device created (POST) OK, http=201
2026-07-01 14:03:09 UTC | STEP7 | deploy triggered, task_id=task-abc123
2026-07-01 14:04:15 UTC | STEP8 | task=task-abc123, status=SUCCESS, progress=100%
2026-07-01 14:04:16 UTC | STEP9 | device confirmed present in org=NVIDIA-IT
2026-07-01 14:04:16 UTC | DONE  | provisioning complete, org=NVIDIA-IT, template=AMER-HUB-1
```

Abort and failure conditions are also logged before the playbook halts:
```
2026-07-01 14:03:03 UTC | STEP3 | ABORT – workflowStatus=Failed, investigate in Director
2026-07-01 14:04:15 UTC | STEP8 | FAILED – status=FAILED, errors=...
```

For the redeploy path (either standalone `versa_site_redeploy.yml` or auto-branched from `provision_cpe.yml`) the milestones are labeled `REDEPLOY START`, `STEP-A`, `STEP-B`, `STEP-C`, and `DONE`.

To watch a specific device's log in real time during a run:
```bash
tail -f logs/BRANCH-002-PRIMARY.log
```

**First-run setup:** `ansible.cfg` sets `log_path = logs/ansible.log`, but Ansible requires the directory to exist before it starts. The playbooks create `logs/` automatically via `pre_tasks`, but this happens after Ansible has already tried to open the log file. Run this once on a new host to get `ansible.log` from the very first execution:

```bash
mkdir -p ~/sdwan-automate/logs
```

---

## Prerequisites

- Ansible 2.9+
- Reachability to Director (`vars/director.yml` → `director_host`)
- Vault password (if `vault/director_credentials.yml` is encrypted)

---

## Vault Setup

The Director password lives in `vault/director_credentials.yml`.
Encrypt before committing to source control:

```bash
ansible-vault encrypt vault/director_credentials.yml
```

To rotate the password:

```bash
ansible-vault edit vault/director_credentials.yml
```

---

## Running from the `sdwan-automate/` directory

### Provisioning

```bash
# All sites, all devices
ansible-playbook playbooks/versa_site_provision.yml --ask-vault-pass

# All sites, all devices (vault password in file)
ansible-playbook playbooks/versa_site_provision.yml \
  --vault-password-file ~/.vault_pass

# One site, all its CPEs
ansible-playbook playbooks/versa_site_provision.yml \
  --ask-vault-pass \
  -e "site_filter=BRANCH-002"

# One site, one specific CPE
ansible-playbook playbooks/versa_site_provision.yml \
  --ask-vault-pass \
  -e "site_filter=BRANCH-002" \
  -e "target_device=BRANCH-002-PRIMARY"

# One specific CPE across all sites (all site files are loaded but only the
# matching site does real work — use site_filter too to avoid that)
ansible-playbook playbooks/versa_site_provision.yml \
  --ask-vault-pass \
  -e "target_device=BRANCH-002-PRIMARY"

# One specific CPE with site_filter (recommended — skips unrelated site files)
ansible-playbook playbooks/versa_site_provision.yml \
  --ask-vault-pass \
  -e "site_filter=BRANCH-003" \
  -e "target_device=BRANCH-003-PRIMARY"

# Override Director host at runtime
ansible-playbook playbooks/versa_site_provision.yml \
  --ask-vault-pass \
  -e "director_host=10.78.22.99"

# Dry run (check mode — no changes sent to Director)
ansible-playbook playbooks/versa_site_provision.yml \
  --ask-vault-pass \
  --check
```

### Re-Deploy

```bash
# Re-deploy all sites, all CPEs
ansible-playbook playbooks/versa_site_redeploy.yml --ask-vault-pass

# Re-deploy one site, all its CPEs
ansible-playbook playbooks/versa_site_redeploy.yml \
  --ask-vault-pass \
  -e "site_filter=BRANCH-002"

# Re-deploy one specific CPE
ansible-playbook playbooks/versa_site_redeploy.yml \
  --ask-vault-pass \
  -e "site_filter=BRANCH-002" \
  -e "target_device=BRANCH-002-PRIMARY"

# Re-deploy one specific CPE across all sites
ansible-playbook playbooks/versa_site_redeploy.yml \
  --ask-vault-pass \
  -e "target_device=BRANCH-002-PRIMARY"
```

### Verbose / Debug output

```bash
# Show task output
ansible-playbook playbooks/versa_site_provision.yml --ask-vault-pass -v

# Show HTTP responses
ansible-playbook playbooks/versa_site_provision.yml --ask-vault-pass -vv

# Full connection debug
ansible-playbook playbooks/versa_site_provision.yml --ask-vault-pass -vvv
```

---

## Command-Line Variables (`-e`)

| Variable             | Applies to   | Description                                                               | Example                              |
|----------------------|--------------|---------------------------------------------------------------------------|--------------------------------------|
| `site_filter`        | Both         | Substring match on site filename. Filters which site files are processed. | `-e "site_filter=BRANCH-002"`        |
| `target_device`      | Both         | Exact match on `device_name`. Filters which CPE within a site is processed. | `-e "target_device=BRANCH-002-PRIMARY"` |
| `director_host_1`    | Both         | Override primary Director IP (auto-discovered at runtime).                | `-e "director_host_1=10.78.22.21"`   |
| `director_host_2`    | Both         | Override standby Director IP (auto-discovered at runtime).                | `-e "director_host_2=10.73.16.2"`    |
| `director_port`      | Both         | Override Director port.                                                   | `-e "director_port=9182"`            |
| `task_poll_retries`  | Both         | Override number of task poll retries (default: 60).                       | `-e "task_poll_retries=120"`         |
| `task_poll_interval` | Both         | Override seconds between poll attempts (default: 10).                     | `-e "task_poll_interval=5"`          |

---

## Idempotency

The provisioning playbook is safe to re-run. For each CPE, STEP 3 queries Director before making any changes:

| Director response                          | Action taken                              |
|--------------------------------------------|-------------------------------------------|
| 404 — device not found                     | Full provisioning (POST + deploy)         |
| 200, `workflowStatus=Deployed`, `applianceExists=false` | Update device record (PUT + deploy) |
| 200, `workflowStatus=Deployed`, `applianceExists=true`  | Branch to re-deploy only          |
| 200, `workflowStatus=Failed`               | Abort — investigate in Director           |
| 200, any other `workflowStatus`            | Abort — investigate in Director           |
| 5XX                                        | Abort — Director error                    |

---

## Adding a New Site

1. Create `vars/sites/BRANCH-XXX.yml` using an existing site file as a template.
2. Set `region` to `AMER`, `APAC`, or `EMEA` to inherit regional defaults.
3. Add one entry per CPE under `devices:`.
4. Run the playbook — no other files need to change.

## Adding a New Region

1. Create `vars/regions/<REGION>.yml` following the pattern of `AMER.yml`.
2. Set `region: "<REGION>"` in the relevant site files.

## Adding a New Template

1. Create `vars/templates/<template_name>.yml` with the `template_var_map` list.
2. Set `template_name` in the region file or site file.
3. No changes to playbook or task files needed.
