#! /usr/bin/python
#  ConfigObject.py - Versa ConfigObject definition
#
#  This file has the definition of any configuration, that is supported
#  by the Versa FlexVNF.
#
#  Copyright (c) 2023, Versa Networks, Inc.
#  All rights reserved.
#


from enum import Enum


class ConfigObjectType(Enum):
    PRE_DEFINED = 1
    USER_DEFINED = 2


class ConfigObject(object):
    """
    Represents a configuration object.

    Attributes:
    name (str): The name of the configuration object.
    name_src_line (int): The source line where the name was defined.
    obj_type (ConfigObjectType): The type of the configuration object.
    """

    def __init__(self, name, name_src_line, is_predefined):
        """
        Initialize a ConfigObject instance.

        Parameters:
        name (str): The name of the configuration object.
        name_src_line (int): The source line where the name was defined.
        is_predefined (bool): Whether the configuration object is predefined or not.
        """
        self.name = name
        self.name_src_line = name_src_line
        self.obj_type = ConfigObjectType.PRE_DEFINED if is_predefined else ConfigObjectType.USER_DEFINED

    def is_predefined(self):
        """
        Check if the configuration object is predefined.

        Returns:
        bool: True if the configuration object is predefined, False otherwise.
        """
        return self.obj_type == ConfigObjectType.PRE_DEFINED


    def get_name(self):
        """
        Returns the name of the configuration object.

        Returns:
        str: The name of the configuration object.
        """
        return self.name

    def set_name(self, _name, _name_src_line):
        """
        Sets the name of the configuration object and the source line where the name was defined.

        Parameters:
        _name (str): The new name of the configuration object.
        _name_src_line (int): The source line where the new name was defined.
        """
        self.name = _name
        self.name_src_line = _name_src_line

    def set_desc(self, _desc, _desc_src_line):
        """
        Sets the description of the configuration object and the source line where the description was defined.

        Parameters:
        _desc (str): The new description of the configuration object.
        _desc_src_line (int): The source line where the new description was defined.
        """
        self.desc = _desc
        self.desc_src_line = _desc_src_line
