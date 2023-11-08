#!/usr/bin/python
#  Service.py - Versa Service definition
#
#  This file has the definition of a network service object, that can be used
#  in any policy configuration on the Versa FlexVNF.
#
#  Copyright (c) 2023, Versa Networks, Inc.
#  All rights reserved.
#

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
    """
    Represents a network service with various properties such as source port, destination port, protocol, etc.
    Inherits from the ConfigObject class.

    Args:
        name (str): The name of the service.
        name_src_line (int): The source line of the name.
        is_predefined (bool): A flag indicating whether the service is predefined.
    """

    def __init__(self, name: str, name_src_line: int, is_predefined: bool):
        """
        Initializes the instance variables.

        Args:
            name (str): The name of the service.
            name_src_line (int): The source line of the name.
            is_predefined (bool): A flag indicating whether the service is predefined.
        """
        super().__init__(name, name_src_line, is_predefined)
        self.src_port = None
        self.dst_port = None
        self.port = None
        self.port_match_type = PortMatchType.ANY_PORT_MATCH
        self.proto = None
        self.proto_value = None
        self.proto_match_type = ProtoMatchType.NONE
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

    def set_proto(self, proto, proto_src_line: int):
        """
        Sets the protocol and the source line of the protocol.

        Args:
            proto (str): The protocol to set.
            proto_src_line (int): The source line of the protocol.
        """
        proto_lower = proto.lower()
        if proto_lower != "ip":
            if proto_lower == "icmp6":
                self.set_proto_value(58, proto_src_line)
            else:
                self.proto = proto
                self.proto_src_line = proto_src_line
                self.proto_match_type = ProtoMatchType.ENUM_PROTO_MATCH

    def set_proto_value(self, proto_value, proto_value_src_line: int):
        """
        Sets the protocol value and the source line of the protocol value.

        Args:
            proto_value (int): The protocol value to set.
            proto_value_src_line (int): The source line of the protocol value.
        """
        self.proto_value = proto_value
        self.proto_value_src_line = proto_value_src_line
        self.proto_match_type = ProtoMatchType.PROTO_VALUE_MATCH

    def equals(self, other: "Service") -> bool:
        """
        Checks if the current instance is equal to another instance.

        Args:
            other (Service): The other instance to compare with.

        Returns:
            bool: True if the instances are equal, False otherwise.
        """
        if self.proto_match_type != other.proto_match_type:
            return False
        if self.port_match_type == PortMatchType.ANY_PORT_MATCH and self.port != other.port:
            return False
        if self.port_match_type == PortMatchType.SRC_DST_PORT_MATCH and (
            self.src_port != other.src_port or self.dst_port != other.dst_port
        ):
            return False
        if self.proto_match_type == ProtoMatchType.ENUM_PROTO_MATCH and self.proto != other.proto:
            return False
        if self.proto_match_type == ProtoMatchType.PROTO_VALUE_MATCH and self.proto_value != other.proto_value:
            return False
        return True

    def write_config(self, output_vd_cfg: bool, cfg_fh, indent: str):
        """
        Writes the configuration of the service to a file.

        Args:
            output_vd_cfg (bool): A flag indicating whether to output the VD configuration.
            cfg_fh (file): The file handle of the configuration file.
            indent (str): The indentation to use when writing to the file.
        """
        vd_str = "service " if output_vd_cfg else ""

        if self.proto_match_type != ProtoMatchType.NONE:
            print(f"{indent}{vd_str}{self.name} {{", file=cfg_fh)
            if self.port_match_type == PortMatchType.ANY_PORT_MATCH and self.port is not None:
                print(f"{indent}    port {self.port};", file=cfg_fh)
            elif self.port_match_type == PortMatchType.SRC_DST_PORT_MATCH:
                if self.src_port is not None:
                    print(f"{indent}    source-port {self.src_port};", file=cfg_fh)
                if self.dst_port is not None:
                    print(f"{indent}    destination-port {self.dst_port};", file=cfg_fh)
            if self.proto_match_type == ProtoMatchType.ENUM_PROTO_MATCH and self.proto is not None:
                print(f"{indent}    protocol {self.proto};", file=cfg_fh)
            elif self.proto_match_type == ProtoMatchType.PROTO_VALUE_MATCH and self.proto_value is not None:
                print(f"{indent}    protocol-value {self.proto_value};", file=cfg_fh)
            print(f"{indent}}}", file=cfg_fh)
