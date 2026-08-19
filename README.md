# deploy-automate

Ansible automation for provisioning and re-deploying Versa SD-WAN sites via the Director REST API.

---

## Directory Structure

```
deploy-automate/
├── ansible.cfg                       # Global Ansible config (log_path, host_key_checking)
├── playbooks/
│   ├── versa_site_provision.yml      # Main provisioning playbook
│   ├── versa_site_redeploy.yml       # Standalone re-deploy playbook
│   └── tasks/
│       ├── check_director.yml        # Director connectivity check (runs once)
│       ├── log_entry.yml             # Reusable per-device log writer
│       ├── provision_site.yml      # Loads site vars, loops over CPEs
│       ├── provision_cpe.yml         # Steps 2–9 for a single CPE
│       ├── redeploy_site.yml       # Loads site vars, loops over CPEs (re-deploy)
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
│   ├── templates/
│   │   └── AMER-HUB-1.yml            # Maps Director var names → Ansible var names
│   └── service_templates/
│       └── NV_MGMT.yml               # Maps service template $v_ vars → Ansible var names
├── vault/
│   └── director_credentials.yml      # Ansible Vault — Director password
├── versa_ansible_automation.pdf      # Versa SD-WAN provisioning reference documentation
└── logs/
    ├── ansible.log                   # Full Ansible run log (all tasks, all devices)
    ├── BRANCH-002-PRIMARY.log        # Per-device milestone log
    └── BRANCH-002-SECONDARY.log
```

---

## Execution Flow

```
versa_site_provision.yml          loops over vars/sites/*.yml
  └── provision_site.yml        loads site + region vars, loops over devices[]
        └── provision_cpe.yml     flattens vars, runs Steps 2–9 per CPE
              └── redeploy_cpe.yml  (branched to when applianceExists=true)

versa_site_redeploy.yml           loops over vars/sites/*.yml
  └── redeploy_site.yml         loads site + region vars, loops over devices[]
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
mkdir -p ~/deploy-automate/logs
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

## Running from the `deploy-automate/` directory

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
| `assume_yes`         | Provision    | Skip the diff + confirm prompt for existing devices (default: false).     | `-e "assume_yes=true"`               |
| `MYDEBUG`            | Both         | Enable verbose debug tasks (PUT/POST body, raw API responses, attr detail). | `-e "MYDEBUG=true"`                |

---

## Diff and Confirm on Re-run

When `versa_site_provision.yml` encounters a CPE that already exists in Director (HTTP 200 from STEP 3), it computes a diff of the current variable bindings in Director against the new values from the site/CPE vars file before making any changes.

The diff is displayed as structured JSON:

```json
{
  "total_changes": 3,
  "device_template": "SPOKE-AMER-REGION-1",
  "device_template_changes": [
    {"variable": "{$v_MPLS_IPv4__staticaddress}", "before": "192.168.20.1/24", "after": "192.168.20.23/24"}
  ],
  "service_template_changes": [
    {"template": "NV_MGMT", "variable": "{$v_Director_Address-Prefix-1__vnfIpaddress}", "before": "(empty)", "after": "10.78.22.21/32"}
  ]
}
```

The playbook then pauses and requires explicit confirmation:

```
Proceed with update? [yes/no]:
```

Type `yes` or `y` to continue. Anything else aborts the run with no changes sent to Director.

**To skip the prompt** (for pipelines or unattended runs):

```bash
ansible-playbook playbooks/versa_site_provision.yml --ask-vault-pass -e "assume_yes=true"
```

`assume_yes` can also be set permanently in `vars/director.yml`.

---

## Idempotency

The provisioning playbook is safe to re-run. For each CPE, STEP 3 queries Director before making any changes:

| Director response                          | Action taken                              |
|--------------------------------------------|-------------------------------------------|
| 404 — device not found                     | Full provisioning (POST + deploy)         |
| 200, `workflowStatus=Deployed`, `applianceExists=false` | Diff shown → confirm → PUT + deploy |
| 200, `workflowStatus=Deployed`, `applianceExists=true`  | Diff shown → confirm → PUT → re-deploy |
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

---

## Service Templates

A Versa service template (`serviceTemplateInfo`) is a named template that can be shared across multiple devices and orgs. Each device may be associated with one or more service templates, each carrying their own set of `$v_` variables.

### How it works

**Existing devices** — STEP 4 reads the current `serviceTemplateInfo` block from the Director GET response. Those variable bindings (including current Director values) are used as the base. Any Ansible var overrides defined in the site/CPE vars are applied on top before the PUT is sent.

**New devices** — STEP 4 builds the service template entries from the `service_templates:` list in the site or region vars file. Attrs start empty; Director fills autogeneratable values on POST.

### Associating service templates with a site

Add a `service_templates:` list to the site (or region) vars file:

```yaml
service_templates:
  - name: "NV_MGMT"
    org: "NVIDIA-IT"
  - name: "QoS_Srv_Tmplt_Springer_G1"
    org: "NVIDIA-IT"
```

`org` defaults to `org_name` if omitted.

### Mapping service template variables

Create `vars/service_templates/<template_name>.yml` with a `service_template_var_map` list and a `category` field. The `category` is sent to Director in the `deviceSpecificServiceTemplates` field of the POST/PUT body (common values: `general`, `class-of-service`):

```yaml
category: "general"

service_template_var_map:
  - director_var: "{$v_Director_Address-Prefix-1__vnfIpaddress}"
    ansible_var:  "svc_vz_mgmt_director_addr_1"
    type:         "ipv4_mask"
```

Variable metadata (which vars are user-supplied vs autogenerated by Director) is fetched from the Director API at `GET /nextgen/binddata/template/<name>`. Variables with `editable=true` in the response must be provided by the user; `editable=false` variables are filled by Director automatically on POST/PUT.

Then set the Ansible variable in the site or CPE vars file:

```yaml
devices:
  - device_name: "BRANCH-003-PRIMARY"
    ...
    svc_vz_mgmt_director_addr_1: "10.73.16.2/32"
```

If no var-map file exists for a template, all its attrs are passed through to Director unchanged (the service template is still included in the POST/PUT body). If a mapped Ansible variable is unset or empty, that attr is also passed through unchanged.

### Adding a New Service Template Mapping

1. Create `vars/service_templates/<template_name>.yml` with the `service_template_var_map` list.
2. Add the template to `service_templates:` in the relevant site/region vars file.
3. Set the Ansible variables in the site or CPE vars file.
4. No changes to playbook or task files needed.
