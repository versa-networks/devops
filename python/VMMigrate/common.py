#!/usr/bin/env python2
#si sw=2 sts=2 et
import glbl 
import requests
import xmltodict
import json
import time
import sys
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from collections import OrderedDict


pyVer = sys.version_info
if pyVer.major == 3:
  import ssl
  import http.client as httplib 
else:
  import ssl
  import httplib


def json_loads(_str,**kwargs):
    global mlog
    try:
      _jstr = json.loads(_str,**kwargs)
      return _jstr
    except Exception as ex:
       mlog.error('Json load failed: {}'.format(ex))
       sys.exit('Json load failed: {}'.format(ex))

# Function to call the RestAPIs
def call(api_dict, auth_type='Basic', content_type="xml", ncs_cmd="yes", max_retry_for_task_completion=30, jsonflag=0,initialwait=0):
    global debug, admin, mlog
    auth = glbl.admin.data['new_dir']['auth']
    ret_true = [1, ""]
    ret_false = [0, ""]
    #glbl.mlog.info("In function " + call.__name__)
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
          if pyVer.major == 3:
            webservice = httplib.HTTPSConnection(glbl.admin.data['new_dir']['vd_ip'], int(glbl.admin.data['new_dir']['vd_rest_port']),context=ssl._create_unverified_context())
          else: 
            webservice = httplib.HTTPSConnection(glbl.admin.data['new_dir']['vd_ip'], int(glbl.admin.data['new_dir']['vd_rest_port']))
          webservice.request(api_dict['method'], api_dict['uri'],
                           api_dict['body'], headers)
          break
        except:
          att = att + 1
          glbl.mlog.info("Attempt %s " % (str(att)))

      resp_obj = webservice.getresponse()
      if pyVer.major == 3:
        resp_string = (resp_obj.read()).decode(encoding='utf-8',errors="ignore")
      else: 
        resp_string = (resp_obj.read()).decode('utf-8')
        #resp_string = str(resp_obj.read())
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
          glbl.mlog.error("Did not receive expected Response Code: Expected %s Got %s with Reason: %s for Uri=%s"
                  % (api_dict['resp'], resp_code,resp_string,api_dict['uri']))
        else:
          glbl.mlog.error("Did not receive expected Response Code: Expected %s Got %s with Reason: %s for Uri=%s"
                  % (api_dict['resp'], resp_code,resp_string,api_dict['uri']))
          #print("-" * 10)
          #return ret_false
        return [0, resp_string]
      else:
        if 'task-id' in resp_string:
          # Task is created, we need to poll
          task_id = _get_task_id(resp_string)
          if not task_id:
            return ret_false
          retval = _task_poll(task_id, max_retry=max_retry_for_task_completion,initialwait=initialwait)
          if retval == True: return ret_true
          else: return ret_false 
          if api_dict['method'] == 'GET':
            return [1, resp_string]
        return [1, resp_string]
    except Exception as ex:
      #print("ERROR, Exception @ REST-Api CALL = %s for URI %s : Error: %s" %(api_dict['method'], api_dict['uri'], str(ex)))
      glbl.mlog.error("ERROR, Exception @ REST-Api CALL = %s for URI %s : Error: %s" %(api_dict['method'], api_dict['uri'], str(ex)))

def _task_poll( task_id, max_retry=5, sleep_interval=5,initialwait=0):
    global debug, mlog
    api_dict = {}
    api_dict['method'] = 'GET'
    #api_dict['uri'] = '/api/operational/tasks/task/%s'%task_id
    api_dict['uri'] = '/vnms/tasks/task/%s'%task_id
    api_dict['body'] = ''
    api_dict['resp'] = '200'
    timeout = 1
    count = 1
    jstr = {}
    if initialwait > 0 : time.sleep(initialwait)
    while timeout and count <= max_retry :
      [ret,task_progress] = call(api_dict,content_type="json",ncs_cmd="no")
      if not task_progress:
        glbl.mlog.info("Failed to GET Progress for Task: %s"%task_id)
        return False
        #completion = task_progress[1]
      completion = task_progress
      jstr = json_loads(completion)
      #cdict = xmltodict.parse(completion)
      #if int(cdict['task']['percentage-completion']) == 100:
      #    timeout = 0
      #print('Polling Status: %s:  Task %s : Completion: %s' \
      #        %(count, task_id, cdict['task']['percentage-completion']))
      if int(jstr["versa-tasks.task"]["versa-tasks.percentage-completion"]) == 100:
        timeout = 0
      #print('Polling Status: %s:  Task %s : Completion: %s' \
      #        %(count, task_id, jstr["versa-tasks.task"]["versa-tasks.percentage-completion"]))
      glbl.mlog.info('Polling Status: %s:  Task %s : Completion: %s' \
                %(count, task_id, jstr["versa-tasks.task"]["versa-tasks.percentage-completion"]))

      time.sleep(sleep_interval)
      count += 1
    if not timeout and jstr["versa-tasks.task"]["versa-tasks.task-status"] != 'FAILED':
      return True

    glbl.mlog.error(' Task %s failed after Count : %s' %(task_id, count))
    return False

