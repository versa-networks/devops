#!/usr/bin/env python2
#si sw=2 sts=2 et
import os, sys, signal, argparse
import jinja2
from jinja2.utils import concat
import re
import requests
import time
import base64
import json
from pprint import pprint
from collections import OrderedDict, Counter
from pprint import pprint
import logging
import logging.handlers
import copy
import glbl
import common 

pyVer = sys.version_info
if pyVer.major == 3:
  import http.client as httplib 
else:
  import httplib


vnms =  None
analy = None 
cntlr = None
cust = None
admin = None
debug = 0
mlog = None
mdict = None
NOT_DEPLOYED = 0 
MYLINES = 0
MYCOL = 0
newdir = None
olddir = None
LOG_FILENAME = None

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

# arguments check
def argcheck():
  """ This performs adds the  argument and checks the requisite inputs
  """
  global args
  mystr = os.path.basename(sys.argv[0])
  parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]),description='%(prog)s Help:',usage='%(prog)s -f filename [options]', add_help=False)
  parser.add_argument('-f','--file',required=True, help='input file [required ]' )
  parser.add_argument('-r','--read',required=False, action='store_true', help='input file [required ]' )
  parser.add_argument('-d','--debug',default=0,type=int,help='set/unset debug flag')

  try:
    args = vars(parser.parse_args())
  except:
    usage()
    sys.exit(0)

# usage
def usage():
  mystr = os.path.basename(sys.argv[0])
  print(bcolors.OKCHECK)
  print( """\
Usage:
    To change versions use:
      %(mystr)s --f/-f <infile>
    To re-read input data :
      %(mystr)s -f vm_phase3.json -r  [ Note : the file MUST be vm_phase3.json and NOT vm_phase2.json ]
    To add more debug:
      %(mystr)s -f <infile> --debug/-d [0/1]
  """ %locals())
  print(bcolors.ENDC)

# json load with try exception
def json_loads(_str,**kwargs):
    global mlog
    try:
      _jstr = json.loads(_str,**kwargs)
      return _jstr
    except Exception as ex:
       mlog.error('Json load failed: {}'.format(ex))
       sys.exit('Json load failed: {}'.format(ex))


# find wan
def find_wan( _str):
  if _str in glbl.vnms.data['wanNtwk']:
    return glbl.vnms.data['wanNtwk'][_str]
  else:
    return None

# get the wan networks
def get_wan_ntwk( _method, _uri, _payload,resp='200', _name=None,_ofile=None):
    global vnms, analy, cntlr, cust, mlog
    resp2 = '202'
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': _uri}
    mlog.info("In function {0} with outfile={1}".format(get_wan_ntwk.__name__,_ofile))
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if out == 1 and len(resp_str) > 3:
      jstr = json_loads(resp_str)
      mywan = {}
      mywan2 = {}
      # wan name : transport domain
      for i in jstr:
        if 'name' in i:
          mywan[i["name"]] =  i["transport-domains"][0]
          mywan2[i["transport-domains"][0]] = mywan[i["name"]]
        else:
          mlog.error("Could not get Wan Ntwk")

      glbl.vnms.data['wanNtwk'] =  {}
      glbl.vnms.data['wanNtwk'] =  mywan
      glbl.vnms.data['transportDomain'] =  {}
      glbl.vnms.data['transportDomain'] =  mywan2
        
      write_outfile(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin)
    else: 
      mlog.error("Could not get Wan Ntwk")
    return ''

# find the transport domain and create mapping
def find_transport_create_mapping(transpDomain, networkName):
    # transportDomain to network Name  mapping
    if transpDomain in glbl.vnms.data['transportDomain']:
      if 'networkName' not in glbl.vnms.data:
        glbl.vnms.data['networkName'] = {}
        glbl.vnms.data['networkName'][transpDomain] = networkName 
      else:
        glbl.vnms.data['networkName'][transpDomain] = networkName 
      return transpDomain
    mlog.error("Could not get transportDomain={0}".format(transpDomain))
    return None



# Create the controller. Added checks to call the function back if there are errors.
def create_controller( _method, _uri,_payload,resp='200', name="Controller"):
    global vnms, analy, cntlr, cust, mlog
    mlog.warn(bcolors.OKWARN + "Have you performed an erase config on the New Controller: {0} and\n".format(name) + 
                               "verified that services are running. If not, do so now [Sec 4 in cheat_sheet.txt]" + bcolors.ENDC)
    ret = yes_or_no2("Continue: " )
    if ret == 0  or ret == 2 : return
    resp = '200'
    vdict = {'body': _payload, 'resp': resp, 'method': _method, 'uri': _uri}
    [status, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no")
    if status == 1:
      mlog.warn("Creation of New Controller: {0} sucessful ".format(name))
      if len (resp_str) > 3 :
        newjstr = json_loads(resp_str)
        mlog.info("Return json from POST on Controller: {0} = {1}".format(name,json.dumps(newjstr,indent=4)))
    else:
      mlog.error("Creation of New Controller = {0} NOT sucessful ".format(name))
      mlog.warn(bcolors.OKWARN+"We can not proceed without the Controller Create.\n" + 
                'You can fix the error and then refresh (type r) to try the creation again.\n' +
                "Typing a n (No)  will exit the program. Typing a y (Yes) will continue" + bcolors.ENDC)
      ret = yes_or_no(bcolors.OKWARN+"To Refresh press r, to Continue press y and to Exit press n: "+ bcolors.ENDC,1)
      if ret == 0 : sys.exit("Creation of New Controller = {0} NOT sucessful ".format(name))
      elif ret == 1: pass
      else: 
        create_controller( _method, _uri,_payload,resp=resp, name=name)

    # the below is payload of the POST not the response
    jstr = json_loads(_payload)
    mycntlr = None
    for mcntlr in glbl.cntlr.data['new_cntlr']:
      if mcntlr["controllerName"] == name:
        mycntlr = mcntlr
        break
    if mycntlr is None:
      mlog.error("Can not find controller: {0} in my list ".format(name))
      sys.exit("Can not find controller: {0} in my list ".format(name))

    # save the public ip address of the controller. this is needed in phase 3
    if "versanms.sdwan-controller-workflow" in jstr:
      if "peerControllers" in jstr["versanms.sdwan-controller-workflow"]: 
        mycntlr["peerControllers"] =  []
        mycntlr["peerControllers"] =  jstr["versanms.sdwan-controller-workflow"]["peerControllers"]
      if "baremetalController" in jstr["versanms.sdwan-controller-workflow"] and "wanInterfaces" in jstr["versanms.sdwan-controller-workflow"]["baremetalController"] :
        wanlist =  jstr["versanms.sdwan-controller-workflow"]["baremetalController"]["wanInterfaces"]
        for wan in wanlist:
          if "unitInfoList" in wan:
            unitinfoList = wan["unitInfoList"] 
            for unitinfo in unitinfoList:
              if "networkName" in unitinfo:
                #x = find_wan(unitinfo["networkName"]) 
                x = find_transport_create_mapping(unitinfo["transportDomainList"][0], unitinfo["networkName"]) 
                if x and x == "Internet" and "publicIPAddress" in unitinfo:
                  mycntlr["inet_public_ip_address"] = unitinfo["publicIPAddress"]
                elif x and x == "MPLS" and "ipv4address" in unitinfo:
                  y = unitinfo["ipv4address"]
                  mycntlr["mpls_public_ip_address"] = y[0].rsplit("/")[0]
                else:
                  mlog.warn("Getting unknown Ntwk Name = {0}".format(unitinfo["networkName"])) 

    write_outfile(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin)
    return

def get_default( _method, _uri,_payload,resp='200', ofile=None):
    global vnms, analy, cntlr, cust, mlog
    mlog.info("In function " + get_default.__name__)
    vdict = {'body': _payload, 'resp': resp, 'method': _method, 'uri': _uri}
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    jstr = json_loads(resp_str)
    print(jstr)
    if ofile is None: 
       mlog.error("No file provided .. exiting")
       sys.exit("No file provided .. exiting")
    out = common.create_out_data("POST","200","/vnms/sdwan/workflow/controllers/controller", jstr)
    fp=open(ofile,"w+")
    out1 = json.dumps(out, indent=4)
    fp.write(out1)
    fp.close()
    return

# Checking the Old and New Controller Configs
def check_controller_config():
    global vnms, analy, cntlr, cust, mlog

    fname ="cntlr_config.json"
    jstr = None
    mlog.info("In function {0} : Output file:{1}".format(check_controller_config.__name__,fname))
    if os.path.exists(fname): 
      fp = open(fname,"r")
      config = fp.read()
      fp.close()
      jstr = json_loads(config,object_pairs_hook=OrderedDict)
    else:
      mlog.warn("Did not find file={0}".format(fname))
      return
    mlog.warn("Checking Controller Config between Old and New Controller Complexes. Please be patient")
    
    err = [0,0]
    if ("Controller" in jstr and 'new_cntlr' in jstr["Controller"] and 'old_cntlr' in jstr["Controller"] and 
          len(jstr['Controller']['new_cntlr']) ==  len(jstr['Controller']['old_cntlr'])):
      option = [0,1]
      for _option in option:
        tvi_data = copy.deepcopy(jstr["Controller"]['new_cntlr'][_option]["configuration"]["config"]["interfaces"]["tvi"])
        elem_new_name = jstr["Controller"]['new_cntlr'][_option]["controllerName"]
        tvi_old_data = copy.deepcopy(jstr["Controller"]['old_cntlr'][_option]["configuration"]["config"]["interfaces"]["tvi"])
        elem_old_name = jstr["Controller"]['old_cntlr'][_option]["controllerName"]
        if len(tvi_data) == len(tvi_old_data): 
          for elem in tvi_data:
            unit_name = elem["name"]
            unit_ip = elem["unit"][0]["family"]["inet"]["address"][0]["addr"]
            for o_elem in tvi_old_data:
              if o_elem["name"] == unit_name:
                o_unit_ip = o_elem["unit"][0]["family"]["inet"]["address"][0]["addr"]
                if o_unit_ip != unit_ip:
                  mlog.error("For New Controller={0}: tvi={1} IP={2} Old Controller={3} tvi={4} IP={5}".format(elem_new_name,
                          unit_name,unit_ip,elem_old_name, o_elem["name"], o_unit_ip))
                  err[_option] = err[_option] + 1
        else: 
          mlog.error("Controller={0}: Number of tvis={1} Old Controller={2} Number of tvis={3}".format(elem_new_name,
                        len(tvi_data), elem_old_name, len(tvi_old_data)))
          continue
        
    else: 
      mlog.error("Bad or missing Data")
      err[0] = 1
      err[1] = 1

    if err[0] > 0 or err[1] > 0 :
      mlog.error("Found {0} Errors for Controller 1 and {1} Errors for Controller 2".format(err[0], err[1]))
      mlog.warn(bcolors.OKWARN+"We can not proceed without reconciling these Errors.\n" + 
                "Typing a n (No)  will exit the program. Typing a y (Yes) will continue" + bcolors.ENDC)
      ret = yes_or_no(bcolors.OKWARN+"To Continue press y and to Exit press n: "+ bcolors.ENDC)
      if ret == 0 : sys.exit("Found Error in Controller Config")
      else: pass

# Build for the Controller. Such that it south-bound is locked
def create_controller_build( _method, _uri,_payload,resp='202',name="Controller"):
    global vnms, analy, cntlr, cust, mlog
    mlog.info("In function " + create_controller_build.__name__)
    [status, resp_str] = common.check_controller_status(name=name)
    if status == 1 and len(resp_str) > 3:
       jstr = json_loads(resp_str)
       if "syncStatus" in jstr and jstr["syncStatus"] == "IN_SYNC":
          mlog.info("Controller {0} is in sync ".format(name))
          vdict = {'body': _payload, 'resp': resp, 'method': _method, 'uri': _uri}
          common.call(vdict,content_type='json',ncs_cmd="no")
       else: 
          mlog.error ("Controller {0} is NOT in sync -- Exiting ".format(name))
          sys.exit("Controller {0} is NOT in sync -- Exiting ".format(name))
    else:
        mlog.error ("Did not get correct resp for Controller {0} is NOT in sync -- Exiting ".format(name))
        sys.exit("Did not get correct resp for Controller {0} is NOT in sync -- Exiting ".format(name))
    return 

# Deploy the Controller
def deploy_controller( _method, _uri,_payload,resp='202',name="Controller", option=0):
    global vnms, analy, cntlr, cust, mlog
    mlog.info("In function " + deploy_controller.__name__)
    vdict = {'body': _payload, 'resp': resp, 'method': _method, 'uri': _uri}
    [status, resp_str] = common.call(vdict,content_type='json', max_retry_for_task_completion=50, ncs_cmd="no")
    if status == 1:
      mlog.warn("Deploy of New Controller = {0} sucessful ".format(name))
      if len (resp_str) > 3 :
        newjstr = json_loads(resp_str)
        mlog.info("Return json from Deploy POST on Controller: {0} = {1}".format(name,json.dumps(newjstr,indent=4)))
    else:
      mlog.error("Deploy of New Controller = {0} NOT sucessful ".format(name))
      mlog.warn(bcolors.OKWARN+"We can not proceed without the Controller Deploy.\n" + 
                'You can fix the error and then refresh (type r) to try the deploy again\n' +
                "Typing a n (No)  will exit the program. Typing a y (Yes) will continue" + bcolors.ENDC)
      ret = yes_or_no(bcolors.OKWARN+"To Refresh press r, to Continue press y and to Exit press n: "+ bcolors.ENDC,1)
      if ret == 0 : sys.exit("Deploy of New Controller = {0} NOT sucessful ".format(name))
      elif ret == 1: pass
      else: 
        deploy_controller( _method, _uri,_payload,resp=resp,name=name, option=option)
    # Now we need to check the status
    mlog.warn("Checking Status of New Controller = {0}. Please be patient".format(name))
    found = 0
    rc = 1
    while rc:
      for i in range(0,5):
        time.sleep(5)
        [out,resp_str] = common.check_controller_status(name=name)
        if out == 1 and len(resp_str) > 3:
          jstr = json_loads(resp_str)
          if "syncStatus" in jstr and jstr["syncStatus"] == "IN_SYNC":                      
            mlog.warn("New Controller = {0} in Sync. ".format(name))
            found = 1
            rc = 0
            break

      if found == 0:
        mlog.warn(bcolors.OKWARN+"Controller Sync Status is not Correct.\n" + 
                  'You can fix the error and then refresh (type r) to try the deploy again\n' +
                  "Typing a n (No)  will exit the program. Typing a y (Yes) will continue" + bcolors.ENDC)
        ret = yes_or_no(bcolors.OKWARN+"To Refresh press r, to Continue press y and to Exit press n: "+ bcolors.ENDC,1)
        if ret == 0 : sys.exit("Controller not in proper state for Controller: {0}".format(name))
        elif ret == 1: rc = 0
        else: 
          pass

    mlog.warn("Finished deploying Controller: {0}". format(name))
    ret = yes_or_no2("To continue press y and to exit press n : " )
    if ret == 0 : sys.exit("Exiting")
    elif ret == 1: pass

    return 

# Get Director Release Info
def get_dir_release_info ( _method, _uri, _payload,resp='200', _name=None,_ofile=None):
    global vnms, analy, cntlr, cust, admin, mlog
    mlog.info("In function " + get_dir_release_info.__name__)
    resp2 = '202'
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': _uri}
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
        jstr = json_loads(resp_str)
        mlog.info("Release Info list = {0}".format(json.dumps(jstr,indent=4)))
        if "package-info" in jstr:
           if ("major-version" in jstr["package-info"][0] and "minor-version" in jstr["package-info"][0] 
                   and "service-version" in jstr["package-info"][0]):
               newstr =  jstr["package-info"][0]["major-version"] + "." \
                                    + jstr["package-info"][0]["minor-version"] + "." \
                                    + jstr["package-info"][0]["service-version"] 
               if newstr != glbl.vnms.data["rel"]:
                  mlog.error("Release data does not match")
                  sys.exit("Release data does not match")
               else:
                  mlog.info("Release data matches")
        elif "error" in jstr and jstr["error"]['http_status_code'] == 401 :
          mlog.error("This is most likely a password issue. Please change in input json file: vm_phase2.json and re-run")
          sys.exit("This is most likely a password issue. Please change in input json file: vm_phase2.json and re-run")
        else : 
          mlog.error("This is most likely a password issue. Please change in input json file: vm_phase2.json and re-run")
          sys.exit("This is most likely a password issue. Please change in input json file: vm_phase2.json and re-run")
    else:
        mlog.error("This is most likely a password issue. Please change in input json file: vm_phase2.json and re-run")
        sys.exit("This is most likely a password issue. Please change in input json file: vm_phase2.json and re-run")
    return ''

# Get Director Time Zone
def get_dir_time_zones ( _method, _uri, _payload,resp='200', _name=None,_ofile=None):
    global vnms, analy, cntlr, cust, mlog
    mlog.info("In function {0} with outfile={1}".format(get_dir_time_zones.__name__,_ofile))
    resp2 = '202'
    # first we delete and then create
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': "DELETE", 'uri': _uri}
    mlog.info("Deleting in {0}".format(get_dir_time_zones.__name__))
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json_loads(resp_str)
      mlog.info("Time Zone = {0}".format(json.dumps(jstr,indent=4)))
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': _uri}
    mlog.info("Creating in {0}".format(get_dir_time_zones.__name__))
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json_loads(resp_str)
      mlog.info("Timezone Info = {0}".format(json.dumps(jstr,indent=4)))
    return ''

# Get Director NTP Server
def get_dir_ntp_server ( _method, _uri, _payload,resp='200', _name=None,_ofile=None):
    global vnms, analy, cntlr, cust, mlog
    mlog.info("In function {0} with outfile={1}".format(get_dir_ntp_server.__name__,_ofile))
    resp2 = '202'
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': "DELETE", 'uri': _uri}
    mlog.info("Deleting in {0}".format(get_dir_ntp_server.__name__))
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json_loads(resp_str)
      mlog.info("NTP info = {0}".format(json.dumps(jstr,indent=4)))
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': _uri}
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json_loads(resp_str)
      mlog.info("NTP Info = {0}".format(json.dumps(jstr,indent=4)))
    return ''

# Get Director DNS Server
def get_dir_dns_server ( _method, _uri, _payload,resp='200', _name=None,_ofile=None):
    global vnms, analy, cntlr, cust, mlog
    mlog.info("In function {0} with outfile={1}".format(get_dir_dns_server.__name__,_ofile))
    resp2 = '202'
    dnspayload = {"dns": {}}
    dnspayloadstr =json.dumps(dnspayload) 
    vdict = {'body': dnspayloadstr , 'resp': resp, 'resp2': resp2, 'method': "PUT", 'uri': _uri}
    mlog.info("Deleting in {0}".format(get_dir_dns_server.__name__))
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="yes",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json_loads(resp_str)
      mlog.info("DNS Info after PUT = {0}".format(json.dumps(jstr,indent=4)))
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': _uri}
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="yes",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json_loads(resp_str)
      mlog.info("DNS Info = {0}".format(json.dumps(jstr,indent=4)))
    return ''

# this is primarily to check that New Director is NOT able to connect to Old Controller
# Do not use this function anywhere
def controller_connect(device):
    global vnms, analy, cntlr, cust, admin, auth, debug, mlog
    resp = '200'
    resp2 = '202'
    _uri = "/api/config/devices/device/" + device["name"] + "/_operations/connect"
    _payload = {}
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': "POST", 'uri': _uri }

    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if out == 1 and len(resp_str) > 3:
      jstr = json_loads(resp_str)
      if "output" in jstr and "result" in  jstr["output"] and jstr["output"]["result"] == 0: 
        mlog.warn("No connection from New Director to Old contoller: {0} -- Good! Any previous errors can be ignored ".format(device["name"]))
        return True
      else:
        return False
    else:
      mlog.warn("No connection from New Director to Old contoller: {0} -- Good! Any previous errors can be ignored ".format(device["name"]))
      return True

# Delete existing Analytics Cluster Data
def cleanup_existing_analytics_cluster():
    global vnms, analy, cntlr, cust, mlog
    mlog.info("In function {0}".format(cleanup_existing_analytics_cluster.__name__))
    resp = '200'
    resp2 = '202'
    payload1 = {}
    uri1 = '/api/config/nms/provider/analytics-cluster?deep=true&offset=0&limit=25'
    vdict = {'body': payload1, 'resp': resp, 'resp2': resp2, 'method': "GET", 'uri': uri1}
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="yes",jsonflag=1)
    if len(resp_str) > 3:
      cluster_name = []
      jstr = json_loads(resp_str)
      if "analytics-cluster" in jstr: 
        for elem in jstr["analytics-cluster"]:
          if "name" in elem: 
            newstr = {"analytics-cluster":{"name": elem["name"] }}
            uri = "/api/config/nms/provider/analytics-cluster/" + elem["name"]
            vdict = {'body': json.dumps(newstr), 'resp': resp, 'resp2': resp2, 'method': "DELETE", 'uri': uri}
            [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="yes",jsonflag=1)

        
