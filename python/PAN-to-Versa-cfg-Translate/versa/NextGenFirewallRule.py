#!/usr/bin/python
#  NextGenFirewallRule.py - Versa Next Gen Firewall Rule definition
#
#  This file has the definition of a next gen firewall rule.
#
#  Copyright (c) 2017, Versa Networks, Inc.
#  All rights reserved.
#
#  pylint: disable=invalid-name


from versa.FirewallRule import FirewallRule


class NextGenFirewallRule(FirewallRule):
    """NextGenFirewallRule
    _summary_

    Args:
        FirewallRule (_type_): _description_
    """

    def __init__(self, _name, _name_src_line, _is_predefined):
        super(NextGenFirewallRule, self).__init__(_name, _name_src_line, _is_predefined)
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

    def write_set_no_closing_brace(self, output_vd_cfg, _cfg_fh, _log_fh, _indent):
        super().write_set_no_closing_brace(output_vd_cfg, _cfg_fh, _log_fh, _indent)
        if (self.get_av_profile() is not None) or (self.get_ips_profile() is not None):
            print(f"{_indent}            security-profile {{", file=_cfg_fh)

        # if (self.get_av_profile() is not None):
        #     print('%s                antivirus {' % (_indent), file=_cfg_fh)
        #     print('%s                    predefined-av-profile "Scan Web and Email Traffic";' % (_indent), file=_cfg_fh)
        #     print('%s                }' % (_indent), file=_cfg_fh)

        if self.get_ips_profile() is not None:
            print(f"{_indent}                ips {{", file=_cfg_fh)
            print(
                f'{_indent}                    predefined-ips-profile "Versa Recommended Profile";',
                file=_cfg_fh,
            )
            print(f"{_indent}                }}", file=_cfg_fh)

        if (self.get_av_profile() is not None) or (self.get_ips_profile() is not None):
            print(f"{_indent}            }}", file=_cfg_fh)

    def write_config(self, output_vd_cfg, _vcfg, _tnt, _cfg_fh, _log_fh, _indent):
        if self.has_devices():
            return

        self.write_rule_open(output_vd_cfg, _vcfg, _tnt, _cfg_fh, _log_fh, _indent)
        match_printed = False
        if (
            (len(list(self.src_zone_map.keys())) > 0)
            or (len(list(self.src_addr_map.keys())) > 0)
            or (len(list(self.src_addr_grp_map.keys())) > 0)
        ):
            print(f"{_indent}        match {{", file=_cfg_fh)
            match_printed = True
            super(NextGenFirewallRule, self).write_src_match_no_closing_brace(
                output_vd_cfg, _vcfg, _tnt, _cfg_fh, _log_fh, _indent
            )
            print(f"{_indent}            }}", file=_cfg_fh)

        if (
            (len(list(self.dst_zone_map.keys())) > 0)
            or (len(list(self.dst_addr_map.keys())) > 0)
            or (len(list(self.dst_addr_grp_map.keys())) > 0)
        ):
            if not match_printed:
                print(f"{_indent}        match {{", file=_cfg_fh)
                match_printed = True
            super(NextGenFirewallRule, self).write_dst_match_no_closing_brace(output_vd_cfg, _cfg_fh, _log_fh, _indent)
            print(f"{_indent}            }}", file=_cfg_fh)

        if len(self.match_ip_version) > 0:
            if not match_printed:
                print(f"{_indent}        match {{", file=_cfg_fh)
                match_printed = True
            print(
                f"{_indent}            # src line {self.match_ip_version_src_line}",
                file=_cfg_fh,
            )
            print(f"{_indent}            ip-version {self.match_ip_version}", file=_cfg_fh)

        cur_tnt = _vcfg.get_target_tenant(_tnt)
        sh_tnt = cur_tnt.get_shared_tenant()
        predef_app_map = _vcfg.get_predef_app_map()
        predef_uc_map = _vcfg.get_predef_url_cat_map()
        if len(list(self.application_map.keys())) > 0:
            if not match_printed:
                print(f"{_indent}        match {{", file=_cfg_fh)
                match_printed = True
            print(
                f"{_indent}            # src line {self.match_ip_version_src_line}",
                file=_cfg_fh,
            )
            print(f"{_indent}            application {{", file=_cfg_fh)

            predef_app_list = []
            user_def_app_list = []
            user_def_app_grp_list = []
            for app in list(self.application_map.keys()):
                if app in list(cur_tnt.application_map.keys()) or (
                    sh_tnt is not None and app in list(sh_tnt.application_map.keys())
                ):
                    user_def_app_list.append(app)
                elif app in list(cur_tnt.application_group_map.keys()) or (
                    sh_tnt is not None and app in list(sh_tnt.application_group_map.keys())
                ):
                    user_def_app_grp_list.append(app)
                elif app in list(predef_app_map.keys()):
                    predef_app_list.append(app)
                else:
                    _vcfg.get_logger().error(
                        f"tenant {_tnt}: while adding application match for rule '{self.name}', no application, group or filter found with name '{app}' in predefined or user-defined "
                    )

            if len(predef_app_list) > 0:
                print(
                    f"{_indent}                predefined-application-list [ ",
                    end="",
                    file=_cfg_fh,
                )
                for app in predef_app_list:
                    print(f" {app.upper()}", end="", file=_cfg_fh)
                print(" ];", file=_cfg_fh)

            if len(user_def_app_list) > 0:
                print(
                    f"{_indent}                user-defined-application-list [ ",
                    end="",
                    file=_cfg_fh,
                )
                for app in user_def_app_list:
                    print(f" {app}", end="", file=_cfg_fh)
                print(" ];", file=_cfg_fh)

            if len(user_def_app_grp_list) > 0:
                print(f"{_indent}                group-list [ ", end="", file=_cfg_fh)
                for app in user_def_app_grp_list:
                    print(f" {app}", end="", file=_cfg_fh)
                print(" ];", file=_cfg_fh)

            print(f"{_indent}            }}", file=_cfg_fh)

        if len(list(self.url_category_map.keys())) > 0:
            if not match_printed:
                print(f"{_indent}        match {{", file=_cfg_fh)
                match_printed = True
            print(
                f"{_indent}            # src line {self.match_ip_version_src_line}",
                file=_cfg_fh,
            )
            print(f"{_indent}            url-category {{", file=_cfg_fh)

            predef_uc_list = []
            user_def_uc_list = []
            for uc in list(self.url_category_map.keys()):
                uc_convert = uc.replace("-", "_")
                if uc in list(cur_tnt.url_category_map.keys()) or (
                    sh_tnt is not None and uc in list(sh_tnt.url_category_map.keys())
                ):
                    user_def_uc_list.append(uc)
                elif uc_convert in list(predef_uc_map.keys()):
                    predef_uc_list.append(uc_convert)
                else:
                    _vcfg.get_logger().error(
                        f"tenant {_tnt}: while adding url-category match for rule '{self.name}', no url-category, found with name '{uc}' in predefined or user-defined "
                    )

            if len(predef_uc_list) > 0:
                print(f"{_indent}                predefined [ ", end="", file=_cfg_fh)
                for uc in predef_uc_list:
                    print(f" {uc}", end="", file=_cfg_fh)
                print(" ];", file=_cfg_fh)

            if len(user_def_uc_list) > 0:
                print(f"{_indent}                user-defined [ ", end="", file=_cfg_fh)
                for uc in user_def_uc_list:
                    print(f" {uc}", end="", file=_cfg_fh)
                print(" ];", file=_cfg_fh)

            print(f"{_indent}            }}", file=_cfg_fh)

        if match_printed:
            print(f"{_indent}        }}", file=_cfg_fh)

        self.write_set_no_closing_brace(output_vd_cfg, _cfg_fh, _log_fh, _indent)
        print(f"{_indent}        }}", file=_cfg_fh)

        print(f"{_indent}    }}", file=_cfg_fh)
