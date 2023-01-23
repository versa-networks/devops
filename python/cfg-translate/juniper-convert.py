#! /usr/bin/python
#
#  juniper-convert.py - Convert Juniper config to Versa config
# 
#  This file has the code to translate Juniper config to Versa config
# 
#  Copyright (c) 2019, Versa Networks, Inc.
#  All rights reserved.
#  pavan@versa-networks.com
#

#
#import statements
#
from enum import Enum
import string
import csv
import json
import objectpath
from optparse import OptionParser
from pprint import pprint
import subprocess,traceback,sys,os,re
import shutil


#date time
from datetime import datetime
import time

#colors
from colorama import Fore, Back, Style

#versa related
from versa.Address import Address
from versa.Address import AddressType
from versa.AddressGroup import AddressGroup
from versa.Schedule import Schedule
from versa.Service import Service
from versa.ServiceGroup import ServiceGroup
from versa.NATPool import NATPool
from versa.NextGenFirewall import NextGenFirewall
from versa.FirewallRule import FirewallRuleAction
from versa.NextGenFirewallRule import NextGenFirewallRule
from versa.VersaConfig import VersaConfig

#global variables
cmdline_opts = None
cmdline_args = None
zone_reader = None
EXIT_FAILURE=1
EXIT_SUCCESS=0

#global variables - 2
jnpr_firewall = { }
tnt_xlate_map = { }
versa_ngfw = None
versa_ngfw_rule = None
data = None
enable_utm = True
versa_output_file = None

#fds
infile_fd = None
tenantfile_fd = None
zonefile_fd = None
versa_out_fd = None

#dictionaries
jnpr_versa_intf_map = { }

#jnpr data
jnpr_cfg_data = { } 
jnpr_fw_data = { }
jnpr_policy_data = { }
jnpr_app_data = {  }
jnpr_zones_data = { }

#
# This function gets command line arguments
#
def get_cmd_line_args():
    """
    This function gets command line arguments
    ------------------------------------------
    -i = input file (jnpr cfg in json format)
    -z = zone file (zone-interface csv file)
    -t = tenant map file (tenant-mapping csv file)
    -d = device name
    -o = output dir
    """
    usage = "usage: %prog -i <jnpr.json> -z <intf.csv> -t <ten.csv> -d <dev> -o <try>"
    cmdline_parser = OptionParser(usage=usage, 
                                   version="jnpr2versa-cfg-xlate-tool 1.0 (beta)")

    #jnpr.conf json input file
    cmdline_parser.add_option("-i", "--input-file", dest="infile",
                        help="Path to Juniper config file in json format", 
                        metavar="infilepath")

    #zone mapping file in csv format
    cmdline_parser.add_option("-z", "--zone-file", dest="zonefile",
                        help="Path to zone/interface CSV file", 
                        metavar="zonefilepath")

    #tenant mapping file in csv format
    cmdline_parser.add_option("-t", "--tenant-file", dest="tenantfile",
                        help="Path to tenant mapping CSV file",
                        metavar="tenantfilepath")

    #device name
    cmdline_parser.add_option("-d", "--device", dest="device",
                        help="Device name", metavar="device")

    #output directory
    cmdline_parser.add_option("-o", "--output-dir", dest="outdir",
                        help="Path to output directory", metavar="outdir")

    #parse command line 
    global cmdline_opts
    global cmdline_args
    (cmdline_opts, cmdline_args) = cmdline_parser.parse_args()

    #sanity check for wrong number of args 
    if (cmdline_opts.infile is None) or (cmdline_opts.zonefile is None):
        cmdline_parser.error("[ERROR]: Wrong Number of arguments")

    #sanity check for wrong number of args 
    if (cmdline_opts.tenantfile is None) or (cmdline_opts.device is None):
        cmdline_parser.error("[ERROR]: Wrong Number of arguments")

    #sanity check for wrong number of args 
    if (cmdline_opts.outdir is None):
        cmdline_parser.error("[ERROR]: Wrong Number of arguments")

    #step1: check sanity of juniper config json input file
    check_infile_sanity(cmdline_opts.infile)

    #step2: check sanity of zone file
    check_zonefile_sanity(cmdline_opts.zonefile)

    #step3: check sanity of tenant file
    check_tenantfile_sanity(cmdline_opts.tenantfile)

    #step4 : create output directory
    create_output_file_and_dir(cmdline_opts.infile, cmdline_opts.outdir)


