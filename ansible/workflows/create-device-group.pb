---
- import_playbook: get-vd-version.pb

- name: Create Device roles
  hosts: all
  connection: local
  gather_facts: no

  roles:
    - create-devicegroup
