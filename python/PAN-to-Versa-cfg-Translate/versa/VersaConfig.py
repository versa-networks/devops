#!/usr/bin/python#
#  VersaConfig.py - Versa Config definition
#
#  This file has the definition of full Versa configuration.
#
#  Copyright (c) 2017, Versa Networks, Inc.
#  All rights reserved.
#
# pylint: disable=bare-except,unused-import,unused-variable,invalid-name,consider-using-f-string


from enum import Enum
from xml.dom import minidom
from versa.Tenant import Tenant
from versa.System import System


class VersaConfig(object):
    """VersaConfig _summary_

    Args:
        object (_type_): _description_
    """

    def __init__(self, _name):
        self.name = _name
        self.tenant_map = {}
        self.nw_intf_map = {}
        self.intf_nw_map = {}
        self.intf_pair_map = {}
        self.intf_ptvi_map = {}
        self.vrf_intf_map = {}
        self.intf_vrf_map = {}
        self.service_any_map = {}
        self.system = System()
        self.predef_app_map = {}
        self.predef_url_cat_map = {}
        self.predef_countries_map = {}
        self.predef_subfamilies_map = {}
        self.tenant_xlate_map = {}
        self.logger = None

    def get_target_tenant(self, _tnt):
        """get_target_tenant _summary_

        Args:
            _tnt (_type_): _description_

        Returns:
            _type_: _description_
        """
        if _tnt in list(self.tenant_xlate_map.keys()):
            tgt_tenant = self.tenant_xlate_map[_tnt][0]
            if tgt_tenant in list(self.tenant_map):
                return self.tenant_map[tgt_tenant]
        if _tnt in list(self.tenant_map):
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

    def get_predef_subfamilies_map(self):
        return self.predef_subfamilies_map

    def set_predef_subfamilies_map(self, _predef_subfamilies_map):
        self.predef_subfamilies_map = _predef_subfamilies_map

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

    def add_network_and_interface(self, _nw, _intf):
        """add_network_and_interface _summary_

        Args:
            _nw (_type_): _description_
            _intf (_type_): _description_
        """
        if _nw not in self.nw_intf_map:
            self.nw_intf_map[_nw] = [_intf]
        else:
            self.nw_intf_map[_nw].extend([_intf])
        self.intf_nw_map[_intf] = _nw

    def add_vrf_and_interface(self, _vrf, _intf):
        """add_vrf_and_interface _summary_

        Args:
            _vrf (_type_): _description_
            _intf (_type_): _description_
        """
        if _vrf not in self.vrf_intf_map:
            self.vrf_intf_map[_vrf] = [_intf]
        else:
            self.vrf_intf_map[_vrf].extend([_intf])
        self.intf_vrf_map[_intf] = _vrf

    def get_vrf_for_interface(self, _intf):
        if _intf in self.intf_vrf_map:
            return self.intf_vrf_map[_intf]
        else:
            return None

    def get_interfaces_for_vrf(self, _vrf):
        return self.vrf_intf_map[_vrf]

    def find_path_segments_rec(self, _paths, _tried, _tgt_intf, _ignore_vrf):
        """find_path_segments_rec _summary_

        Args:
            _paths (_type_): _description_
            _tried (_type_): _description_
            _tgt_intf (_type_): _description_
            _ignore_vrf (_type_): _description_

        Returns:
            _type_: _description_
        """
        # print("Trying path ... %s" % (' <-> '.join(_paths)))
        cur_top = _paths[len(_paths) - 1]
        vrf = self.get_vrf_for_interface(cur_top)
        if vrf is None:
            return False
        intf_list = self.get_interfaces_for_vrf(vrf)
        cur_intf_tried = 0
        for i in intf_list:
            # print("Comparing '%s' and '%s'" % (i, _tgt_intf))
            if i == _tgt_intf:
                _paths.append(i)
                return True

        pi = self.get_paired_interface(cur_top)
        if pi is not None:
            if pi == _tgt_intf:
                _paths.append(pi)
                return True

            if pi not in _tried:
                _tried.extend([pi])
                _paths.append(pi)
                found = self.find_path_segments_rec(_paths, _tried, _tgt_intf, False)
                if not found:
                    _paths.pop()
                else:
                    return True

        if _ignore_vrf:
            return False

        for i in intf_list:
            if i not in _tried:
                _tried.extend([i])
                _paths.append(i)
                found = self.find_path_segments_rec(_paths, _tried, _tgt_intf, True)
                if not found:
                    _paths.pop()
                else:
                    return True
        return False

    def find_path_segments(self, _intf1, _intf2):
        """find_path_segments _summary_

        Args:
            _intf1 (_type_): _description_
            _intf2 (_type_): _description_

        Returns:
            _type_: _description_
        """
        intf_paths = [_intf1]
        intf_tried = [_intf1]
        found = self.find_path_segments_rec(intf_paths, intf_tried, _intf2, False)
        if not found:
            return []
        else:
            return intf_paths

    def add_paired_interface(self, _intf, _paired_intf):
        self.intf_pair_map[_intf] = _paired_intf

    def get_network_for_interface(self, _intf):
        try:
            return self.intf_nw_map[_intf]
        except:
            return None

    def get_interfaces_for_network(self, _nw):
        try:
            return self.nw_intf_map[_nw]
        except:
            return None

    def get_paired_interface(self, _intf):
        try:
            return self.intf_pair_map[_intf]
        except:
            return None

    def get_ptvi(self, _intf):
        try:
            return self.intf_ptvi_map[_intf]
        except:
            return None

    def has_tenant(self, _tenant):
        return _tenant in list(self.tenant_map)

    def get_tenants(self):
        return list(self.tenant_map.keys())

    def get_tenant(self, _tenant, _tenant_line):
        if not _tenant in list(self.tenant_map):
            tnt = Tenant(_tenant, _tenant_line)
            self.tenant_map[_tenant] = tnt
        return self.tenant_map[_tenant]

    def add_tenant(self, _tenant, _tenant_line):
        if not _tenant in self.tenant_map:
            tnt = Tenant(_tenant, _tenant_line)
            self.tenant_map[_tenant] = tnt
        return self.tenant_map[_tenant]

    def replace_address_by_address_group(self):
        for tnt_name, tnt in self.tenant_map.items():
            tnt.replace_address_by_address_group()

    def replace_service_group_by_service_members(self):
        for tnt_name, tnt in self.tenant_map.items():
            tnt.replace_service_group_by_service_members()

    def check_config(self, strict_checks):
        for tnt_name, tnt in self.tenant_map.items():
            tnt.check_config(strict_checks)

    def write_config(self, tnt_xlate_map, tmpl_name, device_name, _cfg_fh, _log_fh):
        """write_config _summary_

        Args:
            tnt_xlate_map (_type_): _description_
            tmpl_name (_type_): _description_
            device_name (_type_): _description_
            _cfg_fh (_type_): _description_
            _log_fh (_type_): _description_
        """

        # Populate the tenant name map, so we can translate old tenant names
        # to new tenant names. Also, if multiple old tenants map to the same
        # new tenant, that information is captured in the map.
        tnt_nm_map = {}
        for src_tname, dst_tnt_info in tnt_xlate_map.items():
            dst_tname = dst_tnt_info[0]
            #dst_tname = dst_tnt_info
            # print("src_tname %s; dst_tname %s" % (src_tname, dst_tname))
            if dst_tname in list(tnt_nm_map):
                tnt_nm_map[dst_tname].extend([src_tname])
            else:
                tnt_nm_map[dst_tname] = [src_tname]
        
        # If generating for Versa Director, use the approriate template/device
        indent1 = "    "
        indent2 = indent1 + indent1
        indent3 = indent2 + indent1
        indent4 = indent2 + indent2
        indent5 = indent4 + indent1
        indent6 = indent5 + indent1
        indent7 = indent6 + indent1
        indent8 = indent7 + indent1

        output_vd_cfg = False
        if tmpl_name is not None:
            print("# Based on CLI argument for template, the config", file=_cfg_fh)
            print(f"# generated will belong to the config template {tmpl_name}", file=_cfg_fh)
            print("devices {", file=_cfg_fh)
            print(f"{indent1}template {tmpl_name}{{", file=_cfg_fh)
            print(f"{indent2}config {{", file=_cfg_fh)
            # print("", file=_cfg_fh)
            indent = indent1
            output_vd_cfg = True
        elif device_name is not None:
            print("# Based on CLI argument for template, the config", file=_cfg_fh)
            print(f"# generated will belong to the device {device_name}", file=_cfg_fh)
            print("devices {", file=_cfg_fh)
            print(f"{indent1}device {{", file=_cfg_fh)
            print(f"{indent2}config {{", file=_cfg_fh)
            # print("", file=_cfg_fh)
            indent = indent2
            output_vd_cfg = True

        # Generate the interface configuration
        print(f"{indent3}# Interfaces configuration", file=_cfg_fh)
        print(f"{indent3}interfaces {{", file=_cfg_fh)
        # print("", file=_cfg_fh)

        intf_map = {}
        for tname, tnt in self.tenant_map.items():
            for zname, zone in tnt.zone_map.items():
                for intf, ifline in zone.interface_map.items():
                    if intf.startswith("vni") and intf.index(".") >= 0:
                        (ifname, unit) = intf.split(".")
                        if ifname in intf_map:
                            intf_map[ifname].extend([unit])
                        else:
                            intf_map[ifname] = [unit]

        for nw, intfs in self.nw_intf_map.items():
            for intf in intfs:
                if intf.startswith("vni") and intf.index(".") >= 0:
                    (ifname, unit) = intf.split(".")
                    if ifname in intf_map:
                        ifunits = intf_map[ifname]
                        if not unit in ifunits:
                            intf_map[ifname].extend([unit])
                    else:
                        intf_map[ifname] = [unit]

        for intf, units in intf_map.items():
            vdi_str = ""
            if output_vd_cfg:
                vdi_str = intf.split("-")[0] + " "
            #print(f"{indent4}# Interface config from zone/interface CSV file", file=_cfg_fh)
            print(f"{indent4}{vdi_str}{intf} {{", file=_cfg_fh)

            for unit in units:
                print(f"{indent5}unit {unit} {{", file=_cfg_fh)
                if unit != "0":
                    print(f"{indent4}vlan-id {unit};", file=_cfg_fh)
                print(f"{indent5}}}", file=_cfg_fh)

            print(f"{indent4}}}", file=_cfg_fh)
        # print("", file=_cfg_fh)

        print(f"{indent3}}}", file=_cfg_fh)
        # print("", file=_cfg_fh)

        # Generate the networks configuration
        print(f"{indent3}# Networks configuration", file=_cfg_fh)
        print(f"{indent3}networks {{", file=_cfg_fh)
        # print("", file=_cfg_fh)

        for nw, intfs in self.nw_intf_map.items():
            vdi_str = ""
            if output_vd_cfg:
                vdi_str = "network "
            #print(f"{indent4}# Network config from zone/interface CSV file", file=_cfg_fh)
            print(f"{indent4}{vdi_str}{nw} {{", file=_cfg_fh)

            print(f"{indent5}interfaces [ ", end="", file=_cfg_fh)
            for intf in intfs:
                print(f"{intf} ", end="", file=_cfg_fh)
            print("];", file=_cfg_fh)

            print(f"{indent4}}}", file=_cfg_fh)
            # print("", file=_cfg_fh)

        print(f"{indent3}}}", file=_cfg_fh)
        # print("", file=_cfg_fh)

        # Generate the tenant configuration
        print(f"{indent3}# Tenant configuration", file=_cfg_fh)
        print(f"{indent3}orgs {{", file=_cfg_fh)
        # print("", file=_cfg_fh)
        # print("%s    org %s {" % (indent, tnt_nm), file=_cfg_fh)
        for tnt_nm in list(tnt_nm_map.keys()):
            print(f"{indent4}org {tnt_nm} {{", file=_cfg_fh)
            if tnt_nm not in list(self.tenant_map):
                continue

            # write configuration for traffic identification using
            # interfaces, based on the interfaces of the tenant config
            src_tnames = tnt_nm_map[tnt_nm]
            # print("%s        # src lines: " % (indent), end="", file=_cfg_fh)
            for sn in src_tnames:
                dst_tnt_info = tnt_xlate_map[sn]
                dst_tname = dst_tnt_info
                if dst_tname not in list(self.tenant_map):
                    # debug_print("Skipping VDOM %s; tenant %s, as tenant is not defined" % (sn, dst_tname))
                    continue
                tnt = self.tenant_map[dst_tname]
                # print(" %s" % (tnt.name_src_line), end="", file=_cfg_fh)
            # print("", file=_cfg_fh)

            # print("%s        %s {" % (indent, tnt_nm), file=_cfg_fh)
            print(f"{indent5}traffic-identification {{", file=_cfg_fh)
            # print('%s            using [' % ( indent ), end='', file=_cfg_fh)
            # for src_tnm in src_tnames:
            #     tnt = self.tenant_map[src_tnm]
            #     tnt.write_interfaces(self, _cfg_fh, _log_fh, '')
            # print(' ];', file=_cfg_fh)

            pflag = True
            for zname, zone in tnt.get_zone_map().items():
                nw_map = zone.get_network_map()
                if len(list(nw_map.keys())) > 0:
                    if pflag:
                        print(f"{indent6}using-networks [ ", end="", file=_cfg_fh)
                        pflag = False

                    for nw in list(nw_map.keys()):
                        print(f"{nw} ", end="", file=_cfg_fh)
            if not pflag:
                print("];", file=_cfg_fh)

            pflag = True
            for zname, zone in tnt.get_zone_map().items():
                intf_map = zone.get_interface_map()
                if len(list(intf_map.keys())) > 0:
                    if pflag:
                        print(f"{indent6}using [ ", end="", file=_cfg_fh)
                        pflag = False

                    for intf in list(intf_map.keys()):
                        print(f"{intf} ", end="", file=_cfg_fh)
            if not pflag:
                print("];", file=_cfg_fh)

            print(f"{indent5}}}", file=_cfg_fh)
            print(f"{indent4}}}", file=_cfg_fh)
            # print("", file=_cfg_fh)
        # print(f"{indent3}}}", file=_cfg_fh)
        # print("", file=_cfg_fh)
        # print("", file=_cfg_fh)

        # Resolve conflicts between object names that are defined in multiple tenants.
        # print("%s    org-services {" % (indent), file=_cfg_fh)
        for tnt_nm in list(tnt_nm_map.keys()):
            print(f"{indent4}org-services {tnt_nm} {{", file=_cfg_fh)
            if tnt_nm not in list(self.tenant_map):
                continue

            for src_tnm in src_tnames:
                dst_tnt_info = tnt_xlate_map[src_tnm]
                dst_tname = dst_tnt_info[0]
                if dst_tname not in list(self.tenant_map):
                    # debug_print("Skipping VDOM %s; tenant %s, as tenant is not defined" % (src_tnm, dst_tname))
                    continue
                tnt = self.tenant_map[dst_tname]

                # Resolve address object name conflicts
                for aname in list(tnt.address_map.keys()):
                    ix = 0
                    for src_tnm_rep in src_tnames:
                        ix = ix + 1
                        if not src_tnm_rep == src_tnm:
                            tnt_rep = self.tenant_map[dst_tname]
                            #tnt_rep = self.tenant_map[src_tnm_rep]
                            if aname in list(tnt_rep.address_map.keys()):
                                a_obj_1 = tnt.get_address(aname)
                                a_obj_2 = tnt_rep.get_address(aname)
                                if not a_obj_1.equals(a_obj_2):
                                    print(
                                        "tnt %s: replacing address %s with %s"
                                        % (tnt_rep.name, aname, aname + "-" + str(ix))
                                    )
                                    tnt_rep.replace_address(aname, aname + "-" + str(ix))

                # Resolve address-group object name conflicts
                for agname in list(tnt.address_group_map.keys()):
                    ix = 0
                    for src_tnm_rep in src_tnames:
                        ix = ix + 1
                        if not src_tnm_rep == src_tnm:
                            tnt_rep = self.tenant_map[dst_tname]
                            #tnt_rep = self.tenant_map[src_tnm_rep]
                            if agname in list(tnt_rep.address_group_map.keys()):
                                ag_obj_1 = tnt.get_address_group(agname)
                                ag_obj_2 = tnt_rep.get_address_group(agname)
                                if not ag_obj_1.equals(ag_obj_2):
                                    print(
                                        "tnt %s: replacing address group %s with %s"
                                        % (tnt_rep.name, agname, agname + "-" + str(ix))
                                    )
                                    tnt_rep.replace_address_group(agname, agname + "-" + str(ix))

                # Resolve schedule object name conflicts
                for sname in list(tnt.schedule_map.keys()):
                    ix = 0
                    for src_tnm_rep in src_tnames:
                        ix = ix + 1
                        if not src_tnm_rep == src_tnm:
                            tnt_rep = self.tenant_map[dst_tname]
                            #tnt_rep = self.tenant_map[src_tnm_rep]
                            if sname in list(tnt_rep.schedule_map.keys()):
                                s_obj_1 = tnt.get_schedule(sname)
                                s_obj_2 = tnt_rep.get_schedule(sname)
                                if not s_obj_1.equals(s_obj_2):
                                    print(
                                        "tnt %s: replacing schedule %s with %s"
                                        % (tnt_rep.name, sname, sname + "-" + str(ix))
                                    )
                                    tnt_rep.replace_schedule(sname, sname + "-" + str(ix))

                # Resolve service object name conflicts
                for sname in list(tnt.service_map.keys()):
                    ix = 0
                    for src_tnm_rep in src_tnames:
                        ix = ix + 1
                        if not src_tnm_rep == src_tnm:
                            tnt_rep = self.tenant_map[dst_tname]
                            #tnt_rep = self.tenant_map[src_tnm_rep]
                            if sname in list(tnt_rep.service_map.keys()):
                                s_obj_1 = tnt.get_service(sname)
                                s_obj_2 = tnt_rep.get_service(sname)
                                if not s_obj_1.equals(s_obj_2):
                                    print(
                                        "tnt %s: replacing service %s with %s"
                                        % (tnt_rep.name, sname, sname + "-" + str(ix))
                                    )
                                    tnt_rep.replace_service(sname, sname + "-" + str(ix))

            # write configuration for tenant services
            # print("", file=_cfg_fh)
            # print("%s        %s {" % (indent, tnt_nm), file=_cfg_fh)

            # start of configuration for tenant objects
            print(f"{indent5}objects {{", file=_cfg_fh)

            # write configuration for tenant address objects
            dup_addr_list = []
            print(f"{indent6}addresses {{", file=_cfg_fh)
            tnt = self.tenant_map[tnt_nm]
            tnt.write_addresses(output_vd_cfg, dup_addr_list, _cfg_fh, _log_fh, indent2 + "    ")
            print(f"{indent6}}}", file=_cfg_fh)

            # write configuration for tenant address-group objects
            dup_addr_grp_list = []
            print(f"{indent6}address-groups {{", file=_cfg_fh)
            tnt = self.tenant_map[tnt_nm]
            tnt.write_address_groups(output_vd_cfg, dup_addr_grp_list, _cfg_fh, _log_fh, indent2 + "    ")
            print(f"{indent6}}}", file=_cfg_fh)

            # write configuration for tenant schedule objects
            incl_schedules = []
            print(f"{indent6}schedules {{", file=_cfg_fh)
            tnt = self.tenant_map[tnt_nm]
            tnt.write_schedules(output_vd_cfg, incl_schedules, _cfg_fh, _log_fh, indent2)
            print(f"{indent6}}}", file=_cfg_fh)

            # write configuration for tenant service objects
            incl_services = []
            print(f"{indent6}services {{", file=_cfg_fh)
            tnt = self.tenant_map[tnt_nm]
            tnt.write_services(output_vd_cfg, incl_services, _cfg_fh, _log_fh, indent2 + "    ")
            print(f"{indent6}}}", file=_cfg_fh)

            # write configuration for tenant zone objects
            #print(f"{indent6}# Interface config from zone/interface CSV file", file=_cfg_fh)
            print(f"{indent6}zones {{", file=_cfg_fh)
            incl_zlist = []
            tnt = self.tenant_map[tnt_nm]

            # aggregate all interfaces, by zone, across all tenants and
            # print as applicable
            for zname, zone in tnt.zone_map.items():
                indent2 = indent + "            "

                if output_vd_cfg:
                    vd_str = "zone "
                else:
                    vd_str = ""
                print(f"{indent7}{vd_str}{zone.name}{{", file=_cfg_fh)
                zone.write_config(_cfg_fh, _log_fh, indent5 + "    ", False)
                print(f"{indent7}}}", file=_cfg_fh)

            print(f"{indent6}}}", file=_cfg_fh)

            # end of configuration for tenant objects
            print(f"{indent5}}}", file=_cfg_fh)

            # write configuration for tenant application objects
            tnt = self.tenant_map[tnt_nm]
            if (
                len(list(tnt.get_application_map().keys())) > 0
                or len(list(tnt.get_application_group_map().keys())) > 0
                or len(list(tnt.get_application_filter_map().keys())) > 0
            ):
                print(f"{indent5}application-identification {{", file=_cfg_fh)

            if list(tnt.get_application_map().keys()):
                dup_app_list = []
                print(f"{indent6}user-defined-applications {{", file=_cfg_fh)
                tnt.write_applications(output_vd_cfg, dup_app_list, _cfg_fh, _log_fh, indent6 + "")
                print(f"{indent6}}}", file=_cfg_fh)

            # write configuration for tenant application-group objects
            if list(tnt.get_application_group_map().keys()):
                dup_app_grp_list = []
                print(f"{indent6}application-groups {{", file=_cfg_fh)
                tnt = self.tenant_map[tnt_nm]
                tnt.write_application_groups(output_vd_cfg, dup_app_grp_list, _cfg_fh, _log_fh, indent6 + "")
                print(f"{indent6}}}", file=_cfg_fh)

            # write configuration for tenant application-filter objects
            if list(tnt.get_application_filter_map().keys()):
                dup_app_fltr_list = []
                print(f"{indent6}application-filters {{", file=_cfg_fh)
                tnt = self.tenant_map[tnt_nm]
                tnt.write_application_filters(output_vd_cfg, dup_app_fltr_list, _cfg_fh, _log_fh, indent6 + "")
                print(f"{indent6}}}", file=_cfg_fh)

            if (
                len(list(tnt.get_application_map().keys())) > 0
                or len(list(tnt.get_application_group_map().keys())) > 0
                or len(list(tnt.get_application_filter_map().keys())) > 0
            ):
                print(f"{indent5}}}", file=_cfg_fh)

            # write configuration for tenant url category objects
            if list(tnt.get_url_category_map().keys()):
                dup_uc_list = []
                print(f"{indent5}url-filtering {{", file=_cfg_fh)
                print(f"{indent6}user-defined-url-categories {{", file=_cfg_fh)
                tnt.write_url_categories(output_vd_cfg, dup_uc_list, _cfg_fh, _log_fh, indent6 + "")
                print(f"{indent6}}}", file=_cfg_fh)
                print(f"{indent5}}}", file=_cfg_fh)

            # start of security configuration for tenant
            print(f"{indent5}security {{", file=_cfg_fh)

            # start of access policies for tenant
            if output_vd_cfg:
                vd_str = "access-policy-group "
            else:
                vd_str = ""
            print(f"{indent6}access-policies {{", file=_cfg_fh)
            print(f"{indent7}{vd_str}Default-Policy {{", file=_cfg_fh)
            print(f"{indent8}rules {{", file=_cfg_fh)

            src_tnames = tnt_nm_map[tnt_nm]
            for src_tnm in src_tnames:
                dst_tnt_info = tnt_xlate_map[src_tnm]
                dst_tname = dst_tnt_info[0]
                tnt = self.tenant_map[dst_tname]
                if tnt.ngfw is not None:
                    tnt.ngfw.write_rules(output_vd_cfg, self, src_tnm, _cfg_fh, _log_fh, indent3 + "            ")
            # end of access policies for tenant
            print(f"{indent8}}}", file=_cfg_fh)
            print(f"{indent7}}}", file=_cfg_fh)
            print(f"{indent6}}}", file=_cfg_fh)

            # end of security configuration for tenant
            print(f"{indent5}}}", file=_cfg_fh)

            # end of configuration for tenant services
            print(f"{indent4}}}", file=_cfg_fh)

        # print("", file=_cfg_fh)
        print(f"{indent3}}}", file=_cfg_fh)
        print("        }", file=_cfg_fh)

        if output_vd_cfg:
            # print("", file=_cfg_fh)
            print("        # end of translated configuration", file=_cfg_fh)
            print(f"{indent1}}}", file=_cfg_fh)
            print("}", file=_cfg_fh)