#
# This function is used to create output dir and output file handle 
#
def create_output_file_and_dir(input_file=None, output_dir_name="jnpr2versa"):
    #get time
    now = datetime.now() 
    dmy = now.strftime("%m-%d-%Y")
    time = now.strftime("%H%M%S")

    #Step1 : Create output dir 
    #generate output dir name
    gen_output_dir_name = os.path.join(output_dir_name + "-" + dmy + "-" + time)

    #create output dir
    if ((os.path.isdir(gen_output_dir_name) != True) or
        (os.path.exists(gen_output_dir_name) != True)):
        try:
            os.mkdir(gen_output_dir_name)
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print("[ERROR]: creating output dir: " + gen_output_dir_name)
            print("[ERROR Details]:")
            print("    " + \
                  repr(traceback.format_exception_only(exc_type, exc_value)))
            print("\nPlease enter a valid directory path where " + \
                  "the output files will be written\n")
            exit(EXIT_FAILURE)
    else:
        print("[ERROR]: Please specify the input Juniper config file, " + \
              "interface/zone CSV file, tenant mapping CSV file " + \
              "and the output directory path")
        exit(EXIT_FAILURE)

    #Step 2: Create output file
    global versa_output_file
    bname_infile = os.path.splitext(os.path.basename(input_file))[0]
    versa_output_file = gen_output_dir_name + "/" + "versa_" + bname_infile + ".conf"
    try:
        global versa_out_fd
        versa_out_fd = open(versa_output_file, 'w')
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("Error: unable to open out file " +  versa_output_file + " for writing")
        print("Error Details:")
        print("    " + \
              repr(traceback.format_exception_only(exc_type, exc_value)))
        exit(EXIT_FAILURE)

#
# This function does sanity check for input file 
#
def check_infile_sanity(infile):
    # open input file
    if (infile):
        try:
            global infile_fd
            infile_fd = open(infile, 'r')
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print("[ERROR]: Unable to open input file " + \
                  infile + " for reading")
            print("[ERROR Details]:")
            print("    " + \
                  repr(traceback.format_exception_only(exc_type, exc_value)))
            exit(EXIT_FAILURE)
    else:
        print("[ERROR]: Please specify the input Juniper config file, " + \
              "interface/zone CSV file, tenant mapping CSV file " + \
              "and the output directory path")
        exit(EXIT_FAILURE)

    print("-> sanity of infile %s: pass" % (infile))

#
# This function does sanity check for tenant file 
#
def check_tenantfile_sanity(tenantfile):
    # open input file
    if (tenantfile):
        try:
            global tenantfile_fd
            tenantfile_fd = open(tenantfile, 'r')
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print("[ERROR]: Unable to open tenant file " + \
                  tenantfile + " for reading")
            print("[ERROR Details]:")
            print("    " + \
                  repr(traceback.format_exception_only(exc_type, exc_value)))
            exit(EXIT_FAILURE)
    else:
        print("[ERROR]: Please specify the input Juniper config file, " + \
              "interface/zone CSV file, tenant mapping CSV file " + \
              "and the output directory path\n")
        exit(EXIT_FAILURE)

    print("-> sanity of tenantfile %s: pass" % (tenantfile))

#
# This function does sanity check for zone file 
#
def check_zonefile_sanity(zonefile):
    # open input file
    if (zonefile):
        try:
            global zonefile_fd
            zonefile_fd = open(zonefile, 'r')
            #zone_reader = csv.DictReader(zonefile_fd)
            #zonefile_csv = csv.reader(zonefile_fd)
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print("[ERROR]: Unable to open input file " + \
                  zonefile + " for reading")
            print("[ERROR Details]:")
            print("    " + \
                  repr(traceback.format_exception_only(exc_type, exc_value)))
            exit(EXIT_FAILURE)
    else:
        print("[ERROR]: Please specify the input Juniper config file, " + \
              "interface/zone CSV file, tenant mapping CSV file " + \
              "and the output directory path\n")
        exit(EXIT_FAILURE)

    print("-> sanity of zonefile %s: pass" % (zonefile))

