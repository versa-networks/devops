#
#  AddressGroup.py - Versa AddressGroup definition
# 
#  This file has the definition of a address group object, that can be used
#  in any policy configuration on the Versa FlexVNF.
# 
#  Copyright (c) 2017, Versa Networks, Inc.
#  All rights reserved.
#

from __future__ import print_function
from versa.ConfigObject import ConfigObject
from enum import Enum



class AddressGroup(ConfigObject):

    def __init__(self, _name, _name_src_line, _is_predefined):
        super(AddressGroup, self).__init__(
                                  _name, _name_src_line, _is_predefined)
        self.address_map = { }
        self.address_group_map = { }
        self.filename_map = { }

    def add_filename(self, _filename, _filename_src_line):
        self.filename_map[_filename] = _filename_src_line

    def set_filename_map(self, _filename_map):
        self.filename_map = _filename_map

    def add_address(self, _address, _address_src_line):
        self.address_map[_address] = _address_src_line

    def set_address_map(self, _address_map):
        self.address_map = _address_map

    def add_address_group(self, _address_group, _address_group_src_line):
        self.address_group_map[_address_group] = _address_group_src_line

    def set_address_group_map(self, _address_group_map):
        self.address_group_map = _address_group_map

    def add_group_members_to_list(self, _tnt, _ordered_list):
        for addr_grp, addr_grp_line in self.address_group_map.iteritems():
            _tnt.get_address_group(addr_grp). \
                               add_group_members_to_list(_tnt, _ordered_list)
            if (addr_grp not in _ordered_list):
                _ordered_list.extend([ addr_grp ])

    def replace_address_by_address_group(self, _address_group):
        if (_address_group in self.address_map):
            addr_grp_line = self.address_map[_address_group]
            self.address_map.pop(_address_group, None)
            self.address_group_map[_address_group] = addr_grp_line

    def replace_address(self, _aname, _new_aname):
        if (_aname in self.address_map):
            aline = self.address_map[_aname]
            self.address_map.pop(_aname, None)
            self.address_map[_new_aname] = aline

    def replace_address_group(self, _agname, _new_agname):
        if (_agname in self.address_group_map):
            aline = self.address_group_map[_agname]
            self.address_group_map.pop(_agname, None)
            self.address_group_map[_new_agname] = aline

    def listsAreEqual(self, a, b):
        for x in a:
            if x not in b:
                return False
        for x in b:
            if x not in a:
                return False
        return True

    def equals(self, _other):
        if (not self.listsAreEqual(self.address_map.keys(),
                                  _other.address_map.keys())):
            return False
        if (not self.listsAreEqual(self.address_group_map.keys(),
                                  _other.address_group_map.keys())):
            return False
        return True

    def write_config(self, output_vd_cfg, _cfg_fh, _log_fh, _indent):
        if (output_vd_cfg):
            vd_str = 'group '
        else:
            vd_str = ''
        print('%s    # src line number %d' % ( _indent, self.name_src_line ), file=_cfg_fh)
        print('%s    %s%s {' % ( _indent, vd_str, self.name ), file=_cfg_fh)

        if (len(self.address_map) > 0):
            print('%s        # src lines:' % ( _indent ),
                  end='', file=_cfg_fh)
            for addr, addr_line in self.address_map.iteritems():
                print(' ', end='', file=_cfg_fh)
                print(addr_line, end='', file=_cfg_fh)
            print('', file=_cfg_fh)

            print('%s        address-list [' % ( _indent ),
                  end='', file=_cfg_fh)

            for addr, addr_line in self.address_map.iteritems():
                print(' ', end='', file=_cfg_fh)
                print(addr, end='', file=_cfg_fh)

            print(' ];', file=_cfg_fh)

        if (len(self.address_group_map) > 0):
            print('%s        # src lines:' % ( _indent ),
                  end='', file=_cfg_fh)
            for addr_grp, addr_grp_line in self.address_group_map.iteritems():
                print(' ', end='', file=_cfg_fh)
                print(addr_grp_line, end='', file=_cfg_fh)
            print('', file=_cfg_fh)

            print('%s        address-group-list [' % ( _indent ),
                  end='', file=_cfg_fh)

            for addr_grp, addr_grp_line in self.address_group_map.iteritems():
                print(' ', end='', file=_cfg_fh)
                print(addr_grp, end='', file=_cfg_fh)

            print(' ];', file=_cfg_fh)

        if (len(self.filename_map) > 0):
            print('%s        # src lines:' % ( _indent ),
                  end='', file=_cfg_fh)
            for addr, addr_line in self.filename_map.iteritems():
                print(' ', end='', file=_cfg_fh)
                print(addr_line, end='', file=_cfg_fh)
            print('', file=_cfg_fh)

            print('%s        address-files [' % ( _indent ),
                  end='', file=_cfg_fh)

            for addr, addr_line in self.filename_map.iteritems():
                print(' ', end='', file=_cfg_fh)
                print(addr, end='', file=_cfg_fh)

            print(' ];', file=_cfg_fh)

        print('%s    }' % ( _indent ), file=_cfg_fh)





