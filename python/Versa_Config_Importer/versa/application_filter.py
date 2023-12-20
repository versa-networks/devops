"""
This module defines the ApplicationFilter data class.

The ApplicationFilter class represents an application filter with its name, 
description, subfamily, and tag attributes. It also includes a method to 
represent the object as a string.


This module can be run directly or imported as a package.
"""
from dataclasses import dataclass, field
import re
from typing import List
import constants as CONSTANT

@dataclass
class ApplicationFilter:
    """
    A class used to represent an Application Filter.

    ...

    Attributes
    ----------
    name : str
        the name of the application filter
    description : str
        a brief description of the application filter
    family : List[str]
        a list of families the application filter belongs to
    subfamily : List[str]
        a list of subfamilies the application filter belongs to
    productivity : List[int]
        a list of productivity scores associated with the application filter
    risk : List[int]
        a list of risk scores associated with the application filter
    tag : List[str]
        a list of tags associated with the application filter

    Methods
    -------
    validate_attribute(attribute, max_length, valid_regex, attribute_name):
        Validates a single attribute based on its length and a regex pattern.
    validate_list_attribute(attribute_list, predefined_values, attribute_name):
        Validates a list of attributes based on a list of predefined values.
    """
    name: str
    description: str
    family: List[str] = field(default_factory=list)
    subfamily: List[str] = field(default_factory=list)
    productivity: List[int] = field(default_factory=list)
    risk: List[int] = field(default_factory=list)
    tag: List[str] = field(default_factory=list)

    PREDEFINED_FAMILY_NAMES = [app.family for app in predefined_applications]
    PREDEFINED_SUBFAMILY_NAMES = [app.subfamily for app in predefined_applications]
    APPLICATION_PRODUCTIVITY_SCORES = [app.productivity for app in predefined_applications]
    APPLICATION_RISK_SCORES = [app.risk for app in predefined_applications]
    PREDEFINED_TAGS = [app.tag for app in predefined_applications]

    def __post_init__(self):
        self.validate_attribute(self.name, CONSTANT.NAME_MAX_LENGTH, CONSTANT.NAME_VALID_REGEX, "name")
        self.validate_attribute(self.description, CONSTANT.DESC_MAX_LENGTH, CONSTANT.DESC_VALID_REGEX, "description")
        self.validate_list_attribute(self.family, self.PREDEFINED_FAMILY_NAMES, "family")
        self.validate_list_attribute(self.subfamily, self.PREDEFINED_SUBFAMILY_NAMES, "subfamily")
        self.validate_list_attribute(self.productivity, self.APPLICATION_PRODUCTIVITY_SCORES, "productivity")
        self.validate_list_attribute(self.risk, self.APPLICATION_RISK_SCORES, "risk")
        self.validate_list_attribute(self.tag, self.PREDEFINED_TAGS, "tag")

    def validate_attribute(self, attribute, max_length, valid_regex, attribute_name):
        """
        Validates a single attribute based on its length and a regex pattern.

        Args:
            attribute (str): The attribute to validate.
            max_length (int): The maximum length of the attribute.
            valid_regex (str): The regex pattern the attribute should match.
            attribute_name (str): The name of the attribute (used in error messages).

        Raises:
            ValueError: If the attribute is too long or doesn't match the regex pattern.
        """
        if len(attribute) > max_length:
            raise ValueError(f"{attribute_name} attribute is too long! Maximum length is {max_length}")

        if not re.match(valid_regex, attribute):
            raise ValueError(f"{attribute_name} attribute contains invalid characters")

    def validate_list_attribute(self, attribute_list, predefined_values, attribute_name):
        """
        Validates a list of attributes based on a list of predefined values.

        Args:
            attribute_list (list): The list of attributes to validate.
            predefined_values (list): The list of predefined valid values.
            attribute_name (str): The name of the attribute (used in error messages).

        Raises:
            ValueError: If any attribute in the list is not in the predefined values.
        """
        for attribute in attribute_list:
            if attribute not in predefined_values:
                raise ValueError(f"{attribute} is not a valid predefined {attribute_name}")


"""
_Example_
application-filters {
    application-filter App-filter {
        description desc;
        subfamily   [ peer-to-peer ];
        tag         [ vs_anonymizer vs_bandwidth vs_dataleak vs_evasive vs_filetransfer vs_malware vs_misused vs_tunnel vs_vulnerable ];
    }
     application-filter Name2 {
        description  DESC;
        family       [ business-system general-internet networking media ];
        subfamily    [ antivirus audio_video database compression authentication application-service behavioral encrypted network-management microsoft-office middleware mail ];
        productivity [ 1 ];
        risk         [ 1 ];
        tag          [ aaa adult_content advertising analytics anonymizer audio_chat basic blog cdn chat classified_ads cloud_services db dea_mail ebook_reader email enterprise file_mngt file_transfer forum gaming im_mc iot mm_streaming mobile networking news_portal p2p remote_access scada social_network standardized transportation update video_chat voip vpn_tun web web_ecom web_search web_sites webmail v_audio_stream v_av v_business v_cloud v_data v_ips v_non_business v_video_stream vs_anonymizer vs_bandwidth vs_dataleak vs_evasive vs_filetransfer vs_malware vs_misused vs_tunnel vs_vulnerable ];
    }
}
"""
