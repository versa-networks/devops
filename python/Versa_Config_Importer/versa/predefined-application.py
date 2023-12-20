"""
This module defines the data classes for representing predefined applications.

Each predefined application has a name, description, family, subfamily, productivity score, risk score, tags, precedence, timeout, match IPS flag, and match rules.
"""

from dataclasses import dataclass, field
import re
from typing import List
import constants as CONSTANT


@dataclass
class Port:
    """
    A class used to represent a Port.

    Attributes
    ----------
    value : int
        the value of the port
    low : int
        the lower limit of the port range
    high : int
        the upper limit of the port range
    """

    value: int = None
    low: int = None
    high: int = None

    def __post_init__(self):
        """
        Validates that the port values are between 0 and 65535, and that low is lower than high.
        """
        if self.value is not None and not (0 <= self.value <= 65535):
            raise ValueError("Port value must be between 0 and 65535")

        if self.low is not None and not (0 <= self.low <= 65535):
            raise ValueError("Low port value must be between 0 and 65535")

        if self.high is not None and not (0 <= self.high <= 65535):
            raise ValueError("High port value must be between 0 and 65535")

        if self.low is not None and self.high is not None and self.low < self.high:
            raise ValueError("Low port value must be lower than high port value")


@dataclass
class MatchRule:
    """
    A class used to represent a Match Rule.

    Attributes
    ----------
    host_pattern : str
        the host pattern of the match rule
    source_prefix : str
        the source prefix of the match rule
    destination_prefix : str
        the destination prefix of the match rule
    protocol : int
        the protocol of the match rule
    source_port : Port
        the source port of the match rule
    destination_port : Port
        the destination port of the match rule
    """

    host_pattern: str
    source_prefix: str
    destination_prefix: str
    protocol: int
    source_port: Port
    destination_port: Port


@dataclass
class PreDefinedApplication:
    """
    A class used to represent a Predefined Application.

    Attributes
    ----------
    name : str
        the name of the predefined application
    description : str
        a brief description of the predefined application
    family : str
        the family the predefined application belongs to
    subfamily : str
        the subfamily the predefined application belongs to
    productivity : int
        the productivity score associated with the predefined application
    risk : int
        the risk score associated with the predefined application
    tag : List[str]
        a list of tags associated with the predefined application
    precedence : int
        the precedence of the predefined application
    app_timeout : int
        the timeout of the predefined application
    app_match_ips : bool
        the match IPS flag of the predefined application
    app_match_rules : List[MatchRule]
        a list of match rules associated with the predefined application
    """

    name: str
    description: str
    family: str
    subfamily: str
    productivity: int
    risk: int
    tag: List[str] = field(default_factory=list)
    precedence: int
    app_timeout: int
    app_match_ips: bool
    app_match_rules: List[MatchRule] = field(default_factory=list)

    def __post_init__(self):
        if len(self.name) > CONSTANT.NAME_MAX_LENGTH:
            raise ValueError(f"name attribute is too long! Maximum length is {CONSTANT.NAME_MAX_LENGTH}")

        if not re.match(CONSTANT.NAME_VALID_REGEX, self.name):
            raise ValueError("name attribute should only contain alphanumeric characters, hyphens, and underscores")

        if self.description and len(self.description) > CONSTANT.DESC_MAX_LENGTH:
            raise ValueError(f"description attribute is too long! Maximum length is {CONSTANT.DESC_MAX_LENGTH}")

        if self.description and not re.match(CONSTANT.DESC_VALID_REGEX, self.description):
            raise ValueError("description attribute should only contain alphanumeric characters, hyphens, underscores, and spaces")

        if self.productivity and self.productivity not in CONSTANT.APPLICATION_PRODUCTIVITY_SCORES:
            raise ValueError(f"{self.productivity} is not a valid productivity score of 1 to 5")

        if self.risk and self.risk not in CONSTANT.APPLICATION_RISK_SCORES:
            raise ValueError(f"{self.risk} is not a valid risk score of 1 to 5")

        if not CONSTANT.APPLICATION_TIMEOUTS["low"] <= self.app_timeout <= CONSTANT.APPLICATION_TIMEOUTS["high"]:
            raise ValueError(f"app_timeout must be between {CONSTANT.APPLICATION_TIMEOUTS["low"]} and {CONSTANT.APPLICATION_TIMEOUTS["high"]}")

        if self.app_match_ips is not None and self.app_match_ips not in (True, False):
            raise ValueError("dynamic_address attribute should be None, True, or False")
        
        if self.family not in CONSTANT.APPLICATION_FAMILY_NAMES:
            raise ValueError(f"{self.family} is not a valid family name")

        if self.subfamily not in CONSTANT.APPLICATION_SUBFAMILY_NAMES:
            raise ValueError(f"{self.subfamily} is not a valid subfamily name")
        for tag in self.tag:
            if tag not in CONSTANT.APPLICATION_TAGS:
                raise ValueError(f"{tag} is not a valid tag")




"""
__Example___
predefined-applications {
    predefined-application Name {
        description   Desc;
        family        business-system;
        subfamily     antivirus;
        productivity  1;
        risk          1;
        tag           [ aaa adult_content advertising analytics anonymizer audio_chat basic blog cdn chat classified_ads cloud_services db dea_mail ebook_reader email enterprise file_mngt file_transfer forum gaming im_mc iot mm_streaming mobile networking news_portal p2p remote_access scada social_network standardized transportation update video_chat voip vpn_tun web web_ecom web_search web_sites webmail v_audio_stream v_av v_business v_cloud v_data v_ips v_non_business v_video_stream vs_anonymizer vs_bandwidth vs_dataleak vs_evasive vs_filetransfer vs_malware vs_misused vs_tunnel vs_vulnerable ];
        precedence    100;
        app-timeout   100;
        app-match-ips true;
        app-match-rules Match_Inform {
            host-pattern       Host.pattern;
            source-prefix      192.168.1.0/24;
            destination-prefix 192.168.2.1/32;
            protocol           1;
            source-port {
                value 1;
            }
            destination-port {
                low  1;
                high 3;
            }
        }
    }
}
"""
