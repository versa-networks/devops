#
#  Tenant.py - Versa Tenant definition
# 
#  Versa configuration supports full multi-tenancy.
#  This file has the definition of Tenant in the Versa configuration.
# 
#  Copyright (c) 2017, Versa Networks, Inc.
#  All rights reserved.
#

from __future__ import print_function
from versa.Address import AddressType
from versa.Zone import Zone
from versa.NextGenFirewall import NextGenFirewall

class Tenant(object):

    def __init__(self, _name, _name_src_line):
        self.name = _name
        self.name_src_line = _name_src_line
        self.ngfw = None
        self.address_map = { }
        self.address_group_map = { }
        self.application_map = { }
        self.application_group_map = { }
        self.application_filter_map = { }
        self.url_category_map = { }
        self.schedule_map = { }
        self.service_map = { }
        self.service_group_map = { }
        self.zone_map = { }
        self.intf_zone_map = { }
        self.nw_zone_map = { }
        self.natpool_map = { }
        self.shared_tnt = None

    def get_shared_tenant(self):
        return self.shared_tnt

    def set_shared_tenant(self, _shared_tnt):
        self.shared_tnt = _shared_tnt

    def set_desc(self, _desc, _desc_src_line):
        self.desc = _desc
        self.desc_src_line = _desc_src_line

    def add_application(self, _application, _application_src_line):
        self.application_map[_application.name] = [_application, _application_src_line]

    def get_application_map(self):
        return self.application_map

    def set_application_map(self, _application_map):
        self.application_map = _application_map

    def get_application(self, _aname):
        if (_aname in self.application_map.keys()):
            return self.application_map[_aname][0]
        else:
            return None

    def add_application_group(self, _application_group, _application_group_src_line):
        self.application_group_map[_application_group.name] = \
                                   [ _application_group, _application_group_src_line ]

    def get_application_group_map(self):
        return self.application_group_map

    def set_application_group_map(self, _application_group_map):
        self.application_group_map = _application_group_map

    def get_application_group(self, _grp_name):
        if (_grp_name in self.application_group_map.keys()):
            return self.application_group_map[_grp_name][0]
        else:
            return None

    def add_application_filter(self, _application_filter, _application_filter_src_line):
        self.application_filter_map[_application_filter.name] = \
                                   [ _application_filter, _application_filter_src_line ]

    def get_application_filter_map(self):
        return self.application_filter_map

    def set_application_filter_map(self, _application_filter_map):
        self.application_filter_map = _application_filter_map

    def get_application_filter(self, _fltr_name):
        if (_fltr_name in self.application_filter_map.keys()):
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
        if (_uc_name in self.url_category_map.keys()):
            return self.url_category_map[_uc_name][0]
        else:
            return None

    def add_address(self, _address, _address_src_line):
        self.address_map[_address.name] = [_address, _address_src_line]

    def set_address_map(self, _address_map):
        self.address_map = _address_map

    def get_address(self, _aname):
        if (_aname in self.address_map):
            return self.address_map[_aname][0]
        else:
            return None

    def add_address_group(self, _address_group, _address_group_src_line):
        self.address_group_map[_address_group.name] = \
                                   [ _address_group, _address_group_src_line ]

    def set_address_group_map(self, _address_group_map):
        self.address_group_map = _address_group_map

    def get_address_group(self, _grp_name):
        if (_grp_name in self.address_group_map):
            return self.address_group_map[_grp_name][0]
        else:
            return None

    def add_schedule(self, _schedule, _schedule_src_line):
        self.schedule_map[_schedule.name] = [_schedule, _schedule_src_line]

    def set_schedule_map(self, _schedule_map):
        self.schedule_map = _schedule_map

    def get_schedule(self, _sname):
        return self.schedule_map[_sname][0]

    def add_service(self, _service, _service_src_line):
        self.service_map[_service.name] = [_service, _service_src_line]

    def get_service_map(self):
        return self.service_map

    def set_service_map(self, _service_map):
        self.service_map = _service_map

    def get_service(self, _sname):
        return self.service_map[_sname][0]

    def add_service_group(self, _service_group, _service_group_src_line):
        self.service_group_map[_service_group.name] = \
                                   [ _service_group, _service_group_src_line ]

    def set_service_group_map(self, _service_group_map):
        self.service_group_map = _service_group_map

    def get_service_group(self, _service):
        if _service in self.service_group_map:
            return self.service_group_map[_service]
        else:
            return None

    def add_zone_interface(self, _zone, _intf, _zone_intf_src_line):
        if (_zone not in self.zone_map):
            self.zone_map[_zone] = Zone(_zone, _zone_intf_src_line, False)
        self.zone_map[_zone].add_interface(_intf, _zone_intf_src_line)
        self.intf_zone_map[_intf] = _zone

    def get_zone_for_interface(self, _intf):
        return self.intf_zone_map[_intf]

    def add_zone_network(self, _zone, _nw, _zone_nw_src_line):
        if (_zone not in self.zone_map):
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
        self.ngfw_src_line = _ngfw_src_line
        # print('setting ngfw for tnt: ' + self.name +
        #       ' ngfw name: ' + self.ngfw.name)

    def replace_address_by_address_group(self):
        for agname, [ag, ag_line] in self.address_group_map.iteritems():
            for agn, [addr_grp, addr_grp_line] in self.address_group_map.iteritems():
                addr_grp.replace_address_by_address_group(agname)
            if (self.ngfw is not None):
                self.ngfw.replace_address_by_address_group(agname)

    def replace_address(self, _aname, _new_aname):
        if (_aname in self.address_map.keys()):
            # replace the address name in address object and address map
            [_address, _address_src_line] = self.address_map[_aname]
            _address.name = _new_aname
            del self.address_map[_aname]
            self.address_map[_new_aname] = [_address, _address_src_line]

            # replace the address name in groups that are referring to the
            # current address name
            for agname, [ag, ag_line] in self.address_group_map.iteritems():
                ag.replace_address(_aname, _new_aname)

            # replace the address name in firewall rules that are referring to
            # the current address name
            if (self.ngfw is not None):
                self.ngfw.replace_address(_aname, _new_aname)

    def replace_address_group(self, _agname, _new_agname):
        if (_agname in self.address_group_map.keys()):
            # replace the address group name in address group object
            # and address group map
            [_address_grp, _address_grp_src_line] = self.address_group_map[_agname]
            _address_grp.name = _new_agname
            del self.address_group_map[_agname]
            self.address_group_map[_new_agname] = [_address_grp, _address_grp_src_line]

            # replace the address group name in groups that are referring to
            # the current address group name
            for agname, [ag, ag_line] in self.address_group_map.iteritems():
                ag.replace_address_group(_agname, _new_agname)

            # replace the address group name in firewall rules that are
            # referring to the current address group name
            if (self.ngfw is not None):
                self.ngfw.replace_address_group(_agname, _new_agname)

    def replace_schedule(self, _sname, _new_sname):
        if (_sname in self.schedule_map.keys()):
            # replace the schedule name in schedule object and schedule map
            [_schedule, _schedule_src_line] = self.schedule_map[_sname]
            _schedule.name = _new_sname
            del self.schedule_map[_sname]
            self.schedule_map[_new_sname] = [_schedule, _schedule_src_line]

            # replace the schedule name in firewall rules that are referring to
            # the current schedule name
            if (self.ngfw is not None):
                self.ngfw.replace_schedule(_sname, _new_sname)

    def replace_service(self, _sname, _new_sname):
        if (_sname in self.service_map.keys()):
            # replace the service name in service object and service map
            [_service, _service_src_line] = self.service_map[_sname]
            _service.name = _new_sname
            del self.service_map[_sname]
            self.service_map[_new_sname] = [_service, _service_src_line]

            # replace the service name in firewall rules that are referring to
            # the current service name
            if (self.ngfw is not None):
                self.ngfw.replace_service(_sname, _new_sname)

    def check_config(self, strict_checks):
        # print('')
        # print('Printing addresses for tenant: %s' % (self.name))
        # print('')
        # for aname, [addr, addr_line] in self.address_map.iteritems():
        #     print(aname)

        for agname, [addr_grp, addr_grp_line] in self.address_group_map.iteritems():
            for addr in addr_grp.address_map.keys():
                # print('checking address group %s ; addr %s' % (agname, addr))
                addr_found = False
                if (addr in self.address_map.keys()):
                    addr_found = True
                else:
                    if (self.shared_tnt is not None and
                        addr in self.shared_tnt.address_map.keys()):
                        addr_found = True

                if (not addr_found):
                    if (strict_checks):
                        raise Exception(
                                'Tenant %s: Missing definition for Address %s'
                                ' (referred by Address Group %s)' %
                                (self.name, addr, addr_grp.name))
                    else:
                        print('Tenant %s: Missing definition for Address "%s"'
                              ' (referred by Address Group "%s")' %
                              (self.name, addr, addr_grp.name))
                        del addr_grp.address_map[addr]

    def replace_service_group_by_service_members(self):
        if (self.ngfw is not None):
            for sgname, [sg, sg_line] in self.service_group_map.iteritems():
                self.ngfw.replace_service_group_by_service_members(sg)

    def get_addresses_for_natpool(self, _natpool):
        addr_list = [ ]
        if (len(self.address_map) > 0):
            for aname, [addr, addr_line] in self.address_map.iteritems():
                if (addr.addr_type == AddressType.IP_V4_RANGE):
                    # print('Tenant %s: Comparing Address %s (%s-%s) '
                    #       'for matching natpool %s (%s-%s))' % (self.name, aname, addr.start_ip, addr.end_ip, _natpool.name, _natpool.start_ip, _natpool.end_ip))
                    if ((addr.start_ip == _natpool.start_ip) and
                        (addr.end_ip == _natpool.end_ip)):
                        # print('Tenant %s: Returning Address %s '
                        #       'for matching natpool %s)' % (self.name, aname, _natpool.name))
                        addr_list.extend( [ addr ] )
        return addr_list

    def write_interfaces(self,  vcfg, _cfg_fh, _log_fh, _indent):
        for zname, zone in self.zone_map.iteritems():
            for intf, ifline in zone.interface_map.iteritems():
                paired_if = vcfg.get_paired_interface(intf)
                ptvi = vcfg.get_ptvi(intf)
                is_merged = vcfg.is_merged_interface(intf)
                print("intf %s: paired intf %s; ptvi %s; is-merged %s" %
                      (intf, paired_if, ptvi, is_merged))
                if (not is_merged):
                    print(' %s' % ( intf ), end='', file=_cfg_fh)

    def write_addresses(self, output_vd_cfg, dup_addr_list, _cfg_fh, _log_fh, _indent):
        if (len(self.address_map) > 0):
            for aname, [addr, addr_line] in self.address_map.iteritems():
                if (not aname in dup_addr_list):
                    addr.write_config(output_vd_cfg, _cfg_fh, _log_fh,
                                      _indent + '            ')
                    dup_addr_list.extend( [ aname ] )

    def write_address_groups(self, output_vd_cfg, dup_addr_grp_list, _cfg_fh, _log_fh, _indent):
        if (len(self.address_group_map) > 0):
            ordered_list = [ ]
            for agname, [addr_grp, addr_grp_line] in self.address_group_map.iteritems():
                if (len(addr_grp.address_group_map) == 0):
                    if ((agname not in ordered_list) and
                        (agname not in dup_addr_grp_list)):
                        ordered_list.extend([agname])
                        dup_addr_grp_list.extend([agname])

            for agname, [addr_grp, addr_grp_line] in self.address_group_map.iteritems():
                if (len(addr_grp.address_group_map) > 0):
                    addr_grp.add_group_members_to_list(self, ordered_list)
                if ((agname not in ordered_list) and
                    (agname not in dup_addr_grp_list)):
                    ordered_list.extend([agname])
                    dup_addr_grp_list.extend([agname])

            # for agname, [addr_grp, addr_grp_line] in self.address_group_map.iteritems():
            #     addr_grp.write_config(_cfg_fh, _log_fh,
            #                           _indent + '            ')

            for agname in ordered_list:
                self.get_address_group(agname).write_config(
                                      output_vd_cfg, _cfg_fh, _log_fh,
                                      _indent + '            ')


    def write_applications(self, output_vd_cfg, dup_app_list, _cfg_fh, _log_fh, _indent):
        if (len(self.application_map.keys()) > 0):
            for aname, [app, app_line] in self.application_map.iteritems():
                if (not aname in dup_app_list):
                    app.write_config(output_vd_cfg, _cfg_fh, _log_fh,
                                      _indent + '            ')
                    dup_app_list.extend( [ aname ] )

    def write_application_groups(self, output_vd_cfg, dup_app_grp_list, _cfg_fh, _log_fh, _indent):
        for agname in self.get_application_group_map().keys():
            self.get_application_group(agname).write_config(
                                       output_vd_cfg, _cfg_fh, _log_fh,
                                       _indent + '            ')


    def write_application_filters(self, output_vd_cfg, dup_app_fltr_list, _cfg_fh, _log_fh, _indent):
        for afname in self.get_application_filter_map().keys():
            self.get_application_filter(afname).write_config(
                                       output_vd_cfg, _cfg_fh, _log_fh,
                                       _indent + '            ')


    def write_url_categories(self, output_vd_cfg, dup_uc_list, _cfg_fh, _log_fh, _indent):
        if (len(self.url_category_map.keys()) > 0):
            for uc_name, [uc, uc_line] in self.url_category_map.iteritems():
                if (not uc_name in dup_uc_list):
                    uc.write_config(output_vd_cfg, _cfg_fh, _log_fh,
                                      _indent + '            ')
                    dup_uc_list.extend( [ uc_name ] )


    def write_schedules(self, output_vd_cfg, incl_schedules, _cfg_fh, _log_fh, _indent):
        if (len(self.schedule_map) > 0):
            for sname, [sched, sched_line] in self.schedule_map.iteritems():
                if (not sname in incl_schedules):
                    sched.write_config(output_vd_cfg, _cfg_fh, _log_fh,
                                       _indent + '            ')
                    incl_schedules.extend( [ sname ] )


    def write_services(self, output_vd_cfg, incl_services, _cfg_fh, _log_fh, _indent):
        if (len(self.service_map) > 0):
            for sname, [svc, svc_line] in self.service_map.iteritems():
                if (not sname in incl_services):
                    svc.write_config(output_vd_cfg, _cfg_fh, _log_fh,
                                     _indent + '            ')
                    incl_services.extend( [ sname ] )


    def write_zones(self, _cfg_fh, _log_fh, _indent):
        if (len(self.zone_map) > 0):
            for zname, zone in self.zone_map.iteritems():
                zone.write_config(_cfg_fh, _log_fh,
                                  _indent + '            ')


    def write_services_config(self, _tnt_nm, _cfg_fh, _log_fh, _indent):
        print("tenant: %s; url category map: %s" % (self.name, str(self.url_category_map)))

        print('%s    org-services %s {' % ( _indent, _tnt_nm), file=_cfg_fh)

        print('%s        objects {' % ( _indent ), file=_cfg_fh)

        if (len(self.address_map) > 0):
            print('%s            addresses {' % ( _indent ), file=_cfg_fh)

            for aname, [addr, addr_line] in self.address_map.iteritems():
                addr.write_config(_cfg_fh, _log_fh,
                                  _indent + '            ')

            print('%s            }' % ( _indent ), file=_cfg_fh)

        if (len(self.address_group_map) > 0):
            print('%s            address-groups {' % ( _indent ), file=_cfg_fh)

            ordered_list = [ ]
            for agname, [addr_grp, addr_grp_line] in self.address_group_map.iteritems():
                if (len(addr_grp.address_group_map) == 0):
                    if (agname not in ordered_list):
                        ordered_list.extend([agname])

            for agname, [addr_grp, addr_grp_line] in self.address_group_map.iteritems():
                if (len(addr_grp.address_group_map) > 0):
                    addr_grp.add_group_members_to_list(self, ordered_list)
                if (agname not in ordered_list):
                    ordered_list.extend([agname])

            # for agname, [addr_grp, addr_grp_line] in self.address_group_map.iteritems():
            #     addr_grp.write_config(_cfg_fh, _log_fh,
            #                           _indent + '            ')

            for agname in ordered_list:
                self.get_address_group(agname).write_config(
                                      _cfg_fh, _log_fh,
                                      _indent + '            ')

            print('%s            }' % ( _indent ), file=_cfg_fh)

        if (len(self.schedule_map) > 0):
            print('%s            schedules {' % ( _indent ), file=_cfg_fh)

            for sname, [sched, sched_line] in self.schedule_map.iteritems():
                sched.write_config(_cfg_fh, _log_fh,
                                   _indent + '            ')

            print('%s            }' % ( _indent ), file=_cfg_fh)

        if (len(self.service_map) > 0):
            print('%s            services {' % ( _indent ), file=_cfg_fh)

            for sname, [svc, svc_line] in self.service_map.iteritems():
                svc.write_config(_cfg_fh, _log_fh,
                                 _indent + '            ')

            print('%s            }' % ( _indent ), file=_cfg_fh)

        if (len(self.zone_map) > 0):
            print('%s            zones {' % ( _indent ), file=_cfg_fh)

            for zname, zone in self.zone_map.iteritems():
                zone.write_config(_cfg_fh, _log_fh,
                                  _indent + '            ')

            print('%s            }' % ( _indent ), file=_cfg_fh)

        print('%s        }' % ( _indent ), file=_cfg_fh)



        if (len(self.application_map) > 0 or \
            len(self.application_group_map) or \
            len(self.application_filter_map) > 0):
            print('%s        application-identification {' % ( _indent ), file=_cfg_fh)

        if (len(self.application_map) > 0):

            print('%s            user-defined-applications {' % ( _indent ), file=_cfg_fh)
            for aname, [app, app_line] in self.application_map.iteritems():
                app.write_config(_cfg_fh, _log_fh,
                                 _indent + '            ')

            print('%s            }' % ( _indent ), file=_cfg_fh)

        if (len(self.application_group_map) > 0):
            print('%s            application-groups {' % ( _indent ), file=_cfg_fh)

            ordered_list = [ ]
            for agname, [app_grp, app_grp_line] in self.application_group_map.iteritems():
                if (len(app_grp.application_group_map) == 0):
                    if (agname not in ordered_list):
                        ordered_list.extend([agname])

            for agname, [app_grp, app_grp_line] in self.application_group_map.iteritems():
                if (len(app_grp.application_group_map) > 0):
                    app_grp.add_group_members_to_list(self, ordered_list)
                if (agname not in ordered_list):
                    ordered_list.extend([agname])

            # for agname, [app_grp, app_grp_line] in self.application_group_map.iteritems():
            #     app_grp.write_config(_cfg_fh, _log_fh,
            #                           _indent + '            ')

            for agname in ordered_list:
                self.get_application_group(agname).write_config(
                                      _cfg_fh, _log_fh,
                                      _indent + '        ')

            for agname, [ag, ag_line] in self.application_group_map.iteritems():
                ag.write_config(_cfg_fh, _log_fh,
                                _indent + '            ')

            print('%s        }' % ( _indent ), file=_cfg_fh)

        if (len(self.application_filter_map) > 0):
            print('%s            application-filters {' % ( _indent ), file=_cfg_fh)

            for afname, [af, af_line] in self.application_filter_map.iteritems():
                af.write_config(_cfg_fh, _log_fh,
                                _indent + '            ')

            print('%s            }' % ( _indent ), file=_cfg_fh)

            print('%s        }' % ( _indent ), file=_cfg_fh)

        if (len(self.application_map) > 0 or \
            len(self.application_group_map) or \
            len(self.application_filter_map) > 0):
            print('%s        }' % ( _indent ), file=_cfg_fh)

        if (len(self.url_category_map) > 0):
            print('%s        url-filtering {' % ( _indent ), file=_cfg_fh)
            print('%s            user-defined-url-categories {' % ( _indent ), file=_cfg_fh)

            for uc_name, [uc, uc_line] in self.url_category_map.iteritems():
                uc.write_config(_cfg_fh, _log_fh,
                                _indent + '        ')

            print('%s            }' % ( _indent ), file=_cfg_fh)
            print('%s        }' % ( _indent ), file=_cfg_fh)



        print('%s        security {' % ( _indent ), file=_cfg_fh)
        # if (tnt.ngfw is None):
        #     print('ngfw for tnt ' + tnt.name + ' is None')
        if (self.ngfw is not None):
            self.ngfw.write_config(_cfg_fh, _log_fh, _indent + '            ')
        print('%s        }' % ( _indent ), file=_cfg_fh)


        print('%s    }' % ( _indent ), file=_cfg_fh)
        print('', file=_cfg_fh)






