#
#  ApplicationGroup.py - Versa ApplicationGroup definition
# 
#  This file has the definition of an application group object, that can be
#  used in any policy configuration on the Versa FlexVNF.
# 
#  Copyright (c) 2019, Versa Networks, Inc.
#  All rights reserved.
#

from __future__ import print_function
from versa.ConfigObject import ConfigObject
from enum import Enum



class ApplicationGroup(ConfigObject):

    def __init__(self, _name, _name_src_line, _is_predefined):
        super(ApplicationGroup, self).__init__(
                                  _name, _name_src_line, _is_predefined)
        self.application_map = { }
        self.application_group_map = { }

    def add_application(self, _application, _application_src_line):
        self.application_map[_application] = _application_src_line

    def get_application_map(self):
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
        for app, app_line in app_grp.application_map.iteritems():
            if (app.is_predefined()):
                if (app not in predef_app_list):
                    predef_app_list.append(app)
            else:
                if (app not in user_def_app_list):
                    user_def_app_list.append(app)

        for child_app_grp, child_app_grp_line in app_grp.application_group_map.iteritems():
            self.get_all_app_list(child_app_grp, predef_app_list, user_def_app_list)


    def write_config(self, output_vd_cfg, _cfg_fh, _log_fh, _indent):
        if (output_vd_cfg):
            vd_str = 'application-group '
        else:
            vd_str = ''

        print('%s    # src line number %d' % ( _indent, self.name_src_line ), file=_cfg_fh)
        print('%s    %s%s {' % ( _indent, vd_str, self.name ), file=_cfg_fh)

        predef_app_list = [ ]
        user_def_app_list = [ ]
        self.get_all_app_list(self, predef_app_list, user_def_app_list)

        if (len(predef_app_list) > 0):
            print('%s        predefined-application-list [' % ( _indent ),
                  end='', file=_cfg_fh)
            for a in predef_app_list:
                print(' %s' % a.name.upper(), end='', file=_cfg_fh)
            print(' ];', file=_cfg_fh)
        if (len(user_def_app_list) > 0):
            print('%s        user-defined-application-list [' % ( _indent ),
                  end='', file=_cfg_fh)
            for a in user_def_app_list:
                print(' %s' % a.name, end='', file=_cfg_fh)
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





