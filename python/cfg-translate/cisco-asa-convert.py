#! /usr/bin/python
#
#  cisco-asa-convert.py - Convert Ciscos ASA config to Versa config
# 
#  This file has the code to translate Cisco ASA config to Versa config
# 
#  Copyright (c) 2017, Versa Networks, Inc.
#  All rights reserved.
#


from __future__ import print_function
from optparse import OptionParser
import subprocess,traceback,sys,os,re
import string
import csv, logging
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
    INTERFACE = 1
    DNS = 2
    POLICY = 3
    ADDRESS = 4
    ADDRESS_GROUP = 5
    SCHEDULE = 6
    SERVICE = 7
    SERVICE_GROUP = 8
    ROUTER = 9
    AAA_SERVER = 10
    LDAP = 11
    CRYPTO = 12
    GROUP_POLICY = 13
    WEB_VPN = 14
    DYNAMIC_ACCESS_POLICY_RECORD = 15
    USERNAME = 16
    TUNNEL_GROUP = 17
    CLASS_MAP = 18
    POLICY_MAP = 19
    CALL_HOME = 20



strict_checks = False
# strict_checks = True


debug_enable = False
debug_enable = True

input_line_num = 0
cfg_state = ConfigState.NONE
cfg_global = False
cfg_vdom = False
cur_vdom = ''
intf_zone_map = { }

cur_tenant = None
cur_addr = None
cur_addr_grp = None
cur_schedule = None
cur_schedule_is_recurring = False
cur_svc = None
cur_svc_grp = None
cur_ngfw = None
cur_ngfw_rule = None
cur_asa_ngfw_rule = None
cur_asa_ngfw_rule_desc = ''
cur_ngfw_rule_has_error = False
cur_rule_num = 0
tnt_xlate_map = { }
LOG_FILENAME = 'versa-cfg-translate.log'
v_logger = None

versa_cfg = VersaConfig('VersaCfg_From_Cisco_ASA')
asa_rules = [ ]
asa_rule_map = { }
asa_rule_intf_map = { }

asa_zone_intf_map = { }
asa_intf_zone_map = { }
ifname = ''
ifzone = ''
cur_addr_obj_name = ''
cur_svc_name = ''
cur_svc_grp_name = ''
cur_svc_grp_proto = ''
cur_svc_grp_member_cnt = 0
cur_addr_grp_name = ''
cur_addr_grp_member_cnt = 0



service_map = {

    'smtp'    : [ 'TCP', '25'        ],
    'https'   : [ 'TCP', '443'       ],
    'isakmp'  : [ 'UDP', '500,4500'  ],
    'ldap'    : [ 'TCP', '389'       ],
    'ldaps'   : [ 'TCP', '636'       ],
    'ssh'     : [ 'TCP', '22'        ],
    'www'     : [ 'TCP', '80'        ]

}


def debug_print(s):
    if (debug_enable):
        print("%s" % (s))
    return




