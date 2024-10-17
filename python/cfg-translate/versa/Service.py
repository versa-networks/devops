#
#  Service.py - Versa Service definition
# 
#  This file has the definition of a network service object, that can be used
#  in any policy configuration on the Versa FlexVNF.
# 
#  Copyright (c) 2017, Versa Networks, Inc.
#  All rights reserved.
#

from __future__ import print_function
from versa.ConfigObject import ConfigObject
from enum import Enum


class PortMatchType(Enum):
    ANY_PORT_MATCH = 1
    SRC_DST_PORT_MATCH = 2

class ProtoMatchType(Enum):
    NONE = 0
    ENUM_PROTO_MATCH = 1
    PROTO_VALUE_MATCH = 2


class Service(ConfigObject):

    def __init__(self, _name, _name_src_line, _is_predefined):
        super(Service, self).__init__(
                                  _name, _name_src_line, _is_predefined)
        self.src_port = None
        self.dst_port = None
        self.port = None
        self.port_match_type = PortMatchType.ANY_PORT_MATCH
        self.proto = None
        self.proto_value = None
        self.proto_match_type = ProtoMatchType.NONE

    def set_src_port(self, _src_port, _src_port_src_line):
        self.src_port = _src_port
        self.src_port_src_line = _src_port_src_line
        self.port_match_type = PortMatchType.SRC_DST_PORT_MATCH

    def set_dst_port(self, _dst_port, _dst_port_src_line):
        self.dst_port = _dst_port
        self.dst_port_src_line = _dst_port_src_line
        self.port_match_type = PortMatchType.SRC_DST_PORT_MATCH

    def set_port(self, _port, _port_src_line):
        self.port = _port
        self.port_src_line = _port_src_line
        self.port_match_type = PortMatchType.ANY_PORT_MATCH

    def set_proto(self, _proto, _proto_src_line):
        if (not _proto.lower() == 'ip'):
            if (_proto.lower() == 'icmp6'):
                self.set_proto_value(58, _proto_src_line)
            else:
                self.proto = _proto
                self.proto_src_line = _proto_src_line
                self.proto_match_type = ProtoMatchType.ENUM_PROTO_MATCH

    def set_proto_value(self, _proto_value, _proto_value_src_line):
        self.proto_value = _proto_value
        self.proto_value_src_line = _proto_value_src_line
        self.proto_match_type = ProtoMatchType.PROTO_VALUE_MATCH

    def equals(self, _other):
        if (not self.proto_match_type == _other.proto_match_type ):
            return False
        if (self.port_match_type == PortMatchType.ANY_PORT_MATCH):
            if (not self.port == _other.port):
                return False
        elif (self.port_match_type == PortMatchType.SRC_DST_PORT_MATCH):
            if (not self.src_port == _other.src_port):
                return False
            if (not self.dst_port == _other.dst_port):
                return False
        if (self.proto_match_type == ProtoMatchType.ENUM_PROTO_MATCH):
            if (not self.proto == _other.proto):
                return False
        elif (self.proto_match_type == ProtoMatchType.PROTO_VALUE_MATCH):
            if (not self.proto_value == _other.proto_value):
                return False
        return True

    def write_config(self, output_vd_cfg, _cfg_fh, _log_fh, _indent):
        if (output_vd_cfg):
            vd_str = 'service '
        else:
            vd_str = ''
        if (not self.proto_match_type == ProtoMatchType.NONE):
            print('%s    # src line number %d' % ( _indent, self.name_src_line), file=_cfg_fh)
            print('%s    %s%s {' % ( _indent, vd_str, self.name ), file=_cfg_fh)
            if (self.port_match_type == PortMatchType.ANY_PORT_MATCH):
                if (self.port is not None):
                    print('%s        # src line number %d' %
                          ( _indent, self.port_src_line ), file=_cfg_fh)
                    print('%s        port %s;' %
                          ( _indent, self.port ), file=_cfg_fh)
            elif (self.port_match_type == PortMatchType.SRC_DST_PORT_MATCH):
                if (self.src_port is not None):
                    print('%s        # src line number %d' %
                          ( _indent, self.src_port_src_line ), file=_cfg_fh)
                    print('%s        source-port %s;' %
                          ( _indent, self.src_port ), file=_cfg_fh)
                if (self.dst_port is not None):
                    print('%s        # src line number %d' %
                          ( _indent, self.port_src_line ), file=_cfg_fh)
                    print('%s        destination-port %s;' %
                          ( _indent, self.dst_port ), file=_cfg_fh)
            if (self.proto_match_type == ProtoMatchType.ENUM_PROTO_MATCH):
                if (self.proto is not None):
                    print('%s        # src line number %d' %
                          ( _indent, self.proto_src_line ), file=_cfg_fh)
                    print('%s        protocol %s;' %
                          ( _indent, self.proto ), file=_cfg_fh)
            elif (self.proto_match_type == ProtoMatchType.PROTO_VALUE_MATCH):
                if (self.proto_value is not None):
                    print('%s        # src line number %d' %
                          ( _indent, self.proto_value_src_line ), file=_cfg_fh)
                    print('%s        protocol-value %s;' %
                          ( _indent, self.proto_value ), file=_cfg_fh)
            print('%s    }' % ( _indent ), file=_cfg_fh)





