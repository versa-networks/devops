#! /usr/bin/python
#  Address.py - Versa Address definition
#
#  This file has the definition of a network address object, that can be used
#  in any policy configuration on the Versa FlexVNF.
#
#  Copyright (c) 2023, Versa Networks, Inc.
#  All rights reserved.
#

from enum import Enum
from versa.ConfigObject import ConfigObject
from typing import Optional


class AddressType(Enum):
    """
    Enum representing the type of an address.

    This Enum is used to specify the type of an address in the configuration. The types can be NONE, IP_V4_RANGE, IP_V4_PREFIX, IP_V6_PREFIX, FQDN, or WILDCARD.

    Attributes:
        NONE (int): Represents no address type.
        IP_V4_RANGE (int): Represents an IPv4 range address type.
        IP_V4_PREFIX (int): Represents an IPv4 prefix address type.
        IP_V6_PREFIX (int): Represents an IPv6 prefix address type.
        FQDN (int): Represents a Fully Qualified Domain Name address type.
        WILDCARD (int): Represents a wildcard address type.
    """

    NONE = (0, "")
    IP_V4_RANGE = (1, "ipv4-range")
    IP_V4_PREFIX = (2, "ipv4-prefix")
    IP_V6_PREFIX = (3, "ipv6-prefix")
    FQDN = (4, "fqdn")
    WILDCARD = (5, "ipv4-wildcard-mask")

    def __init__(self, num, string):
        self.num = num
        self.string = string


class Address(ConfigObject):
    """
    Represents an address in the configuration.

    This class inherits from ConfigObject and adds additional attributes specific to an address, such as the address type and value.

    Args:
        _name (str): The name of the address.
        _name_src_line (int): The line number in the source file where the address name is defined.
        _is_predefined (bool): Whether the address is predefined.
    """

    def __init__(self, _name: str, _name_src_line: int, _is_predefined: bool):
        super().__init__(_name, _name_src_line, _is_predefined)
        self.addr_type: AddressType = AddressType.NONE
        self.addr_value: str = ""
        self.start_ip: str = ""
        self.end_ip: str = ""
        self.desc: str = ""
        self.desc_line: int = 0

    def set_description(self, _desc: str, _desc_line: int):
        self.desc = _desc
        self.desc_line = _desc_line

    def set_addr_type(self, _addr_type: AddressType, _addr_type_src_line: int):
        self.addr_type = _addr_type
        self.addr_type_src_line = _addr_type_src_line

    def set_addr_value(self, _addr_value: str, _addr_value_src_line: int):
        self.addr_value = _addr_value
        self.addr_value_src_line = _addr_value_src_line

    def set_start_ip(self, _start_ip: str, _start_ip_src_line: int):
        self.start_ip = _start_ip
        self.start_ip_src_line = _start_ip_src_line
        self.update_addr_value(_start_ip_src_line)

    def set_end_ip(self, _end_ip: str, _end_ip_src_line: int):
        self.end_ip = _end_ip
        self.end_ip_src_line = _end_ip_src_line
        self.update_addr_value(_end_ip_src_line)

    def update_addr_value(self, _src_line: int):
        if self.start_ip and self.end_ip:
            self.set_addr_value(f"{self.start_ip}-{self.end_ip}", _src_line)

    def equals(self, _other: "Address") -> bool:
        return self.addr_type == _other.addr_type and self.addr_value == _other.addr_value

    def write_config(self, output_vd_cfg: bool, _cfg_fh, _indent: str):
        vd_str = "address " if output_vd_cfg else ""
        addr_type_str = self.addr_type.string

        if addr_type_str and self.addr_value:
            print(f"{_indent}{vd_str}{self.name} {{", file=_cfg_fh)
            if self.addr_type == AddressType.IP_V4_PREFIX and "/" not in self.addr_value:
                print(f"{_indent}    {addr_type_str} {self.addr_value}/32;", file=_cfg_fh)
            else:
                print(f"{_indent}    {addr_type_str} {self.addr_value};", file=_cfg_fh)
            if self.desc:
                print(f'{_indent}    description "{self.desc}";', file=_cfg_fh)
            print(f"{_indent}}}", file=_cfg_fh)
