#! /usr/bin/python
#  ApplicationGroup.py - Versa ApplicationGroup definition
#
#  This file has the definition of an application group object, that can be
#  used in any policy configuration on the Versa FlexVNF.
#
#  Copyright (c) 2023, Versa Networks, Inc.
#  All rights reserved.


from versa.ConfigObject import ConfigObject


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

    def __init__(self, name, is_predefined, desc=""):
        super().__init__(name, is_predefined, desc)
        self._application_map = {}
        self._application_group_map = {}

    def add_application(self, application):
        """
        Adds an application to the application map.

        Parameters:
        application (str): The name of the application.
        """
        self.application_map[application] = ""

    @property
    def application_map(self):
        """
        Returns the application map.

        Returns:
        dict: The application map.
        """
        return self._application_map

    @application_map.setter
    def application_map(self, application_map):
        """
        Sets the application map.

        Args:
        application_map (dict): The new application map.
        """
        self._application_map = application_map
        
    def add_application_group(self, _application_group):
        self.application_group_map[_application_group] = ""

    @property
    def application_group_map(self):
        """
        Returns the application group map.

        Returns:
        dict: The application group map.
        """
        return self._application_group_map

    @application_group_map.setter
    def application_group_map(self, application_group_map):
        """
        Sets the application group map.

        Args:
        application_group_map (dict): The new application group map.
        """
        self._application_group_map = application_group_map

    def get_all_app_list(self, app_grp):
        """
        Populates the provided lists with applications from the given application group.

        For each application in the application group, if the application is predefined, 
        it's added to the `predef_app_list` if it's not already there. If the application 
        is not predefined, it's added to the `user_def_app_list` if it's not already there.

        Args:
            app_grp: The application group to get applications from.
            predef_app_list: A list to populate with predefined applications.
            user_def_app_list: A list to populate with user-defined applications.
        """

        predef_app_list = [app for app in app_grp.application_map.items() if app.is_predefined()]
        user_def_app_list = [app for app in app_grp.application_map.items() if not app.is_predefined()]
        for child_app_grp in app_grp.application_group_map.items():
            predef_app_list.extend(self.get_all_app_list(child_app_grp))
            user_def_app_list.extend(self.get_all_app_list(child_app_grp))
        return list(set(predef_app_list)), list(set(user_def_app_list))

    def write_config(self, output_vd_cfg, cfg_fh, indent):
        """
        Writes the configuration of the application group to a file.

        Parameters:
        output_vd_cfg (bool): If True, prepend "application-group" to the output string.
        cfg_fh (file): File handler where the configuration will be written.
        indent (str): String of spaces for indentation.

        Returns:
        None
        """
        vd_str = "application-group " if output_vd_cfg else ""

        print(f"{indent}{vd_str}{self.name} {{", file=cfg_fh)

        predef_app_list, user_def_app_list = self.get_all_app_list(self)

        def print_app_list(app_list, list_type):
            if app_list:
                apps = " ".join(a.name.upper() if list_type == 'predefined' else a.name for a in app_list)
                print(f"{indent}    {list_type}-application-list [ {apps} ];", file=cfg_fh)

        print_app_list(predef_app_list, 'predefined')
        print_app_list(user_def_app_list, 'user-defined')

        print(f"{indent}}}", file=cfg_fh)
