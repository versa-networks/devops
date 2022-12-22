#!/usr/bin/env python3

import os, sys, signal, argparse
import jinja2
from jinja2.utils import concat
import re
import requests
import time
import base64
import xmltodict
import subprocess
import json
from pprint import pprint
from collections import OrderedDict
import uuid
import copy
from pprint import pprint

pyVer = sys.version_info
if pyVer.major == 3:
  import ssl
  import http.client as httplib 
else:
  import httplib

#import vnms
vnms =  None
analy = None 
cntlr = None
cust = None
admin = None
debug = 0

in_ip = None
in_port = None
in_user = None
in_pswd = None

class bcolors:
  """ the background colors
  """
  HEADER = '\033[95m'
  OKBLUE = '\033[94m'
  OKGREEN = '\033[92m'
  OKCHECK = '\033[96m'
  OKWARN = '\033[93m'
  FAIL = '\033[91m'
  ENDC = '\033[0m'
  BOLD = '\033[1m'
  UNDERLINE = '\033[4m'


def argcheck():
  """ This performs adds the  argument and checks the requisite inputs
  """
  global args
  mystr = os.path.basename(sys.argv[0])
  parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]),description='%(prog)s Help:',usage='%(prog)s -f filename [options]', add_help=False)
  parser.add_argument('-f','--file',required=True, help='input file [required ]' )
  parser.add_argument('-i','--ip',required=True, help='ip' )
  parser.add_argument('-p','--port',default=9182, help='port')
  parser.add_argument('-u','--user',default='Administrator', help='User')
  parser.add_argument('-P','--pswd',default='versa123', help='User')
  parser.add_argument('-d','--debug',default=0, help='set/unset debug flag')

  try:
    args = vars(parser.parse_args())
  except:
    usage()
    sys.exit(0)

def usage():
  mystr = os.path.basename(sys.argv[0])
  print(bcolors.OKCHECK)
  print( """\
Usage:
    To change versions use:
      %(mystr)s --f/-f <infile> -i <ip> -p <port 9182> -u <user> -P <pswd>
    To add more debug:
      %(mystr)s -f <infile> --debug/-d [0/1]
  """ %locals())
  print(bcolors.ENDC)



#from jinja2 import Environment, PackageLoader
#, select_autoescape
def analycall(api_dict):
    global debug, admin
    #vdict = {'body': _payload, 'resp': resp, 'method': _method, 'uri': _uri, 'ip': in_ip,  
    #         'port' : in_port, 'user' : in_user, 'pswd' : in_pswd }
    prefix_uri = "https://{0}:{1}/versa/".format(api_dict['ip'],api_dict['port'])
    prefix_uri1 = "https://{0}:{1}".format(api_dict['ip'],api_dict['port'])
    sess = requests.session()
    url = "{0}login?username={1}&password={2}".format(prefix_uri,api_dict['user'],api_dict['pswd'])
    res = sess.post(url, verify=False)
    if res and res.ok:
      tkn =res.headers['x-csrf-token']
    else: 
      print("Failed")
      return
    url = "{0}{1}".format(prefix_uri1,api_dict['uri'])
    headers = {'Content-type': 'application/json','Accept': 'text/plain','x-csrf-token': tkn} 
    headers['Accept'] = headers['Accept'] + ", application/json"
    res = sess.post(url,data=api_dict['body'],headers=headers)
    if res and res.ok:
      pass
    else: 
      print("Failed")
    sess.close()
    return

