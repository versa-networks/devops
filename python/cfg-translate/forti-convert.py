#! /usr/bin/python
#
#  forti-convert.py - Convert Fortinet config to Versa config
# 
#  This file has the code to translate Fortinet config to Versa config
# 
#  Copyright (c) 2017, Versa Networks, Inc.
#  All rights reserved.
#


from __future__ import print_function
from optparse import OptionParser
import subprocess,traceback,sys,os,re
import string
import csv
from enum import Enum
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



class ConfigState(Enum):
    NONE = 0
    POLICY = 1
    ADDRESS = 2
    ADDRESS_GROUP = 3
    SCHEDULE = 4
    SERVICE = 5
    SERVICE_GROUP = 6
    NAT_POOL = 7



strict_checks = False
# strict_checks = True


debug_enable = False
debug_enable = True

input_line_num = 0
cfg_state = ConfigState.NONE
cfg_depth = 0
cfg_global = False
cfg_vdom = False
cur_vdom = ''
intf_zone_map = { }
tnt_xlate_map = { }

cur_tenant = None
cur_addr = None
cur_addr_grp = None
cur_schedule = None
cur_schedule_is_recurring = False
cur_svc = None
cur_svc_grp = None
cur_ngfw = None
cur_ngfw_rule = None
cur_forti_ngfw_rule = None
cur_ngfw_rule_has_error = False
cur_natpool = None
cur_rule_num = 0

versa_cfg = VersaConfig('VersaCfg_From_Fortinet')
forti_rules = [ ]



def debug_print(s):
    if (debug_enable):
        print("Line %d: %s" % (input_line_num, s))



# Get command line arguments
o_parser = OptionParser()
o_parser.add_option("-i", "--inputfile", dest="infile",
                    help="Path to Fortinet config file", metavar="infilepath")
o_parser.add_option("-z", "--zonefile", dest="zonefile",
                    help="Path to zone/interface CSV file", metavar="zonefilepath")
o_parser.add_option("-t", "--tenantfile", dest="tenantfile",
                    help="Path to tenant mapping CSV file", metavar="tenantfilepath")
o_parser.add_option("-T", "--template", dest="template",
                    help="Template name", metavar="template")
o_parser.add_option("-D", "--device", dest="device",
                    help="Device name", metavar="device")
o_parser.add_option("-o", "--outputdir", dest="outdir",
                    help="Path to output directory", metavar="outdir")
o_parser.add_option("-f", "--fortinet-paths-file", dest="fpathsfile",
                    help="Path to Fortinet path segments file", metavar="fpathsfile")
o_parser.add_option("-v", "--versa-paths-file", dest="vpathsfile",
                    help="Path to Versa path segments file", metavar="vpathsfile")
o_parser.add_option("-V", "--default-vdom", dest="defaultvdom",
                    help="Default VDOM", metavar="defaultvdom")
(c_options, c_args) = o_parser.parse_args()



# Ensure that only one of device or template is specified if transation is
# to be done for versa director
if (c_options.template and c_options.device):
    print("To generate config that can be loaded into the Versa Director " + \
          "configuration, please specify either the Config Template name " + \
          "or the Device name for which config should be generated\n")
    exit(1)


def print_usage():
    print("Please specify the input Fortinet config file, " + \
          "interface/zone CSV file, tenant mapping CSV file, " + \
          "Versa template/device, default VDOM and the output directory path\n")


# open input file
if (c_options.infile):

    try:
        in_fh = open(c_options.infile, 'r')
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("Error: unable to open input file " + \
              c_options.infile + " for reading")
        print("Error Details:")
        print("    " + \
              repr(traceback.format_exception_only(exc_type, exc_value)))
        exit(1)
else:
    print("Input config file parameter missing\n")
    print_usage()
    exit(1)


# open zone/interface file
if (c_options.zonefile):

    try:
        zone_fh = open(c_options.zonefile, 'r')
        zone_csv = csv.reader(zone_fh)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("Error: unable to open zone/interface csv file " + \
              c_options.zonefile + " for reading")
        print("Error Details:")
        print("    " + \
              repr(traceback.format_exception_only(exc_type, exc_value)))
        exit(1)
else:
    print("Zone/interface mapping file parameter missing\n")
    print_usage()
    in_fh.close()
    exit(1)


# open tenant mapping file
if (c_options.tenantfile):

    try:
        tenant_fh = open(c_options.tenantfile, 'r')
        tenant_csv = csv.reader(tenant_fh)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("Error: unable to open tenant mapping csv file " + \
              c_options.tenantfile + " for reading")
        print("Error Details:")
        print("    " + \
              repr(traceback.format_exception_only(exc_type, exc_value)))
        exit(1)
else:
    print("Tenant mapping file parameter missing\n")
    print_usage()
    in_fh.close()
    zone_fh.close()
    exit(1)


# Default vdom
if (c_options.defaultvdom):
    cur_vdom = c_options.defaultvdom
else:
    print("Current VDOM parameter missing\n")
    print_usage()
    exit(1)


