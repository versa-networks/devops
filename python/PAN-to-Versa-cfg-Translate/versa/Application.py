#! /usr/bin/python
#  Application.py - Versa Application definition
#
#  This file has the definition of an application object, that can be used
#  in any policy configuration on the Versa FlexVNF.
#
#  Copyright (c) 2019, Versa Networks, Inc.
#  All rights reserved.
#
#  pylint: disable=invalid-name

from versa.ConfigObject import ConfigObject


class Application(ConfigObject):
    """Application _summary_

    Args:
        ConfigObject (_type_): _description_
    """

    def __init__(self, _name, _name_src_line, _is_predefined):
        super().__init__(_name, _name_src_line, _is_predefined)
        self.desc = None
        self.desc_line = None

    def get_description(self):
        return self.desc

    def set_description(self, _desc, _desc_line):
        self.desc = _desc
        self.desc_line = _desc_line

    def write_config(self, output_vd_cfg, _cfg_fh, _log_fh, _indent):
        """write_config
        _summary_

        Args:
            output_vd_cfg (_type_): _description_
            _cfg_fh (_type_): _description_
            _log_fh (_type_): unused
            _indent (_type_): _description_
        """
        if output_vd_cfg:
            vd_str = "user-defined-application "
        else:
            vd_str = ""

        #print(f"{_indent}    # src line number {self.name_src_line}", file=_cfg_fh)
        print(f"{_indent}    {vd_str}{self.name} {{", file=_cfg_fh)
        if self.desc is not None:
            #print(f"{_indent}        # src line number {self.desc_line}", file=_cfg_fh)
            print(f'{_indent}        description "{self.desc}";', file=_cfg_fh)
        print(f"{_indent}    }}", file=_cfg_fh)
