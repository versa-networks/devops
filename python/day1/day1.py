#!/usr/bin/env python2

import os, sys, signal, argparse

import jinja2
from jinja2.utils import concat
import re
import requests
import time
import base64
import xmltodict
import subprocess
import ssl
import json
from pprint import pprint
from collections import OrderedDict, Counter
import uuid
from pprint import pprint
import logging
import logging.handlers

pyVer = sys.version_info
if pyVer.major == 3:
  import http.client as httplib
else:
  import httplib

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

#import vnms
vnms =  None
analy = None 
cntlr = None
cust = None
admin = None
debug = 0
log = None
curr_task_id = None

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


class Vnms:
  def __init__(self, _vdict):
    self.data = _vdict

class Analytics:
  def __init__(self, _vdict):
    self.data = _vdict

class Controller:
  def __init__(self, _vdict):
    self.data = _vdict

class Customer:
  def __init__(self, _vdict):
    self.data = _vdict

class Admin:
  def __init__(self, _vdict):
    self.data = _vdict

def argcheck():
    """ This performs adds the  argument and checks the requisite inputs
    """
    global args
    mystr = os.path.basename(sys.argv[0])
    parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]),description='%(prog)s Help:',usage='%(prog)s -f filename [options]', add_help=False)
    parser.add_argument('-f','--file',required=True, help='input file [required ]' )
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
      %(mystr)s --f/-f <infile>
    To add more debug:
      %(mystr)s -f <infile> --debug/-d [0/1]
  """ %locals())
    print(bcolors.ENDC)

def json_loads(_str,**kwargs):
    global log
    try:
      _jstr = json.loads(_str,**kwargs)
      return _jstr
    except Exception as ex:
       log.error('Json load failed: {}'.format(ex))
       sys.exit('Json load failed: {}'.format(ex))


def analycall(api_dict):
    global debug, admin, log
    prefix_uri = "https://{0}:{1}/versa/".format(api_dict['ip'],admin.data['analy_rest_port1'])
    prefix_uri1 = "https://{0}:{1}".format(api_dict['ip'],admin.data['analy_rest_port1'])
    sess = requests.session()
    url = "{0}login?username={1}&password={2}".format(prefix_uri,admin.data['analy_user'],admin.data['analy_password'])
    try: 
      res = sess.post(url, verify=False,timeout=5)
    except requests.Timeout:
      sess.close()
      return [False, "Timeout" , ""]
    except requests.ConnectionError:
      sess.close()
      return [False, "Connection Error" , ""]

    resp_code = res.status_code
    if res and res.ok:
      tkn =res.headers['x-csrf-token']
    else: 
      log.error("Failed to login to Analytics")
      sess.close()
      return [False, resp_code, res.text]
    url = "{0}{1}".format(prefix_uri1,api_dict['uri'])
    headers = {'Content-type': 'application/json','Accept': 'text/plain','x-csrf-token': tkn} 
    try:
      res = sess.post(url,data=api_dict['body'],headers=headers, timeout = 5)
    except requests.Timeout:
      sess.close()
      return [False, "Timeout" , ""]
    except requests.ConnectionError:
      sess.close()
      return [False, "Connection Error" , ""]

    resp_code = res.status_code
    if res and res.ok:
      sess.close()
      return [True, resp_code, res.text]
    else: 
      log.error("Failed Rest API to Analytics: {0}".format(res.text))
      sess.close()
      return [False, resp_code, res.text]
    return [False, 0, ""]

# Function to call the RestAPIs
def call(api_dict, auth_type='Basic', content_type="xml", ncs_cmd="yes", max_retry_for_task_completion=30, jsonflag=0,initialwait=0):
    global debug, admin, log, curr_task_id
    auth = admin.data['auth']
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
          if pyVer.major == 3:
            webservice = httplib.HTTPSConnection(admin.data['vd_ip'], int(admin.data['vd_rest_port']),context=ssl._create_unverified_context())
          else: 
            webservice = httplib.HTTPSConnection(admin.data['vd_ip'], int(admin.data['vd_rest_port']))

          webservice.request(api_dict['method'], api_dict['uri'],
                           api_dict['body'], headers)
          break
        except:
          att = att + 1
          log.error("Attempt : %s" % (str(att)))

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
          if debug:
            log.error(
                  "Did not recieve expected Response Code: Expected %s Got %s with Reason: %s"
                  % (api_dict['resp'], resp_code,resp_string))
          else:
            log.error(
                  "Did not recieve expected Response Code: Expected %s Got %s"
                  % (api_dict['resp'], resp_code))
        else:
          if debug:
            log.error(
                  "Did not recieve expected Response Code: Expected %s Got %s ; \nResponse String: %s"
                  % (api_dict['resp'], resp_code, resp_string))
          else:
            log.error(
                  "Did not recieve expected Response Code: Expected %s Got %s ; \n"
                  % (api_dict['resp'], resp_code))
        #print("-" * 10)
        return [0, resp_string]
      else:
        if 'task-id' in resp_string:
          # Task is created, we need to poll
          task_id = _get_task_id(resp_string)
          curr_task_id = task_id
          if not task_id: return ret_false
          retval, stat = _task_poll(task_id,
                                  max_retry=max_retry_for_task_completion,initialwait=initialwait)
          if retval == True: 
            curr_task_id = None
            return ret_true
          else: return ret_false 
          if api_dict['method'] == 'GET':
            return [1, resp_string]
        return [1, resp_string]
    except Exception as ex:
      log.error("ERROR, Exception @ REST-Api CALL = %s for URI %s : Error: %s" %(api_dict['method'], api_dict['uri'], str(ex)))
      return ret_false

def _task_poll( task_id, max_retry=5, sleep_interval=5,initialwait=0):
    global log
    api_dict = {}
    api_dict['method'] = 'GET'
    api_dict['uri'] = '/vnms/tasks/task/%s'%task_id
    api_dict['body'] = ''
    api_dict['resp'] = '200'
    timeout = 1
    count = 1
    retrycntmax = 5
    retrycnt = 0
    jstr = {}
    task_progress = ""
    if initialwait > 0 : time.sleep(initialwait)
    while timeout and count <= max_retry :
      [ret,task_progress] = call(api_dict,content_type="json",ncs_cmd="no")
      found = 0
      # check the task progress
      if len(task_progress) > 3:
        try:
          jstr = json_loads(task_progress)
          if ("versa-tasks.task" in jstr and "versa-tasks.percentage-completion" in jstr["versa-tasks.task"]): 
            found = 1
            if int(jstr["versa-tasks.task"]["versa-tasks.percentage-completion"]) == 100:
              log.warn('Polling Status: %s:  Task %s : Completion: %s' \
                %(count, task_id, jstr["versa-tasks.task"]["versa-tasks.percentage-completion"]))
              timeout = 0
            elif jstr["versa-tasks.task"]["versa-tasks.task-status"] == 'FAILED':
              timeout = 0
            else: 
              log.warn('Polling Status: %s:  Task %s : Completion: %s' \
                %(count, task_id, jstr["versa-tasks.task"]["versa-tasks.percentage-completion"]))
          else:  # so we did not get task completion
            log.warn('Task: %s Resp string: %s Count: %d RetyCnt: %d' \
                %(task_id,task_progess,count, retrycnt)) 
            if retrycnt >= retrycntmax: 
              break
            else:
              retrycnt = retrycnt + 1
              pass
        except:
          found = 0
          pass
      time.sleep(sleep_interval)
      count += 1

    # We are outside the while loop now
    if found == 1:
      if jstr["versa-tasks.task"]["versa-tasks.task-status"] != 'FAILED': 
        return True, "PASS"
      elif jstr["versa-tasks.task"]["versa-tasks.task-status"] == 'FAILED':
        log.error('Task Failed: %s  Resp string: %s  Count %d RetyCntr %d' \
                    %(task_id, task_progess,count, retrycnt)) 
        #log.error("Return False FAIL")
        return False, "FAIL"
    return False, "FAIL"

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


# Not needed any more
def create_overlay():
    payload = '''{
         "overlay-address-scheme": { 
               "ipv4-prefix": "172.17.0.0/16",
               "donot-encode-organization-id": false,
               "maximum-organizations": "32"
    }}'''
    uri = "/api/config/nms/sdwan/overlay-address-scheme"
    resp = '201'
    body = payload
    vdict = {}
    vdict = {'body': body, 'resp': resp, 'method': 'PUT', 'uri': uri}
    [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    return

def enable_ha( _method, _uri, _payload,resp='200'):
    vdict = {'body': _payload, 'resp': resp, 'method': _method, 'uri': _uri}
    [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no",max_retry_for_task_completion=500, jsonflag=1, initialwait=30)
    return

def onboard_provider_org( _method, _uri, _payload,resp='200'):
    vdict = {}
    vdict = {'body': _payload, 'resp': resp, 'method': _method, 'uri': _uri}
    [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    return

def create_controller( _method, _uri,_payload,resp='200',name="Controller"):
    resp = '200'
    log.warn(bcolors.OKWARN + "Have you performed an erase config on the controller: {0} and verified that services are running.\nIf not do so now".format(name) + bcolors.ENDC)
    if yes_or_no("Continue: "):
      vdict = {'body': _payload, 'resp': resp, 'method': _method, 'uri': _uri}
      [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
      if status == 1:
        log.warn("Creation of New Controller={0} successful".format(name))
        if len (resp_str) > 3 :
          newjstr = json_loads(resp_str)
          log.info("Return json from POST on Controller: {0} = {1}".format(name,json.dumps(newjstr,indent=4)))
        else:
          log.error("Creation of New Controller={0} NOT successful".format(name))
          log.warn(bcolors.OKWARN+"We can not proceed without the Controller Create." +
              'You can fix the error and then refresh (type r) to try the creation again.' +
              "Typing a n (No)  will exit the program. Typing a y (Yes) will continue" + bcolors.ENDC)
          ret = yes_or_no2(bcolors.OKWARN+"To Refresh press r, to Continue press y and to Exit press n: "+ bcolors.ENDC,1)
          if ret == 0 : sys.exit("Creation of New Controller = {0} NOT sucessful ".format(name))
          elif ret == 1: pass
          else:
            create_controller( _method, _uri,_payload,resp=resp, name=name)
      else: 
        log.error("Bad Status returned for Controller={0}".format(name))
    return

def get_controller_tvi( _method, _uri,_payload,resp='200',_cntlr_id=None):
    global vnms, analy, cntlr, cust, admin, log
    resp2='202'
    vdict = {'body': _payload, 'resp': resp, 'method': _method, 'uri': _uri}
    [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if out == 1 and len(resp_str) > 3:
      jstr = json_loads(resp_str)
      a=[]
      for i in range(0,len(jstr["tvi"])):
        if (jstr["tvi"][i]["name"] == "tvi-0/2" or jstr["tvi"][i]["name"] == "tvi-0/3"):
          if "mode" in jstr["tvi"][i] and "type" in jstr["tvi"][i]:
            if jstr["tvi"][i]["type"] == "p2mp-esp":
              myname = jstr["tvi"][i]["name"]
              myip = jstr["tvi"][i]["unit"][0]["family"]["inet"]["address"][0]["addr"]
              myip = myip.split("/")[0]
              log.warn("tvi_p2mp_esp has ip ={0} for name={1}".format(myip,myname))
              cntlr.data[_cntlr_id]['tvi_esp'] = myip
            elif jstr["tvi"][i]["type"] == "p2mp-vxlan":
              myname = jstr["tvi"][i]["name"]
              myip = jstr["tvi"][i]["unit"][0]["family"]["inet"]["address"][0]["addr"]
              myip = myip.split("/")[0]
              log.warn("tvi_p2mp_vxlan has ip ={0} for name={1}".format(myip,myname))
              cntlr.data[_cntlr_id]['tvi_vxlan'] = myip
            #cntlr.data[0]['tvi'] = b
            write_outfile(vnms,analy,cntlr,cust, admin)
    else: 
       log.error("Did not receive proper response. Status=%d"%(out)) 
    return

def check_controller_status(name="Controller"):
    global log
    body = ''
    uri = "/nextgen/appliance/status/"+ name + "?byName=true"
    resp = '200'
    method = 'GET'
    vdict = {'body': body, 'resp': resp, 'method': method, 'uri': uri}
    [out,resp_str] = call(vdict, content_type="json", ncs_cmd="no")
    if out == 1 and len(resp_str) > 3:
      log.info('Controller : %d Resp Str: %s'%(out,resp_str))
    else: 
       log.error("Did not receive proper response. Status=%d"%(out)) 
    return [out,resp_str]


def deploy_controller( _method, _uri,_payload,resp='202',name="Controller"):
    global vnms, analy, cntlr, cust
    vdict = {'body': _payload, 'resp': resp, 'method': _method, 'uri': _uri}
    [out,resp_str] = call(vdict, content_type="json", ncs_cmd="no")
    # Now we need to check the status
    #check_controller_status(name=name)
    if out == 1: 
      log.warn("Deploy of Controller={0} succeeded. Check Controller Sync Status. Please be patient".format(name))
      for i in range(0,5):
        time.sleep(5)
        [out,resp_str] = check_controller_status(name=name)
        if out == 1 and len(resp_str) > 3:
          jstr = json_loads(resp_str)
          if "syncStatus" in jstr and jstr["syncStatus"] == "IN_SYNC":
            log.warn("Got Sync from Controller={0}".format(name))
            break
    else:
      log.error("Deploy of Controller={0} NOT successful".format(name))
      log.warn(bcolors.OKWARN+"We can not proceed without the Controller Deploy." +
              'You can fix the error and then refresh (type r) to try the creation again.' +
              "Typing a n (No)  will exit the program. Typing a y (Yes) will continue" + bcolors.ENDC)
      ret = yes_or_no2(bcolors.OKWARN+"To Refresh press r, to Continue press y and to Exit press n: "+ bcolors.ENDC,1)
      if ret == 0 : sys.exit("Deploy of Controller = {0} NOT sucessful ".format(name))
      elif ret == 1: pass
      else:
        deploy_controller( _method, _uri,_payload,resp=resp, name=name)

    log.warn("Checking Controller={0} Sync Status. Please be patient".format(name))
    found = 0
    rc = 1
    while rc:
      for i in range(0,5):
        time.sleep(5)
        [out,resp_str] = common.check_controller_status(name=name)
        if out == 1 and len(resp_str) > 3:
          jstr = json_loads(resp_str)
          if "syncStatus" in jstr and jstr["syncStatus"] == "IN_SYNC":
            log.warn("New Controller = {0} in Sync. ".format(name))
            found = 1
            rc = 0
            break
      if found == 0:
        log.warn(bcolors.OKWARN+"Controller Sync Status is not Correct." + 'You can fix the error and then refresh (type r) to try the deploy again' +
                  "Typing a n (No)  will exit the program. Typing a y (Yes) will continue" + bcolors.ENDC)
        ret = yes_or_no2(bcolors.OKWARN+"To Refresh press r, to Continue press y and to Exit press n: "+ bcolors.ENDC,1)
        if ret == 0 : sys.exit("Controller not in proper state for Controller: {0}".format(name))
        elif ret == 1: rc = 0
        else: pass

    return 

def get_available_orgId( _method, _uri, _payload,resp='200'):
    global vnms, analy, cntlr, cust, admin, log
    resp2 = '202'
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': _uri}
    [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no")
    if resp_str == "":
       log.error("This is most likely a password issue. Please change and re-run")
       exit(0)
    if len(resp_str) >=1 :
      jstr = json_loads(resp_str)
      if debug : log.info("Available OrgId={0}".format(jstr))
      if jstr != 1: jstr = "1"
      vnms.data['parentOrgId'] = jstr
      cust.data['custOrgId'] = str(int(str(jstr)) + 1)
    else:
      log.error("Did not get correct response -- setting default values")
      vnms.data['parentOrgId'] = "1" 
      cust.data['custOrgId'] = "2"

    write_outfile(vnms,analy,cntlr,cust, admin)
    return ''

def get_available_vrf_id( _method, _uri, _payload,resp='200'):
    global vnms, analy, cntlr, cust, admin, log
    resp2 = '202'
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': _uri}
    [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no")
    jstr = json_loads(resp_str)
    if len(resp_str) > 3 :
      vnms.data['parentVrfId'] = jstr["SdwanGlobalIds"]["globalIds"][0]
      cust.data['custOrgVrfId']  = str(int(vnms.data['parentVrfId']) + 1)
      cust.data['custOrgMGMTVrfId'] = str(int(vnms.data['parentVrfId']) + 2)
      write_outfile(vnms,analy,cntlr,cust, admin)
      if debug : print(jstr)
    else:
      print("no valid orgId found")
      sys.exit(0)
    return ''

def get_controller_site_id( _method, _uri, _payload,resp='200'):
    global vnms, analy, cntlr, cust, admin, log
    resp2 = '202'
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': _uri}
    [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no")
    if len(resp_str) > 3 :
      jstr = json_loads(resp_str)
      vnms.data['cntrlSiteId'] = int(jstr["totalCount"])
      cntlr.data[0]['siteId'] = str(int(jstr["totalCount"]) + 1)
      if len(cntlr.data) > 1 :
        cntlr.data[1]['siteId'] = str(int(jstr["totalCount"]) + 2)
      if debug : print(jstr)
      write_outfile(vnms,analy,cntlr,cust, admin)
    else:
      log.error("Did not get Controller Site Id")
      sys.exit("Did not get Controller Site Id")
    return ''

def process_diff(f1, f2):
    cnt1=Counter()
    for i in f1:
      cnt1[i] += 1
    cnt2=Counter()
    for i in f2:
      cnt2[i] += 1

    return list(cnt2-cnt1)

def get_backup( _method, _uri,_payload,resp='200'):
    global log
    resp2='202'
    uri = "/api/config/system/_operations/recovery/list"
    payload = {}
    vdict1 = {'body': payload, 'resp': resp,'resp2': resp2, 'method': "POST", 'uri': uri}
    [out, resp_str] = call(vdict1,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3 :
      recoverylist1 = json_loads(resp_str)
      if "output" in recoverylist1:
        if "files" in recoverylist1["output"]:
          file1 = [ i["name"] for i in recoverylist1["output"]["files"] ] 
        else:
          file1 = []
        # Now call the backup Api
        vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method':_method , 'uri': _uri}
        [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
        if len(resp_str) > 3 :
          backup = json_loads(resp_str)
          if "output" in  backup and "status" in backup["output"] and (backup["output"]["status"].find("initiated") != -1):
            for i in range(0,5):
              time.sleep(10)
              [out, resp_str] = call(vdict1,content_type='json',ncs_cmd="no",jsonflag=1)
              if len(resp_str) > 3 :
                recoverylist2 = json_loads(resp_str)
                if "output" in recoverylist2 and "files" in recoverylist2["output"]:
                  file2 = [ i["name"] for i in recoverylist2["output"]["files"] ] 
                  if len(file2) > len (file1):
                    diff_list = process_diff(file1, file2)
                    if len(diff_list) > 0:
                      diff_name = diff_list[0]
                      log.warn(bcolors.OKWARN +"Backup on Director Created with Name={0} ".format(diff_name)+ bcolors.ENDC)
                      return True
    return False

def get_parent_org_uuid( _method, _uri, _payload,resp='200'):
    global vnms, analy, cntlr, cust, admin, log
    resp2 = '202'
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': _uri}
    [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no")
    if len(resp_str) > 3 :
      jstr = json_loads(resp_str)
      vnms.data['parentOrgId'] = str(jstr["id"])
      vnms.data['parentOrgUuid'] = str(jstr["uuid"])
      if debug : print(jstr)
      write_outfile(vnms,analy,cntlr,cust, admin)
    else:
      log.error("Did not get Parent Org UUID")
      sys.exit(0)
    return ''

def get_cust_orgid( _method, _uri, _payload,resp='200'):
    global vnms, analy, cntlr, cust, admin, log
    resp2 = '202'
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': _uri}
    [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no")
    if len(resp_str) > 3:
      jstr = json_loads(resp_str)
      cust.data['custOrgId'] = str(jstr["organizations"][0]["globalOrgId"])
      cust.data['custOrgVrfId'] = str(jstr["organizations"][0]["globalOrgId"])
      if debug : print(jstr)
      write_outfile(vnms,analy,cntlr,cust, admin)
    else:
      log.error("Did not get Customer OrgID")
      exit(0)
    return ''

def get_bgp_id( _method, _uri, _payload,resp='200'):
    global vnms, analy, cntlr, cust, admin,log
    resp2 = '202'
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': _uri}
    [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json_loads(resp_str)
      cntlr.data[0]['bgpId'] = str(jstr["rti-bgp"][0]["instance-id"])
      if debug : print(jstr)
      write_outfile(vnms,analy,cntlr,cust, admin)
    else:
      log.error("Did not get BGP ID")
    return ''

def analytics_call( _method, _uri,_payload,resp='200'):
    global debug, admin
    vdict = {'body': _payload, 'resp': resp, 'method': _method, 'uri': _uri, 'ip': admin.data['analy_ip']}
    for _ in range(0,5): 
      [ret, resp_code, resp] =  analycall(vdict) 
      if ret: 
        log.info("Resp Code={0} Resp={1}".format(str(resp_code),resp))
        break
      elif (str(resp_code)[0] == "4") : # this is a 4xx
        log.info("Resp Code={0} Resp={1}".format(str(resp_code),resp))
        break
      else: 
        log.info("Retrying Resp Code={0} Resp={1}".format(str(resp_code),resp))
        time.sleep(5)
    return ''

# the only difference between analytics_call and analytics_call1 is the ip which we are passing in the vdict
def analytics1_call( _method, _uri,_payload,resp='200'):
    global debug, admin,log
    vdict = {'body': _payload, 'resp': resp, 'method': _method, 'uri': _uri, 'ip': admin.data['analy_ip1']}
    for _ in range(0,5): 
      [ret, resp_code, resp] =  analycall(vdict) 
      if ret: 
        log.info("Resp Code={0} Resp={1}".format(str(resp_code),resp))
        break
      elif (str(resp_code)[0] == "4") : # this is a 4xx
        log.info("Resp Code={0} Resp={1}".format(str(resp_code),resp))
        break
      else: 
        log.info("Retrying Resp Code={0} Resp={1}".format(str(resp_code),resp))
        time.sleep(5)
    return ''

def create_dns_config( _method, _uri,_payload,resp='200'):
    global log
    vdict = {'body': _payload, 'resp': resp, 'method': _method, 'uri': _uri}
    [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no")
    if out != 1 :
       log.error("Error in functin create_dns_config")
    return ''

def create_ntp_config( _method, _uri,_payload, resp='200'):
    global log
    vdict = {'body': _payload, 'resp': resp, 'method': _method, 'uri': _uri}
    [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no")
    if out != 1 :
       log.error("Could not create ntp config")
    return ''

def update_org_limits (_method, _uri, _payload,resp='200'):
    global log
    vdict = {'body': _payload, 'resp': resp, 'method': _method, 'uri': _uri}
    [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no")
    if out != 1 :
       log.error("Could not update org limits")

    return ''

def create_cust_org ( _method, _uri,_payload, resp='200'):
    global log
    vdict = {'body': _payload, 'resp': resp, 'method': _method, 'uri': _uri}
    [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no",jsonflag=1,max_retry_for_task_completion=40)
    if out == 1:
       return True
    else:
       log.error("Could not create Customer Org")
       sys.exit("Could not create Customer Org")
       return False

def onboard_cust_org ( _method, _uri,_payload,resp='202'):
    global log
    vdict = {'body': _payload, 'resp': resp, 'method': _method, 'uri': _uri}
    [out, resp_str] = call(vdict,content_type='json',ncs_cmd="no",jsonflag=1,max_retry_for_task_completion=40)
    if out == 1:
       return True
    else:
       log.error("Could not onboard Customer Org")
       sys.exit("Could not onboard Customer Org")
       return False

def write_outfile(_vnms,_analy,_cntlr,_cust, _admin):
    global vnms, analy, cntlr, cust, admin, log
    log.info("In function {0} : Output file:outfile_day1.json".format(write_outfile.__name__))
    jstr = {}
    jstr["Vnms"] = _vnms.data
    jstr["Analytics"] = _analy.data
    jstr["Controller"] = _cntlr.data
    jstr["Admin"] = _admin.data
    jstr["Customer"] = _cust.data
    fin=open("outfile_day1.json", "w+")
    mstr1 = json.dumps(jstr, indent=4)
    fin.write(mstr1)
    fin.close()

def yes_or_no(question):
    if pyVer.major== 3:
      reply = str(input(question+' (y/n): ')).lower().strip()
    else:
      reply = str(raw_input(question+' (y/n): ')).lower().strip()
    if reply[0] == 'y':
        return True
    if reply[0] == 'n':
        return False
    else:
        return yes_or_no("Ughhh... please re-enter ") 

def yes_or_no2(question, option=0):

    if option == 0:
      if pyVer.major== 3:
        reply = str(input(question)).lower().strip()
      else:
        reply = str(raw_input(question)).lower().strip()
      if reply[0] == 'n': return 0
      elif reply[0] == 'y': return 1
      elif reply[0] == 's': return 2
      else:
        return yes_or_no2("Did not understand input: Please re-enter ",option)
    else:
      if pyVer.major== 3:
        reply = str(input(question)).lower().strip()
      else:
        reply = str(raw_input(question)).lower().strip()
      if reply[0] == 'n': return 0
      elif reply[0] == 'y': return 1
      elif reply[0] == 'r': return 2
      else:
        return yes_or_no2("Did not understand input: Please re-enter ",option)

def setup_logging(logfile,log_size):
        
    global log
    if log is not None: return
    ## Enable logging
    log = logging.getLogger('day1')
    while len(log.handlers) > 0:
      h = log.handlers[0]
      log.removeHandler(h)
      #print("Number of handlers={}".format(len(log.handlers)))


    # Set logging level
    log.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(message)s")
    cli_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(lineno)d - %(message)s")

    # create a rotating handler
    handler = logging.handlers.RotatingFileHandler(logfile,
                                maxBytes=log_size, backupCount=5)
    stdouth = logging.StreamHandler(sys.stdout)

    # add formatter to ch
    stdouth.setFormatter(cli_formatter)
    handler.setFormatter(formatter)

    # Add the log message handler to the logger
    log.addHandler(handler)
    log.addHandler(stdouth)
    #cls.log = log
    #cls.log_info(cls.VERSA_BANNER)
    return 

def manipulate_analy_data(a1):
    if a1 is not None:
      devlist=a1["Nodes"]
      y={}
      for i in range(len(devlist)): y[devlist[i]["name"]] = devlist[i]["northip"]
      a1["webaddr"] = {}
      a1["webaddr"] = y
      northip = [ devlist[i]["northip"] for i in range(len(devlist)) ]
      a1["northip"] = []
      a1["northip"] = northip
      southip = [ devlist[i]["southip"] for i in range(len(devlist)) ]
      a1["southip"] = []
      a1["southip"] = southip
      analy_southip = []
      for elem in devlist:
         if elem["type"] == "analytics": analy_southip.append(elem["southip"])
      a1["analy_southip"] = []
      a1["analy_southip"] = analy_southip 

      search_southip = []
      for elem in devlist:
         if elem["type"] == "search": search_southip.append(elem["southip"])
      a1["search_southip"] = []
      a1["search_southip"] = search_southip

      lf_southip = []
      for elem in devlist:
         if elem["type"] == "lf": lf_southip.append(elem["southip"])
      a1["lf_southip"] = []
      a1["lf_southip"] = lf_southip

    return

    



def main():
    global vnms, analy, cntlr, cust, admin, auth, debug, log
    #mdict = readfile("in_rest.cfg")
    argcheck()
    debug = int(args['debug'])
    infile = args['file']
    dir1 = dir2 = analy1 = analy2 = cntlr1 = cntlr2 = None
    LOG_FILENAME = 'day1.log'
    LOG_SIZE = 8 * 1024 * 1024
    setup_logging(LOG_FILENAME, LOG_SIZE)
    log.info("===============Starting Day1 Execution==========")

    fp = open(infile,"r")
    jstr = fp.read()
    fp.close()
    mdict=json_loads(jstr,object_pairs_hook=OrderedDict)
    for _keys,_val in mdict.items():
      if _keys.lower() == "vnms": 
         vnms =  Vnms(_val)
         if len(vnms.data["director"]) > 1 :
           dir1 = vnms.data["director"][0]
           dir2 = vnms.data["director"][1]
         else:
           dir1 = vnms.data["director"][0]
           dir2 = None
         #if debug : pprint(vnms.data)
      elif _keys.lower() == "analytics": 
         analy = Analytics(_val)
         if len(analy.data) > 1 :
            analy1 = analy.data[0]
            analy2 = analy.data[1]
         else:
            analy1 = analy.data[0]
            analy2 = None
         manipulate_analy_data(analy1)
         manipulate_analy_data(analy2)
         #if debug : pprint(analy.data)
      elif _keys.lower() == "controller": 
         cntlr =  Controller(_val)
         if len(cntlr.data) > 1 :
            cntlr1 = cntlr.data[0]
            cntlr2 = cntlr.data[1]
         #if debug : pprint(cntlr.data)
      elif _keys.lower() == "customer": 
         cust = Customer(_val)
         pprint(cust.data)
      elif _keys.lower() == "admin": 
         admin = Admin(_val)
         if pyVer.major == 3:
           admin.data['auth'] = base64.b64encode(bytes('%s:%s' % (str(admin.data['user']), str(admin.data['password'])),"utf-8")).decode('ascii')
         else:
           admin.data['auth'] = base64.encodestring('%s:%s' % (str(admin.data['user']), str(admin.data['password']))).replace('\n', '')

    log.warn("Please check your Customer Name={0}, Controller Names={1} {2} and IPs before we continue".format(cust.data['custName'],cntlr.data[0]['controllerName'],cntlr.data[1]['controllerName']))
    if yes_or_no("Continue"): pass
    else: return


    fil = OrderedDict()
    fil['GET_AVAILABLE_ORG_ID.json']  = get_available_orgId
    fil['GET_AVAILABLE_VRF_ID.json'] = get_available_vrf_id
    fil['GET_CONTROLLER_SITE_ID.json'] = get_controller_site_id
    fil['GET_RECOVERY_BACKUP.json'] = get_backup
    fil['CREATE_PROVIDER_ORG.json']  = onboard_provider_org
    fil['GET_PARENT_ORG_UUID.json'] = get_parent_org_uuid
    # Below go the the default function 
    #fil['SDWAN_OVERLAY.json'] = create_dns_config 
    #fil['NTP_CONFIG.json'] = create_dns_config 
    #fil['CREATE_TACACS.json'] = create_dns_config 
    #fil['CREATE_TRANSPORT_DOMAINS.json'] = create_dns_config
    #fil['WAN_NETWORK.json'] = create_dns_config
    #fil['USER_GLOBAL_SETTINGS.json'] = create_dns_config
    #fil['CREATE_ANALYTICS_CLUSTER.json'] = create_dns_config

    fil['REGISTER_VD_HOST_NAME.json'] = analytics_call
    fil['CONFIG_ANALYTICS_CLUSTER_DC1.json'] = analytics_call
    fil['REGISTER_PEER_VD_HOST_NAME.json'] = analytics1_call
    fil['CONFIG_ANALYTICS_CLUSTER_DC2.json'] = analytics1_call
    fil['CREATE_CONTROLLER.json'] = create_controller
    fil['DEPLOY_CONTROLLER.json'] = deploy_controller
    fil['CREATE_PEER_CONTROLLER.json'] = create_controller
    fil['DEPLOY_PEER_CONTROLLER.json'] = deploy_controller
    fil['CREATE_CUST_ORG.json'] = create_cust_org
    fil['ONBOARD_CUST_ORG.json'] = onboard_cust_org
    fil['GET_CUST_ORG_VRFID.json'] = get_cust_orgid 
    fil['GET_CONTROLLER_TVI.json'] = get_controller_tvi
    fil['GET_PEER_CONTROLLER_TVI.json'] = get_controller_tvi



    fil['COMMIT_CONFIG_CHANGES.json'] = create_dns_config
    fil['SYNCH_CONTROLLER_DC1.json'] = create_dns_config

    
    #fil['GET_BGP_ID.json'] = get_bgp_id
    #fil['EBGP_DC1.json'] = create_dns_config
    fil['LOG_COLLECTOR.json'] = analytics_call
    fil['LOG_COLLECTOR_PEER.json'] = analytics1_call
    fil['SRV_TMPL_VZ_MGMT_GST_1.json'] =  create_dns_config
    fil['SRV_TMPL_VZ_MGMT_GST_2.json'] =  create_dns_config
    fil['SRV_TMPL_VZ_MGMT_GST_3.json'] =  create_dns_config
    fil['SRV_TMPL_VZ_LAN_MGMT_GST_ADDON_1.json'] =  create_dns_config
    fil['SRV_TMPL_VZ_LAN_MGMT_GST_ADDON_2.json'] =  create_dns_config
    fil['SRV_TMPL_VZ_MGMT_GST_SFW_ADDON_1.json'] =  create_dns_config
    fil['SRV_TMPL_VZ_MGMT_GST_SFW_ADDON_2.json'] =  create_dns_config
    fil['SRV_TMPL_VZ_MGMT_GST_NGFW_ADDON_1.json'] =  create_dns_config
    fil['SRV_TMPL_VZ_MGMT_GST_NGFW_ADDON_2.json'] =  create_dns_config
    fil['SRV_TMPL_VZ_MGMT_GST_NGFW_ADDON_3.json'] =  create_dns_config
    fil['ENABLE_HA.json'] = enable_ha

    template_path = os.path.abspath(sys.argv[0]).rsplit("/",1)[0] + "/" + vnms.data['rel'] 
    template_loader = jinja2.FileSystemLoader(searchpath=template_path)
    template_env = jinja2.Environment(loader=template_loader,undefined=jinja2.StrictUndefined)
    template_env.filters['jsonify'] = json.dumps
    dir_items = sorted(os.listdir(template_path))

    for i in dir_items:
       # check the format of the files
       if not re.match(r'^\d{3}_.+\.json$', i):
          continue
       _key = i[4:]
       if _key in fil:
          _val = fil[_key]
       else:
          fil[_key]=create_dns_config
          _val = fil[_key]
       #for _key,_val in fil.items():
       my_template = template_env.get_template(i)
       _newkey = _key.split(".")[0]
       log.info("==============In %s==========" %(_newkey))
       if not yes_or_no("Continue for {0}".format(_newkey)): continue
       if _key[0:3] == 'GET':
         if _newkey == 'GET_PARENT_ORG_UUID':
           x= my_template.render(parentOrgName=vnms.data['parentOrgName'])
           y=json_loads(x)
           _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
         elif _newkey == 'GET_CUST_ORG_VRFID':
           x= my_template.render( custName=cust.data['custName'])
           y= json_loads(x)
           _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
         elif _newkey == 'GET_CONTROLLER_TVI' or _newkey == 'GET_PEER_CONTROLLER_TVI':
           cid = 0 if _newkey == 'GET_CONTROLLER_TVI' else 1
           x= my_template.render( controllerName=cntlr.data[cid]['controllerName'])
           y= json_loads(x)
           _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']),_cntlr_id=cid)
         elif _newkey == 'GET_BGP_ID':
           x= my_template.render( controllerName=cntlr.data[0]['controllerName'],
                                  parentOrgName=vnms.data['parentOrgName']) 
           y= json_loads(x)
           _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
         else:
           x= my_template.render()
           y= json_loads(x)
           _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
       elif _newkey == 'CREATE_PROVIDER_ORG':
         vnms.data['parentOrgUuid'] = str(uuid.uuid4())
         x= my_template.render(parentOrgUuid=vnms.data['parentOrgUuid'],
                  parentOrgId=vnms.data['parentOrgId'], parentOrgName=vnms.data['parentOrgName'], 
                  parentOrgSubPlan=vnms.data['parentOrgSubPlan'], parentVrfId=vnms.data['parentVrfId'] )
         y= json_loads(x)
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
       elif _newkey == 'SDWAN_OVERLAY':
         x= my_template.render()
         y= json_loads(x)
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
       elif _newkey == 'NTP_CONFIG':
         x= my_template.render(pipNtp=vnms.data['ntp']['pipNtp'],ntpServerVersion=vnms.data['ntp']['ntpServerVersion'],
                               pipNtp1=vnms.data['ntp']['pipNtp1'],
                               inetDns1=vnms.data['dns']['inetDns1'],inetDns2=vnms.data['dns']['inetDns2'],
                               dnsSearchDomain1=vnms.data['dns']['dnsSearchDomain1'])
         y= json_loads(x)
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
       elif _newkey == 'CREATE_TACACS':
         alist = [analy1]
         if analy2 is not None: alist.append(analy2)
         x= my_template.render(tacacsName=vnms.data['authConnector']['name'],
                               tacacsConnectorType=vnms.data['authConnector']['type'],
                               tacacslist=vnms.data['authConnector']['server-detail'],
                               analytics_clist=alist)
         y= json_loads(x)
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
         log.info("Sleeping for 30 sec -- please be patient")
         time.sleep(30) # Need to sleep because we just did TACACS
       elif _newkey == 'CREATE_TRANSPORT_DOMAINS':
         x= my_template.render(transportDomainName="MPLS", domid="10")
         y= json_loads(x)
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
         x= my_template.render(transportDomainName="Internet", domid="20")
         y= json_loads(x)
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
       elif _newkey == 'WAN_NETWORK':
         x= my_template.render(parentOrgUuid=vnms.data['parentOrgUuid'], versaNtwkTypeForWanNwk="MPLS", 
                               transDomainForWanNwk="MPLS")
         y= json_loads(x)
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
         x= my_template.render(parentOrgUuid=vnms.data['parentOrgUuid'], versaNtwkTypeForWanNwk="Internet", transDomainForWanNwk="Internet")
         y= json_loads(x)
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
       elif _newkey == 'USER_GLOBAL_SETTINGS':
         x= my_template.render()
         y= json_loads(x)
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
       elif _newkey == 'CREATE_ANALYTICS_CLUSTER' or _newkey == 'CREATE_PEER_ANALYTICS_CLUSTER':
         if _newkey == 'CREATE_ANALYTICS_CLUSTER' : myanaly = analy1
         else:
           myanaly = analy2 
           if myanaly is None: continue
         x= my_template.render(defaultAnalyticsClusterName1=myanaly['defaultAnalyticsClusterName1'],
                               analyticsDefaultPortConnector=myanaly['analyticsDefaultPortConnector'],
                               analytics_address=myanaly['webaddr'],
                               analyticsDefaultPort=myanaly['analyticsDefaultPort'],
                               analyip=myanaly['southip'])
         y= json_loads(x)
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
       elif _newkey == 'REGISTER_VD_HOST_NAME' or _newkey == 'REGISTER_PEER_VD_HOST_NAME':
         if _newkey == 'REGISTER_VD_HOST_NAME' : mydir = dir1 
         else:
           mydir = dir2 
           if mydir is None: continue
         x= my_template.render(directorHostName=mydir['directorHostName'])
         y= json_loads(x)
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
       elif _newkey == 'ENABLE_HA': 
         if dir1 is None or dir2 is None : 
            continue
         else:
           x= my_template.render(mgmntIpAddress=dir1['directorIP'], peerMgmntIpAddress=dir2['directorIP'])
           y= json_loads(x)
           _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
       elif _newkey == 'CONFIG_ANALYTICS_CLUSTER_DC1' or _newkey == 'CONFIG_ANALYTICS_CLUSTER_DC2':
         if vnms.data['rel'].find("21") != -1: # We are in release 21.X - do not need this
           continue
         if _newkey == 'CONFIG_ANALYTICS_CLUSTER_DC1' : myanaly = analy1
         else:
           myanaly = analy2 
           if myanaly is None: continue
         x= my_template.render(searchip=myanaly['search_southip'],analyip=myanaly["analy_southip"],allip=myanaly['northip'])
         y= json_loads(x)
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
       elif _newkey == 'CREATE_CONTROLLER' or _newkey == 'CREATE_PEER_CONTROLLER':
         if _newkey == 'CREATE_CONTROLLER' : 
           mycntrl = cntlr1 
           mycntrl_peer = cntlr2 
           myanaly = analy1
         else:
           mycntrl = cntlr2 
           mycntrl_peer = cntlr1 
           myanaly = analy2
           if mycntrl is None or myanaly is None: continue
         x= my_template.render( controllerName=mycntrl['controllerName'],
                                peercontrollerName=mycntrl_peer['controllerName'],
                                siteId =mycntrl['siteId'],
                                stagingController=mycntrl['stagingController'],
                                postStagingController=mycntrl['postStagingController'],
                                resourceType=mycntrl['resourceType'],
                                ipv4dhcp=mycntrl['ipv4dhcp'],
                                state=mycntrl['state'],
                                zipCode=mycntrl['zipcode'],
                                country=mycntrl['country'],
                                longitude=mycntrl['longitude'],
                                latitude=mycntrl['latitude'],
                                mgmt_ntwk_ipv4_addr=mycntrl['mgmt_ntwk_ipv4_addr'],
                                cntrl_ntwk_ipv4_addr=mycntrl['cntrl_ntwk_ipv4_addr'],
                                cntrl_ntwk_ipv4_mask=mycntrl['cntrl_ntwk_ipv4_mask'],
                                cntrl_ntwk_ipv4_gtwy=mycntrl['cntrl_ntwk_ipv4_gtwy'],
                                inet_ntwk_ipv4_addr=mycntrl['inet_ntwk_ipv4_addr'],
                                inet_ntwk_ipv4_mask=mycntrl['inet_ntwk_ipv4_mask'],
                                inet_ntwk_ipv4_gtwy=mycntrl['inet_ntwk_ipv4_gtwy'],
                                inet_ntwk_public_ip=mycntrl['inet_ntwk_public_ip'],
                                pip_ntwk_ipv4_addr=mycntrl['pip_ntwk_ipv4_addr'],
                                pip_ntwk_ipv4_mask=mycntrl['pip_ntwk_ipv4_mask'],
                                pip_ntwk_ipv4_gtwy=mycntrl['pip_ntwk_ipv4_gtwy'],
                                cntlr_mnso_peer_as=mycntrl['cntlr_mnso_peer_as'],
                                parentOrgName=vnms.data['parentOrgName'],
                                defaultAnalyticsClusterName=myanaly['defaultAnalyticsClusterName1'])
         y= json_loads(x)
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']),name=mycntrl['controllerName'])
       elif _newkey == 'DEPLOY_CONTROLLER' or _newkey == 'DEPLOY_PEER_CONTROLLER':
         if _newkey == 'DEPLOY_CONTROLLER' : mycntrl = cntlr1 
         else:
           mycntrl = cntlr2 
           if mycntrl is None: continue
         x= my_template.render( controllerName=mycntrl['controllerName'])
         y= json_loads(x)
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']),name=mycntrl['controllerName'])
       elif _newkey == 'CREATE_CUST_ORG':
         cname = [cntlr1["controllerName"]]
         if cntlr2 is not None: cname.append(cntlr2["controllerName"])
         aname = [analy1["defaultAnalyticsClusterName1"]]
         if analy2 is not None: aname.append(analy2["defaultAnalyticsClusterName1"])
         x= my_template.render( custName=cust.data['custName'],
                                custOrgId=cust.data['custOrgId'],
                                parentOrgName=vnms.data['parentOrgName'], 
                                defaultIkeAuthType=cust.data['defaultIkeAuthType'],
                                controllerName=cname,
                                custOrgVrfId=cust.data['custOrgVrfId'],
                                custOrgMGMTVrfId=cust.data['custOrgMGMTVrfId'],
                                defaultAnalyticsClusterName=aname)
         y= json_loads(x)
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
       elif _newkey == 'ONBOARD_CUST_ORG':
         cname = [cntlr1["controllerName"]]
         if cntlr2 is not None: cname.append(cntlr2["controllerName"])
         aname = [analy1["defaultAnalyticsClusterName1"]]
         if analy2 is not None: aname.append(analy2["defaultAnalyticsClusterName1"])
         x= my_template.render( custName=cust.data['custName'],
                                custOrgId=cust.data['custOrgId'],
                                parentOrgName=vnms.data['parentOrgName'], 
                                defaultIkeAuthType=cust.data['defaultIkeAuthType'],
                                controllerName=cname,
                                custOrgVrfId=cust.data['custOrgVrfId'],
                                custOrgMGMTVrfId=cust.data['custOrgMGMTVrfId'],
                                defaultAnalyticsClusterName=aname)
         y= json_loads(x)
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
       elif _newkey == 'CONFIG_CNTRL1_BUILD_OPTION' or _newkey == 'CONFIG_CNTRL2_BUILD_OPTION':
         if _newkey == 'CONFIG_CNTRL1_BUILD_OPTION' : mycntrl = cntlr1 
         else:
           mycntrl = cntlr2 
           if mycntrl is None: continue
         x= my_template.render( controllerName=mycntrl['controllerName'])
         y= json_loads(x)
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
       elif _newkey == 'PATCH_CNTRL1_NEW' or _newkey == 'PATCH_CNTRL2_NEW':
         if _newkey == 'PATCH_CNTRL1_NEW' : mycntrl = cntlr1 
         else:
           mycntrl = cntlr2 
           if mycntrl is None: continue
         x= my_template.render( controllerName=mycntrl['controllerName'], 
                                    cntrl_gtwy_mnso_ipv4_addr=mycntrl['cntrl_gtwy_mnso_ipv4_addr'],
                                    cntrl_gtwy_mnso_ipv4_mask=mycntrl['cntrl_gtwy_mnso_ipv4_mask'],
                                    custName=cust.data['custName'],
                                    custOrgId=cust.data['custOrgId'],
                                    custOrgMGMTVrfId=cust.data['custOrgMGMTVrfId'],
                                    cntlr_mnso_peer_as=mycntrl['cntlr_mnso_peer_as'],
                                    cntrl_gtwy_mnso_ipv4_gtwy=mycntrl['cntrl_gtwy_mnso_ipv4_gtwy'],
                                    cntlr_mnso_router_id=mycntrl['cntrl_gtwy_mnso_ipv4_addr'],
                                    pipNtp=vnms.data['ntp']['pipNtp'],
                                    pipNtp1=vnms.data['ntp']['pipNtp1'],
                                    ntpServerVersion=vnms.data['ntp']['ntpServerVersion'])
         y= json_loads(x)
         log.info("KEY={0} Output={1}".format(_newkey,json.dumps(y,indent=4)))
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
       elif _newkey == 'PATCH_CNTRL1_ORG_SERVICES' or _newkey == 'PATCH_CNTRL2_ORG_SERVICES':
         if _newkey == 'PATCH_CNTRL1_ORG_SERVICES' : 
           mycntrl = cntlr1 
           myanaly = analy1
         else:
           mycntrl = cntlr2 
           myanaly = analy2
           if mycntrl is None: continue
         indx = range(1, int(str(myanaly['num_analy']))+1)
         southip = dict(zip(indx,myanaly['southip']))
         x= my_template.render( controllerName=mycntrl['controllerName'], 
                                parentOrgName=vnms.data['parentOrgName'], 
                                southip=southip, tvi_esp=mycntrl['tvi_esp'])
         y= json_loads(x)
         log.info("KEY={0} Output={1}".format(_newkey,json.dumps(y,indent=4)))
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
       elif _newkey == 'PATCH_CNTRL1_ORG_LIMIT' or _newkey == 'PATCH_CNTRL2_ORG_LIMIT':
         if _newkey == 'PATCH_CNTRL1_ORG_LIMIT' : mycntrl = cntlr1 
         else:
           mycntrl = cntlr2 
           if mycntrl is None: continue
         x= my_template.render( controllerName=mycntrl['controllerName'], 
                                custName=cust.data['custName'],
                                parentOrgName=vnms.data['parentOrgName'], 
                                custOrgId=cust.data['custOrgId'])
         y= json_loads(x)
         log.info("KEY={0} Output={1}".format(_newkey,json.dumps(y,indent=4)))
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
       elif _newkey == 'COMMIT_CNTRL1_CONFIG_CHANGES' or _newkey == 'COMMIT_CNTRL2_CONFIG_CHANGES':
         if _newkey == 'COMMIT_CNTRL1_CONFIG_CHANGES' : mycntrl = cntlr1 
         else:
           mycntrl = cntlr2 
           if mycntrl is None: continue
         x= my_template.render( controllerName=mycntrl['controllerName'])
         y= json_loads(x)
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
       elif _newkey == 'SYNCH_CONTROLLER_DC1' or _newkey == 'SYNCH_CONTROLLER_DC2':
         if _newkey == 'SYNCH_CONTROLLER_DC1' : mycntrl = cntlr1 
         else:
           mycntrl = cntlr2 
           if mycntrl is None: continue
         x= my_template.render( controllerName=mycntrl['controllerName'])
         y= json_loads(x)
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
       elif _newkey == 'EBGP_DC1':
         x= my_template.render( controllerName=cntlr.data[0]['controllerName'],
                                cntlr_mnso_peer_as=cntlr.data[0]['cntlr_mnso_peer_as'],
                                cntrl_ntwk_ipv4_gtwy=cntlr.data[0]['cntrl_ntwk_ipv4_gtwy'],
                                bgpId=cntlr.data[0]['bgpId'],
                                parentOrgName=vnms.data['parentOrgName']) 
         y= json_loads(x)
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
       elif _newkey == 'LOG_COLLECTOR':
         if vnms.data['rel'].find("21") != -1: # We are in release 21.X - do not need this
           continue
         for i in range(0, int(str(analy.data[0]['num_analy']))):
           x= my_template.render( south_ip=analy.data[0]['southip'][i], num=i+1)
           y= json_loads(x)
           _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
       elif _newkey == 'LOG_COLLECTOR_PEER':
         if vnms.data['rel'].find("21") != -1: # We are in release 21.X - do not need this
           continue
         mynum_analy = int(str(analy.data[1]['num_analy']))
         for i in range(0, mynum_analy):
           x= my_template.render( south_ip=analy.data[1]['southip'][i],
                                  num=mynum_analy+i+1)
           y= json_loads(x)
           _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
       elif (_newkey == 'SRV_TMPL_VZ_MGMT_GST_1' or
             _newkey == 'SRV_TMPL_VZ_MGMT_GST_2' or
             _newkey == 'SRV_TMPL_VZ_LAN_MGMT_GST_ADDON_1' or
             _newkey == 'SRV_TMPL_VZ_LAN_MGMT_GST_ADDON_2' or
             _newkey == 'SRV_TMPL_VZ_MGMT_GST_SFW_ADDON_1' or
             _newkey == 'SRV_TMPL_VZ_MGMT_GST_SFW_ADDON_2' or 
             _newkey == 'SRV_TMPL_VZ_MGMT_GST_NGFW_ADDON_1' or
             _newkey == 'SRV_TMPL_VZ_MGMT_GST_NGFW_ADDON_2' or
             _newkey == 'SRV_TMPL_VZ_MGMT_GST_NGFW_ADDON_3') :
           dirlist=[dir1['directorIP']]
           if  dir2 is not None: dirlist.append(dir2['directorIP'])
           x= my_template.render( custOrgMGMTVrfId=cust.data['custOrgMGMTVrfId'],
                                custName=cust.data['custName'],
                                cntrl_ntwk_ipv4_addr=cntlr.data[0]['cntrl_ntwk_ipv4_addr'],
                                custOrgId=cust.data['custOrgId'],
                                pipNtp=vnms.data['ntp']['pipNtp'],
                                pipNtp1=vnms.data['ntp']['pipNtp1'],
                                vzUserPasswd=vnms.data['users']['VZuser'],
                                adminUserPasswd=vnms.data['users']['admin'],
                                mlist=vnms.data['authConnector']['server-detail'],dirlist=dirlist) 
           y= json_loads(x)
           _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))

    print("==============Completed==============")

if __name__ == "__main__":
    main()


