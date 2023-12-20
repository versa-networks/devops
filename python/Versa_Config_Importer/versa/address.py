"""
This module defines the Address data class and its validation.

The Address class represents an address with various attributes such as name, description, tag, ipv4, ipv4_wildcard_mask, ipv4_range, fqdn, dynamic_address, ipv6, and ipv6_wildcard_mask. 
Some of these attributes may not be applicable to all addresses, so they are marked as Optional and default to None.

The Address class also includes a __post_init__ method that validates the attributes. It checks the length of the name and description, and verifies that they only contain valid characters. 
It also checks that the ipv4, ipv4_wildcard_mask, ipv4_range, fqdn, dynamic_address, ipv6, and ipv6_wildcard_mask attributes, if they are not None, are in the correct format.
"""

from dataclasses import dataclass
import re
from typing import List, Optional
import constants as CONSTANT


@dataclass
class Address:
    """
    A class to represent an Address.

    Attributes
    ----------
    name : str
        the name of the address
    description : str
        a description of the address
    tag : List[str]
        a list of tags associated with the address
    ipv4_prefix : Optional[str]
        the IPv4 prefix of the address, if applicable
    ipv4_wildcard_mask : Optional[str]
        the IPv4 wildcard mask of the address, if applicable
    ipv4_range : Optional[str]
        the IPv4 range of the address, if applicable
    fqdn : Optional[str]
        the fully qualified domain name of the address, if applicable
    dynamic_address : Optional[bool]
        whether the address is dynamic, if applicable
    ipv6_prefix : Optional[str]
        the IPv6 prefix of the address, if applicable
    ipv6_wildcard_mask : Optional[str]
        the IPv6 wildcard mask of the address, if applicable
    """

    name: str
    description: str
    tag: List[str]
    ipv4: Optional[str] = None
    ipv4_wildcard_mask: Optional[str] = None
    ipv4_range: Optional[str] = None
    fqdn: Optional[str] = None
    dynamic_address: Optional[bool] = None
    ipv6: Optional[str] = None
    ipv6_wildcard_mask: Optional[str] = None

    def __post_init__(self):
        if len(self.name) > CONSTANT.NAME_MAX_LENGTH:
            raise ValueError(f"name attribute is too long! Maximum length is {CONSTANT.NAME_MAX_LENGTH}")

        if not re.match(CONSTANT.NAME_VALID_REGEX, self.name):
            raise ValueError("name attribute should only contain alphanumeric characters, hyphens, and underscores")

        if len(self.description) > CONSTANT.DESC_MAX_LENGTH:
            raise ValueError(f"description attribute is too long! Maximum length is {CONSTANT.DESC_MAX_LENGTH}")

        if not re.match(CONSTANT.DESC_VALID_REGEX, self.description):
            raise ValueError("description attribute should only contain alphanumeric characters, hyphens, underscores, and spaces")

        if self.ipv4 and not re.match(CONSTANT.IPV4_ADDR_CIDR_REGEX, self.ipv4):
            raise ValueError("ipv4 attribute should be a valid IPv4 prefix")
        if self.ipv4_wildcard_mask and not re.match(CONSTANT.IPV4_ADDR_WILDCARD_MASK, self.ipv4_wildcard_mask):
            raise ValueError("ipv4_wildcard_mask attribute should be a valid IPv4 wildcard mask")
        if self.ipv4_range and not re.match(CONSTANT.IPV4_ADDR_RANGE, self.ipv4_range):
            raise ValueError("ipv4_range attribute should be a valid IPv4 range")
        if self.fqdn and not re.match(CONSTANT.FQDN_REGEX, self.fqdn):
            raise ValueError("fqdn attribute should be a valid FQDN")
        if self.dynamic_address is not None and self.dynamic_address not in (True, False):
            raise ValueError("dynamic_address attribute should be None, True, or False")
        if self.ipv6 and not re.match(CONSTANT.IPV6_ADDR_REGEX, self.ipv6):
            raise ValueError("ipv6 attribute should be a valid IPv6 prefix")
        if self.ipv6_wildcard_mask and not re.match(CONSTANT.IPV6_ADDR_WILDCARD_MASK, self.ipv6_wildcard_mask):
            raise ValueError("ipv6_wildcard_mask attribute should be a valid IPv6 wildcard mask")


"""
_example_
addresses {
    address Deleteme {
        description Descript;
        ipv4-prefix 1.1.1.1/32;
    }
    address Addr-IPv4 {
        description Desc;
        tag         [ Tag ];
        ipv4-prefix 192.168.1.1/32;
    }
    address Addr-IPv4-WildcardMask {
        description        Desc;
        tag                [ Tags ];
        ipv4-wildcard-mask 192.168.3.100/255.255.3.255;
    }
    address Addr-IPv4-Range {
        description Desc;
        tag         [ Tag ];
        ipv4-range  192.168.1.1-192.168.4.255;
    }
    address Addr-IPv4-FQDN {
        description Desc;
        tag         [ Tag ];
        fqdn        versa-networks.com;
    }
    address Addr-DA {
        description     Desc;
        tag             [ Tag ];
        dynamic-address;
    }
    address Addr-IPv6 {
        description Desc;
        tag         [ Tag ];
        ipv6-prefix 2001:db8:abcd:0012::0/64;
    }
    address Addr-IPv6-Wildcard-Mask {
        description        Desc;
        tag                [ Tag ];
        ipv6-wildcard-mask 2001:0DB8:ABCD:0012:0000:0000:0000:0000/2001:0DB8:ABCD:0012:0000:0000:0000:0000;
    }
}
"""
