#! /usr/bin/python
#  Firewall.py - Versa Firewall definition
#
#  This file has the definition of the Firewall.
#
#  Copyright (c) 2017, Versa Networks, Inc.
#  All rights reserved.
#
#  pylint: disable=invalid-name


from versa.NetworkFunction import NetworkFunction
from versa.NetworkFunction import NetworkFunctionType


class Firewall(NetworkFunction):
    """Firewall
    _summary_

    Args:
        NetworkFunction (_type_): _description_
    """

    def __init__(self, _name, _name_src_line, _is_predefined):
        super().__init__(_name, _name_src_line, _is_predefined, NetworkFunctionType.STATEFUL_FIREWALL)
        self.rules = []
        self.rule_map = {}

    def add_rule(self, _rule):
        self.rules.extend([_rule])
        self.rule_map[_rule.name] = _rule

    def get_rule(self, _rname):
        return self.rule_map[_rname]

    def replace_address_by_address_group(self, _address_group):
        for rule in self.rules:
            rule.replace_address_by_address_group(_address_group)

    def replace_address(self, _aname, _new_aname):
        for rule in self.rules:
            rule.replace_address(_aname, _new_aname)

    def replace_address_group(self, _agname, _new_agname):
        for rule in self.rules:
            rule.replace_address_group(_agname, _new_agname)

    def replace_schedule(self, _sname, _new_sname):
        for rule in self.rules:
            rule.replace_schedule(_sname, _new_sname)

    def replace_service(self, _sname, _new_sname):
        for rule in self.rules:
            rule.replace_service(_sname, _new_sname)

    def replace_service_group_by_service_members(self, _service_group):
        for rule in self.rules:
            rule.replace_service_group_by_service_members(_service_group)

    def write_rules(self, output_vd_cfg, _vfcg, _tnt, _cfg_fh,  _indent):
        for r in self.rules:
            r.write_config(output_vd_cfg, _vfcg, _tnt, _cfg_fh,  _indent + "        ")

    def write_config(self, _cfg_fh,  _indent):
        """
        Writes the firewall configuration to a file.

        This method writes the firewall configuration to a file. The configuration is indented by a specified amount.

        Args:
            _cfg_fh (TextIO): The file handle to write the configuration to.
            _indent (str): The string to use for indentation.
        """
        print(f"{_indent}access-policies {{", file=_cfg_fh)
        print(f"{_indent}    {self.name} {{", file=_cfg_fh)
        print(f"{_indent}        rules {{", file=_cfg_fh)

        for r in self.rules:
            r.write_config(_cfg_fh,  _indent + "                ")

        print(f"{_indent}        }}", file=_cfg_fh)
        print(f"{_indent}    }}", file=_cfg_fh)
        print(f"{_indent}}}", file=_cfg_fh)
