#!/usr/bin/env python3

import requests, sys, json
from pprint import pprint
import ssl
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

customer_name = sys.argv[1]
host = sys.argv[2]
user = sys.argv[3]
pswd = sys.argv[4]

def handle_http_response_exception(response, customer_name):
    if response.status_code != 200:
        print(f"{str(customer_name)} VAN Health CRITICAL")
        if response.content:
            content = json.loads(response.content)
            if 'message' in content:
                print(f"{content['message']}")
            else:
                print(f"{content}")
        else:
            print(f"Unknown error:\n {response}")
        sys.exit(2)

port= "8443"
params = {"username": user, "password": pswd}
headers = {"Content-Type": "application/json", "Accept": "application/json"}

url = f"https://{host}:{port}/versa/login"
url1 = f"https://{host}:{port}/versa/analytics/nodes/status"
shw_url = f"https://{host}:{port}/versa/analytics"
logout_url = f"https://{host}:{port}/versa/logout"

crit_list = []
ok_list = []
data = []

with requests.session() as session:
    response = session.post(url, verify=False, params=params)
    handle_http_response_exception(response, customer_name)
    response1 = session.get(url1, verify=False, params=params)
    handle_http_response_exception(response1, customer_name)
    data = json.loads(response1.content)
    session.get(logout_url)


for i in range(0,len(data)):
 dc = data[i]['datacenter']
 status = data[i]['status']
 diskpc = float(data[i]['diskPercentUsed'])
 state = data[i]['state']
 cpupc = float(data[i]['cpuPercent'])
 mempc = data[i]['memoryPercentUsed']
 #if data[i]['datacenter'] == 'Search': 
 if status != 'Up' or state == 'Recovering' or cpupc > 70.0 or diskpc > 65.0 or mempc > 70.0:
   crit_list.append({'Datacenter':dc,'Status':status,'%cpu Util':cpupc,'%Disk Util':diskpc,'State':state,'%Mem Used':mempc})
 else:
   ok_list.append({'Datacenter':dc,'Status':status,'%cpu Util':cpupc,'%Disk Util':diskpc,'State':state,'%Mem Used':mempc})

if crit_list:
 print (str(customer_name)+": ANALYTICS CRITICAL\n")
 print ("Analytics URL:"+str(shw_url)+"\n")
 for d in range(0,len(crit_list)):
  print (str(crit_list[d]['Datacenter']+" : Status: "+str(crit_list[d]['Status'])))
  print (str(crit_list[d]['Datacenter']+" : Disk % Util: "+str(crit_list[d]['%Disk Util'])))
  print (str(crit_list[d]['Datacenter']+" : State: "+str(crit_list[d]['State'])))
  print (str(crit_list[d]['Datacenter']+" : % Mem Util: "+str(crit_list[d]['%Mem Used'])))
  print (str(crit_list[d]['Datacenter']+" : % CPU Util: "+str(crit_list[d]['%cpu Util'])))
 sys.exit(2)
else:
 print (str(customer_name)+": ANALYTICS OK\n")
 print ("Analytics URL:"+str(shw_url)+"\n")
 for d in range(0,len(ok_list)):
  print (str(ok_list[d]['Datacenter']+" : Status: "+str(ok_list[d]['Status'])))
  print (str(ok_list[d]['Datacenter']+" : Disk % Util: "+str(ok_list[d]['%Disk Util'])))
  print (str(ok_list[d]['Datacenter']+" : State: "+str(ok_list[d]['State'])))
  print (str(ok_list[d]['Datacenter']+" : % CPU Util: "+str(ok_list[d]['%cpu Util'])))
  print (str(ok_list[d]['Datacenter']+" : % Mem Util: "+str(ok_list[d]['%Mem Used'])))
 sys.exit(0)


