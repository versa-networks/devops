#!/usr/bin/python
#  URLCategory.py - Versa URLCategory definition
#
#  This file has the definition of an application object, that can be used
#  in any policy configuration on the Versa FlexVNF.
#
#  Copyright (c) 2023, Versa Networks, Inc.
#  All rights reserved.
#


from versa.ConfigObject import ConfigObject


class URLCategory(ConfigObject):
    """
    Represents a URL category that can be used in any policy configuration on the Versa FlexVNF.

    Inherits from ConfigObject.

    Attributes:
    name (str): The name of the URL category.
    is_predefined (bool): Whether the URL category is predefined or not.
    desc (str): The description of the URL category.
    filename (str): The filename of the URL category.
    host_list (list): A list of hosts in the URL category.
    pattern_list (list): A list of patterns in the URL category.
    """

    def __init__(self, name,  is_predefined):
        """
        Initialize a URLCategory instance.

        Parameters:
        name (str): The name of the URL category.
        is_predefined (bool): Whether the URL category is predefined or not.
        """
        super().__init__(name, is_predefined)
        self.desc = None
        self.filename = None
        self.host_list = []
        self.pattern_list = []

    def get_description(self):
        return self.desc

    def set_description(self, _desc):
        self.desc = _desc

    def get_filename(self):
        return self.filename

    def set_filename(self, _filename):
        self.filename = _filename

    def add_host(self, _host):
        self.host_list.append(_host)

    def add_pattern(self, _pattern):
        self.pattern_list.append(_pattern)

    def write_config(self, output_vd_cfg, cfg_fh, indent):
        """
        Writes the configuration of the URL category to a file.

        Parameters:
        output_vd_cfg (bool): If True, prepend "url-category" to the output.
        cfg_fh (file): File handler where the configuration will be written.
        indent (str): String of spaces for indentation.
        """
        vd_str = "url-category " if output_vd_cfg else ""

        print(f"{indent}    {vd_str}{self.name} {{", file=cfg_fh)

        if self.desc is not None:
            print(f'{indent}        category-description "{self.desc}";', file=cfg_fh)

        if self.filename is not None:
            print(f'{indent}        url-file "{self.filename}";', file=cfg_fh)

        if self.host_list or self.pattern_list:
            print(f"{indent}        urls {{", file=cfg_fh)

            for h in self.host_list:
                print(f"{indent}            strings {h};", file=cfg_fh)

            for p in self.pattern_list:
                print(f"{indent}            patterns {p}.*;", file=cfg_fh)

            print(f"{indent}        }}", file=cfg_fh)

        print(f"{indent}    }}", file=cfg_fh)
