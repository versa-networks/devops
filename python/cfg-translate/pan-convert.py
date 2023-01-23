#! /usr/bin/python
#
#  pan-convert.py - Convert Palo Alto config to Versa config
# 
#  This file has the code to translate Palo Alto config to Versa config
# 
#  Copyright (c) 2019, Versa Networks, Inc.
#  All rights reserved.
#


from __future__ import print_function
from optparse import OptionParser
import subprocess,traceback,sys,os,re
import string
import csv, logging
from enum import Enum
from versa.Address import Address
from versa.Address import AddressType
from versa.AddressGroup import AddressGroup
from versa.Application import Application
from versa.ApplicationGroup import ApplicationGroup
from versa.ApplicationFilter import ApplicationFilter
from versa.URLCategory import URLCategory
from versa.Schedule import Schedule
from versa.Service import Service
from versa.ServiceGroup import ServiceGroup
from versa.NATPool import NATPool
from versa.NextGenFirewall import NextGenFirewall
from versa.FirewallRule import FirewallRuleAction
from versa.NextGenFirewallRule import NextGenFirewallRule
from versa.VersaConfig import VersaConfig
import xml.etree.ElementTree as ET
import ipaddress


cmn_template_name = 'Provider-DataStore'
cmn_tenant_name = 'Provider'
LOG_FILENAME = 'versa-cfg-translate.log'

strict_checks = False
# strict_checks = True
tnt_xlate_map = { }
input_line_num = 0
predef_apps = {  }
predef_app_map = {  }



def load_application_objects_into_tenant(_tnt_xml, _tnt):

    # Process application objects
    applications = _tnt_xml.findall('./application/entry')
    for app in applications:
        aname = app.attrib['name'].replace(' ', '_')
        cur_app = Application(aname, input_line_num, False)
        desc = app.find('./description')
        if (desc is not None):
            cur_app.set_description(desc.text.encode('utf-8'), input_line_num)

        v_logger.info("Tenant %s: Adding Application %s to current tenant" % \
                      (_tnt.name, cur_app.name))
        _tnt.add_application(cur_app, input_line_num)



def load_app_groups_into_tenant(_tnt_xml, _tnt):

    # Process application groups
    app_groups = _tnt_xml.findall('./application-group/entry')
    for ag in app_groups:
        agname = ag.attrib['name'].replace(' ', '_')

        cur_app_grp = _tnt.get_application_group(agname)
        if (cur_app_grp is None):
            cur_app_grp = ApplicationGroup(agname, input_line_num, False)
            _tnt.add_application_group(cur_app_grp, input_line_num)

        ag_members = ag.findall('./members/member')
        for m in ag_members:

            # check if the application is user defined application
            aname = m.text.replace(' ', '_')
            member_added = False

            app = _tnt.get_application(aname)
            sh_tnt = _tnt.get_shared_tenant()
            if (app is not None):
                v_logger.info("tenant %s: adding application group '%s' " \
                              " with custom application member '%s'" % \
                              ( _tnt.name, agname, aname ))
                cur_app_grp.add_application(app, input_line_num)
                member_added = True

            if (not member_added):
                app_grp = _tnt.get_application_group(aname)
                if (app_grp is not None):
                    v_logger.info("tenant %s: adding application group '%s' " \
                                  " with custom application group " \
                                  "member '%s'" % \
                                  ( _tnt.name, agname, aname ))
                    cur_app_grp.add_application_group(app_grp, input_line_num)
                    member_added = True

            if (not member_added and sh_tnt is not None):
                app = sh_tnt.get_application(aname)
                if (app is not None):
                    v_logger.info("tenant %s: adding application group '%s' " \
                                  " with (shared) custom application " \
                                  "member '%s'" % \
                                  ( _tnt.name, agname, aname ))
                    cur_app_grp.add_application(app, input_line_num)
                    member_added = True
                else:
                    app_grp = sh_tnt.get_application_group(aname)
                    if (app_grp is not None):
                        v_logger.info("tenant %s: adding application group " \
                                      "'%s' with (shared) custom " \
                                      "application group member '%s'" % \
                                      ( _tnt.name, agname, aname ))
                        cur_app_grp.add_application_group(app_grp, \
                                                          input_line_num)
                        member_added = True

            if (not member_added):
                # check if the application is predefined application
                if (aname in predef_app_map.keys()):
                    app = predef_app_map[aname]
                    v_logger.info("tenant %s: adding application group '%s' " \
                                  " with predefined application member '%s'" % \
                                  ( _tnt.name, agname, aname ))
                    cur_app_grp.add_application(app, input_line_num)
                    member_added = True

            if (not member_added):
                v_logger.error("tenant %s: while adding application " \
                               "group '%s', member application '%s' not " \
                               "found in predefined or user-defined " \
                               "application list" % \
                               ( _tnt.name, agname, aname ))



def load_app_filters_into_tenant(_tnt_xml, _tnt):

    # Process application filters
    app_filters = _tnt_xml.findall('./application-filter/entry')
    for af in app_filters:
        afname = af.attrib['name'].replace(' ', '_')

        cur_app_filter = _tnt.get_application_filter(afname)
        if (cur_app_filter is None):
            cur_app_filter = ApplicationFilter(afname, input_line_num, False)
            _tnt.add_application_filter(cur_app_filter, input_line_num)

        cat = af.findall('./category/member')
        for c in cat:
            cur_app_filter.add_application_filter('family', c.text.strip(), input_line_num)

        subcat = af.findall('./subcategory/member')
        for c in subcat:
            sc = c.text.strip()
            if sc in predef_subfamilies.keys():
                cur_app_filter.add_application_filter('subfamily', c.text.strip(), input_line_num)
            else:
                v_logger.error("Tenant %s; application filter %s; " \
                               "subfamily %s not found" % \
                               (_tnt.name, cur_app_filter.name, sc))

        risk = af.findall('./risk/member')
        for c in risk:
            cur_app_filter.add_application_filter('risk', c.text.strip(), input_line_num)

        productivity = af.findall('./productivity/member')
        for c in productivity:
            cur_app_filter.add_application_filter('productivity', c.text.strip(), input_line_num)

        tag = af.findall('./tag/member')
        for c in tag:
            cur_app_filter.add_application_filter('tag', c.text.strip(), input_line_num)




