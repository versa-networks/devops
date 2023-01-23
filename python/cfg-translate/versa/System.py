#
#  System.py - Versa System definition
# 
#  This file has the definition of a network address object, that can be used
#  in any policy configuration on the Versa FlexVNF.
# 
#  Copyright (c) 2017, Versa Networks, Inc.
#  All rights reserved.
#

from __future__ import print_function
from versa.ConfigObject import ConfigObject
from enum import Enum



class System(ConfigObject):

    SYSTEM_NAME = 'system'

    def __init__(self):
        super(System, self).__init__(self.SYSTEM_NAME, 0, False)
        self.hostname = ''
        self.hostname_line = None
        self.domain_search = ''
        self.domain_search_line = None
        self.name_servers = [ ]
        self.name_servers_lines = [ ]

    def get_hostname(self):
        return self.hostname

    def set_hostname(self, _name, _line):
        self.hostname = _name
        self.hostname_line = _line

    def get_domain_search(self):
        return self.domain_search

    def set_domain_search(self, _ds, _line):
        self.domain_search = _ds
        self.domain_search_line = _line

    def get_name_servers(self):
        return self.name_servers

    def add_name_server(self, _ns, _line):
        self.name_servers.append(_ns)
        self.name_servers_lines.append(_line)

    def write_config(self, _cfg_fh, _log_fh, _indent):
        if (len(self.interface_map) > 0):
            print('%s    system {' % ( _indent ), file=_cfg_fh)
            print('%s        identification {' % ( _indent ), file=_cfg_fh)
            print('%s            name %s' % \
                              ( _indent, self.get_hostname() ), file=_cfg_fh)
            print('%s        }' % ( _indent ), file=_cfg_fh)
            print('%s    }' % ( _indent ), file=_cfg_fh)




