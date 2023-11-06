#!/usr/bin/python
#  Service.py - Versa Service definition
#
#  This file has the definition of a network service object, that can be used
#  in any policy configuration on the Versa FlexVNF.
#
#  Copyright (c) 2017, Versa Networks, Inc.
#  All rights reserved.
#
#  pylint: disable=invalid-name,attribute-defined-outside-init

from enum import Enum
from versa.ConfigObject import ConfigObject


class PortMatchType(Enum):
    ANY_PORT_MATCH = 1
    SRC_DST_PORT_MATCH = 2


class ProtoMatchType(Enum):
    NONE = 0
    ENUM_PROTO_MATCH = 1
    PROTO_VALUE_MATCH = 2


class Service(ConfigObject):
    """Service _summary_

    Args:
        ConfigObject (_type_): _description_
    """

    def __init__(self, _name, _name_src_line, _is_predefined):
        super().__init__(_name, _name_src_line, _is_predefined)
        self.src_port = None
        self.dst_port = None
        self.port = None
        self.port_match_type = PortMatchType.ANY_PORT_MATCH
        self.proto = None
        self.proto_value = None
        self.proto_match_type = ProtoMatchType.NONE
        self.proto_match_type = None
        self.desc = None
        self.desc_line = None

    def set_description(self, _desc, _desc_line):
        self.desc = _desc
        self.desc_line = _desc_line

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
        """set_proto _summary_

        Args:
            _proto (_type_): _description_
            _proto_src_line (_type_): _description_
        """
        if not _proto.lower() == "ip":
            if _proto.lower() == "icmp6":
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
        """equals _summary_

        Args:
            _other (_type_): _description_

        Returns:
            _type_: _description_
        """
        if not self.proto_match_type == _other.proto_match_type:
            return False
        if self.port_match_type == PortMatchType.ANY_PORT_MATCH:
            if not self.port == _other.port:
                return False
        elif self.port_match_type == PortMatchType.SRC_DST_PORT_MATCH:
            if not self.src_port == _other.src_port:
                return False
            if not self.dst_port == _other.dst_port:
                return False
        if self.proto_match_type == ProtoMatchType.ENUM_PROTO_MATCH:
            if not self.proto == _other.proto:
                return False
        elif self.proto_match_type == ProtoMatchType.PROTO_VALUE_MATCH:
            if not self.proto_value == _other.proto_value:
                return False
        return True

    def write_config(self, output_vd_cfg, _cfg_fh,  _indent):
        """write_config _summary_

        Args:
            output_vd_cfg (_type_): _description_
            _cfg_fh (_type_): _description_
            _indent (_type_): _description_
        """
        if output_vd_cfg:
            vd_str = "service "
        else:
            vd_str = ""
        if not self.proto_match_type == ProtoMatchType.NONE:
            #print(f"{_indent}    # src line number {self.name_src_line}", file=_cfg_fh)
            print(f"{_indent}    {vd_str}{self.name} {{", file=_cfg_fh)
            if self.desc is not None:
                #print(f"{_indent}        # src line number {self.desc_line}", file=_cfg_fh)
                print(f'{_indent}        description "{self.desc}";', file=_cfg_fh)
            if self.port_match_type == PortMatchType.ANY_PORT_MATCH:
                if self.port is not None:
                    #print(f"{_indent}        # src line number {self.port_src_line}",file=_cfg_fh,)
                    print(f"{_indent}        port {self.port};", file=_cfg_fh)
            elif self.port_match_type == PortMatchType.SRC_DST_PORT_MATCH:
                if self.src_port is not None:
                    #print(f"{_indent}        # src line number {self.src_port_src_line}",file=_cfg_fh,)
                    print(f"{_indent}        source-port {self.src_port};", file=_cfg_fh)
                if self.dst_port is not None:
                    #print(f"{_indent}        # src line number {self.port_src_line}",file=_cfg_fh,)
                    print(f"{_indent}        destination-port {self.dst_port};", file=_cfg_fh)
            if self.proto_match_type == ProtoMatchType.ENUM_PROTO_MATCH:
                if self.proto is not None:
                    #print(f"{_indent}        # src line number {self.proto_src_line}",file=_cfg_fh,)
                    print(f"{_indent}        protocol {self.proto};", file=_cfg_fh)
            elif self.proto_match_type == ProtoMatchType.PROTO_VALUE_MATCH:
                if self.proto_value is not None:
                    #print(f"{_indent}        # src line number {self.proto_value_src_line}",file=_cfg_fh,)
                    print(f"{_indent}         protocol-value {self.proto_value};", file=_cfg_fh)
            print(f"{_indent}     }}", file=_cfg_fh)