# Gets the controller configi. This takes long
def get_controller_config( _method, _uri, _payload,resp='200', vd_data=None,option=0,_name=None,_ofile=None):
    global vnms, analy, cntlr, cust, mlog

    resp2='202'
    cntlr_name = glbl.cntlr.data['new_cntlr'][option]["controllerName"]
    mlog.warn("Getting Controller Config for New Controller={0}. Please be patient".format(cntlr_name))
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method':_method , 'uri': _uri,
            'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
            'auth': vd_data['auth'] }
    [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json_loads(resp_str)
      scrub_list = [ "clear", "crypto", "diagnostics", "debug", "operations", "snmp", "redundancy", "networks",  "alarms", "ntp" , "predefined", "security", "elastic-policies", "service-node-groups", "system", "erase","guest-vnfs" ] 

      for i in scrub_list:
        common.scrub(jstr,i)
      write_controller_config(glbl.cntlr,"new_cntlr",option,jstr)

# Write the Controller Config to file.  In this file ONLY the New controller data is written
def write_controller_config(_cntlr,name,cntlr_num,jstr):
    global vnms, analy, cntlr, cust, admin, mlog
    fname ="cntlr_config.json"
    old_jstr = None
    mlog.info("In function {0} : Output file:{1}".format(write_controller_config.__name__,fname))
    if os.path.exists(fname): 
      fp = open(fname,"r")
      old_config = fp.read()
      fp.close()
      old_jstr = json_loads(old_config,object_pairs_hook=OrderedDict)

      if name in old_jstr["Controller"]:
        if len(old_jstr["Controller"][name]) >= cntlr_num : 
          old_jstr["Controller"][name][cntlr_num]["configuration"] = {}
          old_jstr["Controller"][name][cntlr_num]["configuration"] = jstr
        else: 
          old_jstr["Controller"][name].append(copy.deepcopy(_cntlr.data[name][cntlr_num]))
          old_jstr["Controller"][name][cntlr_num]["configuration"] = {}
          old_jstr["Controller"][name][cntlr_num]["configuration"] = jstr
      
      fin=open(fname, "w+")
      mstr1 = json.dumps(old_jstr, indent=4)
      fin.write(mstr1)
      fin.close()
    
    
# Push the NMS provider Information. Care is taken to delete the Old Analytics Cluster Information
def set_nms_provider( _method, _uri, _payload,resp='200', _name=None,_ofile=None):
    global vnms, analy, cntlr, cust, mlog
    mlog.info("In function {0} with outfile={1}".format(set_nms_provider.__name__,_ofile))
    resp2 = '202'
    # before we do this step lets delete the default auth connector
    mlog.info("In function {0} Deleting default auth-connector".format(set_nms_provider.__name__))
    payload1 = {}
    uri1 = '/api/config/nms/provider/default-auth-connector'
    vdict = {'body': payload1, 'resp': resp, 'resp2': resp2, 'method': "DELETE", 'uri': uri1}
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="yes",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json_loads(resp_str)
      mlog.info("NMS Info after DELETE = {0}".format(json.dumps(jstr,indent=4)))

    cleanup_existing_analytics_cluster()
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': _uri}
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="yes",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json_loads(resp_str)
      mlog.info("NMS Info after PUT = {0}".format(json.dumps(jstr,indent=4)))
    # Now we copy the Analytics Cluster configuration from the _payload into the global structure and save
    jstr = json_loads(_payload)
    if "provider" in jstr and "analytics-cluster" in jstr["provider"]:
      glbl.analy.data = jstr["provider"]["analytics-cluster"]
      mlog.info("Writing Analytics Cluster Info")
      write_outfile(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin)
    return ''

'''
# get dir analytics cluster
def get_dir_analytics_cluster ( _method, _uri, _payload,resp='200', _name=None,_ofile=None):
    global vnms, analy, cntlr, cust, mlog
    mlog.info("In function {0} with outfile={1}".format(get_dir_analytics_cluster.__name__,_ofile))
    resp2 = '202'
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': "DELETE", 'uri': _uri}
    mlog.info("Deleting in {0}".format(get_dir_analytics_cluster.__name__))
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json_loads(resp_str)
      mlog.info("Analytic Cluster ater DELETE = {0}".format(json.dumps(jstr,indent=4)))
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': _uri}
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json_loads(resp_str)
      mlog.info("Analytic Cluster = {0}".format(json.dumps(jstr,indent=4)))
    return ''
'''

'''
def get_dir_auth_connector ( _method, _uri, _payload,resp='200', _name=None,_ofile=None):
    global vnms, analy, cntlr, cust, mlog
    mlog.info("In function {0} with outfile={1}".format(get_dir_auth_connector.__name__,_ofile))
    resp2 = '202'
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': "DELETE", 'uri': _uri}
    mlog.info("Deleting in {0}".format(get_dir_auth_connector.__name__))
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json_loads(resp_str)
      pprint(jstr)
    mlog.info("Create in {0}".format(get_dir_auth_connector.__name__))
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': _uri}
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json_loads(resp_str)
      pprint(jstr)
    return ''

'''

'''
def get_dir_default_auth_connector ( _method, _uri, _payload,resp='200', _name=None,_ofile=None):
    global vnms, analy, cntlr, cust, mlog
    mlog.info("In function {0} with outfile={1}".format(get_dir_default_auth_connector.__name__,_ofile))
    resp2 = '202'
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': _uri}
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json_loads(resp_str)
      pprint(jstr)
    return ''

'''
'''
def get_dir_auth_connector_config ( _method, _uri, _payload,resp='200', _name=None,_ofile=None):
    global vnms, analy, cntlr, cust, mlog
    mlog.info("In function {0} with outfile={1}".format(get_dir_auth_connector_config.__name__,_ofile))
    resp2 = '202'
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': _uri}
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json_loads(resp_str)
      pprint(jstr)
    return ''
'''

# Deploy Org Workflow
def deploy_org_workflow( _method, _uri, _payload,resp='200', name=None,_ofile=None):
    global vnms, analy, cntlr, cust, mlog
    mlog.warn("Deploying Org Workflow. Please be patient.")
    resp2 = '202'
    if name is None:
      mlog.error("Can not continue without Customer Name ")
      sys.exit("Can not continue without Customer Name ")
    payload1 = {}
    #mlog.info("In function {0} calling Get ".format(deploy_org_workflow.__name__))
    vdict = {'body': payload1, 'resp': resp, 'resp2': resp2, 'method': "GET", 'uri': _uri}
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",max_retry_for_task_completion=50,jsonflag=1)
    #if out == 1:
    #  mlog.warn("Deploy of org workflow successful")
    if len(resp_str) > 3:
      jstr = json_loads(resp_str)
      orig_jstr = json_loads(_payload)
      if "versanms.sdwan-org-workflow" in jstr:
         # we need to copy the controller and the Analytics data from newdir to olddir
         # and not the reverse way
         if "controllers" in orig_jstr["versanms.sdwan-org-workflow"]:
           jstr["versanms.sdwan-org-workflow"]["controllers"] = []
           jstr["versanms.sdwan-org-workflow"]["controllers"] = orig_jstr["versanms.sdwan-org-workflow"]["controllers"]
         else:
           mlog.error("No controller information -- can not continue. In function {0}".format(deploy_org_workflow.__name__))
           sys.exit("No controller information -- can not continue. In function {0}".format(deploy_org_workflow.__name__))
         if "analyticsClusters" in orig_jstr["versanms.sdwan-org-workflow"]:
           jstr["versanms.sdwan-org-workflow"]["analyticsClusters"] = []
           jstr["versanms.sdwan-org-workflow"]["analyticsClusters"] = orig_jstr["versanms.sdwan-org-workflow"]["analyticsClusters"]
         else:
           mlog.error("No Analytics information -- can not continue. In function {0}".format(deploy_org_workflow.__name__))
           sys.exit("No Analytics information -- can not continue. In function {0}".format(deploy_org_workflow.__name__))
         _newpayload = json.dumps(jstr) 
         vdict = {'body': _newpayload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': _uri}
         mlog.info("In function {0} calling PUT ".format(deploy_org_workflow.__name__))
         [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
         if len(resp_str) > 3:
            jstr = json_loads(resp_str)
            pprint(jstr)
         _newuri = '/vnms/sdwan/workflow/orgs/org/deploy/' + name
         vdict = {'body': _newpayload, 'resp': resp, 'resp2': resp2, 'method': "POST" , 'uri': _newuri}
         mlog.info("In function {0} calling POST ".format(deploy_org_workflow.__name__))
         [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
         if len(resp_str) > 3:
            jstr = json_loads(resp_str)
            #pprint(jstr)
          
      mlog.warn("Getting New Controller Config. Please be patient.")
      i=0
      for _elem in glbl.cntlr.data['new_cntlr']:
        _method = "GET"
        uri="/api/config/devices/device/" + _elem["controllerName"] + "/config?deep"
        _payload = {}
        get_controller_config( _method, uri, _payload,resp='200',vd_data=newdir, option=i, _name="new_cntlr",_ofile=None)
        if i == 1: check_controller_config()
        i= i + 1

    return ''
   
'''
# Get the sdwan Workflow list from New Director
def get_sdwan_workflow_list( _method, _uri, _payload,resp='200', _ofile=None):
    global vnms, analy, cntlr, cust, mlog
    resp2 = '202'
    mlog.info("In function {0} ".format(get_sdwan_workflow_list.__name__))
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': _uri}
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if out == 1 and len(resp_str) > 3:
      jstr = json_loads(resp_str)
      if "versanms.sdwan-controller-list" in jstr:
        if len(jstr["versanms.sdwan-controller-list"]) == 0 or len(jstr["versanms.sdwan-controller-list"]) > 2 :
            mlog.error("Number of Controllers bad = {0} in return .. exiting".format(len(jstr["versanms.sdwan-controller-list"])))
            sys.exit("Number of Controllers bad = {0} in return .. exiting".format(len(jstr["versanms.sdwan-controller-list"])))
        else:
           glbl.cntlr.data['new_cntlr'].append( jstr["versanms.sdwan-controller-list"][0])
           glbl.cntlr.data['new_cntlr'].append( jstr["versanms.sdwan-controller-list"][1])
           #if debug : pprint(glbl.cntlr.data)
           write_outfile(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin)
    return ''
'''

# Find out if template is for a device onboarded to HCN. Must have no controllers present
def is_template_for_hcn(dev):
    resp = '200'
    resp2 = '202'
    _payload = {}
    if "onboard_to_hcn" in dev and dev["onboard_to_hcn"] == 1:
      return True
    _uri = "/api/config/devices/template/" +  dev["poststaging-template"] + "/config/orgs/org/" + glbl.cust.data["custName"] + "/sd-wan/controllers/controller"
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': "GET", 'uri': _uri}
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if out == 1 and len(resp_str) > 3:
      jstr = json_loads(resp_str)
      if "controller" in jstr:
        cntlr_list_old = [glbl.cntlr.data['old_cntlr'][0]["controllerName"], glbl.cntlr.data['old_cntlr'][1]["controllerName"]]
        cntlr_list_new = [glbl.cntlr.data['new_cntlr'][0]["controllerName"], glbl.cntlr.data['new_cntlr'][1]["controllerName"]]
        # Check if this is true or false
        found = 0
        for elem in jstr["controller"]: 
          if (elem["name"] != cntlr_list_old[0] and elem["name"] != cntlr_list_old[1] and 
                elem["name"] != cntlr_list_new[0] and elem["name"] != cntlr_list_new[1]):
            found = found + 1

        if found > 0:
          mlog.warn("Template {0} is for Hub Controller".format(dev["poststaging-template"]))
          dev["onboard_to_hcn"] = 1
          return True

        dev["onboard_to_hcn"] = 0
        return False


# deploy template for a device onboarded to hcn. Notice that the controller section is missing. Recreates back the template
def  deploy_template_workflow_device_onb_to_hcn(dev):
      global vnms, analy, cntlr, cust, mlog
      mlog.warn("Deploying Template Workflow for: {0}".format(dev["poststaging-template"]))
      # determine if the template used for this device is actually for hcn
      resp = '200'
      resp2 = '202'
      _payload = {}
      _uri = "/vnms/sdwan/workflow/templates/template/" +  dev["poststaging-template"]
      vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': "GET", 'uri': _uri}
      [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
      if out == 1 and len(resp_str) > 3:
        jstr = json_loads(resp_str)
        if "versanms.sdwan-template-workflow" in jstr and "templateName" in  jstr["versanms.sdwan-template-workflow"]:
          if dev["poststaging-template"] not in jstr["versanms.sdwan-template-workflow"]["templateName"]:
            mlog.warn("This is a HA template with template={0} with template={1}".format(dev["poststaging-template"],jstr["versanms.sdwan-template-workflow"]["templateName"]))
            dev["template_deployed"] = "1"
            write_outfile(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin)
            return True
        if "versanms.sdwan-template-workflow" in jstr: 
          if "analyticsCluster" in jstr["versanms.sdwan-template-workflow"] and len(jstr["versanms.sdwan-template-workflow"]["analyticsCluster"]) > 0: 
            if len(glbl.analy.data)  > 0:
              mlog.info("Changing Analytics Cluster data for template={0} to {1}".format(dev["poststaging-template"],glbl.analy.data[0]["name"]))
              jstr["versanms.sdwan-template-workflow"]["analyticsCluster"] = glbl.analy.data[0]["name"]
          _payload = json.dumps(jstr)
          _uri = "/vnms/sdwan/workflow/templates/template/" + dev["poststaging-template"]
          vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': "PUT", 'uri': _uri}
          [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
          if out == 0:
            mlog.error("Workflow template PUT deploy = {0} was NOT successful".format(dev["poststaging-template"]))
            dev["template_deployed"] = "0"
            if "redundantPair" in jstr["versanms.sdwan-template-workflow"]:
              dev["redundantPair_templ"] = jstr["versanms.sdwan-template-workflow"]["redundantPair"]["templateName"]
            write_outfile(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin)
            return False
          # Now the deploy
          #if template_manipulation(dev):
          get_vnf_manager(dev)
          return re_create_template(dev)
          # Here we will not do a clean and recreate but just recreate
      else: 
        # the template for a paired device 
        # will need to figure out how to deal with these
        mlog.info("Deploy Template Workflow = {0} was not successful".format(dev["poststaging-template"]))
        dev["template_deployed"] = "0"
        write_outfile(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin)
        return False
      return True



# deploy template for a device Not onboarded to hcn. Adds the New controller section. Recreates back the template
def  deploy_template_workflow(dev):
      global vnms, analy, cntlr, cust, mlog

      if "poststaging-template" not in dev:
        mlog.warn("Post staging template not in device={0}. Please check your input json file".format(dev["name"]))
        return False
      mlog.warn("Deploying Template Workflow for: {0}".format(dev["poststaging-template"]))
      # determine if the template used for this device is actually for hcn
      if dev["type"] == "branch" :
        ret = is_template_for_hcn(dev)
        if ret: 
          return deploy_template_workflow_device_onb_to_hcn(dev)
          #dev["template_deployed"] = "1" # We fake that template deploy is done
          #return True # This is a template for the HCN

      resp = '200'
      resp2 = '202'
      _payload = {}
      _uri = "/vnms/sdwan/workflow/templates/template/" +  dev["poststaging-template"]
      vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': "GET", 'uri': _uri}
      [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
      if out == 1 and len(resp_str) > 3:
        jstr = json_loads(resp_str)
        if "versanms.sdwan-template-workflow" in jstr and "templateName" in  jstr["versanms.sdwan-template-workflow"]:
          if dev["poststaging-template"] not in jstr["versanms.sdwan-template-workflow"]["templateName"]:
            mlog.warn("This is a HA template with template={0} with template={1}".format(dev["poststaging-template"],jstr["versanms.sdwan-template-workflow"]["templateName"]))
            dev["template_deployed"] = "1"
            write_outfile(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin)
            return True
        if "versanms.sdwan-template-workflow" in jstr and "controllers" in  jstr["versanms.sdwan-template-workflow"]:
          cntlr_list = [glbl.cntlr.data['new_cntlr'][0]["controllerName"], glbl.cntlr.data['new_cntlr'][1]["controllerName"]]
          jstr["versanms.sdwan-template-workflow"]["controllers"]= cntlr_list 
          if "analyticsCluster" in jstr["versanms.sdwan-template-workflow"] and len(jstr["versanms.sdwan-template-workflow"]["analyticsCluster"]) > 0: 
            if len(glbl.analy.data)  > 0:
              mlog.info("Changing Analytics Cluster data for template={0} to {1}".format(dev["poststaging-template"],glbl.analy.data[0]["name"]))
              jstr["versanms.sdwan-template-workflow"]["analyticsCluster"] = glbl.analy.data[0]["name"]
          _payload = json.dumps(jstr)
          _uri = "/vnms/sdwan/workflow/templates/template/" + dev["poststaging-template"]
          vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': "PUT", 'uri': _uri}
          [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
          if out == 0:
            mlog.error("Workflow template PUT deploy = {0} was NOT successful".format(dev["poststaging-template"]))
            dev["template_deployed"] = "0"
            if "redundantPair" in jstr["versanms.sdwan-template-workflow"]:
              dev["redundantPair_templ"] = jstr["versanms.sdwan-template-workflow"]["redundantPair"]["templateName"]
            write_outfile(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin)
            return False
          # Now the deploy
          #if template_manipulation(dev):
          get_vnf_manager(dev)
          return re_create_template(dev)
          # Here we will not do a clean and recreate but just recreate
      else: 
        # the template for a paired device 
        # will need to figure out how to deal with these
        mlog.info("Deploy Template Workflow = {0} was not successful".format(dev["poststaging-template"]))
        dev["template_deployed"] = "0"
        write_outfile(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin)
        return False
      return True

# Gets and replace the VNF Manager for the template
def get_vnf_manager(device):
    global vnms, analy, cntlr, cust, mlog

    if device is None: 
      mlog.error("Bad inputs in function {0}. Input File is None ".format(get_vnf_manager.__name__))
      return

    mlog.info("In function {0} with device = {1} ".format(get_vnf_manager.__name__, device["name"]))
    resp = '200'
    resp2 = '202'
    _uri =  "/api/config/devices/template/" + device["poststaging-template"] + "/config/system/vnf-manager"
    _payload = {}
    vdict = {'body': _payload , 'resp': resp, 'resp2': resp2, 'method': "GET", 'uri': _uri}
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if out == 1 and len(resp_str) > 3:
      south_ip = [i['director_southIP'] + "/32" for i in glbl.vnms.data['director']]
      domain_ips = glbl.vnms.data['domain_ips']
      #print("S IP = " + " ".join(south_ip))
      jstr = json_loads(resp_str)
      #mlog.info("VNF Manager Info = {0}".format(json.dumps(jstr,indent=4)))
      if "vnf-manager" in jstr and "ip-addresses" in jstr["vnf-manager"]:
        #x= jstr["vnf-manager"]["ip-addresses"] + south_ip 
        jstr["vnf-manager"]["ip-addresses"] = []
        jstr["vnf-manager"]["ip-addresses"] = south_ip + domain_ips
        del jstr["vnf-manager"]["vnf-manager"]
        payload = json.dumps(jstr)
        vdict = {'body': payload , 'resp': resp, 'resp2': resp2, 'method': "PUT", 'uri': _uri}
        [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
        if len(resp_str) > 3:
          jstr = json_loads(resp_str)
          mlog.info("VNF Manager after PUT = {0}".format(json.dumps(jstr,indent=4)))
    return ''

# Decrypts the keys for the New director. Checks to see that release is 21.2 or len > 100. Otherwise it returns the same data
def decrypt_new_key(_data):
    resp = '200'
    resp2 = '202'
    if len(_data) < 100 or glbl.vnms.data["rel"].find("21.2") == -1 :
      return _data

    _uri = "/vnms/operations/encryption/decrypt"
    _payload = { "cipherText": _data }
    # All done on New Dir
    vdict = {'body': json.dumps(_payload), 'resp': '200', 'resp2': resp2, 'method':"POST", 'uri': _uri,
            'vd_ip' :  newdir['vd_ip'], 'vd_rest_port': newdir['vd_rest_port'],
            'auth': newdir['auth'] }
    [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if out == 1 and len(resp_str) > 3:
      return resp_str
    else:
      mlog.error("Decryption failed for Old Director Failed for Data={0}".format(_data))
      return None

# Decrypts the keys for the Old director. Checks to see that release is 21.2 or len > 100. Otherwise it returns the same data
def decrypt_old_key(_data):
    resp = '200'
    resp2 = '202'
    if len(_data) < 100 or glbl.vnms.data["rel"].find("21.2") == -1 :
      return _data

    _uri = "/vnms/operations/encryption/decrypt"
    _payload = { "cipherText": _data }
    # All done on Old Dir
    vdict = {'body': json.dumps(_payload), 'resp': '200', 'resp2': resp2, 'method':"POST", 'uri': _uri,
            'vd_ip' :  olddir['vd_ip'], 'vd_rest_port': olddir['vd_rest_port'],
            'auth': olddir['auth'] }
    [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if out == 1 and len(resp_str) > 3:
      return resp_str
    else:
      mlog.error("Decryption failed for Old Director Failed for Data={0}".format(_data))
      return None

    
# Decrypts the keys for the New director.
def  decrypt_key(dev):
    resp = '200'
    resp2 = '202'
    vdict = {}
    _uri = "/vnms/operations/encryption/decrypt"

    if "local_auth_key" in dev and len(dev["local_auth_key"]) > 100:
      _payload = { "cipherText": dev["local_auth_key"] }
      vdict = {'body': json.dumps(_payload) , 'resp': resp, 'resp2': resp2, 'method': "POST", 'uri': _uri}
      [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
      if out == 1 and len(resp_str) > 3:
        mlog.info("Device={0} local_auth_key={1} replaced by  Decryted Response={2}".format(dev["name"],dev["local_auth_key"],resp_str))
        dev["local_auth_key"] = resp_str
      else:
        mlog.error("Failed for local_auth key ")

    if "local1_auth_key" in dev and len(dev["local1_auth_key"]) > 100:
      _payload = { "cipherText": dev["local1_auth_key"] }
      vdict = {'body': json.dumps(_payload) , 'resp': resp, 'resp2': resp2, 'method': "POST", 'uri': _uri}
      [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
      if out == 1 and len(resp_str) > 3:
        mlog.info("Device={0} local1_auth_key={1} replaced by  Decryted Response={2}".format(dev["name"],dev["local1_auth_key"],resp_str))
        dev["local1_auth_key"] = resp_str
      else:
        mlog.error("Failed for local1_auth key ")

'''
# Deploy device workflow for devices onboarded to HCN. May not be used
def  deploy_device_workflow_for_hcn(dev):

      resp = '200'
      resp2 = '202'
      _uri = "/vnms/sdwan/workflow/devices/device/" + dev["name"]
      _payload = {}
      vdict = {'body': _payload , 'resp': resp, 'resp2': resp2, 'method': "GET", 'uri': _uri}
      [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
      if out == 1 and len(resp_str) > 3:
        jstr = json_loads(resp_str)
        a = jstr['versanms.sdwan-device-workflow']['postStagingTemplateInfo']['templateData']['device-template-variable']['variable-binding']['attrs']
        for elem in a:
          if "name" in elem and elem["name"].find("IKELKey") != -1 :
            a = decrypt_old_key(elem["value"])
            if a is not None:
              elem["value"] = a
            else:
              mlog.error("Error could not decrypt for Key={0}".format(elem["name"]))


        # Now it is time to push the data
        vdict = {'body': resp_str , 'resp': resp, 'resp2': resp2, 'method': "PUT", 'uri': _uri}
        [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
        if out == 1:
          mlog.info("Deploy Device Workflow PUT was successful for device: {0}".format(dev["name"]))
          # we can not deploy the device workflow because the hub controllers are not alive on the New director
        return
'''

# Deploy device workflow for devices
def  deploy_device_workflow(dev):

      mlog.warn("Deploy Device Workflow for device: {0}".format(dev["name"]))
      if dev["template_deployed"] == "0": 
        mlog.error("Deploy Device Workflow can not be done since template deploy failed for device: {0}".format(dev["name"]))
        return False 

      resp = '200'
      resp2 = '202'
      _uri = "/vnms/sdwan/workflow/devices/device/" + dev["name"]
      _payload = {}
      vdict = {'body': _payload , 'resp': resp, 'resp2': resp2, 'method': "GET", 'uri': _uri}
      [ret, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
      if ret == 1:
        mlog.info("GET to device succeeded Device={0}".format(dev["name"]))
        jstr = json_loads(resp_str)

        vdict = {'body': json.dumps(jstr) , 'resp': resp, 'resp2': resp2, 'method': "PUT", 'uri': _uri}
        [ret, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
        if ret == 1 and dev["onboard_to_hcn"] != 1: 
          mlog.info("Deploy Device Workflow PUT was successful for device: {0}".format(dev["name"]))
          time.sleep(10)
          _uri = "/vnms/sdwan/workflow/devices/device/deploy/" + dev["name"]
          _payload = {}
          vdict = {'body': _payload , 'resp': resp, 'resp2': resp2, 'method': "POST", 'uri': _uri}
          [ret, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
          if ret == 1: 
            # NOW we need to do a GET and save details to the device
            _uri = "/vnms/sdwan/workflow/devices/device/" + dev["name"]
            _payload = {}
            vdict = {'body': _payload , 'resp': resp, 'resp2': resp2, 'method': "GET", 'uri': _uri}
            [ret, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
            if ret == 1  and len(resp_str) > 3:
              jstr = json_loads(resp_str)
              a = jstr['versanms.sdwan-device-workflow']['postStagingTemplateInfo']['templateData']['device-template-variable']['variable-binding']['attrs']
              new_cntlr_names = list(map(lambda x: x['name'], glbl.cntlr.data['new_cntlr']))
              for val in a:
                if "value" in val and val["name"].find("Key") != -1 :
                  if val["name"].find(new_cntlr_names[0]) == -1 and val["name"].find(new_cntlr_names[1]) == -1:
                    mlog.info("Not Controller Device={0} Name={1} Value={2}".format(dev["name"],val["name"],val["value"]))
                    # Not for cntlr -- must be site to site ipsec
                    # Not making any changes here -- maybe later
                  elif val["name"].find(new_cntlr_names[0]) != -1:
                    # For controller 1
                    _data = decrypt_new_key(val["value"])
                    #data2 = decrypt_new_key(val["value"])
                    if _data is not None:
                      dev["local1_auth_key"] = _data
                      mlog.info("Device={0}: local1_auth_key={1}".format(dev["name"],dev["local1_auth_key"]))

                  elif val["name"].find(new_cntlr_names[1]) != -1:
                    # For controller 2
                    _data = decrypt_new_key(val["value"])
                    #_data2 = decrypt_new_key(val["value"])
                    if _data is not None:
                      dev["local_auth_key"] = _data
                      mlog.info("Device={0}: local_auth_key={1}".format(dev["name"],dev["local_auth_key"]))

                elif "value" in val and val["name"].find("IKELIdentifier") != -1 :
                  if val["name"].find(new_cntlr_names[0]) == -1 and val["name"].find(new_cntlr_names[1]) == -1:
                    mlog.info("Not Controller Device={0} Name={1} Value={2}".format(dev["name"],val["name"],val["value"]))
                    # Not for cntlr -- must be site to site ipsec
                    # Not making any changes here -- maybe later
                  elif val["name"].find(new_cntlr_names[0]) != -1:
                    # For controller 1
                    dev["local1_auth_identity"] = val["value"]
                    dev["remote1_auth_identity"] = glbl.cntlr.data['new_cntlr'][0]["controllerName"] + '@' +  glbl.cust.data["custName"] + '.com' 
                    mlog.info("Device={0}: local1_auth_identity={1} remote1_auth_identity={2}".format(dev["name"],dev["local1_auth_identity"],dev["remote1_auth_identity"]))

                  elif val["name"].find(new_cntlr_names[1]) != -1:
                    # For controller 2
                    dev["local_auth_identity"] = val["value"]
                    dev["remote_auth_identity"] = glbl.cntlr.data['new_cntlr'][1]["controllerName"] + '@' +  glbl.cust.data["custName"] + '.com' 
                    mlog.info("Device={0}: local_auth_identity={1} remote_auth_identity={2}".format(dev["name"],dev["local_auth_identity"],dev["remote_auth_identity"]))
            mlog.warn("Deploy Device Workflow for device: {0} was sucessful".format(dev["name"]))
            dev["deployed"] = "1"
            write_outfile(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin)
            return True
        elif dev["onboard_to_hcn"] == 1 and ret == 1: 
          mlog.warn("Deploy Device Workflow for device: {0} was partly sucessful since device onboarded to Hub Controller".format(dev["name"]))
          dev["deployed"] = "1"
          write_outfile(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin)
          return True
        else: 
          mlog.error("Deploy Device Workflow PUT was NOT successful for device: {0}".format(dev["name"]))
          dev["deployed"] = "0"
          write_outfile(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin)
          return False
      else: 
        mlog.error("Deploy Device Workflow GET was NOT successful for device: {0}".format(dev["name"]))
        dev["deployed"] = "0"
        write_outfile(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin)
        return False

     
# Gets the Device Group in case we are re-running. Only those devices are used 
def get_device_group_new( _method, _uri, _payload,resp='200', _name=None,_ofile=None, option=0):
    global vnms, analy, cntlr, cust, mlog
    resp2 = '202'
    vdict = {}
    mlog.info("In function {0} ".format(get_device_group_new.__name__))
    count = 0
    totalcnt = -1

    template_errorlist = list(filter(lambda x: ("template_deployed" not in x) or  ("template_deployed" in x and x['template_deployed'] != "1"), glbl.vnms.data["devices"]))
    if len(template_errorlist) > 0:
      workflow_template_list = []
      for dev in template_errorlist:
        if dev["poststaging-template"] not in workflow_template_list:
          if deploy_template_workflow(dev) :
            workflow_template_list.append(dev["poststaging-template"])

    errorlist = list(filter(lambda x: ("deployed" not in x) or  ("deployed" in x and x['deployed'] != "1"), glbl.vnms.data["devices"]))
    found = 0
    while 1:
      newuri = _uri + "&offset={0}&limit=25".format(count) 
      vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': newuri}
      [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
      if out == 1 and len(resp_str) > 3:
        jstr = json_loads(resp_str)
        if count == 0 and totalcnt == -1:
          if "totalCount" in jstr: totalcnt = int(jstr["totalCount"])
          else: sys.exit("did not get totalCount")
        if "device-group" in jstr:
          for i in range(len(jstr["device-group"])):
            if ("inventory-name" in jstr["device-group"][i] and "poststaging-template" in jstr["device-group"][i] and 
                 len(jstr["device-group"][i]["inventory-name"]) > 0 ) : 
              for devname in jstr["device-group"][i]["inventory-name"]:
                for j in range( len( errorlist)):
                  if devname == errorlist[j]["name"]:
                    mlog.info("Found device in list {0} ".format(devname))
                    found = found + 1
                    
        if totalcnt <= (count + 25): break
        else: count = count + 25
    # Now we need to  a) delete the devices that do not have a post-staging template
    # b) deploy the device templates with the Controller info
    #if found != len(errorlist):
    #  mlog.warn("Found {0:d} devices while we should have {1:d} in such a state".format(found,len(errorlist)))
    #  sys.exit("Found {0:d} devices while we should have {1:d} in such a state".format(found,len(errorlist)))

    # for each of the devices call the template workflow and the device workflow
    for dev in errorlist:
      deploy_device_workflow(dev)

    write_outfile(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin)
    return ''
    
# Initialize the Device data
def init_device_data(_dev, jstr, i, found=1):
    if found == 1:
      if "poststaging-template" not in _dev:
        _dev["poststaging-template"] = jstr["device-group"][i]["poststaging-template"]
      if "dg-group" not in _dev:
        _dev["dg-group"] = jstr["device-group"][i]["name"]
      if "deployed" not in _dev: 
       _dev["deployed"] = "0"
      if "template_deployed" not in _dev:
        _dev["template_deployed"] = "0"
      if "onboard_to_hcn" not in _dev:
        _dev["onboard_to_hcn"] = 0
    else:
      a = {}
      a["name"] = jstr["device-group"][i]["inventory-name"]
      a["poststaging-template"] =  jstr["device-group"][i]["poststaging-template"]
      a["dg-group"] =  jstr["device-group"][i]["name"]
      a["deployed"] =  "0"
      a["template_deployed"] = "0"
      a["onboard_to_hcn"] = 0
      glbl.vnms.data['devices'].append(a) 

    write_outfile(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin)
        
     
# Gets the Device Group 
def get_device_group( _method, _uri, _payload,resp='200', _name=None,_ofile=None, option=0):
    global vnms, analy, cntlr, cust, mlog
    resp2 = '202'
    vdict = {}
    mlog.info("In function {0} ".format(get_device_group.__name__))

    count = 0
    totalcnt = -1
    while 1:
      newuri = _uri + "&offset={0}&limit=25".format(count) 
      vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': newuri}
      [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
      if out == 1 and len(resp_str) > 3:
        jstr = json_loads(resp_str)
        if count == 0 and totalcnt == -1:
          if "totalCount" in jstr: totalcnt = int(jstr["totalCount"])
          else: sys.exit("did not get totalCount")
        if "device-group" in jstr:
          if len(jstr["device-group"]) <= 0 : 
            sys.exit("Got 0 devices in device group")
          for i in range(len(jstr["device-group"])):
            if ("inventory-name" in jstr["device-group"][i] and "poststaging-template" in jstr["device-group"][i] and 
                 len(jstr["device-group"][i]["inventory-name"]) > 0 ) : 
              for devname in jstr["device-group"][i]["inventory-name"]:
                for j in range( len(glbl.vnms.data['devices'])):
                  if devname == glbl.vnms.data['devices'][j]["name"]:
                    mlog.info("Found device in list {0} ".format(devname))
                    dev = glbl.vnms.data['devices'][j]
                    init_device_data(dev, jstr, i, found=1)
                    found = 1
                if found == 0:
                  mlog.warn("Device={0} not found in the list adding now".format(devname))
                  init_device_data(dev, jstr, i, found=0)
                    
        if totalcnt <= (count + 25): break
        else: count = count + 25
    # Now we need to  a) delete the devices that do not have a post-staging template
    # b) deploy the device templates with the Controller info
    newdevice = []
    for dev in glbl.vnms.data['devices']:
      if "poststaging-template" not in dev or "deployed" not in dev:
         mlog.warn("Skipping Device={0} from the list because post-staging template was not found or device not in proper state".format(dev["name"]))
         glbl.vnms.data['devices'].remove(dev)

    # write all the data that we have 
    write_outfile(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin)

    # We should have already determined using get_existing_controller() whether we have hubcontrollers in the system or not 
    is_hub_cntlr_present()
    
    # for each of the devices call the template workflow and the device workflow
    # option = 0 : deploy_template_workflow followed by deploy_device_workflow
    # option = 1 : deploy_template_workflow for all devices followed by deploy_device_workflow for all devices
    workflow_template_list = []
    for dev in glbl.vnms.data['devices']:
      if dev["poststaging-template"] not in workflow_template_list:
        if deploy_template_workflow(dev) :
          workflow_template_list.append(dev["poststaging-template"])

    for dev in glbl.vnms.data['devices']:
      deploy_device_workflow(dev)

    write_outfile(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin)
    return ''
    
# Checks to dee if Hub Controllers are Present
def is_hub_cntlr_present():
    global vnms, analy, cntlr, cust, mlog
    c = glbl.vnms.data.get('hub_cntlr_present', None)
    if c is not None:
      return c
    # the dict itself does not exist we need to get the appliance summary again to determine. Return None for now
    return None 

# Get Parent OrgId
def get_parent_orgid( _method, _uri, _payload,resp='200',_name=None, _ofile=None):
    global vnms, analy, cntlr, cust, mlog
    resp2 = '202'
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': _uri}
    mlog.info("In function {0} with outfile={1}".format(get_parent_orgid.__name__,_ofile))
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if out == 1 and len(resp_str) > 3:
      jstr = json_loads(resp_str)
      if 'uuid' in jstr:
        glbl.vnms.data['parentOrgId'] = jstr['uuid']
        write_outfile(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin)
      else:
        mlog.error("Could not get parent Org UUID")
    else: 
      mlog.error("Could not get parent Org UUID")
    return ''

# Get Controller workflow
def get_controller_workflow( _method, _uri, _payload,resp='200', _ofile=None):
    global vnms, analy, cntlr, cust, mlog
    resp2 = '202'
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': _uri}
    mlog.info("In function {0} with outfile={1}".format(get_controller_workflow.__name__,_ofile))
    if _ofile is None: 
       mlog.error("No file provided .. exiting")
       sys.exit("No file provided .. exiting")
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no")
    if out == 1 and len(resp_str) > 3:
      jstr = json_loads(resp_str)
      out = common.create_out_data("POST","200","/vnms/sdwan/workflow/controllers/controller", jstr)
      fp=open(_ofile,"w+")
      out1 = json.dumps(out, indent=4)
      fp.write(out1)
      fp.close()
    return ''

# Delete Controller workflow. First checks to see it is really present or not 
def delete_controller_workflow(_name ):
    resp2 = '404'
    _uri = '/vnms/sdwan/workflow/controllers/controller/' + _name
    _payload = {}
    # First check if it exists NOT
    mlog.info("In function {0} ".format(delete_controller_workflow.__name__))
    vdict = {'body': _payload , 'resp': '200', 'resp2': resp2, 'method': "GET", 'uri': _uri}
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="yes")
    if out == 1 and len(resp_str) > 3:
      vdict = {'body': _payload , 'resp': '200', 'resp2': '202', 'method': "DELETE", 'uri': _uri}
      [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="yes")
      if out == 1 and len(resp_str) > 3:
        jstr = json_loads(resp_str)
    return 

# Delete Controller using its UUID
def delete_controller_by_uuid( _uuid ):
    resp2 = '202'
    _uri = '/api/config/nms/actions/_operations/delete-appliance'
    _payload = {}
    _payload = { "delete-appliance": {"applianceuuid": "%s" % str(_uuid),
                 "clean-config": "false", 
                 "reset-config": "false", 
                 "load-defaults": "false" }}
    a=json.dumps(_payload)
    #np = json_loads(a)
    mlog.info("In function {0} ".format(delete_controller_by_uuid.__name__))
    vdict = {'body': a, 'resp': '200', 'resp2': resp2, 'method': "POST", 'uri': _uri}
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="yes")
    if out == 1 and len(resp_str) > 3:
      jstr = json_loads(resp_str)
      #pprint(jstr)
    return 

# Create wan ntwk for Reference Template -- not used
def create_wan_ntwk_for_reference_tmplt():
    wan_list = []
    if 'transportDomain' in  glbl.vnms.data and len(glbl.vnms.data['transportDomain']) > 0: 
      i = 0
      for key in glbl.vnms.data['transportDomain'].keys():
        if key in glbl.vnms.data['networkName']: 
          a = {}
          a["intfnum"] = str(i)
          a["ntwkName"] = glbl.vnms.data['networkName'][key]
          a["trnsptDomain"]= key
          wan_list.append(a) 
          i = i + 1
        else: 
          mlog.info("Did not find details of WAN for key={0}".format(key))
      return wan_list
    return None
        
    
# Create Reference template -- not used
def create_reference_tmplt(_method, _uri,_payload,resp='200',name=None, option=0):
    global vnms, analy, cntlr, cust, admin, mlog
    mlog.info("In function {0} ".format(create_reference_tmplt.__name__))
    vdict = {'body': _payload, 'resp': resp, 'method': _method, 'uri': _uri}
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    # Now the Deploy
    uri = "/vnms/sdwan/workflow/templates/template/deploy/" + name
    payload1 = {}
    vdict = {'body': payload1,  'resp': resp, 'method': "POST", 'uri': uri}
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    #{"versanms.sdwan-device-template-diff":null}

    resp = "200"
    resp2 = "202"
    uri0 = "/api/config/devices/template/" + name 
    uri1 = uri0  + "/config/orgs/org/" +  glbl.cust.data["custName"] + "/sd-wan/controllers/controller?deep"
    vdict = {'body': payload1, 'resp': resp, 'method': "GET", 'uri': uri1}
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if out == 1 and len(resp_str) > 3:
      jstr = json_loads(resp_str)
      if "reftemplate" not in glbl.vnms.data :
        glbl.vnms.data["reftemplate"] = {}
        glbl.vnms.data["reftemplate"]["sd-wan-cont"] = {}
        glbl.vnms.data["reftemplate"]["sd-wan-cont"] = jstr

    uri2 = uri0 +  "/config/system/sd-wan/controllers/controller?deep=true&offset=0&limit=25"
    vdict = {'body': payload1, 'resp': resp, 'method': "GET", 'uri': uri2}
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if out == 1 and len(resp_str) > 3:
      jstr = json_loads(resp_str)
      glbl.vnms.data["reftemplate"]["system-cont"] = jstr

    uri3 = uri0 + "/config/orgs/org-services/" +  glbl.cust.data["custName"] + "/ipsec/vpn-profile?deep=true&offset=0&limit=25"
    vdict = {'body': payload1, 'resp': resp, 'method': "GET", 'uri': uri3}
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if out == 1 and len(resp_str) > 3:
      jstr = json_loads(resp_str)
      glbl.vnms.data["reftemplate"]["vpn-profile"] = jstr
    write_outfile(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin)
    
    uri = "/vnms/sdwan/workflow/templates/" + name
    payload1 = {}
    vdict = {'body': payload1,  'resp': resp, 'method': "DELETE", 'uri': uri}
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)


# Recreate Template. Note we use the active section and we take care if the template has HA
def re_create_template(dev):
    resp = "200"
    resp2 = "202"
    fname="current_temp"
    fname1="current_red"
    uri0 = "/vnms/sdwan/workflow/templates/template/deploy/" +  dev["poststaging-template"] + '?verifyDiff=true'
    payload1 = {}
    vdict = {'body': payload1,  'resp': resp, 'method': "POST", 'uri': uri0}
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    red = None
    redName = None
    if out == 1 and len(resp_str) > 3:
      jstr = json_loads(resp_str)
      if "versanms.sdwan-device-template-diff" in jstr and "current" in jstr["versanms.sdwan-device-template-diff"]:
        t_current =  jstr["versanms.sdwan-device-template-diff"]["active"]
        fp=open(fname,"w+")
        fp.write(t_current)
        fp.close()
      if "versanms.sdwan-device-template-diff" in jstr and "redundant" in jstr["versanms.sdwan-device-template-diff"] and "redundantName" in jstr["versanms.sdwan-device-template-diff"]:
        red = 1
        redName =  jstr["versanms.sdwan-device-template-diff"]["redundantName"]
        t_red =  jstr["versanms.sdwan-device-template-diff"]["redundant"]
        fp=open(fname1,"w+")
        fp.write(t_red)
        fp.close()
      if not red: # Not redundant 
        uri1 = "/vnms/template/importstr/?templateName=" +  dev["poststaging-template"]
        fp=open(fname,"r")
        out = fp.read()
        fp.close()
        vdict = {'body': out,  'resp': resp, 'method': "POST", 'uri': uri1}
      else: # Redundant template
        uri1 = "/vnms/template/importstr/together/?templateName=" +  dev["poststaging-template"] + "&redTemplateName=" + redName
        fp=open(fname,"r")
        out = fp.read()
        fp.close()
        fp=open(fname1,"r")
        out1 = fp.read()
        fp.close()
        jstr = { "active": out,
                 "redundant": out1 }
        vdict = {'body': json.dumps(jstr),  'resp': resp, 'method': "POST", 'uri': uri1}

      [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
      if out == 1:
        if not red and resp_str.find("Successfully imported template") != -1:
          mlog.info("Deploy Template Workflow = {0} was successful".format(dev["poststaging-template"]))
          dev["template_deployed"] = "1"
          return True
        elif red: 
          mlog.info("Deploy Redundant Template: Templatate1={0}  Template2={1} was successful".format(dev["poststaging-template"],redName))
          dev["template_deployed"] = "1"
          return True
        else:
          mlog.error("Deploy Template Workflow = {0} was NOT successful. Error={1}".format(dev["poststaging-template"],resp_str))
          dev["template_deployed"] = "0"
          return False
    return False

'''
# Template Manipulation -- not used
def template_manipulation(dev):
    global vnms, analy, cntlr, cust, admin, mlog
    mlog.info("In function {0} ".format(template_manipulation.__name__))
    resp = "200"
    resp2 = "202"
    uri0 = "/api/config/devices/template/" +  dev["poststaging-template"]
    
    uri1 = uri0  + "/config/orgs/org/" +  glbl.cust.data["custName"] + "/sd-wan/controllers/controller?deep"
    payload1 = {}
    vdict = {'body': payload1,  'resp': resp, 'method': "GET", 'uri': uri1}
    #mlog.info("GET for SDWAN Controller Information for Template={0} ".format(dev["poststaging-template"]))
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if out == 1 and len(resp_str) > 3:
      jstr = json_loads(resp_str)
      vdict = {'body': json.dumps(jstr),  'resp': resp, 'method': "DELETE", 'uri': uri1}
      #mlog.info("DELETE for SDWAN Controller Information for Template={0} ".format(dev["poststaging-template"]))
      [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)


    newjstr = glbl.vnms.data["reftemplate"]["sd-wan-cont"] 
    uri1 = uri0  + "/config/orgs/org/" +  glbl.cust.data["custName"] + "/sd-wan/controllers"
    #mlog.info("POST for SDWAN Controller Information for Template={0} ".format(dev["poststaging-template"]))
    vdict = {'body': json.dumps(newjstr),  'resp': resp, 'method': "POST", 'uri': uri1}
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if out == 0:
      mlog.error("POST for SDWAN Controller Information Failed for Template={0} ".format(dev["poststaging-template"]))
      return False


    uri2 = uri0 +  "/config/system/sd-wan/controllers/controller?deep=true&offset=0&limit=25"
    #mlog.info("GET for SDWAN System Controller Information for Template={0} ".format(dev["poststaging-template"]))
    vdict = {'body': payload1, 'resp': resp, 'method': "GET", 'uri': uri2}
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if out == 1 and len(resp_str) > 3:
      jstr = json_loads(resp_str)
      #mlog.info("DELETE for SDWAN System Controller Information for Template={0} ".format(dev["poststaging-template"]))
      vdict = {'body': json.dumps(jstr),  'resp': resp, 'method': "DELETE", 'uri': uri2}
      [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)

    uri2 = uri0 +  "/config/system/sd-wan/controllers"
    newjstr = glbl.vnms.data["reftemplate"]["system-cont"] 
    vdict = {'body': json.dumps(newjstr),  'resp': resp, 'method': "POST", 'uri': uri2}
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if out == 0:
      mlog.error("POST for SDWAN Systerm Controller Information Failed for Template={0} ".format(dev["poststaging-template"]))
      return False


    uri3 = uri0 + "/config/orgs/org-services/" +  glbl.cust.data["custName"] + "/ipsec/vpn-profile?deep=true&offset=0&limit=25"
    vdict = {'body': payload1, 'resp': resp, 'method': "GET", 'uri': uri3}
    #mlog.info("GET for IPSEC VPN Profile Information for Template={0} ".format(dev["poststaging-template"]))
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    old_cntlr_pnames = list(map(lambda x: x['controllerName'] + "-Profile",  glbl.cntlr.data["old_cntlr"]))
    new_cntlr_pnames = list(map(lambda x: x['controllerName'] + "-Profile",  glbl.cntlr.data["new_cntlr"]))
    if out == 1 and len(resp_str) > 3:
      jstr = json_loads(resp_str)

      vpn_profile_list= list(filter(lambda x: (x['name'] == old_cntlr_pnames[0] or x['name'] == old_cntlr_pnames[1] or 
                                              x['name'] == new_cntlr_pnames[0] or x['name'] == new_cntlr_pnames[1] ), jstr["vpn-profile"]))

      vpn_profile_names= list(map(lambda x: x['name'], vpn_profile_list))
      #Now delete individual vpn profiles
      for elem in vpn_profile_names:
        uri3new = uri0 + "/config/orgs/org-services/" +  glbl.cust.data["custName"] + "/ipsec/vpn-profile/" + elem
        vdict = {'body': payload1,  'resp': resp, 'method': "DELETE", 'uri': uri3new}
        #mlog.info("DELETE for IPSEC VPN Profile={0} Information for Template={1} ".format(elem,dev["poststaging-template"]))
        [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)

    uri3 = uri0 + "/config/orgs/org-services/" +  glbl.cust.data["custName"] + "/ipsec"
    newjstr = glbl.vnms.data["reftemplate"]["vpn-profile"] 
    vdict = {'body': json.dumps(newjstr),  'resp': resp, 'method': "POST", 'uri': uri3}
    #mlog.info("POST for IPSEC VPN Profile Information for Template={0} ".format(dev["poststaging-template"]))
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if out == 0:
      mlog.error("POST for IPSEC VPN Profile Information for Template={0} Failed ".format(dev["poststaging-template"]))
      return False
    get_vnf_manager(dev)
    return True

'''    

# Puts these files in in_phase3 directory
def post_script():
    # we need to write a few files so it is easier on the next phase
    global vnms, analy, cntlr, cust, admin, mlog
    mlog.info("In function {0} ".format(post_script.__name__))

    _str = '/api/config/devices/template/'+ '{{templateName}}' 
    for i in range(13,17):
      jstr = {}
      if i == 13:
        _uri= _str + '/config/orgs/org/' +  glbl.cust.data["custName"] + '/sd-wan/controllers/controller'
        fname = "in_phase3/" + "{:03d}_GET_SDWAN_CONTROLLER.json".format(i)
      elif i == 14:
        _uri= _str + '/config/system/sd-wan/controllers/controller?deep=true&offset=0&limit=25'
        fname = "in_phase3/" + "{:03d}_GET_SYSTEM_CONTROLLER.json".format(i)
      elif i == 15:
        _uri= _str + '/config/orgs/org-services/' +  glbl.cust.data["custName"] + '/ipsec/vpn-profile?deep=true&offset=0&limit=25'
        fname = "in_phase3/" + "{:03d}_GET_IPSEC_VPN_PROFILE.json".format(i)
      elif i == 16:
        _uri= _str + '/config/system/vnf-manager'
        fname = "in_phase3/" + "{:03d}_GET_VNF_MANAGER.json".format(i)

      out = common.create_out_data("GET","200",_uri, jstr)
      fp=open(fname,"w+")
      out1 = json.dumps(out, indent=4)
      fp.write(out1)
      fp.close()


    _str = '/api/config/devices/device/'+ '{{deviceName}}' 
    for i in range(23,27):
      jstr = {}
      if i == 23:
        _uri= _str + '/config/orgs/org/' +  glbl.cust.data["custName"] + '/sd-wan/controllers/controller?deep=true&offset=0&limit=25'
        fname = "in_phase3/" + "{:03d}_GET_DEVICE_SDWAN_CONTROLLER.json".format(i)
      elif i == 24:
        _uri= _str + '/config/system/sd-wan/controllers/controller?deep=true&offset=0&limit=25'
        fname = "in_phase3/" + "{:03d}_GET_DEVICE_SYSTEM_CONTROLLER.json".format(i)
      elif i == 25:
        _uri= _str + '/config/orgs/org-services/' +  glbl.cust.data["custName"] + '/ipsec/vpn-profile?deep=true&offset=0&limit=25'
        fname = "in_phase3/" + "{:03d}_GET_DEVICE_IPSEC_VPN_PROFILE.json".format(i)
      elif i == 26:
        _uri= _str + '/config/system/vnf-manager'
        fname = "in_phase3/" + "{:03d}_GET_DEVICE_VNF_MANAGER.json".format(i)

      out = common.create_out_data("GET","200",_uri, jstr)
      fp=open(fname,"w+")
      out1 = json.dumps(out, indent=4)
      fp.write(out1)
      fp.close()
    return
        
# Gets appliance details especially the BranchId
def get_appliance_details(_dev_list, _len):
    global vnms, analy, cntlr, cust, admin, mlog
    resp2 = '202'
    _payload = {}
    mlog.info("In function {0} ".format(get_appliance_details.__name__))
    # round off the limit to the next 100
    mlen = (int(int(_len)/100) + 1)*100
    elem_no_branchId = 9000
    
    uri = '/vnms/cloud/systems/getAllAppliancesBasicDetails?offset=0&limit=' + str(mlen)
    # On Old Dir
    #'/vnms/appliance/appliance?offset=0&limit=' + str(mlen)
    vdict = {'body': _payload, 'resp': '200', 'resp2': resp2, 'method':"GET", 'uri': uri,
            'vd_ip' :  olddir['vd_ip'], 'vd_rest_port': olddir['vd_rest_port'],
            'auth': olddir['auth'] }
    [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if out == 1 and len(resp_str) > 3:
      jstr = json_loads(resp_str)
      if "appliance-list" in jstr: 
        for _elem in _dev_list:
          name = _elem["name"]
          for _app in  jstr["appliance-list"]:
            if _app["name"] == name:
              if "branchId" in _app:
                _elem["branchId"] = int( _app["branchId"]) # we will save it as an integer
              else:
                _elem["branchId"] = elem_no_branchId 
                mlog.error("Appliance={0} has no BranchId. Putting BranchId={1}".format(_app["name"],elem_no_brancId))
                elem_no_branchId = elem_no_branchId + 1
        write_outfile(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin)
      else: 
          mlog.error("DID NOT GET DATA from uri={0}".format(uri))
    else: 
      mlog.error("DID NOT GET DATA from uri={0}".format(uri))

    # final check
    for _elem in _dev_list:
      if "branchId" not in _elem:
        _elem["branchId"] = elem_no_branchId 
        mlog.error("Appliance={0} has no BranchId. Putting BranchId={1}".format(_elem["name"],elem_no_brancId))
        elem_no_branchId = elem_no_branchId + 1


# Gets existing (old) controllers. It deletes the Old controllers present in New Director
def get_existing_controller():
    global vnms, analy, cntlr, cust, admin, mlog
    resp2 = '202'
    _payload = {}
    mlog.info("In function {0} ".format(get_existing_controller.__name__))
    
    # On Old Dir
    vdict = {'body': _payload, 'resp': '200', 'resp2': resp2, 'method':"GET", 'uri': "/vnms/appliance/summary",
            'vd_ip' :  olddir['vd_ip'], 'vd_rest_port': olddir['vd_rest_port'],
            'auth': olddir['auth'] }
    [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)


    old_cntlr_list = []
    old_cntlr_names = []
    new_cntlr_list = []
    new_cntlr_names = []
    if out == 1 and len(resp_str) > 3:
      jstr = json_loads(resp_str,object_pairs_hook=OrderedDict)
      #mlog.info("Device list = {0}".format(json.dumps(jstr,indent=4)))
      old_cntlr_list = list(filter(lambda x: x['type'] == 'controller', jstr))
      old_cntlr_names = list(map(lambda x: x['name'], old_cntlr_list))
      dev_list = list(filter(lambda x: x['type'] != 'controller', jstr))
      hub_cntlr_list = list(filter(lambda x: x['type'] == 'hub_controller' or x['type'] == 'hub-controller', jstr))
      if len(hub_cntlr_list) > 0: 
        new_hub_cntlr_list = copy.deepcopy( hub_cntlr_list )
        if 'hub_cntlr_present' not in glbl.vnms.data:
          glbl.vnms.data['hub_cntlr_present'] = 1
          glbl.vnms.data['hub_cntlr_devices'] = []
          glbl.vnms.data['hub_cntlr_devices'] = new_hub_cntlr_list
        mlog.warn("Hub Controller Num = {0} present".format(len(new_hub_cntlr_list)))
      elif 'hub_cntlr_present' not in glbl.vnms.data:
          glbl.vnms.data['hub_cntlr_present'] = 0

      # we will do this ONLY if the devices is not present
      if "devices" not in glbl.vnms.data:
        glbl.vnms.data['devices'] = []
        glbl.vnms.data['devices'] = dev_list
      write_outfile(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin)
      #pprint(jstr)
      get_appliance_details(glbl.vnms.data['devices'],len(glbl.vnms.data['devices']))

      if len(old_cntlr_list) != 2:
        mlog.error("Number of Existing Controllers not 2.It is  = {0}".format(len(old_cntlr_list)))

      # Make sure the cntrollers are NOT the New controllers: This can not happen since we our query is to olddir
      # this can happen if this file is executed more than once
      found = 0
      for dev in old_cntlr_list: 
        if ((dev["name"] == glbl.cntlr.data["new_cntlr"][0]["controllerName"]) or 
            (dev["name"] == glbl.cntlr.data["new_cntlr"][1]["controllerName"])): 
            sys.exit("Old and New Controller List have same names. Can not continue ")

      # On New Dir
      vdict = {'body': _payload, 'resp': '200', 'resp2': resp2, 'method':"GET", 'uri': "/vnms/appliance/summary",
              'vd_ip' :  newdir['vd_ip'], 'vd_rest_port': newdir['vd_rest_port'],
              'auth': newdir['auth'] }
      [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
      if out == 1 and len(resp_str) > 3:
        jstr = json_loads(resp_str)
        new_cntlr_list = list(filter(lambda x: x['type'] == 'controller', jstr))
        new_cntlr_names = list(map(lambda x: x['name'], new_cntlr_list))
      else:
        mlog.error("Did not find devices = {0}".format(json.dumps(jstr,indent=4)))
        return False



      for dev in old_cntlr_list: 
        if not controller_connect(dev):
          # We can connect from the New Director to the Old Controller. This is a NO NO
          mlog.error("The New Director is able to communicate with the Old Controllers. Please follow instructions. ")
          sys.exit("The New Director is able to communicate with the Old Controllers. Please follow instructions. ")

      #glbl.cntlr.data['old_cntlr'] = []
      # Since this function can be executed multiple times we now need to determine if the Old controllers are present in the New Complex
      for dev in new_cntlr_list: 
        found = 0
        for elem in old_cntlr_names:
          if elem == dev["name"]: # this Controller needs to be deleted
            found = 1
            break
        if found == 1: 
          mlog.warn("Deleting Old Controller: {0} from New Director and checking status. Please be patient".format(dev["name"]))
          delete_controller_by_uuid( dev['uuid'])
          time.sleep(20)
          for i in range(0,5):
            [status,resp_str] = common.check_controller_status(name=dev['name'],resp='404')
            if status == 1: 
              mlog.warn("Old Controller: {0} successfully deleted from New Director. Any previous errors can be ignored".format(dev["name"]))
              break
            else : time.sleep(2)

          mlog.warn("Deleting Old Controller: {0} Workflow".format(dev["name"]))
          delete_controller_workflow(dev['name'])
          if len(glbl.cntlr.data['old_cntlr']) == 0:
            glbl.cntlr.data['old_cntlr'].append(dev) 
          else: #Make sure we are not rewriting the same data again and again
            found = 0
            for i in range(len(glbl.cntlr.data['old_cntlr'])):
              if dev['name'] == glbl.cntlr.data['old_cntlr'][i]['name']: found = 1
            if found == 0:
              glbl.cntlr.data['old_cntlr'].append(dev) 
              mlog.warn("Writing Old Controller Data")
      # we deleted the controller and workflow if the controllers exist. If the workflow exist e.g. User deleted the controllers
      # but left the workflow present. The delete_controller_workflow() first checks and then deletes
      for elem in old_cntlr_names:
        delete_controller_workflow(elem)

      write_outfile(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin)
      return True
    else:
      mlog.error("Did not find devices = {0}".format(json.dumps(jstr,indent=4)))

    return False

# Sync to for Controllers
def set_cntlr_synch_to( _method, _uri,_payload,resp='200',name=None, option=0):
    vdict = {'body': _payload, 'resp': resp, 'method': _method, 'uri': _uri}
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no")
    if out == 1 and len(resp_str) > 3:
      jstr = json_loads(resp_str)
      if "output" in jstr and "result" in jstr["output"] and jstr["output"]["result"]: 
        mlog.info("Got Sync for Controller={0}".format(name))
        return ''
      else:
        mlog.error("Response for Method={0} URI={1} str = {2}".format(_method,_uri,json.dumps(jstr,indent=4)))
        mlog.warn(bcolors.OKWARN+"We can not proceed without the Controller being in Sync.\n" + 
                'You can fix the error and then refresh (type r) to try check Sync again\n' +
                "Typing a n (No)  will exit the program. Typing a y (Yes) will continue" + bcolors.ENDC)
        ret = yes_or_no(bcolors.OKWARN+"To Refresh press r, to Continue press y and to Exit press n: "+ bcolors.ENDC,1)
        if ret == 0 : sys.exit("Exiting")
        elif ret == 1: pass
        else: 
          set_cntlr_synch_to( _method, _uri,_payload,resp='200', name=name, option=option)
          
    return ''

# create dns config. This is default function call for files that have no callback
def create_dns_config( _method, _uri,_payload,resp='200',name=None, option=0):
    vdict = {'body': _payload, 'resp': resp, 'method': _method, 'uri': _uri}
    [out, resp_str] = common.call(vdict,content_type='json',ncs_cmd="no")
    if out == 1 and len(resp_str) > 3:
      jstr = json_loads(resp_str)
      mlog.info("Response for Method={0} URI={1} str = {2}".format(_method,_uri,json.dumps(jstr,indent=4)))
    return ''

# yes or no question
def yes_or_no3(question, option = 0):
    if pyVer.major== 3:
      reply = str(input(question+' (y/n): ')).lower().strip()
    else:
      reply = str(raw_input(question+' (y/n): ')).lower().strip()
    if option == 0:
      if reply[0] == 'n': return 1
      elif reply[0] == 'y': return 1
    return 1

# yes or no question
def yes_or_no2(question):
    if pyVer.major == 3:
      reply = str(input(question+' (y/n): ')).lower().strip()
    else: 
      reply = str(raw_input(question+' (y/n): ')).lower().strip()
    if reply[0] == 'n': return 0
    elif reply[0] == 'y': return 1
    else:
        return yes_or_no2("Did not understand input: Please re-enter ") 

# yes or no question
def yes_or_no(question, option=0):

    if option == 0:
      if pyVer.major== 3:
        reply = str(input(question)).lower().strip()
      else: 
        reply = str(raw_input(question)).lower().strip()
      if reply[0] == 'n': return 0
      elif reply[0] == 'y': return 1
      elif reply[0] == 's': return 2
      else:
          return yes_or_no("Did not understand input: Please re-enter ",option) 
    else: 
      if pyVer.major== 3:
        reply = str(input(question)).lower().strip()
      else:
        reply = str(raw_input(question)).lower().strip()
      if reply[0] == 'n': return 0
      elif reply[0] == 'y': return 1
      elif reply[0] == 'r': return 2
      else:
          return yes_or_no("Did not understand input: Please re-enter ",option) 

# write the output json file
def write_partition_file(_vnms,_analy,_cntlr,_cust, _admin,fil, new_device_list):
    global vnms, analy, cntlr, cust, admin, mlog
    mlog.info("In function {0} : Output file:{1}".format(write_partition_file.__name__,fil))
    jstr = {}
    _vnms.data['devices'] = []
    _vnms.data['devices'] = new_device_list
    jstr["Vnms"] = _vnms.data
    jstr["Analytics"] = _analy.data
    jstr["Controller"] = _cntlr.data
    jstr["Admin"] = _admin.data
    jstr["Customer"] = _cust.data
    fin=open(fil, "w+")
    mstr1 = json.dumps(jstr, indent=4)
    fin.write(mstr1)
    fin.close()

# write the output json file
def write_outfile(_vnms,_analy,_cntlr,_cust, _admin):
    global vnms, analy, cntlr, cust, admin, mlog
    mlog.info("In function {0} : Output file:vm_phase3.json".format(write_outfile.__name__))
    jstr = {}
    jstr["Vnms"] = _vnms.data
    jstr["Analytics"] = _analy.data
    jstr["Controller"] = _cntlr.data
    jstr["Admin"] = _admin.data
    jstr["Customer"] = _cust.data
    fin=open("vm_phase3.json", "w+")
    mstr1 = json.dumps(jstr, indent=4)
    fin.write(mstr1)
    fin.close()

# read input file -- may not be used
def read_input_file(_infile, option=None):
    global vnms, analy, cntlr, cust, admin, auth, debug, mlog, mdict

    fp = open(_infile,"r")
    jstr = fp.read()
    fp.close()
    if option is None:
      mdict=json_loads(jstr)
      for _keys,_val in mdict.items():
        if _keys.lower() == "vnms": 
           vnms =  Vnms(_val)
        elif _keys.lower() == "analytics": 
           analy = Analytics(_val)
        elif _keys.lower() == "controller": 
           cntlr =  Controller(_val)
        elif _keys.lower() == "customer": 
           cust = Customer(_val)
           #pprint(cust.data)
        elif _keys.lower() == "admin": 
           admin = Admin(_val)
      return
    else:
      return json_loads(jstr)


# process the input files
def process_normal(fil,template_env,template_path, option=False):
    global vnms, analy, cntlr, cust, admin, auth, debug, mlog


    dir_items = sorted(os.listdir(template_path))
    for i in dir_items:
       # check the format of the files
       #print("Got item={0}".format(i))
       if not re.match(r'^\d{3}_.+\.json$', i):
          print("Got Not match item={0}".format(i))
          continue
       if option: 
          # Here we are dealing with the re-read case. We just need to read one file 
          if not re.match(r'^\d{3}_GET_DEVICE_GROUP\.json$', i):
            continue
       if re.match(r'^\d{3}_GET_DEVICE_GROUP\.json$', i):
         mlog.warn(bcolors.OKWARN+"Before we run through Template Deploy and Device Deploy we are pausing."+
                "Typing a n (No)  will exit the program. Typing a y (Yes) will continue" + bcolors.ENDC)
         ret = yes_or_no2("Continue: " )
         if ret == 0 : sys.exit("Before Device Deploy")
         elif ret == 1: pass

       _key = i[4:]
       if _key in fil:
          _val = fil[_key]
       else:
          if _key[0:3] == 'GET':
            fil[_key]=get_default
          else:
            fil[_key]=create_dns_config
          _val = fil[_key]
       my_template = template_env.get_template(i)
       _newkey = _key.split(".")[0]
       #print("==============In %s==========" %(_newkey))
       mlog.warn("==============In {0}==========".format(_newkey))
       #ret = yes_or_no("Continue: " )
       #if ret == 0 : exit(0)
       #elif ret == 2: continue
       if _key[0:3] == 'GET':
         if _newkey == 'GET_RELEASE_INFO':
           x= my_template.render()
           y= json_loads(x)
           _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']),_name=None,_ofile=None)
         elif _newkey == 'GET_DEVICE_GROUP':
           x= my_template.render()
           y= json_loads(x)
           _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']),_name=None,_ofile=None)
         elif _newkey == 'GET_PARENT_ORGID':
           x= my_template.render()
           y= json_loads(x)
           _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']),_name=None,_ofile=None)
         elif _newkey == 'GET_WAN_NETWORK':
           x= my_template.render(parentOrgUUID=glbl.vnms.data['parentOrgId'])
           y= json_loads(x)
           _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']),_name=None,_ofile=None)
       elif _newkey == 'CREATE_TIME_ZONE':
         x= my_template.render()
         y= json_loads(x)
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
       elif _newkey == 'CREATE_NTP_SERVER':
         x= my_template.render()
         y= json_loads(x)
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
       elif _newkey == 'CREATE_DNS_SERVER':
         x= my_template.render()
         y= json_loads(x)
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
       elif _newkey == 'SET_NMS_PROVIDER':
         x= my_template.render()
         y= json_loads(x)
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
       elif _newkey == 'CREATE_ANALYTICS_CLUSTER':
         x= my_template.render()
         y= json_loads(x)
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
       elif _newkey == 'CREATE_AUTH_CONNECTOR':
         x= my_template.render()
         y= json_loads(x)
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
       elif _newkey == 'CREATE_DEFAULT_AUTH_CONNECTOR' or _newkey == 'DELETE_AUTH_CONNECTOR':
         x= my_template.render()
         y= json_loads(x)
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']))
       elif _newkey == 'CREATE_CONTROLLER' or _newkey == 'CREATE_PEER_CONTROLLER':
         if _newkey == 'CREATE_CONTROLLER': 
           # before we get into this we need to Delete the existing controllers and 
           # the function get_existing_controller will delete both the controllers and
           # we need to do this once
           rv = get_existing_controller()
           if not rv:
             mlog.error("Can not find appliance data .. exiting")
             sys.exit("Can not find appliance data .. exiting")
         x= my_template.render( )
         y= json_loads(x)
         _name=str(y['payload']['versanms.sdwan-controller-workflow']['controllerName'])
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']),name=_name)
       elif _newkey == 'DEPLOY_CONTROLLER_WORKFLOW' or _newkey == 'DEPLOY_PEER_CONTROLLER_WORKFLOW':
         cntlr_num = 0
         if _newkey == 'DEPLOY_PEER_CONTROLLER_WORKFLOW':
           cntlr_num = 1
         x= my_template.render( )
         y= json_loads(x)
         cntlr_name =str(y['path']).rsplit("/",1)[-1]
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']),name=cntlr_name, option=cntlr_num)
       elif _newkey == 'ORG_DEPLOY_WORKFLOW':
         x= my_template.render( )
         y= json_loads(x)
         a=str(y['path']).rsplit("/",1)[-1]
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']),name=a)
       elif _newkey == 'SET_CONTROLLER_CONFIG_BUILD' or _newkey == 'SET_PEER_CONTROLLER_CONFIG_BUILD':
         x= my_template.render( )
         y= json_loads(x)
         a=str(y['path']).rsplit("/")[-3]
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']),name=a)
       elif (_newkey == 'SET_CONTROLLER_VNI' or
             _newkey == 'SET_CONTROLLER_ROUTING' or
             _newkey == 'SET_CONTROLLER_NTP' or
             _newkey == 'SET_CONTROLLER_OAM_ALARMS' or
             _newkey == 'SET_CONTROLLER_ORG_SERVICES' or
             _newkey == 'SET_CONTROLLER_ORG' or
             _newkey == 'SET_CONTROLLER_SYSTEM' or
             _newkey == 'SET_CONTROLLER_COMMIT' or
             _newkey == 'SET_CONTROLLER_SYNCH'): 
         name=glbl.cntlr.data['new_cntlr'][0]["controllerName"]
         x= my_template.render( )
         y= json_loads(x)
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']),name=name,option=0)
       elif (_newkey == 'SET_PEER_CONTROLLER_VNI' or 
             _newkey == 'SET_PEER_CONTROLLER_ROUTING' or 
             _newkey == 'SET_PEER_CONTROLLER_NTP' or 
             _newkey == 'SET_PEER_CONTROLLER_OAM_ALARMS' or 
             _newkey == 'SET_PEER_CONTROLLER_ORG_SERVICES' or 
             _newkey == 'SET_PEER_CONTROLLER_ORG' or 
             _newkey == 'SET_PEER_CONTROLLER_SYSTEM' or 
             _newkey == 'SET_PEER_CONTROLLER_COMMIT' or 
             _newkey == 'SET_PEER_CONTROLLER_SYNCH'):
         name=glbl.cntlr.data['new_cntlr'][1]["controllerName"]
         x= my_template.render( )
         y= json_loads(x)
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']),name=name,option=1)
       elif _newkey == 'BUILD_DEPLOY_REF_TMPLT':
         continue
         wan_list =  create_wan_ntwk_for_reference_tmplt()
         lan_intf_num = str(len(wan_list)+1)
         controllerName=[glbl.cntlr.data['new_cntlr'][0]["controllerName"],glbl.cntlr.data['new_cntlr'][1]["controllerName"]]
         x= my_template.render(templateName="Ref_Template",  controllerName=controllerName, wan_list=wan_list, 
                                custName=glbl.cust.data["custName"],lan_intfnum=lan_intf_num )
         y= json_loads(x)
         _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']),name="Ref_Template",option=0)

# split a string on length
def my_split_string(_str, n):
    my_list = [_str[index : index + n] for index in range(0, len(_str), n)]
    return my_list


# get terminal size
def get_terminal_size():
  global MYLINES, MYCOL
  os_env = os.environ

  if "LINES" in os_env:
    MYLINES = int(os_env["LINES"]) - 5
  else:
    MYLINES = 20
  if "COLUMNS" in os_env:
    MYCOL = (int(int(os_env["COLUMNS"])/10) - 1)*10
  else:
    MYCOL = 70

# perform initial checks
def perform_initial_checks(_reread):
    err = 0
    mlog.warn("Performing Initial checks. Please be patient")

    if _reread:
      if "devices" not in glbl.vnms.data:
        err = err + 1
        mlog.error("Devices data is missing")
      else: 
        dev = glbl.vnms.data["devices"]
        if len(dev)  == 0 :
          err = err + 1
          mlog.error("There are no devices in input file ")
        else:
          for elem in dev:
            name_present = 1
            if "name" not in elem:
              err = err + 1
              name_present = 0
              mlog.error("Name not present")
            if "dg-group" not in elem and name_present == 1: 
              err = err + 1
              mlog.error("Device Group not present for Device={0}".format(elem["name"]))
            if "poststaging-template" not in elem and name_present == 1:
              err = err + 1
              mlog.error("Post staging template not present  for Device={0}".format(elem["name"]))
            if "type" not in elem and name_present == 1:
              err = err + 1
              mlog.error("Type  not present for Device={0}".format(elem["name"]))



    if "old_cntlr" not in glbl.cntlr.data: 
      err = err + 1
      mlog.error("Data shows old_cntlr is not present")
    elif len(glbl.cntlr.data["old_cntlr"]) != 2 : 
      err = err + 1
      mlog.error("Data old_cntlr is present but len={0} not equal to 2".format(len(glbl.cntlr.data["old_cntlr"])))
    elif ("peerControllers" not in glbl.cntlr.data["old_cntlr"][0] and 
            "peerControllers" not in glbl.cntlr.data["old_cntlr"][1] ):
      err = err + 1
      mlog.error("Peer Controller Data old_cntlr is present but len={0} not equal to 2".format(len(glbl.cntlr.data["old_cntlr"])))
    if err == 0: #we have not hit any of the previous ifs
      peerlist = list(filter(lambda x: "peerControllers" in x and x["peerControllers"],glbl.cntlr.data["old_cntlr"]))
      if len(peerlist) != 1:
        err = err + 1
        mlog.error("Peer Controller should be 1 but we got {0}".format(len(peerlist)))
      elif len(peerlist[0]["peerControllers"]) != 1:
        err = err + 1
        mlog.error("There should be only 1 elem in Peer Controller list but we got {0}".format(len(peerlist[0]["peerControllers"])))

    errc = err
    if "new_cntlr" not in glbl.cntlr.data: 
      errc = errc + 1
      mlog.error("Data shows new_cntlr is not present")
    elif len(glbl.cntlr.data["new_cntlr"]) != 2 : 
      errc = errc + 1
      mlog.error("Data new_cntlr is present but len={0} not equal to 2".format(len(glbl.cntlr.data["new_cntlr"])))
    elif ("peerControllers" not in glbl.cntlr.data["new_cntlr"][0] and 
            "peerControllers" not in glbl.cntlr.data["new_cntlr"][1] ):
      errc = errc + 1
      mlog.error("Peer Controller Data new_cntlr is present but len={0} not equal to 2".format(len(glbl.cntlr.data["new_cntlr"])))
    if errc == err: #we have not hit any of the previous ifs
      peerlist = list(filter(lambda x: "peerControllers" in x and x["peerControllers"],glbl.cntlr.data["new_cntlr"]))
      if len(peerlist) != 1:
        errc = errc + 1
        mlog.error("Peer Controller should be 1 but we got {0}".format(len(peerlist)))
      elif len(peerlist[0]["peerControllers"]) != 1:
        errc = errc + 1
        mlog.error("There should be only 1 elem in Peer Controller list but we got {0}".format(len(peerlist[0]["peerControllers"])))
    if errc > 0: 
      mlog.warn(bcolors.OKWARN+"We can not proceed with the above errors. Please fix then in the input file and then restart"+ 
                "Typing a n (No)  will exit the program. Typing a y (Yes) will continue" + bcolors.ENDC)
      ret = yes_or_no(bcolors.OKWARN+"To Continue press y and to Exit press n: "+ bcolors.ENDC,1)
      if ret == 1: pass
      else: sys.exit("Initial Checks failed")
    else : mlog.warn("All Initial checks passed.")


# read input from user
def read_input_from_user(_partno, newdev):

    _str = (bcolors.OKWARN + "Moving Devices from Partion=1 to Partion={0}.\n\t\t\tChoose A NUMBER or MULTIPLE NUMBERS SEPARATED BY SPACE ".format(_partno) +
                  "OR 0 (Zero) to break OR -1 to print current partition table:" + bcolors.ENDC + ' ')
    branch_list = list(map(lambda x: x['branchId'], newdev))
      
    while 1:
      output_list = []
      err = 0
      try:
        if pyVer.major== 3:
          inp=input(_str)
        else:
          inp=raw_input(_str)
        inp_list = inp.split()
        # first check if all the numbers are integers
        for elem in inp_list:
          num = int(elem) # if the user enters a bad number there will be an exception
          if num == 0: return 
          elif num == -1: 
            show_partition_table(newdev)
            err = 1
            break
          elif num in branch_list:
            output_list.append(num)
            '''
            Errors can go here
            if (_option == 2 and "status" in _comb_dict[num] and  
                  (_comb_dict[num]["status"] == "C2-Complete" or _comb_dict[num]["status"] == "C12-Complete")):
              print("Controller={0} Migration is complete. Re-enter a different the number to continue".format(cntlr_name))
              err = 1
              break
            '''
          else:
            print("Re-enter the number to continue")
            err = 1
            break
      except Exception as ex:
        print("I did not understand your input. Please re-enter the numbers to continue")
        continue

      # we are still inside the while loop and have a valid output list. 
      # time to change the partitions for those devices
      if err == 0 and len(output_list) > 0:
        for elem in output_list:
          dev = list(filter(lambda x: x['branchId'] == elem, newdev))
          if (len(dev) > 1 ):
            print("Error: expected 1 device got:{0}".format( len(dev)))
          else: 
            dev[0]['partition'] = _partno


def process_partition():
    ret = 1
    new_device_list = copy.deepcopy(glbl.vnms.data["devices"])
    for elem in new_device_list:
      if 'partition' not in elem:
        elem['partition'] = 1
      else: 
        elem['partition'] = 1
    question = "Currently all devices are in partition 1. To move them to a different partition type the partition number [2-4](max=4).  Enter -1 to break"
    while ret: 
      part_no = None
      if pyVer.major== 3:
        part_no = int(input(question+': '))
      else:
        part_no = int(raw_input(question+': '))

      if part_no == -1: break
      elif part_no > 4 or part_no <= 1: 
        print("Please enter positive number between 2 and 4")
      else:
        read_input_from_user(part_no,new_device_list)

    # we are out of while loop here
    show_partition_table(new_device_list)
    write_partion_table = yes_or_no2(bcolors.OKWARN + "Do you want to write the current partition table. Type y or n" + bcolors.ENDC)
    if write_partion_table == 1:
      #Now we determine the unique number of partitions 
      part_list = list(Counter(list(map(lambda x: x['partition'], new_device_list))))
      flist=[]
      for elem in part_list:
        # We need to create a output file
        fil="vm_phase3_{:02d}.json".format(elem)
        write_partition_file(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin,fil, new_device_list)
        flist.append(fil)
      mlog.warn(bcolors.OKWARN + "We have written following files: {0}\n".format(' '.join(flist)) + 
                              "You the run the VMMigr_phase3 script using the following command on separate windows\n" + 
                              './VMMigr_phase3.py -f vm_phase3_01.json -p 1 [for Partition 1]\n' + 
                              './VMMigr_phase3.py -f vm_phase3_02.json -p 2 [for Partition 2] etc' + bcolors.ENDC)
    return



# show device status 
def show_partition_table(devlist):
    global vnms, analy, cntlr, cust, admin, auth, debug, mlog, NOT_DEPLOYED 
    # First we sort the existing device list based on partion
    # we can not do the sorted because the devlist is an Ordered Dict
    #newdevlist = sorted(devlist, key=lambda x: x['partition'], reverse=False)
    branch_list = list(map(lambda x: x['branchId'], devlist))
    comb_dict=dict(zip(branch_list,devlist))

    count = 1
    pcol1=0
    pcol2=0
    pcol3=0

    pcol1=int(MYCOL/4)
    pcol2=int(MYCOL/4)
    pcol3=int(MYCOL/4)


    # Header
    print("-" * int(6+pcol1+pcol2+pcol3+15+6))
    print("|{0:<{col0}}|{1:<{col1}}|{2:<{col2}}|{3:<{col3}}|{4:<{col4}}|".format("BIdx","Name","P-STemplate","DG-Group","Part #",
                                              col0=6,col1=pcol1,col2=pcol2,col3=pcol3,col4=15))
    print("-" * int(6+pcol1+pcol2+pcol3+15+6))
    cnt = 0
    # We want 20 lines of output. We can try and read it from os.environ. Right now just hard-coding
    out_line = 20
    new_out_line = out_line

    for _key,v in comb_dict.items():
      cnt = cnt + 1
      namelist = []
      post_staginglist = []
      dg_grouplist = []
      #if len(v['name']) > pcol1:
      namelist = my_split_string(v['name'], pcol1)
      #if len(v['poststaging-template']) > pcol2: 
      post_staginglist = my_split_string(v['poststaging-template'], pcol2)
      #if len(v['dg-group']) > pcol3:
      dg_grouplist = my_split_string(v['dg-group'], pcol3)
      # find the max of 3 values to determine how many lines we need to add. If the max is 1 we do not need to add any lines
      mymax = max( len(namelist), len(post_staginglist), len(dg_grouplist))
      #cnt = cnt + mymax
      if mymax != 1 :
        new_out_line = new_out_line - mymax + 1

      if mymax == 1:
        print("|{0:<{col0}}|{1:<{col1}}|{2:<{col2}}|{3:<{col3}}|{green}{4:<{col4}}{endc}|".format(_key,v['name'],v['poststaging-template'],
                    v['dg-group'],v['partition'],green=bcolors.OKGREEN,endc=bcolors.ENDC,
                    col0=6,col1=pcol1,col2=pcol2,col3=pcol3,col4=15))
      else:
        for i in range(mymax):
          _namelist = "" if i >= len(namelist) else namelist[i]
          _post_staginglist = "" if i >= len(post_staginglist) else post_staginglist[i]
          _dg_grouplist = "" if i >= len(dg_grouplist) else dg_grouplist[i]
          _nd_status = v['partition']  if i == 0 else ""
          _keyl = "" if i > 0 else _key

          print("|{0:<{col0}}|{1:<{col1}}|{2:<{col2}}|{3:<{col3}}|{green}{4:<{col4}}{endc}|".
                format(_keyl,_namelist,_post_staginglist,
                _dg_grouplist,_nd_status, green=bcolors.OKGREEN,endc=bcolors.ENDC,
                col0=6,col1=pcol1,col2=pcol2,col3=pcol3,col4=15))

      if  cnt%new_out_line == 0 and _key !=  len(comb_dict) :
        #print(new_out_line)
        print("-" * int(4+pcol1+pcol2+pcol3+15+6))
        yes_or_no3("Press any key to continue",1 )
        print("-" * int(4+pcol1+pcol2+pcol3+15+6))
        print("|{0:<{col0}}|{1:<{col1}}|{2:<{col2}}|{3:<{col3}}|{4:<{col4}}|".format("Idx","Name","P-STemplate","DG-Group","Status",
                                              col0=6,col1=pcol1,col2=pcol2,col3=pcol3,col4=15))
        print("-" * int(4+pcol1+pcol2+pcol3+15+6))
        #Now reset things back
        new_out_line = out_line 
        cnt = 0

    print("-" * int(6+pcol1+pcol2+pcol3+15+6))
    print(bcolors.ENDC)

# show device status 
def show_devices_status( ):
    global vnms, analy, cntlr, cust, admin, auth, debug, mlog, NOT_DEPLOYED 
    cnt_list = []
    count = 1
    pcol1=0
    pcol2=0
    pcol3=0
    errlist = list(filter(lambda x: "poststaging-template" not in x or (len(x['poststaging-template']) < 3), glbl.vnms.data["devices"]))
    if len(errlist) > 0:
      mlog.error("Post Staging Template not found in devices")
      return
    errlist = list(filter(lambda x: "dg-group" not in x or (len(x['dg-group']) < 3), glbl.vnms.data["devices"]))
    if len(errlist) > 0:
      mlog.error("Device group not found in devices list ")
      return
    errlist = list(filter(lambda x: "name" not in x or (len(x['name']) < 3), glbl.vnms.data["devices"]))
    if len(errlist) > 0:
      mlog.error("Name not found in devices list ")
      return

    cnt_list = list(range(1,len(glbl.vnms.data['devices'])+1))
    bId_list = list(map(lambda x: x['branchId'],glbl.vnms.data['devices']))
    comb_dict=dict(zip(bId_list,glbl.vnms.data['devices']))
    pcol1=int(MYCOL/4)
    pcol2=int(MYCOL/4)
    pcol3=int(MYCOL/4)

    print ("The following in the status of devices from Director = {0}".format( glbl.admin.data['new_dir']['vd_ip']))

    # Header
    print("-" * int(6+pcol1+pcol2+pcol3+15+6))
    print("|{0:<{col0}}|{1:<{col1}}|{2:<{col2}}|{3:<{col3}}|{4:<{col4}}|".format("BIdx","Name","P-STemplate","DG-Group","Status",
                                              col0=6,col1=pcol1,col2=pcol2,col3=pcol3,col4=15))
    print("-" * int(6+pcol1+pcol2+pcol3+15+6))
    cnt = 0
    # We want 20 lines of output. We can try and read it from os.environ. Right now just hard-coding
    out_line = 20
    new_out_line = out_line

    for _key,v in comb_dict.items():
      cnt = cnt + 1
      namelist = []
      post_staginglist = []
      dg_grouplist = []
      #if len(v['name']) > pcol1:
      namelist = my_split_string(v['name'], pcol1)
      #if len(v['poststaging-template']) > pcol2: 
      post_staginglist = my_split_string(v['poststaging-template'], pcol2)
      #if len(v['dg-group']) > pcol3:
      dg_grouplist = my_split_string(v['dg-group'], pcol3)
      # find the max of 3 values to determine how many lines we need to add. If the max is 1 we do not need to add any lines
      mymax = max( len(namelist), len(post_staginglist), len(dg_grouplist))
      #cnt = cnt + mymax
      if mymax != 1 :
        new_out_line = new_out_line - mymax + 1

      if "deployed" in v and v["deployed"] == "1":
        if mymax == 1:
          print("|{0:<{col0}}|{1:<{col1}}|{2:<{col2}}|{3:<{col3}}|{green}{4:<{col4}}{endc}|".format(_key,v['name'],v['poststaging-template'],
                      v['dg-group'],"OK",green=bcolors.OKGREEN,endc=bcolors.ENDC,
                      col0=6,col1=pcol1,col2=pcol2,col3=pcol3,col4=15))
        else:
          for i in range(mymax):
            _namelist = "" if i >= len(namelist) else namelist[i]
            _post_staginglist = "" if i >= len(post_staginglist) else post_staginglist[i]
            _dg_grouplist = "" if i >= len(dg_grouplist) else dg_grouplist[i]
            _nd_status = "OK"  if i == 0 else ""
            _keyl = "" if i > 0 else _key

            print("|{0:<{col0}}|{1:<{col1}}|{2:<{col2}}|{3:<{col3}}|{green}{4:<{col4}}{endc}|".
                  format(_keyl,_namelist,_post_staginglist,
                  _dg_grouplist,_nd_status, green=bcolors.OKGREEN,endc=bcolors.ENDC,
                  col0=6,col1=pcol1,col2=pcol2,col3=pcol3,col4=15))

      else : 
        NOT_DEPLOYED = 1
        if mymax == 1:
          print("|{0:<{col0}}|{1:<{col1}}|{2:<{col2}}|{3:<{col3}}|{warn}{4:<{col4}}{endc}|".format(_key,v['name'],v['poststaging-template'],
                      v['dg-group'],"NOT OK",warn=bcolors.OKWARN,endc=bcolors.ENDC,
                      col0=6,col1=pcol1,col2=pcol2,col3=pcol3,col4=15))
        else:
          for i in range(mymax):
            _namelist = "" if i >= len(namelist) else namelist[i]
            _post_staginglist = "" if i >= len(post_staginglist) else post_staginglist[i]
            _dg_grouplist = "" if i >= len(dg_grouplist) else dg_grouplist[i]
            _nd_status = "NOT OK"  if i == 0 else ""
            _keyl = "" if i > 0 else _key

            print("|{0:<{col0}}|{1:<{col1}}|{2:<{col2}}|{3:<{col3}}|{warn}{4:<{col4}}{endc}|".
                  format(_keyl,_namelist,_post_staginglist,
                  _dg_grouplist,_nd_status, warn=bcolors.OKWARN,endc=bcolors.ENDC,
                  col0=6,col1=pcol1,col2=pcol2,col3=pcol3,col4=15))
      if  cnt%new_out_line == 0 and _key !=  len(comb_dict) :
        #print(new_out_line)
        print("-" * int(4+pcol1+pcol2+pcol3+15+6))
        yes_or_no3("Press any key to continue",1 )
        print("-" * int(4+pcol1+pcol2+pcol3+15+6))
        print("|{0:<{col0}}|{1:<{col1}}|{2:<{col2}}|{3:<{col3}}|{4:<{col4}}|".format("Idx","Name","P-STemplate","DG-Group","Status",
                                              col0=6,col1=pcol1,col2=pcol2,col3=pcol3,col4=15))
        print("-" * int(4+pcol1+pcol2+pcol3+15+6))
        #Now reset things back
        new_out_line = out_line 
        cnt = 0

    print("-" * int(6+pcol1+pcol2+pcol3+15+6))
    print(bcolors.ENDC)
    if NOT_DEPLOYED == 1:
      mlog.warn (bcolors.OKWARN + "If any of the Templates or Devices are in error, the table above will show as NOT OK.\n" + 
           " You must fix all the errors on the Director and then YOU MUST re-run the program as: \n" +
           "          ./VMMigr_phase2.py -f vm_phase3.json -r                    \n" + 
           "NOTE: The input file MUST be vm_phase3.json and the -r option MUST be provided.\n"+ 
           "You can re-run the program  multiple time using the same command.\n" +
           "IF THE ERRORS ARE NOT FIXED, the corresponding devices will NOT be migrated." + bcolors.ENDC)

# main
def main():
    #global vnms, analy, cntlr, cust, admin, auth, debug, mlog, mdict
    global mlog, mdict, newdir, olddir
    #mdict = readfile("in_rest.cfg")
    debug = args['debug']
    infile = args['file']
    reread=args['read']
    LOG_SIZE = 8 * 1024 * 1024
    if reread and infile.find("vm_phase3.json") == -1:
      print("If you are using re-read option the file MUST be vm_phase3.json")
      usage()
      sys.exit(0)
    mlog,f_hndlr,s_hndlr=glbl.init(infile,LOG_FILENAME, LOG_SIZE,"VMMigr2",debug)
    if debug == 0:
      glbl.setup_level(f_hndlr, logging.INFO) # Setting fileHandler loglevel
      glbl.setup_level(s_hndlr, logging.WARNING) # Setting stream Handler loglevel
    else:
      glbl.setup_level(f_hndlr, logging.INFO)
      glbl.setup_level(s_hndlr, logging.INFO)
    mlog.warn(bcolors.OKWARN + "===============Starting Phase 2 Execution LOGS={0} ==========".format(LOG_FILENAME) + bcolors.ENDC)
    if not reread: 
      mlog.warn(bcolors.OKWARN + "Before we proceed below are a few directions:\n" + 
                              "Have you Copied the backup from OLD Director to NEW Director [Sec 1 in cheat_sheet.txt]\n" + 
                              "Have you restored the NEW Director using the backup [Sec 2 in cheat_sheet.txt]\n" + 
                              "Have you ensured that communication from NEW Director to OLD Controller is NOT possible [Sec 3 in cheat_sheet.txt]\n" + 
                              "Did you check the passswords in the input file to allow UI access [Sec 4 in cheat_sheet.txt]\n" + bcolors.ENDC)
    ret = yes_or_no2("To continue press y and to exit press n : " )
    if ret == 0 : return
    elif ret == 1: pass
    if debug == 0:
        mlog.setLevel(logging.WARNING)

    # Initialize director information. Note the variables are global
    newdir= {'vd_ip' :  glbl.admin.data['new_dir']['vd_ip'],
            'vd_rest_port': glbl.admin.data['new_dir']['vd_rest_port'],
            'auth': glbl.admin.data['new_dir']['auth'] }
    olddir= {'vd_ip' :  glbl.admin.data['old_dir']['vd_ip'],
            'vd_rest_port': glbl.admin.data['old_dir']['vd_rest_port'],
            'auth': glbl.admin.data['old_dir']['auth'] }
    #glbl.cntlr.data["old_cntlr"] = []
    #if not reread and os.path.exists("vm_phase3.json"):
    #  newvdict = read_input_file("vm_phase3.json",1)
    #  if ('Controller' in newvdict and 'old_cntlr' in newvdict['Controller'] and 
    #    len(newvdict['Controller']['old_cntlr']) > 0 ):
    #    # we found the data -- now we can replace the controller list
    #    glbl.cntlr.data["old_cntlr"] = newvdict['Controller']['old_cntlr']

    #write_outfile(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin)
    get_terminal_size()

    # before we write the output file we need to see if old_cntlr data is present or not
    perform_initial_checks(reread)


    fil = OrderedDict()
    #############################New###########################
    fil['GET_RELEASE_INFO.json'] = get_dir_release_info
    fil['CREATE_TIME_ZONE.json'] = get_dir_time_zones 
    fil['CREATE_NTP_SERVER.json'] =  get_dir_ntp_server 
    fil['CREATE_DNS_SERVER.json'] = get_dir_dns_server
    fil['SET_NMS_PROVIDER.json'] = set_nms_provider
    fil['GET_PARENT_ORGID.json'] = get_parent_orgid
    fil['GET_WAN_NETWORK.json'] = get_wan_ntwk

    #fil['CREATE_ANALYTICS_CLUSTER.json'] = get_dir_analytics_cluster
    #fil['DELETE_AUTH_CONNECTOR.json'] = get_dir_auth_connector_config
    #fil['CREATE_AUTH_CONNECTOR.json'] = get_dir_auth_connector_config
    #fil['CREATE_DEFAULT_AUTH_CONNECTOR.json'] = get_dir_default_auth_connector
    #fil['CREATE_AUTH_CONNECTOR_CONFIG.json'] = get_dir_auth_connector_config

    fil['CREATE_CONTROLLER.json'] = create_controller
    fil['DEPLOY_CONTROLLER_WORKFLOW.json'] = deploy_controller
    fil['CREATE_PEER_CONTROLLER.json'] = create_controller
    fil['DEPLOY_PEER_CONTROLLER_WORKFLOW.json'] = deploy_controller
    fil['ORG_DEPLOY_WORKFLOW.json'] = deploy_org_workflow

    fil['SET_CONTROLLER_CONFIG_BUILD.json'] = create_controller_build
    fil['SET_CONTROLLER_VNI.json'] = create_dns_config
    fil['SET_CONTROLLER_ROUTING.json'] = create_dns_config
    fil['SET_CONTROLLER_NTP.json'] = create_dns_config
    fil['SET_CONTROLLER_OAM_ALARMS.json'] = create_dns_config
    fil['SET_CONTROLLER_ORG_SERVICES.json'] = create_dns_config
    fil['SET_CONTROLLER_ORG.json'] = create_dns_config
    fil['SET_CONTROLLER_SYSTEM.json'] = create_dns_config
    fil['SET_CONTROLLER_COMMIT.json'] = create_dns_config
    fil['SET_CONTROLLER_SYNCH.json'] = set_cntlr_synch_to

    fil['SET_PEER_CONTROLLER_CONFIG_BUILD.json'] = create_controller_build
    fil['SET_PEER_CONTROLLER_VNI.json'] = create_dns_config
    fil['SET_PEER_CONTROLLER_ROUTING.json'] = create_dns_config
    fil['SET_PEER_CONTROLLER_NTP.json'] = create_dns_config
    fil['SET_PEER_CONTROLLER_OAM_ALARMS.json'] = create_dns_config
    fil['SET_PEER_CONTROLLER_ORG_SERVICES.json'] = create_dns_config
    fil['SET_PEER_CONTROLLER_ORG.json'] = create_dns_config
    fil['SET_PEER_CONTROLLER_SYSTEM.json'] = create_dns_config
    fil['SET_PEER_CONTROLLER_COMMIT.json'] = create_dns_config
    fil['SET_PEER_CONTROLLER_SYNCH.json'] = set_cntlr_synch_to
    fil['BUILD_DEPLOY_REF_TMPLT.json'] = create_reference_tmplt
    if not reread:
      fil['GET_DEVICE_GROUP.json'] = get_device_group
    else: 
      fil['GET_DEVICE_GROUP.json'] = get_device_group_new

    template_path = os.path.abspath(sys.argv[0]).rsplit("/",1)[0] + "/" + "in_phase2"
    if not os.path.exists( template_path ):
      sys.exit("Directory: {0} does not exists".format(template_path)) 
    tmp_outpath = os.path.abspath(sys.argv[0]).rsplit("/",1)[0] + "/" + "in_phase3"
    if not os.path.exists( tmp_outpath ):
      os.makedirs(tmp_outpath )

    template_loader = jinja2.FileSystemLoader(searchpath=template_path)
    template_env = jinja2.Environment(loader=template_loader,undefined=jinja2.StrictUndefined)
    template_env.filters['jsonify'] = json.dumps

    process_normal(fil,template_env,template_path,reread)

    if not reread : post_script()
    show_devices_status( )
    if NOT_DEPLOYED == 0:
      mlog.warn(bcolors.OKWARN + "A partition is a logical grouping of a number of devices. In order to speed up\n" +
                                 "the process of migration one can partition the device list and then run the Phase 3 scripts\n" +
                                 "on each one of then separately. You can customize which device goes to which partition (Max=4)" + bcolors.ENDC)
      partition_y_or_n = yes_or_no2(bcolors.OKWARN + "Do you want to partition the list of Devices. Type y or n" + bcolors.ENDC)
      if partition_y_or_n == 1:
        process_partition()

      mlog.warn(bcolors.OKWARN + "==============Completed ==========" + bcolors.ENDC)
      mlog.warn(bcolors.OKWARN + "Verify that the Old Dir is accessible and proceed to run the next script.\n" + bcolors.ENDC)



if __name__ == "__main__":

  argcheck()
  LOG_FILENAME = 'vmMigrate.log'
  _cnt1 = 0
  if os.path.isfile(LOG_FILENAME):
    with open(LOG_FILENAME,"r") as fp:
      for _cnt1,line in enumerate(fp):
        pass
    fp.close()
    _cnt1 = _cnt1 + 1

  main()

  _errlog=""
  _cnt2 = 0
  if os.path.isfile(LOG_FILENAME):
    with open(LOG_FILENAME,"r") as fp:
      for _cnt2,line in enumerate(fp):
        if _cnt2 >= _cnt1:
          if re.search("ERROR -",line):
            _errlog = _errlog + line
    fp.close()
    if len( _errlog ) > 0:
      fp=open("vmphase2.err","w+")
      fp.write(_errlog)
      fp.close()
      if mlog:
        mlog.warn(bcolors.OKWARN + "Error log vmphase2.err is created since there were errors." + bcolors.ENDC)


