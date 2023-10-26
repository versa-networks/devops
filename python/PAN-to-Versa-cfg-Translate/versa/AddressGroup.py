# ! /usr/bin/python
#  AddressGroup.py - Versa AddressGroup definition
#
#  This file has the definition of a address group object, that can be used
#  in any policy configuration on the Versa FlexVNF.
#
#  Copyright (c) 2017, Versa Networks, Inc.
#  All rights reserved.
#
#  pylint: disable=invalid-name


from versa.ConfigObject import ConfigObject


class AddressGroup(ConfigObject):
    """AddressGroup
    _summary_

    Args:
        ConfigObject (_type_): _description_
    """

    def __init__(self, _name, _name_src_line, _is_predefined):
        super().__init__(_name, _name_src_line, _is_predefined)
        self.address_map = {}
        self.address_group_map = {}
        self.filename_map = {}
        self.desc = None
        self.desc_line = None

    def set_description(self, _desc, _desc_line):
        self.desc = _desc
        self.desc_line = _desc_line

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
        for addr_grp, addr_grp_line in self.address_group_map.items():
            _tnt.get_address_group(addr_grp).add_group_members_to_list(_tnt, _ordered_list)
            if addr_grp not in _ordered_list:
                _ordered_list.extend([addr_grp])

    def replace_address_by_address_group(self, _address_group):
        if _address_group in self.address_map:
            addr_grp_line = self.address_map[_address_group]
            self.address_map.pop(_address_group, None)
            self.address_group_map[_address_group] = addr_grp_line

    def replace_address(self, _aname, _new_aname):
        if _aname in self.address_map:
            aline = self.address_map[_aname]
            self.address_map.pop(_aname, None)
            self.address_map[_new_aname] = aline

    def replace_address_group(self, _agname, _new_agname):
        if _agname in self.address_group_map:
            aline = self.address_group_map[_agname]
            self.address_group_map.pop(_agname, None)
            self.address_group_map[_new_agname] = aline

    def listsAreEqual(self, a, b):
        """listsAreEqual _summary_

        Args:
            a (_type_): _description_
            b (_type_): _description_

        Returns:
            _type_: _description_
        """
        for x in a:
            if x not in b:
                return False
        for x in b:
            if x not in a:
                return False
        return True

    def equals(self, _other):
        """equals _summary_

        Args:
            _other (_type_): _description_

        Returns:
            _type_: _description_
        """
        if not self.listsAreEqual(list(self.address_map.keys()), list(_other.address_map.keys())):
            return False
        if not self.listsAreEqual(list(self.address_group_map.keys()), list(_other.address_group_map.keys())):
            return False
        return True

    def write_config(self, output_vd_cfg, _cfg_fh, _log_fh, _indent):
        """write_config _summary_

        Args:
            output_vd_cfg (_type_): _description_
            _cfg_fh (_type_): _description_
            _log_fh (_type_): _description_
            _indent (_type_): _description_
        """
        if output_vd_cfg:
            vd_str = "group "
        else:
            vd_str = ""
        print(f"{_indent}    # src line number {self.name_src_line}", file=_cfg_fh)
        print(f"{_indent}    {vd_str}{self.name} {{", file=_cfg_fh)
        if self.desc is not None:
            print(f"{_indent}        # src line number {self.desc_line}", file=_cfg_fh)
            print(f'{_indent}        description "{self.desc}";', file=_cfg_fh)
        if len(self.address_map) > 0:
            print(f"{_indent}        # src lines:", end="", file=_cfg_fh)
            for addr, addr_line in self.address_map.items():
                print(" ", end="", file=_cfg_fh)
                print(addr_line, end="", file=_cfg_fh)
            print("", file=_cfg_fh)

            print(f"{_indent}        address-list [", end="", file=_cfg_fh)

            for addr, addr_line in self.address_map.items():
                print(" ", end="", file=_cfg_fh)
                print(addr, end="", file=_cfg_fh)

            print(" ];", file=_cfg_fh)

        if len(self.address_group_map) > 0:
            print(f"{_indent}        # src lines:", end="", file=_cfg_fh)
            for addr_grp, addr_grp_line in self.address_group_map.items():
                print(" ", end="", file=_cfg_fh)
                print(addr_grp_line, end="", file=_cfg_fh)
            print("", file=_cfg_fh)

            print(f"{_indent}        address-group-list [", end="", file=_cfg_fh)

            for addr_grp, addr_grp_line in self.address_group_map.items():
                print(" ", end="", file=_cfg_fh)
                print(addr_grp, end="", file=_cfg_fh)

            print(" ];", file=_cfg_fh)

        if len(self.filename_map) > 0:
            print(f"{_indent}        # src lines:", end="", file=_cfg_fh)
            for addr, addr_line in self.filename_map.items():
                print(" ", end="", file=_cfg_fh)
                print(addr_line, end="", file=_cfg_fh)
            print("", file=_cfg_fh)

            print(f"{_indent}        address-files [", end="", file=_cfg_fh)

            for addr, addr_line in self.filename_map.items():
                print(" ", end="", file=_cfg_fh)
                print(addr, end="", file=_cfg_fh)

            print(" ];", file=_cfg_fh)

        print(f"{_indent}    }}", file=_cfg_fh)
