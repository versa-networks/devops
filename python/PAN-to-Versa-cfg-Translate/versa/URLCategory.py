#!/usr/bin/python
#  URLCategory.py - Versa URLCategory definition
#
#  This file has the definition of an application object, that can be used
#  in any policy configuration on the Versa FlexVNF.
#
#  Copyright (c) 2019, Versa Networks, Inc.
#  All rights reserved.
#
#  pylint: disable=invalid-name


from versa.ConfigObject import ConfigObject


class URLCategory(ConfigObject):
    """URLCategory _summary_

    Args:
        ConfigObject (_type_): _description_
    """

    def __init__(self, _name, _name_src_line, _is_predefined):
        super().__init__(_name, _name_src_line, _is_predefined)
        self.desc = None
        self.desc_line = None
        self.filename = None
        self.filename_line = None
        self.host_list = []
        self.pattern_list = []

    def get_description(self):
        return self.desc

    def set_description(self, _desc, _desc_line):
        self.desc = _desc
        self.desc_line = _desc_line

    def get_filename(self):
        return self.filename

    def set_filename(self, _filename, _filename_line):
        self.filename = _filename
        self.filename_line = _filename_line

    def add_host(self, _host):
        self.host_list.append(_host)

    def add_pattern(self, _pattern):
        self.pattern_list.append(_pattern)

    def write_config(self, output_vd_cfg, _cfg_fh, _log_fh, _indent):
        """write_config _summary_

        Args:
            output_vd_cfg (_type_): _description_
            _cfg_fh (_type_): _description_
            _log_fh (_type_): _description_
            _indent (_type_): _description_
        """
        if output_vd_cfg:
            vd_str = "url-category "
        else:
            vd_str = ""

        print(f"{_indent}    # src line number {self.name_src_line}", file=_cfg_fh)
        print(f"{_indent}    {vd_str}{self.name} {{", file=_cfg_fh)
        if self.desc is not None:
            print(f"{_indent}        # src line number {self.desc_line}", file=_cfg_fh)
            print(f'{_indent}        category-description "{self.desc}";', file=_cfg_fh)
        if self.filename is not None:
            print(f"{_indent}        # src line number {self.filename_line}", file=_cfg_fh)
            print(f'{_indent}        url-file "{self.filename}";', file=_cfg_fh)

        if len(self.host_list) > 0 or len(self.pattern_list) > 0:
            print(f"{_indent}        urls {{", file=_cfg_fh)

        if len(self.host_list) > 0:
            for h in self.host_list:
                print(f"{_indent}            strings {h};", file=_cfg_fh)

        if len(self.pattern_list) > 0:
            for p in self.pattern_list:
                print(f"{_indent}            patterns {p}.*;", file=_cfg_fh)

        if len(self.host_list) > 0 or len(self.pattern_list) > 0:
            print(f"{_indent}        }}", file=_cfg_fh)

        print(f"{_indent}    }}", file=_cfg_fh)
