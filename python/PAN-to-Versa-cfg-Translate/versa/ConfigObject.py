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
    """
    Enum representing the type of a configuration object.
    
    Attributes:
    PRE_DEFINED (int): Represents a predefined configuration object.
    USER_DEFINED (int): Represents a user-defined configuration object.
    """
    PRE_DEFINED = 1
    USER_DEFINED = 2

class ConfigObject(object):
    """
    Class representing a configuration object.

    Attributes:
    name (str): The name of the configuration object.
    obj_type (ConfigObjectType): The type of the configuration object.
    desc (str): The description of the configuration object.
    """

    def __init__(self, name, is_predefined, desc=""):
        """
        Initializes a ConfigObject instance.

        Parameters:
        name (str): The name of the configuration object.
        is_predefined (bool): Indicates whether the configuration object is predefined or not.
        desc (str): The description of the configuration object. Defaults to an empty string.
        """
        self._name = name
        self._obj_type = ConfigObjectType.PRE_DEFINED if is_predefined else ConfigObjectType.USER_DEFINED
        self._desc = desc

    @property
    def is_predefined(self):
        """
        Check if the configuration object is predefined.

        Returns:
        bool: True if the configuration object is predefined, False otherwise.
        """
        return self._obj_type == ConfigObjectType.PRE_DEFINED

    @property
    def name(self):
        """
        Gets the name of the configuration object.

        Returns:
        str: The name of the configuration object.
        """
        return self._name

    @name.setter
    def name(self, name):
        """
        Sets the name of the configuration object.

        Parameters:
        name (str): The new name of the configuration object.
        """
        self._name = name

    @property
    def desc(self):
        """
        Gets the description of the configuration object.

        Returns:
        str: The description of the configuration object.
        """
        return self._desc

    @desc.setter
    def desc(self, desc):
        """
        Sets the description of the configuration object.

        Parameters:
        desc (str): The new description of the configuration object.
        """
        self._desc = desc
