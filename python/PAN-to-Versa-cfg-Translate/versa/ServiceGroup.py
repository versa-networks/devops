#!/usr/bin/python
#  ServiceGroup.py - Versa ServiceGroup definition
#
#  This file has the definition of a service group object, that can be used
#  in any policy configuration on the Versa FlexVNF.
#
#  Copyright (c) 2017, Versa Networks, Inc.
#  All rights reserved.
#
#  pylint: disable=invalid-name

from versa.ConfigObject import ConfigObject


class ServiceGroup(ConfigObject):
    """ServiceGroup _summary_

    Args:
        ConfigObject (_type_): _description_
    """

    def __init__(self, _name, _name_src_line, _is_predefined):
        super().__init__(_name, _name_src_line, _is_predefined)
        self.service_map = {}
        self.service_group_map = {}

    def add_service(self, _service, _service_src_line):
        self.service_map[_service] = _service_src_line

    def set_service_map(self, _service_map):
        self.service_map = _service_map

    def add_service_group(self, _service_group, _service_group_src_line):
        self.service_group_map[_service_group] = _service_group_src_line

    def set_service_group_map(self, _service_group_map):
        self.service_group_map = _service_group_map

    def replace_service_by_service_group(self, _service_group):
        if _service_group in self.service_map:
            addr_grp_line = self.service_map[_service_group]
            self.service_map.pop(_service_group, None)
            self.service_group_map[_service_group] = addr_grp_line
            # print('Service Group %s: changing member %s from service to service group' % (self.name, _service_group))

    def write_config(self, _cfg_fh, _log_fh, _indent):
        """write_config _summary_

        Args:
            _cfg_fh (_type_): _description_
            _log_fh (_type_): _description_
            _indent (_type_): _description_
        """
        print(f"{_indent}    {self.name} {{", file=_cfg_fh)

        if len(self.service_map) > 0:
            print(f"{_indent}         # src lines:", end="", file=_cfg_fh)
            for addr, addr_line in self.service_map.items():
                print(" ", end="", file=_cfg_fh)
                print(addr_line, end="", file=_cfg_fh)
            print("", file=_cfg_fh)

            print(f"{_indent}         service-list [", end="", file=_cfg_fh)

            for addr, addr_line in self.service_map.items():
                print(" ", end="", file=_cfg_fh)
                print(addr, end="", file=_cfg_fh)

            print(" ];", file=_cfg_fh)

        if len(self.service_group_map) > 0:
            print(f"{_indent}         # src lines:", end="", file=_cfg_fh)
            for addr_grp, addr_grp_line in self.service_group_map.items():
                print(" ", end="", file=_cfg_fh)
                print(addr_grp_line, end="", file=_cfg_fh)
            print("", file=_cfg_fh)

            print(f"{_indent}         service-group-list [", end="", file=_cfg_fh)

            for addr_grp, addr_grp_line in self.service_group_map.items():
                print(" ", end="", file=_cfg_fh)
                print(addr_grp, end="", file=_cfg_fh)

            print(" ];", file=_cfg_fh)

        print(f"{_indent}     }}", file=_cfg_fh)
