#!/usr/bin/python
#  Zone.py - Versa Zone definition
#
#  This file has the definition of a network address object, that can be used
#  in any policy configuration on the Versa FlexVNF.
#
#  Copyright (c) 2023, Versa Networks, Inc.
#  All rights reserved.

from versa.ConfigObject import ConfigObject


class Zone(ConfigObject):
    """
    Represents a network address object that can be used in any policy configuration on the Versa FlexVNF.

    Inherits from ConfigObject.

    Attributes:
    name (str): The name of the zone.
    name_src_line (int): The source line where the name was defined.
    is_predefined (bool): Whether the zone is predefined or not.
    interface_map (dict): A map of interfaces in the zone.
    network_map (dict): A map of networks in the zone.
    """

    def __init__(self, name, name_src_line, is_predefined):
        """
        Initialize a Zone instance.

        Parameters:
        name (str): The name of the zone.
        name_src_line (int): The source line where the name was defined.
        is_predefined (bool): Whether the zone is predefined or not.
        """
        super().__init__(name, name_src_line, is_predefined)
        self.interface_map = {}
        self.network_map = {}

    def add_interface(self, _interface, _interface_src_line):
        self.interface_map[_interface] = _interface_src_line

    def set_interface_map(self, _interface_map, _interface_map_src_line):
        self.interface_map = _interface_map
        self.interface_map_src_line = _interface_map_src_line

    def get_interface_map(self):
        return self.interface_map

    def add_network(self, _network, _network_src_line):
        self.network_map[_network] = _network_src_line

    def set_network_map(self, _network_map, _network_map_src_line):
        self.network_map = _network_map
        self.network_map_src_line = _network_map_src_line

    def get_network_map(self):
        return self.network_map

    def write_config(self, cfg_fh, indent, print_name=True):
        """
        Writes the configuration of the zone to a file.

        Parameters:
        cfg_fh (file): File handler where the configuration will be written.
        indent (str): String of spaces for indentation.
        print_name (bool, optional): If True, print the name of the zone. Defaults to True.
        """
        if self.interface_map or self.network_map:
            if print_name:
                print(f"{indent}    {self.name} {{", file=cfg_fh)
                print_name = False

            for map_name, map_data in [("interface-list", self.interface_map), ("networks", self.network_map)]:
                if map_data:
                    print(f"{indent}        {map_name} [ ", end="", file=cfg_fh)
                    print(" ".join(map_data.keys()), end="", file=cfg_fh)
                    print(" ];", file=cfg_fh)

            print(f"{indent}    }}", file=cfg_fh)