# populate the zone/interface map
vdom_intf_map = { }
forti_versa_intf_map = { }
for row in zone_csv:

    # ignore invalid rows
    if (row[0].startswith('#')):
        continue
    if (len(row) < 4):
        continue

    # Update interface zone map
    intf_zone_map[row[0]] = row[1:]

    # Update vdom zone map
    if (row[6] not in vdom_intf_map):
        vdom_intf_map[row[6]] = [ row[0] ]
    else:
        vdom_intf_map[row[6]].extend( [ row[0] ] )

    # Update fortinet -> versa intf map
    forti_versa_intf_map[row[0]] = row[3]

zone_fh.close()


# populate the tenant map
for row in tenant_csv:
    if (row[0].startswith('#')):
        continue
    if (len(row) < 2):
        continue
    tnt_xlate_map[row[0]] = row[1:]
tenant_fh.close()



# create output dir
if (c_options.outdir):
    if ((os.path.isdir(c_options.outdir) != True) or
        (os.path.exists(c_options.outdir) != True)):
        try:
            os.mkdir(c_options.outdir)
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print("Error creating output dir: " + c_options.outdir)
            print("Error Details:")
            print("    " + \
                  repr(traceback.format_exception_only(exc_type, exc_value)))
            print("\nPlease enter a valid directory path where " + \
                  "the output files will be written\n")
            exit(1)
else:
    print("Output directory parameter missing\n")
    print_usage()
    in_fh.close()
    exit(1)



# open output file
bname = os.path.splitext(os.path.basename(c_options.infile))[0]
outfile = c_options.outdir + '/' + bname + '.cfg'
try:
    out_fh = open(outfile, 'w')
except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    print("Error: unable to open out file " + \
          c_options.outdir + "/" + outfile + " for writing")
    print("Error Details:")
    print("    " + \
          repr(traceback.format_exception_only(exc_type, exc_value)))
    in_fh.close()
    exit(1)




# open output csv file
bname = os.path.splitext(os.path.basename(c_options.infile))[0]
csv_outfile = c_options.outdir + '/' + bname + '.csv'
try:
    csv_out_fh = open(csv_outfile, 'w')
except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    print("Error: unable to open out file " + \
          c_options.outdir + "/" + csv_outfile + " for writing")
    print("Error Details:")
    print("    " + \
          repr(traceback.format_exception_only(exc_type, exc_value)))
    in_fh.close()
    out_fh.close()
    exit(1)




# open log file
logfile = c_options.outdir + '/' + bname + '.json'
try:
    log_fh = open(logfile, 'w')
except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    print("Error: unable to open log file " + \
          c_options.outdir + "/" + logfile + " for writing")
    print("Error Details:")
    print("    " + \
          repr(traceback.format_exception_only(exc_type, exc_value)))
    in_fh.close()
    csv_out_fh.close()
    out_fh.close()
    exit(1)



versa_cfg = VersaConfig('VersaCfg_From_Fortinet_' + bname)

zone_utm_map = { }
for ifname, ifinfo in intf_zone_map.iteritems():
    if (len(ifinfo) > 5):
        zone = ifinfo[0]
        nw = ifinfo[1]
        intf = ifinfo[2]
        paired_intf = ifinfo[3]
        vrf = ifinfo[4]
        vdom = ifinfo[5]
        utm_enable = ifinfo[6]
        tname = tnt_xlate_map[vdom][0]

        # Update paired interfaces
        if (len(intf) > 0 and len(paired_intf) > 0):
            versa_cfg.add_paired_interface(intf, paired_intf)
            debug_print("interface %s: paired interface %s" % (intf, paired_intf))
        # Update network <-> interfaces
        versa_cfg.add_network_and_interface(nw, intf)

        # Update routing-instance <-> interfaces
        versa_cfg.add_vrf_and_interface(vrf, intf)

        # Update routing-instance <-> interfaces
        cur_tenant = versa_cfg.get_tenant(vdom, input_line_num)
        cur_tenant.add_zone_interface(zone, intf, input_line_num)

        if (utm_enable == 'true'):
            zone_utm_map[zone] = True
        else:
            zone_utm_map[zone] = False


vdom_path_map = { }
vdom_zone_map = { }
for vdom, intf_list in vdom_intf_map.iteritems():
    debug_print("Evaluating paths for vdom: %s" % (vdom))
    for i in range(0, len(intf_list)):
        intf1 = intf_list[i]
        if (intf1.startswith('TVI')):
            continue
        if (vdom not in vdom_zone_map):
            vdom_zone_map[vdom] = [ intf_zone_map[intf1][0] ]
        else:
            vdom_zone_map[vdom].extend( [ intf_zone_map[intf1][0] ] )



print('# SerialNum,VDom,RuleName,SrcZone,DstZone,SrcAddr,DstAddr,Services,Schedule,Action,AV,IPS', file=csv_out_fh)