# Function to call the RestAPIs
def call(api_dict, auth_type='Basic', content_type="xml", ncs_cmd="yes", max_retry_for_task_completion=30, jsonflag=0):
    global debug, admin
    auth = api_dict['auth']
    ret_true = [1, ""]
    ret_false = [0, ""]
    try:
        resp_string = ""
        if content_type == "json":
            if ncs_cmd == "yes":
                request_headers = {
                    "Authorization": "Basic %s" % auth,
                    "Content-type": "application/vnd.yang.data+json"
                }
                rest_headers = {
                    "Authorization": "Basic %s" % auth,
                    "Accept": "application/vnd.yang.data+json",
                    "Content-type": "application/vnd.yang.data+json"
                }
            else:
                request_headers = {
                    "Authorization": "Basic %s" % auth,
                    "Content-type": "application/json"
                }
                rest_headers = {
                    "Authorization": "Basic %s" % auth,
                    "Accept": "application/json",
                    "Content-type": "application/json"
                }
        else:
            rest_headers = {
                "Authorization": "Basic %s" % auth,
                "Accept": "application/xml",
                "Content-type": "application/xml"
            }
        empty_headers = {"Authorization": "Basic %s" % auth, "Accept": "*/*"}
        if api_dict['method'] == "GET" and jsonflag == 0:
            headers = empty_headers
        else:
            headers = rest_headers
        if content_type == "xml2":
            headers = {
                "Authorization": "Basic %s" % auth,
                "Accept": "application/xml",
                "Content-type": "application/xml"
            }

        att = 0
        while att  < 2: 
         try:
          webservice = None
          if pyVer.major == 3:
            webservice = httplib.HTTPSConnection(api_dict['vd_ip'], int(api_dict['vd_rest_port']),context=ssl._create_unverified_context())
          else: 
            webservice = httplib.HTTPSConnection(api_dict['vd_ip'], int(api_dict['vd_rest_port']))
          webservice.request(api_dict['method'], api_dict['uri'],
                           api_dict['body'], headers)
          break
         except:
          att = att + 1
          print("Attempt %s " % (str(att)))

        resp_obj = webservice.getresponse()
        if pyVer.major == 3:
          resp_string = (resp_obj.read()).decode(encoding='utf-8',errors="ignore")
        else: 
          resp_string = str(resp_obj.read())
        resp_code = str(resp_obj.status)
        response = resp_code
        reason = str(resp_obj.reason)
        webservice.close()
        # We can not be so strict so we are just check 2 digits of the response code 
        #if not (resp_code == api_dict['resp'] or
        #        ('resp2' in api_dict and resp_code == api_dict['resp2'])):
        if not (resp_code[0:2] == api_dict['resp'][0:2] or
                ('resp2' in api_dict and resp_code[0:2] == api_dict['resp2'][0:2])):
            if not api_dict['method'] == 'GET':
               if debug:
                print("Did not receive expected Response Code: Expected %s Got %s with Reason: %s for Uri=%s"
                    % (api_dict['resp'], resp_code,resp_string,api_dict['uri']))
               else:
                print( "Did not receive expected Response Code: Expected %s Got %s for Uri=%s"
                    % (api_dict['resp'], resp_code,api_dict['uri']))
            else:
               if debug:
                print("Did not recieve expected Response Code: Expected %s Got %s with Reason: %s"
                    % (api_dict['resp'], resp_code,resp_string,api_dict['uri']))
               else:
                print( "Did not receive expected Response Code: Expected %s Got %s for Uri=%s"
                    % (api_dict['resp'], resp_code,api_dict['uri']))
            #print("-" * 10)
            #return ret_false
            return [0, resp_string]
        else:
            if 'task-id' in resp_string:
                # Task is created, we need to poll
                task_id = _get_task_id(resp_string)
                if not task_id:
                    return ret_false
                retval = _task_poll(task_id,api_dict,
                                  max_retry=max_retry_for_task_completion)
                if retval == True: return ret_true
                else: return ret_false 
            if api_dict['method'] == 'GET':
                return [1, resp_string]
            return [1, resp_string]
    except Exception as ex:
        print("ERROR, Exception @ REST-Api CALL = %s for URI %s : Error: %s" %(api_dict['method'], api_dict['uri'], str(ex)))

def _task_poll( task_id, vdict, max_retry=5, sleep_interval=10):
    api_dict = {}
    api_dict['method'] = 'GET'
    #api_dict['uri'] = '/api/operational/tasks/task/%s'%task_id
    api_dict['uri'] = '/vnms/tasks/task/%s'%task_id
    api_dict['body'] = ''
    api_dict['resp'] = '200'
    api_dict['vd_ip'] = vdict['vd_ip']
    api_dict['vd_rest_port'] = vdict['vd_rest_port']
    api_dict['auth']  = vdict['auth'] 
    timeout = 1
    count = 1
    jstr = {}
    while timeout and count <= max_retry :
        [ret, task_progress] = call(api_dict,content_type="json",ncs_cmd="no")
        if ret == 0:
            print("Failed to GET Progress for Task: %s"%task_id)
            return False
        #completion = task_progress[1]
        completion = task_progress
        jstr = json.loads(completion)
        #cdict = xmltodict.parse(completion)
        #if int(cdict['task']['percentage-completion']) == 100:
        #    timeout = 0
        #print('Polling Status: %s:  Task %s : Completion: %s' \
        #        %(count, task_id, cdict['task']['percentage-completion']))
        if int(jstr["versa-tasks.task"]["versa-tasks.percentage-completion"]) == 100:
           timeout = 0
        print('Polling Status: %s:  Task %s : Completion: %s' \
                %(count, task_id, jstr["versa-tasks.task"]["versa-tasks.percentage-completion"]))

        time.sleep(2)
        count += 1
    if not timeout and jstr["versa-tasks.task"]["versa-tasks.task-status"] != 'FAILED':
        return True
    return False

