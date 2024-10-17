#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 19:26:01 2022

@author: arunchandar
"""

import subprocess
# read in users and strip the newlines
with open(raw_input("Enter API Filename: "),'r+') as f:
	lines = f.readlines()
        lines = [line.lstrip() for line in lines]
	lines = [line.replace("\t", "") for line in lines]
	d1 = [line.rstrip() for line in lines]
        print(d1)

data2 = raw_input("Enter API URL: ")

api = []
for data in d1:
    api.append('curl -k -d {} --user Administrator:<<Enter Password>> -X POST {} --insecure -H "Content-Type:application/json" -w "HTTP- %{{http_code}} code\n"'.format(data,data2))
print (api)
results=[]

for apis in api:
     results.append(subprocess.call(apis, shell=True))
     print(apis)

#for i,result in enumerate(results):
 #    if result == 0:
  #      print(apis[i])

