#!/usr/bin/python
#  System.py - Versa System definition
#
#  This file has the definition of a network address object, that can be used
#  in any policy configuration on the Versa FlexVNF.
#
#  Copyright (c) 2023, Versa Networks, Inc.
#  All rights reserved.
#

from versa.ConfigObject import ConfigObject


class System(ConfigObject):
    """
    Represents a system configuration.

    This class inherits from ConfigObject and adds additional attributes specific to system configurations, such as hostname, domain search, and name servers.

    Args:
        ConfigObject (class): The base class for configuration objects. It provides common attributes for all configuration objects, such as name, and predefined flag.
    """

    SYSTEM_NAME = "system"

    def __init__(self):
        super().__init__(self.SYSTEM_NAME, False)
        self.hostname = ""
        self.domain_search = ""
        self.name_servers = []
        self.interface_map = 0

    def get_hostname(self):
        return self.hostname

    def set_hostname(self, _name):
        self.hostname = _name

    def get_domain_search(self):
        return self.domain_search

    def set_domain_search(self, _ds):
        self.domain_search = _ds

    def get_name_servers(self):
        return self.name_servers

    def add_name_server(self, _ns):
        self.name_servers.append(_ns)

    def write_config(self, _cfg_fh, _indent):
        """
        Writes the system configuration to a file.

        This method writes the system configuration to a file. The configuration is indented by a specified amount.

        Args:
            _cfg_fh (TextIO): The file handle to write the configuration to.
            _indent (str): The string to use for indentation.
        """
        if len(self.interface_map) > 0:
            print(
                f"""{_indent}    system {{
        {_indent}        identification {{
        {_indent}            name {self.get_hostname()}
        {_indent}        }}
        {_indent}    }}""",
                file=_cfg_fh,
            )