def process_line_in_none_state(_l, _words):
    global cfg_state
    global versa_cfg
    global v_logger
    global input_line_num
    global ifname
    global cur_addr
    global cur_svc
    global cur_svc_grp
    global cur_addr_obj_name
    global cur_svc_name
    global cur_svc_grp_name
    global cur_svc_grp_proto
    global cur_svc_grp_member_cnt
    global cur_addr_grp_name
    global cur_addr_grp_member_cnt
    global cur_addr_grp
    global cur_asa_ngfw_rule
    global cur_asa_ngfw_rule_desc
    global cur_asa_ngfw_rule_desc_line


    # Reset the various state variables
    cfg_state = ConfigState.NONE
    ifname = ''
    cur_addr_obj_name = ''
    cur_svc_name = ''
    cur_svc_grp_name = ''
    cur_svc_grp_proto = ''
    cur_addr_grp_name = ''
    cur_addr = None
    cur_addr_grp = None
    cur_svc_grp = None
    cur_svc_grp_member_cnt = 0
    cur_addr_grp_member_cnt = 0

    if (_l[0] == '!'):
        return

    # Hostname
    elif (_words[0] == 'hostname'):
        v_logger.info("%d: setting hostname to %s" % \
                      ( input_line_num, words[1] ))
        debug_print("%d: setting hostname to %s" % \
                    ( input_line_num, words[1] ))
        hostname = _words[1]
        versa_cfg.get_system().set_hostname(hostname, input_line_num)
    elif (_words[0] == 'no' and _words[1] == 'names'):
        v_logger.info("%d: ignoring 'no names' command - supported by " \
                      "Versa Analytics" % ( input_line_num ))
    elif (_words[0] == 'name'):
        v_logger.info("%d: ignoring 'name' command - supported by " \
                      "Versa Analytics" % ( input_line_num ))
    elif (_words[0] == 'no' and _words[1] == 'mac-address'):
        v_logger.info("%d: ignoring 'no mac-address' command - " \
                      "supported by HA configuration" % ( input_line_num ))
    elif (_words[0] == 'mac-address'):
        v_logger.info("%d: ignoring 'mac-address' command - supported by " \
                      "HA configuration" % ( input_line_num ))
    elif (_words[0] == 'interface'):
        v_logger.info("%d: configuration start for interface %s" % \
                      ( input_line_num, ifname ))
        debug_print("%d: configuration start for interface %s" % \
                    ( input_line_num, ifname ))
        cfg_state = ConfigState.INTERFACE
        ifname = _words[1]
        ifzone = ''
    elif ((_words[0] == 'boot') or
          (_words[0] == 'ftp') or
          (_words[0] == 'pager') or
          (_words[0] == 'logging') or
          (_words[0] == 'no' and _words[1] == 'logging') or
          (_words[0] == 'flow-export') or
          (_words[0] == 'mtu') or
          (_words[0] == 'failover') or
          (_words[0] == 'monitor-interface') or
          (_words[0] == 'no' and _words[1] == 'monitor-interface') or
          (_words[0] == 'asdm') or
          (_words[0] == 'no' and _words[1] == 'asdm') or
          (_words[0] == 'icmp') or
          (_words[0] == 'arp') or
          (_words[0] == 'no' and _words[1] == 'arp') or
          (_words[0] == 'ip' and _words[1] == 'local') or
          (_words[0] == 'nat') or
          (_words[0] == 'xlate') or
          (_words[0] == 'threat-detection') or
          (_words[0] == 'aaa') or
          (_words[0] == 'http') or
          (_words[0] == 'http') or
          (_words[0] == 'snmp-server') or
          (_words[0] == 'user-identity') or
          (_words[0] == 'route') or
          (_words[0] == 'timeout') or
          (_words[0] == 'sysopt') or
          (_words[0] == 'service') or
          (_words[0] == 'ssh') or
          (_words[0] == 'ssl') or
          (_words[0] == 'no' and _words[1] == 'ssh') or
          (_words[0] == 'telnet') or
          (_words[0] == 'console') or
          (_words[0] == 'ntp') or
          (_words[0] == 'service-policy') or
          (_words[0] == 'prompt') or
          (_words[0] == 'no' and _words[1] == 'call-home') or
          (_words[0] == 'management-access') or
          (_words[0] == 'dhcpd') or
          (_words[0] == 'dhcprelay') or
          (_words[0] == 'domain-name') or
          (_words[0] == 'same-security-traffic') or
          (_words[0] == 'passwd') or
          (_words[0] == 'enable' and _words[1] == 'password') or
          (_words[0] == 'clock') or
          (_words[0] == 'dns-guard' and len(_words) == 1)):
        v_logger.info("%d: ignoring config line : '%s'" % \
                      ( input_line_num, l ))
    elif (_words[0] == 'dns'):
        v_logger.info("%d: configuration start for dns" % \
                      ( input_line_num ))
        debug_print("%d: configuration start for dns" % \
                    ( input_line_num ))
        if ((_words[1] == 'domain-lookup') or
            (_words[1] == 'server-group')):
            v_logger.info("%s: ignoring config line : '%s'" % \
                          ( input_line_num, l ))
        cfg_state = ConfigState.DNS
    elif (_words[0] == 'object' and _words[1] == 'network'):
        v_logger.info("%d: configuration start for address %s" % \
                      ( input_line_num, words[2] ))
        debug_print("%d: configuration start for address %s" %
                    ( input_line_num, words[2] ))
        cfg_state = ConfigState.ADDRESS
        cur_addr_obj_name = _words[2]
        cur_addr = Address(cur_addr_obj_name, input_line_num, False)
    elif (_words[0] == 'object' and _words[1] == 'service'):
        v_logger.info("%d: configuration start for service %s" % \
                      ( input_line_num, words[2] ))
        debug_print("%d: configuration start for service %s" %
                    ( input_line_num, words[2] ))
        cfg_state = ConfigState.SERVICE
        cur_svc_name = _words[2]
        cur_svc = Service(cur_svc_name, input_line_num, False)
    elif (_words[0] == 'object-group' and \
          (_words[1] == 'service' or _words[1] == 'protocol')):
        v_logger.info("%d: configuration start for service group %s" % \
                      ( input_line_num, words[2] ))
        debug_print("%d: configuration start for service group %s" %
                    ( input_line_num, words[2] ))
        cfg_state = ConfigState.SERVICE_GROUP
        cur_svc_grp_member_cnt = 0
        cur_svc_grp_name = _words[2]
        if (len(words) > 3):
            cur_svc_grp_proto = _words[3] 
        cur_svc_grp = ServiceGroup(cur_svc_grp_name, input_line_num, False)
    elif (_words[0] == 'object-group' and _words[1] == 'network'):
        v_logger.info("%d: configuration start for address group %s" % \
                      ( input_line_num, words[2] ))
        debug_print("%d: configuration start for address group %s" %
                    ( input_line_num, words[2] ))
        cfg_state = ConfigState.ADDRESS_GROUP
        cur_addr_grp_member_cnt = 0
        cur_addr_grp_name = _words[2]
        cur_addr_grp = AddressGroup(cur_addr_grp_name, input_line_num, False)
    elif (_words[0] == 'access-list' and words[2] == 'extended'):
        process_firewall_rule(l, words)
    elif (_words[0] == 'access-list' and words[2] == 'remark'):
        ix = l.index('remark')
        cur_asa_ngfw_rule_desc = '"%s"' % l[ix + 7:]
        cur_asa_ngfw_rule_desc_line = input_line_num
    elif (_words[0] == 'access-list' and words[2] == 'standard'):
        v_logger.info("%d: ignoring standard ACL '%s'" % \
                      ( input_line_num, l ))
    elif (_words[0] == 'router'):
        v_logger.info("%d: configuration start for router" % \
                      ( input_line_num ))
        debug_print("%d: configuration start for router" % \
                    ( input_line_num ))
        cfg_state = ConfigState.ROUTER
    elif (_words[0] == 'aaa-server'):
        v_logger.info("%d: configuration start for aaa-server" % \
                      ( input_line_num ))
        debug_print("%d: configuration start for aaa-server" % \
                    ( input_line_num ))
        cfg_state = ConfigState.AAA_SERVER
    elif (_words[0] == 'ldap'):
        v_logger.info("%d: configuration start for ldap" % \
                      ( input_line_num ))
        debug_print("%d: configuration start for ldap" % \
                    ( input_line_num ))
        cfg_state = ConfigState.LDAP
    elif ((_words[0] == 'crypto') and
          (_words[1] == 'ca' or \
           _words[1] == 'ikev1' or \
           _words[1] == 'ikev2' or \
           _words[2] == 'ikev2')):
        v_logger.info("%d: configuration start for crypto" % \
                      ( input_line_num ))
        debug_print("%d: configuration start for crypto" % \
                    ( input_line_num ))
        cfg_state = ConfigState.CRYPTO
    elif (_words[0] == 'crypto'):
        v_logger.info("%d: ignoring config line : '%s'" % \
                      ( input_line_num, l ))
    elif (_words[0] == 'group-policy'):
        v_logger.info("%d: configuration start for group-policy" % \
                      ( input_line_num ))
        debug_print("%d: configuration start for group-policy" % \
                    ( input_line_num ))
        cfg_state = ConfigState.GROUP_POLICY
    elif (_words[0] == 'webvpn'):
        v_logger.info("%d: configuration start for webvpn" % \
                      ( input_line_num ))
        debug_print("%d: configuration start for webvpn" % \
                    ( input_line_num ))
        cfg_state = ConfigState.WEB_VPN
    elif (_words[0] == 'dynamic-access-policy-record'):
        v_logger.info("%d: configuration start for " \
                      "dynamic-access-policy-record" % \
                      ( input_line_num ))
        debug_print("%d: configuration start for " \
                      "dynamic-access-policy-record" % \
                    ( input_line_num ))
        cfg_state = ConfigState.DYNAMIC_ACCESS_POLICY_RECORD
    elif (_words[0] == 'username'):
        v_logger.info("%d: configuration start for " \
                      "username" % \
                      ( input_line_num ))
        debug_print("%d: configuration start for " \
                      "username" % \
                    ( input_line_num ))
        cfg_state = ConfigState.USERNAME
    elif (_words[0] == 'tunnel-group'):
        v_logger.info("%d: configuration start for " \
                      "tunnel-group" % \
                      ( input_line_num ))
        debug_print("%d: configuration start for " \
                      "tunnel-group" % \
                    ( input_line_num ))
        cfg_state = ConfigState.TUNNEL_GROUP
    elif (_words[0] == 'class-map'):
        v_logger.info("%d: configuration start for " \
                      "class-map" % \
                      ( input_line_num ))
        debug_print("%d: configuration start for " \
                      "class-map" % \
                    ( input_line_num ))
        cfg_state = ConfigState.CLASS_MAP
    elif (_words[0] == 'policy-map'):
        v_logger.info("%d: configuration start for " \
                      "policy-map" % \
                      ( input_line_num ))
        debug_print("%d: configuration start for " \
                      "policy-map" % \
                    ( input_line_num ))
        cfg_state = ConfigState.POLICY_MAP
    elif (_words[0] == 'call-home'):
        v_logger.info("%d: configuration start for " \
                      "call-home" % \
                      ( input_line_num ))
        debug_print("%d: configuration start for " \
                      "call-home" % \
                    ( input_line_num ))
        cfg_state = ConfigState.CALL_HOME
    elif (_words[0] == 'access-group'):
        acl_name = words[1]
        direction = words[2]
        intf = words[4]
        asa_rule_intf_map[acl_name] = [ direction, intf, input_line_num ]
        v_logger.info("%d: added interface %s direction %s for acl %s" % \
                      ( input_line_num, intf, direction, acl_name ))
        debug_print("%d: added interface %s direction %s for acl %s" % \
                    ( input_line_num, intf, direction, acl_name ))
    else:
        v_logger.error("%d: config line not translated: '%s'" % \
                       ( input_line_num, l ))
    return




def set_service_info(_cur_svc, _words, _ix, _set_src, _proto):
    global input_line_num
    global service_map


    if (_words[_ix] == 'eq'):
        svc_nm = _words[_ix + 1]
        if (svc_nm in service_map):
            proto = service_map[svc_nm][0]
            ports = service_map[svc_nm][1]
        else:
            proto = _proto
            ports = svc_nm
        if (_set_src):
            _cur_svc.set_proto(proto, input_line_num)
            _cur_svc.set_src_port(ports, input_line_num)
            v_logger.info("%d: service %s has proto %s and " \
                          "source port %s" % \
                          ( input_line_num, _cur_svc.name, proto, ports))
            debug_print("%d: service %s has proto %s and " \
                        "source port %s" % \
                        ( input_line_num, _cur_svc.name, proto, ports))
        else:
            _cur_svc.set_proto(proto, input_line_num)
            _cur_svc.set_port(ports, input_line_num)
            v_logger.info("%d: service %s has proto %s and " \
                          "dest port %s" % \
                          ( input_line_num, _cur_svc.name, proto, ports))
            debug_print("%d: service %s has proto %s and " \
                        "dest port %s" % \
                        ( input_line_num, _cur_svc.name, proto, ports))
    elif (_words[_ix] == 'range'):
        start_port = _words[_ix + 1]
        end_port = _words[_ix + 2]
        proto = _proto
        ports = '%s-%s' % (start_port, end_port)
        _cur_svc.set_proto(proto, input_line_num)
        _cur_svc.set_port(ports, input_line_num)
        v_logger.info("%d: service %s has proto %s and " \
                      "source port %s" % \
                      ( input_line_num, _cur_svc.name, proto, ports))
        debug_print("%d: service %s has proto %s and " \
                    "dest port %s" % \
                    ( input_line_num, _cur_svc.name, proto, ports))
    return




