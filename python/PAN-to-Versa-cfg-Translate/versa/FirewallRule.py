#! /usr/bin/python
#  FirewallRule.py - Versa Firewall Rule definition
#
#  This file has the definition of a firewall rule.
#
#  Copyright (c) 2023, Versa Networks, Inc.
#  All rights reserved.

from enum import Enum
from versa.ConfigObject import ConfigObject


class FirewallRuleAction(Enum):
    """
    Enumeration for firewall rule actions.

    This enumeration defines the possible actions that a firewall rule can take: ALLOW, DENY, and REJECT.
    """

    ALLOW = 1
    DENY = 2
    REJECT = 3

    @staticmethod
    def get_action_string(_action: "FirewallRuleAction") -> str:
        """
        Returns the string representation of a firewall rule action.

        Args:
            _action (FirewallRuleAction): The firewall rule action.

        Returns:
            str: The string representation of the firewall rule action. If the action is not ALLOW or REJECT, it returns "deny".
        """
        if _action == FirewallRuleAction.ALLOW:
            return "allow"
        elif _action == FirewallRuleAction.REJECT:
            return "reject"
        else:
            return "deny"


class FirewallRule(ConfigObject):
    """
    Represents a firewall rule in the configuration.

    This class inherits from ConfigObject and adds additional attributes specific to firewall rules, such as source and destination zones, addresses, address groups, and services, as well as the action to be taken when the rule matches.

    Args:
        ConfigObject (class): The base class for configuration objects. It provides common attributes for all configuration objects, such as name, and predefined flag.
    """

    def __init__(self, _name, _is_predefined):
        """
        Initializes a new instance of the FirewallRule class.

        Args:
            _name (str): The name of the firewall rule.
            _is_predefined (bool): A flag indicating whether the rule is predefined.
        """
        super().__init__(_name, _is_predefined)
        self.src_zone_map = {}
        self.dst_zone_map = {}
        self.src_addr_map = {}
        self.dst_addr_map = {}
        self.src_addr_grp_map = {}
        self.dst_addr_grp_map = {}
        self.src_addr_region_map = {}
        self.dst_addr_region_map = {}
        self.service_map = {}
        self.action = FirewallRuleAction.DENY
        self.schedule = None
        self.natpool = None
        self.desc = ""
        self.match_ip_version = ""
        self.tag = ""
        self.tenant = ""

    def set_tenant(self, _tnt):
        self.tenant = _tnt

    def get_tenant(self):
        return self.tenant

    def set_tag(self, _tag):
        self.tag = _tag

    def set_desc(self, _desc):
        self.desc = _desc

    def get_match_ip_version(self):
        return self.match_ip_version

    def set_match_ip_version(self, _match_ip_version):
        self.match_ip_version = _match_ip_version

    def get_desc(self):
        return self.desc

    def add_src_zone(self, _src_zone):
        if _src_zone in self.src_zone_map:
            self.src_zone_map[_src_zone].extend(None)
        else:
            self.src_zone_map[_src_zone] = [None]

    def add_dst_zone(self, _dst_zone: str) -> None:
        """Adds a destination zone to the destination zone map.

        Args:
            _dst_zone (str): The name of the destination zone.
        """
        self.dst_zone_map.setdefault(_dst_zone, []).append(None)

    def get_src_zone_map(self):
        return self.src_zone_map

    def get_dst_zone_map(self):
        return self.dst_zone_map

    def set_src_zone_map(self, _src_zone_map):
        self.src_zone_map = _src_zone_map

    def set_dst_zone_map(self, _dst_zone_map):
        self.dst_zone_map = _dst_zone_map

    def add_src_addr(self, _src_addr):
        self.src_addr_map[_src_addr] = None

    def add_dst_addr(self, _dst_addr):
        self.dst_addr_map[_dst_addr] = None 

    def get_src_addr_map(self):
        return self.src_addr_map

    def get_dst_addr_map(self):
        return self.dst_addr_map

    def set_src_addr_map(self, _src_addr_map):
        self.src_addr_map = _src_addr_map

    def set_dst_addr_map(self, _dst_addr_map):
        self.dst_addr_map = _dst_addr_map

    def add_src_addr_grp(self, _src_addr_grp):
        self.src_addr_grp_map[_src_addr_grp] = None

    def add_dst_addr_grp(self, _dst_addr_grp):
        self.dst_addr_grp_map[_dst_addr_grp] = None

    def get_src_addr_grp_map(self):
        return self.src_addr_grp_map

    def get_dst_addr_grp_map(self):
        return self.dst_addr_grp_map

    def set_src_addr_grp_map(self, _src_addr_grp_map):
        self.src_addr_grp_map = _src_addr_grp_map

    def set_dst_addr_grp_map(self, _dst_addr_grp_map):
        self.dst_addr_grp_map = _dst_addr_grp_map

    def add_src_addr_region(self, _src_addr_region):
        self.src_addr_region_map[_src_addr_region] = None

    def add_dst_addr_region(self, _dst_addr_region):
        self.dst_addr_region_map[_dst_addr_region] = None

    def get_src_addr_region_map(self):
        return self.src_addr_region_map

    def get_dst_addr_region_map(self):
        return self.dst_addr_region_map

    def set_src_addr_region_map(self, _src_addr_region_map):
        self.src_addr_region_map = _src_addr_region_map

    def set_dst_addr_region_map(self, _dst_addr_region_map):
        self.dst_addr_region_map = _dst_addr_region_map

    def replace_address_by_address_group(self, _address_group: str) -> None:
        """Replaces an address in the source and destination address maps with an address group.

        Args:
            _address_group (str): The name of the address group.
        """
        if _address_group in self.src_addr_map:
            self.src_addr_grp_map[_address_group] = self.src_addr_map.pop(_address_group)
        if _address_group in self.dst_addr_map:
            self.dst_addr_grp_map[_address_group] = self.dst_addr_map.pop(_address_group)

    def replace_address(self, _aname: str, _new_aname: str) -> None:
        """Replaces an address in the source and destination address maps with a new address.

        Args:
            _aname (str): The name of the address to be replaced.
            _new_aname (str): The name of the new address.
        """
        if _aname in self.src_addr_map:
            self.src_addr_map[_new_aname] = self.src_addr_map.pop(_aname)
        if _aname in self.dst_addr_map:
            self.dst_addr_map[_new_aname] = self.dst_addr_map.pop(_aname)

    def replace_address_group(self, _agname, _new_agname):
        """
        Replaces an address group in the source and destination address group maps with a new address group.

        Args:
            _agname (str): The name of the address group to be replaced.
            _new_agname (str): The name of the new address group.

        This method checks if the address group to be replaced is in the source and destination address group maps. If it is, the method deletes it from the map and adds the new address group with the same line number.
        """
        if _agname in self.src_addr_grp_map:
            self.src_addr_grp_map[_new_agname] = self.src_addr_grp_map.pop(_agname)
        if _agname in self.dst_addr_grp_map:
            self.dst_addr_grp_map[_new_agname] = self.dst_addr_grp_map.pop(_agname)

    def add_service(self, _service):
        """
        Adds a service to the service map.

        Args:
            _service (str): The service to be added. If it's a string, it's used directly. If it's a Service object, its name is used.

        This method checks the type of the _service parameter. If it's a string, it uses it directly. If it's a Service object, it uses its name. Then it adds the service to the service map with the source line as the value.
        """
        _svc = _service if isinstance(_service, str) else _service.name

    def get_service_map(self):
        return self.service_map

    def set_service_map(self, _service_map):
        self.service_map = _service_map

    def replace_service_group_by_service_members(self, _service_group):
        """Replaces a service group in the service map with its service members.

        Args:
            _service_group (ServiceGroup): The service group to be replaced.
        """
        if _service_group.name in self.service_map:
            self.service_map.pop(_service_group.name)

    def replace_service(self, _sname, _new_sname):
        if _sname in self.service_map:
            del self.service_map[_sname]
            self.service_map[_new_sname] = None

    def set_action(self, _action):
        self.action = _action


    def get_action(self):
        return self.action

    def get_action_string(self):
        return FirewallRuleAction.get_action_string(self.action)

    def get_schedule(self):
        return self.schedule

    def set_schedule(self, _schedule):
        self.schedule = _schedule


    def get_natpool(self):
        return self.natpool

    def set_natpool(self, _natpool):
        self.natpool = _natpool

    def replace_schedule(self, _sname, _new_sname):
        if _sname == self.schedule:
            self.schedule = _sname

    def write_rule_open(self, output_vd_cfg, _vcfg, _tnt, _cfg_fh, _indent):
        """
        Writes the opening of a firewall rule to a file.

        Args:
            output_vd_cfg (bool): A flag indicating whether the output virtual directory configuration is present.
            _vcfg (dict): The configuration of the virtual circuit.
            _tnt (str): The tenant name.
            _cfg_fh (file object): The file handler where the rule opening will be written.
            _indent (str): The indentation to be used in the output file.

        This method writes the name, description, and tag of a firewall rule to a file. Each of these elements is written only
        if it is not empty. The output is formatted with the provided indentation. If the output virtual directory configuration
        is present, an "access-policy" prefix is added to the rule name.
        """
        vd_str = "access-policy " if output_vd_cfg else ""
        output = [f"{_indent}    {vd_str}{self.name} {{"]
        if self.desc:
            output.append(f'{_indent}    description "{self.desc}";')
        if self.tag:
            output.append(f'{_indent}   tag "{self.tag}";')
        print("\n".join(output), file=_cfg_fh)

    def write_src_match_no_closing_brace(self, _, _vcfg, _tnt, _cfg_fh, _indent):
        """
        Writes the source match of a firewall rule to a file without a closing brace.

        Args:
            output_vd_cfg (dict): The configuration of the output virtual directory.
            _vcfg (dict): The configuration of the virtual circuit.
            _tnt (str): The tenant name.
            _cfg_fh (file object): The file handler where the source match will be written.
            _indent (str): The indentation to be used in the output file.

        This method writes the schedule, services, source zone, source addresses, source address groups,
        and source address regions of a firewall rule to a file. Each of these elements is written only
        if it is not empty. The output is formatted with the provided indentation.
        """
        output = []

        if self.schedule is not None:
            schedule = f"{_indent}            schedule {self.schedule};"
            output.append(f"\n{schedule}\n\n")

        if len(self.service_map) > 0:
            services = [svc if isinstance(svc, str) else svc.name for svc in self.service_map.items()]
            output.append(f"{_indent}            services {{")
            output.append(f"{_indent}                services-list [ {' '.join(services)} ];")
            output.append(f"{_indent}            }}")

        output.append(f"{_indent}            source {{")
        if len(self.src_zone_map) > 0:
            zones = " ".join(zone for zone in self.src_zone_map.items())
            output.append(f"{_indent}                zone {{")
            output.append(f"{_indent}                    zone-list [ {zones} ];")
            output.append(f"{_indent}                }}")

        if len(self.src_addr_map) > 0 or len(self.src_addr_grp_map) > 0:
            output.append(f"{_indent}                address {{")

        if len(self.src_addr_map) > 0:
            addresses = " ".join(addr for addr in self.src_addr_map.items())
            output.append(f"{_indent}                    address-list [ {addresses} ];")

        if len(self.src_addr_grp_map) > 0:
            addr_groups = " ".join(addr_grp for addr_grp in self.src_addr_grp_map.items())
            output.append(f"{_indent}                    address-group-list [ {addr_groups} ];")

        if len(self.src_addr_map) > 0 or len(self.src_addr_grp_map) > 0:
            output.append(f"{_indent}                }}")

        if len(self.src_addr_region_map) > 0:
            regions = " ".join(region for region in self.src_addr_region_map.items())
            output.append(f"{_indent}                region [ {regions} ];")

        if output:
            print("\n".join(output), file=_cfg_fh)

    def write_dst_match_no_closing_brace(self, _, _cfg_fh, _indent):
        """
        Writes the destination match of a firewall rule to a file without a closing brace.

        This method writes the destination match of a firewall rule to a file. The destination match includes the zone, address, address group, and region. Each part of the match is indented by a specified amount.

        Args:
            output_vd_cfg (bool): A flag indicating whether to output the virtual device configuration.
            _cfg_fh (file object): The file handler where the rule configuration will be written.
            _indent (str): The indentation to be used in the output file.
        """
        output = []

        output.append(f"{_indent}            destination {{")
        if len(self.dst_zone_map) > 0:
            output.append(f"{_indent}                zone {{")
            zones = " ".join(zone for zone in self.dst_zone_map.items())
            output.append(f"{_indent}                    zone-list [ {zones} ];")
            output.append(f"{_indent}                }}")

        if self.dst_addr_map or self.dst_addr_grp_map:
            output.append(f"{_indent}                address {{")

        if len(self.dst_addr_map) > 0:
            addresses = " ".join(addr for addr in self.dst_addr_map.items())
            output.append(f"{_indent}                    address-list [ {addresses} ];")

        if len(self.dst_addr_grp_map) > 0:
            addr_groups = " ".join(addr_grp for addr_grp in self.dst_addr_grp_map.items())
            output.append(f"{_indent}                    address-group-list [ {addr_groups} ];")

        if self.dst_addr_map or self.dst_addr_grp_map:
            output.append(f"{_indent}                }}")

        if self.dst_addr_region_map:
            regions = " ".join(region for region in self.dst_addr_region_map.keys())
            output.append(f"{_indent}                region [ {regions} ];")

        if output:
            print("\n".join(output), file=_cfg_fh)

    def write_set_no_closing_brace(self, _: bool, _cfg_fh, _indent: str) -> None:
        """
        Writes a part of the firewall rule configuration to a file without a closing brace.

        This method writes a part of the firewall rule configuration to a file. The configuration is indented by a specified amount and does not include a closing brace.

        Args:
            output_vd_cfg (bool): A flag indicating whether to output the virtual device configuration.
            _cfg_fh (TextIO): The file handle to write the configuration to.
            _indent (str): The string to use for indentation.
        """
        output = [
            f"{_indent}        set {{",
            f"{_indent}            action {FirewallRuleAction.get_action_string(self.action)};",
            f"{_indent}            lef {{",
            f"{_indent}                profile Default-Logging-Profile;",
            f"{_indent}            }}",
        ]
        if output:
            print("\n".join(output), file=_cfg_fh)

    def write_config(self, output_vd_cfg, _vcfg, _tnt, _cfg_fh, _indent):
        """
        Writes the configuration of a firewall rule to a file.

        This method writes the configuration of a firewall rule to a file. The configuration includes the rule opening, source match, destination match, IP version, and set. Each part of the configuration is indented by a specified amount.

        Args:
            output_vd_cfg (bool): A flag indicating whether to output the virtual device configuration.
            _vcfg (str): The virtual configuration of the firewall rule.
            _tnt (str): The tenant to which the firewall rule belongs.
            _cfg_fh (file object): The file handler where the rule configuration will be written.
            _indent (str): The indentation to be used in the output file.
        """
        output = []

        output.append(self.write_rule_open(output_vd_cfg, _vcfg, _tnt, _cfg_fh, _indent))
        match_printed = False

        if self.src_zone_map or self.src_addr_map or self.src_addr_grp_map:
            output.append(f"{_indent}        match {{")
            match_printed = True
            output.append(self.write_src_match_no_closing_brace(output_vd_cfg, _vcfg, _tnt, _cfg_fh, _indent))
            output.append(f"{_indent}            }}")

        if self.dst_zone_map or self.dst_addr_map or self.dst_addr_grp_map:
            if not match_printed:
                output.append(f"{_indent}        match {{")
                match_printed = True
            output.append(self.write_dst_match_no_closing_brace(output_vd_cfg, _cfg_fh, _indent))
            output.append(f"{_indent}            }}")

        if self.match_ip_version:
            output.append(f"{_indent}            ip-version {self.match_ip_version}")

        if match_printed:
            output.append(f"{_indent}        }}")

        output.append(self.write_set_no_closing_brace(output_vd_cfg, _cfg_fh, _indent))
        output.append(f"{_indent}        }}")
        output.append(f"{_indent}    }}")

        if output:
            print("\n".join(output), file=_cfg_fh)
