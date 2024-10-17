#
#  URLCategory.py - Versa URLCategory definition
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



class URLCategory(ConfigObject):

    def __init__(self, _name, _name_src_line, _is_predefined):
        super(URLCategory, self).__init__(
                                  _name, _name_src_line, _is_predefined)
        self.desc = None
        self.desc_line = None
        self.filename = None
        self.filename_line = None
        self.host_list = [ ]
        self.pattern_list = [ ]

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
        if (output_vd_cfg):
            vd_str = 'url-category '
        else:
            vd_str = ''

        print('%s    # src line number %d' % ( _indent, self.name_src_line), file=_cfg_fh)
        print('%s    %s%s {' % ( _indent, vd_str, self.name ), file=_cfg_fh)
        if (self.desc is not None):
            print('%s        # src line number %d' %
                  ( _indent, self.desc_line ), file=_cfg_fh)
            print('%s        category-description "%s";' %
                  ( _indent, self.desc ), file=_cfg_fh)
        if (self.filename is not None):
            print('%s        # src line number %d' %
                  ( _indent, self.filename_line ), file=_cfg_fh)
            print('%s        url-file "%s";' %
                  ( _indent, self.filename ), file=_cfg_fh)

        if (len(self.host_list) > 0 or len(self.pattern_list) > 0):
            print('%s        urls {' % ( _indent ), file=_cfg_fh)

        if (len(self.host_list) > 0):
            for h in self.host_list:
                print('%s            strings %s;' %
                      ( _indent, h ), file=_cfg_fh)

        if (len(self.pattern_list) > 0):
            for p in self.pattern_list:
                print('%s            patterns %s.*;' %
                      ( _indent, p ), file=_cfg_fh)

        if (len(self.host_list) > 0 or len(self.pattern_list) > 0):
            print('%s        }' % ( _indent ), file=_cfg_fh)

        print('%s    }' % ( _indent ), file=_cfg_fh)





