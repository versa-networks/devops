#
#  FirewallRule.py - Versa Firewall Rule definition
# 
#  This file has the definition of a firewall rule.
# 
#  Copyright (c) 2017, Versa Networks, Inc.
#  All rights reserved.
#


from __future__ import print_function
from versa.ConfigObject import ConfigObject
from enum import Enum



class FirewallRuleAction(Enum):
    ALLOW = 1
    DENY = 2
    REJECT = 3

    @staticmethod
    def get_action_string(_action):
        if (_action == FirewallRuleAction.ALLOW):
            return 'allow'
        elif (_action == FirewallRuleAction.REJECT):
            return 'reject'
        else:
            return 'deny'


class FirewallRule(ConfigObject):

    def __init__(self, _name, _name_src_line, _is_predefined):
        super(FirewallRule, self).__init__(
                                      _name, _name_src_line, _is_predefined)
        self.src_zone_map = { }
        self.dst_zone_map = { }
        self.src_addr_map = { }
        self.dst_addr_map = { }
        self.src_addr_grp_map = { }
        self.dst_addr_grp_map = { }
        self.src_addr_region_map = { }
        self.dst_addr_region_map = { }
        self.service_map = { }
        self.action = FirewallRuleAction.DENY
        self.action_line = 0
        self.schedule = None
        self.schedule_line = 0
        self.natpool = None
        self.natpool_line = 0
        self.desc = ''
        self.desc_src_line = 0
        self.match_ip_version = ''
        self.match_ip_version_src_line = 0


    def set_tenant(self, _tnt):
        self.tenant = _tnt

    def get_tenant(self):
        return self.tenant

    def set_desc(self, _desc, _desc_src_line):
        self.desc = _desc
        self.desc_src_line = _desc_src_line

    def get_match_ip_version(self):
        return self.match_ip_version

    def set_match_ip_version(self, _match_ip_version, _match_ip_version_src_line):
        self.match_ip_version = _match_ip_version
        self.match_ip_version_src_line = _match_ip_version_src_line

    def get_desc(self):
        return self.desc

    def add_src_zone(self, _src_zone, _src_zone_src_line):
        if (_src_zone in self.src_zone_map):
            self.src_zone_map[_src_zone].extend([ _src_zone_src_line ])
        else:
            self.src_zone_map[_src_zone] = [ _src_zone_src_line ]

    def add_dst_zone(self, _dst_zone, _dst_zone_src_line):
        if (_dst_zone in self.dst_zone_map):
            self.dst_zone_map[_dst_zone].extend([ _dst_zone_src_line ])
        else:
            self.dst_zone_map[_dst_zone] = [ _dst_zone_src_line ]

    def get_src_zone_map(self):
        return self.src_zone_map

    def get_dst_zone_map(self):
        return self.dst_zone_map

    def set_src_zone_map(self, _src_zone_map):
        self.src_zone_map = _src_zone_map

    def set_dst_zone_map(self, _dst_zone_map):
        self.dst_zone_map = _dst_zone_map



    def add_src_addr(self, _src_addr, _src_addr_src_line):
        self.src_addr_map[_src_addr] = _src_addr_src_line

    def add_dst_addr(self, _dst_addr, _dst_addr_src_line):
        self.dst_addr_map[_dst_addr] = _dst_addr_src_line

    def get_src_addr_map(self):
        return self.src_addr_map

    def get_dst_addr_map(self):
        return self.dst_addr_map

    def set_src_addr_map(self, _src_addr_map):
        self.src_addr_map = _src_addr_map

    def set_dst_addr_map(self, _dst_addr_map):
        self.dst_addr_map = _dst_addr_map



    def add_src_addr_grp(self, _src_addr_grp, _src_addr_grp_src_line):
        self.src_addr_grp_map[_src_addr_grp] = _src_addr_grp_src_line

    def add_dst_addr_grp(self, _dst_addr_grp, _dst_addr_grp_src_line):
        self.dst_addr_grp_map[_dst_addr_grp] = _dst_addr_grp_src_line

    def get_src_addr_grp_map(self):
        return self.src_addr_grp_map

    def get_dst_addr_grp_map(self):
        return self.dst_addr_grp_map

    def set_src_addr_grp_map(self, _src_addr_grp_map):
        self.src_addr_grp_map = _src_addr_grp_map

    def set_dst_addr_grp_map(self, _dst_addr_grp_map):
        self.dst_addr_grp_map = _dst_addr_grp_map



    def add_src_addr_region(self, _src_addr_region, _src_addr_region_src_line):
        self.src_addr_region_map[_src_addr_region] = _src_addr_region_src_line

    def add_dst_addr_region(self, _dst_addr_region, _dst_addr_region_src_line):
        self.dst_addr_region_map[_dst_addr_region] = _dst_addr_region_src_line

    def get_src_addr_region_map(self):
        return self.src_addr_region_map

    def get_dst_addr_region_map(self):
        return self.dst_addr_region_map

    def set_src_addr_region_map(self, _src_addr_region_map):
        self.src_addr_region_map = _src_addr_region_map

    def set_dst_addr_region_map(self, _dst_addr_region_map):
        self.dst_addr_region_map = _dst_addr_region_map



    def replace_address_by_address_group(self, _address_group):
        if (_address_group in self.src_addr_map):
            addr_grp_line = self.src_addr_map[_address_group]
            del self.src_addr_map[_address_group]
            self.src_addr_grp_map[_address_group] = addr_grp_line
        if (_address_group in self.dst_addr_map):
            addr_grp_line = self.dst_addr_map[_address_group]
            del self.dst_addr_map[_address_group]
            self.dst_addr_grp_map[_address_group] = addr_grp_line

    def replace_address(self, _aname, _new_aname):
        if (_aname in self.src_addr_map):
            aline = self.src_addr_map[_aname]
            del self.src_addr_map[_aname]
            self.src_addr_map[_new_aname] = aline
        if (_aname in self.dst_addr_map):
            aline = self.dst_addr_map[_aname]
            del self.dst_addr_map[_aname]
            self.dst_addr_map[_new_aname] = aline

    def replace_address_group(self, _agname, _new_agname):
        if (_agname in self.src_addr_map):
            aline = self.src_addr_grp_map[_agname]
            del self.src_addr_grp_map[_agname]
            self.src_addr_grp_map[_new_agname] = aline
        if (_agname in self.dst_addr_grp_map):
            aline = self.dst_addr_grp_map[_agname]
            del self.dst_addr_grp_map[_agname]
            self.dst_addr_grp_map[_new_agname] = aline


    def add_service(self, _service, _service_src_line):
        if (type(_service) == type('')):
            _svc = _service
        else:
            _svc = _service.name
        self.service_map[_svc] = _service_src_line

    def get_service_map(self):
        return self.service_map

    def set_service_map(self, _service_map):
        self.service_map = _service_map

    def replace_service_group_by_service_members(self, _service_group):
        if (_service_group.name in self.service_map):
            svc_grp_line = self.service_map[_service_group.name]
            del self.service_map[_service_group.name]
            for svc in _service_group.service_map.keys():
                print('Firewall rule %s: Replacing service group %s with member %s' % (self.name, _service_group.name, svc))
                self.service_map[svc] = svc_grp_line

    def replace_service(self, _sname, _new_sname):
        if (_sname in self.service_map):
            sline = self.service_map[_sname]
            del self.service_map[_sname]
            self.service_map[_new_sname] = sline


    def set_action(self, _action, _action_line):
        self.action = _action
        self.action_line = _action_line

    def get_action(self):
        return self.action

    def get_action_line(self):
        return self.action_line

    def get_action_string(self):
        return FirewallRuleAction.get_action_string(self.action)

    def get_schedule(self):
        return self.schedule

    def set_schedule(self, _schedule, _schedule_line):
        self.schedule = _schedule
        self.schedule_line = _schedule_line


    def get_natpool(self):
        return self.natpool

    def set_natpool(self, _natpool, _natpool_line):
        self.natpool = _natpool
        self.natpool_line = _natpool_line


    def replace_schedule(self, _sname, _new_sname):
        if (_sname == self.schedule):
            self.schedule = _sname


    def write_rule_open(self, output_vd_cfg, _vcfg, _tnt, _cfg_fh, _log_fh, _indent):
        if (output_vd_cfg):
            vd_str = 'access-policy '
        else:
            vd_str = ''
        if (len(self.desc) > 0):
            print('%s    # %d' % ( _indent, self.desc_src_line ), file=_cfg_fh)
            print('%s    description "%s"' % ( _indent, self.desc ), file=_cfg_fh)
        print('%s    # src line %d' % ( _indent, self.name_src_line ), file=_cfg_fh)
        print('%s    %s%s {' % ( _indent, vd_str, self.name ), file=_cfg_fh)


    def write_src_match_no_closing_brace(self, output_vd_cfg, _vcfg, _tnt, _cfg_fh, _log_fh, _indent):
        if (self.schedule is not None):
            print('', file=_cfg_fh)
            if (self.schedule_line > 0):
                print('%s            # src line: %d;' %
                      ( _indent, self.schedule_line ),
                      file=_cfg_fh)
            else:
                print('%s            # src line: none (implicit)' %
                      ( _indent ),
                      file=_cfg_fh)

            print('%s            schedule %s;' % ( _indent, self.schedule ),
                  file=_cfg_fh)
            print('', file=_cfg_fh)

        if (len(self.service_map) > 0):
            print('%s            services {' % ( _indent ), file=_cfg_fh)

            print('%s                # src lines:' % ( _indent ),
                  end='', file=_cfg_fh)
            for svc, svc_line in self.service_map.iteritems():
                print(' ', end='', file=_cfg_fh)
                print(svc_line, end='', file=_cfg_fh)
            print('', file=_cfg_fh)

            print('%s                services-list [' % ( _indent ),
                  end='', file=_cfg_fh)

            for svc, svc_line in self.service_map.iteritems():
                print(' ', end='', file=_cfg_fh)
                if (type(svc) == type('')):
                    print(svc, end='', file=_cfg_fh)
                else:
                    print(svc.name, end='', file=_cfg_fh)

            print(' ];', file=_cfg_fh)

            print('%s            }' % ( _indent ), file=_cfg_fh)

        print('%s            source {' % ( _indent ), file=_cfg_fh)
        if (len(self.src_zone_map) > 0):
            print('%s                zone {' % ( _indent ), file=_cfg_fh)

            print('%s                    # src lines:' % ( _indent ),
                  end='', file=_cfg_fh)
            for zone, zone_line in self.src_zone_map.iteritems():
                print(' ', end='', file=_cfg_fh)
                print(zone_line, end='', file=_cfg_fh)
            print('', file=_cfg_fh)

            print('%s                    zone-list [' % ( _indent ),
                  end='', file=_cfg_fh)

            for zone, zone_line in self.src_zone_map.iteritems():
                print(' ', end='', file=_cfg_fh)
                print(zone, end='', file=_cfg_fh)

            print(' ];', file=_cfg_fh)
            print('%s                }' % ( _indent ), file=_cfg_fh)

        if (len(self.src_addr_map) > 0 or len(self.src_addr_grp_map) > 0):
            print('%s                address {' % ( _indent ), file=_cfg_fh)

        if (len(self.src_addr_map) > 0):
            print('', file=_cfg_fh)
            print('%s                    # src lines:' % ( _indent ),
                  end='', file=_cfg_fh)
            for addr, addr_line in self.src_addr_map.iteritems():
                print(' ', end='', file=_cfg_fh)
                print(addr_line, end='', file=_cfg_fh)
            print('', file=_cfg_fh)

            print('%s                    address-list [' % ( _indent ),
                  end='', file=_cfg_fh)

            for addr, addr_line in self.src_addr_map.iteritems():
                print(' ', end='', file=_cfg_fh)
                print(addr, end='', file=_cfg_fh)

            print(' ];', file=_cfg_fh)
            print('', file=_cfg_fh)

        if (len(self.src_addr_grp_map) > 0):
            print('', file=_cfg_fh)
            print('%s                    # src lines:' % ( _indent ),
                  end='', file=_cfg_fh)
            for addr_grp, addr_grp_line in self.src_addr_grp_map.iteritems():
                print(' ', end='', file=_cfg_fh)
                print(addr_grp_line, end='', file=_cfg_fh)
            print('', file=_cfg_fh)

            print('%s                    address-group-list [' % ( _indent ),
                  end='', file=_cfg_fh)

            for addr_grp, addr_grp_line in self.src_addr_grp_map.iteritems():
                print(' ', end='', file=_cfg_fh)
                print(addr_grp, end='', file=_cfg_fh)

            print(' ];', file=_cfg_fh)
            print('', file=_cfg_fh)

        if (len(self.src_addr_map) > 0 or len(self.src_addr_grp_map) > 0):
            print('%s                }' % ( _indent ), file=_cfg_fh)



        if (len(self.src_addr_region_map) > 0):
            print('%s                region [' % ( _indent ), end='', file=_cfg_fh)
            for r, r_line in self.src_addr_region_map.iteritems():
                print(' ', end='', file=_cfg_fh)
                print(r, end='', file=_cfg_fh)
            print(' ];', file=_cfg_fh)
            print('', file=_cfg_fh)




    def write_dst_match_no_closing_brace(self, output_vd_cfg, _cfg_fh, _log_fh, _indent):
        print('%s            destination {' % ( _indent ), file=_cfg_fh)
        if (len(self.dst_zone_map) > 0):
            print('%s                zone {' % ( _indent ), file=_cfg_fh)

            print('%s                    # src lines:' % ( _indent ),
                  end='', file=_cfg_fh)
            for zone, zone_line in self.dst_zone_map.iteritems():
                print(' ', end='', file=_cfg_fh)
                print(zone_line, end='', file=_cfg_fh)
            print('', file=_cfg_fh)

            print('%s                    zone-list [' % ( _indent ),
                  end='', file=_cfg_fh)

            for zone, zone_line in self.dst_zone_map.iteritems():
                print(' ', end='', file=_cfg_fh)
                print(zone, end='', file=_cfg_fh)

            print(' ];', file=_cfg_fh)
            print('%s                }' % ( _indent ), file=_cfg_fh)

        if (len(self.dst_addr_map) > 0 or len(self.dst_addr_grp_map) > 0):
            print('%s                address {' % ( _indent ), file=_cfg_fh)

        if (len(self.dst_addr_map) > 0):
            print('', file=_cfg_fh)
            print('%s                    # src lines:' % ( _indent ),
                  end='', file=_cfg_fh)
            for addr, addr_line in self.dst_addr_map.iteritems():
                print(' ', end='', file=_cfg_fh)
                print(addr_line, end='', file=_cfg_fh)
            print('', file=_cfg_fh)

            print('%s                    address-list [' % ( _indent ),
                  end='', file=_cfg_fh)

            for addr, addr_line in self.dst_addr_map.iteritems():
                print(' ', end='', file=_cfg_fh)
                print(addr, end='', file=_cfg_fh)

            print(' ];', file=_cfg_fh)
            print('', file=_cfg_fh)

        if (len(self.dst_addr_grp_map) > 0):
            print('', file=_cfg_fh)
            print('%s                    # src lines:' % ( _indent ),
                  end='', file=_cfg_fh)
            for addr_grp, addr_grp_line in self.dst_addr_grp_map.iteritems():
                print(' ', end='', file=_cfg_fh)
                print(addr_grp_line, end='', file=_cfg_fh)
            print('', file=_cfg_fh)

            print('%s                    address-group-list [' % ( _indent ),
                  end='', file=_cfg_fh)

            for addr_grp, addr_grp_line in self.dst_addr_grp_map.iteritems():
                print(' ', end='', file=_cfg_fh)
                print(addr_grp, end='', file=_cfg_fh)

            print(' ];', file=_cfg_fh)
            print('', file=_cfg_fh)

        if (len(self.dst_addr_map) > 0 or len(self.dst_addr_grp_map) > 0):
            print('%s                }' % ( _indent ), file=_cfg_fh)

        if (len(self.dst_addr_region_map) > 0):
            print('%s                region [' % ( _indent ), end='', file=_cfg_fh)
            for r, r_line in self.dst_addr_region_map.iteritems():
                print(' ', end='', file=_cfg_fh)
                print(r, end='', file=_cfg_fh)
            print(' ];', file=_cfg_fh)
            print('', file=_cfg_fh)



    def write_set_no_closing_brace(self, output_vd_cfg, _cfg_fh, _log_fh, _indent):
        print('%s        set {' % (_indent), file=_cfg_fh)

        if (self.action_line > 0):
            print('%s            # src line: %d;' %
                  ( _indent, self.action_line ),
                  file=_cfg_fh)
        else:
            print('%s            # src line: none (implicit)' %
                  ( _indent ),
                  file=_cfg_fh)

        print('%s            action %s;' %
              ( _indent, FirewallRuleAction.get_action_string(self.action) ),
              file=_cfg_fh)

        print('%s            lef {' % ( _indent ),
              file=_cfg_fh)
        print('%s                profile Default-Logging-Profile;' % ( _indent ),
              file=_cfg_fh)
        #print('%s                event end;' % ( _indent ),
        #      file=_cfg_fh)
        print('%s            }' % ( _indent ),
              file=_cfg_fh)

    def write_config(self, output_vd_cfg, _vcfg, _tnt, _cfg_fh, _log_fh, _indent):
        write_rule_open(output_vd_cfg, _vcfg, _tnt, _cfg_fh, _log_fh, _indent)
        match_printed = False

        if ((len(self.src_zone_map.keys()) > 0) or
            (len(self.src_addr_map.keys()) > 0) or
            (len(self.src_addr_grp_map.keys()) > 0)):
            print('%s        match {' % ( _indent ), file=_cfg_fh)
            match_printed = True
            write_src_match_no_closing_brace(output_vd_cfg, _vcfg, _tnt, _cfg_fh, _log_fh, _indent)
            print('%s            }' % (_indent), file=_cfg_fh)

        if ((len(self.dst_zone_map.keys()) > 0) or
            (len(self.dst_addr_map.keys()) > 0) or
            (len(self.dst_addr_grp_map.keys()) > 0)):
            if (not match_printed):
                print('%s        match {' % ( _indent ), file=_cfg_fh)
                match_printed = True
            write_dst_match_no_closing_braceoutput_vd_cfg, (_cfg_fh, _log_fh, _indent)
            print('%s            }' % (_indent), file=_cfg_fh)

        if (len(self.match_ip_version) > 0):
            print('%s            # src line %d' % (_indent, self.match_ip_version_src_line), file=_cfg_fh)
            print('%s            ip-version %s' % (_indent, self.match_ip_version), file=_cfg_fh)

        if (match_printed):
            print('%s        }' % (_indent), file=_cfg_fh)

        write_set_no_closing_braceoutput_vd_cfg, (_cfg_fh, _log_fh, _indent)
        print('%s        }' % (_indent), file=_cfg_fh)

        print('%s    }' % (_indent), file=_cfg_fh)





