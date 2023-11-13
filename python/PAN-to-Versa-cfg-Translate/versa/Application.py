#! /usr/bin/python
#  Application.py - Versa Application definition
#
#  This file has the definition of an application object, that can be used
#  in any policy configuration on the Versa FlexVNF.
#
#  Copyright (c) 2023, Versa Networks, Inc.
#  All rights reserved.
#

from typing import Optional, TextIO
from versa.ConfigObject import ConfigObject


class Application(ConfigObject):
    """
    Represents an application object that can be used in any policy configuration on the Versa FlexVNF.

    The Application class inherits from the ConfigObject class and adds additional attributes and methods related to
    the specific needs of an application object.

    Attributes:
        name (str): The name of the Application object.
        name_src_line (int): The source line of the Application object's name.
        is_predefined (bool): Whether the Application object is predefined or not.
        desc (Optional[str]): The description of the Application object, defaults to None.
        desc_line (Optional[str]): The source line of the Application object's description, defaults to None.
    """

    def __init__(self, _name: str, _name_src_line: int, _is_predefined: bool) -> None:
        """
        Initialize an Application object.

        Args:
            _name (str): The name of the Application object.
            _name_src_line (int): The source line of the Application object's name.
            _is_predefined (bool): Whether the Application object is predefined or not.

        Attributes:
            desc (Optional[str]): The description of the Application object, defaults to None.
            desc_line (Optional[str]): The source line of the Application object's description, defaults to None.
        """
        super().__init__(_name, _name_src_line, _is_predefined)
        self.desc: Optional[str] = None
        self.desc_line: Optional[int] = None
        self.family: Optional[str] = None
        self.subfamily: Optional[str] = None
        self.risk: Optional[str] = None
        self.tag: Optional[str] = None
        self.precedence: Optional[int] = 100
        # How should precedence be hanlded?
        self.app_timeout: Optional[int] = None
        self.app_match_ips: Optional[bool] = None
        self.app_tags: Optional[str] = None
        self.app_match_rules = []

    def get_description(self) -> str:
        """Returns the description of the Application object."""
        return self.desc if self.desc is not None else ""

    def set_description(self, _desc: str, _desc_line: int) -> None:
        """
        Sets the description and its source line for the Application object.

        Args:
            _desc (str): The description to be set.
            _desc_line (int): The source line of the description.
        """
        if _desc is not None:
            self.desc = _desc

    def get_family(self) -> str:
        """Returns the family of the Application object."""
        return self.family if self.family is not None else ""

    def set_family(self, _family: str, _family_line: int) -> None:
        """
        Sets the family and its source line for the Application object.

        Args:
            _family (str): The family to be set.
            _family_line (int): The source line of the family.
        """
        if _family is not None:
            self.family = _family

    def get_subfamily(self) -> str:
        """Returns the subfamily of the Application object."""
        return self.subfamily if self.subfamily is not None else ""

    def set_subfamily(self, _subfamily: str, _subfamily_line: int) -> None:
        """
        Sets the subfamily and its source line for the Application object.

        Args:
            _subfamily (str): The subfamily to be set.
            _subfamily_line (int): The source line of the subfamily.
        """
        if _subfamily is not None:
            self.subfamily = _subfamily

    def get_risk(self) -> str:
        """Returns the risk of the Application object."""
        return self.risk if self.risk is not None else ""

    def set_risk(self, _risk: str) -> None:
        """
        Sets the risk and its source line for the Application object.

        Args:
            _risk (str): The risk to be set.
        """
        if _risk is not None:
            self.risk = _risk

    def get_tag(self) -> str:
        """Returns the tag of the Application object."""
        return self.tag if self.tag is not None else ""

    def set_tag(self, _tag: str) -> None:
        """
        Sets the tag and its source line for the Application object.

        Args:
            _tag (str): The tag to be set.
        """
        if _tag is not None:
            self.tag = _tag

    def get_precedence(self) -> int:
        """Returns the precedence of the Application object."""
        return self.precedence if self.precedence is not None else ""

    def set_precedence(self, _precedence: int) -> None:
        """
        Sets the precedence for the Application object.

        Args:
            _precedence (int): The precedence to be set.
        """
        if _precedence is not None:
            self.precedence = _precedence

    def get_app_timeout(self) -> int:
        """Returns the app_timeout of the Application object."""
        return self.app_timeout if self.app_timeout is not None else ""

    def set_app_timeout(self, _app_timeout: int) -> None:
        """
        Sets the app_timeout for the Application object.

        Args:
            _app_timeout (int): The app_timeout to be set.
        """
        if _app_timeout is not None:
            self.app_timeout = _app_timeout

    def get_app_match_ips(self) -> bool:
        """Returns the app_match_ips of the Application object."""
        return self.app_match_ips if self.app_match_ips is not None else ""

    def set_app_match_ips(self, _app_match_ips: bool) -> None:
        """
        Sets the app_match_ips and its source line for the Application object.

        Args:
            _app_match_ips (bool): The app_match_ips to be set.
        """
        if _app_match_ips is not None:
            self.app_match_ips = _app_match_ips

    def attach_app_match_rule(self, app_match_rules):
        self.app_match_rules.append(app_match_rules)

    def write_config(self, output_vd_cfg: bool, _cfg_fh: TextIO, _indent: str) -> None:
        """Writes the configuration of the Application object to a file.

        Args:
            output_vd_cfg (bool): Whether to output the vd_cfg or not.
            _cfg_fh (TextIO): The file handler to write the configuration to.
            _indent (str): The indentation to use when writing the configuration.
        """
        vd_str = "user-defined-application " if output_vd_cfg else ""

        print(f"{_indent}{vd_str}{self.name} {{", file=_cfg_fh)
        if self.desc is not None:
            print(f'{_indent}    description "{self.desc}";', file=_cfg_fh)
        if self.family is not None:
            print(f"{_indent}    family {self.family};", file=_cfg_fh)
        if self.subfamily is not None:
            print(f"{_indent}    subfamily {self.subfamily};", file=_cfg_fh)
        if self.tag is not None:
            print(f"{_indent}    tag [ {self.tag} ];", file=_cfg_fh)
        if self.risk is not None:
            print(f"{_indent}    risk {self.risk};", file=_cfg_fh)
        if self.precedence is not None:
            print(f"{_indent}    precedence {self.precedence};", file=_cfg_fh)
        if self.app_timeout is not None or self.app_timeout != 0:
            print(f"{_indent}    app-timeout {self.app_timeout};", file=_cfg_fh)
        if self.app_match_ips is not None and self.app_match_ips:
            print(f"{_indent}    app-match-ips {self.app_match_ips};", file=_cfg_fh)
        for app_match_rule in self.app_match_rules:
            app_match_rule.write_config(output_vd_cfg, _cfg_fh, _indent + "    ")
        print(f"{_indent}}}", file=_cfg_fh)