def set_address_info(_cur_addr, _words, _ix):
    global input_line_num
    global service_map

    if (_words[_ix] == 'host'):
        ip_addr = _words[_ix + 1]
        mask = '255.255.255.255'
        int_mask = 0xffffffff
        mask_len = 32
        v_logger.info("%d: address %s; IP prefix: %s %s 0x%x %d" %
                      ( input_line_num, _cur_addr.name, \
                        ip_addr, mask, int_mask, mask_len))
        debug_print("%d: address %s; IP prefix: %s %s 0x%x %d" %
                    ( input_line_num, _cur_addr.name, \
                        ip_addr, mask, int_mask, mask_len))
        _cur_addr.set_addr_type(AddressType.IP_V4_PREFIX,
                               input_line_num)
        _cur_addr.set_addr_value(ip_addr + '/' + str(mask_len),
                                input_line_num)
        v_logger.info("%d: Adding Address %s to current tenant" % \
                      (input_line_num, _cur_addr.name))
        debug_print("%d: Adding Address %s to current tenant" % \
                    (input_line_num, _cur_addr.name))
        cur_tenant.add_address(_cur_addr, input_line_num)
    elif (_words[_ix] == 'range'):
        _cur_addr.set_addr_type(AddressType.IP_V4_RANGE,
                               input_line_num)
        _cur_addr.set_start_ip(_words[_ix + 1], input_line_num)
        v_logger.info("%d: address %s; IP range: %s %s " %
                      ( input_line_num, _cur_addr.name, \
                        _words[_ix + 1], _words[_ix + 2]))
        debug_print("%d: address %s; IP range: %s %s " %
                    ( input_line_num, _cur_addr.name, \
                      _words[_ix + 1], _words[_ix + 2]))

        st_ip = _cur_addr.start_ip.split('.')
        end_ip = _words[_ix + 2].split('.')
        if (st_ip[0] != end_ip[0]):
            raise Exception('Line %d: start/end IP address should ' \
                            'belong to same /8 prefix' % ' \
                            '( input_line_num ) )
        elif (st_ip[1] != end_ip[1]):
            v_logger.info("%d: Address object %s: adding multiple " \
                          "address objects for range %s.%d - %s.%d" % \
                          ( input_line_num, _cur_addr.name, st_ip[0], \
                            int(st_ip[1]), st_ip[0], int(end_ip[1])))
            debug_print("%d: Address object %s: adding multiple " \
                        "address objects for range %s.%d - %s.%d" % \
                        ( input_line_num, _cur_addr.name, st_ip[0], \
                          int(st_ip[1]), st_ip[0], int(end_ip[1])))
            addr_grp = AddressGroup(_cur_addr.name,
                                    _cur_addr.name_src_line, False)
            for ix in range(int(st_ip[1]), int(end_ip[1]) + 1):
                addr = Address(_cur_addr.name + '-' + str(ix),
                               _cur_addr.name_src_line, False)
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
                v_logger.info("%d: Adding address object %s " \
                              "to tenant %s and address group %s" % \
                              (input_line_num, addr.name, cur_tenant.name, \
                               addr_grp.name))
                debug_print("%d: Adding address object %s " \
                            "to tenant %s and address group %s" % \
                            (input_line_num, addr.name, cur_tenant.name, \
                             addr_grp.name))
                cur_tenant.add_address(addr, input_line_num)
                addr_grp.add_address(addr.name, input_line_num)
            cur_tenant.add_address_group(addr_grp, input_line_num)
        else:
            _cur_addr.set_end_ip(_words[_ix + 2], input_line_num)
            v_logger.info("%d: Adding Address %s to current tenant" % \
                          (input_line_num, _cur_addr.name))
            debug_print("%d: Adding Address %s to current tenant" % \
                        (input_line_num, _cur_addr.name))
            cur_tenant.add_address(_cur_addr, input_line_num)
    elif (_words[_ix] == 'fqdn'):
        fqdn = _words[_ix + 2]
        v_logger.info("%d: address %s; FQDN: %s" %
                      ( input_line_num, _cur_addr.name, fqdn))
        debug_print("%d: address %s; FQDN: %s" %
                    ( input_line_num, _cur_addr.name, fqdn))
        _cur_addr.set_addr_type(AddressType.FQDN,
                               input_line_num)
        _cur_addr.set_addr_value(fqdn, input_line_num)
        v_logger.info("%d: Adding Address %s to current tenant" % \
                      (input_line_num, _cur_addr.name))
        debug_print("%d: Adding Address %s to current tenant" % \
                    (input_line_num, _cur_addr.name))
        cur_tenant.add_address(_cur_addr, input_line_num)
    elif (_words[_ix] == 'description'):
        desc = l.strip()
        desc = desc[11:]
        desc = desc.replace('"', '')
        desc = desc.strip()
        _cur_addr.set_description(desc, input_line_num)
    else:
        if (_words[_ix] == 'subnet'):
            _ix = _ix + 1

        _cur_addr.set_addr_type(AddressType.IP_V4_PREFIX,
                               input_line_num)
        ip_addr = _words[_ix]
        mask = _words[_ix + 1]
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
        v_logger.info("%d: address %s; IP prefix: %s %s 0x%x %d" %
                      ( input_line_num, _cur_addr.name, \
                        ip_addr, mask, int_mask, mask_len))
        debug_print("%d: address %s; IP prefix: %s %s 0x%x %d" %
                    ( input_line_num, _cur_addr.name, \
                      ip_addr, mask, int_mask, mask_len))
        _cur_addr.set_addr_value(ip_addr + '/' + str(mask_len),
                                input_line_num)
        v_logger.info("%d: Adding Address %s to current tenant" % \
                      (input_line_num, _cur_addr.name))
        debug_print("%d: Adding Address %s to current tenant" % \
                    (input_line_num, _cur_addr.name))
        cur_tenant.add_address(_cur_addr, input_line_num)
    return




