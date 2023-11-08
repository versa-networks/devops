#! /usr/bin/python
#  ApplicationFilter.py - Versa ApplicationFilter definition
#
#  This file has the definition of an application filter object, that can be
#  used in any policy configuration on the Versa FlexVNF.
#
#  Copyright (c) 2023, Versa Networks, Inc.
#  All rights reserved.
#

from typing import Any, Dict, TextIO
from versa.ConfigObject import ConfigObject


class ApplicationFilter(ConfigObject):
    """
    Represents an application filter object that can be used in any policy configuration on the Versa FlexVNF.

    The ApplicationFilter class inherits from the ConfigObject class and adds additional attributes and methods related to
    the specific needs of an application filter object.

    Attributes:
        name (str): The name of the ApplicationFilter object.
        name_src_line (int): The source line of the ApplicationFilter object's name.
        is_predefined (bool): Whether the ApplicationFilter object is predefined or not.
        application_filter_map (dict): A dictionary that maps filter names to their values and source lines.
    """

    def __init__(self, _name: str, _name_src_line: int, _is_predefined: bool) -> None:
        """
        Initialize an ApplicationFilter object.

        Args:
            _name (str): The name of the ApplicationFilter object.
            _name_src_line (str): The source line of the ApplicationFilter object's name.
            _is_predefined (bool): Whether the ApplicationFilter object is predefined or not.

        Attributes:
            application_filter_map (Dict[str, Any]): A dictionary that maps filter names to their values and source lines.
        """
        super().__init__(_name, _name_src_line, _is_predefined)
        self.application_filter_map: Dict[str, Any] = {}

    def add_application_filter(self, _fltr_name: str, _fltr_val: str, _fltr_src_line: str) -> None:
        """Adds an application filter to the ApplicationFilter object.

        Args:
            _fltr_name (str): The name of the filter to add.
            _fltr_val (str): The value of the filter to add.
            _fltr_src_line (str): The source line of the filter.
        """
        if self.application_filter_map.get(_fltr_name) is None:
            self.application_filter_map[_fltr_name] = [[_fltr_val], _fltr_src_line]
        else:
            self.application_filter_map[_fltr_name][0].append(_fltr_val)

    def get_application_filter_map(self) -> Dict[str, Any]:
        """Returns the application filter map of the ApplicationFilter object."""
        return self.application_filter_map

    def set_application_filter_map(self, _application_filter_map: Dict[str, Any]) -> None:
        """Sets the application filter map of the ApplicationFilter object."""
        self.application_filter_map = _application_filter_map

    def write_config(self, output_vd_cfg: bool, _cfg_fh: TextIO, _indent: str) -> None:
        """Writes the configuration of the ApplicationFilter object to a file.

        Args:
            output_vd_cfg (bool): Whether to output the vd_cfg or not.
            _cfg_fh (TextIO): The file handler to write the configuration to.
            _indent (str): The indentation to use when writing the configuration.
        """
        vd_str = "application-filter " if output_vd_cfg else ""
        print(f"{_indent}{vd_str}{self.name} {{", file=_cfg_fh)

        for fn, fv in self.application_filter_map.items():
            print(f"{_indent}    {fn} [", end="", file=_cfg_fh)
            print(" ".join(fv[0]), end="", file=_cfg_fh)
            print(" ];", file=_cfg_fh)

        print(f"{_indent}}}", file=_cfg_fh)


"""
# Unused code
    predef_apps = [app.upper() for app in self.application_map if app.is_predefined()]
    userdef_apps = [app for app in self.application_map if not app.is_predefined()]

    if len(self.application_map) > 0:
        print(f"{_indent}        # src lines: {' '.join(str(line) for line in self.application_map.values())}", file=_cfg_fh)

        if predef_apps:
            print(f"{_indent}        predefined-application-list [ {' '.join(predef_apps)} ];", file=_cfg_fh)

        if userdef_apps:
            print(f"{_indent}        user-defined-application-list [ {' '.join(userdef_apps)} ];", file=_cfg_fh)

        print(f"{_indent}    }}", file=_cfg_fh)
"""
