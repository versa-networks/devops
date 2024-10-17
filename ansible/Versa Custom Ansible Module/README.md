Versa Custom Ansible Module:

Introduction
Automating Versa SD-WAN network with Ansible. This repository contains the custom library for managing the Versa SD-WAN Network with the help of REST API call.

SD-WAN automation with Ansible
Add the custom module utilities by dropping the file pyVERSA.py into module_utils directory adjacent to your collection or role. To load the custom modules automatically and make them available to all playbooks and roles, drop the files versa_device_get_operations.py, versa_device_get_rt_operations.py, versa_vd_get_operations.py in the interested folder and update the reference in the active ansible.cfg file. 

Example:
Sample Location:

bot1$ ls -l /home/versa/modules
-rw-rw-r-- 1 versa versa 3350 May 10  2023 versa_device_get_operations.py
-rw-rw-r-- 1 versa versa 3889 May 10  2023 versa_device_get_rt_operations.py
-rw-rw-r-- 1 versa versa 3023 May 10  2023 versa_vd_get_operations.py

bot1$ ls -l /home/versa/module_utils/
-rw-rw-r-- 1 versa versa 41911 May 10  2023 pyVERSA.py

Update the active ansible.cfg file with the below information.
library        = /home/versa/modules
module_utils   = /home/versa/module_utils/

Current Opeartions available:
get_version(self):
get_devices(self, deviceName=None):
get_deviceGroups(self, org_name=None):
get_available_SiteId(self, withSerialNumber=False):
get_available_OrgId(self):
get_available_ControllerId(self):
get_device_templates(self, deviceTemplate=None):
get_provider_org(self):
get_orgs(self, uuid_only=False, provider_only=False):
get_task_details(self, task_id):
get_transport_domains(self, detail=False):
get_controllers(self, controllerName=None):
get_analytics_cluster(self, detail=False):
get_available_RegiondId(self):
get_regions(self):
get_device_network(self, deviceName, detail=False):
get_device_bgp_config(self, deviceName, vrf=None, detail=False):
get_appliances(self):
get_dev_interface_config(self, deviceName):

versa@admin:~/ansible_playbook$ cat versa-device-show-bgp.pb
- name: Test playbook
  hosts: localhost
  gather_facts: no

  tasks:
  - name: Get device operational data from VD using custom Versa ansible module
    versa_device_get_rt_operations:
      username: "{{ rest_api_username }}"
      password: "{{ rest_api_password }}"
      host: "{{ vd }}"
      devicename: "controller1"
      vrfname: "TEST-Control-VR"
      methodname: "show_bgp_summary"
      detailview: True
    register: results

  - debug: var=results

versa@admin:~/ansible_playbook$ ansible-playbook versa-device-show-bgp.pb -i host

PLAY [Test playbook] *************************************************************************************************************************************************************************

TASK [Get device operational data from VD using custom Versa ansible module] *****************************************************************************************************************
ok: [localhost]