def process_firewall_rule(_l, _words):
    global v_logger
    global input_line_num
    global cur_asa_ngfw_rule
    global cur_asa_ngfw_rule_desc
    global cur_asa_ngfw_rule_desc_line

    asa_rname = _words[1]
    rnum = 1
    if (asa_rname in asa_rule_map.keys()):
        rnum = len(asa_rule_map[asa_rname]) + 1

    # Make a new nextgen firewall rule for the current policy
    rname = '%s_%d' % ( asa_rname, rnum)
    v_logger.info("%d: configuration start for access policy %s" % \
                  ( input_line_num, rname ))
    debug_print("%d: configuration start for access policy %s" %
                ( input_line_num, rname ))
    cfg_state = ConfigState.POLICY
    cur_asa_ngfw_rule = NextGenFirewallRule(rname,
                                            input_line_num, False)
    cur_asa_ngfw_rule.set_tenant(cur_tenant)

    # Set the rule action
    action = words[3]
    if (action == 'permit'):
        cur_asa_ngfw_rule.set_action(FirewallRuleAction.ALLOW,
                                     input_line_num)
        v_logger.info("%d: set action 'allow' for ACL %s " % \
                      ( input_line_num, rname ))
        debug_print("%d: set action 'allow' for ACL %s " % \
                    ( input_line_num, rname ))
    elif (action == 'deny'):
        cur_asa_ngfw_rule.set_action(FirewallRuleAction.DENY,
                                     input_line_num)
        v_logger.info("%d: set action 'deny' for ACL %s " % \
                      ( input_line_num, rname ))
        debug_print("%d: set action 'deny' for ACL %s " % \
                    ( input_line_num, rname ))
    else:
        v_logger.error("%d: Error - unknown action %s for ACL %s " % \
                      ( input_line_num, action, rname ))
        debug_print("%d: Error - unknown action %s for ACL %s " % \
                    ( input_line_num, action, rname ))
        return

    src_addr_ix = 4
    proto = words[4]
    if (proto == 'ip' or proto == 'tcp' or proto == 'udp' or proto == 'icmp'):
        src_addr_ix = 5
    else:
        try:
            proto_num = int(proto)
            tmp_line = cur_asa_ngfw_rule.name_src_line
            cur_svc = Service('proto_%d' % proto_num, tmp_line, False)
            cur_svc.set_proto_value(proto_num, tmp_line)
            v_logger.info("%d: Adding Service %s to " \
                          "current tenant" % \
                          (input_line_num, cur_svc.name))
            debug_print("%d: Adding Service %s to current " \
                        "tenant" % \
                        (input_line_num, cur_svc.name))
            cur_tenant.add_service(cur_svc, input_line_num)
            v_logger.info("%d: Setting Service to %s for ACL %s" % \
                          (input_line_num, cur_svc.name, \
                           cur_asa_ngfw_rule.name))
            debug_print("%d: Setting Service to %s for ACL %s" % \
                        (input_line_num, cur_svc.name, cur_asa_ngfw_rule.name))
            cur_asa_ngfw_rule.add_service(cur_svc, input_line_num)
            src_addr_ix = 5
        except:
            pass

    # Set the source address
    src_addr = words[src_addr_ix]
    dst_addr_ix = src_addr_ix + 1
    if (src_addr == 'any'):
        cur_asa_ngfw_rule.add_src_addr(src_addr, input_line_num)
        v_logger.info("%d: set src address %s for ACL %s " % \
                     ( input_line_num, 'any', rname ))
        debug_print("%d: set src address %s for ACL %s " % \
                    ( input_line_num, 'any', rname ))
    elif (src_addr == 'any4'):
        cur_asa_ngfw_rule.add_src_addr(src_addr, input_line_num)
        v_logger.info("%d: set src address %s for ACL %s " % \
                     ( input_line_num, src_addr, rname ))
        debug_print("%d: set src address %s for ACL %s " % \
                    ( input_line_num, src_addr, rname ))
    elif (src_addr == 'object-group'):
        src_addr_grp = words[src_addr_ix + 1]
        cur_asa_ngfw_rule.add_src_addr_grp(src_addr_grp, input_line_num)
        v_logger.info("%d: set src address group %s for ACL %s " % \
                     ( input_line_num, src_addr_grp, rname ))
        debug_print("%d: set src address group %s for ACL %s " % \
                    ( input_line_num, src_addr_grp, rname ))
        dst_addr_ix = src_addr_ix + 2
    elif (src_addr == 'object'):
        src_addr = words[src_addr_ix + 1]
        cur_asa_ngfw_rule.add_src_addr(src_addr, input_line_num)
        v_logger.info("%d: set src address %s for ACL %s " % \
                      ( input_line_num, src_addr, rname ))
        debug_print("%d: set src address %s for ACL %s " % \
                    ( input_line_num, src_addr, rname ))
        dst_addr_ix = src_addr_ix + 2
    else:
        cur_addr = Address('%s_src_addr' % rname, input_line_num, False)
        set_address_info(cur_addr, words, src_addr_ix)
        cur_asa_ngfw_rule.add_src_addr(cur_addr.name, input_line_num)
        v_logger.info("%d: set src address %s for ACL %s " % \
                      ( input_line_num, cur_addr.name, rname ))
        debug_print("%d: set src address %s for ACL %s " % \
                    ( input_line_num, cur_addr.name, rname ))
        dst_addr_ix = src_addr_ix + 2

    # Set the destination address
    dst_addr = words[dst_addr_ix]
    next_word_ix = dst_addr_ix + 1
    if (dst_addr == 'any'):
        cur_asa_ngfw_rule.add_dst_addr(dst_addr, input_line_num)
        v_logger.info("%d: set dst address %s for ACL %s " % \
                      ( input_line_num, 'any', rname ))
        debug_print("%d: set dst address %s for ACL %s " % \
                    ( input_line_num, 'any', rname ))
    elif (dst_addr == 'any4'):
        cur_asa_ngfw_rule.add_dst_addr(dst_addr, input_line_num)
        v_logger.info("%d: set dst address %s for ACL %s " % \
                      ( input_line_num, dst_addr, rname ))
        debug_print("%d: set dst address %s for ACL %s " % \
                    ( input_line_num, dst_addr, rname ))
    elif (dst_addr == 'object-group'):
        dst_addr_grp = words[dst_addr_ix + 1]
        cur_asa_ngfw_rule.add_dst_addr_grp(dst_addr_grp, input_line_num)
        v_logger.info("%d: set dst address group %s for ACL %s " % \
                      ( input_line_num, dst_addr_grp, rname ))
        debug_print("%d: set dst address group %s for ACL %s " % \
                    ( input_line_num, dst_addr_grp, rname ))
        next_word_ix = dst_addr_ix + 2
    elif (dst_addr == 'object'):
        dst_addr = words[dst_addr_ix + 1]
        cur_asa_ngfw_rule.add_dst_addr(dst_addr, input_line_num)
        v_logger.info("%d: set dst address %s for ACL %s " % \
                      ( input_line_num, dst_addr, rname ))
        debug_print("%d: set dst address %s for ACL %s " % \
                    ( input_line_num, dst_addr, rname ))
        next_word_ix = dst_addr_ix + 2
    elif (dst_addr == 'interface'):
        dst_zone = words[dst_addr_ix + 1]
        cur_asa_ngfw_rule.add_dst_zone(dst_zone, input_line_num)
        v_logger.info("%d: set dst zone %s for ACL %s " % \
                      ( input_line_num, dst_zone, rname ))
        debug_print("%d: set dst zone %s for ACL %s " % \
                    ( input_line_num, dst_zone, rname ))
        next_word_ix = dst_addr_ix + 2
    else:
        cur_addr = Address('%s_dst_addr' % rname, input_line_num, False)
        set_address_info(cur_addr, words, dst_addr_ix)
        cur_asa_ngfw_rule.add_dst_addr(cur_addr.name, input_line_num)
        v_logger.info("%d: set dst address %s for ACL %s " % \
                      ( input_line_num, cur_addr.name, rname ))
        debug_print("%d: set dst address %s for ACL %s " % \
                    ( input_line_num, cur_addr.name, rname ))
        next_word_ix = dst_addr_ix + 2

    # Check if there is a service set for the rule
    if (next_word_ix < len(words)):
        # Check if its a standard service
        cur_svc = None
        if (words[next_word_ix] == 'object-group'):
            cur_svc_grp = _words[next_word_ix + 1]
            v_logger.info("%d: Setting Service Group to %s for ACL %s" % \
                          (input_line_num, \
                           cur_svc_grp, cur_asa_ngfw_rule.name))
            debug_print("%d: Setting Service Group to %s for ACL %s" % \
                        (input_line_num, cur_svc_grp, cur_asa_ngfw_rule.name))
            cur_asa_ngfw_rule.add_service(cur_svc_grp, input_line_num)
        else:
            if (words[next_word_ix] == 'eq'):
                svc_nm = _words[next_word_ix + 1]
                if (svc_nm in service_map):
                    tnt_svc_map = cur_tenant.get_service_map()
                    if (not svc_nm in tnt_svc_map.keys()):
                        tmp_line = cur_asa_ngfw_rule.name_src_line
                        cur_svc = Service(svc_nm, tmp_line, False)
                        set_service_info(cur_svc, words, \
                                         src_ix + 1, False, words[1])
                        v_logger.info("%d: Adding Service %s to " \
                                      "current tenant" % \
                                      (input_line_num, cur_svc.name))
                        debug_print("%d: Adding Service %s to current " \
                                    "tenant" % \
                                    (input_line_num, cur_svc.name))
                        cur_tenant.add_service(cur_svc, input_line_num)
                    else:
                        cur_svc = tnt_svc_map[svc_nm][0]

            if (cur_svc is None):
                tmp_line = cur_asa_ngfw_rule.name_src_line
                cur_svc = Service('%s_svc' % cur_asa_ngfw_rule.name, \
                                  tmp_line, False)
                set_service_info(cur_svc, words, src_ix + 1, False, words[1])
                v_logger.info("%d: Adding Service %s to current tenant" % \
                              (tmp_line, cur_svc.name))
                debug_print("%d: Adding Service %s to current tenant" % \
                            (tmp_line, cur_svc.name))
                cur_tenant.add_service(cur_svc, input_line_num)

            v_logger.info("%d: Setting Service to %s for ACL %s" % \
                          (input_line_num, \
                           cur_svc.name, cur_asa_ngfw_rule.name))
            debug_print("%d: Setting Service to %s for ACL %s" % \
                        (input_line_num, cur_svc.name, cur_asa_ngfw_rule.name))
            cur_asa_ngfw_rule.add_service(cur_svc, input_line_num)
    else:
        # Set the service
        proto = words[4]
        if (proto == 'ip' or proto == 'tcp' or \
            proto == 'udp' or proto == 'icmp'):
            cur_asa_ngfw_rule.add_service(proto, input_line_num)
            v_logger.info("%d: set service '%s' for ACL %s " % \
                          ( input_line_num, proto, rname ))
            debug_print("%d: set service '%s' for ACL %s " % \
                        ( input_line_num, proto, rname ))
        else:
            v_logger.info("%d: Error - unknown service %s for ACL %s " % \
                          ( input_line_num, proto, rname ))
            debug_print("%d: Error - unknown action %s for ACL %s " % \
                        ( input_line_num, proto, rname ))
            return


    # Add the current rule to the rule map
    if (len(cur_asa_ngfw_rule_desc) > 0):
        cur_asa_ngfw_rule.set_desc(cur_asa_ngfw_rule_desc,
                                   cur_asa_ngfw_rule_desc_line)
    if (asa_rname in asa_rule_map.keys()):
        asa_rule_map[asa_rname].append(cur_asa_ngfw_rule)
    else:
        asa_rule_map[asa_rname] = [ cur_asa_ngfw_rule ]

    # Rule config end
    cur_asa_ngfw_rule = None
    cur_asa_ngfw_rule_desc = ''
    cur_asa_ngfw_rule_desc_line = 0
    cfg_state = ConfigState.NONE
    v_logger.info("%d: configuration end for access policy %s" % \
                  ( input_line_num, rname ))
    debug_print("%d: configuration end for access policy %s" %
                ( input_line_num, rname ))
    return




