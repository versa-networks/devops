#
#  Address.py - Versa Address definition
# 
#  This file has the definition of a network address object, that can be used
#  in any policy configuration on the Versa FlexVNF.
# 
#  Copyright (c) 2017, Versa Networks, Inc.
#  All rights reserved.
#

from __future__ import print_function
from versa.ConfigObject import ConfigObject
from enum import Enum



class AddressType(Enum):
    NONE = 0
    IP_V4_RANGE = 1
    IP_V4_PREFIX = 2
    IP_V6_PREFIX = 3
    FQDN = 4
    WILDCARD = 5

class Address(ConfigObject):

    def __init__(self, _name, _name_src_line, _is_predefined):
        super(Address, self).__init__(
                                  _name, _name_src_line, _is_predefined)
        self.addr_type = AddressType.NONE
        self.addr_value = None
        self.start_ip = None
        self.end_ip = None
        self.desc = None
        self.desc_line = None

    def get_description(self):
        return self.desc

    def set_description(self, _desc, _desc_line):
        self.desc = _desc
        self.desc_line = _desc_line

    def set_addr_type(self, _addr_type, _addr_type_src_line):
        self.addr_type = _addr_type
        self.addr_type_src_line = _addr_type_src_line

    def set_addr_value(self, _addr_value, _addr_value_src_line):
        self.addr_value = _addr_value
        self.addr_value_src_line = _addr_value_src_line

    def set_start_ip(self, _start_ip, _start_ip_src_line):
        self.start_ip = _start_ip
        self.start_ip_src_line = _start_ip_src_line
        if (self.end_ip is not None):
            set_addr_value(self.start_ip + '-' + self.end_ip)

    def set_end_ip(self, _end_ip, _end_ip_src_line):
        self.end_ip = _end_ip
        self.end_ip_src_line = _end_ip_src_line
        if (self.start_ip is not None):
            self.set_addr_value(self.start_ip + '-' + self.end_ip,
                                str(self.start_ip_src_line) + ', ' +
                                                 str(self.end_ip_src_line))

    def equals(self, _other):
        return ((self.addr_type == _other.addr_type) and
                (self.addr_value == _other.addr_value))

    def write_config(self, output_vd_cfg, _cfg_fh, _log_fh, _indent):
        if (output_vd_cfg):
            vd_str = 'address '
        else:
            vd_str = ''
        print('%s    # src line number %d' % ( _indent, self.name_src_line), file=_cfg_fh)
        if (self.addr_type == AddressType.IP_V4_RANGE):
            print('%s    %s%s {' % ( _indent, vd_str, self.name ), file=_cfg_fh)
            print('%s        # src line number %s' %
                  ( _indent, self.addr_value_src_line ), file=_cfg_fh)
            print('%s        ipv4-range %s;' %
                  ( _indent, self.addr_value ), file=_cfg_fh)
            if (self.desc is not None):
                print('%s        # src line number %d' %
                      ( _indent, self.desc_line ), file=_cfg_fh)
                print('%s        description %s;' %
                      ( _indent, self.desc ), file=_cfg_fh)
            print('%s    }' % ( _indent ), file=_cfg_fh)
        elif (self.addr_type == AddressType.FQDN):
            print('%s    %s%s {' % ( _indent, vd_str, self.name ), file=_cfg_fh)
            print('%s        # src line number %d' %
                  ( _indent, self.addr_value_src_line ), file=_cfg_fh)
            print('%s        fqdn %s;' %
                  ( _indent, self.addr_value ), file=_cfg_fh)
            if (self.desc is not None):
                print('%s        # src line number %d' %
                      ( _indent, self.desc_line ), file=_cfg_fh)
                print('%s        description "%s";' %
                      ( _indent, self.desc ), file=_cfg_fh)
            print('%s    }' % ( _indent ), file=_cfg_fh)
        elif (self.addr_type == AddressType.IP_V4_PREFIX):
            print('%s    %s%s {' % ( _indent, vd_str, self.name ), file=_cfg_fh)
            print('%s        # src line number %d' %
                  ( _indent, self.addr_value_src_line ), file=_cfg_fh)
            print('%s        ipv4-prefix %s;' %
                  ( _indent, self.addr_value ), file=_cfg_fh)
            if (self.desc is not None):
                print('%s        # src line number %d' %
                      ( _indent, self.desc_line ), file=_cfg_fh)
                print('%s        description "%s";' %
                      ( _indent, self.desc ), file=_cfg_fh)
            print('%s    }' % ( _indent ), file=_cfg_fh)
        elif (self.addr_type == AddressType.WILDCARD):
            print('%s    %s%s {' % ( _indent, vd_str, self.name ), file=_cfg_fh)
            print('%s        # src line number %d' %
                  ( _indent, self.addr_value_src_line ), file=_cfg_fh)
            print('%s        ipv4-wildcard-mask %s;' %
                  ( _indent, self.addr_value ), file=_cfg_fh)
            if (self.desc is not None):
                print('%s        # src line number %d' %
                      ( _indent, self.desc_line ), file=_cfg_fh)
                print('%s        description "%s";' %
                      ( _indent, self.desc ), file=_cfg_fh)
            print('%s    }' % ( _indent ), file=_cfg_fh)





