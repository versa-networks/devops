- name: Test playbook
  hosts: localhost
  gather_facts: no

  tasks:
  - name: Get device operational data from VD using custom Versa ansible module
    versa_device_get_rt_operations:
      username: "{{username}}"
      password: "{{password}}"
      host: "{{vd-host}}"
      devicename: "{{device_name}}"
      vrfname: "{{vrf_name}}"
      methodname: "{{method_name}}"
      detailview: False
    register: results

  - debug: var=results
