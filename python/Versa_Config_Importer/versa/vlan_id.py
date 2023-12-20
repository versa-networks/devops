"""
This module defines two data classes: VLANObject and VLANIDs.

VLANObject represents a VLAN object with a name, description, and a list of VLAN IDs.
VLANIDs represents a collection of VLAN objects.

Each class includes validation in the __post_init__ method to ensure that the data is valid.
For example, the name and description must be of a certain length and can only contain certain characters,
and the VLAN IDs must be integers within a certain range.
"""
from dataclasses import dataclass
import re
from typing import List
import constants as CONSTANT


@dataclass
class VLANObject:
    """
    A class to represent a VLAN object.

    Attributes
    ----------
    name : str
        name of the VLAN object
    description : str
        description of the VLAN object
    vlan_id : List[int]
        list of VLAN IDs
    """

    name: str
    description: str
    vlan_id: List[int]

    def __post_init__(self):
        if len(self.name) > CONSTANT.NAME_MAX_LENGTH:
            raise ValueError(f"name attribute is too long! Maximum length is {CONSTANT.NAME_MAX_LENGTH}")

        if not re.match(CONSTANT.NAME_VALID_REGEX, self.name):
            raise ValueError("name attribute should only contain alphanumeric characters, hyphens, and underscores")

        if len(self.description) > CONSTANT.DESC_MAX_LENGTH:
            raise ValueError(f"description attribute is too long! Maximum length is {CONSTANT.DESC_MAX_LENGTH}")

        if not re.match(CONSTANT.DESC_VALID_REGEX, self.description):
            raise ValueError("description attribute should only contain alphanumeric characters, hyphens, underscores, and spaces")

        if not all(isinstance(id, int) for id in self.vlan_id):
            raise ValueError("All vlan_id values should be of type int")

        if not all(CONSTANT.VLAN_ID_MIN_VALUE <= id <= CONSTANT.VLAN_ID_MAX_VALUE for id in self.vlan_id):
            raise ValueError(f"All vlan_id values should be between {CONSTANT.VLAN_ID_MIN_VALUE} and {CONSTANT.VLAN_ID_MAX_VALUE}")


@dataclass
class VLANIDs:
    """
    A class to represent a collection of VLAN objects.

    Attributes
    ----------
    vlan_object : VLANObject
        an instance of the VLANObject class
    """

    vlan_object: VLANObject


"""
Example cfg

vlan-ids {
    vlan-object VLAN_ID {
        description Desc;
        vlan-id     [ 115 ];
    }
}
"""
