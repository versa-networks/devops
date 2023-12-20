"""
This module defines the ApplicationGroup data class and its validation.

The ApplicationGroup class represents an application group with various attributes such as name, description, tag, predefined_application_list, and user_defined_application_list.

The ApplicationGroup class also includes a __post_init__ method that validates the attributes. It checks the length of the name and description, and verifies that they only contain valid characters.
"""

from dataclasses import dataclass
import re
from typing import List, Optional
import constants as CONSTANT

@dataclass
class ApplicationGroup:
    """
    A class to represent an Application Group.

    ...

    Attributes
    ----------
    name : str
        the name of the application group
    description : Optional[str]
        the description of the application group, None by default
    tag : List[str]
        a list of tags associated with the application group
    predefined_application_list : List[str]
        a list of predefined applications in the application group
    user_defined_application_list : List[str]
        a list of user-defined applications in the application group

    Methods
    -------
    __post_init__():
        Validates the attributes of the ApplicationGroup instance.
    """
    name: str
    description: Optional[str] = None
    tag: List[str] = []
    predefined_application_list: List[str] = []
    user_defined_application_list: List[str] = []

    def __post_init__(self):
        if len(self.name) > CONSTANT.NAME_MAX_LENGTH:
            raise ValueError(f"name attribute is too long! Maximum length is {CONSTANT.NAME_MAX_LENGTH}")

        if not re.match(CONSTANT.NAME_VALID_REGEX, self.name):
            raise ValueError("name attribute should only contain alphanumeric characters, hyphens, and underscores")

        if self.description and len(self.description) > CONSTANT.DESC_MAX_LENGTH:
            raise ValueError(f"description attribute is too long! Maximum length is {CONSTANT.DESC_MAX_LENGTH}")

        if self.description and not re.match(CONSTANT.DESC_VALID_REGEX, self.description):
            raise ValueError("description attribute should only contain alphanumeric characters, hyphens, underscores, and spaces")

        predefined_application_names = [app.name for app in predefined_applications]
        for app_name in self.predefined_application_list:
            if app_name not in predefined_application_names:
                raise ValueError(f"{app_name} is not a valid predefined application name")

        user_defined_application_names = [app.name for app in user_defined_applications]
        for app_name in self.user_defined_application_list:
            if app_name not in user_defined_application_names:
                raise ValueError(f"{app_name} is not a valid user defined application name")

"""
__Example
devices {
    template Escalated-Risk-Pathing-Policy {
        config {
            orgs {
                org-services RobK-Demo-1 {
                    application-identification {
                        application-groups {
                            application-group app_group {
                                description                   desc;
                                tag                           [ Tag ];
                                predefined-application-list   [ 0ZZ0 ];
                                user-defined-application-list [ Name ];
                            }
                        }
                    }
                }
            }
        }
    }
}
"""
