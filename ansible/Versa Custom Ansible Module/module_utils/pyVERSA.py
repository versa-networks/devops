#!/usr/bin/env python3
# coding=utf-8
"""
#####################################################################
#
# Purpose:  Library to abstract REST API calls to Versa Director
#
# Copyright (c) 2020 VERSA Networks. All rights reserved.
#
#
#####################################################################
"""


from jinja2 import Template
from requests.auth import HTTPBasicAuth
from io import BytesIO
from lxml import etree
import requests
import json
import yaml
import urllib3
import time
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


resource_uris = {
    'url_resource_paths': {
        '20.2': {
            'vd_create_analytics_cluster': '{{ base_url }}api/config/nms/provider',
            'vd_create_controller': '{{ base_url }}vnms/sdwan/workflow/controllers/controller',
            'vd_create_device': '{{ base_url }}vnms/sdwan/workflow/devices/device',
            'vd_create_devicegroup': '{{ base_url }}nextgen/deviceGroup',
            'vd_create_parent_org': '{{ base_url }}nextgen/organization',
            'vd_create_region': '{{ base_url }}nextgen/regions',
            'vd_create_transport_domain': '{{ base_url }}api/config/nms/sdwan/transport-domains',
            'vd_delete_analytics_cluster': '{{ base_url }}api/config/nms/provider/analytics-cluster/{{ analyticsClusterName }}',
            'vd_delete_device': '{{ base_url }}vnms/sdwan/workflow/devices/{{ deviceName }}',
            'vd_delete_deviceGroup': '{{ base_url }}nextgen/deviceGroup/{{ deviceGroupName }}',
            'vd_delete_region': '{{ base_url }}nextgen/regions/{{ regionName }}',
            'vd_delete_transport_domain': '{{ base_url }}api/config/nms/sdwan/transport-domains/transport-domain/{{ txDomainName }}',
            'vd_deploy_controller': '{{ base_url }}vnms/sdwan/workflow/controllers/controller/deploy/{{ controllerName }}',
            'vd_deploy_device': '{{ base_url }}vnms/sdwan/workflow/devices/device/deploy/{{deviceName}}',
            'vd_device_properties': '{{base_url}}api/config/devices/device/{{deviceName}}/config/orgs/org/{{orgName}}',
            'vd_get_analytics_cluster': '{{ base_url }}api/config/nms/provider/analytics-cluster',
            'vd_get_available_ControllerId': '{{ base_url }}vnms/sdwan/global/Controller/availableId',
            'vd_get_available_OrgId': '{{ base_url }}vnms/sdwan/global/Org/availableId',
            'vd_get_available_RegionId': '{{ base_url }}nextgen/regions/id',
            'vd_get_available_SiteId': '{{ base_url }}vnms/sdwan/global/Branch/availableId',
            'vd_get_available_VrfId': '{{ base_url }}vnms/sdwan/global/availableIds/VRF',
            'vd_get_controllers': '{{ base_url }}vnms/sdwan/workflow/controllers',
            'vd_get_deviceGroup': '{{ base_url }}nextgen/deviceGroup',
            'vd_get_device_bgp_config': '{{base_url}}api/config/devices/device/deviceName/config/protocols/bgp/global-bgp',
            'vd_get_device_networks': '{{base_url}}api/config/devices/device/{{ deviceName }}/config/networks',
            'vd_get_device_templates': '{{ base_url }}vnms/sdwan/workflow/templates',
            'vd_get_device_vrf_bgp_config': '{{base_url}}api/config/devices/device/{{deviceName}}/config/routing-instances/routing-instance/{{vrf}}/protocols/bgp/rti-bgp',
            'vd_get_devicegroups': '{{ base_url }}nextgen/deviceGroup/deviceGroupNames?organization={{ org_name }}',
            'vd_get_devices': '{{ base_url }}vnms/sdwan/workflow/devices',
            'vd_get_orgs': '{{ base_url }}nextgen/organization',
            'vd_get_orgs_root': '{{ base_url }}nextgen/organization/roots',
            'vd_get_regions': '{{ base_url }}nextgen/regions',
            'vd_get_task_details': '{{ base_url }}vnms/tasks/task/{{ task_id }}',
            'vd_get_transport_domains': '{{ base_url }}api/config/nms/sdwan/transport-domains',
            'vd_get_version': '{{ base_url }}api/operational/system/package-info',
            'vd_show_bgp_neighbor': '{{base_url}}api/operational/devices/device/{{deviceName}}/live-status/bgp/neighbors/detail/{{vrf}}/neighbor-ip',
            'vd_show_bgp_summary': '{{base_url}}api/operational/devices/device/{{deviceName}}/live-status/bgp/summary/instance/{{vrf}}',
            'vd_show_interface': '{{base_url}}api/operational/devices/device/{{deviceName}}/live-status/interfaces/{{interfaceType}}'
        },
        'default': {
            'vd_create_analytics_cluster': '{{ base_url }}api/config/nms/provider',
            'vd_create_controller': '{{ base_url }}vnms/sdwan/workflow/controllers/controller',
            'vd_create_device': '{{ base_url }}vnms/sdwan/workflow/devices/device',
            'vd_create_devicegroup': '{{ base_url }}nextgen/deviceGroup',
            'vd_create_parent_org': '{{ base_url }}nextgen/organization',
            'vd_create_region': '{{ base_url }}nextgen/regions',
            'vd_create_transport_domain': '{{ base_url }}api/config/nms/sdwan/transport-domains',
            'vd_delete_analytics_cluster': '{{ base_url }}api/config/nms/provider/analytics-cluster/{{ analyticsClusterName }}',
            'vd_delete_device': '{{ base_url }}vnms/sdwan/workflow/devices/{{ deviceName }}',
            'vd_delete_deviceGroup': '{{ base_url }}nextgen/deviceGroup/{{ deviceGroupName }}',
            'vd_delete_region': '{{ base_url }}nextgen/regions/{{ regionName }}',
            'vd_delete_transport_domain': '{{ base_url }}api/config/nms/sdwan/transport-domains/transport-domain/{{ txDomainName }}',
            'vd_deploy_controller': '{{ base_url }}vnms/sdwan/workflow/controllers/controller/deploy/{{ controllerName }}',
            'vd_deploy_device': '{{ base_url }}vnms/sdwan/workflow/devices/device/deploy/{{deviceName}}',
            'vd_device_properties': '{{base_url}}api/config/devices/device/{{deviceName}}/config/orgs/org/{{orgName}}',
            'vd_get_analytics_cluster': '{{ base_url }}api/config/nms/provider/analytics-cluster',
            'vd_get_available_ControllerId': '{{ base_url }}vnms/sdwan/global/Controller/availableId',
            'vd_get_available_OrgId': '{{ base_url }}vnms/sdwan/global/Org/availableId',
            'vd_get_available_RegionId': '{{ base_url }}nextgen/regions/id',
            'vd_get_available_SiteId': '{{ base_url }}vnms/sdwan/global/Branch/availableId',
            'vd_get_available_VrfId': '{{ base_url }}vnms/sdwan/global/availableIds/VRF',
            'vd_get_controllers': '{{ base_url }}vnms/sdwan/workflow/controllers',
            'vd_get_deviceGroup': '{{ base_url }}nextgen/deviceGroup',
            'vd_get_device_bgp_config': '{{base_url}}api/config/devices/device/deviceName/config/protocols/bgp/global-bgp',
            'vd_get_device_networks': '{{base_url}}api/config/devices/device/{{ deviceName }}/config/networks',
            'vd_get_device_templates': '{{ base_url }}vnms/sdwan/workflow/templates',
            'vd_get_device_vrf_bgp_config': '{{base_url}}api/config/devices/device/{{deviceName}}/config/routing-instances/routing-instance/{{vrf}}/protocols/bgp/rti-bgp',
            'vd_get_devicegroups': '{{ base_url }}nextgen/deviceGroup/deviceGroupNames?organization={{ org_name }}',
            'vd_get_devices': '{{ base_url }}vnms/sdwan/workflow/devices',
            'vd_get_orgs': '{{ base_url }}nextgen/organization',
            'vd_get_orgs_root': '{{ base_url }}nextgen/organization/roots',
            'vd_get_regions': '{{ base_url }}nextgen/regions',
            'vd_get_task_details': '{{ base_url }}vnms/tasks/task/{{ task_id }}',
            'vd_get_transport_domains': '{{ base_url }}api/config/nms/sdwan/transport-domains',
            'vd_get_version': '{{ base_url }}api/operational/system/package-info',
            'vd_show_bgp_neighbor': '{{base_url}}api/operational/devices/device/{{deviceName}}/live-status/bgp/neighbors/detail/{{vrf}}/neighbor-ip',
            'vd_show_bgp_summary': '{{base_url}}api/operational/devices/device/{{deviceName}}/live-status/bgp/summary/instance/{{vrf}}',
            'vd_show_interface': '{{base_url}}api/operational/devices/device/{{deviceName}}/live-status/interfaces/{{interfaceType}}'
        }
    }
}