def _get_task_id( string):
    try:
      jstr=json.loads (string)
      if "TaskResponse" in jstr:
        return str(jstr["TaskResponse"]["task-id"])
      elif "output" in jstr and 'result' in jstr['output']:
        return str(jstr['output']['result']['task']['task-id'])
    except:
      pass
    try:
      xdict = xmltodict.parse(string)
      return xdict['output']['result']['task']['task-id']
    except Exception:
      pass
    try:
      resp_dict = ast.literal_eval(string)
      taskId = resp_dict['TaskResponse']['task-id']
      return taskId
    except Exception as ex:
      return False


def analytics_call( _method, _uri,_payload,resp='200'):
    global debug, admin
    global in_ip, in_port, in_user, in_pswd
    vdict = {}
    vdict = {'body': _payload, 'resp': resp, 'method': _method, 'uri': _uri, 'ip': in_ip,  
             'port' : in_port, 'user' : in_user, 'pswd' : in_pswd }
    out = analycall(vdict)
    return ''

def scrub(obj, bad_key="_this_is_bad"):
    if isinstance(obj, dict):
      # the call to `list` is useless for py2 but makes
      # the code py2/py3 compatible
      for key in list(obj.keys()):
        if key == bad_key:
          del obj[key]
        else:
          scrub(obj[key], bad_key)
    elif isinstance(obj, list):
      for i in reversed(range(len(obj))):
        if obj[i] == bad_key:
          del obj[i]
        else:
          scrub(obj[i], bad_key)
    else:
      # neither a dict nor a list, do nothing
      pass

def get_cntlr_org_services( _method, _uri, _payload,resp='200', vd_data=None,_ofile=None):
  global vnms, analy, cntlr, cust, admin, mlog
  resp2 = '202'
  vdict = {}
  vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method':_method , 'uri': _uri,
            'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
            'auth': vd_data['auth'] }
  [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
  customer="Customer1"
  org_data = {}
  if len(resp_str) > 3:
    jstr = json.loads(resp_str)
    if "ipsec" in jstr:
      for _elem in jstr["ipsec"]["vpn-profile"]:
        if _elem["name"] == customer+"-PostStaging":
          org_data[_elem["name"]] = {}
          org_data[_elem["name"]]["ike"] = {}
          org_data[_elem["name"]]["ike"]["group"] = _elem["ike"]["group"]
          org_data[_elem["name"]]["ike"]["transform"] = _elem["ike"]["transform"]
          org_data[_elem["name"]]["ipsec"] = {}
          org_data[_elem["name"]]["ipsec"]["transform"] = _elem["ipsec"]["transform"]

  if pyVer.major == 3:
    #auth = base64.b64encode(bytes('Administrator:Versa@1234'),"utf-8").decode('ascii')
    auth = base64.b64encode(bytes('%s:%s' % (str("Administrator"), str("Versa@1234")),"utf-8")).decode('ascii')
  else:
    auth = base64.encodestring('Administrator:Versa@1234' ).replace('\n', '')
  newdirdata= {'vd_ip' :  "192.168.236.2",
            'vd_rest_port': 9182,
            'auth': auth }
  vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method':_method , 'uri': _uri,
            'vd_ip' :  newdirdata['vd_ip'], 'vd_rest_port': newdirdata['vd_rest_port'],
            'auth': newdirdata['auth'] }
  [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)

  if len(resp_str) > 3:
    jstr = json.loads(resp_str)
    if "ipsec" in jstr:
      for _elem in jstr["ipsec"]["vpn-profile"]:
        if _elem["name"] == customer+"-PostStaging" and _elem["name"] in org_data: 
          if "ike" in _elem and _elem["ike"]["group"] == org_data[_elem["name"]]["ike"]["group"]:
            print("Matched IKE group {0}".format(_elem["ike"]["group"]))
          else:
            print("Did not match IKE group {0} {1}".format(_elem["ike"]["group"],org_data[_elem["name"]]["ike"]["group"]))
          if "ike" in _elem and _elem["ike"]["transform"] == org_data[_elem["name"]]["ike"]["transform"]:
            print("Matched IKE transform {0}".format(_elem["ike"]["transform"]))
          else:
            print("Did not match IKE transform {0} {1}".format(_elem["ike"]["transform"],org_data[_elem["name"]]["ike"]["transform"]))
          if "ipsec" in _elem and _elem["ipsec"]["transform"] == org_data[_elem["name"]]["ipsec"]["transform"]:
            print("Matched IPSEC transform {0}".format(_elem["ipsec"]["transform"]))
          else:
            print("Did not match IPSEC transform {0} {1}".format(_elem["ipsec"]["transform"],org_data[_elem["name"]]["ipsec"]["transform"]))
        else: 
          print("Did not match name {0}".format(_elem["name"]))
          
    print("JJ")

