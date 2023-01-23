#
#  ApplicationFilter.py - Versa ApplicationFilter definition
# 
#  This file has the definition of an application filter object, that can be
#  used in any policy configuration on the Versa FlexVNF.
# 
#  Copyright (c) 2019, Versa Networks, Inc.
#  All rights reserved.
#

from __future__ import print_function
from versa.ConfigObject import ConfigObject
from enum import Enum



class ApplicationFilter(ConfigObject):

    def __init__(self, _name, _name_src_line, _is_predefined):
        super(ApplicationFilter, self).__init__(
                                  _name, _name_src_line, _is_predefined)
        self.application_filter_map = { }

    def add_application_filter(self, _fltr_name, _fltr_val, _fltr_src_line):
        # print('fn: %s; fv: %s; map: %s' % ( _fltr_name, _fltr_val, str(self.application_filter_map) ))
        if not _fltr_name in self.application_filter_map.keys():
            self.application_filter_map[_fltr_name] = \
                                  [ [ _fltr_val ], _fltr_src_line ]
        else:
            self.application_filter_map[_fltr_name][0].append(_fltr_val)

    def get_application_filter_map(self):
        return self.application_filter_map

    def set_application_filter_map(self, _application_filter_map):
        self.application_filter_map = _application_filter_map

    def write_config(self, output_vd_cfg, _cfg_fh, _log_fh, _indent):
        if (output_vd_cfg):
            vd_str = 'application-filter '
        else:
            vd_str = ''

        print('%s    # src line number %d' % ( _indent, self.name_src_line ), file=_cfg_fh)
        print('%s    %s%s {' % ( _indent, vd_str, self.name ), file=_cfg_fh)

        for fn, fv in self.application_filter_map.iteritems():
            print('%s        %s [' % ( _indent, fn ),
                  end='', file=_cfg_fh)
            for v in fv[0]:
                print(' %s' % v, end='', file=_cfg_fh)
            print(' ];', file=_cfg_fh)

        print('%s    }' % ( _indent ), file=_cfg_fh)
        return

        predef_flag = True
        userdef_flag = True
        if (len(self.application_map) > 0):
            print('%s        # src lines:' % ( _indent ),
                  end='', file=_cfg_fh)
            for app, app_line in self.application_map.iteritems():
                print(' ', end='', file=_cfg_fh)
                print(app_line, end='', file=_cfg_fh)
            print('', file=_cfg_fh)

            for app, app_line in self.application_map.iteritems():
                if (app.is_predefined()):
                    if (predef_flag):
                        print('%s        predefined-application-list [' % ( _indent ),
                              end='', file=_cfg_fh)
                        predef_flag = False
                    print(' ', end='', file=_cfg_fh)
                    print(app.upper(), end='', file=_cfg_fh)

            if (not predef_flag):
                print(' ];', file=_cfg_fh)

            for app, app_line in self.application_map.iteritems():
                if (not app.is_predefined()):
                    if (userdef_flag):
                        print('%s        user-defined-application-list [' % ( _indent ),
                              end='', file=_cfg_fh)
                        userdef_flag = False
                    print(' ', end='', file=_cfg_fh)
                    print(app, end='', file=_cfg_fh)

            if (not userdef_flag):
                print(' ];', file=_cfg_fh)

        print('%s    }' % ( _indent ), file=_cfg_fh)