#
# This function reads zone csv file 
# and adds network, vrf, interfaces and tenants
#
versa_cfg = VersaConfig("versa-config-from-jnpr-config.conf")
def load_zonefile_csv():
    reader = csv.DictReader(zonefile_fd)
    for row in reader:
        #add network and interfaces
        versa_cfg.add_network_and_interface(row["Network"],
                                            row["Versa-Interface"])

        #add routing instance and interfaces
        versa_cfg.add_vrf_and_interface(row["Versa-VRF"],
                                        row["Versa-Interface"])

        #add tenant 
        tenant = versa_cfg.add_tenant(row["Tenant"], None)

        #add zone and interface
        tenant.add_zone_interface(row["Zone"], row["Versa-Interface"], None)

    print("-> loading zone file : pass")

#
# This function reads tenant csv file 
# and constructs tenant xlate map 
#
def load_tenantfile_csv():
    reader = csv.DictReader(tenantfile_fd)
    for row in reader:
        global tnt_xlate_map
        tnt_xlate_map[row["Tenant"]] = row["Tenant"] 
        print(tnt_xlate_map)
    print("-> loading  tenant file : pass")

#
# This function reads juniper config in json format
#
def load_juniper_json_config():
    try:
        global jnpr_cfg_data 
        jnpr_cfg_data = json.load(infile_fd)
    except ValueError as e:
        print("[ERROR]: Invalid json format: %s" % e)
        exit(EXIT_FAILURE)

    print("-> loading  infile (json format) : pass")

    #juniper firewall data
    global jnpr_fw_data
    if jnpr_cfg_data["configuration"][0]["firewall"][0].has_key("family"):
        jnpr_fw_data = jnpr_cfg_data["configuration"][0]["firewall"][0]["family"][0]["inet"][0]
    else:
        jnpr_fw_data = jnpr_cfg_data["configuration"][0]["firewall"][0]

    #juniper policies data
    global jnpr_policy_data
    jnpr_policy_data = jnpr_cfg_data["configuration"][0]["security"][0]["policies"][0]

    #juniper applications data
    global jnpr_app_data
    jnpr_app_data = jnpr_cfg_data["configuration"][0]["applications"][0]

    #juniper zones data
    global jnpr_zones_data
    jnpr_zones_data = jnpr_cfg_data["configuration"][0]["security"][0]["zones"][0]

#
# This function is used to create versa objects address-groups 
# using jnpr address-book address-set data 
#
def create_versa_objects_address_groups_from_jnpr_address_set (tenant=None, line_num=None):

    #jnpr address-book data
    #note: wildcard, fqdn case not handled
    for zone_count in range(len(jnpr_zones_data["security-zone"])) :
        for addr_grp_count in range(len(jnpr_zones_data["security-zone"][zone_count]["address-book"][0]["address-set"])) :
                
                #versa create address-group object
                addr_grp_name = jnpr_zones_data["security-zone"][zone_count]["address-book"][0]["address-set"][addr_grp_count]["name"]["data"]
                addr_grp = AddressGroup(addr_grp_name, None, False)

                #add members of address-group
                for addr_count in range(len(jnpr_zones_data["security-zone"][zone_count]["address-book"][0]["address-set"][addr_grp_count]["address"])) :
                    addr_name = jnpr_zones_data["security-zone"][zone_count]["address-book"][0]["address-set"][addr_grp_count]["address"][addr_count]["name"]["data"]
                 
                    #add address to add-grp
                    addr_grp.add_address(addr_name, None)

                #add address-group object to tenant
                tenant.add_address_group(addr_grp, None)

#
# This function is used to create versa objects addresses
# using jnpr address-book data 
#
def create_versa_objects_addresses_from_jnpr_address_book (tenant=None, line_num=None):

    #jnpr address-book data
    #note: wildcard, fqdn case not handled
    for zone_count in range(len(jnpr_zones_data["security-zone"])) :
        for addr_count in range(len(jnpr_zones_data["security-zone"][zone_count]["address-book"][0]["address"])) :
            if jnpr_zones_data["security-zone"][zone_count]["address-book"][0]["address"][addr_count].has_key("ip-prefix"):
                
                #versa create address object
                addr_name = jnpr_zones_data["security-zone"][zone_count]["address-book"][0]["address"][addr_count]["name"]["data"]
                addr = Address(addr_name, None, False)
                ip_prefix = jnpr_zones_data["security-zone"][zone_count]["address-book"][0]["address"][addr_count]["ip-prefix"][0]["data"]

                # set ip-addr type
                addr.set_addr_type(AddressType.IP_V4_PREFIX, None)

                #set address value
                addr.set_addr_value(ip_prefix, None)

                #add address object to tenant
                tenant.add_address(addr, None)

