#!/usr/bin/python
#  Tenant.py - Versa Tenant definition
#
#  Versa configuration supports full multi-tenancy.
#  This file has the definition of Tenant in the Versa configuration.
#
#  Copyright (c) 2023, Versa Networks, Inc.
#  All rights reserved.
#


from typing import TextIO, List
from versa.Address import AddressType
from versa.Zone import Zone


class Tenant(object):
    """
    Represents a tenant in a multi-tenant system.

    Each tenant has a set of resources that are isolated from those of other tenants.
    These resources include addresses, address groups, applications, URL categories, schedules, and services.

    Attributes:
        name (str): The name of the tenant.
        address_map (dict): A map of addresses belonging to the tenant.
        address_group_map (dict): A map of address groups belonging to the tenant.
        application_map (dict): A map of applications belonging to the tenant.
        url_category_map (dict): A map of URL categories belonging to the tenant.
        schedule_map (dict): A map of schedules belonging to the tenant.
        service_map (dict): A map of services belonging to the tenant.
        ngfw (NGFW): The Next-Generation Firewall associated with the tenant.

    Methods:
        write_addresses: Writes the addresses to the configuration file.
        write_address_groups: Writes the address groups to the configuration file.
        write_applications: Writes the applications to the configuration file.
        write_url_categories: Writes the URL categories to the configuration file.
        write_schedules: Writes the schedules to the configuration file.
        write_services: Writes the services to the configuration file.
        write_services_config: Writes the services configuration for the tenant to a file.
    """

    def __init__(self, _name, _name_src_line):
        self.name = _name
        self.name_src_line = _name_src_line
        self.ngfw = None
        self.address_map = {}
        self.address_group_map = {}
        self.application_map = {}
        self.application_group_map = {}
        self.application_filter_map = {}
        self.url_category_map = {}
        self.schedule_map = {}
        self.service_map = {}
        self.service_group_map = {}
        self.zone_map = {}
        self.intf_zone_map = {}
        self.nw_zone_map = {}
        self.natpool_map = {}
        self.shared_tnt = None
        self.desc= None

    def get_shared_tenant(self):
        return self.shared_tnt

    def set_shared_tenant(self, _shared_tnt):
        self.shared_tnt = _shared_tnt

    def set_desc(self, _desc, _):
        self.desc = _desc

    def add_application(self, _application, _application_src_line):
        self.application_map[_application.name] = [_application, _application_src_line]

    def get_application_map(self):
        return self.application_map

    def set_application_map(self, _application_map):
        self.application_map = _application_map

    def get_application(self, _app_name):
        if _app_name in list(self.application_map.keys()):
            return self.application_map[_app_name][0]
        else:
            return None

    def add_application_group(self, _application_group, _application_group_src_line):
        self.application_group_map[_application_group.name] = [
            _application_group,
            _application_group_src_line,
        ]

    def get_application_group_map(self):
        return self.application_group_map

    def set_application_group_map(self, _application_group_map):
        self.application_group_map = _application_group_map

    def get_application_group(self, _grp_name):
        if _grp_name in list(self.application_group_map.keys()):
            return self.application_group_map[_grp_name][0]
        else:
            return None

    def add_application_filter(self, _application_filter, _application_filter_src_line):
        self.application_filter_map[_application_filter.name] = [
            _application_filter,
            _application_filter_src_line,
        ]

    def get_application_filter_map(self):
        return self.application_filter_map

    def set_application_filter_map(self, _application_filter_map):
        self.application_filter_map = _application_filter_map

    def get_application_filter(self, _fltr_name):
        if _fltr_name in list(self.application_filter_map.keys()):
            return self.application_filter_map[_fltr_name][0]
        else:
            return None

    def add_url_category(self, _url_category, _url_category_src_line):
        self.url_category_map[_url_category.name] = [_url_category, _url_category_src_line]

    def get_url_category_map(self):
        return self.url_category_map

    def set_url_category_map(self, _url_category_map):
        self.url_category_map = _url_category_map

    def get_url_category(self, _uc_name):
        if _uc_name in list(self.url_category_map.keys()):
            return self.url_category_map[_uc_name][0]
        else:
            return None

    def add_address(self, _address, _address_src_line):
        self.address_map[_address.name] = [_address, _address_src_line]

    def set_address_map(self, _address_map):
        self.address_map = _address_map

    def get_address(self, _app_name):
        if _app_name in self.address_map:
            return self.address_map[_app_name][0]
        else:
            return None

    def add_address_group(self, _address_group, _address_group_src_line):
        self.address_group_map[_address_group.name] = [_address_group, _address_group_src_line]

    def set_address_group_map(self, _address_group_map):
        self.address_group_map = _address_group_map

    def get_address_group(self, _grp_name):
        if _grp_name in self.address_group_map:
            return self.address_group_map[_grp_name][0]
        else:
            return None

    def add_schedule(self, _schedule, _schedule_src_line):
        self.schedule_map[_schedule.name] = [_schedule, _schedule_src_line]

    def set_schedule_map(self, _schedule_map):
        self.schedule_map = _schedule_map

    def get_schedule(self, _schedule_name):
        return self.schedule_map[_schedule_name][0]

    def add_service(self, _service, _service_src_line):
        self.service_map[_service.name] = [_service, _service_src_line]

    def get_service_map(self):
        return self.service_map

    def set_service_map(self, _service_map):
        self.service_map = _service_map

    def get_service(self, _service_name):
        return self.service_map[_service_name][0]

    def add_service_group(self, _service_group, _service_group_src_line):
        self.service_group_map[_service_group.name] = [_service_group, _service_group_src_line]

    def set_service_group_map(self, _service_group_map):
        self.service_group_map = _service_group_map

    def get_service_group(self, _service):
        if _service in self.service_group_map:
            return self.service_group_map[_service]
        else:
            return None

    def add_zone_interface(self, _zone, _intf, _zone_intf_src_line):
        if _zone not in self.zone_map:
            self.zone_map[_zone] = Zone(_zone, _zone_intf_src_line, False)
        self.zone_map[_zone].add_interface(_intf, _zone_intf_src_line)
        self.intf_zone_map[_intf] = _zone

    def get_zone_for_interface(self, _intf):
        return self.intf_zone_map[_intf]

    def add_zone_network(self, _zone, _nw, _zone_nw_src_line):
        if _zone not in self.zone_map:
            self.zone_map[_zone] = Zone(_zone, _zone_nw_src_line, False)
        self.zone_map[_zone].add_network(_nw, _zone_nw_src_line)
        self.nw_zone_map[_nw] = _zone

    def get_zone_for_network(self, _nw):
        return self.nw_zone_map[_nw]

    def set_zone_map(self, _zone_map):
        self.zone_map = _zone_map

    def get_zone_map(self):
        return self.zone_map

    def add_natpool(self, _natpool, _natpool_src_line):
        self.natpool_map[_natpool.name] = [_natpool, _natpool_src_line]

    def set_natpool_map(self, _natpool_map):
        self.natpool_map = _natpool_map

    def get_natpool(self, _npname):
        return self.natpool_map[_npname][0]

    def get_next_gen_firewall(self):
        return self.ngfw

    def set_next_gen_firewall(self, _ngfw, _ngfw_src_line):
        self.ngfw = _ngfw

    def replace_address_by_address_group(self):
        """
        Replaces the address by the address group in both the ngfw and the address group map.

        This method iterates over each address group in the address group map. For each address group,
        it replaces the address by the address group in all other address groups and in the ngfw.

        No parameters are required as it operates on the instance's own address group map and ngfw.

        Returns:
        None
        """
        for agname, [_, _] in self.address_group_map.items():
            for _, [addr_grp, _] in self.address_group_map.items():
                addr_grp.replace_address_by_address_group(agname)
            if self.ngfw is not None:
                self.ngfw.replace_address_by_address_group(agname)

    def replace_address(self, address_name: str, new_address_name: str) -> None:
        """
        Replaces an address with a new address in the address map, address groups, and firewall rules.

        Args:
            address_name (str): The current address name.
            new_address_name (str): The new address name to replace the current one.

        Returns:
            None
        """
        address_info = self.address_map.pop(address_name, None)
        if address_info is not None:
            address, address_src_line = address_info
            address.name = new_address_name
            self.address_map[new_address_name] = [address, address_src_line]

            # replace the address name in groups that are referring to the current address name
            for _, ag_info in self.address_group_map.items():
                ag_info[0].replace_address(address_name, new_address_name)

            # replace the address name in firewall rules that are referring to the current address name
            if self.ngfw is not None:
                self.ngfw.replace_address(address_name, new_address_name)

    def replace_address_group(self, app_group_name: str, new_app_group_name: str) -> None:
        """
        Replaces an address group with a new address group in the address group map,
        other address groups, and firewall rules.

        Args:
            app_group_name (str): The current address group name.
            new_app_group_name (str): The new address group name to replace the current one.

        Returns:
            None
        """
        if app_group_name in self.address_group_map:
            # replace the address group name in address group object and address group map
            address_grp, address_grp_src_line = self.address_group_map.pop(app_group_name)
            address_grp.name = new_app_group_name
            self.address_group_map[new_app_group_name] = [address_grp, address_grp_src_line]

            # replace the address group name in groups that are referring to the current address group name
            for agn, (ag, _) in self.address_group_map.items():
                if agn != app_group_name:
                    ag.replace_address_group(app_group_name, new_app_group_name)

            # replace the address group name in firewall rules that are referring to the current address group name
            if self.ngfw is not None:
                self.ngfw.replace_address_group(app_group_name, new_app_group_name)

    def replace_schedule(self, schedule_name: str, new_schedule_name: str) -> None:
        """
        Replaces a schedule with a new schedule in the schedule map and firewall rules.

        Args:
            schedule_name (str): The current schedule name.
            new_schedule_name (str): The new schedule name to replace the current one.

        Returns:
            None
        """
        if schedule_name in self.schedule_map:
            # replace the schedule name in schedule object and schedule map
            schedule, schedule_src_line = self.schedule_map.pop(schedule_name)
            schedule.name = new_schedule_name
            self.schedule_map[new_schedule_name] = [schedule, schedule_src_line]

            # replace the schedule name in firewall rules that are referring to the current schedule name
            if self.ngfw is not None:
                self.ngfw.replace_schedule(schedule_name, new_schedule_name)

    def replace_service(self, service_name: str, new_service_name: str) -> None:
        """
        Replaces a service with a new service in the service map and firewall rules.

        Args:
            service_name (str): The current service name.
            new_service_name (str): The new service name to replace the current one.

        Returns:
            None
        """
        if service_name in self.service_map:
            # replace the service name in service object and service map
            service, service_src_line = self.service_map.pop(service_name)
            service.name = new_service_name
            self.service_map[new_service_name] = [service, service_src_line]

            # replace the service name in firewall rules that are referring to the current service name
            if self.ngfw is not None:
                self.ngfw.replace_service(service_name, new_service_name)

    def check_config(self, strict_checks: bool) -> None:
        """
        Checks the configuration of the tenant. If an address is not found in the tenant's address map
        and the shared tenant's address map, it raises an exception or prints a warning and removes the
        address from the address group's address map depending on the strict_checks flag.

        Args:
            strict_checks (bool): If True, raises an exception when an address is not found.
                                  If False, prints a warning and removes the address from the address group's address map.

        Raises:
            Exception: If strict_checks is True and an address is not found in the tenant's address map
                       and the shared tenant's address map.
        """
        for _, [addr_grp, _] in self.address_group_map.items():
            for addr in list(addr_grp.address_map.keys()):
                addr_found = any([
                    addr in self.address_map,
                    addr in self.address_group_map,
                    self.shared_tnt is not None and addr in self.shared_tnt.address_map,
                    self.shared_tnt is not None and addr in self.shared_tnt.address_group_map
                ])
                if not addr_found:
                    if strict_checks:
                        raise Exception(
                            f"Tenant {self.name}: Missing definition for Address {addr} (referred by Address Group {addr_grp.name})"
                        )
                    else:
                        print(
                            f'Tenant {self.name}: Missing definition for Address "{addr}" (referred by Address Group "{addr_grp.name}")'
                        )
                        del addr_grp.address_map[addr]

    def replace_service_group_by_service_members(self) -> None:
        """
        Replaces each service group in the firewall rules with its service members.

        This function assumes that the ngfw attribute of the Tenant class is an instance of a class
        that has a replace_service_group_by_service_members method.

        Returns:
            None
        """
        if self.ngfw is not None:
            for service_group, _ in self.service_group_map.values():
                self.ngfw.replace_service_group_by_service_members(service_group)

    def get_addresses_for_natpool(self, natpool):
        """
        Returns a list of addresses that match the start and end IP of the given NAT pool.

        Args:
            natpool (NatPool): The NAT pool to match addresses against.

        Returns:
            List[Address]: A list of addresses that match the start and end IP of the NAT pool.
        """
        return [
            addr
            for addr, _ in self.address_map.values()
            if addr.addr_type == AddressType.IP_V4_RANGE
            and addr.start_ip == natpool.start_ip
            and addr.end_ip == natpool.end_ip
        ]

    def write_interfaces(self, vcfg, _cfg_fh: TextIO, _indent: str) -> None:
        """
        Writes the interfaces to the configuration file.

        Args:
            vcfg (Vcfg): An instance of the Vcfg class.
            _cfg_fh (TextIO): The file handler of the configuration file.
            _indent (str): The indentation to use when writing to the file.

        Returns:
            None
        """
        for zone in self.zone_map.values():
            for intf, _ in zone.interface_map.items():
                paired_if = vcfg.get_paired_interface(intf)
                ptvi = vcfg.get_ptvi(intf)
                is_merged = vcfg.is_merged_interface(intf)
                print(f"intf {intf}: paired intf {paired_if}; ptvi {ptvi}; is-merged {is_merged}")
                if not is_merged:
                    print(f"{_indent}{intf}", end="", file=_cfg_fh)

    def write_addresses(self, output_vd_cfg: bool, dup_addr_set: set, _cfg_fh: TextIO, _indent: str) -> None:
        """
        Writes the addresses to the configuration file.

        Args:
            output_vd_cfg (bool): A flag indicating whether to output the virtual device configuration.
            dup_addr_list (List[str]): A list of duplicate address names.
            _cfg_fh (TextIO): The file handler of the configuration file.
            _indent (str): The indentation to use when writing to the file.

        Returns:
            None
        """
        for address_name, (addr, _) in self.address_map.items():
            if address_name not in dup_addr_set:
                addr.write_config(output_vd_cfg, _cfg_fh, _indent)
                dup_addr_set.add(address_name)

    def write_address_groups(
        self, output_vd_cfg: bool, dup_addr_grp_list: List[str], _cfg_fh: TextIO, _indent: str
    ) -> None:
        """
        Writes the address groups to the configuration file.

        Args:
            output_vd_cfg (bool): A flag indicating whether to output the virtual device configuration.
            dup_addr_grp_list (List[str]): A list of duplicate address group names.
            _cfg_fh (TextIO): The file handler of the configuration file.
            _indent (str): The indentation to use when writing to the file.

        Returns:
            None
        """
        if self.address_group_map:
            ordered_list = []
            for app_group_name, (addr_grp, _) in self.address_group_map.items():
                if not addr_grp.address_group_map and app_group_name not in dup_addr_grp_list:
                    ordered_list.append(app_group_name)
                    dup_addr_grp_list.append(app_group_name)

            for app_group_name, (addr_grp, _) in self.address_group_map.items():
                if addr_grp.address_group_map:
                    addr_grp.add_group_members_to_list(self, ordered_list)
                if app_group_name not in dup_addr_grp_list:
                    ordered_list.append(app_group_name)
                    dup_addr_grp_list.append(app_group_name)

            for app_group_name in ordered_list:
                self.get_address_group(app_group_name).write_config(output_vd_cfg, _cfg_fh, _indent)

    def write_applications(self, output_vd_cfg: bool, dup_app_list: List[str], _cfg_fh: TextIO, _indent: str) -> None:
        """
        Writes the applications to the configuration file.

        Args:
            output_vd_cfg (bool): A flag indicating whether to output the virtual device configuration.
            dup_app_list (List[str]): A list of duplicate application names.
            _cfg_fh (TextIO): The file handler of the configuration file.
            _indent (str): The indentation to use when writing to the file.

        Returns:
            None
        """
        for app_name, (app, _) in self.application_map.items():
            if app_name not in dup_app_list:
                app.write_config(output_vd_cfg, _cfg_fh, _indent)
                dup_app_list.append(app_name)

    def write_application_groups(self, output_vd_cfg, _, _cfg_fh, _indent):
        for app_group_name in list(self.get_application_group_map().keys()):
            self.get_application_group(app_group_name).write_config(output_vd_cfg, _cfg_fh, _indent)

    def write_application_filters(self, output_vd_cfg, _, _cfg_fh, _indent):
        for app_filter_name in list(self.get_application_filter_map().keys()):
            self.get_application_filter(app_filter_name).write_config(output_vd_cfg, _cfg_fh, _indent)

    def write_url_categories(self, output_vd_cfg: bool, dup_uc_list: List[str], _cfg_fh: TextIO, _indent: str) -> None:
        """
        Writes the URL categories to the configuration file.

        Args:
            output_vd_cfg (bool): A flag indicating whether to output the virtual device configuration.
            dup_uc_list (List[str]): A list of duplicate URL category names.
            _cfg_fh (TextIO): The file handler of the configuration file.
            _indent (str): The indentation to use when writing to the file.

        Returns:
            None
        """
        for uc_name, (uc, _) in self.url_category_map.items():
            if uc_name not in dup_uc_list:
                uc.write_config(output_vd_cfg, _cfg_fh, _indent)
                dup_uc_list.append(uc_name)

    def write_schedules(self, output_vd_cfg: bool, incl_schedules: List[str], _cfg_fh: TextIO, _indent: str) -> None:
        """
        Writes the schedules to the configuration file.

        Args:
            output_vd_cfg (bool): A flag indicating whether to output the virtual device configuration.
            incl_schedules (List[str]): A list of included schedule names.
            _cfg_fh (TextIO): The file handler of the configuration file.
            _indent (str): The indentation to use when writing to the file.

        Returns:
            None
        """
        for schedule_name, (sched, _) in self.schedule_map.items():
            if schedule_name not in incl_schedules:
                sched.write_config(output_vd_cfg, _cfg_fh, _indent)
                incl_schedules.append(schedule_name)

    def write_services(self, output_vd_cfg: bool, incl_services: List[str], _cfg_fh: TextIO, _indent: str) -> None:
        """
        Writes the configuration of each service in the service_map to a file,
        if the service is not already included in incl_services.

        Args:
            output_vd_cfg (bool): A flag indicating whether to output the virtual device configuration.
            incl_services (List[str]): A list of service names that have already been included.
            _cfg_fh (TextIO): The file handler where the service configurations will be written.
            _indent (str): The indentation to be used for the written configurations.

        Returns:
            None
        """
        for service_name, (svc, _) in self.service_map.items():
            if service_name not in incl_services:
                svc.write_config(output_vd_cfg, _cfg_fh, _indent)
                incl_services.append(service_name)

    def write_zones(self, _cfg_fh: TextIO, _indent: str) -> None:
        """
        Writes the configuration of each zone in the zone_map to a file.

        This method iterates over each zone in the zone_map and writes its configuration to the file
        specified by _cfg_fh. Each line of the configuration is indented according to _indent.

        Args:
            _cfg_fh (TextIO): The file handler to which to write the configuration.
            _indent (str): The indentation to use for each line of the configuration.

        Returns:
            None
        """
        if self.zone_map:
            _cfg_fh.write("\n".join(zone.write_config(_indent) for zone in self.zone_map.values()))

    def write_services_config(self, _tnt_nm: str, _cfg_fh: TextIO, _indent: str) -> None:
        """
        Writes the services configuration for a tenant to a file.

        Args:
            _tnt_nm (str): The name of the tenant for which to generate the configuration.
            _cfg_fh (TextIO): The file handler to which to write the configuration.
            _indent (str): The indentation to use for each line of the configuration.

        Returns:
            None
        """
        print(f"tenant: {self.name}; url category map: {str(self.url_category_map)}")
        print(f"{_indent}    org-services {_tnt_nm} {{", file=_cfg_fh)
        print(f"{_indent}        objects {{", file=_cfg_fh)

        config_maps = {
            "address_map": "addresses",
            "address_group_map": "address-groups",
            "schedule_map": "schedules",
            "service_map": "services",
            "zone_map": "zones",
            "application_map": "user-defined-applications",
            "application_group_map": "application-groups",
            "application_filter_map": "application-filters",
            "url_category_map": "user-defined-url-categories",
        }

        for attr, label in config_maps.items():
            if len(getattr(self, attr)) > 0:
                print(f"{_indent}            {label} {{", file=_cfg_fh)
                for _, (obj, _) in getattr(self, attr).items():
                    obj.write_config(_cfg_fh, _indent + "            ")
                print(f"{_indent}            }}", file=_cfg_fh)

        print(f"{_indent}        }}", file=_cfg_fh)
        print(f"{_indent}        security {{", file=_cfg_fh)

        if self.ngfw is not None:
            self.ngfw.write_config(_cfg_fh, _indent)
        print(f"{_indent}        }}", file=_cfg_fh)
        print(f"{_indent}    }}", file=_cfg_fh)
        print("", file=_cfg_fh)
