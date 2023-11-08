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

    NONE: int = 0
    IP_V4_RANGE: int = 1
    IP_V4_PREFIX: int = 2
    IP_V6_PREFIX: int = 3
    FQDN: int = 4
    WILDCARD: int = 5


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
        """
        Initialize an Address object.

        Args:
            _name (str): The name of the address.
            _name_src_line (int): The line number in the source file where the address name is defined.
            _is_predefined (bool): Whether the address is predefined.
        """
        super().__init__(_name, _name_src_line, _is_predefined)
        self.addr_type: AddressType = AddressType.NONE
        self.addr_value: Optional[str] = None
        self.start_ip: Optional[str] = None
        self.end_ip: Optional[str] = None
        self.desc: Optional[str] = None
        self.desc_line: Optional[int] = None

    def get_description(self) -> str:
        """
        Returns the description of the address.

        Returns:
            str: The description of the address.
        """
        return self.desc if self.desc is not None else ""

    def set_description(self, _desc: str, _desc_line: int):
        """Sets the description of the address."""
        self.desc = _desc
        self.desc_line = _desc_line

    def set_addr_type(self, _addr_type: AddressType, _addr_type_src_line: int):
        """Sets the address type."""
        self.addr_type = _addr_type
        self.addr_type_src_line = _addr_type_src_line

    def set_addr_value(self, _addr_value: str, _addr_value_src_line: int):
        """Sets the address value."""
        self.addr_value = _addr_value
        self.addr_value_src_line = _addr_value_src_line

    def set_start_ip(self, _start_ip: str, _start_ip_src_line: int):
        """Sets the start IP address."""
        self.start_ip = _start_ip
        self.start_ip_src_line = _start_ip_src_line
        if self.end_ip is not None:
            self.set_addr_value(f"{self.start_ip}-{self.end_ip}", _start_ip_src_line)

    def set_end_ip(self, _end_ip: str, _end_ip_src_line: int):
        """Sets the end IP address."""
        self.end_ip = _end_ip
        self.end_ip_src_line = _end_ip_src_line
        if self.start_ip is not None:
            self.set_addr_value(f"{self.start_ip}-{self.end_ip}", _end_ip_src_line)

    def equals(self, _other: 'Address') -> bool:
        """
        Checks if this address is equal to another address.

        Args:
            _other (Address): The other address to compare with.

        Returns:
            bool: True if the addresses are equal, False otherwise.
        """
        return self.addr_type == _other.addr_type and self.addr_value == _other.addr_value

    def write_config(self, output_vd_cfg: bool, _cfg_fh, _indent: str):
        """
        Writes the configuration to a file.

        Args:
            output_vd_cfg (bool): Whether to output the Versa Director configuration.
            _cfg_fh (TextIO): The file handle to write the configuration to.
            _indent (str): The indentation to use when writing the configuration.
        """
        vd_str = "address " if output_vd_cfg else ""
        addr_type_str = {
            AddressType.IP_V4_RANGE: "ipv4-range",
            AddressType.FQDN: "fqdn",
            AddressType.IP_V4_PREFIX: "ipv4-prefix",
            AddressType.WILDCARD: "ipv4-wildcard-mask"
        }.get(self.addr_type, "")

        if addr_type_str and self.addr_value is not None:
            print(f"{_indent}{vd_str}{self.name} {{", file=_cfg_fh)
            if self.addr_type == AddressType.IP_V4_PREFIX and "/" not in self.addr_value:
                print(f"{_indent}    {addr_type_str} {self.addr_value}/32;", file=_cfg_fh)
            else:
                print(f"{_indent}    {addr_type_str} {self.addr_value};", file=_cfg_fh)
            if self.desc is not None:
                print(f'{_indent}    description "{self.desc}";', file=_cfg_fh)
            print(f"{_indent}}}", file=_cfg_fh)
