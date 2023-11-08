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
        if _desc_line is not None:
            self.desc_line = _desc_line

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
        print(f"{_indent}}}", file=_cfg_fh)