def load_url_category_objects_into_tenant(_tnt_xml, _tnt):

    # Process custom url category objects
    url_categories = _tnt_xml.findall('./profiles/custom-url-category/entry')
    for uc in url_categories:
        aname = uc.attrib['name'].replace(' ', '_')
        cur_uc = URLCategory(aname, input_line_num, False)
        desc = uc.find('./description')
        if (desc is not None):
            cur_uc.set_description(desc.text.encode('utf-8'), input_line_num)

        urls = uc.findall('./list/member')
        for url in urls:
            url_str = url.text.strip()
            if ('*' in url_str):
                cur_uc.add_pattern(url_str.replace('*', '.*'))
            else:
                cur_uc.add_host(url_str)

        v_logger.info("Tenant %s: Adding URL Category %s to current tenant" % \
                      (_tnt.name, cur_uc.name))
        _tnt.add_url_category(cur_uc, input_line_num)



def load_address_objects_into_tenant(_tnt_xml, _tnt):

    # Process address objects
    addresses = _tnt_xml.findall('./address/entry')
    for addr in addresses:
        aname = addr.attrib['name'].replace(' ', '_')
        cur_addr = Address(aname, input_line_num, False)
        ip_nm = addr.find('./ip-netmask')
        add_flag = False
        if (ip_nm is not None):
            cur_addr.set_addr_value(ip_nm.text.replace(' ', '_'), \
                                    input_line_num)
            cur_addr.set_addr_type(AddressType.IP_V4_PREFIX,
                                   input_line_num)
            add_flag = True

        if (not add_flag):
            fqdn = addr.find('./fqdn')
            if (fqdn is not None):
                cur_addr.set_addr_value(fqdn.text, input_line_num)
                cur_addr.set_addr_type(AddressType.FQDN,
                                       input_line_num)
                add_flag = True

        if (not add_flag):
            v_logger.error("Tenant %s: Address %s unsupported" % \
                           (_tnt.name, cur_addr.name))
            continue

        v_logger.info("Tenant %s: Adding Address %s to current tenant" % \
                      (_tnt.name, cur_addr.name))
        _tnt.add_address(cur_addr, input_line_num)



def load_address_group_objects_into_tenant(_tnt_xml, _tnt):

    # Process address groups
    addr_groups = _tnt_xml.findall('./address-group/entry')
    for ag in addr_groups:
        agname = ag.attrib['name'].replace(' ', '_')

        cur_addr_grp = _tnt.get_address_group(agname)
        if (cur_addr_grp is None):
            cur_addr_grp = AddressGroup(agname, input_line_num, False)
            _tnt.add_address_group(cur_addr_grp, input_line_num)

        ag_members = ag.findall('./members/member')
        for m in ag_members:
            addr = m.text.replace(' ', '_')
            v_logger.info("tenant %s: adding address group '%s' " \
                          " with address member '%s'" % \
                          ( _tnt.name, agname, addr ))
            cur_addr_grp.add_address(addr, input_line_num)

        ag_members = ag.findall('./static/member')
        for m in ag_members:
            addr = m.text.replace(' ', '_')
            v_logger.info("tenant %s: adding address group '%s' " \
                          " with address member '%s'" % \
                          ( _tnt.name, agname, addr ))
            cur_addr_grp.add_address(addr, input_line_num)



def load_external_address_group_objects_into_tenant(_tnt_xml, _tnt):

    # Process address groups
    addr_groups = _tnt_xml.findall('./external-list/entry')
    for ag in addr_groups:
        entry = ag.find('type/ip')
        if (entry is not None):
            agname = ag.attrib['name'].replace(' ', '_')

            cur_addr_grp = _tnt.get_address_group(agname)
            if (cur_addr_grp is None):
                cur_addr_grp = AddressGroup(agname, input_line_num, False)
                _tnt.add_address_group(cur_addr_grp, input_line_num)

            url = entry.find('./url').text
            ix = url.rfind('/')
            fn = url[ix + 1:]
            v_logger.info("tenant %s: adding address group '%s' " \
                          " with file name '%s'" % \
                          ( _tnt.name, agname, fn ))
            cur_addr_grp.add_filename(fn, input_line_num)



def load_external_url_category_objects_into_tenant(_tnt_xml, _tnt):

    # Process address groups
    url_categories = _tnt_xml.findall('./external-list/entry')
    for url_cat in url_categories:
        entry = url_cat.find('type/url')
        if (entry is not None):
            url_cat_name = url_cat.attrib['name'].replace(' ', '_')

            cur_url_cat = _tnt.get_url_category(url_cat_name)
            if (cur_url_cat is None):
                cur_url_cat = URLCategory(url_cat_name, input_line_num, False)
                _tnt.add_url_category(cur_url_cat, input_line_num)

            url = entry.find('./url').text
            ix = url.rfind('/')
            fn = url[ix + 1:]
            v_logger.info("tenant %s: adding url category '%s' " \
                          " with file name '%s'" % \
                          ( _tnt.name, url_cat_name, fn ))
            cur_url_cat.set_filename(fn, input_line_num)



