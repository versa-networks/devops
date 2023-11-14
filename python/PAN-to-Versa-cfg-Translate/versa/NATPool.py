#! /usr/bin/python
#  NATPool.py - Versa NATPool definition
#
#  This file has the definition of a NAT address pool object
#
#  Copyright (c) 2023, Versa Networks, Inc.
#  All rights reserved.


from enum import Enum
from versa.ConfigObject import ConfigObject


class NATPoolType(Enum):
    NONE = 0
    IP_V4_RANGE = 1
    IP_V4_PREFIX = 2
    IP_V6_PREFIX = 3


class NATPool(ConfigObject):
    """
    NATPool represents a pool of Network Address Translation (NAT) addresses.

    Args:
        name (str): The name of the NAT pool.
        name_src_line (int): The line number in the source file where the name is defined.
        is_predefined (bool): Whether the NAT pool is predefined or not.
    """

    def __init__(self, name, name_src_line, is_predefined):
        super().__init__(name, name_src_line, is_predefined)
        self.addr_type = NATPoolType.NONE
        self.addr_value = None
        self.start_ip = None
        self.end_ip = None

    def set_addr_type(self, addr_type, addr_type_src_line):
        """
        Sets the address type of the NAT pool.

        Args:
            addr_type (NATPoolType): The address type.
            addr_type_src_line (int): The line number in the source file where the address type is defined.
        """
        self.addr_type = addr_type
        self.addr_type_src_line = addr_type_src_line

    def set_addr_value(self, addr_value, addr_value_src_line):
        """
        Sets the address value of the NAT pool.

        Args:
            addr_value (str): The address value.
            addr_value_src_line (int): The line number in the source file where the address value is defined.
        """
        self.addr_value = addr_value
        self.addr_value_src_line = addr_value_src_line

    def set_start_ip(self, start_ip, start_ip_src_line):
        """
        Sets the start IP address of the NAT pool.

        Args:
            start_ip (str): The start IP address.
            start_ip_src_line (int): The line number in the source file where the start IP is defined.
        """
        self.start_ip = start_ip
        self.start_ip_src_line = start_ip_src_line
        if self.end_ip is not None:
            self.set_addr_value(self.start_ip + "-" + self.end_ip)

    def set_end_ip(self, end_ip, end_ip_src_line):
        """
        Sets the end IP address of the NAT pool.

        Args:
            end_ip (str): The end IP address.
            end_ip_src_line (int): The line number in the source file where the end IP is defined.
        """
        self.end_ip = end_ip
        self.end_ip_src_line = end_ip_src_line
        if self.start_ip is not None:
            self.set_addr_value(
                f"{self.start_ip}-{self.end_ip}",
                f"{self.start_ip_src_line}, {self.end_ip_src_line}",
            )

    def equals(self, other):
        """
        Checks if this NAT pool is equal to another NAT pool.

        Args:
            other (NATPool): The other NAT pool to compare with.

        Returns:
            bool: True if the two NAT pools are equal, False otherwise.
        """
        if not isinstance(other, NATPool):
            return False

        return (self.addr_type == other.addr_type) and (self.addr_value == other.addr_value)

    def write_config(self, output_vd_cfg, cfg_fh, indent):
        """
        Writes the configuration of the NAT pool to a file.

        Args:
            output_vd_cfg (bool): Whether to output the virtual device configuration or not.
            cfg_fh (file): The file handle where the configuration will be written.
            indent (str): The indentation to use in the output.
        """
        vd_str = "pools " if output_vd_cfg else ""
        addr_str = "address-range" if self.addr_type == NATPoolType.IP_V4_RANGE else "address"

        output = [
            f"{indent}{vd_str}{self.name} {{",
            f"{indent}        {addr_str} {self.addr_value};",
            f"{indent}    }}"
        ]

        print('\n'.join(output), file=cfg_fh)