TASK [debug] *********************************************************************************************************************************************************************************
ok: [localhost] => {
    "results": {
        "changed": false,
        "failed": false,
        "message": "FINISHED",
        "my_useful_info": {},
        "original_message": "",
        "result": {
            "instance": {
                "address-family": [
                    {
                        "adj-rib-in-suppressed-routes": 0,
                        "advertised-routes": 0,
                        "afi-index": "ipv4",
                        "afi-safi-numloc-rib-routes": 9,
                        "aoc-rib-eligible-routes": 9,
                        "ebgp-routes-received": 0,
                        "ibgp-routes-received": 0,
                        "loc-rib-not-eligible-routes": 0,
                        "safi-index": "unicast"
                    },
                    {
                        "afi-index": "ipv4",
                        "safi-index": "multicast"
                    },
                    {
                        "adj-rib-in-suppressed-routes": 0,
                        "advertised-routes": 0,
                        "afi-index": "ipv4",
                        "afi-safi-numloc-rib-routes": 0,
                        "aoc-rib-eligible-routes": 0,
                        "ebgp-routes-received": 0,
                        "ibgp-routes-received": 0,
                        "loc-rib-not-eligible-routes": 0,
                        "safi-index": "mplsBgpVpn"
                    },
                    {
                        "afi-index": "ipv4",
                        "safi-index": "mplsBgpMVpn"
                    },
                    {
                        "adj-rib-in-suppressed-routes": 0,
                        "advertised-routes": 0,
                        "afi-index": "ipv4",
                        "afi-safi-numloc-rib-routes": 3,
                        "aoc-rib-eligible-routes": 3,
                        "ebgp-routes-received": 0,
                        "ibgp-routes-received": 0,
                        "loc-rib-not-eligible-routes": 0,
                        "safi-index": "versaPrivate"
                    },
                    {
                        "adj-rib-in-suppressed-routes": 0,
                        "advertised-routes": 0,
                        "afi-index": "ipv6",
                        "afi-safi-numloc-rib-routes": 0,
                        "aoc-rib-eligible-routes": 0,
                        "ebgp-routes-received": 0,
                        "ibgp-routes-received": 0,
                        "loc-rib-not-eligible-routes": 0,
                        "safi-index": "unicast"
                    },
                    {
                        "afi-index": "ipv6",
                        "safi-index": "multicast"
                    },
                    {
                        "adj-rib-in-suppressed-routes": 0,
                        "advertised-routes": 0,
                        "afi-index": "ipv6",
                        "afi-safi-numloc-rib-routes": 0,
                        "aoc-rib-eligible-routes": 0,
                        "ebgp-routes-received": 0,
                        "ibgp-routes-received": 0,
                        "loc-rib-not-eligible-routes": 0,
                        "safi-index": "mplsBgpVpn"
                    },
                    {
                        "afi-index": "ipv6",
                        "safi-index": "mplsBgpMVpn"
                    },
                    {
                        "adj-rib-in-suppressed-routes": 0,
                        "advertised-routes": 0,
                        "afi-index": "l2vpn",
                        "afi-safi-numloc-rib-routes": 0,
                        "aoc-rib-eligible-routes": 0,
                        "ebgp-routes-received": 0,
                        "ibgp-routes-received": 0,
                        "loc-rib-not-eligible-routes": 0,
                        "safi-index": "evpn"
                    }
                ],
                "instance": 2,
                "router-id": "10.2.64.1",
                "routing-instance": "TEST-Control-VR"
            }
        }
    }
}

PLAY RECAP ***********************************************************************************************************************************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0