def load_service_objects_into_tenant(_tnt_xml, _tnt):

    # Process service objects
    services = _tnt_xml.findall('./service/entry')
    for svc in services:
        sname = svc.attrib['name'].replace(' ', '_')
        cur_svc = Service(sname, input_line_num, False)
        tcp = svc.find('./protocol/tcp')
        udp = svc.find('./protocol/udp')
        if (tcp is not None):
            port = tcp.find('port').text
            cur_svc.set_proto('tcp', input_line_num)
            cur_svc.set_dst_port(port, input_line_num)
        elif (udp is not None):
            port = udp.find('port').text
            cur_svc.set_proto('udp', input_line_num)
            cur_svc.set_dst_port(port, input_line_num)

        v_logger.info("tenant %s: Adding Service %s" % \
                      (tnt, sname))
        _tnt.add_service(cur_svc, input_line_num)



def load_service_group_objects_into_tenant(_tnt_xml, _tnt):

    # Process service group objects
    svc_groups = _tnt_xml.findall('./service-group/entry')
    for sg in svc_groups:
        sgname = sg.attrib['name'].replace(' ', '_')

        cur_svc_grp = cur_tnt.get_service_group(sgname)
        if (cur_svc_grp is None):
            cur_svc_grp = ServiceGroup(sgname, input_line_num, False)
            _tnt.add_service_group(cur_svc_grp, input_line_num)

        sg_members = sg.findall('./members/member')
        for m in sg_members:
            svc = m.text
            v_logger.info("tenant %s: adding service group '%s' " \
                          " with service member '%s'" % \
                          ( tnt, sgname, svc ))
            cur_svc_grp.add_service(svc, input_line_num)



def load_schedule_objects_into_tenant(_tnt_xml, _tnt):

    # Process service objects
    schedules = _tnt_xml.findall('./schedule/entry')
    for s in schedules:
        sname = s.attrib['name'].replace(' ', '_')

        nr = s.findall('./schedule-type/non-recurring/member')
        if (len(nr) > 0):
            cur_sched = Schedule(sname, input_line_num, False, False)
            for dt in nr:
                cur_sched.add_non_recurring_day_time(dt.text.strip(),
                                                     input_line_num)
        else:
            cur_sched = Schedule(sname, input_line_num, False, True)

            daily = s.findall('./schedule-type/recurring/daily/member')
            for d in daily:
                cur_sched.add_recurring_day_time('daily',
                                                  d.text.strip(),
                                                  input_line_num)

            weekly = s.findall('./schedule-type/recurring/weekly/*')
            for w in weekly:
                times = w.findall('./member')
                for t in times:
                    cur_sched.add_recurring_day_time(w.tag,
                                                     t.text.strip(),
                                                     input_line_num)

            v_logger.info("tenant %s: Adding Schedule %s" % \
                          (tnt, sname))
        _tnt.add_schedule(cur_sched, input_line_num)



def process_rule_address_match(_vr, _cur_tnt, _amap, _is_src_match):

    sh_tnt = _cur_tnt.get_shared_tenant()
    for addr in _amap.keys():

        # check if there is an address object with this name
        add_flag = False
        ao = _cur_tnt.get_address(addr)
        if (ao is not None):
            v_logger.info("tenant %s: adding ngfw rule '%s' " \
                          " with src/dst address '%s'" % \
                          ( _cur_tnt.name, _vr.name, addr ))
            if (_is_src_match):
                _vr.add_src_addr(addr, input_line_num)
            else:
                _vr.add_dst_addr(addr, input_line_num)
            add_flag = True

        # check if there is an address group object with this name
        if (not add_flag):
            ago = _cur_tnt.get_address_group(addr)
            if (ago is not None):
                v_logger.info("tenant %s: adding ngfw rule '%s' " \
                              " with src/dst address group '%s'" % \
                              ( _cur_tnt.name, _vr.name, addr ))
                if (_is_src_match):
                    _vr.add_src_addr_grp(addr, input_line_num)
                else:
                    _vr.add_dst_addr_grp(addr, input_line_num)
                add_flag = True

        # check if there is an address object with this name in the
        # shared tenant
        if (not add_flag):
            ao = sh_tnt.get_address(addr)
            if (ao is not None):
                v_logger.info("tenant %s: adding ngfw rule '%s' " \
                              " with src/dst address (shared) '%s'" % \
                              ( _cur_tnt.name, _vr.name, addr ))
                if (_is_src_match):
                    _vr.add_src_addr(addr, input_line_num)
                else:
                    _vr.add_dst_addr(addr, input_line_num)
                add_flag = True


        # check if there is an address group object with this name
        # in the shared tenant
        if (not add_flag):
            ago = sh_tnt.get_address_group(addr)
            if (ago is not None):
                v_logger.info("tenant %s: adding ngfw rule '%s' " \
                              " with src/dst address group (shared) "
                              "'%s'" % \
                              ( _cur_tnt.name, _vr.name, addr ))
                if (_is_src_match):
                    _vr.add_src_addr_grp(addr, input_line_num)
                else:
                    _vr.add_dst_addr_grp(addr, input_line_num)
                add_flag = True

        # check if an IP address was referenced as an object, and
        # add the new IP address object if applicable
        if (not add_flag):
            try:
                if ('/' in addr):
                    ipaddr = ipaddress.ip_network(unicode(addr))
                    cur_addr = Address(addr, input_line_num, False)
                    cur_addr.set_addr_value(addr, input_line_num)
                else:
                    ipaddr = ipaddress.ip_address(unicode(addr))
                    cur_addr = Address(addr, input_line_num, False)
                    cur_addr.set_addr_value(addr + '/32', \
                                            input_line_num)
                cur_addr.set_addr_type(AddressType.IP_V4_PREFIX,
                                       input_line_num)
                v_logger.info("Tenant %s: Adding Address %s to " \
                              "current tenant" % \
                              (_cur_tnt.name, cur_addr.name))
                _cur_tnt.add_address(cur_addr, input_line_num)
                if (_is_src_match):
                    _vr.add_src_addr(addr, input_line_num)
                else:
                    _vr.add_dst_addr(addr, input_line_num)
                add_flag = True
            except:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                v_logger.error("Tenant %s: while adding rule %s to " \
                               "current tenant, error while parsing " \
                               "address (%s)" % \
                               ( _cur_tnt.name, _vr.name, \
                                 repr(traceback.format_exception_only( \
                                                      exc_type, exc_value)) ))
                #print("Error: unable to parse ip addr " + addr)
                #print("Error Details:")
                #print("    " + \
                #      repr(traceback.format_exception_only( \
                #                                exc_type, exc_value)))
                pass

        # Check if the object matches a country name
        if (not add_flag):
            if (addr in predef_countries.keys()):
                if (_is_src_match):
                    _vr.add_src_addr_region(addr, input_line_num)
                else:
                    _vr.add_dst_addr_region(addr, input_line_num)

        # No reference found for the referenced address object
        if (not add_flag):
            v_logger.error("tenant %s: while adding ngfw rule " \
                           "'%s' no address or address group " \
                           "found with name '%s'" % \
                           ( _cur_tnt.name, _vr.name, addr ))




