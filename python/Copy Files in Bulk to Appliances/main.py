#!/usr/bin/env python

import cmd
import getpass
#import sites_list
import json
import jsondiff
import urllib3
import os
import yaml
import requests
import click
import time

#from clint import resources
#from clint import arguments
from datetime import datetime
#from jsndiff import diff
#from files import File
#from sites import Site
#from routes import Route, RoutingTable
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


#@click.command()
#@click.option('--save', default=1, help='Number of greetings.')
#@click.option('--user', prompt='Your name', help='The person to greet.')


class VsnapyShell(cmd.Cmd):
	intro = 'Welcome to the Vsnapy Shell.   Type help or ? to list commands.\n'
	prompt = '(vsnapy) '
	file = None

	def do_show_devices(self, arg):
		'Show the sites onboarded to Director for a particular Tenant (For up to 200 devices). Expects a value for the Tenant name'
		#url =  'https://' + dirfqdn + ':9182/vnms/dashboard/tenantDetailAppliances/' + tenant + '?start=0&limit=' + limit 
		sites_list = get_site_names(arg)
		if sites_list == 0:
			print("The Organization " + arg + ' does not exist. Please verify')
		else:
			print("\n List of Sites \n")
			print(sites_list)


	def do_push_urlf_all(self,arg):
		'Push the file specified in the CONFIG file to all the Devices in the specified Org (passed as an argument)'
		sites_list = get_site_names(arg)
		if sites_list == 0:
			print("The Organization " + arg + ' does not exist. Please verify')
		else:
			config = read_config()
			url_file = config['url-file']
			uuid = get_org_uuid(arg)
			print("This will override the specified URL file (" + url_file + ") to " + str(len(sites_list)) + " devices in the Tenant: " + arg + " , Tenant UUID: " + uuid + ".\nDo you want to continue?")
			confirm = input("Yes(Y)/No(N)?:")
			if confirm == "Y":
				for site in sites_list:
					print("Pushing to "+site+ "  " + arg + "   "+uuid)
					url = base_url + '/vnms/upload/url-file-upload/appliance?appliance=' + site + '&file='+ url_file +'&org-uuid='+uuid
					print("URL: " + url + "\n")
					response = post_action(url,user,password)
					print("Response Code: " + str(response.status_code))
					print("Response: " + response.text + "\n")
			else:
				print("Operation Cancelled")


	def do_exit(self, arg):
		'Exit Vsnapy Shell'
		print('Thank you for using Vsnapy')
		self.close()
		exit()
		return True

	def close(self):
		if self.file:
			self.file.close()
			self.file = None

class AuthError(Exception):
	pass

class URLError(Exception):
	pass

class VD_NotReachable(Exception):
	pass

def get_data(url,user,password):
		raw = requests.get(url, auth=(user, password), headers={"Accept": "application/json"}, verify=False)
		if raw.status_code == 401:
			raise AuthError
		return raw

def post_action(url,user,password):
	raw = requests.post(url, auth=(user, password), headers={"Accept": "application/json"}, verify=False)
	return raw

def check_ping(VD_IP):
    response = os.system("ping -c 2 -W 500 " + VD_IP)
    # and then check the response...
    if response == 0:
        return True
    else:
        return False

#Method to read any yaml file
def read_yaml(path):
	url_list = []
	with open(path) as file:
		# The FullLoader parameter handles the conversion from YAML
		# scalar values to Python the dictionary format
		config = yaml.load(file, Loader=yaml.FullLoader)
	return config

#Method to fetch the list of devices
def get_site_names(org):
	url = base_url + '/vnms/dashboard/tenantDetailAppliances/' + org + '?start=0&limit=200'
	sites = get_data(url,user,password)
	if sites.status_code != 403:
		sites_list = []
		json_object = json.loads(sites.text)
		pairs = json_object.items()
		for key, value in pairs:
			for key  in value:
				for site in value["value"]:
					if site["applianceLocation"]["type"] != "controller":
						sites_list.append(site["name"])
				return(sites_list)
	else:
		return(0)

def get_org_uuid(org):
	url = base_url + '/vnms/organization/orgs?offset=0&limit=25'
	orgs = get_data(url,user,password)
	orgs_object = json.loads(orgs.text)
	#pairs = json_object.items()
	#print(orgs_object["organizations"])
	pairs = orgs_object["organizations"]
	for pair in pairs:
		if pair["name"] == org:
			return  pair["uuid"]

def read_config():
	config = read_yaml('config.yaml')
	#print(config)
	return config

def main():
	#Begining of the main code
	# This pulls the information from the config.yaml file and takes the inputs
	#user = config['user']
	#password = config['password']
	config = read_config()
	global VD_IP
	VD_IP = config['director-ip']
	pingdisable = config['disable-ping']
	#Creates a base URL that all API calls will use
	global base_url
	base_url = 'https://' + VD_IP + ':9182'
	#Checks reachability to Director
	if pingdisable == 'true':
		ping = True
	else:
		ping = check_ping(VD_IP)
	if ping:
		global user
		user = input("Username:")
		global password
		password = getpass.getpass(prompt='Password for "'+ user +':')
		url = base_url + "/vnms/tasks/summary"
		raw = get_data(url,user,password)
		VsnapyShell().cmdloop()
	else:
		raise VD_NotReachable

if __name__ == "__main__":
	try:	
		main()
	except VD_NotReachable:
		print("IP for Versa Director in YAML file is not reachable. Please check")
	except AuthError:
		print("Incorrect Authentication. Please check the user and password")
		print("")
		print("------------")
		print("")
		time.sleep(3)
		main()
