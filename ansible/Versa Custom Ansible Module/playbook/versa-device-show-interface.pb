- name: Test playbook
  hosts: localhost
  gather_facts: no

  tasks:
  - name: Get device operational data from VD using custom Versa ansible module
    versa_device_get_operations:
      username: "{{vd-username}}"
      password: "{{vd-password}}"
      host: "{{vd-host}}"
      devicename: "{{device_name}}"
      methodname: "show_interface"
    register: results

  - debug: var=results