#
# This function is used create versa applications objects 
# using jnpr applications data 
#
def create_versa_objects_services_from_jnpr_app (tenant=None, line_num=None):

    print("---- application block start ----")

    #jnpr application data
    for app_count in range(len(jnpr_app_data["application"])) :

        #continue
        if not jnpr_app_data["application"][app_count].has_key("term"):
            continue

        print("start")
        print("->app name    : %s" % jnpr_app_data["application"][app_count]["name"]["data"])

        #create versa service object with name
        jnpr_svc_name = jnpr_app_data["application"][app_count]["name"]["data"]
        versa_svc = Service(jnpr_svc_name, line_num, False)

        #name
        if jnpr_app_data["application"][app_count]["term"][0].has_key("name"):
            jnpr_svc_name_2 = jnpr_app_data["application"][app_count]["term"][0]["name"]["data"]
            print("->app name    : %s" % jnpr_app_data["application"][app_count]["term"][0]["name"]["data"])

        #set protocol
        if jnpr_app_data["application"][app_count]["term"][0].has_key("protocol"):
            jnpr_svc_proto = jnpr_app_data["application"][app_count]["term"][0]["protocol"][0]["data"]
            versa_svc.set_proto(jnpr_svc_proto, line_num)
            print("->app protocol: %s" % jnpr_app_data["application"][app_count]["term"][0]["protocol"][0]["data"])

        #set sport range/sport
        if jnpr_app_data["application"][app_count]["term"][0].has_key("source-port"):
            jnpr_svc_sport_range = jnpr_app_data["application"][app_count]["term"][0]["source-port"][0]["data"]
            versa_svc.set_src_port(jnpr_svc_sport_range, line_num)
            print("->app sport   : %s" % jnpr_app_data["application"][app_count]["term"][0]["source-port"][0]["data"])

        #set dport range/dport
        if jnpr_app_data["application"][app_count]["term"][0].has_key("destination-port"):
            jnpr_svc_dport_range = jnpr_app_data["application"][app_count]["term"][0]["destination-port"][0]["data"]
            versa_svc.set_dst_port(jnpr_svc_dport_range, line_num)
            print("->app dport   : %s" % jnpr_app_data["application"][app_count]["term"][0]["destination-port"][0]["data"])

        print("end")

        #add service object to tenant
        tenant.add_service(versa_svc, None)

    print("---- application block end----")

