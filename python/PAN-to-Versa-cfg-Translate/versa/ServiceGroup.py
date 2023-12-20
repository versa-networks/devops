#!/usr/bin/python
#  ServiceGroup.py - Versa ServiceGroup definition
#
#  This file has the definition of a service group object, that can be used
#  in any policy configuration on the Versa FlexVNF.
#
#  Copyright (c) 2023, Versa Networks, Inc.
#  All rights reserved.
#


from versa.ConfigObject import ConfigObject


class ServiceGroup(ConfigObject):
    """
    Represents a service group configuration.

    This class inherits from ConfigObject and adds additional attributes specific to service group configurations, such as service map and service group map.

    Args:
        ConfigObject (class): The base class for configuration objects. It provides common attributes for all configuration objects, such as name, and predefined flag.
    """

    def __init__(self, name, is_predefined):
        super().__init__(name, is_predefined)
        self.service_map = {}
        self.service_group_map = {}

    def add_service(self, _service):
        self.service_map[_service] = None

    def set_service_map(self, _service_map):
        self.service_map = _service_map

    def add_service_group(self, _service_group):
        self.service_group_map[_service_group] = None

    def set_service_group_map(self, _service_group_map):
        self.service_group_map = _service_group_map

    def replace_service_by_service_group(self, service_group):
        """
        Replaces a service with a service group in the service_map if the service group exists.
        Then adds the service group to the service_group_map.

        Args:
            service_group (str): The service group to replace the service with.
        """
        if service_group in self.service_map:
            self.service_map.pop(service_group)
            
    def write_config(self, cfg_fh, indent):
        """
        Writes the configuration of the service group to a file.

        Args:
            cfg_fh (file): The file handle where the configuration will be written.
            indent (str): The indentation to use in the output.
        """
        output = []

        output.append(f"{indent}    {self.name} {{")

        if self.service_map:
            output.append("")
            output.append(f"{indent}         service-list [ {' '.join(self.service_map.keys())} ];")

        if self.service_group_map:
            output.append(f"{indent}         service-group-list [ {' '.join(self.service_group_map.keys())} ];")

        output.append(f"{indent}     }}")

        if output:
            print('\n'.join(output), file=cfg_fh)
