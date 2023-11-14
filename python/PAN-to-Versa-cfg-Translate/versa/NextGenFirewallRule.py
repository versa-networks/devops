#!/usr/bin/python
#  NextGenFirewallRule.py - Versa Next Gen Firewall Rule definition
#
#  This file has the definition of a next gen firewall rule.
#
#  Copyright (c) 2023, Versa Networks, Inc.
#  All rights reserved.
#


from versa.FirewallRule import FirewallRule


class NextGenFirewallRule(FirewallRule):
    """
    A class representing a next-generation firewall rule.

    This class extends the `FirewallRule` class and adds additional functionality for handling
    next-generation firewall features such as application maps, URL category maps, and device maps.
    It also provides methods for setting and getting AV and IPS profiles.

    Attributes:
        application_map (dict): A map of applications.
        url_category_map (dict): A map of URL categories.
        devices_map (dict): A map of devices.
        av_profile (str): The AV profile.
        av_profile_line (int): The line number where the AV profile is defined.
        ips_profile (str): The IPS profile.
        ips_profile_line (int): The line number where the IPS profile is defined.
        print_cnt (int): A counter for print operations.

    Args:
        _name (str): The name of the firewall rule.
        _name_src_line (int): The line number where the name is defined.
        _is_predefined (bool): A flag indicating whether the rule is predefined.
    """

    def __init__(self, _name, _name_src_line, _is_predefined):
        """
        Initializes a new instance of the NextGenFirewallRule class.

        This method extends the `__init__` method from the superclass and initializes additional
        attributes specific to next-generation firewall rules, such as application maps, URL
        category maps, device maps, AV and IPS profiles, and a print counter.

        Args:
            _name (str): The name of the firewall rule.
            _name_src_line (int): The line number where the name is defined.
            _is_predefined (bool): A flag indicating whether the rule is predefined.
        """
        super().__init__(_name, _name_src_line, _is_predefined)
        self.application_map = {}
        self.url_category_map = {}
        self.devices_map = {}
        self.av_profile = None
        self.av_profile_line = None
        self.ips_profile = None
        self.ips_profile_line = None
        self.print_cnt = 0

    def add_application(self, _application, _application_src_line):
        self.application_map[_application] = _application_src_line

    def get_application_map(self):
        return self.application_map

    def set_application_map(self, _application_map):
        self.application_map = _application_map

    def add_url_category(self, _url_category, _url_category_src_line):
        self.url_category_map[_url_category] = _url_category_src_line

    def get_url_category_map(self):
        return self.url_category_map

    def set_url_category_map(self, _url_category_map):
        self.url_category_map = _url_category_map

    def add_devices(self, _devices, _devices_src_line):
        self.devices_map[_devices] = _devices_src_line

    def set_devices_map(self, _devices_map):
        self.devices_map = _devices_map

    def has_devices(self):
        return len(self.devices_map) > 0

    def get_av_profile(self):
        return self.av_profile

    def set_av_profile(self, _av_profile, _av_profile_line):
        self.av_profile = _av_profile
        self.av_profile_line = _av_profile_line

    def get_ips_profile(self):
        return self.ips_profile

    def set_ips_profile(self, _ips_profile, _ips_profile_line):
        self.ips_profile = _ips_profile
        self.ips_profile_line = _ips_profile_line

    def write_set_no_closing_brace(self, output_vd_cfg, _cfg_fh, _indent):
        """
        Writes the security profile configuration to a file if AV or IPS profile is set.

        This method extends the `write_set_no_closing_brace` method from the superclass.
        It checks if the AV profile or the IPS profile is set, and if either is, it writes
        the corresponding security profile configuration to the file.

        Args:
            output_vd_cfg (bool): A flag indicating whether to output the VD configuration.
            _cfg_fh (file): The file handle of the configuration file.
            _indent (str): The indentation to use when writing to the file.

        """
        output = []

        set_no_closing_brace_output = super().write_set_no_closing_brace(output_vd_cfg, _cfg_fh, _indent)
        if set_no_closing_brace_output is not None:
            output += set_no_closing_brace_output
        if self.get_av_profile() or self.get_ips_profile():
            output.append(f"{_indent}            security-profile {{")

        if self.get_ips_profile():
            output.append(f"{_indent}                ips {{")
            output.append(f'{_indent}                    predefined-ips-profile "Versa Recommended Profile";')
            output.append(f"{_indent}                }}")

        if self.get_av_profile() or self.get_ips_profile():
            output.append(f"{_indent}            }}")

        print('\n'.join(output), file=_cfg_fh)

    def write_config(self, output_vd_cfg, _vcfg, _tnt, _cfg_fh, _indent):
        """
        Writes the configuration of the next-generation firewall rule to a file.

        This method checks various conditions (e.g., whether the rule has devices, whether the source
        and destination zone maps are not empty, etc.) and writes the corresponding configuration to
        the file. It also handles the printing of the match block and the set block.

        Args:
            output_vd_cfg (bool): A flag indicating whether to output the VD configuration.
            _vcfg (VCfg): The VCfg object containing the configuration.
            _tnt (str): The tenant.
            _cfg_fh (file): The file handle of the configuration file.
            _indent (str): The indentation to use when writing to the file.
        """

        if self.has_devices():
            return

        self.write_rule_open(output_vd_cfg, _vcfg, _tnt, _cfg_fh, _indent)
        match_printed = False

        src_conditions = [self.src_zone_map, self.src_addr_map, self.src_addr_grp_map]

        if any(src_conditions):
            print(f"{_indent}        match {{", file=_cfg_fh)
            match_printed = True
            super().write_src_match_no_closing_brace(output_vd_cfg, _vcfg, _tnt, _cfg_fh, _indent)
            print(f"{_indent}            }}", file=_cfg_fh)

        dst_conditions = [self.dst_zone_map, self.dst_addr_map, self.dst_addr_grp_map]

        if any(dst_conditions):
            if not match_printed:
                print(f"{_indent}        match {{", file=_cfg_fh)
                match_printed = True
            super().write_dst_match_no_closing_brace(output_vd_cfg, _cfg_fh, _indent)
            print(f"{_indent}            }}", file=_cfg_fh)

        if self.match_ip_version:
            if not match_printed:
                print(f"{_indent}        match {{", file=_cfg_fh)
                match_printed = True
            print(f"{_indent}            ip-version {self.match_ip_version}", file=_cfg_fh)

        cur_tnt = _vcfg.get_target_tenant(_tnt)
        sh_tnt = cur_tnt.get_shared_tenant()
        predef_app_map = _vcfg.get_predef_app_map()
        predef_uc_map = _vcfg.get_predef_url_cat_map()

        if self.application_map:
            if not match_printed:
                print(f"{_indent}        match {{", file=_cfg_fh)
                match_printed = True
            print(f"{_indent}            application {{", file=_cfg_fh)

            predef_app_list = [app for app in self.application_map if app in predef_app_map]
            user_def_app_list = [
                app
                for app in self.application_map
                if app in cur_tnt.application_map or (sh_tnt is not None and app in sh_tnt.application_map)
            ]
            user_def_app_grp_list = [
                app
                for app in self.application_map
                if app in cur_tnt.application_group_map or (sh_tnt is not None and app in sh_tnt.application_group_map)
            ]

            if predef_app_list:
                print(
                    f"{_indent}                predefined-application-list [ {' '.join(predef_app_list)} ];",
                    file=_cfg_fh,
                )
            if user_def_app_list:
                print(
                    f"{_indent}                user-defined-application-list [ {' '.join(user_def_app_list)} ];",
                    file=_cfg_fh,
                )
            if user_def_app_grp_list:
                print(f"{_indent}                group-list [ {' '.join(user_def_app_grp_list)} ];", file=_cfg_fh)

            print(f"{_indent}            }}", file=_cfg_fh)

        if self.url_category_map:
            if not match_printed:
                print(f"{_indent}        match {{", file=_cfg_fh)
                match_printed = True
            print(f"{_indent}            url-category {{", file=_cfg_fh)

            predef_uc_list = [
                uc.replace("-", "_") for uc in self.url_category_map if uc.replace("-", "_") in predef_uc_map
            ]
            user_def_uc_list = [
                uc
                for uc in self.url_category_map
                if uc in cur_tnt.url_category_map or (sh_tnt is not None and uc in sh_tnt.url_category_map)
            ]

            if predef_uc_list:
                print(f"{_indent}                predefined [ {' '.join(predef_uc_list)} ];", file=_cfg_fh)
            if user_def_uc_list:
                print(f"{_indent}                user-defined [ {' '.join(user_def_uc_list)} ];", file=_cfg_fh)

            print(f"{_indent}            }}", file=_cfg_fh)

        if match_printed:
            print(f"{_indent}        }}", file=_cfg_fh)

        self.write_set_no_closing_brace(output_vd_cfg, _cfg_fh, _indent)
        print(f"{_indent}        }}", file=_cfg_fh)

        print(f"{_indent}    }}", file=_cfg_fh)
