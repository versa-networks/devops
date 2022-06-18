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
#import uuid
from pprint import pprint
import copy
import logging
import logging.handlers
import glbl
import common 

pyVer = sys.version_info
if pyVer.major == 3:
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
mlog = None
mdict = None
MYLINES = 0
MYCOL = 0

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
  """ Add and check arguments for the script
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
    sys.exit("Exiting")

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
    global mlog
    try:
      _jstr = json.loads(_str,**kwargs)
      return _jstr
    except Exception as ex:
       mlog.error('Json load failed: {}'.format(ex))
       sys.exit('Json load failed: {}'.format(ex))

def get_default( _method, _uri,_payload,resp='200', ofile=None):
    global vnms, analy, cntlr, cust, mlog
    vdict = {}
    mlog.info("In function " + get_default.__name__)
    vdict = {'body': _payload, 'resp': resp, 'method': _method, 'uri': _uri}
    [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
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

def write_outfile(_vnms,_analy,_cntlr,_cust, _admin):
    global vnms, analy, cntlr, cust, admin, mlog
    mlog.info("In function {0} : Output file:vm_phase4.json".format(write_outfile.__name__))
    jstr = {}
    jstr["Vnms"] = _vnms.data
    jstr["Analytics"] = _analy.data
    jstr["Controller"] = _cntlr.data
    jstr["Admin"] = _admin.data
    jstr["Customer"] = _cust.data
    fin=open("vm_phase4.json", "w+")
    mstr1 = json.dumps(jstr, indent=4)
    fin.write(mstr1)
    fin.close()


def get_old_peer_controller_name(_cntlrdata):
    for _cntlr in glbl.cntlr.data['old_cntlr']:
      if _cntlrdata == 2 and "peerControllers" in _cntlr :
        return _cntlr
      elif _cntlrdata == 1 and "peerControllers" not in _cntlr :
        return _cntlr



def get_new_peer_controller_name(_cntlrdata):
    for _cntlr in glbl.cntlr.data['new_cntlr']:
      if _cntlrdata == 2 and "peerControllers" in _cntlr :
        return _cntlr
      elif _cntlrdata == 1 and "peerControllers" not in _cntlr :
        return _cntlr

def get_n_fill_bind_data(_method, _uri, _payload,resp='200',vd_data=None, device=None):
    global vnms, analy, cntlr, cust, mlog

    if device is None or vd_data is None :
      mlog.error("Bad inputs in function {0} ".format(get_n_fill_bind_data.__name__))
      return
    
    mlog.info("In function {0} with device = {1} ".format(get_n_fill_bind_data.__name__, device["name"]))
    dg_group = device["dg-group"]
    devlist = list(filter(lambda x: x['dg-group'] == dg_group, glbl.vnms.data["devices"]))
    uri = ("/nextgen/binddata/templateData/template/" + device["poststaging-template"] + 
          "/devicegroup/" + dg_group + "?offset=0&limit=25")
    payload = {}
    resp2 = '202'
    vdict = {}
    vdict = {'body': payload, 'resp': resp, 'resp2': resp2, 'method': "GET", 'uri': uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth']
    }
    [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json_loads(resp_str)
      mlog.info("Bind Data = {0}".format(json.dumps(jstr,indent=4)))
      old_p_cntlr = get_old_peer_controller_name(2)
      new_p_cntlr = get_new_peer_controller_name(2)
      found = 0
      if "deviceTemplateVariable" in jstr:
        for j in jstr["deviceTemplateVariable"]:  
          dev = None
          for i in devlist:
            if j["device"] == i["name"]:
              dev = i
              break
          if dev is None: 
            mlog.error ("Could not find device = {0}".format(j["device"]))
            continue
            
          if "variableBinding" in j and "attrs" in j["variableBinding"]:
            for var in j["variableBinding"]["attrs"] :
              if (var["name"] == '{$v_' + cust.data["custName"] + "_" + new_p_cntlr["controllerName"]
                             + '-Profile_Local_auth_email_identifier__IKELIdentifier}'):
                  var["value"]  = dev["local_auth_identity"]
                  found = found + 1
              elif (var["name"] == '{$v_' + cust.data["custName"] + "_" + new_p_cntlr["controllerName"]
                                    + '-Profile_Local_auth_email_key__IKELKey}'):
                  var["value"]  = dev["local_auth_key"]
                  found = found + 1
      if found >= 2 : 
        payload = json.dumps(jstr)
        vdict = {}
        uri = ("/nextgen/binddata/templateData/template/" + device["poststaging-template"] + 
              "/devicegroup/" + dg_group)
        vdict = {'body': payload, 'resp': resp, 'resp2': resp2, 'method': 'PUT', 'uri': uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth']
        }

        mlog.info("Sending PUT from function {0}".format(get_n_fill_bind_data.__name__))
        [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
        if len(resp_str) > 3:
          jstr = json_loads(resp_str)
          mlog.info("Bind data after PUT = {0}".format(json.dumps(jstr,indent=4)))
      for i in devlist:
        for j in glbl.vnms.data["devices"]:
          if i["name"] == j["name"] :
            j["status"] = ""
            j["status"] = "Complete"
      write_outfile(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin)
              


#def get_hub_cntlr_device_ipsec_vpn_profile( _method, _uri, _payload,resp='200',vd_data=None, device=None,_cntlr=2):
def get_hub_cntlr_device_ipsec_vpn_profile( vd_data=None, device=None,_cntlr=2):
    global vnms, analy, cntlr, cust, mlog

    if device is None or vd_data is None :
      mlog.error("Bad inputs in function {0} ".format(get_hub_cntlr_device_ipsec_vpn_profile.__name__))
      return

    if _cntlr != 1 : # we will do this only if _cntlr = 1
      return ''
    mlog.warn("Modifying IPSEC VPN Profile details for device = {0} since it is a Hub-Controller".format(device["name"]))
    _uri="/api/config/devices/device/" + device["name"] + "/config/orgs/org-services/alpha/ipsec/vpn-profile?deep=true&offset=0&limit=25"
    _payload = {}
    resp = '200'
    resp2 = '202'
    vdict = {}
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': "GET" , 'uri': _uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth']
    }
    [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json_loads(resp_str)
      newjstr = json_loads(resp_str)
      #mlog.info("IPSEC VPN Profile = {0}".format(json.dumps(jstr,indent=4)))
      scrub_list = [ "operations"]
      for i in scrub_list:
        common.scrub(jstr,i)

      found = 0
      vpn_profile = []
      vpn_data = []
      if "vpn-profile" in jstr: 
        south_ip = glbl.vnms.data['director'][0]['director_southIP'] + "/32" 
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
        time.sleep(10)
        payload = json.dumps(vpn_data[i])
        vdict = {}
        uri =  _uri.rsplit('?',1)[0] + "/" + vpn_profile[i]
        vdict = {'body': payload, 'resp': resp, 'resp2': resp2, 'method': 'PUT', 'uri': uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth']
        }
        mlog.info("Sending PUT from function {0} for VPN Profile={1}".format(get_hub_cntlr_device_ipsec_vpn_profile.__name__,vpn_profile[i]))
        [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)

        if len(resp_str) > 3:
          jstr = json_loads(resp_str)
          mlog.info("IPSEC VPN Profile after PUT = {0}".format(json.dumps(jstr,indent=4)))
    else : 
      mlog.error("Not Sending PUT from function {0}".format(get_hub_cntlr_device_ipsec_vpn_profile.__name__))
    return ''
    

def get_device_ipsec_vpn_profile( _method, _uri, _payload,resp='200',vd_data=None, device=None,_cntlr=2):
    global vnms, analy, cntlr, cust, mlog

    if device is None or vd_data is None :
      mlog.error("Bad inputs in function {0} ".format(get_device_ipsec_vpn_profile.__name__))
      return

    mlog.warn("Modifying IPSEC VPN Profile details for device = {0} ".format(device["name"]))
    resp2 = '202'
    vdict = {}
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': _uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth']
    }
    [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json_loads(resp_str)
      newjstr = json_loads(resp_str)
      #mlog.info("IPSEC VPN Profile = {0}".format(json.dumps(jstr,indent=4)))
      scrub_list = [ "operations"]
      for i in scrub_list:
        common.scrub(jstr,i)

      if is_hub_cntlr_present() and check_if_device_onboarded_to_hcn_device(device):
        #get_hub_cntlr_device_ipsec_vpn_profile( _method, _uri, _payload,resp='200',vd_data=vd_data, device=device,_cntlr=_cntlr)
        mlog.warn("Device={0} onboarded to Hub Controller... returning".format(device["name"]))
        return
      old_p_cntlr = get_old_peer_controller_name(_cntlr)
      new_p_cntlr = get_new_peer_controller_name(_cntlr)
      # Delete the OlD VPN profile first
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
      found = 0
      if "vpn-profile" in jstr: 
        for vpn in jstr["vpn-profile"] :
          #if vpn["name"] == (old_p_cntlr["name"] + "-Profile"):
          if vpn["name"].find(old_p_cntlr["name"]) != -1:
            vpn['name'] = new_p_cntlr["controllerName"] + "-Profile"
            if "local-auth-info" in vpn:
              # Key
              a = vpn["local-auth-info"]['key']
              if a.find("$v_") != -1:
                a=re.sub(old_p_cntlr["name"], new_p_cntlr["controllerName"], a, count=0,flags=0)
                vpn["local-auth-info"]['key'] = a
              else:
                if _cntlr == 2: 
                  vpn["local-auth-info"]['key'] = device["local_auth_key"]
                else:
                  vpn["local-auth-info"]['key'] = device["local1_auth_key"]
              # Email identifier
              b = vpn["local-auth-info"]['id-string']
              if b.find("$v_") != -1:
                b=re.sub(old_p_cntlr["name"], new_p_cntlr["controllerName"], b, count=0,flags=0)
                vpn["local-auth-info"]['id-string'] = b
              else:
                if _cntlr == 2: 
                  vpn["local-auth-info"]['id-string'] = device["local_auth_identity"]
                else:
                  vpn["local-auth-info"]['id-string'] = device["local1_auth_identity"]
              #vpn["local-auth-info"]['key'] = device["local_auth_key"]
              #vpn["local-auth-info"]['id-string'] = device["local_auth_identity"]
              #vpn["local-auth-info"]['key'] = a
              #vpn["local-auth-info"]['id-string'] = b
              found = found + 1
            if "peer-auth-info" in vpn:
              if _cntlr == 2: 
                vpn["peer-auth-info"]["id-string"] = device["remote_auth_identity"]
              else:
                vpn["peer-auth-info"]["id-string"] = device["remote1_auth_identity"]
              found = found + 1
            if found == 2: break
          #else:
          #  # New addition
          #  jstr["vpn-profile"].remove(vpn)

        # Only send the PATCH if we found all our elements
        if found == 2:
          #mlog.info("IPSEC VPN Profile after Deletion = {0}".format(json.dumps(jstr,indent=4)))
          time.sleep(10)
          payload = json.dumps(jstr)
          vdict = {}
          uri =  _uri.rsplit('?',1)[0]
          #uri = uri + "?unhide=deprecated"
          vdict = {'body': payload, 'resp': resp, 'resp2': resp2, 'method': 'PATCH', 'uri': uri,
                'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
                 'auth': vd_data['auth']
          }
          mlog.info("Sending PATCH from function {0}".format(get_device_ipsec_vpn_profile.__name__))
          [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)

          if len(resp_str) > 3:
            jstr = json_loads(resp_str)
            mlog.info("IPSEC VPN Profile after PATCH = {0}".format(json.dumps(jstr,indent=4)))

          #if device["type"] == "hub-controller": 
          #  get_hub_cntlr_device_ipsec_vpn_profile( _method, _uri, _payload,resp='200',vd_data=vd_data, device=device,_cntlr=_cntlr)

        else:
          mlog.error("Not Sending PATCH from function {0}".format(get_ipsec_vpn_profile.__name__))
    else : 
      mlog.error("Not Sending PATCH from function {0}".format(get_ipsec_vpn_profile.__name__))
    return ''

def get_ipsec_vpn_profile( _method, _uri, _payload,resp='200',vd_data=None, device=None):
    global vnms, analy, cntlr, cust, mlog

    if device is None or vd_data is None :
      mlog.error("Bad inputs in function {0} ".format(get_ipsec_vpn_profile.__name__))
      return

    mlog.info("In function {0} with device = {1} ".format(get_ipsec_vpn_profile.__name__, device["name"]))
    resp2 = '202'
    vdict = {}
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': _uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth']
    }
    [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json_loads(resp_str)
      mlog.info("IPSEC VPN Profile = {0}".format(json.dumps(jstr,indent=4)))
      old_p_cntlr = get_old_peer_controller_name(2)
      new_p_cntlr = get_new_peer_controller_name(2)
      found = 0
      if "vpn-profile" in jstr: 
        for vpn in jstr["vpn-profile"] :
          if vpn["name"] == (old_p_cntlr["name"] + "-Profile"):
            vpn['name'] = new_p_cntlr["controllerName"]
            if "local-auth-info" in vpn:
              # Key
              a = vpn["local-auth-info"]['key']
              if a.find("$v_") > 0:
                a=re.sub(old_p_cntlr["name"], new_p_cntlr["controllerName"], a, count=0,flags=0)
                vpn["local-auth-info"]['key'] = a
              else:
                vpn["local-auth-info"]['key'] = ('{$v_' + cust.data["custName"] + "_" + new_p_cntlr["controllerName"]
                                    + '-Profile_Local_auth_email_key__IKELKey}')
              # Email identifier
              b = vpn["local-auth-info"]['id-string']
              if b.find("$v_") > 0:
                b=re.sub(old_p_cntlr["name"], new_p_cntlr["controllerName"], b, count=0,flags=0)
                vpn["local-auth-info"]['id-string'] = b
              else:
                vpn["local-auth-info"]['id-string'] = ('{$v_' + cust.data["custName"] + "_" + new_p_cntlr["controllerName"]
                             + '-Profile_Local_auth_email_identifier__IKELIdentifier}')
              #vpn["local-auth-info"]['key'] = device["local_auth_key"]
              #vpn["local-auth-info"]['id-string'] = device["local_auth_identity"]
              #vpn["local-auth-info"]['key'] = a
              #vpn["local-auth-info"]['id-string'] = b
              found = found + 1
            if "peer-auth-info" in vpn:
              vpn["peer-auth-info"]["id-string"] = device["remote_auth_identity"]
              found = found + 1
            if found == 2: break

        # Only send the PATCH if we found all our elements
        if found == 2:
          payload = json.dumps(jstr)
          vdict = {}
          uri =  _uri.rsplit('?',1)[0]
          uri = uri + "?unhide=deprecated"
          vdict = {'body': payload, 'resp': resp, 'resp2': resp2, 'method': 'PATCH', 'uri': uri,
                'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
                 'auth': vd_data['auth']
          }
          mlog.info("Sending PATCH from function {0}".format(get_ipsec_vpn_profile.__name__))
          [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)

          if len(resp_str) > 3:
            jstr = json_loads(resp_str)
            mlog.info("IPSEC VPN Profile after PATCH = {0}".format(json.dumps(jstr,indent=4)))

          if out == 1:
            payload = {}
            vdict = {}
            uri =  _uri.rsplit('?',1)[0]
            uri =  uri + "/" + old_p_cntlr["name"] + "-Profile"
            vdict = {'body': payload, 'resp': resp, 'resp2': resp2, 'method': 'DELETE', 'uri': uri,
                  'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
                   'auth': vd_data['auth']
            }
            mlog.info("Sending DELETE from function {0}".format(get_ipsec_vpn_profile.__name__))
            [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
            get_n_fill_bind_data(_method, _uri, _payload,resp='200',vd_data=vd_data, device=device)
          else:
            mlog.error("Not Sending DELETE from function {0}".format(get_ipsec_vpn_profile.__name__))
        else:
          mlog.error("Not Sending PATCH from function {0}".format(get_ipsec_vpn_profile.__name__))
    else : 
      mlog.error("Not Sending PATCH from function {0}".format(get_ipsec_vpn_profile.__name__))
    return ''

def get_device_system_controller( _method, _uri, _payload,resp='200',vd_data=None, device=None, newdict=None,_cntlr=2):
    global vnms, analy, cntlr, cust, mlog

    if device is None or vd_data is None :
      mlog.error("Bad inputs in function {0} ".format(get_device_system_controller.__name__))
      return

    mlog.warn("Modifying System Controller details for device = {0} ".format(device["name"]))
    resp2 = '202'
    vdict = {}
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': _uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth']
    }
    [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json_loads(resp_str)
      #mlog.info("System Controller = {0}".format(json.dumps(jstr,indent=4)))
      if is_hub_cntlr_present() and check_if_device_onboarded_to_hcn_device(device):
        mlog.warn("Device={0} onboarded to Hub Controller... returning".format(device["name"]))
        return
      old_p_cntlr = get_old_peer_controller_name(_cntlr)
      new_p_cntlr = get_new_peer_controller_name(_cntlr)
      # first let us do the delete
      payload = {}
      vdict = {}
      uri =  _uri.rsplit('?',1)[0]
      uri =  uri + "/" + old_p_cntlr["name"] 
      vdict = {'body': payload, 'resp': resp, 'resp2': resp2, 'method': 'DELETE', 'uri': uri,
                  'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
                   'auth': vd_data['auth']
      }
      [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
      if len(resp_str) > 3:
        newjstr = json_loads(resp_str)
        #mlog.info("System Controller = {0}".format(json.dumps(newjstr,indent=4)))

      if "controller" in jstr:
        for i in jstr["controller"] :
          if i['name'] != old_p_cntlr["name"] :
            jstr["controller"].remove(i)

        found = 0
        for i in jstr["controller"] :
          if i['name'] == old_p_cntlr["name"] :
            i['name'] = new_p_cntlr["controllerName"]
            i["site-name"] = new_p_cntlr["controllerName"]
            if "transport-addresses" in i and "transport-address" in i["transport-addresses"]:
                for j in  i["transport-addresses"]["transport-address"]:
                  if "Internet" in j["transport-domains"]:
                    j['name'] = new_p_cntlr["controllerName"] + '-Transport-INET'
                    j['ip-address'] = new_p_cntlr["inet_public_ip_address"]
                    found = found + 1
                    mlog.info("Added INET pulic IP: {0}".format(new_p_cntlr["inet_public_ip_address"]))
                  elif "MPLS" in j["transport-domains"]:
                    #elif len(j["transport-domains"]) > 1  and "mpls_public_ip_address" in new_p_cntlr:
                    j['name'] = new_p_cntlr["controllerName"] + '-Transport-MPLS'
                    j['ip-address'] = new_p_cntlr["mpls_public_ip_address"]
                    found = found + 1
                    mlog.info("Added MPLS pulic IP: {0}".format(new_p_cntlr["mpls_public_ip_address"]))
                  else:
                    mlog.error("Unidentified Transport Domain:{0} ".format(' '.join(j["transport-domains"])))
                    
        if found > 0 : 
          # since we are doing a POST we now need to remove the list
          newjstr = {}
          newjstr = { "controller" : jstr["controller"][0] }
          payload = json.dumps(newjstr)
          vdict = {}
          uri =  _uri.rsplit('?',1)[0]
          # For POST to work properly we need to modify the uri too
          uri =  uri.rsplit('/',1)[0]
          vdict = {'body': payload, 'resp': resp, 'resp2': resp2, 'method': 'POST', 'uri': uri,
                'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
                 'auth': vd_data['auth']
          }
          [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)

          if len(resp_str) > 3:
            jstr = json_loads(resp_str)
            mlog.info("System Controller after PATCH = {0}".format(json.dumps(jstr,indent=4)))

          [out, resp_str] = common.newcall(newdict,content_type='json',ncs_cmd="no",jsonflag=1)
        else: 
          mlog.error("Could not find anything to add in function {0} for device = {1} ".format(get_system_controller.__name__,device["name"] ))
    else:
      mlog.error("Could not send PATCH from function {0} for device = {1} ".format(get_system_controller.__name__,device["name"] ))

    return ''

def get_system_controller( _method, _uri, _payload,resp='200',vd_data=None, device=None):
    global vnms, analy, cntlr, cust, mlog

    if device is None or vd_data is None :
      mlog.error("Bad inputs in function {0} ".format(get_system_controller.__name__))
      return

    mlog.info("In function {0} with device = {1} ".format(get_system_controller.__name__, device["name"]))
    resp2 = '202'
    vdict = {}
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': _uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth']
    }
    [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json_loads(resp_str)
      mlog.info("System Controller = {0}".format(json.dumps(jstr,indent=4)))
      old_p_cntlr = get_old_peer_controller_name(2)
      new_p_cntlr = get_new_peer_controller_name(2)
      if "controller" in jstr:
        found = 0
        for i in jstr["controller"] :
          if i['name'] == old_p_cntlr["name"] :
            i['name'] = new_p_cntlr["controllerName"]
            i["site-name"] = new_p_cntlr["controllerName"]
            if "transport-addresses" in i and "transport-address" in i["transport-addresses"]:
                for j in  i["transport-addresses"]["transport-address"]:
                  if "Internet" in j["transport-domains"]:
                    j['name'] = new_p_cntlr["controllerName"] + '-Transport-INET'
                    j['ip-address'] = new_p_cntlr["inet_public_ip_address"]
                    found = found + 1
                    mlog.info("Added INET pulic IP: {0}".format(new_p_cntlr["inet_public_ip_address"]))
                  elif "MPLS" in j["transport-domains"]:
                    #elif len(j["transport-domains"]) > 1  and "mpls_public_ip_address" in new_p_cntlr:
                    j['name'] = new_p_cntlr["controllerName"] + '-Transport-MPLS'
                    j['ip-address'] = new_p_cntlr["mpls_public_ip_address"]
                    found = found + 1
                    mlog.info("Added MPLS pulic IP: {0}".format(new_p_cntlr["mpls_public_ip_address"]))
                  else:
                    mlog.error("Unidentified Transport Domain:{0} ".format(' '.join(j["transport-domains"])))
                    
        if found > 0 : 
          payload = json.dumps(jstr)
          vdict = {}
          uri =  _uri.rsplit('?',1)[0]
          vdict = {'body': payload, 'resp': resp, 'resp2': resp2, 'method': 'PATCH', 'uri': uri,
                'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
                 'auth': vd_data['auth']
          }
          [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)

          if len(resp_str) > 3:
            jstr = json_loads(resp_str)
            mlog.info("System Controller after PATCH = {0}".format(json.dumps(jstr,indent=4)))

          if out == 1:
            payload = {}
            vdict = {}
            uri =  uri + "/" + old_p_cntlr["name"] 
            vdict = {'body': payload, 'resp': resp, 'resp2': resp2, 'method': 'DELETE', 'uri': uri,
                  'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
                   'auth': vd_data['auth']
            }
            [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
          else:
            mlog.error("Not Sending DELETE from function {0} for device = {1} ".format(get_system_controller.__name__,device["name"]))
        else: 
          mlog.error("Could not find anything to add in function {0} for device = {1} ".format(get_system_controller.__name__,device["name"] ))
    else:
      mlog.error("Could not send PATCH from function {0} for device = {1} ".format(get_system_controller.__name__,device["name"] ))

    return ''

def is_hub_cntlr_present():
    global vnms, analy, cntlr, cust, mlog
    if glbl.vnms.data['hub_cntlr_present'] == 1: return True
    return False

def check_if_device_onboarded_to_hcn(jstr):

    if "controller" in jstr:
      found = 0

      for i in jstr["controller"] :
        for _cntlr in glbl.cntlr.data['old_cntlr']:
          if i['name'] == _cntlr['name'] :
            found = found + 1
      if found > 0: return False
      else: return True

    return False

def check_if_device_onboarded_to_hcn_device(device):
  if "onboard_to_hcn" in device and device["onboard_to_hcn"] == 1 : return True
  return False
     


#def get_device_sdwan_site( _method, _uri, _payload,resp='200',vd_data=None, device=None,_cntlr=2):
def get_device_sdwan_site(vd_data=None, device=None,_cntlr=2):
    global vnms, analy, cntlr, cust, mlog

    if device is None or vd_data is None :
      mlog.error("Bad inputs in function {0} ".format(get_device_sdwan_controller.__name__))
      return ''

    if _cntlr != 1 : # we will do this only if _cntlr = 1
      return ''
    #mlog.warn("Modifying SDWAN Controller details for device = {0} ".format(device["name"]))
    uri = "/api/config/devices/device/" + device["name"] + "/config/orgs/org/alpha/sd-wan/site/branch-vnf-manager"
    _payload = {}
    resp = '200'
    resp2 = '202'
    vdict = {}
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': "GET" , 'uri': uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth']
    }
    [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      time.sleep(10)
      south_ip = [i['director_southIP'] + "/32" for i in glbl.vnms.data['director']]
      jstr = json_loads(resp_str)
      #mlog.info("SDWAN Controller = {0}".format(json.dumps(jstr,indent=4)))
      if "branch-vnf-manager" in jstr and "ip-addresses" in jstr["branch-vnf-manager"]:
        jstr["branch-vnf-manager"]["ip-addresses"] = south_ip
      # First the delete
      payload = json.dumps(jstr)
      vdict = {}
      vdict = {'body': payload, 'resp': resp, 'resp2': resp2, 'method': 'PUT', 'uri': uri,
            'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
             'auth': vd_data['auth']
      }
      [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
      if len(resp_str) > 3:
        newjstr = json_loads(resp_str)
        #mlog.info("SDWAN Controller = {0}".format(json.dumps(newjstr,indent=4)))
    else: 
      mlog.error("Could not send PUT from function {0} for device = {1} ".format(get_device_sdwan_site.__name__,device["name"] ))
    return ''

def get_device_sdwan_controller( _method, _uri, _payload,resp='200',vd_data=None, device=None,_cntlr=2):
    global vnms, analy, cntlr, cust, mlog

    if device is None or vd_data is None :
      mlog.error("Bad inputs in function {0} ".format(get_device_sdwan_controller.__name__))
      return

    mlog.warn("Modifying SDWAN Controller details for device = {0} ".format(device["name"]))
    resp2 = '202'
    vdict = {}
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': _uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth']
    }
    [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json_loads(resp_str)
      #mlog.info("SDWAN Controller = {0}".format(json.dumps(jstr,indent=4)))
      if is_hub_cntlr_present() and "onboard_to_hcn" not in device and check_if_device_onboarded_to_hcn(jstr):
        device["onboard_to_hcn"] = 1
        #get_device_sdwan_site( _method, _uri, _payload,resp='200',vd_data=vd_data, device=device,_cntlr=_cntlr)
        mlog.warn("Device={0} onboarded to Hub Controller... returning".format(device["name"]))
        return
      elif is_hub_cntlr_present() and "onboard_to_hcn" in device and device["onboard_to_hcn"] == 1:
        #get_device_sdwan_site( _method, _uri, _payload,resp='200',vd_data=vd_data, device=device,_cntlr=_cntlr)
        mlog.warn("Device={0} onboarded to Hub Controller... returning".format(device["name"]))
        return
      else:
        device["onboard_to_hcn"] = 0

      old_p_cntlr = get_old_peer_controller_name(_cntlr)
      new_p_cntlr = get_new_peer_controller_name(_cntlr)
      # First the delete
      payload = {}
      vdict = {}
      uri =  _uri.rsplit('?',1)[0]
      uri =  uri + "/" + old_p_cntlr['name'] 
      vdict = {'body': payload, 'resp': resp, 'resp2': resp2, 'method': 'DELETE', 'uri': uri,
            'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
             'auth': vd_data['auth']
      }
      [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
      if len(resp_str) > 3:
        newjstr = json_loads(resp_str)
        #mlog.info("SDWAN Controller = {0}".format(json.dumps(newjstr,indent=4)))

      if "controller" in jstr:
        found = 0

        for i in jstr["controller"] :
          if i['name'] != old_p_cntlr['name'] :
            jstr["controller"].remove(i)

        for i in jstr["controller"] :
          if i['name'] == old_p_cntlr['name'] :
            i['name'] = new_p_cntlr["controllerName"]
            found = found + 1

      if found > 0 :
        newjstr = {}
        newjstr = { "controller" : jstr["controller"][0] }
        payload = json.dumps(newjstr)
        #payload = json.dumps(jstr)
        vdict = {}
        uri =  _uri.rsplit('?',1)[0]
        # For POST to work properly we need to modify the uri too
        uri =  uri.rsplit('/',1)[0]
        vdict = {'body': payload, 'resp': resp, 'resp2': resp2, 'method': 'POST', 'uri': uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth']
        }
        # we will not call the Rest API but return the vdict
        #if device["type"] == "hub-controller":
        #  get_device_sdwan_site( _method, _uri, _payload,resp='200',vd_data=vd_data, device=device,_cntlr=_cntlr)
        return vdict
        '''
        [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)

        if len(resp_str) > 3:
          jstr = json_loads(resp_str)
          mlog.info("SDWAN Controller after PATCH = {0}".format(json.dumps(jstr,indent=4)))
        return vdict

        if out == 1: 
          payload = {}
          vdict = {}
          uri =  uri + "/" + old_p_cntlr['name'] 
          vdict = {'body': payload, 'resp': resp, 'resp2': resp2, 'method': 'DELETE', 'uri': uri,
                'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
                 'auth': vd_data['auth']
          }
          [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
        else:
          mlog.error("Not Sending DELETE from function {0} for device = {1} ".format(get_sdwan_controller.__name__,device["name"]))
        '''
      else : 
        mlog.error("Could not find anything to add in function {0} for device = {1} ".format(get_sdwan_controller.__name__,device["name"] ))

    else: 
      mlog.error("Could not send PATCH from function {0} for device = {1} ".format(get_sdwan_controller.__name__,device["name"] ))
    return ''

def get_sdwan_controller( _method, _uri, _payload,resp='200',vd_data=None, device=None):
    global vnms, analy, cntlr, cust, mlog

    if device is None or vd_data is None :
      mlog.error("Bad inputs in function {0} ".format(get_sdwan_controller.__name__))
      return

    mlog.info("In function {0} with device = {1} ".format(get_sdwan_controller.__name__, device["name"]))
    resp2 = '202'
    vdict = {}
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': _uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth']
    }
    [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json_loads(resp_str)
      mlog.info("SDWAN Controller = {0}".format(json.dumps(jstr,indent=4)))
      old_p_cntlr = get_old_peer_controller_name(2)
      new_p_cntlr = get_new_peer_controller_name(2)
      if "controller" in jstr:
        found = 0
        for i in jstr["controller"] :
          if i['name'] == old_p_cntlr['name'] :
            i['name'] = new_p_cntlr["controllerName"]
            found = found + 1

      if found > 0 :
        payload = json.dumps(jstr)
        vdict = {}
        uri =  _uri.rsplit('?',1)[0]
        vdict = {'body': payload, 'resp': resp, 'resp2': resp2, 'method': 'PATCH', 'uri': uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth']
        }
        [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)

        if len(resp_str) > 3:
          jstr = json_loads(resp_str)
          mlog.info("SDWAN Controller after PATCH = {0}".format(json.dumps(jstr,indent=4)))

        if out == 1: 
          payload = {}
          vdict = {}
          uri =  uri + "/" + old_p_cntlr['name'] 
          vdict = {'body': payload, 'resp': resp, 'resp2': resp2, 'method': 'DELETE', 'uri': uri,
                'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
                 'auth': vd_data['auth']
          }
          [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
        else:
          mlog.error("Not Sending DELETE from function {0} for device = {1} ".format(get_sdwan_controller.__name__,device["name"]))
      else : 
        mlog.error("Could not find anything to add in function {0} for device = {1} ".format(get_sdwan_controller.__name__,device["name"] ))

    else: 
      mlog.error("Could not send PATCH from function {0} for device = {1} ".format(get_sdwan_controller.__name__,device["name"] ))
    return ''

def get_device_vnf_manager( _method, _uri, _payload,resp='200',vd_data=None, device=None,_cntlr=2):
    global vnms, analy, cntlr, cust, mlog

    if device is None or vd_data is None :
      mlog.error("Bad inputs in function {0} ".format(get_device_vnf_manager.__name__))
      return

    mlog.warn("Modifying VNF Manager details for device = {0} ".format(device["name"]))
    resp2 = '202'
    vdict = {}
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': _uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth']
    }
    [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      south_ip = [i['director_southIP'] + "/32" for i in glbl.vnms.data['director']]
      domain_ips = glbl.vnms.data['domain_ips']
      method = "PATCH"
      jstr = json_loads(resp_str)
      #mlog.info("VNF Manager Info = {0}".format(json.dumps(jstr,indent=4)))
      if "vnf-manager" in jstr and "ip-addresses" in jstr["vnf-manager"]:
        # Since we are doing this on the Old Director using PATCH, we will just add our IPs
        if _cntlr == 2:
          x= jstr["vnf-manager"]["ip-addresses"] + south_ip 
        else: 
          x= south_ip + domain_ips 
          method = "PUT"
        jstr["vnf-manager"]["ip-addresses"] = x
        #del jstr["vnf-manager"]["vnf-manager"]
        payload = json.dumps(jstr)
        vdict = {'body': payload, 'resp': resp, 'resp2': resp2, 'method': method , 'uri': _uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth']
        }
        [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
        if len(resp_str) > 3:
          jstr = json_loads(resp_str)
          mlog.info("VNF Manager after PUT = {0}".format(json.dumps(jstr,indent=4)))
        """
        if _cntlr == 2:
          newuri = '/api/config/devices/template/' + device['poststaging-template'] + '/config/system/vnf-manager'
          vdict = {'body': payload, 'resp': resp, 'resp2': resp2, 'method': 'GET', 'uri': newuri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth']
          }
          [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
          if len(resp_str) > 3:
            jstr = json_loads(resp_str)
            #mlog.info("VNF Manager Info = {0}".format(json.dumps(jstr,indent=4)))
            if "vnf-manager" in jstr and "ip-addresses" in jstr["vnf-manager"]:
              jstr["vnf-manager"]["ip-addresses"] = south_ip
              del jstr["vnf-manager"]["vnf-manager"]
              payload = json.dumps(jstr)
              vdict = {'body': payload, 'resp': resp, 'resp2': resp2, 'method': 'PUT', 'uri': _uri,
                    'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
                     'auth': vd_data['auth']
              }
              [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
              if len(resp_str) > 3:
                jstr = json_loads(resp_str)
                mlog.info("VNF Manager Template after PUT = {0}".format(json.dumps(jstr,indent=4)))
        """
    return ''

def get_vnf_manager( _method, _uri, _payload,resp='200',vd_data=None, device=None):
    global vnms, analy, cntlr, cust, mlog

    if device is None or vd_data is None :
      mlog.error("Bad inputs in function {0} ".format(get_vnf_manager.__name__))
      return

    mlog.info("In function {0} with device = {1} ".format(get_vnf_manager.__name__, device["name"]))
    resp2 = '202'
    vdict = {}
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': _method, 'uri': _uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth']
    }
    [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      south_ip = [i['director_southIP'] + "/32" for i in glbl.vnms.data['director']]
      jstr = json_loads(resp_str)
      mlog.info("VNF Manager Info = {0}".format(json.dumps(jstr,indent=4)))
      if "vnf-manager" in jstr and "ip-addresses" in jstr["vnf-manager"]:
        x= jstr["vnf-manager"]["ip-addresses"] + south_ip 
        jstr["vnf-manager"]["ip-addresses"] = x
        del jstr["vnf-manager"]["vnf-manager"]
        payload = json.dumps(jstr)
        vdict = {'body': payload, 'resp': resp, 'resp2': resp2, 'method': 'PUT', 'uri': _uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth']
        }
        [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
        if len(resp_str) > 3:
          jstr = json_loads(resp_str)
          mlog.info("VNF Manager after Delete = {0}".format(json.dumps(jstr,indent=4)))
    return ''

def create_dns_config( _method, _uri,_payload,resp='200'):
    vdict = {}
    vdict = {'body': _payload, 'resp': resp, 'method': _method, 'uri': _uri}
    [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no")
    if len(resp_str) > 3:
      print(json_loads(resp_str))
    return ''

def choose_template_vs_device():
    return 1
    '''
    while 1:
      num=int(input("Choose Template (0) or Device (1): "))  
      if num == 0: return 0
      elif num == 1: return 1 
      else:
        print("Re-enter 0 or 1 to continue")
    '''

def get_lef_status (vd_data,device,_cntlr):
    global vnms, analy, cntlr, cust, mlog
    resp='200'
    resp2 = '202'
    _payload ={}
    vdict = {}
    _uri = ( "/vnms/dashboard/appliance/" + device["name"] + "/live?&command=orgs/org-services/" + 
              glbl.cust.data["custName"] +  "/lef/collectors?deep" )
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method':"GET", 'uri': _uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth'] }
    [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json_loads(resp_str)
      if "lef:collectors" in jstr and "collector" in jstr["lef:collectors"]:
        found = 0
        count = 0
        for elem in  jstr["lef:collectors"]["collector"] :
          if "status" in elem:
            for subelem in elem["status"]:
              if "status" in  subelem:
                count = count + 1
                if subelem["status"]  == "Established" or subelem["status"]  == "Suspend":
                  found = found + 1
        if found == count :
          mlog.warn("LEF status for Device={0} is UP from Director with IP {1}".format(device["name"],vd_data['vd_ip']))
          return True
        else: 
          mlog.error("LEF status for Device={0} is DOWN from Director with IP {1} Total={2} Found={3}".format(device["name"],vd_data['vd_ip'],count,found))
          return False
      else:
        mlog.error("Did not receive proper response for uri = {0}".format(_uri))
        return False
    else:
      mlog.error("Did not receive proper response for uri = {0}".format(_uri))
      return False

def get_sla_status (vd_data,device,_cntlr):
    global vnms, analy, cntlr, cust, mlog
    resp='200'
    resp2 = '202'
    _payload ={}
    vdict = {}
    _uri = ( "/vnms/dashboard/appliance/" + device["name"] + "/live?&command=orgs/org/" + 
              glbl.cust.data["custName"] +  "/sd-wan/sla-monitor/status/" )
    cntlr_name = None
    if check_if_device_onboarded_to_hcn_device(device):
      idx = _cntlr - 1
      if idx < len( glbl.vnms.data['hub_cntlr_devices']): 
        cntlr_name = glbl.vnms.data['hub_cntlr_devices'][idx]["name"]
    else:
      mycntlr = get_new_peer_controller_name(_cntlr)
      cntlr_name = mycntlr["controllerName"]
    if not cntlr_name:
      mlog.warn("Name of Controller not found. Can not get SLA status for Device={0} not found from Director with IP {1}".format(device["name"],vd_data['vd_ip']))
      return False

    _uri = _uri + cntlr_name + "?deep" 
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method':"GET", 'uri': _uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth'] }
    [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if out == 1 and len(resp_str) > 3:
      try:
        jstr = json_loads(resp_str)
        if "sdwan:status" in jstr and "path-status" in jstr["sdwan:status"]:
          found =0
          count = 0
          for elem in  jstr["sdwan:status"]["path-status"]:
            if "conn-state" in elem:
              count = count + 1
              if elem ["conn-state"] == "up":
                found = found + 1
          if found == count :
            mlog.warn("SLA status for Device={0} to Controller={1} is UP from Director with IP {2}".format(device["name"],cntlr_name,vd_data['vd_ip']))
            return True
          else: 
            mlog.error("SLA status for Device={0} to Controller={1} is DOWN from Director with IP {2}".format(device["name"],cntlr_name,vd_data['vd_ip']))
            return False
        else:
          mlog.error("Did not receive proper response for uri = {0}".format(_uri))
          return False
      except:
        mlog.error("Did not receive proper response for uri = {0}".format(_uri))
        return False
    else:
      mlog.error("Did not receive proper response for uri = {0}".format(_uri))
      return False

def get_bgp_status(vd_data,device,_cntlr):
    global vnms, analy, cntlr, cust, mlog
    resp='200'
    resp2 = '202'
    _uri = ( "/vnms/dashboard/appliance/" + device["name"] + "/live?&command=bgp/neighbors/brief/" + 
                glbl.cust.data["custName"] + "-Control-VR?deep" )
    _payload = {}
    vdict = {}
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method':"GET", 'uri': _uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth'] }
    [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json_loads(resp_str)
      if "routing-module:brief" in jstr and "neighbor-ip" in jstr["routing-module:brief"]:
        count =0;
        found =0
        for elem in jstr["routing-module:brief"]["neighbor-ip"]:
          count = count + 1 
          if elem["state"] == "Established": found = found + 1
        if count == found:
          mlog.warn("BGP connectivity for Device={0} is UP from Director with IP {1}".format(device["name"],vd_data['vd_ip']))
          return True
        else: 
          mlog.error("BGP connectivity for Device={0} is DOWN from Director with IP {1}".format(device["name"],vd_data['vd_ip']))
          return False
      else: 
        mlog.error("Did not receive proper response for uri = {0}".format(_uri))
        return False
    else: 
      mlog.error("Did not receive proper response for uri = {0}".format(_uri))
      return False

def check_device_sync_status(vd_data, device): 
    global vnms, analy, cntlr, cust, admin, auth, debug, mlog
    resp = '200'
    resp2 = '202'
    _uri = "/vnms/dashboard/appliance/" + device["uuid"] + "/syncStatus"
    #mlog.warn("Director with IP {0} is Checking Sync Status for device {1}. Please be patient".format(vd_data['vd_ip'],device["name"]))
    _payload = {}
    vdict = {}
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': "GET", 'uri': _uri,
            'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
             'auth': vd_data['auth']
    }

    for i in range(0,2):
      time.sleep(5)
      [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
      if out == 1:
        if len(resp_str) > 3:
          jstr = json_loads(resp_str)
          if ("versanms.ApplianceStatus" in jstr and "sync-status" in  jstr["versanms.ApplianceStatus"] and "unreachable" in  jstr["versanms.ApplianceStatus"] and 
               jstr["versanms.ApplianceStatus"]["sync-status"] == "IN_SYNC"  and  jstr["versanms.ApplianceStatus"]["unreachable"] == 0): 
            mlog.warn("Device {0} is in Sync from Director with IP {1}".format(device["name"],vd_data['vd_ip']))
            return True

    mlog.error("Device {0} is either Unreachable or NOT in Sync from Director with IP {1}".format(device["name"],vd_data['vd_ip']))
    return False
    

def device_connect(vd_data,device=None,_cntlr=2):
    global vnms, analy, cntlr, cust, admin, auth, debug, mlog
    resp = '200'
    resp2 = '202'
    _uri = "/api/config/devices/device/" + device["name"] + "/_operations/connect"
    mlog.warn("Director with IP {0} is trying  to connect to device {1}. Please be patient".format(vd_data['vd_ip'],device["name"]))
    _payload = {}
    vdict = {}
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': "POST", 'uri': _uri,
            'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
             'auth': vd_data['auth']
    }
    found = 0
    for i in range(0,10):
      time.sleep(5)
      [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
      if out == 1:
        if len(resp_str) > 3:
          jstr = json_loads(resp_str)
          if "output" in jstr and "result" in  jstr["output"] and jstr["output"]["result"] == 1: 
            mlog.warn("Director with IP {0} is able to connect to device {1} for Controlller {2}".format(vd_data['vd_ip'],device["name"],str(_cntlr)))
            found = 1
            break

    if found == 0:
      mlog.error("Director with IP {0} is NOT able to connect to device {1} for Controlller {2}".format(vd_data['vd_ip'],device["name"],str(_cntlr)))
      return

    if _cntlr == 2:
      _payload = {}
      _uri = "/api/config/devices/device/" + device["name"] + "/_operations/sync-from"
      vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': "POST", 'uri': _uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth']
      }
      [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
      if out == 1: 
        if len(resp_str) > 3:
          jstr = json_loads(resp_str)
          if "output" in jstr and "result" in  jstr["output"] and jstr["output"]["result"] == 1: 
            mlog.info("Sync from Director with IP {0} successful for device {1}".format(vd_data['vd_ip'],device["name"]))
            device["status"] = "C2-Complete"
            return
      else:
        mlog.error("Sync from Director with IP {0} NOT successful for device {1}".format(vd_data['vd_ip'],device["name"]))
        return
    else: 
      device["status"] = "C12-Complete"
      mlog.warn("Performing checks from Director with IP {0} for device {1}. Please be patient".format(vd_data['vd_ip'],device["name"]))
      for i in range (0,3):
        time.sleep(30)
        if get_bgp_status( vd_data,device,_cntlr): break

      for i in range (0,3):
        time.sleep(30)
        if get_sla_status (vd_data,device,2): break
      for i in range (0,3):
        time.sleep(5)
        if get_sla_status (vd_data,device,1): break

      for i in range (0,3):
        time.sleep(5)
        if get_lef_status (vd_data,device,_cntlr): break

      if device["type"] == "hub-controller": 
        get_hub_cntlr_device_ipsec_vpn_profile(vd_data=vd_data, device=device,_cntlr=_cntlr)
        get_device_sdwan_site( vd_data=vd_data, device=device,_cntlr=_cntlr)
      save_config_snapshot(device["name"],vd_data, _cntlr)
      mlog.warn("Device migration sucessfull for device {0}".format(device["name"]))
      return

def get_n_process_appliance_list( vd_data):
    global vnms, analy, cntlr, cust, admin, auth, debug, mlog
    resp = '200'
    resp2 = '202'
    _uri = "/vnms/appliance/appliance"
    _payload = {}
    vdict = {}

    count = 0
    totalcnt = -1
    while 1:
      newuri = _uri + "?offset={0}&limit=25".format(count) 
      vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method': "GET", 'uri': newuri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth']
      }
      [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
      if len(resp_str) > 3:
        jstr = json_loads(resp_str)
        if "versanms.ApplianceStatusResult" in jstr: 
          if count == 0 and totalcnt == -1:
            if "totalCount" in jstr["versanms.ApplianceStatusResult"] : 
              totalcnt = int(jstr["versanms.ApplianceStatusResult"]["totalCount"])
            else: sys.exit("did not get totalCount")

          if "appliances" in jstr["versanms.ApplianceStatusResult"]:
            newjstr = jstr["versanms.ApplianceStatusResult"]["appliances"]
            for dev in newjstr:
              for j in range( len(glbl.vnms.data['devices'])):
                if dev["name"] == glbl.vnms.data['devices'][j]["name"]:
                    #mlog.info("Found device in list {0} ".format(dev["name"]))
                    glbl.vnms.data['devices'][j]["deviceStatus"] = {}
                    glbl.vnms.data['devices'][j]["deviceStatus"]["ping-status"] = dev["ping-status"]
                    glbl.vnms.data['devices'][j]["deviceStatus"]["sync-status"] = dev["sync-status"]
                    
        if totalcnt <= (count + 25): break
        else: count = count + 25
    write_outfile(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin)
    # Find and print the error list
    errorlist = list(filter(lambda x: "deviceStatus" in x and (x['deviceStatus']["ping-status"]!= "REACHABLE" or x['deviceStatus']["sync-status"]!= "IN_SYNC"), glbl.vnms.data["devices"]))
    if len(errorlist) > 0:
      print ("The following devices are in error status from Director = {0}".format(vd_data['vd_ip']))
      col0=int(MYCOL/4)
      col1=int(MYCOL/4)
      col2=int(MYCOL/4)
      print("-" * int(4+col0+col1+col2))
      print("|{0:<{col0}}|{1:<{col1}}|{2:<{col2}}|".format("Name","DeviceStatus","SyncStatus",
                        col0=col0,col1=col1,col2=col2))
      print("-" * int(4+col0+col1+col2))
      for v in errorlist:
        namelist = []
        #if len(v['name']) > col0:
        namelist = my_split_string(v['name'], col0)
        if len (namelist) == 1:
          print("|{0:<{col0}}|{1:<{col1}}|{2:<{col2}}|".format(v["name"],
                        v['deviceStatus']['ping-status'],
                        v['deviceStatus']['sync-status'],
                        col0=col0,col1=col1,col2=col2))
        else:
          for i in range(len(namelist)):
            _namelist = "" if i >= len(namelist) else namelist[i]
            _pingstatus = "" if i > 0 else v['deviceStatus']['ping-status']
            _syncstatus = "" if i > 0 else v['deviceStatus']['sync-status']
            print("|{0:<{col0}}|{1:<{col1}}|{2:<{col2}}|".format(_namelist,
                        _pingstatus,
                        _syncstatus,
                        col0=col0,col1=col1,col2=col2))

      print("-" * int(4+col0+col1+col2))
      print("If you proceed the above devices will NOT be migrated\n" +
            "Once the above devices are reachable you can rerun the script\n")
      ret = yes_or_no("To continue press y and to exit press n or press r to refresh: ",1)
      if ret == 0 : return ret
      elif ret == 1: pass
      else: return ret
    # if we are here we are continuing or there are no errors. 
    #We now need to create a new list of ONLY the devices that need migration
    new_device_list = list(filter(lambda x: "deviceStatus" in x and (x['deviceStatus']["ping-status"] == "REACHABLE" and x['deviceStatus']["sync-status"] == "IN_SYNC"), glbl.vnms.data["devices"]))
    # we will overwrite even if anything is present from before
    glbl.vnms.data["newdevicelist"] = []  
    glbl.vnms.data["newdevicelist"] = new_device_list
    write_outfile(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin)
    return ret

def my_split_string(_str, n):
    my_list = [_str[index : index + n] for index in range(0, len(_str), n)]
    return my_list

def get_devices_list( _all_device, _batch_device, _batch_device_num, option=2):
    global vnms, analy, cntlr, cust, admin, auth, debug, mlog, MYLINES, MYCOL

    # This if statement is just in case we do not have a newdevicelist. Most likely it should never happen
    if 'newdevicelist' not in glbl.vnms.data or len(glbl.vnms.data['newdevicelist']) <= 0:
      new_device_list = list(filter(lambda x: "deviceStatus" in x and (x['deviceStatus']["ping-status"] == "REACHABLE" and x['deviceStatus']["sync-status"] == "IN_SYNC"), glbl.vnms.data["devices"]))
      # we will overwrite even if anything is present from before
      glbl.vnms.data["newdevicelist"] = []  
      glbl.vnms.data["newdevicelist"] = new_device_list
      write_outfile(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin)
    

    mlog.warn(bcolors.OKWARN + "==============Moving Controller-{0} ==========".format(str(option)) + bcolors.ENDC)
    cnt_list = list(range(1,len(glbl.vnms.data['newdevicelist'])+1))
    comb_dict=dict(zip(cnt_list,glbl.vnms.data['newdevicelist']))
    pcol1=int(MYCOL/4)
    pcol2=int(MYCOL/4)
    pcol3=int(MYCOL/4)


    print("-" * int(4+pcol1+pcol2+pcol3+15+6+15))
    print("|{0:<{col0}}|{1:<{col1}}|{2:<{col2}}|{3:<{col3}}|{4:<{col4}}|{5:<{col5}}|".format("Idx","Name","P-STemplate","DG-Group","Status","NewDir Status",
                                              col0=4,col1=pcol1,col2=pcol2,col3=pcol3,col4=15,col5=14))
    print("-" * int(4+pcol1+pcol2+pcol3+15+6+15))
    cnt = 0
    out_line = MYLINES
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
      dg_grouplist = my_split_string(v['poststaging-template'], pcol3)
      # find the max of 3 values to determine how many lines we need to add. If the max is 1 we do not need to add any lines
      mymax = max( len(namelist), len(post_staginglist), len(dg_grouplist))
      #cnt = cnt + mymax
      if mymax != 1 :
        new_out_line = new_out_line - mymax + 1

      new_dirstatus = "OK" if v['deployed'] == "1" else "N_OK"
      if "status" in v:
        if mymax == 1:
          print("|{0:<{col0}}|{1:<{col1}}|{2:<{col2}}|{3:<{col3}}|{green}{4:<{col4}}{endc}|{5:<{col5}}|".
                  format(_key,v['name'],v['poststaging-template'],
                  v['dg-group'],v['status'],new_dirstatus, green=bcolors.OKGREEN,endc=bcolors.ENDC,
                  col0=4,col1=pcol1,col2=pcol2,col3=pcol3,col4=15,col5=14))
        else:
          for i in range(mymax):
            _namelist = "" if i >= len(namelist) else namelist[i]
            _post_staginglist = "" if i >= len(post_staginglist) else post_staginglist[i]
            _dg_grouplist = "" if i >= len(dg_grouplist) else dg_grouplist[i]
            _nd_status = new_dirstatus  if i == 0 else ""
            _keyl = "" if i > 0 else _key
            _statusl = "" if i > 0 else v['status']
            print("|{0:<{col0}}|{1:<{col1}}|{2:<{col2}}|{3:<{col3}}|{green}{4:<{col4}}{endc}|{5:<{col5}}|".
                  format(_keyl,_namelist,_post_staginglist,
                  _dg_grouplist,_statusl, _nd_status,
                  green=bcolors.OKGREEN,endc=bcolors.ENDC,
                  col0=4,col1=pcol1,col2=pcol2,col3=pcol3,col4=15,col5=14))


      else : 
        if mymax == 1:
          print("|{0:<{col0}}|{1:<{col1}}|{2:<{col2}}|{3:<{col3}}|{warn}{4:<{col4}}{endc}|{5:<{col5}}|".
                  format(_key,v['name'],v['poststaging-template'],
                  v['dg-group'],"NotComplete",new_dirstatus, warn=bcolors.OKWARN,endc=bcolors.ENDC,
                  col0=4,col1=pcol1,col2=pcol2,col3=pcol3,col4=15,col5=14))
        else:
          for i in range(mymax):
            _namelist = "" if i >= len(namelist) else namelist[i]
            _post_staginglist = "" if i >= len(post_staginglist) else post_staginglist[i]
            _dg_grouplist = "" if i >= len(dg_grouplist) else dg_grouplist[i]
            _nd_status = new_dirstatus  if i == 0 else ""
            _keyl = "" if i > 0 else _key
            _statusl = "" if i > 0 else "NotComplete"
            print("|{0:<{col0}}|{1:<{col1}}|{2:<{col2}}|{3:<{col3}}|{warn}{4:<{col4}}{endc}|{5:<{col5}}|".
                  format(_keyl,_namelist,_post_staginglist,
                  _dg_grouplist,_statusl, _nd_status,
                  warn=bcolors.OKWARN,endc=bcolors.ENDC,
                  col0=4,col1=pcol1,col2=pcol2,col3=pcol3,col4=15,col5=14))

      if  cnt%new_out_line == 0 and _key !=  len(comb_dict) :
        #print(new_out_line)
        print("-" * int(4+pcol1+pcol2+pcol3+15+6+15))
        yes_or_no3("Press y or n to continue" )
        print("-" * int(4+pcol1+pcol2+pcol3+15+6+15))
        print("|{0:<{col0}}|{1:<{col1}}|{2:<{col2}}|{3:<{col3}}|{4:<{col4}}|{5:<{col5}}|".
                          format("Idx","Name","P-STemplate","DG-Group","Status","NewDir Status",
                          col0=4,col1=pcol1,col2=pcol2,col3=pcol3,col4=15,col5=14))
        print("-" * int(4+pcol1+pcol2+pcol3+15+6+15))
        #Now reset things back
        new_out_line = out_line 
        cnt = 0

    print("-" * int(4+pcol1+pcol2+pcol3+15+6+15))

    if _all_device == 1:
      return [range(1,count), count, comb_dict ]
    elif _batch_device == 1 and _batch_device_num > 0 : 
      return [range(1,count), _batch_device_num, comb_dict ]
    else:
      pass

    while 1:
      if option == 2:
        _str = bcolors.OKWARN + "Choose a number to continue moving Controller-2 or enter 0 to start moving Controller-1 : " + bcolors.ENDC
      else : 
        _str = bcolors.OKWARN + "Choose a number to continue moving Controller-1 or enter 0 to quit the program : " + bcolors.ENDC
      try:
        if pyVer.major== 3:
          num=int(input(_str))
        else:
          num=int(raw_input(_str))
        if num == 0: return [[num], 0, None]
        elif num in comb_dict:
          if (option == 2 and "status" in comb_dict[num] and  
                (comb_dict[num]["status"] == "C2-Complete" or comb_dict[num]["status"] == "C12-Complete")):
            print("Controller 2 Migration is complete. Re-enter a different the number to continue")
          elif option == 1 and "status" in comb_dict[num] and comb_dict[num]["status"] == "C12-Complete":
            print("Controller 1 and 2 Migration is complete. Re-enter a different the number to continue")
          elif option == 1 and "status" not in comb_dict[num]:
            print("Can not migrate Controller 1 before Controller 2 Migration is complete. Re-enter a different the number to continue")
          else:  
            return [[num], 1, comb_dict]
        else:
          print("Re-enter the number to continue")
      except:
          print("I did not understand your input. Please re-enter the number to continue")


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

def yes_or_no2(question):
    if pyVer.major== 3:
      reply = str(input(question+' (y/n): ')).lower().strip()
    else:
      reply = str(raw_input(question+' (y/n): ')).lower().strip()
    if reply[0] == 'n': return 0
    elif reply[0] == 'y': return 1
    else:
        return yes_or_no2("Did not understand input: Please re-enter ") 

def yes_or_no3(question):
    if pyVer.major== 3:
      reply = str(input(question+' (y/n): ')).lower().strip()
    else:
      reply = str(raw_input(question+' (y/n): ')).lower().strip()
    if reply[0] == 'n': return 1
    elif reply[0] == 'y': return 1
    return 1


def save_config_snapshot (dev, vd_data, _cntlr):
    resp='200', 
    resp2 = '202'
    localtime = time.localtime(time.time()) 
    configSnapshotName = "beforeMigr" if _cntlr == 2 else "afterMigr"
    configSnapshotName = (configSnapshotName + 
      "{0:04d}_{1:02d}_{2:02d}_{3:02d}_{4:02d}".format(localtime.tm_year,
      localtime.tm_mon,localtime.tm_mday,localtime.tm_hour,localtime.tm_min))
    vdict = {}
    _uri = "/vnms/operations/save/snapshot/" + configSnapshotName  + "/device/" + dev
    _payload = {}
    vdict = {'body': _payload, 'resp': resp, 'resp2': resp2, 'method':"POST" , 'uri': _uri,
              'vd_ip' :  vd_data['vd_ip'], 'vd_rest_port': vd_data['vd_rest_port'],
               'auth': vd_data['auth'] }
    [out, resp_str] = common.newcall(vdict,content_type='json',ncs_cmd="no",jsonflag=1)
    if len(resp_str) > 3:
      jstr = json_loads(resp_str)
      if "response-code" in jstr and "response-type" in jstr and jstr["response-type"] == "success":
        mlog.warn("Config Snapshot={0} for Device={1} is saved in Director with IP {2}".format(configSnapshotName,dev,vd_data['vd_ip']))
      else: 
        mlog.error("Config Snapshot={0} for Device={1} was NOT saved in Director with IP {2}".format(configSnapshotName,dev,vd_data['vd_ip']))
    else: 
      mlog.error("Did not receive proper response for uri = {0}".format(_uri))


def process_device_list (fil,template_env,template_path,tmpl_device,newdir,olddir,all_device,batch_device, batch_device_num, _cntlr):
    global vnms, analy, cntlr, cust, admin, auth, debug, mlog

    #mlog.warn(bcolors.OKWARN + "==============Moving Controller-{0} ==========".format(str(_cntlr)) + bcolors.ENDC)
    newvdict = {}
    dir_items = sorted(os.listdir(template_path))
    if _cntlr == 2:
      dirdata = olddir
    else:
      dirdata = newdir

    while 1:
      [num_list, batch_num, comb_list ]=get_devices_list( all_device, batch_device, batch_device_num, option=_cntlr)
      if len(num_list) == 0 or (len(num_list) == 1 and num_list[0] == 0): break
      cnt = 0
      for item in num_list :
        #print("I=%d"%(item)) 
        #pprint(comb_list[item])
        dev = comb_list[item]
        # Here we check whether the status is right or not
        skip = 0
        if _cntlr == 2:
          if "status" in dev:
            skip = 1
            mlog.warn("Device={0} already Status={1}".format(dev["name"],dev["status"]))
          elif "deployed" in dev and dev["deployed"] != "1":
            skip = 1
            mlog.warn("Device={0} already Status={1}".format(dev["name"],dev["deployed"]))
        else: 
          if "status" in dev and dev["status"] != "C2-Complete":
            skip = 1
            mlog.warn("Device={0} already Status={1}".format(dev["name"],dev["status"]))
          elif "deployed" in dev and dev["deployed"] != "1":
            skip = 1
            mlog.warn("Device={0} already Status={1}".format(dev["name"],dev["deployed"]))

        if skip == 0:
          # We start processing each device in the list
          for i in dir_items:
             # check the format of the files
             if not re.match(r'^\d{3}_.+\.json$', i):
                continue
             elif tmpl_device == 0 and not re.match(r'^\d1\d_.+\.json$', i):
                continue
             elif tmpl_device == 1 and not re.match(r'^\d2\d_.+\.json$', i):
                continue
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
             mlog.info("==============In {0} for Device={1}==========".format(_newkey,dev["name"]))
             #ret = yes_or_no("Continue: " )
             #if ret == 0 : sys.exit("Exiting")
             #elif ret == 2: continue
             # we need to check the sync status of the device from the Director in question. If for some some reason that is false we bail out right here
             if ((_newkey == 'GET_DEVICE_SDWAN_CONTROLLER' and check_device_sync_status(dirdata, dev)) or (_newkey != 'GET_DEVICE_SDWAN_CONTROLLER')):
               pass
             else: 
               break
             if _key[0:3] == 'GET':
               if _newkey == 'GET_CONTROLLER_WORKFLOW' or _newkey == 'GET_PEER_CONTROLLER_WORKFLOW':
                 x= my_template.render()
                 y= json_loads(x)
                 _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']),vd_data=olddir,_ofile=None)
               elif _newkey == 'GET_VNF_MANAGER':
                 x= my_template.render(templateName=dev["poststaging-template"])
                 y= json_loads(x)
                 _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']),vd_data=olddir,device=dev)
               elif _newkey == 'GET_SDWAN_CONTROLLER':
                 x= my_template.render(templateName=dev["poststaging-template"])
                 y= json_loads(x)
                 _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']),vd_data=olddir,device=dev)
               elif _newkey == 'GET_SYSTEM_CONTROLLER':
                 x= my_template.render(templateName=dev["poststaging-template"])
                 y= json_loads(x)
                 _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']),vd_data=olddir,device=dev)
               elif _newkey == 'GET_IPSEC_VPN_PROFILE':
                 x= my_template.render(templateName=dev["poststaging-template"])
                 y= json_loads(x)
                 _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']),vd_data=olddir,device=dev)
               elif _newkey == 'GET_DEVICE_SDWAN_CONTROLLER':
                 if _cntlr == 2:
                   save_config_snapshot(dev["name"],dirdata, _cntlr)
                 x= my_template.render(deviceName=dev["name"])
                 y= json_loads(x)
                 newvdict = _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']),vd_data=dirdata,device=dev, _cntlr=_cntlr)
               elif _newkey == 'GET_DEVICE_SYSTEM_CONTROLLER':
                 x= my_template.render(deviceName=dev["name"])
                 y= json_loads(x)
                 _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']),vd_data=dirdata,device=dev,newdict=newvdict, _cntlr=_cntlr)
                 newvdict = {}
               elif _newkey == 'GET_DEVICE_IPSEC_VPN_PROFILE':
                 x= my_template.render(deviceName=dev["name"])
                 y= json_loads(x)
                 _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']),vd_data=dirdata,device=dev, _cntlr=_cntlr)
               elif _newkey == 'GET_DEVICE_VNF_MANAGER':
                 x= my_template.render(deviceName=dev["name"])
                 y= json_loads(x)
                 _val(str(y['method']), str(y['path']), json.dumps(y['payload']),resp=str(y['response']),vd_data=dirdata,device=dev,_cntlr=_cntlr)
                 # now we do a repeated connect on device from newdir
                 device_connect(newdir,device=dev,_cntlr=_cntlr)
                 write_outfile(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin)

        # we are done with processing of one device
        cnt = cnt+1
        if batch_num == 1:
          # we are moving single devices
          break
        if cnt%batch_num == 0: 
           ret = yes_or_no2("Choose y to continue or n to break from migrating Controller-1")
           if ret == 0:
             break

      # We are still inside the while 1 loop 
      if all_device == 1 or batch_device == 1:
        # we need to break out of the while 1 loop
        break

def get_terminal_size():
  global MYLINES, MYCOL
  os_env = os.environ

  if "LINES" in os_env:
    MYLINES = int(os_env["LINES"]) - 5
  else:
    MYLINES = 20
  if "COLUMNS" in os_env:
    MYCOL = (int(os_env["COLUMNS"])/10 - 1)*10
  else:
    MYCOL = 70




def main():
    #global vnms, analy, cntlr, cust, admin, auth, debug, mlog, mdict
    global mlog, mdict
    #mdict = readfile("in_rest.cfg")
    argcheck()
    debug = int(args['debug'])
    infile = args['file']
    LOG_FILENAME = 'vmMigrate.log'
    LOG_SIZE = 8 * 1024 * 1024
    mlog,f_hndlr,s_hndlr=glbl.init(infile,LOG_FILENAME, LOG_SIZE,"VMMigr3",debug)
    if debug == 0:
      glbl.setup_level(f_hndlr, logging.INFO) # Setting fileHandler loglevel
      glbl.setup_level(s_hndlr, logging.WARNING) # Setting stream Handler loglevel
    else:
      glbl.setup_level(f_hndlr, logging.INFO)
      glbl.setup_level(s_hndlr, logging.INFO)
       
    mlog.warn(bcolors.OKWARN + "===============Starting Phase 3 Execution==========" + bcolors.ENDC)
    mlog.warn(bcolors.OKWARN + "Are you running the script more than once. If so, you mist exit the script,\ncopy vm_phase4.json to vm_phase3.json and then restart script.\n" + bcolors.ENDC)
    ret = yes_or_no2("To continue press y and to exit press n : " )
    if ret == 0 : return
    elif ret == 1: pass


    write_outfile(glbl.vnms,glbl.analy,glbl.cntlr,glbl.cust, glbl.admin)
    get_terminal_size()

    fil = OrderedDict()
    #######################################################
    fil['GET_VNF_MANAGER.json'] = get_vnf_manager
    fil['GET_SDWAN_CONTROLLER.json'] = get_sdwan_controller
    fil['GET_SYSTEM_CONTROLLER.json'] =  get_system_controller 
    fil['GET_IPSEC_VPN_PROFILE.json'] = get_ipsec_vpn_profile
    fil['GET_DEVICE_VNF_MANAGER.json'] = get_device_vnf_manager
    fil['GET_DEVICE_SDWAN_CONTROLLER.json'] = get_device_sdwan_controller
    fil['GET_DEVICE_SYSTEM_CONTROLLER.json'] = get_device_system_controller
    fil['GET_DEVICE_IPSEC_VPN_PROFILE.json'] = get_device_ipsec_vpn_profile


    newdir= {'vd_ip' :  glbl.admin.data['new_dir']['vd_ip'],
            'vd_rest_port': glbl.admin.data['new_dir']['vd_rest_port'],
            'auth': glbl.admin.data['new_dir']['auth']
    }
    olddir= {'vd_ip' :  glbl.admin.data['old_dir']['vd_ip'],
            'vd_rest_port': glbl.admin.data['old_dir']['vd_rest_port'],
            'auth': glbl.admin.data['old_dir']['auth']
    }

    template_path = os.path.abspath(sys.argv[0]).rsplit("/",1)[0] + "/" + "in_phase3"
    template_loader = jinja2.FileSystemLoader(searchpath=template_path)
    template_env = jinja2.Environment(loader=template_loader,undefined=jinja2.StrictUndefined)
    template_env.filters['jsonify'] = json.dumps
    dir_items = sorted(os.listdir(template_path))

    while 1:
      rc = get_n_process_appliance_list( olddir)
      if rc == 0: return
      elif rc == 1: break
      else: pass
    
    tmpl_device = choose_template_vs_device()
    all_device = 0
    batch_device = 0
    batch_device_num=0

    all_device = yes_or_no2(bcolors.OKWARN + "Do you want to migrate all devices. Type y or n " + bcolors.ENDC )
    if all_device  == 0 :
      batch_device = yes_or_no2(bcolors.OKWARN + "Do you want to migrate a batch of devices. Type y or n" + bcolors.ENDC)
      if batch_device == 1:
        if pyVer.major== 3:
          batch_device_num=int(input(bcolors.OKWARN + "How many devices do you want to migrate in one batch. Type a number: " + bcolors.ENDC ))
        else:
          batch_device_num=int(raw_input(bcolors.OKWARN + "How many devices do you want to migrate in one batch. Type a number: " + bcolors.ENDC ))
        print(bcolors.OKWARN + "You have chosen to migrate a batch of {0} devices at a time".format(str(batch_device_num)) + bcolors.ENDC)
      else:
        print(bcolors.OKWARN + "You have chosen to migrate one device at a time"+ bcolors.ENDC )
    else:
        print(bcolors.OKWARN + "You have chosen to migrate ALL devices at a time" + bcolors.ENDC )
      

    # Controller 2 processing
    process_device_list(fil,template_env,template_path,tmpl_device,newdir,olddir,all_device,batch_device, batch_device_num, 2)

    # Controller 1 processing
    process_device_list(fil,template_env,template_path,tmpl_device,newdir,olddir,all_device,batch_device, batch_device_num, 1)

    mlog.warn(bcolors.OKWARN + "==============Completed execution of Phase 3==========\n" + bcolors.ENDC)

if __name__ == "__main__":
  _cnt1 = 0
  if os.path.isfile("vmMigrate.log"):
    with open("vmMigrate.log","r") as fp:
      for _cnt1,line in enumerate(fp):
        pass
    fp.close()
    _cnt1 = _cnt1 + 1

  main()

  _errlog=""
  _cnt2 = 0
  if os.path.isfile("vmMigrate.log"):
    with open("vmMigrate.log","r") as fp:
      for _cnt2,line in enumerate(fp):
        if _cnt2 >= _cnt1:
          if re.search("ERROR -",line):
            _errlog = _errlog + line
    fp.close()
    if len( _errlog ) > 0:
      fp=open("vmphase3.err","w+")
      fp.write(_errlog)
      fp.close()
      if mlog:
        mlog.warn(bcolors.OKWARN + "Error log vmphase3.err is created since there were errors." + bcolors.ENDC)