def _task_poll_new( task_id, vdict, max_retry=5, sleep_interval=5,initialwait=0):
    global debug, mlog
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
    if initialwait > 0 : time.sleep(initialwait)
    while timeout and count <= max_retry :
      [ret,task_progress] = newcall(api_dict,content_type="json",ncs_cmd="no")
      if not task_progress:
        glbl.mlog.info("Failed to GET Progress for Task: %s"%task_id)
        return False
      #completion = task_progress[1]
      completion = task_progress
      jstr = json_loads(completion)
      #cdict = xmltodict.parse(completion)
      #if int(cdict['task']['percentage-completion']) == 100:
      #    timeout = 0
      #print('Polling Status: %s:  Task %s : Completion: %s' \
      #        %(count, task_id, cdict['task']['percentage-completion']))
      if int(jstr["versa-tasks.task"]["versa-tasks.percentage-completion"]) == 100:
        timeout = 0
      #print('Polling Status: %s:  Task %s : Completion: %s' \
      #        %(count, task_id, jstr["versa-tasks.task"]["versa-tasks.percentage-completion"]))
      glbl.mlog.info('Polling Status: %s:  Task %s : Completion: %s' \
          %(count, task_id, jstr["versa-tasks.task"]["versa-tasks.percentage-completion"]))

      time.sleep(sleep_interval)
      count += 1
    if not timeout and jstr["versa-tasks.task"]["versa-tasks.task-status"] != 'FAILED':
      return True

    glbl.mlog.error(' Task %s failed after Count : %s' %(task_id, count))
    return False

def _get_task_id( string):
    try:
      jstr=json_loads (string)
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

def check_controller_status(name="Controller",resp='200'):
    global mlog
    body = ''
    glbl.mlog.info("In function " + check_controller_status.__name__)
    uri = "/nextgen/appliance/status/"+ name + "?byName=true"
    #resp = '200'
    method = 'GET'
    vdict = {}
    vdict = {'body': body, 'resp': resp, 'method': method, 'uri': uri}
    [status,resp_str] = call(vdict, content_type="json", ncs_cmd="no")
    if glbl.debug : print('Controller : %s Resp Str: %s'%(status,resp_str))
    return [status,resp_str]


def create_out_data(_method,_resp,_uri,_str): 
    _out = OrderedDict()
    _out["method"] = _method
    _out["response"] = _resp
    _out["path"]   = _uri
    _out["payload"] = _str
    return _out

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


# Function to call the RestAPIs
# The ONLY difference between newcall and call is that it uses
# api_dict for the IP address and port while call uses global data
def newcall(api_dict, auth_type='Basic', content_type="xml", ncs_cmd="yes", max_retry_for_task_completion=30, jsonflag=0,initialwait=0):
    global debug, admin, mlog
    auth = api_dict['auth']
    ret_true = [1, ""]
    ret_false = [0, ""]
    #glbl.mlog.info("In function " + call.__name__)
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
          if pyVer.major == 3:
            webservice = httplib.HTTPSConnection(api_dict['vd_ip'], int(api_dict['vd_rest_port']),context=ssl._create_unverified_context())
          else: 
            webservice = httplib.HTTPSConnection(api_dict['vd_ip'], int(api_dict['vd_rest_port']))
          webservice.request(api_dict['method'], api_dict['uri'],
                           api_dict['body'], headers)
          break
        except:
          att = att + 1
          glbl.mlog.info("Attempt %s " % (str(att)))

      resp_obj = webservice.getresponse()
      if pyVer.major == 3:
        resp_string = (resp_obj.read()).decode(encoding='utf-8',errors="ignore")
      else: 
        resp_string = (resp_obj.read()).decode('utf-8')
        #resp_string = str(resp_obj.read())
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
          glbl.mlog.error("Did not receive expected Response Code: Expected %s Got %s with Reason: %s for Uri=%s"
                  % (api_dict['resp'], resp_code,resp_string,api_dict['uri']))
        else:
          glbl.mlog.error("Did not receive expected Response Code: Expected %s Got %s with Reason: %s for Uri=%s"
                  % (api_dict['resp'], resp_code,resp_string,api_dict['uri']))
        #print("-" * 10)
        return ret_false
      else:
        if 'task-id' in resp_string:
          # Task is created, we need to poll
          task_id = _get_task_id(resp_string)
          if not task_id:
            return ret_false
          retval = _task_poll_new(task_id,api_dict, max_retry=max_retry_for_task_completion,initialwait=initialwait)
          if retval == True: return ret_true
          else: return ret_false 
        if api_dict['method'] == 'GET':
          return [1, resp_string]
        return [1, resp_string]
    except Exception as ex:
      glbl.mlog.error("ERROR, Exception @ REST-Api CALL = %s for URI %s : Error: %s" %(api_dict['method'], api_dict['uri'], str(ex)))
