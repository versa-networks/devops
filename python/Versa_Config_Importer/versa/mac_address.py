"""
This module defines data classes for representing MAC addresses and related objects.

Classes:
    MacAddress: Represents a MAC address with its description and wildcard mask.
    MacObject: Represents an object that contains a MAC address and its type.
    MacAddresses: Represents a collection of MAC objects.
"""
from dataclasses import dataclass
import re
from typing import List
import constants as CONSTANT


@dataclass
class MacAddress:
    """
    Represents a MAC address with its description and wildcard mask.

    Attributes:
        address_type (str): The type of the MAC address (address or wildcard-mask).
        mac_address (str): The MAC address.
        description (str): The description of the MAC address.
        mac_address_with_wildcard_mask (str): The wildcard mask of the MAC address.

    Raises:
        ValueError: If the MAC address is not valid.
    """

    address_type: str  # address or wildcard-mask
    mac_address: str
    mac_address_with_wildcard_mask: str
    description: str

    def __post_init__(self):
        if self.address_type not in ["address", "wildcard-mask"]:
            raise ValueError(f"Invalid address type: {self.address_type}")
        if self.address_type == "address" and not re.match(CONSTANT.MAC_ADDRESS_VALID_REGEX, self.mac_address):
            raise ValueError(f"Invalid MAC address: {self.mac_address}")
        if self.address_type == "wildcard-mask":
            split_wildcard_address, split_wildcard_mask = self.mac_address_with_wildcard_mask.split("/")
            if not re.match(CONSTANT.MAC_ADDRESS_VALID_REGEX, split_wildcard_address) or not re.match(CONSTANT.MAC_ADDRESS_WILDCARD_MASKVALID_REGEX, split_wildcard_mask):
                raise ValueError(f"Invalid MAC address or wildcard mask: {self.mac_address_with_wildcard_mask}")


@dataclass
class MacObject:
    """
    Represents an object that contains a MAC address and its type.

    Attributes:
        name (str): The name of the object.
        mac_address (MacAddress): The MAC address of the object.
        cast_type (str): The type of the object (multicast or broadcast).
    """

    name: str
    mac_address: MacAddress
    cast_type: str  # multicast or broadcast

    def __post_init__(self):
        if self.cast_type not in ["multicast", "broadcast"]:
            raise ValueError(f"Invalid MAC object type: {self.cast_type}")


@dataclass
class MacAddresses:
    """
    Represents a collection of MAC objects.

    Attributes:
        mac_objects (List[MacObject]): The list of MAC objects.
    """

    mac_objects: List[MacObject]


"""
Example cfg
mac-addresses {
    mac-object MAC-Addr-Broadcast {
        address BC-09-1B-F8-7B-8F {
            description BlueTooth;
        }
        wildcard-mask BC:09:1B:F8:7B:8F/ff:ff:00:ff:00:00 {
            description "ff is considered";
        }
        broadcast;
    }
    mac-object MAC-Addr-Multicast {
        address BC:09:1B:F8:7B:8F {
            description Desc;
        }
        wildcard-mask BC:09:1B:F8:7B:8F/FF:FF:FF:FF:FF:00 {
            description Desc;
        }
        multicast;
    }
}
"""