#
# This function is used create versa firewall rule
# using jnpr policy object
#
def create_versa_firewall_rules_from_jnpr_policy (tenant=None, line_num=None):

    #create next gen firewall
    global versa_ngfw
    versa_ngfw = NextGenFirewall(tenant.name + 'unknown', line_num, False)

    #set next gen firewall 
    tenant.set_next_gen_firewall(versa_ngfw, line_num)

    # process all firewall rules
    for policy_count in range(len(jnpr_policy_data["policy"])):

        #src_zone name
        src_zone_name = jnpr_policy_data["policy"][policy_count]["from-zone-name"]["data"]

        #dst_zone name
        dst_zone_name = jnpr_policy_data["policy"][policy_count]["to-zone-name"]["data"]

        for count in range(len(jnpr_policy_data["policy"][policy_count]["policy"])) :
            print(" ----- firewall rule ----- start")

            #create ngfw rule
            ngfw_rule_name = jnpr_policy_data["policy"][policy_count]["policy"][count]["name"]["data"]
            global versa_ngfw_rule
            versa_ngfw_rule = NextGenFirewallRule(ngfw_rule_name, line_num, False)

            #add source-zone to ngfw-rule
            versa_ngfw_rule.add_src_zone(src_zone_name, None)

            #add destination-zone to ngfw-rule
            versa_ngfw_rule.add_dst_zone(dst_zone_name, None)

            #src address
            for src_addr_count in range(len(jnpr_policy_data["policy"][policy_count]["policy"][count]["match"][0]["source-address"])):
                print("-> src_addr : %s" % (jnpr_policy_data["policy"][policy_count]["policy"][count]["match"][0]["source-address"][src_addr_count]["data"]))
                src_addr_name = jnpr_policy_data["policy"][policy_count]["policy"][count]["match"][0]["source-address"][src_addr_count]["data"]
                #versa add source address 
                versa_ngfw_rule.add_src_addr(src_addr_name, None)

            #dst address
            for dst_addr_count in range(len(jnpr_policy_data["policy"][policy_count]["policy"][count]["match"][0]["destination-address"])):
                print("-> dst_addr : %s" % (jnpr_policy_data["policy"][policy_count]["policy"][count]["match"][0]["destination-address"][dst_addr_count]["data"]))
                dst_addr_name = jnpr_policy_data["policy"][policy_count]["policy"][count]["match"][0]["destination-address"][dst_addr_count]["data"]
                #versa add destination address 
                versa_ngfw_rule.add_dst_addr(dst_addr_name, None)

            #application/services
            for app_count in range(len(jnpr_policy_data["policy"][policy_count]["policy"][count]["match"][0]["application"])):
                print("-> application : %s" % (jnpr_policy_data["policy"][policy_count]["policy"][count]["match"][0]["application"][app_count]["data"]))
                svc_name = jnpr_policy_data["policy"][policy_count]["policy"][count]["match"][0]["application"][app_count]["data"]
                #versa add services 
                versa_ngfw_rule.add_service(svc_name, None)

            #then clause permit
            if jnpr_policy_data["policy"][policy_count]["policy"][count]["then"][0].has_key("permit") :
                print("-> then traffic: permit")
                # versa rule action = accept
                versa_ngfw_rule.set_action(FirewallRuleAction.ALLOW, None)

            #then clause deny 
            if jnpr_policy_data["policy"][policy_count]["policy"][count]["then"][0].has_key("deny") :
                print("-> then traffic: deny")
                # versa rule action = reject 
                versa_ngfw_rule.set_action(FirewallRuleAction.REJECT, None)

            print(" ----- firewall rule ----- end")

            #add ngfw_rule to ngfw object
            versa_ngfw.add_rule(versa_ngfw_rule)


#
# This function is used create versa firewall rule
# using jnpr firewall object
#
def create_versa_firewall_rules_from_jnpr_firewall (tenant=None, line_num=None):

    #create next gen firewall
    global versa_ngfw
    print(tenant.name)
    versa_ngfw = NextGenFirewall(tenant.name + 'unknown', line_num, False)

    #set next gen firewall 
    tenant.set_next_gen_firewall(versa_ngfw, line_num)

    # process all firewall rules
    for element in range(len(jnpr_fw_data["filter"])):
            for term in range(len(jnpr_fw_data["filter"][element]["term"])):

                #create ngfw rule
                ngfw_rule_name = jnpr_fw_data["filter"][element]["term"][term]["name"]["data"]
                global versa_ngfw_rule
                versa_ngfw_rule = NextGenFirewallRule(ngfw_rule_name, line_num, False)

                #rule/term object 
                term_object = jnpr_fw_data["filter"][element]["term"][term]

                #print("----- jnpr firewall rule - start -----")
                #rule name
                #print("-> rule name : %s" % (ngfw_rule_name))

                #check for from stanza 
                if term_object.has_key("from"):
                    #addresses
                    if term_object["from"][0].has_key("address"):
                        print("-> from : ip addresses : ")
                        for addr_count in range(len(term_object["from"][0]["address"])):
                            print(term_object["from"][0]["address"][addr_count]["name"]["data"])
                    #ports
                    if term_object["from"][0].has_key("port"):
                        print("-> from : ports: ")
                        for port_count in range(len(term_object["from"][0]["port"])):
                            print(term_object["from"][0]["port"][port_count]["data"])
                        
                #check for then stanza
                if term_object.has_key("then"):
                    #forwarding class
                    if term_object["then"][0].has_key("forwarding-class"):
                        print("->then : fwd-class: %s" % (term_object["then"][0]["forwarding-class"][0]["data"]))

                    # accept
                    if term_object["then"][0].has_key("accept"):
                        print("->then : accept")
                        # versa rule action = accept
                        versa_ngfw_rule.set_action(FirewallRuleAction.ALLOW, None)

                    # reject 
                    if term_object["then"][0].has_key("reject"):
                        print("->then : reject")
                        # versa rule action = reject 
                        versa_ngfw_rule.set_action(FirewallRuleAction.REJECT, None)

                print("----- jnpr firewall rule - end-----")

               #check if utm should be enabled or not
                if (enable_utm):
                    versa_ngfw_rule.set_av_profile('"Scan Web and Email Traffic"', 0)
                    versa_ngfw_rule.set_ips_profile('"Versa Recommended Profile"', 0)
                else:
                    versa_ngfw_rule.set_av_profile(None, 0)
                    versa_ngfw_rule.set_ips_profile(None, 0)

                #add ngfw_rule to ngfw object
                versa_ngfw.add_rule(versa_ngfw_rule)

                #add src zone map
                zm = {"Wireless_30": "20"}
                versa_ngfw_rule.set_src_zone_map(zm)

                #add dst zone map
                zm = {"Wireless_30": "20"}
                versa_ngfw_rule.set_dst_zone_map(zm)

