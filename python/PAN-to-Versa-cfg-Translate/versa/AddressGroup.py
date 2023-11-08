# ! /usr/bin/python
#  AddressGroup.py - Versa AddressGroup definition
#
#  This file has the definition of a address group object, that can be used
#  in any policy configuration on the Versa FlexVNF.
#
#  Copyright (c) 2023, Versa Networks, Inc.
#  All rights reserved.
#

from typing import Dict, Optional
from versa.ConfigObject import ConfigObject


class AddressGroup(ConfigObject):
    """
    The AddressGroup class inherits from the ConfigObject class and represents a group of addresses in a network configuration.

    An AddressGroup object has the following attributes:
    - name: The name of the address group.
    - name source line: The line in the source file where the name is defined.
    - predefined status: A boolean indicating whether the address group is predefined or not.
    - address map: A dictionary mapping addresses to their source lines.
    - address group map: A dictionary mapping address groups to their source lines.
    - filename map: A dictionary mapping filenames to their source lines.
    - description: A description of the address group.
    - description source line: The line in the source file where the description is defined.

    The AddressGroup class provides methods for setting and getting these attributes, adding and removing addresses and address groups, checking equality of address groups, and writing the address group configuration to a file.
    """

    def __init__(self, _name: str, _name_src_line: int, _is_predefined: bool) -> None:
        """
        Initializes an AddressGroup object.

        Args:
            _name (str): The name of the AddressGroup.
            _name_src_line (str): The source line of the name.
            _is_predefined (bool): Whether the AddressGroup is predefined or not.

        This method initializes an AddressGroup object with the given name, name source line, and predefined status. 
        It also initializes the address_map, address_group_map, filename_map, desc, and desc_line attributes of the object.
        """
        super().__init__(_name, _name_src_line, _is_predefined)
        self.address_map: Dict[str, int] = {}
        self.address_group_map: Dict[str, int] = {}
        self.filename_map: Dict[str, int] = {}
        self.desc = None
        self.desc_line = None

    def set_description(self, _desc, _desc_line) -> None:
        """
        Sets the description and its source line for the AddressGroup object.

        Args:
            _desc (str): The description to be set.
            _desc_line (int): The source line of the description.
        """
        if _desc is not None and _desc.strip():
            self.desc = _desc
        if _desc_line is not None:
            self.desc_line = _desc_line


    def add_filename(self, _filename: str, _filename_src_line: int) -> None:
        """
        Adds a filename and its source line to the filename_map of the AddressGroup object.

        Args:
            _filename (str): The filename to be added.
            _filename_src_line (str): The source line of the filename.
        """
        if _filename_src_line is not None:
            self.filename_map[_filename] = _filename_src_line

    def set_filename_map(self, _filename_map: dict) -> None:
        """
        Sets the filename_map for the AddressGroup object.

        Args:
            _filename_map (dict): The filename_map to be set.
        """
        self.filename_map = _filename_map

    def add_address(self, _address: str, _address_src_line: int) -> None:
        """
        Adds an address and its source line to the address_map of the AddressGroup object.

        Args:
            _address (str): The address to be added.
            _address_src_line (str): The source line of the address.
        """
        if _address_src_line is not None:
            self.address_map[_address] = _address_src_line

    def set_address_map(self, _address_map: dict) -> None:
        """
        Sets the address_map for the AddressGroup object.

        Args:
            _address_map (dict): The address_map to be set.
        """
        self.address_map = _address_map

    def add_address_group(self, _address_group: str, _address_group_src_line: int) -> None:
        """
        Adds an address group and its source line to the address_group_map of the AddressGroup object.

        Args:
            _address_group (str): The address group to be added.
            _address_group_src_line (str): The source line of the address group.
        """
        if _address_group_src_line is not None:
            self.address_group_map[_address_group] = _address_group_src_line

    def set_address_group_map(self, _address_group_map: dict) -> None:
        """
        Sets the address_group_map for the AddressGroup object.

        Args:
            _address_group_map (dict): The address_group_map to be set.
        """
        self.address_group_map = _address_group_map

    def add_group_members_to_list(self, _tnt, _ordered_list):
        """
        Adds the members of the address group to a list.

        Args:
            _tnt (TNT): The TNT object that contains the address groups.
            _ordered_list (list): The list to which the members will be added.

        This method iterates over the address_group_map and adds the members of each address group to _ordered_list. 
        If a member is not already in _ordered_list, it is appended to the end of the list.
        """
        for addr_grp, addr_grp_line in self.address_group_map.items():
            _tnt.get_address_group(addr_grp).add_group_members_to_list(_tnt, _ordered_list)
            if addr_grp not in _ordered_list:
                _ordered_list.append(addr_grp)

    def replace_address_by_address_group(self, _address_group):
        """
        Replaces an address by an address group in the maps.

        Args:
            _address_group (str): The name of the address group.

        This method replaces an address by an address group in the maps. If the address group named _address_group exists in the address_map, 
        it is removed and added to the address_group_map with the same value.
        """
        addr_grp_line = self.address_map.pop(_address_group, None)
        if addr_grp_line is not None:
            self.address_group_map[_address_group] = addr_grp_line

    def replace_address(self, _aname, _new_aname):
        """
        Replaces an address in the address_map.

        Args:
            _aname (str): The name of the address to be replaced.
            _new_aname (str): The new name of the address.

        This method replaces an address in the address_map. If the address named _aname exists in the map, 
        it is removed and a new address named _new_aname is added to the map with the same value.
        """
        aline = self.address_map.pop(_aname, None)
        if aline is not None:
            self.address_map[_new_aname] = aline

    def replace_address_group(self, _agname, _new_agname):
        """
        Replaces an address group in the address_group_map.

        Args:
            _agname (str): The name of the address group to be replaced.
            _new_agname (str): The new name of the address group.

        This method replaces an address group in the address_group_map. If the address group named _agname exists in the map, 
        it is removed and a new address group named _new_agname is added to the map with the same value.
        """
        aline = self.address_group_map.pop(_agname, None)
        if aline is not None:
            self.address_group_map[_new_agname] = aline

    def listsAreEqual(self, a, b):
        """
        Checks if two lists are equal.

        Args:
            a (list): The first list to compare.
            b (list): The second list to compare.

        Returns:
            bool: True if the two lists contain the same elements, False otherwise.

        This method checks if two lists contain the same elements. It does not consider the order of the elements. 
        If the two lists contain the same elements, the method returns True. If they do not contain the same elements, 
        the method returns False.
        """
        return set(a) == set(b)

    def equals(self, _other):
        """
        Checks if the current AddressGroup object is equal to another AddressGroup object.

        Args:
            _other (AddressGroup): The other AddressGroup object to compare with.

        Returns:
            bool: True if the address_map and address_group_map of both AddressGroup objects have the same keys, False otherwise.

        This method compares the keys of the address_map and address_group_map of the current AddressGroup object 
        with those of another AddressGroup object. If the keys are the same, the method returns True, indicating that 
        the two AddressGroup objects are equal. If the keys are not the same, the method returns False.
        """
        return (set(self.address_map.keys()) == set(_other.address_map.keys()) and
                set(self.address_group_map.keys()) == set(_other.address_group_map.keys()))

    def print_dict_items(self, label, dictionary, cfg_fh, indent):
        """
        This function prints the keys of a dictionary with a given label, file handler, and indentation.
        :param label: The label to print before the dictionary keys.
        :param dictionary: The dictionary whose keys are to be printed.
        :param cfg_fh: The file handler where to print the keys.
        :param indent: The indentation to use when printing.
        """
        keys = ' '.join(dictionary.keys())
        print(f"{indent}    {label} [ {keys} ];", file=cfg_fh)

    def write_config(self, output_vd_cfg, _cfg_fh, _indent):
        """
        Writes the configuration of the AddressGroup object to a file.

        Args:
            output_vd_cfg (bool): A flag indicating whether to output the configuration in a specific format.
            _cfg_fh (file): The file handle where the configuration will be written.
            _indent (str): The indentation to be used in the output file.

        This method writes the configuration of the AddressGroup object to the file specified by _cfg_fh. 
        The output format is controlled by the output_vd_cfg flag. If output_vd_cfg is True, 
        the configuration is written in a specific format. If it's False, the configuration is written in a default format.
        The _indent argument specifies the indentation to be used in the output file.
        """
        vd_str = "group " if output_vd_cfg else ""
        print(f"{_indent}{vd_str}{self.name} {{", file=_cfg_fh)
        if self.desc is not None:
            print(f'{_indent}    description "{self.desc}";', file=_cfg_fh)
        if self.address_map:
            self.print_dict_items("address-list", self.address_map, _cfg_fh, _indent)
        if self.address_group_map:
            self.print_dict_items("address-group-list", self.address_group_map, _cfg_fh, _indent)
        if self.filename_map:
            self.print_dict_items("address-files", self.filename_map, _cfg_fh, _indent)
        print(f"{_indent}}}", file=_cfg_fh)
