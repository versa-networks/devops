
#https://cloud-demo.versa-networks.com/versa/ncs-services/vnms/appliance/filter/BMBF-CruiseLines?offset=0&limit=25
#/versa/ncs-services/vnms/upload/url-file-upload/appliance?appliance=Gerardo-House-365&org-uuid=f282172d-0b00-4140-85c6-a115b0db65cd&fetch=count
#/versa/ncs-services/vnms/upload/url-file-upload/appliance?org-uuid=f282172d-0b00-4140-85c6-a115b0db65cd&file=SES_GRP_BLACKLIST_test_.csv&appliance=Gerardo-House-365

- name: Test to create Ansible PB for Certs managment
  hosts: localhost
  gather_facts: no
  vars_prompt:
  - name: username
    prompt: What is your username?
    private: no
  - name: password
    prompt: What is your password?
    private: yes
    #encrypt: sha512_crypt
    #confirm: no
    #salt_size: 7

  vars:
      device: "Gerardo-House-365"


  tasks:
    - name: Geting the device list
      uri:
        url: "https://cloud-demo.versa-networks.com:9182/vnms/dashboard/tenantDetailAppliances/Jeff?start=0&limit=4"
        method: GET
        user: "{{ username }}"
        password: "{{ password }}"
        headers:
          Accept: application/json
          Content-Type: application/json
        return_content: yes
        force_basic_auth: yes
        validate_certs: no
        follow_redirects: all
        timeout: 60
      ignore_errors: yes
      register: tasks_json
      failed_when: tasks_json.status != 200

    - name: Saving the Devices from Tenant
      set_fact:
        device_names: "{{ tasks_json.json | community.general.json_query('List.value[?applianceLocation.type==`branch`].applianceLocation.applianceName')}}"
        
    - debug: 
        msg: "{{ device_names }}"

    - name: Push url file to devices
      uri:
        url: "https://cloud-demo.versa-networks.com:9182/vnms/upload/url-file-upload/appliance?appliance={{ item }}&file=SES_GRP_BLACKLIST_test_.csv&org-uuid=f282172d-0b00-4140-85c6-a115b0db65cd"
        method: POST
        user: "{{ username }}"
        password: "{{ password }}"
        headers:
          Accept: application/json
          Content-Type: application/json
        return_content: yes
        force_basic_auth: yes
        validate_certs: no
        follow_redirects: all
        timeout: 60
      loop: "{{ device_names }}"
      ignore_errors: yes
      register: result
     # msg: "{{ result }}"
      failed_when: result.status != 200

    - debug:
        msg: "{{ result.value }}"