"""
Example Versa Application configuration:
user-defined-application BLADELOGIC {
    description   PWHOBLADELOGIC-DRQS7541625-TREQ575503-RL;
    family        business-system;
    subfamily     standard;
    risk          1;
    tag           [ vs_malware ];
    precedence    100;
    app-timeout   600;
    app-match-ips true;
    app-match-rules PORT-TCP-27829 {
        host-pattern       host-patter;
        source-prefix      192.168.1.1/24;
        destination-prefix 192.168.10.10/32;
        protocol           6;
        source-port {
            low  1;
            high 10;
        }
        destination-port {
            value 27829;
        }
    }
}
"""


class AppMatchRules(ConfigObject):
    """
    A class used to represent application match rules.

    ...

    Attributes
    ----------
    host_pattern : str
        a string that represents the host pattern
    source_prefix : str
        a string that represents the source prefix
    destination_prefix : str
        a string that represents the destination prefix
    protocol : int
        an integer that represents the protocol
    source_port_low : str
        a string that represents the low source port
    source_port_high : int
        an integer that represents the high source port
    source_port_value : str
        a string that represents the source port value
    destination_port_low : int
        an integer that represents the low destination port
    destination_port_high : int
        an integer that represents the high destination port
    destination_port_value : str
        a string that represents the destination port value

    Methods
    -------
    get_protocol():
        Returns the protocol if it is not None, else returns an empty string.
    set_protocol(_protocol):
        Sets the protocol if the provided _protocol is not None.
    get_destination_port_value():
        Returns the destination port value if it is not None, else returns an empty string.
    set_destination_port_value(_destination_port_value):
        Sets the destination port value if the provided _destination_port_value is not None.
    get_destination_port_high():
        Returns the destination port high if it is not None, else returns an empty string.
    set_destination_port_high(_destination_port_high):
        Sets the destination port high if the provided _destination_port_high is not None.
    get_destination_port_low():
        Returns the destination port low if it is not None, else returns an empty string.
    set_destination_port_low(_destination_port_low):
        Sets the destination port low if the provided _destination_port_low is not None.
    """

    def __init__(self, _name: str, _name_src_line: int, _is_predefined: bool) -> None:
        super().__init__(_name, _name_src_line, _is_predefined)
        self.host_pattern: Optional[str] = None
        self.source_prefix: Optional[str] = None
        self.destination_prefix: Optional[str] = None
        self.protocol: Optional[int] = None
        self.source_port_low: Optional[str] = None
        self.source_port_high: Optional[int] = None
        self.source_port_value: Optional[str] = None
        self.destination_port_low: Optional[int] = None
        self.destination_port_high: Optional[int] = None
        self.destination_port_value: Optional[str] = None

    def get_protocol(self):
        return self.protocol if self.protocol is not None else ""

    def set_protocol(self, _protocol):
        if _protocol is not None:
            self.protocol = _protocol

    def get_destination_port_value(self):
        return self.destination_port_value if self.destination_port_value is not None else ""

    def set_destination_port_value(self, _destination_port_value):
        if _destination_port_value is not None:
            self.destination_port_value = _destination_port_value

    def get_destination_port_high(self):
        return self.destination_port_high if self.destination_port_high is not None else ""

    def set_destination_port_high(self, _destination_port_high):
        if _destination_port_high is not None:
            self.destination_port_high = _destination_port_high

    def get_destination_port_low(self):
        return self.destination_port_low if self.destination_port_low is not None else ""

    def set_destination_port_low(self, _destination_port_low):
        if _destination_port_low is not None:
            self.destination_port_low = _destination_port_low

    def write_config(self, output_vd_cfg: bool, _cfg_fh: TextIO, _indent: str) -> None:
        """Writes the configuration of the Application App Match object to a file.

        Args:
            output_vd_cfg (bool): Whether to output the vd_cfg or not.
            _cfg_fh (TextIO): The file handler to write the configuration to.
            _indent (str): The indentation to use when writing the configuration.
        """
        if self.name is not None:
            print(f"{_indent}app-match-rules {self.name} {{", file=_cfg_fh)
            if self.host_pattern is not None:
                print(f"{_indent}    host-pattern {self.host_pattern};", file=_cfg_fh)
            if self.source_prefix is not None:
                print(f"{_indent}    source-prefix {self.source_prefix};", file=_cfg_fh)
            if self.destination_prefix is not None:
                print(f"{_indent}    destination-prefix {self.destination_prefix};", file=_cfg_fh)
            if self.protocol is not None:
                print(f"{_indent}    protocol {self.protocol};", file=_cfg_fh)
            if self.source_port_low is not None and self.source_port_high is not None:
                print(f"{_indent}    source-port {{", file=_cfg_fh)
                print(f"{_indent}        low {self.source_port_low};", file=_cfg_fh)
                print(f"{_indent}        high {self.source_port_high};", file=_cfg_fh)
                print(f"{_indent}    }}", file=_cfg_fh)
            if self.destination_port_value is not None:
                print(f"{_indent}    destination-port {{", file=_cfg_fh)
                print(f"{_indent}        value {self.destination_port_value};", file=_cfg_fh)
                print(f"{_indent}    }}", file=_cfg_fh)

            if self.destination_port_low is not None and self.destination_port_high is not None:
                print(f"{_indent}    destination-port {{", file=_cfg_fh)
                print(f"{_indent}        low {self.destination_port_low};", file=_cfg_fh)
                print(f"{_indent}        high {self.destination_port_high};", file=_cfg_fh)
                print(f"{_indent}    }}", file=_cfg_fh)
            print(f"{_indent}}}", file=_cfg_fh)

            """"
        app-match-rules PORT-TCP-27829 {
        host-pattern       host-patter;
        source-prefix      192.168.1.1/24;
        destination-prefix 192.168.10.10/32;
        protocol           6;
        source-port {
            low  1;
            high 10;
        }
        destination-port {
            value 27829;
        }
    }
}
"""