# Get command line arguments
o_parser = OptionParser()
o_parser.add_option("-i", "--inputfile", dest="infile",
                    help="Path to Palo Alto config file in XML format", \
                    metavar="infilepath")
o_parser.add_option("-z", "--zonefile", dest="zonefile",
                    help="Path to zone/interface CSV file", \
                    metavar="zonefilepath")
o_parser.add_option("-a", "--appfile", dest="appfile",
                    help="Path to Versa predefined applications CSV file", \
                    metavar="appfilepath")
o_parser.add_option("-s", "--subfamiliesfile", dest="subfamiliesfile",
                    help="Path to Versa application subfamiles CSV file", \
                    metavar="subfamiliesfilepath")
o_parser.add_option("-u", "--urlfile", dest="urlfile",
                    help="Path to Versa predefined URL categories XML file", \
                    metavar="urlfilepath")
o_parser.add_option("-c", "--countriesfile", dest="countriesfile",
                    help="Path to Versa predefined countries XML file", \
                    metavar="countriesfilepath")
o_parser.add_option("-T", "--template", dest="template",
                    help="Template name", metavar="template")
o_parser.add_option("-D", "--device", dest="device",
                    help="Device name", metavar="device")
o_parser.add_option("-o", "--outputdir", dest="outdir",
                    help="Path to output directory", metavar="outdir")
o_parser.add_option("-v", "--versa-paths-file", dest="vpathsfile",
                    help="Path to Versa path segments file", \
                    metavar="vpathsfile")
(c_options, c_args) = o_parser.parse_args()



# Ensure that only one of device or template is specified if transation is
# to be done for versa director
if (c_options.template and c_options.device):
    print("To generate config that can be loaded into the Versa Director " + \
          "configuration, please specify either the Config Template name " + \
          "or the Device name for which config should be generated\n")
    exit(1)



# open predefined applications file
if (c_options.appfile):

    try:
        app_fh = open(c_options.appfile, 'r')
        app_csv = csv.reader(app_fh)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("Error: unable to open predefined applications csv file " + \
              c_options.appfile + " for reading")
        print("Error Details:")
        print("    " + \
              repr(traceback.format_exception_only(exc_type, exc_value)))
        exit(1)
else:
    print("Please specify the input Palo Alto config file, " + \
          "predefined applications CSV file, predefined URL categories " + \
          "XML file, countries CSV file, interface/zone CSV file, " + \
          "subfamilies file, and the output directory path\n")
    exit(1)


# open predefined URL categories XML file
if (c_options.urlfile):

    try:
        url_tree = ET.parse(c_options.urlfile)
        url_root = url_tree.getroot()
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("Error: unable to parse URL categories XML file " + \
              c_options.urlfile)
        print("Error Details:")
        print("    " + \
              repr(traceback.format_exception_only(exc_type, exc_value)))
        exit(1)
else:
    print("Please specify the input Palo Alto config file, " + \
          "predefined applications CSV file, predefined URL categories " + \
          "XML file, countries CSV file, interface/zone CSV file, " + \
          "subfamilies file, and the output directory path\n")
    exit(1)


# open predefined countries file
if (c_options.countriesfile):

    try:
        countries_fh = open(c_options.countriesfile, 'r')
        countries_csv = csv.reader(countries_fh)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("Error: unable to open predefined countries csv file " + \
              c_options.coutriesfile + " for reading")
        print("Error Details:")
        print("    " + \
              repr(traceback.format_exception_only(exc_type, exc_value)))
        exit(1)
else:
    print("Please specify the input Palo Alto config file, " + \
          "predefined applications CSV file, predefined URL categories " + \
          "XML file, countries CSV file, interface/zone CSV file, " + \
          "subfamilies file, and the output directory path\n")
    exit(1)


# open predefined subfamiles file
if (c_options.subfamiliesfile):

    try:
        subfamilies_fh = open(c_options.subfamiliesfile, 'r')
        subfamilies_csv = csv.reader(subfamilies_fh)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("Error: unable to open predefined subfamilies csv file " + \
              c_options.subfamiliesile + " for reading")
        print("Error Details:")
        print("    " + \
              repr(traceback.format_exception_only(exc_type, exc_value)))
        exit(1)
else:
    print("Please specify the input Palo Alto config file, " + \
          "predefined applications CSV file, predefined URL categories " + \
          "XML file, countries CSV file, interface/zone CSV file, " + \
          "subfamilies file, and the output directory path\n")
    exit(1)


# open input file
if (c_options.infile):

    try:
        xml_tree = ET.parse(c_options.infile)
        xml_root = xml_tree.getroot()
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("Error: unable to parse XML input file " + \
              c_options.infile)
        print("Error Details:")
        print("    " + \
              repr(traceback.format_exception_only(exc_type, exc_value)))
        exit(1)
