#! /usr/bin/python
#  NATPool.py - Versa NATPool definition
#
#  This file has the definition of a NAT address pool object
#
#  Copyright (c) 2017, Versa Networks, Inc.
#  All rights reserved.
##pylint: disable= invalid-name

from enum import Enum
from versa.ConfigObject import ConfigObject


class NATPoolType(Enum):
    NONE = 0
    IP_V4_RANGE = 1
    IP_V4_PREFIX = 2
    IP_V6_PREFIX = 3


class NATPool(ConfigObject):
    """NATPool
    _summary_

    Args:
        ConfigObject (_type_): _description_
    """

    def __init__(self, _name, _name_src_line, _is_predefined):
        super().__init__(_name, _name_src_line, _is_predefined)
        self.addr_type = NATPoolType.NONE
        self.addr_value = None
        self.start_ip = None
        self.end_ip = None

    def set_addr_type(self, _addr_type, _addr_type_src_line):
        self.addr_type = _addr_type
        self.addr_type_src_line = _addr_type_src_line

    def set_addr_value(self, _addr_value, _addr_value_src_line):
        self.addr_value = _addr_value
        self.addr_value_src_line = _addr_value_src_line

    def set_start_ip(self, _start_ip, _start_ip_src_line):
        """set_start_ip _summary_

        Args:
            _start_ip (_type_): _description_
            _start_ip_src_line (_type_): _description_
        """
        self.start_ip = _start_ip
        self.start_ip_src_line = _start_ip_src_line  # pylint: disable=attribute-defined-outside-init
        if self.end_ip is not None:
            set_addr_value(self.start_ip + "-" + self.end_ip)

    def set_end_ip(self, _end_ip, _end_ip_src_line):
        self.end_ip = _end_ip
        self.end_ip_src_line = _end_ip_src_line  # pylint: disable=attribute-defined-outside-init
        if self.start_ip is not None:
            self.set_addr_value(
                self.start_ip + "-" + self.end_ip,
                str(self.start_ip_src_line) + ", " + str(self.end_ip_src_line),
            )

    def equals(self, _other):
        return (self.addr_type == _other.addr_type) and (self.addr_value == _other.addr_value)

    def write_config(self, output_vd_cfg, _cfg_fh,  _indent):
        """write_config _summary_

        Args:
            output_vd_cfg (_type_): _description_
            _cfg_fh (_type_): _description_
            _indent (_type_): _description_
        """
        if output_vd_cfg:
            vd_str = "pools "
        else:
            vd_str = ""
        if self.addr_type == NATPoolType.IP_V4_RANGE:
            print(f"{_indent}{vd_str}{self.name} {{", file=_cfg_fh)
            print(f"{_indent}        address-range {self.addr_value};", file=_cfg_fh)
            print(f"{_indent}    }}", file=_cfg_fh)
        elif self.addr_type == NATPoolType.IP_V4_PREFIX:
            print(f"{_indent}    {vd_str}{self.name} {{", file=_cfg_fh)
            print(f"{_indent}        address {self.addr_value};", file=_cfg_fh)
            print(f"{_indent}    }}", file=_cfg_fh)