#
# This function acts as main() 
#
def main():

    #for each tenant 
    for k, tenant_name in tnt_xlate_map.iteritems():

        #get tenant
        tenant = versa_cfg.get_tenant(tenant_name, None)

        # creates "set orgs org-services <tnt-name> security access-policies Default-Policy rules .."
        create_versa_firewall_rules_from_jnpr_firewall(tenant, None)

        # creates "set orgs org-services <tnt-name> security access-policies Default-Policy rules .."
        create_versa_firewall_rules_from_jnpr_policy(tenant, None)

        #creates "set orgs org-services <tnt-name> objects addresses .. "
        create_versa_objects_addresses_from_jnpr_address_book(tenant, None)

        #creates "set orgs org-services <tnt-name> objects address-groups"
        create_versa_objects_address_groups_from_jnpr_address_set(tenant, None)

        # creates "set orgs org-services <tenant-name> objects services"
        create_versa_objects_services_from_jnpr_app(tenant, None)

#
# This function loads all input files
# - juniper config in json format
# - zone interface mapping csv file
# - tenants csv file
#
def load_input_files():

    #load juniper config (json format) into python dictionary
    load_juniper_json_config()

    #load zonefile csv
    load_zonefile_csv()

    #load tenantfile csv
    load_tenantfile_csv()

#
# This function is called just before exit
# - close open file descriptors
# - print output
#
def jnpr_2_versa_conf_conversion_exit():

    #close opened files
    infile_fd.close()
    versa_out_fd.close()
    zonefile_fd.close()
    tenantfile_fd.close()

    #print user output
    print(Fore.CYAN)
    print(Style.BRIGHT)
    print("-------------------Details below ----------------------------------")
    print("Input Juniper Config (json format) : %s" % (cmdline_opts.infile))
    print("Input interface-zone csv file      : %s" % (cmdline_opts.zonefile))
    print("Input tenant-zone csv file         : %s" % (cmdline_opts.tenantfile))
    print("Ouput Versa Config                 : %s" % (versa_output_file))
    print("-------------------------------------------------------------------")
    print(Style.RESET_ALL)

#
# This function is used to write final config
#
def generate_final_versa_config():
    global versa_cfg

    #check config
    #versa_cfg.check_config(strict_checks)

    # final write to file
    global cmdline_opts
    versa_cfg.write_config(tnt_xlate_map, None, cmdline_opts.device,
                           versa_out_fd, None)


# ------- fun starts here ------------
start_time = time.time()

#step1: process cmdline params
get_cmd_line_args()

#step2: load input files for processing
load_input_files()

#step3: process input files
main()

#step4: write output versa config
generate_final_versa_config()

#step5: cleanup and exit
jnpr_2_versa_conf_conversion_exit()

end_time = time.time()
print("time-taken: %s (secs)" % (end_time - start_time))
# --- end of file ---