versa@admin:~$ ansible -m versa_vd_get_operations -i hosts -a "host=10.48.58.101 username=Administrator password=xxxxxxxxx methodname=get_devices" localhost
localhost | SUCCESS => {
    "changed": false,
    "message": "FINISHED",
    "metadata": "Using VERSA NETWORKS Custom Ansible module",
    "my_useful_info": {},
    "original_message": "",
    "result": {
        "totalCount": 19,
        "versanms.sdwan-device-list": [
            {
                "deviceName": "branch01",
                "lastModifiedBy": "Administrator",
                "lastModifiedTime": "2023-01-16T14:18:12.666+0000",
                "siteId": "109",
                "workflowStatus": "Deployed"
            },
            {
                "deviceName": "branch02",
                "lastModifiedBy": "Administrator",
                "lastModifiedTime": "2023-01-16T14:18:37.818+0000",
                "siteId": "110",
                "workflowStatus": "Deployed"
            },
            {
                "deviceName": "branch03",
                "lastModifiedBy": "Administrator",
                "lastModifiedTime": "2023-01-16T14:19:02.754+0000",
                "siteId": "111",
                "workflowStatus": "Deployed"
            },
            {
                "deviceName": "MC-RVR",
                "lastModifiedBy": "Administrator",
                "lastModifiedTime": "2023-01-28T14:16:00.448+0000",
                "siteId": "113",
                "workflowStatus": "Deployed"
            },
            {
                "deviceName": "MC-SRC",
                "lastModifiedBy": "Administrator",
                "lastModifiedTime": "2023-01-28T12:55:10.215+0000",
                "siteId": "112",
                "workflowStatus": "Deployed"
            },
            {
                "deviceName": "ngfw01",
                "lastModifiedBy": "Administrator",
                "lastModifiedTime": "2020-12-02T10:44:15.811+0000",
                "siteId": "108",
                "workflowStatus": "Deployed"
            },
            {
                "deviceName": "sdwangw01",
                "lastModifiedBy": "Administrator",
                "lastModifiedTime": "2021-02-22T11:50:51.846+0000",
                "siteId": "114",
                "workflowStatus": "Deployed"
            },
            {
                "deviceName": "sfw01",
                "lastModifiedBy": "Administrator",
                "lastModifiedTime": "2020-12-02T13:02:54.221+0000",
                "siteId": "107",
                "workflowStatus": "Deployed"
            },
            {
                "deviceName": "sfw02",
                "lastModifiedBy": "Administrator",
                "lastModifiedTime": "2020-12-02T12:06:48.847+0000",
                "siteId": "106",
                "workflowStatus": "Deployed"
            },
            {
                "deviceName": "T1-2-internet",
                "lastModifiedBy": "Administrator",
                "lastModifiedTime": "2021-03-05T15:02:41.788+0000",
                "siteId": "118",
                "workflowStatus": "Deployed"
            },
            {
                "deviceName": "T1-Hub01",
                "lastModifiedBy": "Administrator",
                "lastModifiedTime": "2020-06-30T14:11:04.495+0000",
                "siteId": "104",
                "workflowStatus": "Deployed"
            },
            {
                "deviceName": "T1-Hub02",
                "lastModifiedBy": "Administrator",
                "lastModifiedTime": "2020-06-30T15:19:30.816+0000",
                "siteId": "105",
                "workflowStatus": "Deployed"
            },
            {
                "deviceName": "T1-SDWAN-GW01",
                "lastModifiedBy": "Administrator",
                "lastModifiedTime": "2021-02-22T13:04:18.333+0000",
                "siteId": "119",
                "workflowStatus": "Deployed"
            },
            {
                "deviceName": "T1-test-branch01",
                "lastModifiedBy": "Administrator",
                "lastModifiedTime": "2020-06-18T17:06:35.189+0000",
                "siteId": "101",
                "workflowStatus": "Deployed"
            },
            {
                "deviceName": "T1-test-branch10",
                "lastModifiedBy": "Administrator",
                "lastModifiedTime": "2020-06-22T12:24:46.680+0000",
                "siteId": "102",
                "workflowStatus": "Deployed"
            },
            {
                "deviceName": "T1-test-branch11",
                "lastModifiedBy": "Administrator",
                "lastModifiedTime": "2020-06-22T12:26:09.456+0000",
                "siteId": "103",
                "workflowStatus": "Deployed"
            },
            {
                "deviceName": "T4-Hub01",
                "lastModifiedBy": "Administrator",
                "lastModifiedTime": "2021-02-05T04:52:09.913+0000",
                "siteId": "115",
                "workflowStatus": "Deployed"
            },
            {
                "deviceName": "T4-Spoke01",
                "lastModifiedBy": "Administrator",
                "lastModifiedTime": "2021-02-05T05:09:45.518+0000",
                "siteId": "116",
                "workflowStatus": "Deployed"
            },
            {
                "deviceName": "T4-Spoke02",
                "lastModifiedBy": "Administrator",
                "lastModifiedTime": "2021-02-05T05:24:34.589+0000",
                "siteId": "117",
                "workflowStatus": "Deployed"
            }
        ]
    }
}
versa@admin:~$ ~
