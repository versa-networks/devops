#!/usr/bin/python#
#  VersaConfig.py - Versa Config definition
#
#  This file has the definition of full Versa configuration.
#
#  Copyright (c) 2023, Versa Networks, Inc.
#  All rights reserved.
#


from collections import defaultdict
from versa.System import System
from versa.Tenant import Tenant


class VersaConfig(object):
    """
    Represents a Versa configuration.

    Attributes:
    name (str): The name of the Versa configuration.
    tenant_map (dict): A map of tenants in the configuration.
    network_interface_map (dict): A map of network interfaces in the configuration.
    interface_network_map (dict): A map of interfaces to networks in the configuration.
    interface_pair_map (dict): A map of interface pairs in the configuration.
    interface_ptvi_map (dict): A map of interfaces to PTVIs in the configuration.
    vrf_interface_map (dict): A map of VRFs to interfaces in the configuration.
    interface_vrf_map (dict): A map of interfaces to VRFs in the configuration.
    service_any_map (dict): A map of services in the configuration.
    system (System): The system configuration.
    predef_app_map (dict): A map of predefined applications in the configuration.
    predef_url_cat_map (dict): A map of predefined URL categories in the configuration.
    predef_countries_map (dict): A map of predefined countries in the configuration.
    predef_families_map (dict): A map of predefined families in the configuration.
    predef_subfamilies_map (dict): A map of predefined subfamilies in the configuration.
    tenant_xlate_map (dict): A map of tenant translations in the configuration.
    logger (Logger): The logger for the configuration.
    """

    def __init__(self, name):
        """
        Initialize a VersaConfig instance.

        Parameters:
        name (str): The name of the VersaConfig instance.
        """
        self.name = name
        self.tenant_map = {}
        self.network_interface_map = {}
        self.intf_network_map = {}
        self.intf_pair_map = {}
        self.intf_ptvi_map = {}
        self.vrf_interface_map = {}
        self.intf_vrf_map = {}
        self.service_any_map = {}
        self.system = System()
        self.predef_app_map = {}
        self.predef_url_cat_map = {}
        self.predef_countries_map = {}
        self.predef_families_map = {}
        self.predef_subfamilies_map = {}
        self.predef_app_tags_map = {}
        self.tenant_xlate_map = {}
        self.logger = None

    def get_target_tenant(self, _tnt):
        """
        Gets the target tenant from the tenant map or tenant translation map.

        Args:
            tenant (str): The name of the tenant.

        Returns:
            Tenant: The target tenant if found, otherwise None.
        """
        if _tnt in self.tenant_xlate_map:
            tgt_tenant = self.tenant_xlate_map[_tnt][0]
            if tgt_tenant in self.tenant_map:
                return self.tenant_map[tgt_tenant]
        if _tnt in self.tenant_map:
            return self.tenant_map[_tnt]
        return None

    def get_tenant_xlate_map(self):
        return self.tenant_xlate_map

    def set_tenant_xlate_map(self, _tenant_xlate_map):
        self.tenant_xlate_map = _tenant_xlate_map

    def get_predef_app_map(self):
        return self.predef_app_map

    def set_predef_app_map(self, _predef_amap):
        self.predef_app_map = _predef_amap

    def get_predef_url_cat_map(self):
        return self.predef_url_cat_map

    def set_predef_url_cat_map(self, _predef_uc_map):
        self.predef_url_cat_map = _predef_uc_map

    def get_predef_countries_map(self):
        return self.predef_countries_map

    def set_predef_countries_map(self, _predef_countries_map):
        self.predef_countries_map = _predef_countries_map

    def get_predef_families_map(self):
        return self.predef_families_map

    def set_predef_families_map(self, _predef_families_map):
        self.predef_families_map = _predef_families_map

    def get_predef_subfamilies_map(self):
        return self.predef_subfamilies_map

    def set_predef_subfamilies_map(self, _predef_subfamilies_map):
        self.predef_subfamilies_map = _predef_subfamilies_map

    def get_predef_app_tags_map(self):
        return self.predef_app_tags_map

    def set_predef_app_tags_map(self, _predef_app_tags_map):
        self.predef_app_tags_map = _predef_app_tags_map

    def get_logger(self):
        return self.logger

    def set_logger(self, _logger):
        self.logger = _logger

    def get_system(self):
        return self.system

    def set_name(self, _name):
        self.name = _name

    def set_service_any(self, _name):
        self.service_any_map[_name] = True

    def clear_service_any(self, _name):
        self.service_any_map[_name] = False

    def add_network_and_interface(self, network, interface):
        """
        Adds a network and its associated interface to the configuration maps.

        Args:
            network (str): The name of the network.
            interface (str): The name of the interface.
        """
        if network not in self.network_interface_map:
            self.network_interface_map[network] = [interface]
        else:
            self.network_interface_map[network].append(interface)

        self.intf_network_map[interface] = network

    def add_vrf_and_interface(self, vrf, interface):
        """
        Adds a VRF and its associated interface to the configuration maps.

        Args:
            vrf (str): The name of the VRF.
            interface (str): The name of the interface.
        """
        if vrf not in self.vrf_interface_map:
            self.vrf_interface_map[vrf] = [interface]
        else:
            self.vrf_interface_map[vrf].append(interface)

        self.intf_vrf_map[interface] = vrf

    def get_vrf_for_interface(self, _interface):
        if _interface in self.intf_vrf_map:
            return self.intf_vrf_map[_interface]
        else:
            return None

    def get_interfaces_for_vrf(self, _vrf):
        return self.vrf_interface_map[_vrf]

    def find_path_segments_rec(self, paths, tried, tgt_interface, ignore_vrf):
        """
        Finds the path segments between two interfaces recursively.

        Args:
            paths (list): The current path of interfaces.
            tried (list): The interfaces that have been tried.
            tgt_interface (str): The target interface.
            ignore_vrf (bool): Whether to ignore the VRF.

        Returns:
            bool: True if a path is found, False otherwise.
        """
        cur_top = paths[-1]
        vrf = self.get_vrf_for_interface(cur_top)
        if vrf is None:
            return False

        interface_list = self.get_interfaces_for_vrf(vrf)

        if tgt_interface in interface_list:
            paths.append(tgt_interface)
            return True

        pi = self.get_paired_interface(cur_top)
        if pi is not None:
            if pi == tgt_interface:
                paths.append(pi)
                return True

            if pi not in tried:
                tried.append(pi)
                paths.append(pi)
                found = self.find_path_segments_rec(paths, tried, tgt_interface, False)
                if found:
                    return True
                paths.pop()

        if ignore_vrf:
            return False

        for i in interface_list:
            if i not in tried:
                tried.append(i)
                paths.append(i)
                found = self.find_path_segments_rec(paths, tried, tgt_interface, True)
                if found:
                    return True
                paths.pop()

        return False

    def find_path_segments(self, interface1, interface2):
        """
        Finds the path segments between two interfaces.

        Args:
            interface1 (Interface): The starting interface.
            interface2 (Interface): The ending interface.

        Returns:
            list: A list of interfaces that form the path from interface1 to interface2. If no path is found, returns an empty list.
        """
        interface_paths = [interface1]
        interface_tried = [interface1]
        found = self.find_path_segments_rec(interface_paths, interface_tried, interface2, False)
        return interface_paths if found else []

    def add_paired_interface(self, _interface, _paired_interface):
        self.intf_pair_map[_interface] = _paired_interface

    def get_network_for_interface(self, _interface):
        try:
            return self.intf_network_map[_interface]
        except KeyError:
            return None

    def get_interfaces_for_network(self, _network):
        try:
            return self.network_interface_map[_network]
        except KeyError:
            return None

    def get_paired_interface(self, _interface):
        try:
            return self.intf_pair_map[_interface]
        except KeyError:
            return None

    def get_ptvi(self, _interface):
        try:
            return self.intf_ptvi_map[_interface]
        except KeyError:
            return None

    def has_tenant(self, _tenant):
        return _tenant in list(self.tenant_map)

    def get_tenants(self):
        return list(self.tenant_map.keys())

    def get_tenant(self, _tenant, _tenant_line):
        if _tenant not in self.tenant_map:
            self.tenant_map[_tenant] = Tenant(_tenant, _tenant_line)
        return self.tenant_map[_tenant]

    def add_tenant(self, _tenant, _tenant_line):
        if _tenant not in self.tenant_map:
            self.tenant_map[_tenant] = Tenant(_tenant, _tenant_line)
        return self.tenant_map[_tenant]

    def replace_address_by_address_group(self):
        for _, tnt in self.tenant_map.items():
            tnt.replace_address_by_address_group()

    def replace_service_group_by_service_members(self):
        for _, tnt in self.tenant_map.items():
            tnt.replace_service_group_by_service_members()

    def check_config(self, strict_checks):
        """
        Check the configuration for each tenant.

        Parameters:
        strict_checks (bool): If True, perform strict checks.

        Returns:
        None
        """
        for _, tnt in self.tenant_map.items():
            tnt.check_config(strict_checks)

    def write_config(self, tnt_xlate_map, template_name, device_name, _cfg_fh, args):
        """write_config _summary_

        Args:
            tnt_xlate_map (_type_): _description_
            template_name (_type_): _description_
            device_name (_type_): _description_
            _cfg_fh (_type_): _description_
        """

        # Populate the tenant name map, so we can translate old tenant names to new tenant names.
        # Also, if multiple old tenants map to the same new tenant, that information is captured in the map.
        tnt_name_map = defaultdict(list)
        for src_tnt_name, dst_tnt_info in tnt_xlate_map.items():
            dst_tnt_name = dst_tnt_info[0]
            tnt_name_map[dst_tnt_name].append(src_tnt_name)

        # If generating for Versa Director, use the approriate template/device
        # indents[0] is 0 spaces. indents[1] is 4 spaces, indents[2] is 8 spaces, indents[3] is 12 spaces, etc.
        indents = ["    " * i for i in range(9)]

        output_vd_cfg = False
        if template_name is not None:
            print(f"devices {{\n{indents[1]}template {template_name}{{\n{indents[2]}config {{", file=_cfg_fh)
            output_vd_cfg = True
        elif device_name is not None:
            print(f"devices {{\n{indents[1]}device {{\n{indents[2]}config {{", file=_cfg_fh)
            output_vd_cfg = True

        # Generate the interface configuration
        print("    Interfaces")
        print(f"{indents[3]}interfaces {{", file=_cfg_fh)

        interface_map = defaultdict(list)
        for _, tnt in self.tenant_map.items():
            for _, zone in tnt.zone_map.items():
                for interface, _ in zone.interface_map.items():
                    if interface.startswith("vni") and "." in interface:
                        interface_name, unit = interface.split(".")
                        interface_map[interface_name].append(unit)

        interface_map = defaultdict(list)
        for network, interfaces in self.network_interface_map.items():
            for interface in interfaces:
                if interface.startswith("vni") and "." in interface:
                    interface_name, unit = interface.split(".")
                    interface_map[interface_name].append(unit)

        for interface, units in interface_map.items():
            vdi_str = ""
            if output_vd_cfg:
                vdi_str = interface.split("-")[0] + " "
            print(f"{indents[4]}{vdi_str}{interface} {{", file=_cfg_fh)

            for unit in units:
                print(f"{indents[5]}unit {unit} {{", file=_cfg_fh)
                if unit != "0":
                    print(f"{indents[6]}vlan-id {unit};", file=_cfg_fh)
                print(f"{indents[5]}}}", file=_cfg_fh)

            print(f"{indents[4]}}}", file=_cfg_fh)

        print(f"{indents[3]}}}", file=_cfg_fh)

        # Generate the networks configuration
        print(f"{indents[3]}networks {{", file=_cfg_fh)
        print("    Networks")

        for network, interfaces in self.network_interface_map.items():
            vdi_str = "network " if output_vd_cfg else ""
            interfaces_string = " ".join(interfaces)
            network_str = f"{indents[4]}{vdi_str}{network} {{\n{indents[5]}interfaces [ {interfaces_string} ];\n{indents[4]}}}"
            print(network_str, file=_cfg_fh)

        print(f"{indents[3]}}}", file=_cfg_fh)

        # Generate the tenant configuration
        print(f"{indents[3]}orgs {{", file=_cfg_fh)

        for tnt_name in list(tnt_name_map.keys()):
            print(f"{indents[4]}org {tnt_name} {{", file=_cfg_fh)
            if tnt_name not in list(self.tenant_map):
                continue
            print(f"{indents[5]}appliance-owner;", file=_cfg_fh)
            print("    Services")
            print(f"{indents[5]}services [ {args.org_services} ];", file=_cfg_fh)

            # write configuration for traffic identification using interfaces, based on the interfaces of the tenant config
            src_tnt_names = tnt_name_map[tnt_name]
            for src_tenant_name in src_tnt_names:
                dst_tnt_name = tnt_xlate_map[src_tenant_name][0]
                if dst_tnt_name not in self.tenant_map:
                    continue
                tnt = self.tenant_map[dst_tnt_name]

            print(f"{indents[5]}traffic-identification {{", file=_cfg_fh)

            pflag = True
            for _, zone in tnt.get_zone_map().items():
                network_map = zone.get_network_map()

                if pflag and network_map:
                    print(f"{indents[6]}using-networks [ ", end="", file=_cfg_fh)
                    pflag = False

                for network in network_map.keys():
                    print(f"{network} ", end="", file=_cfg_fh)
            if not pflag:
                print("];", file=_cfg_fh)

            pflag = True
            for _, zone in tnt.get_zone_map().items():
                interface_map = zone.get_interface_map()

                if pflag and interface_map:
                    print(f"{indents[6]}using [ ", end="", file=_cfg_fh)
                    pflag = False

                for interface in interface_map.keys():
                    print(f"{interface} ", end="", file=_cfg_fh)

            if not pflag:
                print("];", file=_cfg_fh)

            print(f"{indents[5]}}}", file=_cfg_fh)
            print(f"{indents[4]}}}", file=_cfg_fh)

        # Resolve conflicts between object names that are defined in multiple tenants.
        for tnt_name, _ in tnt_name_map.items():
            print(f"{indents[4]}org-services {tnt_name} {{", file=_cfg_fh)
            if tnt_name not in self.tenant_map:
                continue
            for src_tnm in src_tnt_names:
                dst_tnt_name = tnt_xlate_map[src_tnm][0]
                if dst_tnt_name not in self.tenant_map:
                    continue
                tnt = self.tenant_map[dst_tnt_name]

                # Resolve address object name conflicts
                for address_name, _ in tnt.address_map.items():
                    ix = 0
                    for src_tnm_rep in src_tnt_names:
                        ix += 1
                        if src_tnm_rep != src_tnm:
                            tnt_rep = self.tenant_map[dst_tnt_name]
                            if address_name in tnt_rep.address_map.keys():
                                a_obj_1 = tnt.get_address(address_name)
                                a_obj_2 = tnt_rep.get_address(address_name)
                                if not a_obj_1.equals(a_obj_2):
                                    tnt_rep.replace_address(address_name, address_name + "-" + str(ix))

                # Resolve address-group object name conflicts
                for address_group_name in tnt.address_group_map.keys():
                    ix = 0
                    for src_tnm_rep in src_tnt_names:
                        ix += 1
                        if src_tnm_rep != src_tnm:
                            tnt_rep = self.tenant_map[dst_tnt_name]
                            if address_group_name in tnt_rep.address_group_map.keys():
                                ag_obj_1 = tnt.get_address_group(address_group_name)
                                ag_obj_2 = tnt_rep.get_address_group(address_group_name)
                                if not ag_obj_1.equals(ag_obj_2):
                                    tnt_rep.replace_address_group(address_group_name, address_group_name + "-" + str(ix))

                # Resolve schedule object name conflicts
                for schedule_name in tnt.schedule_map.keys():
                    ix = 0
                    for src_tnm_rep in src_tnt_names:
                        ix += 1
                        if src_tnm_rep != src_tnm:
                            tnt_rep = self.tenant_map[dst_tnt_name]
                            if schedule_name in tnt_rep.schedule_map.keys():
                                s_obj_1 = tnt.get_schedule(schedule_name)
                                s_obj_2 = tnt_rep.get_schedule(schedule_name)
                                if not s_obj_1.equals(s_obj_2):
                                    tnt_rep.replace_schedule(schedule_name, schedule_name + "-" + str(ix))

                # Resolve service object name conflicts
                for service_name in tnt.service_map.keys():
                    ix = 0
                    for src_tnm_rep in src_tnt_names:
                        ix += 1
                        if src_tnm_rep != src_tnm:
                            tnt_rep = self.tenant_map[dst_tnt_name]
                            if service_name in tnt_rep.service_map.keys():
                                s_obj_1 = tnt.get_service(service_name)
                                s_obj_2 = tnt_rep.get_service(service_name)
                                if not s_obj_1.equals(s_obj_2):
                                    tnt_rep.replace_service(service_name, service_name + "-" + str(ix))

            # start of configuration for tenant objects
            print("    Objects")
            print(f"{indents[5]}objects {{", file=_cfg_fh)
            # write configuration for tenant address objects
            dup_addr_set = set()
            print("        Addresses")
            print(f"{indents[6]}addresses {{", file=_cfg_fh)
            tnt = self.tenant_map[tnt_name]
            tnt.write_addresses(output_vd_cfg, dup_addr_set, _cfg_fh, indents[7])
            print(f"{indents[6]}}}", file=_cfg_fh)

            # write configuration for tenant address-group objects
            dup_addr_grp_list = []
            print(f"{indents[6]}address-groups {{", file=_cfg_fh)
            print("        Address Groups")
            tnt = self.tenant_map[tnt_name]
            tnt.write_address_groups(output_vd_cfg, dup_addr_grp_list, _cfg_fh, indents[7])
            print(f"{indents[6]}}}", file=_cfg_fh)

            # write configuration for tenant schedule objects
            incl_schedules = []
            print(f"{indents[6]}schedules {{", file=_cfg_fh)
            print("        Schedules")
            tnt = self.tenant_map[tnt_name]
            tnt.write_schedules(output_vd_cfg, incl_schedules, _cfg_fh, indents[7])
            print(f"{indents[6]}}}", file=_cfg_fh)

            # write configuration for tenant service objects
            incl_services = []
            print(f"{indents[6]}services {{", file=_cfg_fh)
            print("        Services")
            tnt = self.tenant_map[tnt_name]
            tnt.write_services(output_vd_cfg, incl_services, _cfg_fh, indents[7])
            print(f"{indents[6]}}}", file=_cfg_fh)

            # write configuration for tenant zone objects
            print(f"{indents[6]}zones {{", file=_cfg_fh)
            print("        Zones")
            tnt = self.tenant_map[tnt_name]

            # aggregate all interfaces, by zone, across all tenants and print as applicable
            for _, zone in tnt.zone_map.items():
                # indents[2] = indents[1] + "            "

                vd_str = "zone " if output_vd_cfg else ""
                print(f"{indents[7]}{vd_str}{zone.name}{{", file=_cfg_fh)
                zone.write_config(_cfg_fh, indents[5] + "    ", False)

            print(f"{indents[6]}}}", file=_cfg_fh)

            # end of configuration for tenant objects

            print(f"{indents[5]}}}", file=_cfg_fh)
            # write configuration for tenant application objects
            tnt = self.tenant_map[tnt_name]
            if len(list(tnt.get_application_map().keys())) > 0 or len(list(tnt.get_application_group_map().keys())) > 0 or len(list(tnt.get_application_filter_map().keys())) > 0:
                print(f"{indents[5]}application-identification {{", file=_cfg_fh)
            print("    Applications")
            if list(tnt.get_application_map().keys()):
                dup_app_list = []
                print(f"{indents[6]}user-defined-applications {{", file=_cfg_fh)
                tnt.write_applications(output_vd_cfg, dup_app_list, _cfg_fh, indents[7])
                print(f"{indents[6]}}}", file=_cfg_fh)

            # write configuration for tenant application-group objects
            print("    Application Groups")
            if list(tnt.get_application_group_map().keys()):
                dup_app_grp_list = []
                print(f"{indents[6]}application-groups {{", file=_cfg_fh)
                tnt = self.tenant_map[tnt_name]
                tnt.write_application_groups(output_vd_cfg, dup_app_grp_list, _cfg_fh, indents[7])
                print(f"{indents[6]}}}", file=_cfg_fh)

            # write configuration for tenant application-filter objects
            print("    Application Filters")
            if list(tnt.get_application_filter_map().keys()):
                dup_app_fltr_list = []
                print(f"{indents[6]}application-filters {{", file=_cfg_fh)
                tnt = self.tenant_map[tnt_name]
                tnt.write_application_filters(output_vd_cfg, dup_app_fltr_list, _cfg_fh, indents[7])
                print(f"{indents[6]}}}", file=_cfg_fh)

            if len(list(tnt.get_application_map().keys())) > 0 or len(list(tnt.get_application_group_map().keys())) > 0 or len(list(tnt.get_application_filter_map().keys())) > 0:
                print(f"{indents[5]}}}", file=_cfg_fh)

            # write configuration for tenant url category objects
            print("    URL Categories")
            if list(tnt.get_url_category_map().keys()):
                dup_uc_list = []
                print(f"{indents[5]}url-filtering {{", file=_cfg_fh)
                print(f"{indents[6]}user-defined-url-categories {{", file=_cfg_fh)
                tnt.write_url_categories(output_vd_cfg, dup_uc_list, _cfg_fh, indents[7])
                print(f"{indents[6]}}}", file=_cfg_fh)
                print(f"{indents[5]}}}", file=_cfg_fh)

            # start of security configuration for tenant
            print(f"{indents[5]}security {{", file=_cfg_fh)
            print("    Security Rules")
            # start of access policies for tenant
            vd_str = "access-policy-group " if output_vd_cfg else ""
            print(f"{indents[6]}access-policies {{", file=_cfg_fh)
            print(f"{indents[7]}{vd_str}Default-Policy {{", file=_cfg_fh)
            print(f"{indents[8]}rules {{", file=_cfg_fh)

            src_tnt_names = tnt_name_map[tnt_name]
            for src_tnm in src_tnt_names:
                dst_tnt_name = tnt_xlate_map[src_tnm][0]
                tnt = self.tenant_map[dst_tnt_name]
                if tnt.ngfw is not None:
                    tnt.ngfw.write_rules(output_vd_cfg, self, src_tnm, _cfg_fh, indents[3] + "            ")
            # end of access policies for tenant
            print(f"{indents[8]}}}", file=_cfg_fh)
            print(f"{indents[7]}}}", file=_cfg_fh)
            print(f"{indents[6]}}}", file=_cfg_fh)

            # end of security configuration for tenant
            print(f"{indents[5]}}}", file=_cfg_fh)

            # end of configuration for tenant services
            print(f"{indents[4]}}}", file=_cfg_fh)
            print(f"{indents[3]}}}", file=_cfg_fh)
            print(f"{indents[3]}{args.service_node_groups}", file=_cfg_fh)

        print(f"{indents[3]}}}", file=_cfg_fh)
        print(f"{indents[2]}}}", file=_cfg_fh)
        print(f"{indents[1]}}}", file=_cfg_fh)

        if output_vd_cfg:
            print("}", file=_cfg_fh)
