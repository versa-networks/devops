#!/usr/bin/python
#  System.py - Versa System definition
#
#  This file has the definition of a network address object, that can be used
#  in any policy configuration on the Versa FlexVNF.
#
#  Copyright (c) 2017, Versa Networks, Inc.
#  All rights reserved.
#
#  pylint: disable=invalid-name, no-member

from versa.ConfigObject import ConfigObject


class System(ConfigObject):
    """System _summary_

    Args:
        ConfigObject (_type_): _description_

    Returns:
        _type_: _description_
    """

    SYSTEM_NAME = "system"

    def __init__(self):
        super().__init__(self.SYSTEM_NAME, 0, False)
        self.hostname = ""
        self.hostname_line = None
        self.domain_search = ""
        self.domain_search_line = None
        self.name_servers = []
        self.name_servers_lines = []

    def get_hostname(self):
        return self.hostname

    def set_hostname(self, _name, _line):
        self.hostname = _name
        self.hostname_line = _line

    def get_domain_search(self):
        return self.domain_search

    def set_domain_search(self, _ds, _line):
        self.domain_search = _ds
        self.domain_search_line = _line

    def get_name_servers(self):
        """get_name_servers _summary_

        Returns:
            _type_: _description_
        """
        return self.name_servers

    def add_name_server(self, _ns, _line):
        self.name_servers.append(_ns)
        self.name_servers_lines.append(_line)

    def write_config(self, _cfg_fh,  _indent):
        """write_config _summary_

        Args:
            _cfg_fh (_type_): _description_
            _indent (_type_): _description_
        """
        if len(self.interface_map) > 0:
            print(f"{_indent}    system {{", file=_cfg_fh)
            print(f"{_indent}        identification {{", file=_cfg_fh)
            print(f"{_indent}            name {self.get_hostname()}", file=_cfg_fh)
            print(f"{_indent}        }}", file=_cfg_fh)
            print(f"{_indent}    }}", file=_cfg_fh)
