#
#  Application.py - Versa Application definition
# 
#  This file has the definition of an application object, that can be used
#  in any policy configuration on the Versa FlexVNF.
# 
#  Copyright (c) 2019, Versa Networks, Inc.
#  All rights reserved.
#

from __future__ import print_function
from versa.ConfigObject import ConfigObject
from enum import Enum



class Application(ConfigObject):

    def __init__(self, _name, _name_src_line, _is_predefined):
        super(Application, self).__init__(
                                  _name, _name_src_line, _is_predefined)
        self.desc = None
        self.desc_line = None

    def get_description(self):
        return self.desc

    def set_description(self, _desc, _desc_line):
        self.desc = _desc
        self.desc_line = _desc_line

    def write_config(self, output_vd_cfg, _cfg_fh, _log_fh, _indent):
        if (output_vd_cfg):
            vd_str = 'user-defined-application '
        else:
            vd_str = ''

        print('%s    # src line number %d' % ( _indent, self.name_src_line), file=_cfg_fh)
        print('%s    %s%s {' % ( _indent, vd_str, self.name ), file=_cfg_fh)
        if (self.desc is not None):
            print('%s        # src line number %d' %
                  ( _indent, self.desc_line ), file=_cfg_fh)
            print('%s        description "%s";' %
                  ( _indent, self.desc ), file=_cfg_fh)
        print('%s    }' % ( _indent ), file=_cfg_fh)