else:
    print("Please specify the input Palo Alto config file, " + \
          "predefined applications CSV file, predefined URL categories " + \
          "XML file, countries CSV file, interface/zone CSV file, " + \
          "subfamilies file, and the output directory path\n")
    exit(1)


# open zone/interface file
if (c_options.zonefile):

    try:
        zone_fh = open(c_options.zonefile, 'r')
        zone_csv = csv.reader(zone_fh)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("Error: unable to open zone/interface csv file " + \
              c_options.zonefile + " for reading")
        print("Error Details:")
        print("    " + \
              repr(traceback.format_exception_only(exc_type, exc_value)))
        exit(1)
else:
    print("Please specify the input Palo Alto config file, " + \
          "predefined applications CSV file, predefined URL categories " + \
          "XML file, countries CSV file, interface/zone CSV file, " + \
          "subfamilies file, and the output directory path\n")
    exit(1)


# create output dir
if (c_options.outdir):
    if ((os.path.isdir(c_options.outdir) != True) or
        (os.path.exists(c_options.outdir) != True)):
        try:
            os.mkdir(c_options.outdir)
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print("Error creating output dir: " + c_options.outdir)
            print("Error Details:")
            print("    " + \
                  repr(traceback.format_exception_only(exc_type, exc_value)))
            print("\nPlease enter a valid directory path where " + \
                  "the output files will be written\n")
            exit(1)
else:
    print("Please specify the input Palo Alto config file, " + \
          "predefined applications CSV file, predefined URL categories " + \
          "XML file, countries CSV file, interface/zone CSV file, " + \
          "subfamilies file, and the output directory path\n")
    exit(1)



# open output file
bname = os.path.splitext(os.path.basename(c_options.infile))[0]
outfile = c_options.outdir + '/' + bname + '.cfg'
try:
    out_fh = open(outfile, 'w')
except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    print("Error: unable to open out file " + \
          c_options.outdir + "/" + outfile + " for writing")
    print("Error Details:")
    print("    " + \
          repr(traceback.format_exception_only(exc_type, exc_value)))
    exit(1)




# open output csv file
bname = os.path.splitext(os.path.basename(c_options.infile))[0]
csv_outfile = c_options.outdir + '/' + bname + '.csv'
try:
    csv_out_fh = open(csv_outfile, 'w')
except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    print("Error: unable to open out file " + \
          c_options.outdir + "/" + csv_outfile + " for writing")
    print("Error Details:")
    print("    " + \
          repr(traceback.format_exception_only(exc_type, exc_value)))
    out_fh.close()
    exit(1)




# open log file
logfile = c_options.outdir + '/' + bname + '.json'
try:
    log_fh = open(logfile, 'w')
except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    print("Error: unable to open log file " + \
          c_options.outdir + "/" + logfile + " for writing")
    print("Error Details:")
    print("    " + \
          repr(traceback.format_exception_only(exc_type, exc_value)))
    csv_out_fh.close()
    out_fh.close()
    exit(1)



# get the log file and create it
try:
    logpath = os.path.join(c_options.outdir, LOG_FILENAME)
    logging.basicConfig(filename='/dev/null', level=logging.DEBUG)
    formatter = logging.Formatter('[%(asctime)s] '
                                  '[%(levelname)s] %(message)s')
    fh = logging.FileHandler(logpath)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    v_logger = logging.getLogger(logpath)
    v_logger.addHandler(fh)
except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    print("Error: unable to create logger with " + logpath)
    print("Error Details:")
    print("    " + \
          repr(traceback.format_exception_only(exc_type, exc_value)))
    exit(1)




versa_cfg = VersaConfig('VersaCfg_From_PAN_' + bname)
versa_cfg.set_logger(v_logger)

pan_intf_zone_map = { }
versa_intf_zone_map = { }


# populate the zone/interface map
cur_line_num = 0
pan_versa_intf_map = { }
for row in zone_csv:
    cur_line_num = cur_line_num + 1

    # ignore invalid rows
    if (row[0].startswith('#')):
        continue
    if (len(row) < 4):
        continue

    # Update interface zone map
    pan_intf_zone_map[row[0]] = row
    versa_intf_zone_map[row[3]] = row
    versa_intf_zone_map[row[3]].append(str(cur_line_num))

    src_tnt =  row[6]
    tnt =  row[7]
    if (not versa_cfg.has_tenant(tnt)):
        versa_cfg.add_tenant(tnt, '0')
        tnt_xlate_map[src_tnt] = [ tnt ]

zone_fh.close()
tnt_names = versa_cfg.get_tenants()


# Add the interfaces, networks and zones
for v_ifname, ifinfo in versa_intf_zone_map.iteritems():
    ifinfo = versa_intf_zone_map[v_ifname]
    tnt = ifinfo[7]
    cur_tnt = versa_cfg.get_tenant(tnt, '0')
    v_logger.info("%s:%s: adding versa interface %s to tenant %s; " \
                  "network %s; zone %s; pan interface %s" % \
                  ( c_options.zonefile, ifinfo[8], \
                    v_ifname, tnt, ifinfo[2], ifinfo[1], ifinfo[0] ))
    versa_cfg.add_network_and_interface(ifinfo[2], v_ifname)

    if (len(ifinfo[2]) > 0):
        cur_tnt.add_zone_network(ifinfo[1], \
                                 ifinfo[2], ifinfo[8])
    else:
        cur_tnt.add_zone_interface(ifinfo[1], \
                                   v_ifname, ifinfo[8])


