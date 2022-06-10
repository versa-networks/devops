---
- name: Create Device roles
  hosts: branches
  connection: local
  gather_facts: no

  roles:
    - create-device
