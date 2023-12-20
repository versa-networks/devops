"""
This module defines the data classes for address groups.
"""

from dataclasses import dataclass
import re
from typing import List, Union
import constants as CONSTANT

def validate_string(value: str, regex: str, max_length: int, attribute_name: str):
    """
    Validates a string based on a regular expression and a maximum length.

    Args:
        value (str): The string to validate.
        regex (str): The regular expression to match the string against.
        max_length (int): The maximum allowed length for the string.
        attribute_name (str): The name of the attribute, used in error messages.

    Raises:
        ValueError: If the string is longer than max_length or if it doesn't match the regex.
    """
    if len(value) > max_length:
        raise ValueError(f"{attribute_name} attribute is too long! Maximum length is {max_length}")

    if not re.match(regex, value):
        raise ValueError(f"{attribute_name} attribute should only contain alphanumeric characters, hyphens, underscores, and spaces")

@dataclass
class MatchTerm:
    """
    This class represents a match term with a list of tags.
    """
    tags: List[str]

    def __post_init__(self):
        for tag in self.tags:
            validate_string(tag, CONSTANT.DESC_VALID_REGEX, CONSTANT.DESC_MAX_LENGTH, 'tag')

@dataclass
class DynamicGroup:
    """
    This class represents a dynamic group with a description, tags, match terms.
    """
    description: str
    tag: List[str]
    match: List[MatchTerm]

    def __post_init__(self):
        validate_string(self.description, CONSTANT.DESC_VALID_REGEX, CONSTANT.DESC_MAX_LENGTH, 'description')

@dataclass
class StaticGroup:
    """
    This class represents a static group with a description, tags, address list, address files.
    """
    description: str
    tag: List[str]
    address_list: List[str]
    address_files: List[str]

    def __post_init__(self):
        validate_string(self.description, CONSTANT.DESC_VALID_REGEX, CONSTANT.DESC_MAX_LENGTH, 'description')

@dataclass
class AddressGroups:
    """
    This class represents address groups with a list of static and dynamic groups.
    """
    name: str
    group: List[Union[StaticGroup, DynamicGroup]]

    def __post_init__(self):
        validate_string(self.name, CONSTANT.NAME_VALID_REGEX, CONSTANT.NAME_MAX_LENGTH, 'name')

"""
__Examples__
    
address-groups {
    group Addr_Grp-Static {
        description   desc;
        tag           [ tag ];
        address-list  [ Addr-IPv4 Addr-IPv4-WildcardMask Addr-IPv4-Range Addr-IPv4-FQDN ];
        address-files [ file.com ];
        type          static;
    }
    group Addr_Grp-Dynamic {
        description Desc;
        tag         [ Tag ];
        match Match-Term-1 {
            tags [ "This is a tag" "They are AND connected" ];
        }
        match Match-Term-2 {
            tags [ "There is an OR between Match Terms" ];
        }
        type        dynamic;
    }
}
"""
