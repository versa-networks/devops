- name: Test playbook
  hosts: localhost
  gather_facts: no

  tasks:
  - name: Get devices from VD using custom Versa ansible module
    versa_vd_get_operations:
      username: "{{vd-username}}"
      password: "{{vd-password}}"
      host: "{{vd-host}}"
      methodname: "get_devices"
    register: results

  - debug: var=results