# Populate the predefined applications
for row in app_csv:
    if (len(row) <= 0 or len(row[0]) <= 0):
        continue
    try:
        appid = int(row[0])
    except:
        continue

    appname = row[3]
    predef_apps[appname] = row

    cur_app = Application(appname, input_line_num, True)
    predef_app_map[appname] = cur_app

app_fh.close()
versa_cfg.set_predef_app_map(predef_app_map)


# Populate the predefined url categories
predef_url_categories = {  }
predef_url_categories_map = {  }
url_cat_list = url_root.findall('./categories/entity/subtype')
for c in url_cat_list:

    url_cat_name = c.text
    predef_apps[url_cat_name] = c

    cur_url_cat = URLCategory(url_cat_name, input_line_num, True)
    predef_url_categories_map[url_cat_name] = cur_url_cat
versa_cfg.set_predef_url_cat_map(predef_url_categories_map)


# Populate the predefined countries
predef_countries = {  }
count = 0
for row in countries_csv:
    count = count + 1
    if (len(row) < 5):
        continue

    code_index = len(row) - 4
    code = row[code_index].strip()
    #print("row %d; code index %d; code : '%s'" % ( count, code_index, code ))
    predef_countries[code] = row

countries_fh.close()
versa_cfg.set_predef_countries_map(predef_countries)



# Populate the predefined subfamilies
predef_subfamilies = {  }
for row in subfamilies_csv:
    subfamily = row[0]
    predef_subfamilies[subfamily] = row

subfamilies_fh.close()
versa_cfg.set_predef_subfamilies_map(predef_subfamilies)



# Load the shared vsys config into the Provider-DataStore tenant
versa_cfg.add_tenant('Provider-DataStore', '0')
shared_tnt = versa_cfg.get_tenant('Provider-DataStore', '0')
shared_xml = xml_root.find('./shared')
tnt_xlate_map['shared'] = [ 'Provider-DataStore' ]
versa_cfg.set_tenant_xlate_map(tnt_xlate_map)
if (shared_xml is not None):

    # Process applications
    load_application_objects_into_tenant(shared_xml, shared_tnt)

    # Process application groups
    load_app_groups_into_tenant(shared_xml, shared_tnt)

    # Process application filters
    load_app_filters_into_tenant(shared_xml, shared_tnt)

    # Process custom url categories
    load_url_category_objects_into_tenant(shared_xml, shared_tnt)

    # Process address objects
    load_address_objects_into_tenant(shared_xml, shared_tnt)

    # Process external list adddress objects
    load_external_address_group_objects_into_tenant(shared_xml, shared_tnt)

    # Process external list url category objects
    load_external_url_category_objects_into_tenant(shared_xml, shared_tnt)

    # Process address group objects
    load_address_group_objects_into_tenant(shared_xml, shared_tnt)

    # Process service objects
    load_service_objects_into_tenant(shared_xml, shared_tnt)

    # Process service group objects
    load_service_group_objects_into_tenant(shared_xml, shared_tnt)

    # Process schedule objects
    load_schedule_objects_into_tenant(shared_xml, shared_tnt)



# Process all tenants from the pan cfg file
vsys_list = xml_root.findall('./devices/entry/vsys/entry')
for v in vsys_list:

    # Get current tenant
    src_tnt = v.attrib['name'].replace(' ', '_')
    tnt = tnt_xlate_map[src_tnt][0]
    cur_tnt = versa_cfg.get_tenant(tnt, '0')
    cur_tnt.set_shared_tenant(shared_tnt)

    # Process applications
    load_application_objects_into_tenant(v, cur_tnt)

    # Process application groups
    load_app_groups_into_tenant(v, cur_tnt)

    # Process application filters
    load_app_filters_into_tenant(v, cur_tnt)

    # Process custom url categories
    load_url_category_objects_into_tenant(v, cur_tnt)

    # Process address objects
    load_address_objects_into_tenant(v, cur_tnt)

    # Process address group objects
    load_address_group_objects_into_tenant(v, cur_tnt)

    # Process external list adddress objects
    load_external_address_group_objects_into_tenant(v, cur_tnt)

    # Process external list url category objects
    load_external_url_category_objects_into_tenant(v, cur_tnt)

    # Process service objects
    load_service_objects_into_tenant(v, cur_tnt)

    # Process service group objects
    load_service_group_objects_into_tenant(v, cur_tnt)

    # Process schedule objects
    load_schedule_objects_into_tenant(v, cur_tnt)

    # Process security rules
    cur_ngfw = NextGenFirewall(cur_tnt.name + '_policy',
                               input_line_num, False)
    cur_tnt.set_next_gen_firewall(cur_ngfw, input_line_num)

    rules = v.findall('./rulebase/security/rules/entry')
    for r in rules:
        rname = r.attrib['name'].replace(' ', '_')
        vr = NextGenFirewallRule(rname, input_line_num, False)
        vr.set_tenant(cur_tnt)
        cur_ngfw.add_rule(vr)

        # process source zone match
        src_zones = r.findall('./from/member')
        zm = { }
        for sz in src_zones:
            zm[sz.text.replace(' ', '_')] = input_line_num
        if (len(zm.keys()) > 0 and not 'any' in zm.keys()):
            vr.set_src_zone_map(zm)

        # process destination zone match
        dst_zones = r.findall('./to/member')
        zm = { }
        for dz in dst_zones:
            zm[dz.text.replace(' ', '_')] = input_line_num
        if (len(zm.keys()) > 0 and not 'any' in zm.keys()):
            vr.set_dst_zone_map(zm)

        # process source address match
        src_addresses = r.findall('./source/member')
        amap = { }
        for sa in src_addresses:
            amap[sa.text.replace(' ', '_')] = input_line_num

        if (len(amap.keys()) > 0 and not 'any' in amap.keys()):
            process_rule_address_match(vr, cur_tnt, amap, True)

        # process destination address match
        dst_addresses = r.findall('./destination/member')
        dmap = { }
        for da in dst_addresses:
            dmap[da.text.replace(' ', '_')] = input_line_num

        if (len(dmap.keys()) > 0 and not 'any' in dmap.keys()):
            process_rule_address_match(vr, cur_tnt, dmap, False)

        # process service match
        services = r.findall('./service/member')
        smap = { }
        for svc in services:
            smap[svc.text.replace(' ', '_')] = input_line_num

        if (len(smap.keys()) > 0 and not 'any' in smap.keys()):
            vr.set_service_map(smap)

        # process service group match
        service_groups = r.findall('./service-group/member')
        sg_map = { }
        for sg in service_groups:
            sg_map[sg.text.replace(' ', '_')] = input_line_num

        if (len(sg_map.keys()) > 0 and not 'any' in sg_map.keys()):
            for sg in sg_map.keys():
                vr.add_service(sg, sg_map[sg])

        # process service match
        schedule = r.find('./schedule')
        if (schedule is not None):
            vr.set_schedule(schedule.text.strip().replace(' ', '_'), \
                            input_line_num)

        # process application match
        applications = r.findall('./application/member')
        amap = { }
        for app in applications:
            amap[app.text.replace(' ', '_')] = input_line_num

        if (len(amap.keys()) > 0 and not 'any' in amap.keys()):
            vr.set_application_map(amap)

        # process url-category match
        url_categories = r.findall('./category/member')
        uc_map = { }
        for uc in url_categories:
            #uc_name = uc.text.replace(' ', '_').replace('_', '-')
            uc_name = uc.text.replace(' ', '_')
            uc_map[uc_name] = input_line_num

        if (len(uc_map.keys()) > 0 and not 'any' in uc_map.keys()):
            vr.set_url_category_map(uc_map)

        # process action match
        action = r.find('./action')
        if (action is not None):
            astr = action.text.strip()
            if (astr == 'allow'):
                vr.set_action(FirewallRuleAction.ALLOW, input_line_num)
            elif (astr == 'deny'):
                vr.set_action(FirewallRuleAction.DENY, input_line_num)



