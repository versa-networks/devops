# Ansible Playbooks to automate configuration of workflows

Uses REST API calls to VD create/update workflows [create device-groups, create devices, create bgp configuration]

### Requirements
Requirements specified in requirements.txt

#### Ansible Directory Structure
```
$ tree
.
├── README.md
├── check-devicegroup.pb
├── create-bgp.pb
├── create-device-group.pb
├── create-devices.pb
├── create-parent-org.pb
├── get-vd-version.pb
├── group_vars
│   ├── BR03
│   │   └── var.yaml
│   └── all
│       ├── all.yaml
│       ├── credentials.yml
│       └── resource_paths.yaml
├── host_vars
│   ├── branch01
│   │   └── var.yml
│   ├── branch03
│   │   └── vars.yaml
│   ├── branch07
│   │   └── vars.yaml
│   └── branch08
│       └── vars.yaml
├── hosts
└── roles
    ├── create-bgp
    │   ├── tasks
    │   │   └── main.yml
    │   └── templates
    │       ├── json_template.j2
    │       └── json_template_static.j2
    ├── create-device
    │   ├── tasks
    │   │   └── main.yaml
    │   └── templates
    │       └── json_template.j2
    ├── create-devicegroup
    │   ├── tasks
    │   │   ├── check-devicegroup.yaml
    │   │   └── main.yaml
    │   └── templates
    │       └── json_template.j2
    ├── create-parent-org
    │   ├── tasks
    │   │   └── main.yaml
    │   ├── templates
    │   │   └── json_template.j2
    │   └── vars
    │       ├── credentials.json
    │       └── credentials.yml
    └── get-vd-version
        └── tasks
            └── main.yaml
```

#### VD REST API Call Resources
The REST API call for version 20.2.1 are defined in group_vars/all/resource_paths.yaml

If REST API calls are different for other VD versions, these can be added to this variable file.

Sample Content:
```
$ cat group_vars/all/resource_paths.yaml
---
url_resource_paths:
  20.2: &default              # Enable inheritance
    vd_get_available_OrgId: "{{ base_url }}vnms/sdwan/global/Org/availableId"
    vd_get_available_VrfId: "{{ base_url }}vnms/sdwan/global/availableIds/VRF"
    vd_get_available_SiteId: "{{ base_url }}vnms/sdwan/global/Branch/availableId/withSerialNumber"
    vd_get_orgs_root: "{{ base_url }}nextgen/organization/roots"
    vd_get_devicegroups: "{{ base_url}}nextgen/deviceGroup/deviceGroupNames?organization={{ org_name }}"
    vd_create_parent_org: "{{ base_url }}nextgen/organization"
    vd_create_devicegroup: "{{ base_url }}nextgen/deviceGroup"
    vd_get_devices: "{{ base_url }}vnms/sdwan/workflow/devices"
    vd_create_device: "{{ base_url }}vnms/sdwan/workflow/devices/device"
    vd_deploy_device: "{{ base_url }}vnms/sdwan/workflow/devices/device/deploy/{{ inventory_hostname }}"
  default:
    <<: *default               # Inherit all values from 20.2 (set as default)
    vd_get_version: "{{ base_url }}api/operational/system/package-info"
```

