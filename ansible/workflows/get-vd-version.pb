---
- name: Create Device roles
  hosts: localhost
  connection: local
  gather_facts: no

  roles:
    - get-vd-version