def get_org_deploy_worflow( _method, _uri, _payload,resp='200', vd_data=None,_ofile=None):
  global vnms, analy, cntlr, cust, admin, mlog
  print("In function " + get_org_data.__name__)
  resp2 = '202'
  vdict = {}
  vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method':_method , 'uri': _uri,
            'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
            'auth': vd_data['auth'] }
  [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)

  org_data = {}
  if len(resp_str) > 3:
    jstr = json.loads(resp_str)
    if "versanms.sdwan-org-workflow" in jstr:
      y = jstr["versanms.sdwan-org-workflow"]["orgName"]
      org_data[y] = {}
      for _elem in jstr["versanms.sdwan-org-workflow"]["vrfs"]:
        org_data[y][_elem["name"] ] = _elem["id"]
      print("JJ")

  if pyVer.major == 3:
    #auth = base64.b64encode(bytes('Administrator:Versa@1234'),"utf-8").decode('ascii')
    auth = base64.b64encode(bytes('%s:%s' % (str("Administrator"), str("Versa@1234")),"utf-8")).decode('ascii')
  else:
    auth = base64.encodestring('Administrator:Versa@1234' ).replace('\n', '')
  newdirdata= {'vd_ip' :  "192.168.236.2",
            'vd_rest_port': 9182,
            'auth': auth }
  vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method':_method , 'uri': _uri,
            'vd_ip' :  newdirdata['vd_ip'], 'vd_rest_port': newdirdata['vd_rest_port'],
            'auth': newdirdata['auth'] }
  [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)

  if len(resp_str) > 3:
    jstr = json.loads(resp_str)
    if "versanms.sdwan-org-workflow" in jstr:
      y = jstr["versanms.sdwan-org-workflow"]["orgName"]
      if y in org_data:
        for _elem in jstr["versanms.sdwan-org-workflow"]["vrfs"]:
          if ( _elem["name"] in org_data[y] and _elem["id"] == org_data[y][_elem["name"]]):
            print("matched {0}".format(_elem["name"]))
          else:
            print("did not matched {0}".format(_elem["name"]))


def get_org_data ( _method, _uri, _payload,resp='200', vd_data=None,_ofile=None):
  global vnms, analy, cntlr, cust, admin, mlog
  print("In function " + get_org_data.__name__)
  resp2 = '202'
  vdict = {}
  vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method':_method , 'uri': _uri,
            'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
            'auth': vd_data['auth'] }
  [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)

  org_data = {}
  if len(resp_str) > 3:
    jstr = json.loads(resp_str)
    if "organizations" in jstr:
      for _elem in jstr["organizations"]:
        a={}
        a['name'] = _elem["name"]
        a["globalOrgId"] = _elem["globalOrgId"]
        a["providerOrg"] = _elem["providerOrg"]
        org_data[_elem["name"] ] = {}
        org_data[_elem["name"] ] = a
      print("JJ")

  if pyVer.major == 3:
    auth = base64.b64encode(bytes('Administrator:Versa@1234'),"utf-8").decode('ascii')
  else:
    auth = base64.encodestring('Administrator:Versa@1234' ).replace('\n', '')
  newdirdata= {'vd_ip' :  "192.168.236.2",
            'vd_rest_port': 9182,
            'auth': auth }
  vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method':_method , 'uri': _uri,
            'vd_ip' :  newdirdata['vd_ip'], 'vd_rest_port': newdirdata['vd_rest_port'],
            'auth': newdirdata['auth'] }
  [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)

  if len(resp_str) > 3:
    jstr = json.loads(resp_str)
    if "organizations" in jstr:
      for _elem in jstr["organizations"]:
        if ( _elem["name"] in org_data and _elem["globalOrgId"] == org_data[_elem["name"]]["globalOrgId"] 
             and _elem["providerOrg"] == org_data[_elem["name"]]["providerOrg"]):
          print("matched {0}".format(_elem["name"]))
        else:
          print("did not matched {0}".format(_elem["name"]))

    