# Get command line arguments
o_parser = OptionParser()
o_parser.add_option("-i", "--inputfile", dest="infile",
                    help="Path to Cisco ASA config file", metavar="infilepath")
o_parser.add_option("-z", "--zonefile", dest="zonefile",
                    help="Path to zone/interface CSV file", \
                    metavar="zonefilepath")
o_parser.add_option("-T", "--template", dest="template",
                    help="Template name", metavar="template")
o_parser.add_option("-D", "--device", dest="device",
                    help="Device name", metavar="device")
o_parser.add_option("-o", "--outputdir", dest="outdir",
                    help="Path to output directory", metavar="outdir")
o_parser.add_option("-v", "--versa-paths-file", dest="vpathsfile",
                    help="Path to Versa path segments file", \
                    metavar="vpathsfile")
(c_options, c_args) = o_parser.parse_args()



# Ensure that only one of device or template is specified if transation is
# to be done for versa director
if (c_options.template and c_options.device):
    print("To generate config that can be loaded into the Versa Director " + \
          "configuration, please specify either the Config Template name " + \
          "or the Device name for which config should be generated\n")
    exit(1)



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
    print("Please specify the input Cisco ASA config file, " + \
          "interface/zone CSV file and the output directory path\n")
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
    print("Please specify the input Cisco ASA config file, " + \
          "interface/zone CSV file and the output directory path\n")
    in_fh.close()
    exit(1)





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
    print("Please specify the input Cisco ASA config file, " + \
          "interface/zone CSV file and the output directory path\n")
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



# get the log file and create it
try:
    logging.basicConfig(filename='/dev/null', level=logging.DEBUG)
    logpath = os.path.join(c_options.outdir, LOG_FILENAME)
    formatter = logging.Formatter('[%(asctime)s] '
                                  '[%(levelname)s] %(message)s')
    fh = logging.FileHandler(logpath)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    v_logger = logging.getLogger(logpath)
    v_logger.addHandler(fh)
except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    print("Error: unable to create logger with " + logpath)
    print("Error Details:")
    print("    " + \
          repr(traceback.format_exception_only(exc_type, exc_value)))
    exit(1)




versa_cfg = VersaConfig('VersaCfg_From_Cisco_ASA_' + bname)



# populate the zone/interface map
asa_versa_intf_map = { }
for row in zone_csv:

    # ignore invalid rows
    if (row[0].startswith('#')):
        continue
    if (len(row) < 4):
        continue

    # Update interface zone map
    intf_zone_map[row[1]] = row[2:]

    asa_versa_intf_map[row[0]] = row[1]

    tnt =  row[3]
    if (not versa_cfg.has_tenant(tnt)):
        versa_cfg.add_tenant(tnt, '0')
        tnt_xlate_map[tnt] = [ tnt ]

zone_fh.close()
tnt_names = versa_cfg.get_tenants()
cur_tenant = versa_cfg.get_tenant(tnt_names[0], input_line_num)




print('# SerialNum,RuleName,SrcZone,SrcAddr,DstZone,DstAddr,' \
      'IP-Version,Services,Schedule,Action', file=csv_out_fh)


