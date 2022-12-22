---
- name: Create Device roles
  hosts: localhost
  connection: local
  gather_facts: no

  roles:
    - create-parent-org
