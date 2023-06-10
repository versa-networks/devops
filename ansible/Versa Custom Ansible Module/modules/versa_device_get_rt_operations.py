#!/usr/bin/env python3

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: versa_device_get_operations

short_description: Versa Networks Module to perform get device BGP/route-table related operational data using REST API calls against Versa Director

version_added: "1.0.0"

description: Versa Networks Module to perform get device BGP/route-table related operational data using REST API calls against Versa Director.

options:
    host:
        description: hostname or ip adress of Versa Director
        required: true
        type: str

    username:
        description: Versa Director username for authentication
        required: true
        type: str

    password:
        description: Versa Director password for authentication
        required: true
        type: str

    devicename:
        description: Name of device/appliance as registered on Versa Director
        required: true
        type: str

    methodname:
        description: Method from pyVERSA library to execute for this task
        required: true
        type: str

author:
    - Versa Networks (@yourGitHubHandle)
'''

EXAMPLES = r'''
An example playbook:

- name: Test playbook
  hosts: localhost
  gather_facts: no

  tasks:
  - name: Get devices operational data from VD using custom Versa ansible module
    versa_vd_get_operations:
      username: "{{username}}"
      password: "{{password}}"
      host: "{{vd_host}}"
      devicename: "{{device_name}}
      vrfname: "{{vrf_name}}
      methodname: "{{ module_name }}"
      detailview: False
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pyVERSA import Director


def run_module():
    # define available arguments/parameters a user can pass to the module
    """
    module_args = dict(
        username=dict(type='str', required=True),
        password=dict(type='str', required=True),
        vd_host=dict(type='str', require=True)
    )
    """
    module = AnsibleModule(
       argument_spec=dict(
           host=dict(required=True),
           username=dict(required=True, type='str'),
           password=dict(required=True, type='str'),
           devicename=dict(required=True, type='str'),
           vrfname=dict(require=True, type='str'),
           methodname=dict(required=True, type='str'),
           detailview=dict(required=False, type=bool)
           ),
           supports_check_mode=True
       )

    result = dict(
        changed=False,
        original_message='',
        message='',
        my_useful_info={},
    )
    """
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    """
    if module.check_mode:
        module.exit_json(**result)

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)

    host = module.params['host']
    username = module.params['username']
    password = module.params['password']
    devicename = module.params['devicename']
    vrfname = module.params['vrfname']
    methodname = module.params['methodname']
    detailview = module.params['detailview'] if module.params['detailview'] else False
    #vd = Director('10.48.58.101', 'Administrator', 'V3rsa@123', verify_cert=False)
    vd = Director(host, username, password, verify_cert=False)
    #vd_result = vd.get_controllers()
    vd_result = getattr(vd, methodname)(deviceName=devicename, vrf=vrfname, detail=detailview)

    #result['original_message'] = module.params['name']
    result['message'] = 'FINISHED'
    result['result'] = vd_result
    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