for ln in in_fh:

    # strip whitespace and update line number
    input_line_num = input_line_num + 1
    l = ln.rstrip()

    # skip comments
    if (len(l) == 0 or l.startswith(':')):
        continue

    # tokenize the config line
    words = l.split()
    if (len(words) <= 0):
        debug_print("Syntax error")
        break

    # Process the configuration depending on the state
    if (cfg_state == ConfigState.NONE):
        process_line_in_none_state(l, words)


    elif (cfg_state == ConfigState.INTERFACE):
        if (not l[0] == ' '):
            v_logger.info("%d: configuration end for interface %s" % \
                          ( input_line_num, ifname ))
            debug_print("%d: configuration end for interface %s" % \
                        ( input_line_num, ifname ))
            if (len(ifzone) > 0):
                if (ifname in asa_versa_intf_map):
                    v_ifname = asa_versa_intf_map[ifname]
                    asa_zone_intf_map[ifzone.lower()] = v_ifname
                    asa_intf_zone_map[v_ifname] = ifzone
                    versa_cfg.add_network_and_interface(
                                                     '%s-network' % ifzone, \
                                                     v_ifname)
                    v_logger.info("%d: adding versa interface %s " \
                                  "(asa interface %s)" % \
                                  ( input_line_num, v_ifname, ifname ))
                    cur_tenant.add_zone_interface(ifzone, \
                                                  v_ifname, input_line_num)
                else:
                    v_logger.info("%d: ignoring interface '%s' as interface " \
                                  "mapping was not found in zone/interface "
                                  "mapping file" % ( input_line_num, ifname ))
            else:
                v_logger.info("%d: ignoring interface '%s' as nameif " \
                              "not found" % ( input_line_num, ifname ))
            process_line_in_none_state(l, words)
        elif (words[0] == 'nameif'):
            ifzone = words[1]
        else:
            v_logger.debug("%d: ignoring interface config line: '%s'" % \
                           ( input_line_num, l ))


    elif (cfg_state == ConfigState.DNS):
        if (not (l[0] == ' ' or words[0] == 'dns')):
            process_line_in_none_state(l, words)
            v_logger.info("%d: configuration end for dns" % \
                          ( input_line_num ))
            debug_print("%d: configuration end for dns" % \
                        ( input_line_num ))
        elif (words[0] == 'name-server'):
            versa_cfg.get_system().add_name_server(words[1], input_line_num)
        elif (words[0] == 'domain-name'):
            versa_cfg.get_system().set_domain_search(words[1], input_line_num)
        else:
            v_logger.debug("%d: ignoring dns config line: '%s'" % \
                           ( input_line_num, l ))


    elif (cfg_state == ConfigState.ROUTER):
        if (not (l[0] == ' ')):
            v_logger.info("%d: configuration end for router" % \
                          ( input_line_num ))
            debug_print("%d: configuration end for router" % \
                        ( input_line_num ))
            cfg_state = ConfigState.NONE


    elif (cfg_state == ConfigState.AAA_SERVER):
        if (not (l[0] == ' ')):
            v_logger.info("%d: configuration end for aaa-server" % \
                          ( input_line_num ))
            debug_print("%d: configuration end for aaa-server" % \
                        ( input_line_num ))
            cfg_state = ConfigState.NONE
            if (not words[0] == '!'):
                process_line_in_none_state(l, words)


    elif (cfg_state == ConfigState.LDAP):
        if (not (l[0] == ' ')):
            v_logger.info("%d: configuration end for ldap" % \
                          ( input_line_num ))
            debug_print("%d: configuration end for ldap" % \
                        ( input_line_num ))
            cfg_state = ConfigState.NONE


    elif (cfg_state == ConfigState.CRYPTO):
        if (not (l[0] == ' ')):
            v_logger.info("%d: configuration end for crypto" % \
                          ( input_line_num ))
            debug_print("%d: configuration end for crypto" % \
                        ( input_line_num ))
            cfg_state = ConfigState.NONE
            if (not words[0] == '!'):
                process_line_in_none_state(l, words)


    elif (cfg_state == ConfigState.GROUP_POLICY):
        if (not (l[0] == ' ')):
            v_logger.info("%d: configuration end for group-policy" % \
                          ( input_line_num ))
            debug_print("%d: configuration end for group-policy" % \
                        ( input_line_num ))
            cfg_state = ConfigState.NONE
            if (not words[0] == '!'):
                process_line_in_none_state(l, words)


    elif (cfg_state == ConfigState.WEB_VPN):
        if (not (l[0] == ' ')):
            v_logger.info("%d: configuration end for webvpn" % \
                          ( input_line_num ))
            debug_print("%d: configuration end for webvpn" % \
                        ( input_line_num ))
            cfg_state = ConfigState.NONE
            if (not words[0] == '!'):
                process_line_in_none_state(l, words)


    elif (cfg_state == ConfigState.DYNAMIC_ACCESS_POLICY_RECORD):
        if (not (l[0] == ' ')):
            v_logger.info("%d: configuration end for " \
                          "dynamic-access-policy-record" % \
                          ( input_line_num ))
            debug_print("%d: configuration end for " \
                          "dynamic-access-policy-record" % \
                        ( input_line_num ))
            cfg_state = ConfigState.NONE
            if (not words[0] == '!'):
                process_line_in_none_state(l, words)


    elif (cfg_state == ConfigState.USERNAME):
        if (not (l[0] == ' ')):
            v_logger.info("%d: configuration end for " \
                          "username" % \
                          ( input_line_num ))
            debug_print("%d: configuration end for " \
                          "username" % \
                        ( input_line_num ))
            cfg_state = ConfigState.NONE
            if (not words[0] == '!'):
                process_line_in_none_state(l, words)


    elif (cfg_state == ConfigState.TUNNEL_GROUP):
        if (not (l[0] == ' ')):
            v_logger.info("%d: configuration end for " \
                          "tunnel-group" % \
                          ( input_line_num ))
            debug_print("%d: configuration end for " \
                          "tunnel-group" % \
                        ( input_line_num ))
            cfg_state = ConfigState.NONE
            if (not words[0] == '!'):
                process_line_in_none_state(l, words)


    elif (cfg_state == ConfigState.CLASS_MAP):
        if (not (l[0] == ' ')):
            v_logger.info("%d: configuration end for " \
                          "class-map" % \
                          ( input_line_num ))
            debug_print("%d: configuration end for " \
                          "class-map" % \
                        ( input_line_num ))
            cfg_state = ConfigState.NONE
            if (not words[0] == '!'):
                process_line_in_none_state(l, words)


    elif (cfg_state == ConfigState.POLICY_MAP):
        if (not (l[0] == ' ')):
            v_logger.info("%d: configuration end for " \
                          "policy-map" % \
                          ( input_line_num ))
            debug_print("%d: configuration end for " \
                          "policy-map" % \
                        ( input_line_num ))
            cfg_state = ConfigState.NONE
            if (not words[0] == '!'):
                process_line_in_none_state(l, words)


    elif (cfg_state == ConfigState.CALL_HOME):
        if (not (l[0] == ' ')):
            v_logger.info("%d: configuration end for " \
                          "call-home" % \
                          ( input_line_num ))
            debug_print("%d: configuration end for " \
                          "call-home" % \
                        ( input_line_num ))
            cfg_state = ConfigState.NONE
            if (not words[0] == '!'):
                process_line_in_none_state(l, words)


    elif (cfg_state == ConfigState.ADDRESS):
        if (not l[0] == ' '):
            v_logger.info("%d: configuration end for address %s" % \
                          ( input_line_num, cur_addr_obj_name ))
            debug_print("%d: configuration end for address %s" %
                        ( input_line_num, cur_addr_obj_name ))
            process_line_in_none_state(l, words)
        else:
            if (words[0] == 'nat'):
                v_logger.info("%d: ignoring nat configuration for %s" % \
                              ( input_line_num, cur_addr_obj_name ))
                debug_print("%d: ignoring nat configuration for %s" % \
                            ( input_line_num, cur_addr_obj_name ))
            else:
                set_address_info(cur_addr, words, 0)


    elif (cfg_state == ConfigState.SERVICE):
        if (not l[0] == ' '):
            v_logger.info("%d: configuration end for service %s" % \
                          ( input_line_num, cur_svc_name ))
            debug_print("%d: configuration end for service %s" %
                        ( input_line_num, cur_svc_name ))
            process_line_in_none_state(l, words)
        elif (words[0] == 'service'):
            if ('source' in l and 'destination' in l):
                # If both src/dst are specified convert current service 
                # object into a service group object
                v_logger.info("%d: Converting service %s into service " \
                              "group as both src/dst specified" % \
                              ( input_line_num, cur_svc_name))
                debug_print("%d: Converting service %s into service " \
                            "group as both src/dst specified" % \
                            ( input_line_num, cur_svc_name))
                cur_svc_grp = ServiceGroup(cur_svc_name, \
                                           input_line_num, False)
                cur_tenant.add_service_group(cur_svc_grp, input_line_num)

                # Add source service
                src_ix = 0
                while (src_ix < len(words)):
                    if (words[src_ix] == 'source'):
                        break
                    src_ix = src_ix + 1

                # Check if its a standard service
                if (words[src_ix + 1] == 'eq'):
                    svc_nm = words[src_ix + 2]
                    if (svc_nm in service_map):
                        tnt_svc_map = cur_tenant.get_service_map()
                        if (not svc_nm in tnt_svc_map.keys()):
                            tmp_line = cur_svc.name_src_line
                            cur_svc = Service(svc_nm, tmp_line, False)
                            set_service_info(cur_svc, words, \
                                             src_ix + 1, True, words[1])
                            v_logger.info("%d: Adding Service %s to " \
                                          "current tenant" % \
                                          (input_line_num, cur_svc.name))
                            debug_print("%d: Adding Service %s to current " \
                                        "tenant" % \
                                        (input_line_num, cur_svc.name))
                            cur_tenant.add_service(cur_svc, input_line_num)
                        else:
                            cur_svc = tnt_svc_map[svc_nm][0]
                else:
                    tmp_line = cur_svc.name_src_line
                    cur_svc = Service('%s_src' % cur_svc_name, tmp_line, False)
                    set_service_info(cur_svc, words, src_ix + 1, True, words[1])
                    v_logger.info("%d: Adding Service %s to current tenant" % \
                                  (input_line_num, cur_svc.name))
                    debug_print("%d: Adding Service %s to current tenant" % \
                                (input_line_num, cur_svc.name))
                    cur_tenant.add_service(cur_svc, input_line_num)

                v_logger.info("%d: Adding Service %s to Service Group %s" % \
                              (input_line_num, cur_svc.name, cur_svc_grp.name))
                debug_print("%d: Adding Service %s to Service Group %s" % \
                            (input_line_num, cur_svc.name, cur_svc_grp.name))
                cur_svc_grp.add_service(cur_svc.name, input_line_num)

                # Add destination service
                dst_ix = 0
                while (dst_ix < len(words)):
                    if (words[dst_ix] == 'destination'):
                        break
                    dst_ix = dst_ix + 1

                # Check if its a standard service
                if (words[dst_ix + 1] == 'eq'):
                    svc_nm = words[dst_ix + 2]
                    if (svc_nm in service_map):
                        tnt_svc_map = cur_tenant.get_service_map()
                        if (not svc_nm in tnt_svc_map.keys()):
                            tmp_line = cur_svc.name_src_line
                            cur_svc = Service(svc_nm, tmp_line, False)
                            set_service_info(cur_svc, words, \
                                             dst_ix + 1, False, words[1])
                            v_logger.info("%d: Adding Service %s to " \
                                          "current tenant" % \
                                          (input_line_num, cur_svc.name))
                            debug_print("%d: Adding Service %s to current " \
                                        "tenant" % \
                                        (input_line_num, cur_svc.name))
                            cur_tenant.add_service(cur_svc, input_line_num)
                        else:
                            cur_svc = tnt_svc_map[svc_nm][0]
                else:
                    tmp_line = cur_svc.name_src_line
                    cur_svc = Service('%s_dst' % cur_svc_name, tmp_line, False)
                    set_service_info(cur_svc, words, \
                                     dst_ix + 1, False, words[1])
                    v_logger.info("%d: Adding Service %s to " \
                                  "current tenant" % \
                                  (input_line_num, cur_svc.name))
                    debug_print("%d: Adding Service %s to " \
                                "current tenant" % \
                                (input_line_num, cur_svc.name))
                    cur_tenant.add_service(cur_svc, input_line_num)

                v_logger.info("%d: Adding Service %s to Service Group %s" % \
                              (input_line_num, cur_svc.name, cur_svc_grp.name))
                debug_print("%d: Adding Service %s to Service Group %s" % \
                            (input_line_num, cur_svc.name, cur_svc_grp.name))
                cur_svc_grp.add_service(cur_svc.name, input_line_num)
            elif ('source' in l):
                # Add source service
                set_service_info(cur_svc, words, src_ix + 1, True, words[1])
                v_logger.info("%d: Adding Service %s to current tenant" % \
                              (input_line_num, cur_svc.name))
                debug_print("%d: Adding Service %s to current tenant" % \
                            (input_line_num, cur_svc.name))
                cur_tenant.add_service(cur_svc, input_line_num)
            elif ('destination' in l):
                # Add destination service
                set_service_info(cur_svc, words, src_ix + 1, False, words[1])
                v_logger.info("%d: Adding Service %s to current tenant" % \
                              (input_line_num, cur_svc.name))
                debug_print("%d: Adding Service %s to current tenant" % \
                            (input_line_num, cur_svc.name))
                cur_tenant.add_service(cur_svc, input_line_num)


    elif (cfg_state == ConfigState.SERVICE_GROUP):
        if (not l[0] == ' '):
            v_logger.info("%d: configuration end for service group %s" % \
                          ( input_line_num, cur_svc_grp_name ))
            debug_print("%d: configuration end for service group %s" %
                        ( input_line_num, cur_svc_grp_name ))
            cur_tenant.add_service_group(cur_svc_grp, input_line_num)
            process_line_in_none_state(l, words)
        elif (words[0] == 'port-object'):
            # Check if its a standard service
            if (words[1] == 'eq'):
                svc_nm = words[2]
                if (svc_nm in service_map):
                    tnt_svc_map = cur_tenant.get_service_map()
                    if (not svc_nm in tnt_svc_map.keys()):
                        cur_svc = Service(svc_nm, input_line_num, False)
                        set_service_info(cur_svc, words, \
                                         1, True, words[1])
                        v_logger.info("%d: Adding Service %s to " \
                                      "current tenant" % \
                                      (input_line_num, cur_svc.name))
                        debug_print("%d: Adding Service %s to current " \
                                    "tenant" % \
                                    (input_line_num, cur_svc.name))
                        cur_tenant.add_service(cur_svc, input_line_num)
                    else:
                        cur_svc = tnt_svc_map[svc_nm][0]
            if (cur_svc is None):
                cur_svc_grp_member_cnt = cur_svc_grp_member_cnt + 1
                cur_svc = Service('%s_%d' % \
                                  (cur_svc_grp_name, cur_svc_grp_member_cnt), \
                                  input_line_num, False)
                set_service_info(cur_svc, words, 1, False, cur_svc_grp_proto)
                v_logger.info("%d: Adding Service %s to current tenant" % \
                              (input_line_num, cur_svc.name))
                debug_print("%d: Adding Service %s to current tenant" % \
                            (input_line_num, cur_svc.name))
                cur_tenant.add_service(cur_svc, input_line_num)

            v_logger.info("%d: Adding Service %s to Service Group %s" % \
                          (input_line_num, cur_svc.name, cur_svc_grp.name))
            debug_print("%d: Adding Service %s to Service Group %s" % \
                        (input_line_num, cur_svc.name, cur_svc_grp.name))
            cur_svc_grp.add_service(cur_svc.name, input_line_num)
        elif (words[0] == 'service-object'):
            if (words[1] == 'object'):
                svc_name = words[2]
                v_logger.info("%d: Adding Service %s to Service Group %s" % \
                              (input_line_num, svc_name, cur_svc_grp.name))
                debug_print("%d: Adding Service %s to Service Group %s" % \
                            (input_line_num, svc_name, cur_svc_grp.name))
                cur_svc_grp.add_service(svc_name, input_line_num)
            elif (words[1] == 'icmp'):
                cur_svc_grp_member_cnt = cur_svc_grp_member_cnt + 1
                cur_svc = Service('%s_%d' % \
                                  (cur_svc_grp_name, cur_svc_grp_member_cnt), \
                                  input_line_num, False)
                cur_svc.set_proto('ICMP', input_line_num)
                v_logger.info("%d: Adding Service %s to current tenant" % \
                              (input_line_num, cur_svc.name))
                debug_print("%d: Adding Service %s to current tenant" % \
                            (input_line_num, cur_svc.name))
                cur_tenant.add_service(cur_svc, input_line_num)

                v_logger.info("%d: Adding Service %s to Service Group %s" % \
                              (input_line_num, cur_svc.name, cur_svc_grp.name))
                debug_print("%d: Adding Service %s to Service Group %s" % \
                            (input_line_num, cur_svc.name, cur_svc_grp.name))
                cur_svc_grp.add_service(cur_svc.name, input_line_num)
        elif (words[0] == 'protocol-object'):
            if (words[1] == 'icmp'):
                cur_svc_grp_member_cnt = cur_svc_grp_member_cnt + 1
                cur_svc = Service('%s_%d' % \
                                  (cur_svc_grp_name, cur_svc_grp_member_cnt), \
                                  input_line_num, False)
                cur_svc.set_proto('ICMP', input_line_num)
                v_logger.info("%d: Adding Service %s to current tenant" % \
                              (input_line_num, cur_svc.name))
                debug_print("%d: Adding Service %s to current tenant" % \
                            (input_line_num, cur_svc.name))
                cur_tenant.add_service(cur_svc, input_line_num)

                v_logger.info("%d: Adding Service %s to Service Group %s" % \
                              (input_line_num, cur_svc.name, cur_svc_grp.name))
                debug_print("%d: Adding Service %s to Service Group %s" % \
                            (input_line_num, cur_svc.name, cur_svc_grp.name))
                cur_svc_grp.add_service(cur_svc.name, input_line_num)
            elif (words[1] == 'ip'):
                v_logger.info("%d: Service Group %s has protocol 'ip' " \
                              "which refers to any IP port/protocol" % \
                              (input_line_num, cur_svc_grp.name))
                debug_print("%d: Service Group %s has protocol 'ip' " \
                              "which refers to any IP port/protocol" % \
                            (input_line_num, cur_svc_grp.name))
                versa_cfg.set_service_any(cur_svc_grp.name)


    elif (cfg_state == ConfigState.ADDRESS_GROUP):
        if (not l[0] == ' '):
            v_logger.info("%d: configuration end for address group %s" % \
                          ( input_line_num, cur_addr_grp_name ))
            debug_print("%d: configuration end for address group %s" %
                        ( input_line_num, cur_addr_grp_name ))
            cur_tenant.add_address_group(cur_addr_grp, input_line_num)
            process_line_in_none_state(l, words)
        elif (words[0] == 'network-object'):
            if (words[1] == 'object'):
                addr_name = words[2]
                v_logger.info("%d: Adding Address %s to Address Group %s" % \
                              (input_line_num, addr_name, cur_addr_grp.name))
                debug_print("%d: Adding Address %s to Address Group %s" % \
                            (input_line_num, addr_name, cur_addr_grp.name))
                cur_addr_grp.add_address(addr_name, input_line_num)
            else:
                cur_addr_grp_member_cnt = cur_addr_grp_member_cnt + 1
                cur_addr = Address('%s_%d' % \
                                   (cur_addr_grp_name, \
                                    cur_addr_grp_member_cnt), \
                                    input_line_num, False)
                set_address_info(cur_addr, words, 1)
                v_logger.info("%d: Adding Address %s to Address Group %s" % \
                              (input_line_num, cur_addr.name, \
                               cur_addr_grp.name))
                debug_print("%d: Adding Address %s to Address Group %s" % \
                            (input_line_num, cur_addr.name, cur_addr_grp.name))
                cur_addr_grp.add_address(cur_addr.name, input_line_num)
        elif (words[0] == 'group-object'):
            addr_grp_name = words[1]
            v_logger.info("%d: Adding Address Group %s to Address Group %s" % \
                          (input_line_num, addr_grp_name, cur_addr_grp.name))
            debug_print("%d: Adding Address Group %s to Address Group %s" % \
                        (input_line_num, addr_grp_name, cur_addr_grp.name))
            cur_addr_grp.add_address_group(addr_grp_name, input_line_num)



