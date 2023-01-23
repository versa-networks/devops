#
#  Zone.py - Versa Zone definition
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



class Zone(ConfigObject):

    def __init__(self, _name, _name_src_line, _is_predefined):
        super(Zone, self).__init__(
                                  _name, _name_src_line, _is_predefined)
        self.interface_map = { }
        self.network_map = { }

    def add_interface(self, _interface, _interface_src_line):
        self.interface_map[_interface] = _interface_src_line

    def set_interface_map(self, _interface_map, _interface_map_src_line):
        self.interface_map = _interface_map
        self.interface_map_src_line = _interface_map_src_line

    def get_interface_map(self):
        return self.interface_map

    def add_network(self, _network, _network_src_line):
        self.network_map[_network] = _network_src_line

    def set_network_map(self, _network_map, _network_map_src_line):
        self.network_map = _network_map
        self.network_map_src_line = _network_map_src_line

    def get_network_map(self):
        return self.network_map

    def write_config(self, _cfg_fh, _log_fh, _indent, _print_name=True):
        pnflag = _print_name
        if (len(self.interface_map) > 0):
            if (pnflag):
                print('%s    %s {' % ( _indent, self.name ), file=_cfg_fh)
            print('%s        interface-list [ ' %
                  ( _indent ), end='', file=_cfg_fh)
            for k, v in self.interface_map.iteritems():
                print(' %s' % ( k ), end='', file=_cfg_fh)

            print(' ];', file=_cfg_fh)
            if (pnflag):
                print('%s    }' % ( _indent ), file=_cfg_fh)
                pnflag = False

        if (len(self.network_map) > 0):
            if (pnflag):
                print('%s    %s {' % ( _indent, self.name ), file=_cfg_fh)
            print('%s        networks [ ' %
                  ( _indent ), end='', file=_cfg_fh)
            for k, v in self.network_map.iteritems():
                print(' %s' % ( k ), end='', file=_cfg_fh)

            print(' ];', file=_cfg_fh)
            if (pnflag):
                print('%s    }' % ( _indent ), file=_cfg_fh)
                pnflag = False



