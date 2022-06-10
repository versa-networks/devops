---
- name: Create BGP configuration
  hosts: branch01
  connection: local
  gather_facts: no

  roles:
    - create-bgp