# Add the firewall rules from ASA to versa configuration
rule_num = 1
cur_ngfw = NextGenFirewall(cur_tenant.name + '_policy',
                           0, False)
cur_tenant.set_next_gen_firewall(cur_ngfw, cur_ngfw.name_src_line)
for acl, info in asa_rule_intf_map.iteritems():
    [ direction, intf, line_num ] = info
    rules = asa_rule_map[acl]
    for r in rules:
        rule_line_num = r.name_src_line
        cur_ngfw_rule = NextGenFirewallRule(r.name,
                                            r.name_src_line, False)
        if (direction == 'in'):
            cur_ngfw_rule.add_src_zone(intf, line_num)
        elif (direction == 'out'):
            cur_ngfw_rule.add_dst_zone(intf, line_num)
        else:
            v_logger.info("%d: Error - unknown direction %s in access-group" % \
                          (line_num, direction))
            debug_print("%d: Error - unknown direction %s in access-group" % \
                        (line_num, direction))

        # Set the src address
        addr_map = r.get_src_addr_map()
        if (len(addr_map.keys()) > 1):
            cur_ngfw_rule.set_src_addr_map(addr_map)
        elif (len(addr_map.keys()) == 1):
            k = addr_map.keys()[0]
            if (k == 'any4'):
                cur_ngfw_rule.set_match_ip_version('ipv4', line_num)
            elif (not k == 'any'):
                cur_ngfw_rule.set_src_addr_map(addr_map)

        # Set the dst address
        addr_map = r.get_dst_addr_map()
        if (len(addr_map.keys()) > 1):
            cur_ngfw_rule.set_dst_addr_map(addr_map)
        elif (len(addr_map.keys()) == 1):
            k = addr_map.keys()[0]
            if (k == 'any4'):
                cur_ngfw_rule.set_match_ip_version('ipv4', line_num)
            elif (not k == 'any'):
                cur_ngfw_rule.set_dst_addr_map(addr_map)

        # Set the src address group
        cur_ngfw_rule.set_src_addr_grp_map(r.get_src_addr_grp_map())

        # Set the dst address group
        cur_ngfw_rule.set_dst_addr_grp_map(r.get_dst_addr_grp_map())

        # Set the service
        sm = r.get_service_map()
        if (not 'ip' in sm.keys()):
            if ('tcp' in sm.keys() and len(sm.keys()) == 1):
                tnt_sm = cur_tenant.get_service_map()
                if (not 'tcp' in tnt_sm.keys()):
                    cur_svc = Service('tcp', line_num, False)
                    cur_svc.set_proto('TCP', line_num)
                    v_logger.info("%d: Adding Service %s to current tenant" % \
                                  (rule_line_num, cur_svc.name))
                    debug_print("%d: Adding Service %s to current tenant" % \
                                (rule_line_num, cur_svc.name))
                    cur_tenant.add_service(cur_svc, line_num)
                else:
                    cur_svc = tnt_sm['tcp'][0]
                v_logger.info("%d: Setting Service to %s for rule %s" % \
                              (rule_line_num, cur_svc.name, \
                               cur_ngfw_rule.name))
                debug_print("%d: Setting Service to %s to for rule %s" % \
                            (rule_line_num, cur_svc.name, cur_ngfw_rule.name))
                cur_ngfw_rule.add_service(cur_svc, line_num)
            elif ('udp' in sm.keys() and len(sm.keys()) == 1):
                tnt_sm = cur_tenant.get_service_map()
                if (not 'udp' in tnt_sm.keys()):
                    cur_svc = Service('udp', line_num, False)
                    cur_svc.set_proto('UDP', line_num)
                    v_logger.info("%d: Adding Service %s to current tenant" % \
                                  (rule_line_num, cur_svc.name))
                    debug_print("%d: Adding Service %s to current tenant" % \
                                (rule_line_num, cur_svc.name))
                    cur_tenant.add_service(cur_svc, line_num)
                else:
                    cur_svc = tnt_sm['udp'][0]
                v_logger.info("%d: Setting Service to %s for rule %s" % \
                              (rule_line_num, cur_svc.name, \
                               cur_ngfw_rule.name))
                debug_print("%d: Setting Service to %s to for rule %s" % \
                            (rule_line_num, cur_svc.name, cur_ngfw_rule.name))
                cur_ngfw_rule.add_service(cur_svc, line_num)
            elif ('icmp' in sm.keys() and len(sm.keys()) == 1):
                tnt_sm = cur_tenant.get_service_map()
                if (not 'icmp' in tnt_sm.keys()):
                    cur_svc = Service('icmp', line_num, False)
                    cur_svc.set_proto('ICMP', line_num)
                    v_logger.info("%d: Adding Service %s to current tenant" % \
                                  (rule_line_num, cur_svc.name))
                    debug_print("%d: Adding Service %s to current tenant" % \
                                (rule_line_num, cur_svc.name))
                    cur_tenant.add_service(cur_svc, line_num)
                else:
                    cur_svc = tnt_sm['icmp'][0]
                v_logger.info("%d: Setting Service to %s for rule %s" % \
                              (rule_line_num, cur_svc.name, \
                               cur_ngfw_rule.name))
                debug_print("%d: Setting Service to %s to for rule %s" % \
                            (rule_line_num, cur_svc.name, cur_ngfw_rule.name))
                cur_ngfw_rule.add_service(cur_svc, line_num)
            else:
                first = True
                snames = ''
                for sn in sm.keys():
                    if (type(sn) == type('')):
                        sname = sn
                    else:
                        sname = sn.name
                    if (not first):
                        snames = snames + ', '
                    snames = snames + sname
                v_logger.info("%d: Setting Service to %s for rule %s" % \
                              (rule_line_num, snames, \
                               cur_ngfw_rule.name))
                debug_print("%d: Setting Service to %s to for rule %s" % \
                            (rule_line_num, snames, cur_ngfw_rule.name))
                cur_ngfw_rule.set_service_map(sm)
        cur_ngfw_rule.set_schedule(r.get_schedule(), 0)
        cur_ngfw_rule.set_action(r.get_action(), r.get_action_line())
        cur_ngfw.add_rule(cur_ngfw_rule)


        saddr_list = r.get_src_addr_map().keys()
        saddr_list.extend(r.get_src_addr_grp_map().keys())
        daddr_list = r.get_dst_addr_map().keys()
        daddr_list.extend(r.get_dst_addr_grp_map().keys())

        print('%d,%s,%s,%s,%s,%s,' \
              '%s,%s,%s,%s' % \
              ( rule_num, \
                r.name, \
                str(r.get_src_zone_map().keys()), \
                str(saddr_list), \
                str(r.get_dst_zone_map().keys()), \
                str(daddr_list), \
                '', \
                str(r.get_service_map().keys()), \
                str(r.get_schedule()), \
                r.get_action().to_string() \
              ), \
              file=csv_out_fh)


        saddr_list = cur_ngfw_rule.get_src_addr_map().keys()
        saddr_list.extend(cur_ngfw_rule.get_src_addr_grp_map().keys())
        daddr_list = cur_ngfw_rule.get_dst_addr_map().keys()
        daddr_list.extend(cur_ngfw_rule.get_dst_addr_grp_map().keys())

        print('%d.1,%s,%s,%s,%s,%s,' \
              '%s,%s,%s,%s' % \
              ( rule_num, \
                cur_ngfw_rule.name, \
                str(cur_ngfw_rule.get_src_zone_map().keys()), \
                str(saddr_list), \
                str(cur_ngfw_rule.get_dst_zone_map().keys()), \
                str(daddr_list), \
                str(cur_ngfw_rule.get_match_ip_version()), \
                str(cur_ngfw_rule.get_service_map().keys()), \
                str(cur_ngfw_rule.get_schedule()), \
                cur_ngfw_rule.get_action().to_string() \
              ), \
              file=csv_out_fh)
        rule_num = rule_num + 1

versa_cfg.replace_address_by_address_group()
versa_cfg.replace_service_group_by_service_members()
versa_cfg.check_config(strict_checks)
versa_cfg.write_config(tnt_xlate_map, c_options.template,
                       c_options.device, out_fh, log_fh)


out_fh.close()
csv_out_fh.close()
log_fh.close()
in_fh.close()