class Director(object):
    """
    Defines Methods to VD REST API
    """

    def __init__(self,
                 host=None,
                 username=None,
                 password=None,
                 connection_timeout=90,
                 session_timeout=90,
                 port=9182, verify_cert=True, data_type='json'):
        """
        Initialize object to VD REST API
        Attributes for establishing connection to specified Versa Director required.

        Keyword Arguments:
            host {str}                  -- IP address or hostname of target VD.
            username {str}              -- Username to authenticate against target VD REST API for basic Authentication.
            password {str}              -- Password to authenticate against target VD REST API for basic Authentication.
            connection_timeout {int}    -- OPTIONAL: Specify connection timeout to VD REST API to change from default (default: 90)
            session_timeout {int}       -- OPTIONAL: Specify a session timeout for Token based authentication (default: 90)
            port {int}                  -- Specify TCP port to connect to VD REST API(default: {9182})
            verify_cert {bool}          -- Enable/Disable Verification of VD REST HTTPS SSL certificate (default: {True})
            data_type {str}             -- Specify data format. Options are 'JSON' and 'XML' (default: {'json'})
        """

        self.host = host
        self.username = username
        self.password = password
        self.connection_timeout = connection_timeout
        self.session_timeout = session_timeout
        self.port = port
        self.verify_cert = verify_cert
        self.base_url = f"https://{self.host}:{self.port}/"
        self.data_type = data_type
        #self.url_resource_paths = self.get_resource_paths()
        self.url_resource_templates = self.get_resource_paths()
        self.version = None
        self.get_version()  # if data_type == 'json' else 'default'

    def _get_token(self):
        pass

    def _generate_headers(self, data_type=None):
        """
        Generate Headers for HTTPS REST API

        Keyword Arguments:
            data_type {[type]}      -- Specify data format for 'Content-Type' and 'Accept' headers (default: {None})

        Returns:
            headers                 -- Dict of headers
        """
        valid_data_types = ['json', 'xml']

        if data_type and data_type in valid_data_types:
            headers = {
                "Content-Type": "application/%s"%data_type, 
                "Accept": "application/%s"%data_type
            }

        elif self.data_type in valid_data_types:
            headers = {
                "Content-Type": "application/%s"%self.data_type, 
                "Accept": "application/%s"%self.data_type
            }
        else:
            headers = {}

        ##rint(headers)         ### DEBUG

        return headers

    def change_data_type(self, data_type):
        valid_data_types = ('json', 'xml')
        if data_type in valid_data_types:
            self.data_type = data_type

    def rest_api_get(self, url_key=None, url=None, data_format=None):
        if not url and url_key:
            url = self.get_url_resource(url_key)

        data_type = data_format if data_format else self.data_type
        headers = self._generate_headers(data_type=data_type)

        response = requests.get(
            url, 
            auth=HTTPBasicAuth(self.username, self.password),
            headers=headers,
            verify=self.verify_cert
        )

        if response.status_code == 200 or response.status_code == 202:
            if data_type == 'json':
                result = response.json() if self.data_type == 'json' else response
            elif data_type == 'xml':
                result = response.text
            else:
                result = response
        else:
            result = response

        ##print(result)
        return result
    
    def rest_api_post(self, data=None, url_key=None, url=None, data_type=None):
        if data and data_type == 'json':
            try:
                json.loads(data)
                payload_ok = True
            except Exception as err:
                payload_ok = False
                print(err)
                raise ValueError("Invalid json object")

        elif not data:
            payload_ok = True
            print("No payload to REST POST")
            data_type = 'json'
        
        else:
            payload_ok = False
            #result = None
            print("Invalid data")
            raise ValueError("Invalid data type")

        if payload_ok:
            if not url and url_key:
                url = self.get_url_resource(url_key)

            headers = self._generate_headers(data_type)

            response = requests.post(
                url, 
                auth=HTTPBasicAuth(self.username, self.password),
                headers=headers,
                verify=self.verify_cert,
                data=data
            )

            #result = response.json() if self.data_type == 'json' else response

        return response

    def rest_api_put(self, data=None, url_key=None, url=None, data_type=None):
        if data and data_type == 'json':
            try:
                json.loads(data)
                payload_ok = True
            except Exception as err:
                payload_ok = False
                print(err)
                raise ValueError("Invalid json object")

        elif not data:
            payload_ok = True
            print("No payload to REST POST")
            data_type = 'json'
        
        else:
            payload_ok = False
            #result = None
            print("Invalid data")
            raise ValueError("Invalid data type")

        if payload_ok:
            if not url and url_key:
                url = self.get_url_resource(url_key)

            headers = self._generate_headers(data_type)

            response = requests.put(
                url, 
                auth=HTTPBasicAuth(self.username, self.password),
                headers=headers,
                verify=self.verify_cert,
                data=data
            )

            #result = response.json() if self.data_type == 'json' else response

        return response


    def rest_api_delete(self, url_key=None, url=None):

        if not url and url_key:
            url = self.get_url_resource(url_key)

        headers = self._generate_headers()

        response = requests.delete(
            url, 
            auth=HTTPBasicAuth(self.username, self.password),
            headers=headers,
            verify=self.verify_cert,
        )

        return response

    """
    def get_baseurl(self):
        return self.base_url
    """

    def get_resource_paths(self):
        """
        try:
            #abspath = os.path.dirname(os.path.abspath(__file__))
            with open('/home/ashvino/ansible/lib/ansible/module_utils/resource_paths.yml', 'r') as resource_file:
                resource_data = resource_file.read()
                url_resource_templates = yaml.safe_load(resource_data)['url_resource_paths']
                
        except Exception as err:
            url_resource_templates = None
            print(err)
        """
        url_resource_templates = resource_uris['url_resource_paths']

        #print(url_resource_templates)            ### DEBUG
        self.url_resource_templates = url_resource_templates
        return url_resource_templates

    def get_url_resource(self, url_key, variables=None):
        version = self.version if (self.version and self.version in self.url_resource_templates) else 'default'
        if variables:
            variables['base_url'] = self.base_url
        else:
            variables = {'base_url': self.base_url }

        url_resource_template = Template(self.url_resource_templates[version].get(url_key))

        url = url_resource_template.render(variables)
        print(url)
        return url

    def _load_xml(self, response):
        try:
            version_xml = etree.parse(BytesIO(response.content)).getroot()
        except Exception as err:
            print(err)
            version_xml = None
            raise ValueError("Invalid XML response")
            
        return version_xml

    def get_version(self):
        """Get VersaOS version from Versa Director

        Returns:
            [json or raw requests] -- JSON object from VD get_version if data_type is json else returns a raw response from requests.get
        """
        #url = self.get_resource_paths()['default'].get('vd_get_version')
        #url = self.get_url_resource('vd_get_version')          # Deprecating

        response = self.rest_api_get('vd_get_version')
        if self.data_type == 'json':
            version_short = ".".join((response['package-info'][0].get('major-version'), response['package-info'][0].get('minor-version')))
        elif self.data_type == 'xml':
            version_xml = self._load_xml(response)
            if version_xml is not None:
                ns  = version_xml.getchildren()[0].tag.split('}')[0] + "}" 
                version_data = version_xml.find(version_xml.getchildren()[0].tag)
                version_short = version_data.findtext(ns + "branch")
            else:
                print("Unable to find version")
                version_short = 'default'

        self.version = str(version_short)

        return response

    def get_devices(self, deviceName=None):
        """
        Get list of devices configured on VD.

        Keyword Arguments:
            deviceName {[str]} -- deviceName as configured on VD (default: {None})

        Returns:
            devices            -- Returns JSON object for list of devices from VD if request succesful
        """
        if deviceName:
            url = self.get_url_resource('vd_get_devices') + "/device/" + deviceName
            devices = self.rest_api_get(url=url)
        else:
            devices = self.rest_api_get('vd_get_devices')

        return devices

    def create_device(self, json_payload):
        """
        Create a Device on VD using REST POST.
        Equivalent to Workflow -> Device -> Add Device -> Save on VD
        JSON payload of device properties is sent to VD and if successful, device is in status: Saved.

        Arguments:
            json_payload [JSON]     -- JSON payload to create device

        Raises:
            ValueError:             If invalid JSON object given

        Returns:
            response                raw response as received. May contain a status_code as provided by requests library
        """
        url = self.get_url_resource('vd_create_device')

        availableSiteId = self.get_available_SiteId()
        try:
            data = json.loads(json_payload)
        except Exception as err:
            print(err)
            raise ValueError("Invalid json object")

        data['versanms.sdwan-device-workflow']['siteId'] = availableSiteId
        final_payload = json.dumps(data)
        response = self.rest_api_post(data=final_payload, url=url, data_type='json')


        return response

    def deploy_device(self, deviceName):
        """
        Deploy a Saved device on VD Workflow using REST POST
        This will initiate a Task on VD to Deploy the device.
        Equivalent to Workflow -> Device -> Deploy/Re-Deploy

        Arguments:
            deviceName [str]    -- Device Name of device as configured on VD
        Returns:
            raw response from requests library. response.status_code provides status code of REST.
        """
        vars = {'deviceName': deviceName}
        url = self.get_url_resource('vd_deploy_device', vars)
        response = self.rest_api_post(url=url)

        return response


    def get_deviceGroups(self, org_name=None):
        """
        Get list of Device Groups as configured on VD

        Keyword Arguments:
            org_name [str]     -- Specify Organization Name to filter Device Groups specific to organisation  (default: {None})

        Returns:
            devices            -- Returns JSON object for list of Device Groups from VD if request succesful
        """
        if org_name:
            vars = {'org_name': org_name }
            url = self.get_url_resource('vd_get_devicegroups', vars)
        ## print(url)           ### DEBUG
            deviceGroups = self.rest_api_get(url = url)
        else:
            deviceGroups = self.rest_api_get('vd_get_deviceGroup')

        return deviceGroups

    def get_available_SiteId(self, withSerialNumber=False):
        """
        Get unique global SiteId
        Required when creating a new device.

        Keyword Arguments:
            withSerialNumber {bool}     -- Specify this filter to get SiteId with generated UUID Serial Number (default: {False})

        Returns:
            availableSiteId [str]       -- Returns JSON object for list of availableSiteId from VD if request succesful
        """
        if withSerialNumber:
            url = self.get_url_resource('vd_get_available_SiteId') + "/withSerialNumber"
            available_SiteId = self.rest_api_get(url=url)
        else:
            available_SiteId = self.rest_api_get('vd_get_available_SiteId')
        return available_SiteId

    def get_available_OrgId(self):
        """
        Get unique global OrganizationId
        Required when creating a new Organization.

        Returns:
            availableOrgId [str]         -- Returns JSON object for list of availableOrgId from VD if request succesful
        """
        available_OrgId = self.rest_api_get('vd_get_available_OrgId')
        return available_OrgId

    def get_available_ControllerId(self):
        """
        Get unique global ControllerId
        Required when creating a new Controller.

        Returns:
            availableControllerId [str]       -- Returns JSON object for list of availableControllerId from VD if request succesful
        """
        available_ControllerId = self.rest_api_get('vd_get_available_ControllerId')
        return available_ControllerId

    def get_device_templates(self, deviceTemplate=None):
        """
        Get Device Templates configured on VD Workflow

        Keyword Arguments:
            deviceTemplate [str]        -- Filter by Device Template name. Provides more detailed config. (default: {None})

        Returns:
            deviceTemplates             -- Returns JSON object for list of Device Templates from VD if request succesful
        """
        if not deviceTemplate:
            return self.rest_api_get('vd_get_device_templates')
        else:
            url = self.get_url_resource('vd_get_device_templates') + "/template/" + deviceTemplate
            response = self.rest_api_get(url=url)

        return response

    def create_deviceGroup(self, json_payload=None, dg_org_name=None, dg_name=None):
        """
        Creates DeviceGroup on VD using REST POST

        Keyword Arguments:
            json_payload [JSON]         -- Provide full JSON body for creation of Device Group (default: {None})
            dg_org_name [str]           -- Provide DeviceGroup Organization Name instead of full JSON object (default: {None})
            dg_name [str]               -- Provide DeviceGroup Name instead of full JSON object (default: {None})

        Returns:
            response                raw response as received. May contain a status_code as provided by requests library
        """
        if json_payload:
            data = json_payload
        elif dg_org_name and dg_name:
            data = json.dumps({
                "device-group": {
                    "name": dg_name,
                    "dg:organization": dg_org_name
                }
            })

        response = self.rest_api_post(data, url_key='vd_create_devicegroup', data_type='json')

        return response

    def delete_deviceGroup(self, dg_name):
        """
        Delete specified Device Group using REST DELETE

        Keyword Arguments:
            dg_name [str]               -- Specify Device Group Name to be deleted

        Returns:
            response                    raw response as received. May contain a status_code as provided by requests library
        """
        vars = {'dg_name': dg_name }
        url = self.get_url_resource('vd_delete_deviceGroup', vars)
        print(url)          ### DEBUG
        response = self.rest_api_delete(url=url)

        return response

    def get_provider_org(self):
        """
        Get Provide Organization from VD

        Returns:
            OrganizationName            -- Returns JSON object for Provider Organization from VD if request succesful
        """
        response = self.rest_api_get('vd_get_orgs_root')
        return response

    def get_orgs(self, uuid_only=False, provider_only=False):
        """
        Get Organizations configured on VD

        Keyword Arguments:
            uuid_only [bool]            -- Filter attributes of Organization and return only uuid (default: {False})
            provider_only [bool]        -- Filter for Provider Organization only (default: {False})

        Returns:
            Organizations               -- Returns JSON object for list of Organizations from VD if request succesful
        """
        if uuid_only:
            url = self.get_url_resource('vd_get_orgs') + "?uuidOnly=true"
        elif provider_only:
            url = self.get_url_resource('vd_get_orgs') + "/roots"
        else:
            url = self.get_url_resource('vd_get_orgs')
        
        response = self.rest_api_get(url=url)

        return response

    def get_task_details(self, task_id):
        """
        Get Task details from VD

        Arguments:
            task_id [str]           -- Specify task_id to retrieve details from VD

        Returns:
            taskId details          -- Returns JSON object for task Id from VD if request succesful
        """
        vars = {'task_id': task_id}
        url = self.get_url_resource('vd_get_task_details', vars)
        #print(url)          ## DEBUG

        response = self.rest_api_get(url=url)

        return response

    def delete_device(self, deviceName):
        """
        Delete specified Device from VD using REST DELETE

        Arguments:
            deviceName [str]        -- Specify deviceName for device to be deleted.

        Returns:
            response                    raw response as received. May contain a status_code as provided by requests library
        """
        vars = {'deviceName': deviceName}
        url = self.get_url_resource('vd_delete_device', vars)
        #print(url)         ## DEBUG

        response = self.rest_api_delete(url=url)
        TASK_COMPLETED = False
        if response.status_code == 202:
            response_dict = response.json()
            task_id = response_dict['TaskResponse'].get('task-id')
            #task_href = response_dict['TaskResponse']['link'].get('href')
            print(f"Task {task_id} started to delete device")

            while not TASK_COMPLETED:
                task_status = self.get_task_details(task_id)
                if int(task_status['versa-tasks.task'].get('versa-tasks.percentage-completion')) == 100:
                    TASK_RESULT = task_status['versa-tasks.task'].get('versa-tasks.task-status')
                    TASK_COMPLETED = True
                    print(f"Task {task_id} completed with result: {TASK_RESULT}")
                    break
                time.sleep(2)  
            
        else:
            task_status = {'TASK_COMPLETED': TASK_COMPLETED}

        return response, task_status

    def get_transport_domains(self, detail=False):
        """
        Get Transport Domains available on VD

        Keyword Arguments:
            detail [bool]           -- Specify detail=True to get details for Transport domain (default: {False})

        Returns:
            transportDomain         -- Returns JSON object for list of Transport Domains from VD if request succesful
        """
        if detail:
            url = self.get_url_resource('vd_get_transport_domains') + "?deep=true"
            response = self.rest_api_get(url=url)
        else:
            response = self.rest_api_get('vd_get_transport_domains')

        return response
    
    def create_transport_domain(self, txDomainName, txDomainDescription=None):
        """
        Create Transport Domain on VD using REST POST

        Arguments:
            txDomainName {[type]}       -- Name of Transport Domain to be created

        Keyword Arguments:
            txDomainDescription [str] -- OPTIONAL: Provide a description to Transport Domain (default: {None})

        Returns:
            response                    raw response as received. May contain a status_code as provided by requests library
        """
        transport_domains = self.get_transport_domains(detail=True)
        txDomainIds = [ x.get('id') for x in transport_domains['transport-domains'].get('transport-domain')]
        txDomainId = int(sorted(txDomainIds)[-1]) + 10
        if txDomainId not in txDomainIds:
            data = {
                "transport-domain": {
                    "name": txDomainName,
                    "id": txDomainId
                }
            }
            if txDomainDescription:
                data['transport-domain']['description'] = txDomainDescription

            json_payload = json.dumps(data)
            response = self.rest_api_post(json_payload, 'vd_create_transport_domain', data_type='json')

        else:
            response = None

        return response


    def delete_transport_domain(self, txDomainName):
        """
        Delete Transport Domain from VD using REST DELETE

        Arguments:
            txDomainName [str]      -- Specify Transport Domain name to be deleted.

        Returns:
            response                    raw response as received. May contain a status_code as provided by requests library
        """
        vars = {'txDomainName': txDomainName }
        url = self.get_url_resource('vd_delete_transport_domain', vars)
        response = self.rest_api_delete(url=url)

        return response

    def get_controllers(self, controllerName=None):
        """
        Get list of controllers as configured on VD

        Returns:
            Controllers            -- Returns JSON object for list of Controllers from VD if request succesful
        """
        if controllerName:
            url = self.get_url_resource('vd_get_controllers') + "/controller/" + controllerName
            response = self.rest_api_get(url=url)
        else:
            response = self.rest_api_get('vd_get_controllers')

        return response

    def create_controller(self, json_payload, data_type=None):
        """
        Create Controller from JSON object using REST POST
        Equivalent to Workflow -> Infrastructure -> Controllers -> Add Controller -> Save on VD
        JSON payload of device properties is sent to VD and if successful, device is in status: Saved.

        Arguments:
            json_payload [JSON]         -- JSON payload for Controller properties

        Keyword Arguments:
            data_type [str]             -- Data format if different from JSON, e.g XML
            
        Returns:
            response                    raw response as received. May contain a status_code as provided by requests library
        """
        data = json.loads(json_payload)
        available_ControllerId = self.get_available_ControllerId()

        data['versanms.sdwan-controller-workflow']["siteId"] = available_ControllerId
        final_payload = json.dumps(data)
        print(final_payload)
        print(type(final_payload))
        response = self.rest_api_post(final_payload, 'vd_create_controller', data_type=data_type)

        return response

    def deploy_controller(self, controllerName):
        """
        Deploy a Saved Controller on VD using REST POST
        This will initiate a Task on VD to Deploy Controller
        Equivalent to Workflow -> Infrastructure -> Controllers -> Deploy/Re-Deploy

        Arguments:
            deviceName [str]    -- Device Name of device as configured on VD
        Returns:
            raw response from requests library. response.status_code provides status code of REST.
        """
        url = self.get_url_resource('vd_deploy_controller') + controllerName
        print(url)
        response = self.rest_api_post(url=url)

        return response

    def get_analytics_cluster(self, detail=False):
        """
        Get List of Analytics Clusters configured on VD

        Returns:
            analytics clusters    -- List of analytics clusters
        """
        if detail:
            url = self.get_url_resource('vd_get_analytics_cluster') + '?deep=true'
            response = self.rest_api_get(url=url)
        else:
            response = self.rest_api_get('vd_get_analytics_cluster')
        return response

    def create_analytics_cluster(self, json_payload):
        """
        Create Analytics Cluster from JSON body

        Example json_payload:
            {
                "analytics-cluster": [
                    {
                        "connector-config": {
                            "port": "8080",
                            "web-addresses": [
                                {
                                    "ip-address": "10.10.10.3",
                                    "name": "van01"
                                }
                            ]
                        },
                        "log-collector-config": {
                            "ip-address": [
                                "10.10.11.3"
                            ],
                            "port": "1234"
                        },
                        "name": "VAN01"
                    }
                ]
            }

        Arguments:
            json_payload [JSON]       -- JSON body for Analytics Cluster coniguration (default: {None})

        Returns:
            response                    raw response as received. May contain a status_code as provided by requests library
        """
        response = self.rest_api_post(json_payload, 'vd_create_analytics_cluster', data_type='json')
        return response

    def delete_analytics_cluster(self, analyticsClusterName):
        """
        Delete specified Analytics Cluster

        Arguments:
            analyticsClusterName [str] -- Analytics Cluster Name to be deleted

        Returns:
            response                    raw response as received. May contain a status_code as provided by requests library
        """
        vars = {'analyticsClusterName': analyticsClusterName }
        url = self.get_url_resource('vd_delete_analytics_cluster', vars)
        response = self.rest_api_delete(url=url)
        
        return response

    def get_available_RegiondId(self):
        """
        Get unique global RegionId
        Required when creating a new Region.

        Returns:
            availableRegionId [str]       -- Returns JSON object for list of availableRegionId from VD if request succesful
        """

        response = self.rest_api_get('vd_get_available_RegionId')
    
        return response
    
    def get_regions(self):
        """
        Get list of regions configured on VD

        Returns:
            Regions [JSON]       -- Returns JSON object for list of availableRegionId from VD if request succesful
        """
        response = self.rest_api_get('vd_get_regions')
        return response
    
    def create_region(self, regionName, regionDescription=None):
        """
        Create Region on VD using REST POST

        Arguments:
            regionName [str]        -- Region Name to be created

        Keyword Arguments:
            regionDescription [str] -- OPTIONAL: Description of Region (default: {None})
        """
        #def create_transport_domain(self, txDomainName, txDomainDescription=None):
        available_RegionId = self.get_available_RegiondId().get('nextAvailableRegionId')

        data = {
            "name": regionName,
            "regionId": available_RegionId,
        }

        if regionDescription:
            data['description'] = regionDescription

        json_payload = json.dumps(data)
        response = self.rest_api_post(json_payload, 'vd_create_region', data_type='json')

        return response

    def delete_region(self, regionName):
        """
        Delete specified Region

        Arguments:
            regionName [str]            -- Region Name to be deleted

        Returns:
            response                    raw response as received. May contain a status_code as provided by requests library
        """
        vars = {'regionName': regionName}
        url = self.get_url_resource('vd_delete_region', vars)
        print(url)
        response = self.rest_api_delete(url=url)

        return response

    def get_device_network(self, deviceName, detail=False):
        """
        Get Networks configured for Device

        Arguments:
            deviceName [str]     -- Specify name of Device for which to retrieve Networks

        Keyword Arguments:
            detail [bool]        -- Return more detailed output if detail=True (default: {False})

        Returns:
            Networks [JSON]      -- Returns JSON object for list of Networks from VD if request succesful
        """
        vars = { 'deviceName': deviceName }
        url_gen = self.get_url_resource('vd_get_device_networks', vars)
        if detail:
            url = url_gen + "?deep=true"
        else:
            url = url_gen

        response = self.rest_api_get(url=url)

        return response
    
    def get_device_bgp_config(self, deviceName, vrf=None, detail=False):
        """
        Get BGP configuration for Device

        Arguments:
            deviceName [str]    -- Device Name
        Keyword Arguments:
            vrf [str]           -- Specify vrf for BGP configuration (default: {None})
            detail [bool]       -- detail=True provides more detailed output (default: {False})

        Returns:
            BGP config [JSON]   -- Returns JSON object for device BGP configuration from VD if request succesful
        """
        if vrf:
            vars = {'deviceName': deviceName, 'vrf': vrf }
            
            url_gen = self.get_url_resource('vd_get_device_vrf_bgp_config', vars)
            if detail:
                url = url_gen + "?deep=true"
            else:
                url = url_gen
        else:
            vars = {'deviceName': deviceName}
            url_gen = self.get_url_resource('vd_get_device_bgp_config', vars)
            if detail:
                url = url_gen + "?deep=true"
            else:
                url = url_gen

        
        response = self.rest_api_get(url=url)

        return response


    def show_bgp_summary(self, deviceName, vrf, detail=False):
        """
        Retrieve JSON output for 'show bgp summary' command

        Arguments:
            deviceName [str]        -- device name
            vrf [str]               -- vrf or Routing-instance name 

        Keyword Arguments:
            detail [bool]           -- detail=True -> Detailed output (default: {False})

        Returns:
            BGP summary[JSON]       -- Returns JSON object for device BGP summary operational command from VD if request succesful
        """
        vars = {
            'deviceName': deviceName,
            'vrf': vrf
        }
        url = self.get_url_resource('vd_show_bgp_summary', vars) + ("?deep=true" if detail else "")
        print(url)

        response = self.rest_api_get(url=url)

        return response

    def show_bgp_neighbor(self, deviceName, vrf):
        """
        Retrieve JSON output for 'show bgp neighbor' command

        Arguments:
            deviceName [str]        -- Device Name
            vrf [str]               -- vrf or Routing-Instance name

        Returns:
            BGP neighbor [JSON]     -- Returns JSON object for device BGP neighbor operational command from VD if request succesful
        """
        vars = {
            'deviceName': deviceName,
            'vrf': vrf
        }
        url = self.get_url_resource('vd_show_bgp_neighbor', vars)

        response = self.rest_api_get(url=url)

        return response

    def show_interface(self, deviceName, interfaceType='brief', detail=False):
        """
        Retrieve JSON output for 'show interface' command

        Arguments:
            deviceName [str]            -- device name

        Keyword Arguments:
            interfaceType [str]         -- Specify interface type command. Options: 'brief', 'info', 'dynamic-tunnels' (default: {'brief'})
            detail [bool]               -- detail=True -> Provide detailed output (default: {False})

        Raises:
            ValueError: [description]

        Returns:
            [type] -- [description]
        """
        interfaceTypes = ('brief', 'info', 'dynamic-tunnels')
        if interfaceType in interfaceTypes:
            vars = {
                'deviceName': deviceName, 
                'interfaceType': interfaceType
            }
            url = self.get_url_resource('vd_show_interface', vars) + ("?deep=true" if detail else "")
            print(url)
            response = self.rest_api_get(url=url)
        else:
            response = None
            raise ValueError("Invalid Interface Type. Expected one of: %s" %(",".join(interfaceTypes)))

        return response
