#! /usr/bin/python
#  ApplicationGroup.py - Versa ApplicationGroup definition
#
#  This file has the definition of an application group object, that can be
#  used in any policy configuration on the Versa FlexVNF.
#
#  Copyright (c) 2023, Versa Networks, Inc.
#  All rights reserved.


from versa.ConfigObject import ConfigObject
from enum import Enum


class ApplicationGroup(ConfigObject):
    """
    Represents an application group in the configuration.

    Attributes:
    application_map (dict): A map of applications to their source lines.
    application_group_map (dict): A map of application groups to their source lines.

    Methods:
    add_application(_application, _application_src_line): Adds an application to the application map.
    get_application_map(): Returns the application map.
    set_application_map(_application_map): Sets the application map.
    add_application_group(_application_group, _application_group_src_line): Adds an application group to the application group map.
    get_application_group_map(): Returns the application group map.
    set_application_group_map(_application_group_map): Sets the application group map.
    get_all_app_list(app_grp, predef_app_list, user_def_app_list): Gets all applications in the application group and its child groups.
    write_config(output_vd_cfg, _cfg_fh, _indent): Writes the configuration of the application group to a file.
    """

    def __init__(self, name, name_src_line, is_predefined):
        """
        Initialize an ApplicationGroup instance.

        Parameters:
        name (str): The name of the application group.
        name_src_line (int): The source line where the name was defined.
        is_predefined (bool): Whether the application group is predefined or not.
        """
        super().__init__(name, name_src_line, is_predefined)
        self.application_map = {}
        self.application_group_map = {}

    def add_application(self, application, application_src_line):
        """
        Adds an application to the application map.

        Parameters:
        application (str): The name of the application.
        application_src_line (int): The source line where the application was defined.
        """
        self.application_map[application] = application_src_line

    def get_application_map(self):
        """
        Returns the application map.

        Returns:
        dict: The application map.
        """
        return self.application_map

    def set_application_map(self, _application_map):
        self.application_map = _application_map

    def add_application_group(self, _application_group, _application_group_src_line):
        self.application_group_map[_application_group] = _application_group_src_line

    def get_application_group_map(self):
        return self.application_group_map

    def set_application_group_map(self, _application_group_map):
        self.application_group_map = _application_group_map

    def get_all_app_list(self, app_grp, predef_app_list, user_def_app_list):
        for app, app_line in app_grp.application_map.items():
            if app.is_predefined():
                if app not in predef_app_list:
                    predef_app_list.append(app)
            else:
                if app not in user_def_app_list:
                    user_def_app_list.append(app)

        for child_app_grp, child_app_grp_line in app_grp.application_group_map.items():
            self.get_all_app_list(child_app_grp, predef_app_list, user_def_app_list)

    def write_config(self, output_vd_cfg, _cfg_fh, _indent):
        """
        Writes the configuration of the application group to a file.

        Parameters:
        output_vd_cfg (bool): If True, prepend "application-group" to the output string.
        _cfg_fh (file): File handler where the configuration will be written.
        _indent (str): String of spaces for indentation.

        Returns:
        None
        """
        vd_str = "application-group " if output_vd_cfg else ""

        print(f"{_indent}{vd_str}{self.name} {{", file=_cfg_fh)

        predef_app_list = []
        user_def_app_list = []
        self.get_all_app_list(self, predef_app_list, user_def_app_list)

        if predef_app_list:
            apps = " ".join(a.name.upper() for a in predef_app_list)
            print(f"{_indent}    predefined-application-list [ {apps} ];", file=_cfg_fh)
        if user_def_app_list:
            apps = " ".join(a.name for a in user_def_app_list)
            print(f"{_indent}    user-defined-application-list [ {apps} ];", file=_cfg_fh)

        print(f"{_indent}}}", file=_cfg_fh)
        return


"""
#Unused
    if self.application_map:
        print(f"{_indent}        # src lines: {' '.join(str(line) for line in self.application_map.values())}", file=_cfg_fh)

        predef_apps = [app.upper() for app in self.application_map if app.is_predefined()]
        userdef_apps = [app for app in self.application_map if not app.is_predefined()]

        if predef_apps:
            print(f"{_indent}        predefined-application-list [ {' '.join(predef_apps)} ];", file=_cfg_fh)

        if userdef_apps:
            print(f"{_indent}        user-defined-application-list [ {' '.join(userdef_apps)} ];", file=_cfg_fh)

    print(f"{_indent}    }}", file=_cfg_fh)
"""
