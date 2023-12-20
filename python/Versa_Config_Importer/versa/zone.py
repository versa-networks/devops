"""
This module defines data classes for representing zones.

Classes:
    Zone: Represents a zone with various attributes.
    Zones: Represents a collection of Zone objects.
"""

from dataclasses import dataclass
import re
from typing import List, Optional
import constants as CONSTANT


@dataclass
class Zone:
    """
    Represents a zone with various attributes.

    Attributes:
        name (str): The name of the zone.
        description (Optional[str]): The description of the zone. Defaults to None.
        tag (Optional[List[str]]): The tags associated with the zone. Defaults to None.
        org (Optional[str]): The organization associated with the zone. Defaults to None.
        routing_instance (Optional[str]): The routing instance of the zone. Defaults to None.
    """

    name: str
    description: Optional[str] = None
    tag: Optional[List[str]] = None
    org: Optional[str] = None
    routing_instance: Optional[str] = None

    def __post_init__(self):
        if len(self.name) > CONSTANT.NAME_MAX_LENGTH:
            raise ValueError(f"name attribute is too long! Maximum length is {CONSTANT.NAME_MAX_LENGTH}")

        if not re.match(CONSTANT.NAME_VALID_REGEX, self.name):
            raise ValueError("name attribute should only contain alphanumeric characters, hyphens, and underscores")

        if len(self.description) > CONSTANT.DESC_MAX_LENGTH:
            raise ValueError(f"description attribute is too long! Maximum length is {CONSTANT.DESC_MAX_LENGTH}")

        if not re.match(CONSTANT.DESC_VALID_REGEX, self.description):
            raise ValueError("description attribute should only contain alphanumeric characters, hyphens, underscores, and spaces")


@dataclass
class Zones:
    """
    Represents a collection of Zone objects.

    Attributes:
        zones (List[Zone]): The list of Zone objects.
    """

    zones: List[Zone]


"""
__Example__

zones {
    zone Intf-INET-Zone;
    zone RTI-INET-Zone;
    zone Demo-Org {
        description Desc;
        tag         [ Tag ];
        org         RobK-Demo-1;
    }
    zone Demo-Rout {
        description      Desc;
        tag              [ Tag ];
        routing-instance RobK-Demo-1-Enterprise;
    }
    zone Demo-Intf {
        description Desc;
        tag         [ Tag ];
    }
}
"""