def get_dir_release_info ( _method, _uri, _payload,resp='200', vd_data=None,_ofile=None):
  global vnms, analy, cntlr, cust, admin, mlog
  print("In function " + get_dir_release_info.__name__)
  resp2 = '202'
  vdict = {}
  vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method':_method , 'uri': _uri,
            'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
            'auth': vd_data['auth'] }
  [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
  if len(resp_str) > 3:
    jstr = json.loads(resp_str)
    print("Release Info list = {0}".format(json.dumps(jstr,indent=4)))
    if "package-info" in jstr:
      if ("major-version" in jstr["package-info"][0] and "minor-version" in jstr["package-info"][0]
          and "service-version" in jstr["package-info"][0]):
        newstr =  jstr["package-info"][0]["major-version"] + "." \
                  + jstr["package-info"][0]["minor-version"] + "." \
                  + jstr["package-info"][0]["service-version"]
        print(newstr)
  return ''

def get_hub_cntlr_device_ipsec_vpn_profile( _method, _uri, _payload,resp='200',vd_data=None, device=None,_cntlr=2):
    global vnms, analy, cntlr, cust, mlog

    if device is None or vd_data is None :
      print("Bad inputs in function {0} ".format(get_device_ipsec_vpn_profile.__name__))
      return

    print("Modifying IPSEC VPN Profile details for device = {0} ".format(device))
    resp2 = '202'
    vdict = {}
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': _uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth']
    }
    [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json.loads(resp_str)
      newjstr = json.loads(resp_str)
      #mlog.info("IPSEC VPN Profile = {0}".format(json.dumps(jstr,indent=4)))
      scrub_list = [ "operations"]
      for i in scrub_list:
        scrub(jstr,i)

      # Delete the OlD VPN profile first
      """
      payload = {}
      vdict = {}
      uri =  _uri.rsplit('?',1)[0]
      uri =  uri + "/" + old_p_cntlr["name"] + "-Profile"
      vdict = {'body': payload, 'resp': resp, 'resp2': resp2, 'method': 'DELETE', 'uri': uri,
                  'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
                   'auth': vd_data['auth']
      }
      mlog.info("Sending DELETE from function {0}".format(get_device_ipsec_vpn_profile.__name__))
      [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
      # END OF DELETE    
      """
      found = 0
      vpn_profile = []
      vpn_data = []
      if "vpn-profile" in jstr: 
        #south_ip = glbl.vnms.data['director'][0]['director_southIP'] + "/32" 
        south_ip = "192.168.236.145" + "/32" 
        for vpn in jstr["vpn-profile"] :
          #if vpn["name"] == (old_p_cntlr["name"] + "-Profile"):
          if vpn["vpn-type"] == "controller-staging-sdwan":
            vpn_profile.append(vpn['name']) 
            found = found + 1
            if "address-pools" in vpn and "accessible-subnets" in vpn["address-pools"]:
              for elem in vpn["address-pools"]["accessible-subnets"]:
                if elem["subnet"][0:2] != "10":
                  elem["subnet"] = south_ip
              newjstr = {}
              newjstr["vpn-profile"] = copy.deepcopy(vpn)
              vpn_data.append(newjstr)

      for i in range(len(vpn_data)):
        #mlog.info("IPSEC VPN Profile after Deletion = {0}".format(json.dumps(jstr,indent=4)))
        payload = json.dumps(vpn_data[i])
        vdict = {}
        uri =  _uri.rsplit('?',1)[0] + "/" + vpn_profile[i]
        vdict = {'body': payload, 'resp': resp, 'resp2': resp2, 'method': 'PUT', 'uri': uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth']
        }
        print("Sending PUT from function {0} for VPN Profile={1}".format(get_hub_cntlr_device_ipsec_vpn_profile.__name__,vpn_profile[i]))
        [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)

        if len(resp_str) > 3:
          jstr = json.loads(resp_str)
          print("IPSEC VPN Profile after PUT = {0}".format(json.dumps(jstr,indent=4)))
    else : 
      print("Not Sending PUT from function {0}".format(get_hub_cntlr_device_ipsec_vpn_profile.__name__))
    return ''
    

def get_backup( _method, _uri,_payload,resp='200',vd_data=None):
    resp2='202'
    vdict = {}
    #vdict = {'body': _payload, 'resp': resp, 'method': _method, 'uri': _uri}
    uri = "/api/config/system/_operations/recovery/list"
    payload = {}
    vdict1 = {'body': payload, 'resp': resp, 'resp2': resp2, 'method': "POST", 'uri': uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth']
    }
    [out, resp_str] = call(vdict1,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3 :
      recoverylist1 = json.loads(resp_str)
      if "output" in recoverylist1 and "files" in recoverylist1["output"]:
        file1 = recoverylist1["output"]["files"]
        # Now call the backup Api
        vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method':_method , 'uri': _uri,
                  'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
                   'auth': vd_data['auth']
        }
        [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
        if len(resp_str) > 3 :
          backup = json.loads(resp_str)
          if "output" in  backup and "status" in backup["output"] and (backup["output"]["status"].find("initiated") != -1):
            for i in range(0,5):
              time.sleep(10)
              [out, resp_str] = call(vdict1,content_type='json',ncs_cmd="no",jsonflag=1)
              if len(resp_str) > 3 :
                recoverylist2 = json.loads(resp_str)
                if "output" in recoverylist2 and "files" in recoverylist2["output"]:
                  file2 = recoverylist2["output"]["files"]
                  if len(file2) > len (file1):
                    print("Found")
                    print (file2 - file1)
                    break
def get_wan_ntwk( _method, _uri, _payload,resp='200', vd_data=None,_ofile=None):
    global vnms, analy, cntlr, cust, mlog
    resp2 = '202'
    vdict = {}
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method':_method , 'uri': _uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth'] }
    print("In function {0} with outfile={1}".format(get_wan_ntwk.__name__,_ofile))
    [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json.loads(resp_str)
      mywan = {}
      for i in jstr:
        if "name" in i:
          mywan[i["name"]] = i["transport-domains"][0]
     
      pprint(mywan)
    else:
      print("Could not get Wan Ntwk")
    return

def enable_ha( _method, _uri, _payload,resp='200', vd_data=None, _ofile=None):
    global vnms, analy, cntlr, cust
    resp2='202'
    vdict = {}
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method':_method , 'uri': _uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth'] }
    [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    jstr = json.loads(resp_str)
    print(resp_str)
    return

def get_controller_tvi ( _method, _uri, _payload,resp='200', vd_data=None, _ofile=None):
    global vnms, analy, cntlr, cust
    resp2='202'
    vdict = {}
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method':_method , 'uri': _uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth'] }
    [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    jstr = json.loads(resp_str)
    a=[]
    for i in range(0,len(jstr["tvi"])):
      if (jstr["tvi"][i]["name"] == "tvi-0/2" or jstr["tvi"][i]["name"] == "tvi-0/3"):
        if "mode" in jstr["tvi"][i] and "type" in jstr["tvi"][i]:
          if jstr["tvi"][i]["type"] == "p2mp-esp":
            myname = jstr["tvi"][i]["name"]
            myip = jstr["tvi"][i]["unit"][0]["family"]["inet"]["address"][0]["addr"]
            myip = myip.split("/")[0]
            print("tvi_p2mp_esp has ip ={0} for name={1}".format(myip,myname))
          elif jstr["tvi"][i]["type"] == "p2mp-vxlan":
            myname = jstr["tvi"][i]["name"]
            myip = jstr["tvi"][i]["unit"][0]["family"]["inet"]["address"][0]["addr"]
            myip = myip.split("/")[0]
            print("tvi_p2mp_vxlan has ip ={0} for name={1}".format(myip,myname))
          #cntlr.data[0]['tvi'] = b
    return

def save_config_snapshot ( _method, _uri, _payload,resp='200', vd_data=None, _ofile=None):
    resp2 = '202'
    vdict = {}
    deviceName = "SevOne-TestBranch-2"
    configSnapshotName = "test1"
    _uri = _uri + configSnapshotName  + "/device/" + deviceName 
    _payload = {}
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method':"POST" , 'uri': _uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth'] }
    [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json.loads(resp_str)
      if "response-code" in jstr and "response-type" in jstr and jstr["response-type"] == "success":
        print("SUCCESS")
      else: 
        print("Failure")

def get_lef_status( _method, _uri, _payload,resp='200', vd_data=None, _ofile=None):
    resp2 = '202'
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method':_method , 'uri': _uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth'] }
    [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json.loads(resp_str)
      if "lef:collectors" in jstr and "collector" in jstr["lef:collectors"]:
        found = 0
        count = 0
        for elem in  jstr["lef:collectors"]["collector"] :
          if "status" in elem:
            for subelem in elem["status"]:
              if "status" in  subelem:
                count = count + 1
                if subelem["status"]  == "Established":
                  found = found + 1
        if found == count :
          print("LEF status is up ")
        else: 
          print("LEF status is not up ")
      else:
        print("LEF status is not up ")

def get_controller_status( _method, _uri, _payload,resp='200', vd_data=None, _ofile=None):
    resp2 = '202'
    vdict = {}
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method':_method , 'uri': _uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth'] }
    [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json.loads(resp_str)
      if "sdwan:status" in jstr and "path-status" in jstr["sdwan:status"]:
        for elem in  jstr["sdwan:status"]["path-status"]:
          if elem["conn-state"] == "up":
            print("SLA status to Controller is up ")
          else: 
            print("SLA status to Controller is not up ")
      else:
        print("SLA status to Controller is not up ")

def get_bgp_status( _method, _uri, _payload,resp='200', vd_data=None, _ofile=None):
    resp2 = '202'
    vdict = {}
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method':_method , 'uri': _uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth'] }
    [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json.loads(resp_str)
      if "routing-module:brief" in jstr and "neighbor-ip" in jstr["routing-module:brief"]:
        count =0;
        found =0
        for elem in jstr["routing-module:brief"]["neighbor-ip"]:
          count = count + 1 
          if elem["state"] == "Established": found = found + 1
        if count == found:
          print("Bgp connectivity to Device looks good")
        else: 
          print("Bgp connectivity to Device DOES NOT look good")
      else: 
        print("Did not find proper response ")


def get_controller_org_services( _method, _uri, _payload,resp='200', vd_data=None, _ofile=None):
    global vnms, analy, cntlr, cust, mlog
    #mlog.info("In function {0} with outfile={1}".format(get_controller_org_services.__name__,_ofile))
    resp2 = '202'
    vdict = {}
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method':_method , 'uri': _uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth'] }
    [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json.loads(resp_str)
      scrub_list = [ "device-id", "dynamic-address", "persistent-action" "pac", "user-identification", "objects", 
                      "keytab", "live-users", "operations" ]
      for i in scrub_list:
        scrub(jstr,i)

      newjstr = {}
      if "org-services" in jstr:
         for i in range(len(jstr["org-services"])):
             if i == 0 : newjstr["org-services"] = [None]*len(jstr["org-services"])
             newjstr["org-services"][i] = {}
             for _key,_val in jstr["org-services"][i].items():
                if _key == "adc":
                   newjstr["org-services"][i]["adc:adc"] = _val
                   print("adc info changed in org-services data in function {0}".format(get_controller_org_services.__name__))
                elif _key == "application-identification":
                   newjstr["org-services"][i]["appid:application-identification"] = _val
                   print("appid info changed in org-services data in function {0}".format(get_controller_org_services.__name__))
                elif _key == "crypto":
                   newjstr["org-services"][i]["crypto:crypto"] = _val
                   print("crypto info changed in org-services data in function {0}".format(get_controller_org_services.__name__))
                elif _key == "ipsec":
                   newjstr["org-services"][i]["ipsec:ipsec"] = _val
                   print("ipsec info changed in org-services data in function {0}".format(get_controller_org_services.__name__))
                elif _key == "pbf":
                   newjstr["org-services"][i]["pbf:pbf"] = _val
                   print("lef info changed in org-services data in function {0}".format(get_controller_org_services.__name__))
                elif _key == "lef":
                   newjstr["org-services"][i]["lef:lef"] = _val
                   print("lef info changed in org-services data in function {0}".format(get_controller_org_services.__name__))
                elif _key == "security":
                   newjstr["org-services"][i]["security:security"] = _val
                   print("security info changed in org-services data in function {0}".format(get_controller_org_services.__name__))
                elif _key == "traffic-monitoring":
                   newjstr["org-services"][i]["traffic-monitoring:traffic-monitoring"] = _val
                   print("security info changed in org-services data in function {0}".format(get_controller_org_services.__name__))
                elif _key == "url-filtering":
                   newjstr["org-services"][i]["url-filtering:url-filtering"] = _val
                   print("security info changed in org-services data in function {0}".format(get_controller_org_services.__name__))
                else: 
                   newjstr["org-services"][i][_key] = _val
      if _ofile is None: 
         print("No file provided .. exiting")
         sys.exit("No file provided .. exiting")
      _str = '/api/config/devices/device/' + "ControllerName" + '/config/orgs/org-services'
      out = create_out_data("PATCH","200",_str,newjstr)
      fp=open(_ofile,"w+")
      out1 = json.dumps(out, indent=4)
      fp.write(out1)
      fp.close()
    else:
      print("Did not find proper org-services data in function {0}".format(get_controller_org_services.__name__))
      sys.exit("Did not find proper org-services data in function {0}".format(get_controller_org_services.__name__))
    return ''

def create_out_data(_method,_resp,_uri,_str): 
    _out = OrderedDict()
    _out["method"] = _method
    _out["response"] = _resp
    _out["path"]   = _uri
    _out["payload"] = _str
    return _out

def create_dns_config( _method, _uri,_payload,resp='200',vd_data=None):
    resp2='202'
    vdict = {}
    #vdict = {'body': _payload, 'resp': resp, 'method': _method, 'uri': _uri}
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method':_method , 'uri': _uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth'] }
    [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3 :
      x = None
      jstr = json.loads(resp_str)
      print(json.dumps(jstr,indent=4))

    return ''

def main():
    global vnms, analy, cntlr, cust, admin, auth, debug
    global in_ip, in_port, in_user, in_pswd
    #mdict = readfile("in_rest.cfg")
    argcheck()
    debug = int(args['debug'])
    infile = args['file']
    in_ip = args['ip']
    in_port = args['port'] 
    in_user = args['user']
    in_pswd = args['pswd']

    if pyVer.major == 3:
      auth = base64.b64encode(bytes('%s:%s' % (str(in_user), str(in_pswd)),"utf-8")).decode('ascii')
    else:
      auth = base64.encodestring('%s:%s' % (in_user, in_pswd)).replace('\n', '')

    #pprint(mdict) 
    dirdata= {'vd_ip' :  in_ip,
            'vd_rest_port': in_port,
            'auth': auth
    }
    


    template_path = os.path.abspath(sys.argv[0]).rsplit("/",1)[0] 
    template_loader = jinja2.FileSystemLoader(searchpath=template_path)
    template_env = jinja2.Environment(loader=template_loader,undefined=jinja2.StrictUndefined)
    template_env.filters['jsonify'] = json.dumps

    my_template = template_env.get_template(infile)
    #x= my_template.render( directorHostName = "wbuatcc-ffdca1-2988005e003")
    #x= my_template.render( south_ip = "172.16.10.164", num=3)
    #x= my_template.render( deviceName = "HC2")
    #x= my_template.render( deviceName = "HC2")
    searchip = ["192.168.236.23", "192.168.236.22" ]
    analyip = ["192.168.236.21", "192.168.236.20" ]
    allip = ["192.168.236.20", "192.168.236.21", "192.168.236.22", "192.168.236.23", "192.168.236.24"]
    #x= my_template.render( custName="Customer1")
    x= my_template.render( controller1Name="Versa-Controller-1",custName="Customer1")
    y= json.loads(x)
    #create_dns_config(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']),vd_data=dirdata)
    #get_backup(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']),vd_data=dirdata)
    #get_wan_ntwk( str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']),vd_data=dirdata, _ofile=None)
    #get_controller_org_services(  str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']), vd_data=dirdata, _ofile="abcd")
    #get_bgp_status(  str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']), vd_data=dirdata, _ofile="abcd")
    #get_controller_status(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']), vd_data=dirdata, _ofile="abcd")
    #get_lef_status(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']), vd_data=dirdata, _ofile="abcd")
    #save_config_snapshot(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']), vd_data=dirdata, _ofile="abcd")
    #get_controller_tvi (str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']), vd_data=dirdata, _ofile="abcd")
    #enable_ha( str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']), vd_data=dirdata, _ofile="abcd")
    #analytics_call( str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
    #get_hub_cntlr_device_ipsec_vpn_profile( str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']), vd_data=dirdata, device="HC2", _cntlr=2)
    #get_dir_release_info ( str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']), vd_data=dirdata, _ofile="abcd")
    #get_org_data ( str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']), vd_data=dirdata, _ofile="abcd")
    #get_org_deploy_worflow( str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']), vd_data=dirdata, _ofile="abcd")
    get_cntlr_org_services( str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']), vd_data=dirdata, _ofile="abcd")

    print("==============Completed==============")

if __name__ == "__main__":
    #global debug
    print(debug)
    main()


