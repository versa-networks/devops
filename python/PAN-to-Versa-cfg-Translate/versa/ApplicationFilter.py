#! /usr/bin/python
#  ApplicationFilter.py - Versa ApplicationFilter definition
#
#  This file has the definition of an application filter object, that can be
#  used in any policy configuration on the Versa FlexVNF.
#
#  Copyright (c) 2019, Versa Networks, Inc.
#  All rights reserved.
#
#  pylint: disable=invalid-name

from versa.ConfigObject import ConfigObject


class ApplicationFilter(ConfigObject):
    """ApplicationFilter _summary_

    Args:
        ConfigObject (_type_): _description_
    """

    def __init__(self, _name, _name_src_line, _is_predefined):
        super(ApplicationFilter, self).__init__(_name, _name_src_line, _is_predefined)
        self.application_filter_map = {}

    def add_application_filter(self, _fltr_name, _fltr_val, _fltr_src_line):
        """add_application_filter_summary_

        Args:
            _fltr_name (_type_): _description_
            _fltr_val (_type_): _description_
            _fltr_src_line (_type_): _description_
        """
        # print('fn: %s; fv: %s; map: %s' % ( _fltr_name, _fltr_val, str(self.application_filter_map) ))
        if not _fltr_name in list(self.application_filter_map.keys()):
            self.application_filter_map[_fltr_name] = [[_fltr_val], _fltr_src_line]
        else:
            self.application_filter_map[_fltr_name][0].append(_fltr_val)

    def get_application_filter_map(self):
        return self.application_filter_map

    def set_application_filter_map(self, _application_filter_map):
        self.application_filter_map = _application_filter_map

    def write_config(self, output_vd_cfg, _cfg_fh, _log_fh, _indent):
        """write_config _summary_

        Args:
            output_vd_cfg (_type_): _description_
            _cfg_fh (_type_): _description_
            _log_fh (_type_): _description_
            _indent (_type_): _description_
        """
        if output_vd_cfg:
            vd_str = "application-filter "
        else:
            vd_str = ""

        print(f"{_indent}    # src line number {self.name_src_line}", file=_cfg_fh)
        print(f"{_indent}    {vd_str}{self.name} {{", file=_cfg_fh)

        for fn, fv in self.application_filter_map.items():
            print(f"f{_indent}        {fn} [", end="", file=_cfg_fh)
            for v in fv[0]:
                print(f" {v}", end="", file=_cfg_fh)
            print(" ];", file=_cfg_fh)

        print(f"{_indent}    }}", file=_cfg_fh)
        return


"""
# Unused code
        predef_flag = True
        userdef_flag = True
        if len(self.application_map) > 0:
            print("%s        # src lines:" % (_indent), end="", file=_cfg_fh)
            for app, app_line in self.application_map.items():
                print(" ", end="", file=_cfg_fh)
                print(app_line, end="", file=_cfg_fh)
            print("", file=_cfg_fh)

            for app, app_line in self.application_map.items():
                if app.is_predefined():
                    if predef_flag:
                        print(
                            "%s        predefined-application-list [" % (_indent),
                            end="",
                            file=_cfg_fh,
                        )
                        predef_flag = False
                    print(" ", end="", file=_cfg_fh)
                    print(app.upper(), end="", file=_cfg_fh)

            if not predef_flag:
                print(" ];", file=_cfg_fh)

            for app, app_line in self.application_map.items():
                if not app.is_predefined():
                    if userdef_flag:
                        print(
                            "%s        user-defined-application-list [" % (_indent),
                            end="",
                            file=_cfg_fh,
                        )
                        userdef_flag = False
                    print(" ", end="", file=_cfg_fh)
                    print(app, end="", file=_cfg_fh)

            if not userdef_flag:
                print(" ];", file=_cfg_fh)

        print("%s    }" % (_indent), file=_cfg_fh)
"""