#### Example of running a playbook:
```
$ ansible-playbook create-devices.pb -i hosts

PLAY [Create Device roles] ***********************************************************************************************************************************************************************************************************************************

TASK [get-vd-version : Get version of Versa Director] ********************************************************************************************************************************************************************************************************
ok: [branch07]
ok: [branch08]
ok: [branch03]

TASK [get-vd-version : Register vd_version] ******************************************************************************************************************************************************************************************************************
ok: [branch07]
ok: [branch08]
ok: [branch03]

TASK [create-devicegroup : Check if DeviceGroup exists on Versa Director for organisation acme] **************************************************************************************************************************************************************
ok: [branch07 -> localhost]
ok: [branch03 -> localhost]
ok: [branch08 -> localhost]

TASK [create-devicegroup : [DEBUG] Generate temporary JSON config & store in /tmp/branch07_devicegroup.json] *************************************************************************************************************************************************
skipping: [branch07]
skipping: [branch08]
ok: [branch03]

TASK [create-devicegroup : Create DeviceGroup on Versa Director for organisation acme] ***********************************************************************************************************************************************************************
skipping: [branch07]
skipping: [branch08]
changed: [branch03]

TASK [get-vd-version : Get version of Versa Director] ********************************************************************************************************************************************************************************************************
skipping: [branch07]
skipping: [branch08]
skipping: [branch03]

TASK [get-vd-version : Register vd_version] ******************************************************************************************************************************************************************************************************************
skipping: [branch07]
skipping: [branch08]
skipping: [branch03]

TASK [create-device : Retrieve available SiteId from Versa Director] *****************************************************************************************************************************************************************************************
ok: [branch07]
ok: [branch08]
ok: [branch03]

TASK [create-device : Register SiteId] ***********************************************************************************************************************************************************************************************************************
ok: [branch07]
ok: [branch08]
ok: [branch03]

TASK [create-device : Generate temporary JSON config & store in /tmp] ****************************************************************************************************************************************************************************************
changed: [branch08]
changed: [branch03]
changed: [branch07]

TASK [create-device : Create device on Versa Director Workflow] **********************************************************************************************************************************************************************************************
changed: [branch07]
changed: [branch03]
changed: [branch08]

TASK [create-device : Deploy device on Versa Director Workflow] **********************************************************************************************************************************************************************************************
changed: [branch08]
changed: [branch07]
changed: [branch03]

TASK [create-device : Output results of Deploy Device task] **************************************************************************************************************************************************************************************************
ok: [branch07] => {
    "results1.json.TaskResponse": {
        "link": {
            "href": "vnms/tasks/task/206",
            "rel": "GET"
        },
        "task-id": "206"
    }
}
ok: [branch08] => {
    "results1.json.TaskResponse": {
        "link": {
            "href": "vnms/tasks/task/204",
            "rel": "GET"
        },
        "task-id": "204"
    }
}
ok: [branch03] => {
    "results1.json.TaskResponse": {
        "link": {
            "href": "vnms/tasks/task/205",
            "rel": "GET"
        },
        "task-id": "205"
    }
}

TASK [create-device : Register TaskId for Deployment Tasks] **************************************************************************************************************************************************************************************************
ok: [branch07]
ok: [branch08]
ok: [branch03]

TASK [create-device : Wait for Deployment Tasks to complete on Versa Director] *******************************************************************************************************************************************************************************
FAILED - RETRYING: Wait for Deployment Tasks to complete on Versa Director (6 retries left).
FAILED - RETRYING: Wait for Deployment Tasks to complete on Versa Director (6 retries left).
FAILED - RETRYING: Wait for Deployment Tasks to complete on Versa Director (6 retries left).
ok: [branch07]
ok: [branch08]
ok: [branch03]

TASK [create-device : Verify Device template status is 'Deployed' on Versa Director] *************************************************************************************************************************************************************************
ok: [branch07]
ok: [branch08]
ok: [branch03]

TASK [create-device : Return status of Devices created] ******************************************************************************************************************************************************************************************************
skipping: [branch07] => (item={u'lastModifiedBy': u'Administrator', u'deviceName': u'branch01', u'lastModifiedTime': u'2020-04-14T14:27:20.973+0000', u'workflowStatus': u'Deployed', u'siteId': u'101'})
skipping: [branch07] => (item={u'lastModifiedBy': u'Administrator', u'deviceName': u'branch02', u'lastModifiedTime': u'2020-04-15T10:58:51.835+0000', u'workflowStatus': u'Deployed', u'siteId': u'102'})
skipping: [branch08] => (item={u'lastModifiedBy': u'Administrator', u'deviceName': u'branch01', u'lastModifiedTime': u'2020-04-14T14:27:20.973+0000', u'workflowStatus': u'Deployed', u'siteId': u'101'})
skipping: [branch07] => (item={u'lastModifiedBy': u'Administrator', u'deviceName': u'branch03', u'lastModifiedTime': u'2020-05-05T08:32:07.331+0000', u'workflowStatus': u'Deployed', u'siteId': u'105'})
skipping: [branch08] => (item={u'lastModifiedBy': u'Administrator', u'deviceName': u'branch02', u'lastModifiedTime': u'2020-04-15T10:58:51.835+0000', u'workflowStatus': u'Deployed', u'siteId': u'102'})
skipping: [branch03] => (item={u'lastModifiedBy': u'Administrator', u'deviceName': u'branch01', u'lastModifiedTime': u'2020-04-14T14:27:20.973+0000', u'workflowStatus': u'Deployed', u'siteId': u'101'})
skipping: [branch08] => (item={u'lastModifiedBy': u'Administrator', u'deviceName': u'branch03', u'lastModifiedTime': u'2020-05-05T08:32:07.331+0000', u'workflowStatus': u'Deployed', u'siteId': u'105'})
skipping: [branch03] => (item={u'lastModifiedBy': u'Administrator', u'deviceName': u'branch02', u'lastModifiedTime': u'2020-04-15T10:58:51.835+0000', u'workflowStatus': u'Deployed', u'siteId': u'102'})
ok: [branch07] => (item={u'lastModifiedBy': u'Administrator', u'deviceName': u'branch07', u'lastModifiedTime': u'2020-05-05T08:32:10.390+0000', u'workflowStatus': u'Deployed', u'siteId': u'103'}) => {
    "ansible_loop_var": "item",
    "item": {
        "deviceName": "branch07",
        "lastModifiedBy": "Administrator",
        "lastModifiedTime": "2020-05-05T08:32:10.390+0000",
        "siteId": "103",
        "workflowStatus": "Deployed"
    }
}
skipping: [branch08] => (item={u'lastModifiedBy': u'Administrator', u'deviceName': u'branch07', u'lastModifiedTime': u'2020-05-05T08:32:10.390+0000', u'workflowStatus': u'Deployed', u'siteId': u'103'})
skipping: [branch07] => (item={u'lastModifiedBy': u'Administrator', u'deviceName': u'branch08', u'lastModifiedTime': u'2020-05-05T08:32:09.015+0000', u'workflowStatus': u'Deployed', u'siteId': u'104'})
ok: [branch03] => (item={u'lastModifiedBy': u'Administrator', u'deviceName': u'branch03', u'lastModifiedTime': u'2020-05-05T08:32:07.331+0000', u'workflowStatus': u'Deployed', u'siteId': u'105'}) => {
    "ansible_loop_var": "item",
    "item": {
        "deviceName": "branch03",
        "lastModifiedBy": "Administrator",
        "lastModifiedTime": "2020-05-05T08:32:07.331+0000",
        "siteId": "105",
        "workflowStatus": "Deployed"
    }
}
ok: [branch08] => (item={u'lastModifiedBy': u'Administrator', u'deviceName': u'branch08', u'lastModifiedTime': u'2020-05-05T08:32:09.015+0000', u'workflowStatus': u'Deployed', u'siteId': u'104'}) => {
    "ansible_loop_var": "item",
    "item": {
        "deviceName": "branch08",
        "lastModifiedBy": "Administrator",
        "lastModifiedTime": "2020-05-05T08:32:09.015+0000",
        "siteId": "104",
        "workflowStatus": "Deployed"
    }
}
skipping: [branch03] => (item={u'lastModifiedBy': u'Administrator', u'deviceName': u'branch07', u'lastModifiedTime': u'2020-05-05T08:32:10.390+0000', u'workflowStatus': u'Deployed', u'siteId': u'103'})
skipping: [branch03] => (item={u'lastModifiedBy': u'Administrator', u'deviceName': u'branch08', u'lastModifiedTime': u'2020-05-05T08:32:09.015+0000', u'workflowStatus': u'Deployed', u'siteId': u'104'})

PLAY RECAP ***************************************************************************************************************************************************************************************************************************************************
branch03                   : ok=15   changed=4    unreachable=0    failed=0    skipped=2    rescued=0    ignored=0
branch07                   : ok=13   changed=3    unreachable=0    failed=0    skipped=4    rescued=0    ignored=0
branch08                   : ok=13   changed=3    unreachable=0    failed=0    skipped=4    rescued=0    ignored=0



$ ansible-playbook create-bgp.pb -i hosts

PLAY [Create BGP configuration] ******************************************************************************************************************************************************************************************************************************

TASK [create-bgp : [DEBUG] Generate temporary JSON config & store in /tmp/branch01_bgp.json] *****************************************************************************************************************************************************************
ok: [branch01]

TASK [create-bgp : Deploy BGP Configuration to Device] *******************************************************************************************************************************************************************************************************
changed: [branch01]

TASK [create-bgp : debug] ************************************************************************************************************************************************************************************************************************************
ok: [branch01] => {
    "results1": {
        "accept": "application/vnd.yang.data+json",
        "accept_encoding": "deflate",
        "auditid": "51",
        "cache_control": "no-cache, no-store, max-age=0, must-revalidate",
        "changed": true,
        "connection": "close",
        "content": "",
        "content_length": "0",
        "content_type": "application/vnd.yang.data+json",
        "cookies": {},
        "cookies_string": "",
        "date": "Tue, 05 May 2020 08:41:21 GMT",
        "elapsed": 17,
        "etag": "1588-668065-853318@localhost",
        "expires": "0",
        "failed": false,
        "last_modified": "Thu, 23 Apr 2020 09:22:19 GMT",
        "location": "http://localhost:9181/api/config/devices/device/branch01/config/routing-module:routing-instances/routing-instance/acme-LAN-VR/protocols/bgp/rti-bgp/1",
        "msg": "OK (0 bytes)",
        "pragma": "no-cache",
        "redirected": false,
        "response_time": "Tue, 05 May 2020 8:41:21 UTC",
        "server": "VersaDirector",
        "status": 201,
        "strict_transport_security": "max-age=31536000 ; includeSubDomains",
        "tenant": "ProviderDataCenterSystemAdmin",
        "url": "https://10.48.58.51:9182/api/config/devices/device/branch01/config/routing-instances/routing-instance/acme-LAN-VR/protocols/bgp",
        "x_content_type_options": "nosniff, nosniff",
        "x_frame_options": "DENY",
        "x_xss_protection": "1; mode=block"
    }
}

PLAY RECAP ***************************************************************************************************************************************************************************************************************************************************
branch01                   : ok=3    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