for ln in in_fh:

    # strip whitespace and update line number
    input_line_num = input_line_num + 1
    l = ln.rstrip()

    # skip comments
    if (len(l) == 0 or l.startswith('#')):
        continue

    # If already inside of a config block look for the end statement and
    # update the depth appropriately
    if (cfg_depth > 0):
        if (l.strip() == 'end'):
            cfg_depth = cfg_depth - 1
            if (cfg_depth == 0):
                if (cfg_global):
                    cfg_global = False
                elif (cfg_vdom):
                    cfg_vdom = False
                    if (cur_tenant is not None):
                        debug_print("Tenant end: " + cur_tenant.name)
                        cur_tenant = None
            elif (cfg_depth == 1):
                if (cfg_state == ConfigState.POLICY):
                    debug_print("Next gen firewall end: %s" % (cur_ngfw.name))
                    cur_tenant.set_next_gen_firewall(cur_ngfw,
                                                     cur_ngfw.name_src_line)
                    cur_ngfw = None
                    cfg_state = ConfigState.NONE
                elif (cfg_state == ConfigState.ADDRESS):
                    debug_print("Address object definitions end")
                    cur_addr = None
                    cfg_state = ConfigState.NONE
                elif (cfg_state == ConfigState.ADDRESS_GROUP):
                    debug_print("Address Group object definitions end")
                    cur_addr_grp = None
                    cfg_state = ConfigState.NONE
                elif (cfg_state == ConfigState.SCHEDULE):
                    debug_print("Schedule object definitions end")
                    cur_schedule = None
                    cur_schedule_is_recurring = False
                    cfg_state = ConfigState.NONE
                elif (cfg_state == ConfigState.SERVICE):
                    debug_print("Service object definitions end")
                    cur_svc = None
                    cfg_state = ConfigState.NONE
                elif (cfg_state == ConfigState.SERVICE_GROUP):
                    debug_print("Service Group object definitions end")
                    cur_svc_grp = None
                    cfg_state = ConfigState.NONE
                elif (cfg_state == ConfigState.NAT_POOL):
                    debug_print("NAT Pool object definitions end")
                    cur_natpool = None
                    cfg_state = ConfigState.NONE
            continue

    # tokenize the config line
    words = l.split()
    if (len(words) <= 0):
        debug_print("Syntax error")
        break

    # Create current tenant if within vdom
    if (cfg_depth == 1 and cfg_vdom):
        if (words[0] == 'edit'):
            cur_tenant = versa_cfg.get_tenant(words[1], input_line_num)
            debug_print("Tenant start: " + cur_tenant.name)
        elif (words[0] == 'next'):
            debug_print("Tenant end: " + cur_tenant.name)
            cur_tenant = None

    # Process the configuration depending on the state
    if (cfg_state == ConfigState.POLICY):
        if (words[0] == 'edit'):
            rule_nm = words[1]
            for ix in range(2, len(words)):
                rule_nm = rule_nm + '_' + words[ix]
            if (len(rule_nm) > 31):
                rule_nm = words[len(words) - 1]
            rule_nm = rule_nm.replace('"', '')
            rule_nm = rule_nm.replace('/', '_')
            rule_nm = rule_nm.replace('(', '_')
            rule_nm = rule_nm.replace(')', '_')

            cur_forti_ngfw_rule = NextGenFirewallRule(words[1],
                                                      input_line_num, False)
            cur_forti_ngfw_rule.set_tenant(cur_vdom)
            cur_ngfw_rule = NextGenFirewallRule('Rule_' + words[1],
                                                input_line_num, False)
            cur_ngfw_rule_has_error = False
            debug_print("Next gen firewall rule start: %s" %
                        (cur_ngfw_rule.name))
        elif (words[0] == 'next'):
            debug_print("Next gen firewall rule end: %s" % (cur_ngfw_rule.name))
            if (cur_ngfw_rule_has_error):
                debug_print("Skipping Next gen firewall rule %s because "
                            "it has error(s)" %
                            (cur_ngfw_rule.name))
            else:
                forti_rules.append(cur_forti_ngfw_rule)
                cur_rule_num = cur_rule_num + 1
                sz_map = cur_forti_ngfw_rule.get_src_zone_map()
                dz_map = cur_forti_ngfw_rule.get_dst_zone_map()
                print('%d,' % (cur_rule_num), end='', file=csv_out_fh)
                print('%s,' % (cur_forti_ngfw_rule.get_tenant()), end='', file=csv_out_fh)
                print('\"%s\",' % (cur_forti_ngfw_rule.get_name()), end='', file=csv_out_fh)
                print('\"%s\",' % (sz_map.keys()), end='', file=csv_out_fh)
                print('\"%s\",' % (dz_map.keys()), end='', file=csv_out_fh)
                print('\"%s\",' % (cur_forti_ngfw_rule.get_src_addr_map().keys()), end='', file=csv_out_fh)
                print('\"%s\",' % (cur_forti_ngfw_rule.get_dst_addr_map().keys()), end='', file=csv_out_fh)
                print('\"%s\",' % (cur_forti_ngfw_rule.get_service_map().keys()), end='', file=csv_out_fh)
                print('\"%s\",' % (cur_forti_ngfw_rule.get_schedule()), end='', file=csv_out_fh)
                print('\"%s\",' % (FirewallRuleAction.get_action_string(cur_forti_ngfw_rule.get_action())), end='', file=csv_out_fh)
                print('%s,' % (cur_forti_ngfw_rule.get_av_profile()), end='', file=csv_out_fh)
                print('%s,' % (cur_forti_ngfw_rule.get_ips_profile()), file=csv_out_fh)

                if (len(vdom_path_map.keys()) == 0):
                    enable_utm = False
                    zm = { }
                    if ('any' in sz_map.keys()):
                        for z in vdom_zone_map[cur_vdom]:
                            zm[z] = input_line_num
                            if (zone_utm_map[z]):
                                enable_utm = True
                    else:
                        for fi in sz_map.keys():
                            vi = forti_versa_intf_map[fi]
                            z = cur_tenant.get_zone_for_interface(vi)
                            zm[z] = input_line_num
                            if (zone_utm_map[z]):
                                enable_utm = True
                    cur_ngfw_rule.set_src_zone_map(zm)
                    if (enable_utm):
                        cur_ngfw_rule.set_av_profile('"Scan Web and Email Traffic"', 0)
                        cur_ngfw_rule.set_ips_profile('"Versa Recommended Profile"', 0)
                    else:
                        cur_ngfw_rule.set_av_profile(None, 0)
                        cur_ngfw_rule.set_ips_profile(None, 0)

                    zm = { }
                    if ('any' in dz_map.keys()):
                        for z in vdom_zone_map[cur_vdom]:
                            zm[z] = input_line_num
                    else:
                        for fi in dz_map.keys():
                            vi = forti_versa_intf_map[fi]
                            z = cur_tenant.get_zone_for_interface(vi)
                            zm[z] = input_line_num
                    cur_ngfw_rule.set_dst_zone_map(zm)

                    print('%d.1,' % (cur_rule_num), end='', file=csv_out_fh)
                    print('%s,' % (tnt_xlate_map[cur_vdom]), end='', file=csv_out_fh)
                    print('\"%s\",' % (cur_ngfw_rule.get_name()), end='', file=csv_out_fh)
                    print('\"%s\",' % (cur_ngfw_rule.get_src_zone_map().keys()), end='', file=csv_out_fh)
                    print('\"%s\",' % (cur_ngfw_rule.get_dst_zone_map().keys()), end='', file=csv_out_fh)
                    print('\"%s\",' % (cur_ngfw_rule.get_src_addr_map().keys()), end='', file=csv_out_fh)
                    print('\"%s\",' % (cur_ngfw_rule.get_dst_addr_map().keys()), end='', file=csv_out_fh)
                    print('\"%s\",' % (cur_ngfw_rule.get_service_map().keys()), end='', file=csv_out_fh)
                    print('\"%s\",' % (cur_ngfw_rule.get_schedule()), end='', file=csv_out_fh)
                    print('\"%s\",' % (FirewallRuleAction.get_action_string(cur_ngfw_rule.get_action())), end='', file=csv_out_fh)
                    print('%s,' % (cur_ngfw_rule.get_av_profile()), end='', file=csv_out_fh)
                    print('%s,' % (cur_ngfw_rule.get_ips_profile()), file=csv_out_fh)
                    cur_ngfw.add_rule(cur_ngfw_rule)
                else:
                    debug_print("SZ map: %s" % sz_map)
                    debug_print("DZ map: %s" % dz_map)
                    sub_ix = 0
                    for sz in sz_map:
                        for dz in dz_map:
                            key = cur_vdom + ':' + sz + ':' + dz
                            debug_print("Looking for interface path %s" %
                                        (key))
                            if key in vdom_path_map:
                                path_segments = vdom_path_map[key]
                                for i in range(0, len(path_segments) - 1):
                                    ps1 = path_segments[i]
                                    ps2 = path_segments[i + 1]
                                    if (ps1 == versa_cfg.get_paired_interface(ps2)):
                                        continue
                                    sub_ix = sub_ix + 1

                                    enable_utm = False
                                    sz = cur_tenant.get_zone_for_interface(ps1)
                                    dz = cur_tenant.get_zone_for_interface(ps2)
                                    if (zone_utm_map[sz]):
                                        enable_utm = True
                                    debug_print("src zone %s; utm: %s" % (sz, str(enable_utm)))
                                    new_rule = NextGenFirewallRule(
                                                cur_ngfw_rule.name + '.' + str(sub_ix),
                                                cur_ngfw_rule.name_src_line,
                                                False)
                                    if (enable_utm):
                                        new_rule.set_av_profile('"Scan Web and Email Traffic"', 0)
                                        new_rule.set_ips_profile('"Versa Recommended Profile"', 0)
                                    else:
                                        new_rule.set_av_profile(None, 0)
                                        new_rule.set_ips_profile(None, 0)
                                    new_rule.set_src_zone_map(
                                                   { sz : input_line_num })
                                    new_rule.set_dst_zone_map(
                                                   { dz : input_line_num })
                                    new_rule.set_src_addr_map(cur_ngfw_rule.get_src_addr_map())
                                    new_rule.set_dst_addr_map(cur_ngfw_rule.get_dst_addr_map())
                                    new_rule.set_service_map(cur_ngfw_rule.get_service_map())
                                    new_rule.set_schedule(cur_ngfw_rule.get_schedule(), 0)
                                    print('%d.%d,' % (cur_rule_num, sub_ix), end='', file=csv_out_fh)
                                    print('%s,' % (tnt_xlate_map[cur_vdom]), end='', file=csv_out_fh)
                                    print('\"%s\",' % (new_rule.get_name()), end='', file=csv_out_fh)
                                    print('\"%s\",' % (new_rule.get_src_zone_map().keys()), end='', file=csv_out_fh)
                                    print('\"%s\",' % (new_rule.get_dst_zone_map().keys()), end='', file=csv_out_fh)
                                    print('\"%s\",' % (new_rule.get_src_addr_map().keys()), end='', file=csv_out_fh)
                                    print('\"%s\",' % (new_rule.get_dst_addr_map().keys()), end='', file=csv_out_fh)
                                    print('\"%s\",' % (new_rule.get_service_map().keys()), end='', file=csv_out_fh)
                                    print('\"%s\",' % (new_rule.get_schedule()), end='', file=csv_out_fh)
                                    print('%s,' % FirewallRuleAction.get_action_string(new_rule.get_action()), end='', file=csv_out_fh)
                                    print('%s,' % (new_rule.get_av_profile()), end='', file=csv_out_fh)
                                    print('%s,' % (new_rule.get_ips_profile()), file=csv_out_fh)
                                    cur_ngfw.add_rule(new_rule)
            cur_ngfw_rule = None
            cur_forti_ngfw_rule = None
            cur_ngfw_rule_has_error = False
        elif (words[0] == 'set'):
            if (words[1] == 'name'):
                if (words[2].startswith('"')):
                    nm = words[2].replace('"', '')
                    nm = nm.replace(',', '')
                    nm = nm.replace('.', '_')
                    for i in range(3, len(words)):
                        cur_nm = words[i].replace(',', '')
                        if (cur_nm.endswith('"')):
                            nm = nm + '_' + cur_nm.replace('"', '')
                            break
                        else:
                            nm = nm + '_' + cur_nm
                else:
                    nm = words[2]
                nm = nm.replace('/', '_')
                nm = nm.replace('(', '_')
                nm = nm.replace(')', '_')
                cur_ngfw_rule.set_name(nm, input_line_num)
                cur_forti_ngfw_rule.set_name(nm, input_line_num)
            elif (words[1] == 'srcintf'):
                for i in range(2, len(words)):
                    cur_nm = words[i].replace('"', '')
                    cur_forti_ngfw_rule.add_src_zone(cur_nm, input_line_num)
                    if (cur_nm.lower() != 'any'):
                        if (cur_nm not in intf_zone_map):
                            cur_ngfw_rule_has_error = True
                            debug_print('Interface/zone mapping not found for interface ' + cur_nm)
                        else:
                            cur_ngfw_rule.add_src_zone(intf_zone_map[cur_nm][0],
                                                       input_line_num)
            elif (words[1] == 'dstintf'):
                for i in range(2, len(words)):
                    cur_nm = words[i].replace('"', '')
                    cur_forti_ngfw_rule.add_dst_zone(cur_nm, input_line_num)
                    if (cur_nm.lower() != 'any'):
                        if (cur_nm not in intf_zone_map):
                            cur_ngfw_rule_has_error = True
                            debug_print('Interface/zone mapping not found for interface ' + cur_nm)
                        else:
                            cur_ngfw_rule.add_dst_zone(intf_zone_map[cur_nm][0],
                                                       input_line_num)
            elif (words[1] == 'srcaddr'):
                for i in range(2, len(words)):
                    cur_nm = words[i].replace('"', '')
                    cur_forti_ngfw_rule.add_src_addr(cur_nm, input_line_num)
                    if (cur_nm.lower() != 'all'):
                        cur_ngfw_rule.add_src_addr(cur_nm,
                                                   input_line_num)
            elif (words[1] == 'dstaddr'):
                for i in range(2, len(words)):
                    cur_nm = words[i].replace('"', '')
                    cur_forti_ngfw_rule.add_dst_addr(cur_nm, input_line_num)
                    if (cur_nm.lower() != 'all'):
                        cur_ngfw_rule.add_dst_addr(cur_nm,
                                                   input_line_num)
            elif (words[1] == 'action'):
                if (words[2].lower() == 'accept'):
                    cur_ngfw_rule.set_action(FirewallRuleAction.ALLOW,
                                             input_line_num)
                    cur_forti_ngfw_rule.set_action(FirewallRuleAction.ALLOW,
                                                   input_line_num)
            elif (words[1] == 'schedule'):
                cur_ngfw_rule.set_schedule(words[2].replace('"', ''),
                                           input_line_num)
                cur_forti_ngfw_rule.set_schedule(words[2].replace('"', ''),
                                                 input_line_num)
            elif (words[1] == 'service'):
                cur_nm = ""
                for i in range(2, len(words)):
                    if (not cur_nm == ""):
                        cur_nm = cur_nm + '_' + words[i]
                    else:
                        cur_nm = words[i]
                    if (not cur_nm.endswith('"')):
                        continue
                    cur_nm = cur_nm.replace('"', '')
                    if (len(cur_nm) > 31):
                        cur_nm = words[i]
                        cur_nm = cur_nm.replace('"', '')
                    if (cur_nm.lower() != 'all'):
                        cur_ngfw_rule.add_service(cur_nm, input_line_num)
                    cur_forti_ngfw_rule.add_service(cur_nm, input_line_num)
                    cur_nm = ""
            elif (words[1] == 'devices'):
                cur_nm = ""
                for i in range(2, len(words)):
                    if (not cur_nm == ""):
                        cur_nm = cur_nm + '_' + words[i]
                    else:
                        cur_nm = words[i]
                    if (not cur_nm.endswith('"')):
                        continue
                    cur_nm = cur_nm.replace('"', '')
                    cur_ngfw_rule.add_devices(cur_nm, input_line_num)
                    cur_forti_ngfw_rule.add_devices(cur_nm, input_line_num)
                    cur_nm = ""
            elif (words[1] == 'poolname'):
                cur_nm = ""
                for i in range(2, len(words)):
                    if (not cur_nm == ""):
                        cur_nm = cur_nm + '_' + words[i]
                    else:
                        cur_nm = words[i]
                    if (not cur_nm.endswith('"')):
                        continue
                cur_nm = cur_nm.replace('"', '')
                cur_ngfw_rule.set_natpool(cur_nm, input_line_num)
                cur_forti_ngfw_rule.set_natpool(cur_nm, input_line_num)
                cur_nm = ""
            elif (words[1] == 'av-profile'):
                cur_nm = ""
                for i in range(2, len(words)):
                    if (not cur_nm == ""):
                        cur_nm = cur_nm + '_' + words[i]
                    else:
                        cur_nm = words[i]
                    if (not cur_nm.endswith('"')):
                        continue
                cur_nm = cur_nm.replace('"', '')
                cur_ngfw_rule.set_av_profile(cur_nm, input_line_num)
                cur_forti_ngfw_rule.set_av_profile(cur_nm, input_line_num)
                cur_nm = ""
            elif (words[1] == 'ips-sensor'):
                cur_nm = ""
                for i in range(2, len(words)):
                    if (not cur_nm == ""):
                        cur_nm = cur_nm + '_' + words[i]
                    else:
                        cur_nm = words[i]
                    if (not cur_nm.endswith('"')):
                        continue
                cur_nm = cur_nm.replace('"', '')
                cur_ngfw_rule.set_ips_profile(cur_nm, input_line_num)
                cur_forti_ngfw_rule.set_ips_profile(cur_nm, input_line_num)
                cur_nm = ""
    elif (cfg_state == ConfigState.ADDRESS):
        if (words[0] == 'edit'):
            addr_nm = words[1]
            for ix in range(2, len(words)):
                addr_nm = addr_nm + '_' + words[ix]
            if (len(addr_nm) > 31):
                addr_nm = words[len(words) - 1]
            addr_nm = addr_nm.replace('"', '')
            cur_addr = Address(addr_nm,
                               input_line_num, False)
            debug_print("Address object start: %s" %
                        (cur_addr.name))
        elif (words[0] == 'next'):
            if (cur_addr is not None):
                debug_print("Address object end: %s" % (cur_addr.name))
                cur_tenant.add_address(cur_addr, input_line_num)
            cur_addr = None
        elif (words[0] == 'set'):
            if (words[1] == 'type'):
                if (words[2] == 'iprange'):
                    cur_addr.set_addr_type(AddressType.IP_V4_RANGE,
                                           input_line_num)
                elif (words[2] == 'fqdn'):
                    cur_addr.set_addr_type(AddressType.FQDN,
                                           input_line_num)
                elif (words[2] == 'wildcard'):
                    cur_addr.set_addr_type(AddressType.WILDCARD,
                                           input_line_num)
            elif (words[1] == 'wildcard'):
                cur_addr.set_addr_value(words[2] + '/' + words[3],
                                        input_line_num)
            elif (words[1] == 'start-ip'):
                cur_addr.set_start_ip(words[2], input_line_num)
            elif (words[1] == 'end-ip'):
                st_ip = cur_addr.start_ip.split('.')
                end_ip = words[2].split('.')
                if (st_ip[0] != end_ip[0]):
                    raise Exception('Line %d: start/end IP address should belong to same /8 prefix' % ( input_line_num ) )
                elif (st_ip[1] != end_ip[1]):
                    debug_print("Address object %s: adding multiple address objects for range %s.%d - %s.%d" % (cur_addr.name, st_ip[0], int(st_ip[1]), st_ip[0], int(end_ip[1])))
                    addr_grp = AddressGroup(cur_addr.name,
                                            cur_addr.name_src_line, False)
                    for ix in range(int(st_ip[1]), int(end_ip[1]) + 1):
                        addr = Address(cur_addr.name + '-' + str(ix),
                                       cur_addr.name_src_line, False)
                        addr.set_addr_type(AddressType.IP_V4_RANGE,
                                           input_line_num)
                        cur_st_ip = st_ip[0] + '.' + \
                                    str(ix) + '.' + \
                                    st_ip[2] + '.' + \
                                    st_ip[3]
                        cur_end_ip = end_ip[0] + '.' + \
                                     str(ix) + '.' + \
                                     end_ip[2] + '.' + \
                                     end_ip[3]
                        addr.set_start_ip(cur_st_ip, input_line_num)
                        addr.set_end_ip(cur_end_ip, input_line_num)
                        debug_print("Adding address object %s to tenant %s" % (addr.name, cur_tenant.name))
                        cur_tenant.add_address(addr, input_line_num)
                        addr_grp.add_address(addr.name, input_line_num)
                    cur_tenant.add_address_group(addr_grp, input_line_num)
                    debug_print("Address object end: %s" % (cur_addr.name))
                    cur_addr = None
                else:
                    cur_addr.set_end_ip(words[2], input_line_num)
            elif (words[1] == 'fqdn'):
                cur_addr.set_addr_value(words[2], input_line_num)
            elif (words[1] == 'subnet'):
                cur_addr.set_addr_type(AddressType.IP_V4_PREFIX,
                                       input_line_num)
                ip_addr = words[2]
                mask = words[3]
                mask_bytes = mask.split('.')
                int_mask = 0
                for ix in range(0, 4):
                    mask_byte = int(mask_bytes[ix])
                    int_mask = int_mask << 8
                    int_mask = int_mask | mask_byte
                mask_len = 0
                mask_bit = 1
                for ix in range(0, 32):
                    if (int_mask & mask_bit):
                        break
                    else:
                        mask_len = mask_len + 1
                        mask_bit = mask_bit << 1
                mask_len = 32 - mask_len
                # debug_print("IP prefix: %s %s 0x%x %d" %
                #             ( ip_addr, mask, int_mask, mask_len))
                cur_addr.set_addr_value(ip_addr + '/' + str(mask_len),
                                        input_line_num)
    elif (cfg_state == ConfigState.ADDRESS_GROUP):
        if (words[0] == 'edit'):
            cur_addr_grp = AddressGroup(words[1].replace('"', ''),
                                        input_line_num, False)
            debug_print("Address Group object start: %s" %
                        (cur_addr_grp.name))
        elif (words[0] == 'next'):
            debug_print("Address Group object end: %s" % (cur_addr_grp.name))
            cur_tenant.add_address_group(cur_addr_grp, input_line_num)
            cur_addr_grp = None
        elif (words[0] == 'set'):
            if (words[1] == 'member'):
                for ix in range(2, len(words)):
                    cur_nm = ""
                    for i in range(2, len(words)):
                        if (not cur_nm == ""):
                            cur_nm = cur_nm + '_' + words[i]
                        else:
                            cur_nm = words[i]
                        if (not cur_nm.endswith('"')):
                            continue
                        cur_nm = cur_nm.replace('"', '')
                        if (len(cur_nm) > 31):
                            cur_nm = words[i]
                            cur_nm = cur_nm.replace('"', '')
                        if (cur_nm.lower() != 'all'):
                            cur_addr_grp.add_address(cur_nm, input_line_num)
                            debug_print("Adding Address %s to Address Group %s" % (cur_nm, cur_addr_grp.name))
                            cur_nm = ""
    elif (cfg_state == ConfigState.SCHEDULE):
        if (words[0] == 'edit'):
            cur_schedule = Schedule(words[1].replace('"', ''),
                                    input_line_num, False,
                                    cur_schedule_is_recurring)
            debug_print("Schedule object start: %s" %
                        (cur_schedule.name))
        elif (words[0] == 'next'):
            debug_print("Schedule object end: %s" % (cur_schedule.name))
            cur_tenant.add_schedule(cur_schedule, input_line_num)
            cur_schedule = None
        elif (words[0] == 'set'):
            if (words[1] == 'day'):
                for ix in range(2, len(words)):
                    cur_schedule.add_recurring_day_time(
                                         words[ix].replace('"', ''),
                                         "",
                                         input_line_num)
    elif (cfg_state == ConfigState.SERVICE):
        if (words[0] == 'edit'):
            svc_nm = words[1]
            for ix in range(2, len(words)):
                svc_nm = svc_nm + '_' + words[ix]
            if (len(svc_nm) > 31):
                svc_nm = words[len(words) - 1]
            svc_nm = svc_nm.replace('"', '')
            cur_svc = Service(svc_nm, input_line_num, False)
            debug_print("Service object start: %s" %
                        (cur_svc.name))
        elif (words[0] == 'next'):
            debug_print("Service object end: %s" % (cur_svc.name))
            cur_tenant.add_service(cur_svc, input_line_num)
            cur_svc = None
        elif (words[0] == 'set'):
            if (words[1] == 'protocol'):
                cur_svc.set_proto(words[2], input_line_num)
            elif (words[1] == 'protocol-number'):
                cur_svc.set_proto_value(words[2], input_line_num)
            elif (words[1] == 'tcp-portrange'):
                if (cur_svc.proto == 'UDP'):
                    cur_svc.set_proto('TCP_OR_UDP', input_line_num)
                else:
                    cur_svc.set_proto('TCP', input_line_num)
                port_ranges = words[2]
                for ix in range(3, len(words)):
                    port_ranges = port_ranges + ',' + words[ix]
                cur_svc.set_port(port_ranges, input_line_num)
            elif (words[1] == 'udp-portrange'):
                if (cur_svc.proto == 'TCP'):
                    cur_svc.set_proto('TCP_OR_UDP', input_line_num)
                else:
                    cur_svc.set_proto('UDP', input_line_num)
                port_ranges = words[2]
                for ix in range(3, len(words)):
                    port_ranges = port_ranges + ',' + words[ix]
                cur_svc.set_port(port_ranges, input_line_num)
    elif (cfg_state == ConfigState.SERVICE_GROUP):
        if (words[0] == 'edit'):
            svc_grp_nm = words[1]
            for ix in range(2, len(words)):
                svc_grp_nm = svc_grp_nm + '_' + words[ix]
            cur_svc_grp = ServiceGroup(svc_grp_nm.replace('"', ''),
                                       input_line_num, False)
            debug_print("Service Group object start: %s" %
                        (cur_svc_grp.name))
        elif (words[0] == 'next'):
            debug_print("Service Group object end: %s" % (cur_svc_grp.name))
            cur_tenant.add_service_group(cur_svc_grp, input_line_num)
            cur_svc_grp = None
        elif (words[0] == 'set'):
            if (words[1] == 'member'):
                cur_nm = ""
                for i in range(2, len(words)):
                    if (not cur_nm == ""):
                        cur_nm = cur_nm + '_' + words[i]
                    else:
                        cur_nm = words[i]
                    if (not cur_nm.endswith('"')):
                        continue
                    cur_nm = cur_nm.replace('"', '')
                    if (len(cur_nm) > 31):
                        cur_nm = words[i]
                        cur_nm = cur_nm.replace('"', '')
                    if (cur_nm.lower() != 'all'):
                        cur_svc_grp.add_service(cur_nm, input_line_num)
                        debug_print("Adding Service %s to Service Group %s" % (cur_nm, cur_svc_grp.name))
                    cur_nm = ""
    elif (cfg_state == ConfigState.NAT_POOL):
        if (words[0] == 'edit'):
            np_nm = words[1]
            for ix in range(2, len(words)):
                np_nm = np_nm + '_' + words[ix]
            if (len(np_nm) > 31):
                np_nm = words[len(words) - 1]
            np_nm = np_nm.replace('"', '')
            cur_natpool = NATPool(np_nm, input_line_num, False)
            debug_print("NAT Pool object start: %s" %
                        (cur_natpool.name))
        elif (words[0] == 'next'):
            if (cur_natpool is not None):
                debug_print("NAT Pool object end: %s" % (cur_natpool.name))
                cur_tenant.add_natpool(cur_natpool, input_line_num)
            cur_natpool = None
        elif (words[0] == 'set'):
            if (words[1] == 'startip'):
                cur_natpool.set_start_ip(words[2], input_line_num)
            elif (words[1] == 'endip'):
                cur_natpool.set_end_ip(words[2], input_line_num)

    # Jump to the next config block
    if (words[0] != 'config'):
        if (cfg_depth == 1 and words[0] == 'edit' and len(words) > 1 and cfg_vdom):
            cur_vdom = words[1]
        continue

    # check/set whether config is for global or for vdom
    if (cfg_depth == 0):
        if (words[1] == 'global'):
            cfg_global = True
        elif (words[1] == 'vdom'):
            cfg_vdom = True
    cfg_depth = cfg_depth + 1

    # Check for firewall policy rule
    if (words[1] == 'firewall'):
        if (words[2] == 'policy'):
            cfg_state = ConfigState.POLICY
            cur_ngfw = NextGenFirewall(cur_tenant.name + '_policy',
                                       input_line_num, False)
            debug_print("Next gen firewall start: %s" % (cur_ngfw.name))
        elif (words[2] == 'address'):
            cfg_state = ConfigState.ADDRESS
            cur_addr = None
            debug_print("Address object definitions start")
        elif (words[2] == 'addrgrp'):
            cfg_state = ConfigState.ADDRESS_GROUP
            cur_addr_grp = None
            debug_print("Address Group object definitions start")
        elif (words[2] == 'schedule'):
            cfg_state = ConfigState.SCHEDULE
            cur_schedule = None
            if (len(words) > 3 and words[3] == 'recurring'):
                cur_schedule_is_recurring = True
            else:
                cur_schedule_is_recurring = False
            debug_print("Schedule object definitions start")
        elif (words[2] == 'service' and words[3] == 'custom'):
            cfg_state = ConfigState.SERVICE
            cur_svc = None
            debug_print("Service object definitions start")
        elif (words[2] == 'service' and words[3] == 'group'):
            cfg_state = ConfigState.SERVICE_GROUP
            cur_svc_grp = None
            debug_print("Service Group object definitions start")
        elif (words[2] == 'ippool'):
            cfg_state = ConfigState.NAT_POOL
            cur_natpool = None
            debug_print("NAT Pool object definitions start")

    # check config keyword and switch to appropriate config processing
    elif (words[1] == 'vdom'):
        # Translate config for vdom
        debug_print("Processing vdom config (depth = %d) ..." % (cfg_depth))
        # translate_vdom_cfg(in_fh)
    # else:
        # Unsupported config keyword
        # debug_print("Config translation unsupported for %s (depth = %d)" %
        #             (words[1], cfg_depth))



versa_cfg.replace_address_by_address_group()
versa_cfg.replace_service_group_by_service_members()
versa_cfg.check_config(strict_checks)
versa_cfg.write_config(tnt_xlate_map, c_options.template,
                       c_options.device, out_fh, log_fh)


out_fh.close()
csv_out_fh.close()
log_fh.close()
in_fh.close()