versa_cfg.replace_address_by_address_group()
versa_cfg.replace_service_group_by_service_members()
versa_cfg.check_config(strict_checks)
versa_cfg.write_config(tnt_xlate_map, c_options.template,
                       c_options.device, out_fh, log_fh)



# Create the CSV file for rule comparison of translated rules
print('#Tenant,SerialNum,RuleName,SrcZone,SrcAddr,DstZone,DstAddr,' \
      'Schedule,Services,Service Groups,Application,URL Category,User,Action', file=csv_out_fh)

# Process all tenants from the pan cfg file
vsys_list = xml_root.findall('./devices/entry/vsys/entry')
for v in vsys_list:

    # Get current tenant
    src_tnt = v.attrib['name'].replace(' ', '_')
    tnt = tnt_xlate_map[src_tnt][0]
    cur_tnt = versa_cfg.get_tenant(tnt, '0')
    cur_ngfw = cur_tnt.get_next_gen_firewall()

    # Iterate through and print information for the various rules
    count = 0
    rules = v.findall('./rulebase/security/rules/entry')
    for r in rules:
        count = count + 1
        orig_rname = r.attrib['name']
        rname = r.attrib['name'].replace(' ', '_')
        xrule = cur_ngfw.get_rule(rname)

        # Print tenant
        print('%s,' % src_tnt, end='', file=csv_out_fh)

        # Print serial number
        print('%d,' % count, end='', file=csv_out_fh)

        # Print rule name
        print('%s,' % orig_rname, end='', file=csv_out_fh)

        # Print source zones
        src_zones = r.findall('./from/member')
        for sz in src_zones:
            print('%s ' % sz.text, end='', file=csv_out_fh)
        print(',', end='', file=csv_out_fh)

        # process source address match
        src_addresses = r.findall('./source/member')
        for sa in src_addresses:
            print('%s ' % sa.text, end='', file=csv_out_fh)
        print(',', end='', file=csv_out_fh)

        # Print destination zones
        dst_zones = r.findall('./to/member')
        for dz in dst_zones:
            print('%s ' % dz.text, end='', file=csv_out_fh)
        print(',', end='', file=csv_out_fh)

        # process destination address match
        dst_addresses = r.findall('./destination/member')
        for da in dst_addresses:
            print('%s ' % da.text, end='', file=csv_out_fh)
        print(',', end='', file=csv_out_fh)

        # process schedule match
        schedule = r.find('./schedule')
        if (schedule is not None):
            print('%s' % schedule.text.strip(), end='', file=csv_out_fh)
        print(',', end='', file=csv_out_fh)

        # process service match
        services = r.findall('./service/member')
        for svc in services:
            print('%s ' % svc.text, end='', file=csv_out_fh)
        print(',', end='', file=csv_out_fh)

        # process service group match
        service_groups = r.findall('./service-group/member')
        for sg in service_groups:
            print('%s ' % sg.text, end='', file=csv_out_fh)
        print(',', end='', file=csv_out_fh)

        # process application match
        applications = r.findall('./application/member')
        for app in applications:
            print('%s ' % app.text, end='', file=csv_out_fh)
        print(',', end='', file=csv_out_fh)

        # process url-category match
        url_categories = r.findall('./category/member')
        for uc in url_categories:
            print('%s ' % uc.text, end='', file=csv_out_fh)
        print(',', end='', file=csv_out_fh)

        # process source user match
        users = r.findall('./source-user/member')
        if (len(users) > 0):
            print('"', end='', file=csv_out_fh)
            for u in users:
                u_esc = u.text.replace('"', '')
                print('%s ' % u.text, end='', file=csv_out_fh)
            print('"', end='', file=csv_out_fh)
        print(',', end='', file=csv_out_fh)

        # process action match
        action = r.find('./action')
        if (action is not None):
            print('%s' % action.text.strip(), end='', file=csv_out_fh)
        print(',', end='', file=csv_out_fh)



        # End of current rule
        print('', file=csv_out_fh)




        ### Print translated rule

        # Print tenant
        print('%s,' % tnt, end='', file=csv_out_fh)

        # Print serial number
        print('%d.1,' % count, end='', file=csv_out_fh)

        # Print rule name
        print('%s,' % rname, end='', file=csv_out_fh)

        # Print source zones
        for zone, zone_line in xrule.get_src_zone_map().iteritems():
            print('%s ' % zone, end='', file=csv_out_fh)
        print(',', end='', file=csv_out_fh)

        # process source address match
        if (len(xrule.get_src_addr_map()) > 0):
            print('address-list: [', end='', file=csv_out_fh)
            for addr, addr_line in xrule.get_src_addr_map().iteritems():
                print(' %s' % addr, end='', file=csv_out_fh)
            print(' ] ', end='', file=csv_out_fh)
        if (len(xrule.get_src_addr_grp_map()) > 0):
            print('address-group-list: [', end='', file=csv_out_fh)
            for addr_grp, addr_grp_line in xrule.get_src_addr_grp_map().iteritems():
                print(' %s' % addr_grp, end='', file=csv_out_fh)
            print(' ] ', end='', file=csv_out_fh)
        print(',', end='', file=csv_out_fh)

        # Print destination zones
        for zone, zone_line in xrule.get_dst_zone_map().iteritems():
            print('%s ' % zone, end='', file=csv_out_fh)
        print(',', end='', file=csv_out_fh)

        # process destination address match
        if (len(xrule.get_dst_addr_map()) > 0):
            print('address-list: [', end='', file=csv_out_fh)
            for addr, addr_line in xrule.get_dst_addr_map().iteritems():
                print(' %s' % addr, end='', file=csv_out_fh)
            print(' ] ', end='', file=csv_out_fh)
        if (len(xrule.get_dst_addr_grp_map()) > 0):
            print('address-group-list: [', end='', file=csv_out_fh)
            for addr_grp, addr_grp_line in xrule.get_dst_addr_grp_map().iteritems():
                print(' %s' % addr_grp, end='', file=csv_out_fh)
            print(' ] ', end='', file=csv_out_fh)
        print(',', end='', file=csv_out_fh)

        # Print schedule
        if (xrule.get_schedule() is not None):
            print('%s' % xrule.get_schedule(), end='', file=csv_out_fh)
        print(',', end='', file=csv_out_fh)

        # Print services
        for svc in xrule.get_service_map().keys():
            print('%s ' % svc, end='', file=csv_out_fh)
        print(',,', end='', file=csv_out_fh)

        # process application match
        if (len(xrule.get_application_map().keys()) > 0):
            predef_app_list = []
            user_def_app_list = []
            user_def_app_grp_list = []
            for app in xrule.get_application_map().keys():
                if (app in cur_tnt.application_map.keys() or
                    (shared_tnt is not None and
                     app in shared_tnt.application_map.keys())):
                    user_def_app_list.append(app)
                elif (app in cur_tnt.application_group_map.keys() or
                      (shared_tnt is not None and
                       app in shared_tnt.application_group_map.keys())):
                    user_def_app_grp_list.append(app)
                elif (app in predef_app_map.keys()):
                    predef_app_list.append(app)

            if (len(predef_app_list) > 0):
                print('predefined-application-list: [', end='', file=csv_out_fh)
                for app in predef_app_list:
                    print(' %s' % app, end='', file=csv_out_fh)
                print(' ] ', end='', file=csv_out_fh)
            if (len(user_def_app_list) > 0):
                print('user-defined-application-list: [', end='', file=csv_out_fh)
                for app in user_def_app_list:
                    print(' %s' % app, end='', file=csv_out_fh)
                print(' ] ', end='', file=csv_out_fh)
            if (len(user_def_app_grp_list) > 0):
                print('user-defined-application-group-list: [', end='', file=csv_out_fh)
                for app in user_def_app_grp_list:
                    print(' %s' % app, end='', file=csv_out_fh)
                print(' ] ', end='', file=csv_out_fh)
        print(',', end='', file=csv_out_fh)


        # process application match
        if (len(xrule.get_url_category_map().keys()) > 0):
            predef_uc_list = []
            user_def_uc_list = []
            for uc in xrule.get_url_category_map().keys():
                uc_convert = uc.replace('-', '_')
                if (uc in cur_tnt.url_category_map.keys() or
                    (shared_tnt is not None and
                     uc in shared_tnt.url_category_map.keys())):
                    user_def_uc_list.append(uc)
                elif (uc_convert in predef_url_categories_map.keys()):
                    predef_uc_list.append(uc_convert)

            if (len(predef_uc_list) > 0):
                print('predefined [ ', end='', file=csv_out_fh)
                for uc in predef_uc_list:
                    print(' %s' % uc, end='', file=csv_out_fh)
                print(' ] ', end='', file=csv_out_fh)

            if (len(user_def_uc_list) > 0):
                print('user-defined [ ', end='', file=csv_out_fh)
                for uc in user_def_uc_list:
                    print(' %s' % uc, end='', file=csv_out_fh)
                print(' ]', end='', file=csv_out_fh)
        print(',', end='', file=csv_out_fh)


        # ignore user match for now
        print(',', end='', file=csv_out_fh)


        # Print action
        if (xrule.get_action() is not None):
            print('%s' % xrule.get_action_string(), end='', file=csv_out_fh)
        print(',', end='', file=csv_out_fh)



        # End of current rule
        print('', file=csv_out_fh)



app_fh.close()
out_fh.close()
csv_out_fh.close()
log_fh.close()



