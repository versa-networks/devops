#!/usr/bin/python
#  pan-convert.py - Convert Palo Alto config to Versa config
#
#  This file has the code to translate Palo Alto config to Versa config
#
#  Copyright (c) 2023, Versa Networks, Inc.
#  All rights reserved.
#  pylint: disable=invalid-name,unused-import,too-many-lines,line-too-long,attribute-defined-outside-init

import argparse
import csv
import _csv
import io
import logging
import os
import re
import sys
import versa

import lxml.etree as ET

from csv import reader

from argparse import Namespace
from typing import Any, Dict, List, Optional, TextIO, Tuple, Union

from versa.Address import Address, AddressType
from versa.AddressGroup import AddressGroup
from versa.Application import Application
from versa.ApplicationFilter import ApplicationFilter
from versa.ApplicationGroup import ApplicationGroup
from versa.Firewall import Firewall
from versa.FirewallRule import FirewallRuleAction
from versa.NextGenFirewall import NextGenFirewall
from versa.NextGenFirewallRule import NextGenFirewallRule
from versa.Schedule import Schedule
from versa.Service import Service
from versa.ServiceGroup import ServiceGroup
from versa.URLCategory import URLCategory
from versa.VersaConfig import VersaConfig
from datetime import datetime


# Constants
CMN_TEMPLATE_NAME = "Provider-DataStore"
"""str: Common template name."""

CMN_TENANT_NAME = "Provider"
"""str: Common tenant name."""

LOG_FILENAME = "versa-cfg-translate.log"
"""str: Log file name."""

STRICT_CHECKS = False
"""bool: Enable strict checks."""

INPUT_LINE_NUM = 0
"""int: Input line number."""

def parse_args(args_list: list) -> Namespace:
    """Parse command-line arguments.

    Args:
        args_list (list): List of command-line arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Convert Palo Alto config to Versa config",
    )
    parser.add_argument(
        "-pc",
        "--pan_config_file",
        dest="pan_config_file",
        action="store",
        help="Path to Palo Alto config file in XML format",
        required=True,
    )
    parser.add_argument(
        "-z",
        "--zone_file",
        dest="zone_file",
        action="store",
        help="Path to zone/interface CSV file",
        default="Source_Files/interface-list.csv",
    )
    parser.add_argument(
        "-a",
        "--app_file",
        dest="app_file",
        action="store",
        help="Path to Versa predefined applications CSV file",
        default="Predefined/applications.csv",
    )
    parser.add_argument(
        "-s",
        "--subfamilies_file",
        dest="subfamilies_file",
        action="store",
        help="Path to Versa application subfamilies CSV file",
        default="Predefined/app_subfamiles.csv",
    )
    parser.add_argument(
        "-u",
        "--url_file",
        dest="url_file",
        action="store",
        help="Path to Versa predefined URL categories XML file",
        default="Predefined/categories.xml",
    )
    parser.add_argument(
        "-c",
        "--countries_file",
        dest="countries_file",
        action="store",
        help="Path to Versa predefined countries XML file",
        default="Predefined/countries.csv",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-T",
        "--template_file_name",
        dest="template_file_name",
        action="store",
        help="Template name",
    )
    group.add_argument(
        "-D",
        "--device_name",
        dest="device_name",
        action="store",
        help="Device name",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        dest="output_dir",
        action="store",
        help="Path to output directory",
        default="Output_Files/",
    )
    parser.add_argument(
        "-v",
        "--versa_paths_file",
        dest="versa_paths_file",
        action="store",
        help="Path to Versa path segments file",
    )
    parser.add_argument(
        "-org",
        "--org_name",
        dest="org_name",
        action="store",
        help="Organization name",
    )
    group.add_argument(
        "-n",
        "--template_name",
        dest="template_name",
        action="store",
        help="Versa Template name",
    )
    parser.add_argument(
        "-cil",
        "--create_interface_list",
        dest="create_interface_list",
        action="store_true",
        help="Create Interface List File",
    )
    args = parser.parse_args(args_list)

    return args


def the_logger(args: Namespace) -> logging.Logger:
    """Create a logger object.

    Args:
        args (argparse.Namespace): Command-line arguments.

    Returns:
        logging.Logger: Logger object, or None if there was an error.
    """
    log_path = os.path.join(args.output_dir, LOG_FILENAME)
    try:
        formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
        fh = logging.FileHandler(log_path)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger = logging.getLogger(log_path)
        logger.addHandler(fh)
        logger.setLevel(logging.DEBUG)
    except OSError as e:
        print(f"Error: Unable to create logger with {log_path}")
        print(f"Error Details: {e}")
        sys.exit(1)
    return logger


def create_output_dir(args: Namespace) -> bool:
    """
    Create the output directory if it doesn't exist.

    Args:
        args (Namespace): Command-line arguments.

    Returns:
        bool: True if the output directory exists or was created, False otherwise.
    """
    if not args.output_dir:
        print("Error: Please specify the output directory path")
        return False

    try:
        if os.path.isdir(args.output_dir):
            return True
        os.mkdir(args.output_dir)
        return True
    except OSError as e:
        print(f"Error creating output directory: {args.output_dir}")
        print(f"Error Details: {e}")
        print("Please enter a valid directory path where the output files will be written")
        return False


def get_template_name(template_file_name: str) -> Optional[str]:
    """Extract template name from a file.

    Args:
        template_file_name (str): The name of the template file.

    Raises:
        FileNotFoundError: If the template file is not found.
        ValueError: If unable to parse the template file.

    Returns:
        Optional[str]: The name of the template, or None if not found.
    """
    try:
        with open(template_file_name, "r", encoding="utf-8") as file:
            content = file.read()
            match = re.search(r'template\s+(\w+)\s+\{', content)
            if match:
                return match.group(1)
            else:
                raise ValueError(f"Unable to find template name in file {template_file_name}")
    except FileNotFoundError:
        raise FileNotFoundError(f"File {template_file_name} not found.")

def open_3rd_party_config_file(args: Namespace):
    """Open and parse an XML file.

    Args:
        args (argparse.Namespace): Command-line arguments.

    Returns:
        Optional[Element]: XML root element, or None if there was an error.
    """
    try:
        with open(args.pan_config_file, "r", encoding="utf-8") as xml_file:
            xml_tree = ET.parse(xml_file)
            xml_root = xml_tree.getroot()
            return xml_root
    except FileNotFoundError:
        print(f"Error: input file {args.pan_config_file} not found")
    except Exception as e:
        print(f"Error: unable to parse XML input file {args.pan_config_file}")
        print(f"Error Details: {e}")
    return None


def create_zone_interface_file(args: argparse.Namespace, xml_root):
    """Create a CSV file containing zone and interface information.

    Args:
        args (argparse.Namespace): Command-line arguments.
        xml_root (lxml.etree.Element): Root element of the XML tree.
    """
    if not args.zone_file:
        return

    try:
        with open(args.zone_file, "w", encoding="utf-8") as zone_fh:
            
            print("#3rd_Party_Interface,3rd_Party_Zone_Name,Versa_Zone_Name,Versa_Interface_Name,Versa_Paired_Interface_Name,Versa_VRF_Name,3rd_Party_Vsys_Name,Versa_Tenant_Name", file=zone_fh)

            zone_list: List[Dict[str, Union[str, int]]] = []
            count = 0

            for element in xml_root.xpath(".//*[devices]/descendant::zone", namespaces=xml_root.nsmap):
                for subelements in element:
                    zone_name = subelements.get("name").upper()
                    for k in subelements.iter("member"):
                        pan_interface = k.text

                        if any(row["3rd_Party_Zone_Name"] == zone_name for row in zone_list):
                            continue

                        match = re.search(r"\.\d{1,10}", pan_interface)
                        matched_text = match.group(0) if match else ""
                        
                        versa_paired_interface_name = ""
                        
                        if "ae" in pan_interface:
                            versa_interface_name = f"{pan_interface}.0"
                        elif "tunnel" in pan_interface:
                            versa_interface_name = f"tvi-0/{matched_text}"
                        elif "." in pan_interface:
                            versa_interface_name = f"vni-0/{count}{matched_text}"
                        else:
                            versa_interface_name = f"vni-0/{count}.0"
                            
                        row = {
                            "3rd_Party_Interface": pan_interface,
                            "3rd_Party_Zone_Name": zone_name,
                            "Versa_Zone_Name": f"{args.org_name}-{zone_name}",
                            "Versa_Interface_Name": versa_interface_name,
                            "Versa_Paired_Interface_Name": "",
                            "Versa_VRF_Name": f"{args.org_name}-LAN-VR",
                            "3rd_Party_Vsys_Name": "vsys1",
                            "Versa_Tenant_Name": args.org_name,
                        }

                        zone_list.append(row)
                        
                        print(f"{pan_interface},{zone_name},{args.org_name}-{zone_name},{versa_interface_name},{versa_paired_interface_name},{args.org_name}-LAN-VR,vsys1,{args.org_name}", file=zone_fh,)
                        count += 1
    except Exception as e:
        print(f"Error: unable to open zone/interface csv file {args.zone_file} for writing")
        print(f"Error Details: {e}")
        sys.exit(1)


def open_predefined_applications(args: Namespace):
    """Open and parse a predefined applications CSV file.

    Args:
        args (argparse.Namespace): Command-line arguments.

    Returns:
        Tuple[_csv._reader, TextIO]: CSV reader object and file object.
    """
    if not args.app_file:
        print("Please specify the predefined applications CSV file")
        sys.exit(1)
    
    print("   Applications")
    try:
        app_fh = open(args.app_file, "r", encoding="utf-8")
        app_csv = csv.reader(app_fh)
        return app_csv, app_fh
    except OSError as e:
        print(f"Error: unable to open predefined applications CSV file {args.app_file} for reading")
        print(f"Error Details: {e}")
        sys.exit(1)
    except csv.Error as e:
        print(f"Error: unable to parse predefined applications CSV file {args.app_file}")
        print(f"Error Details: {e}")
        sys.exit(1)


def open_predefined_URL_categories_XML(args: Namespace):
    """Open and parse a predefined URL categories XML file.

    Args:
        args (argparse.Namespace): Command-line arguments.

    Returns:
        Element: XML root element.
    """
    if not args.url_file:
        print("Please specify the predefined URL categories file")
        return None

    print("   URL categories")
    try:
        url_tree = ET.parse(args.url_file)
        url_root = url_tree.getroot()
        return url_root
    except ET.ParseError as e:
        print(f"Error: unable to parse URL categories XML file {args.url_file}")
        print(f"Error Details: {e}")
        return None
    except OSError as e:
        print(f"Error: unable to open URL categories XML file {args.url_file} for reading")
        print(f"Error Details: {e}")
        return None


def open_predefined_countries_file(args: Namespace):
    """Open and parse a predefined countries CSV file.

    Args:
        args (argparse.Namespace): Command-line arguments.

    Returns:
        Tuple[Optional[csv.reader], Optional[io.TextIOWrapper]]: CSV reader object and file object, or None if there was an error.
    """
    if not args.countries_file:
        print("Please specify the predefined countries file")
        return None
    
    print("   Countries")
    try:
        countries_fh = open(args.countries_file, "r", encoding="utf-8")
        countries_csv = csv.reader(countries_fh)
        return countries_csv, countries_fh
    except FileNotFoundError:
        print(f"Error: countries CSV file {args.countries_file} not found")
    except Exception as e:
        print(f"Error: unable to open countries CSV file {args.countries_file} for reading")
        print(f"Error Details: {e}")
    return None, None


def open_predefined_subfamilies_file(args: Namespace):
    """Open and parse a predefined subfamilies CSV file.

    Args:
        args (argparse.Namespace): Command-line arguments.

    Returns:
        Tuple[Optional[csv.reader], Optional[io.TextIOWrapper]]: CSV reader object and file object, or None if there was an error.
    """
    if not args.subfamilies_file:
        print("Please specify the predefined sub families categories file")
        return None
    
    print("   Subfamilies")
    try:
        subfamilies_fh = open(args.subfamilies_file, "r", encoding="utf-8")
        subfamilies_csv = csv.reader(subfamilies_fh)
        return subfamilies_csv, subfamilies_fh
    except FileNotFoundError:
        print(f"Error: subfamilies CSV file {args.subfamilies_file} not found")
    except Exception as e:
        print(f"Error: unable to open subfamilies CSV file {args.subfamilies_file} for reading")
        print(f"Error Details: {e}")
    return None, None


def open_zone_interface_file(args: Namespace):
    """Open and parse a zone/interface CSV file.

    Args:
        args (argparse.Namespace): Command-line arguments.

    Returns:
        Tuple[Optional[csv.reader], Optional[io.TextIOWrapper]]: CSV reader object and file object, or None if there was an error.
    """
    if not args.zone_file:
        print("Error: Please specify the interface/zone CSV file")
        return None, None

    try:
        zone_fh = open(args.zone_file, "r", encoding="utf-8")
        zone_csv = csv.reader(zone_fh)
        return zone_csv, zone_fh
    except Exception as e:
        print(f"Error: unable to open zone/interface CSV file {args.zone_file} for reading")
        print(f"Error Details: {e}")
        return None, None


def open_output_files(args: Namespace) -> Tuple[str, TextIO]:
    """
    Open output files for writing.

    Args:
        args (Namespace): Command-line arguments.

    Returns:
        Tuple[str, TextIO]: Tuple containing the output file names and file objects.
    """
    pan_config_file_name = os.path.splitext(os.path.basename(args.pan_config_file))[0]
    outfile = os.path.join(args.output_dir, f"{pan_config_file_name}.cfg")
    #csv_outfile = os.path.join(args.output_dir, f"{pan_config_file_name}.csv")
    #logfile = os.path.join(args.output_dir, f"{pan_config_file_name}.json")

    try:
        out_fh = open(outfile, "w", encoding="utf-8")
        #csv_out_fh = open(csv_outfile, "w", encoding="utf-8")
        #log_fh = open(logfile, "w", encoding="utf-8")
    except OSError as e:
        print(f"Error: unable to open output files for writing")
        print(f"Error Details: {e}")
        sys.exit(1)

    return pan_config_file_name, out_fh


def populate_zone_interface_map(zone_csv, zone_fh: Any, versa_cfg: Any, tnt_xlate_map: Dict[str, List[str]]):
    """
    Populate the interface zone map from a CSV file.

    Args:
        zone_csv (csv.reader): Contents of the zone file.
        zone_fh (Any): File handle for the zone file.
        versa_cfg (Any): Storage object for Versa Config.
        tnt_xlate_map (Dict[str, List[str]]): A dictionary containing tenant translation information.

    Returns:
        Tuple[Any, Dict[str, List[str]], Dict[str, List[str]]]: A tuple containing the updated versa_cfg object, tnt_xlate_map dictionary, and the versa_intf_zone_map dictionary.
    """
    pan_intf_zone_map: Dict[str, List[str]] = {}
    versa_intf_zone_map: Dict[str, List[str]] = {}
    cur_line_num: int = 0

    for row in zone_csv:
        cur_line_num += 1

        if row[0].startswith("#") or len(row) < 4:
            continue

        pan_intf_zone_map[row[0]] = row
        versa_intf_zone_map[row[3]] = row + [str(cur_line_num)]

        src_tnt, tnt = row[6], row[7]
        if not versa_cfg.has_tenant(tnt):
            versa_cfg.add_tenant(tnt, "0")
            tnt_xlate_map[src_tnt] = [tnt]

    zone_fh.close()
    return versa_cfg, tnt_xlate_map, versa_intf_zone_map


def populate_interfaces_networks_zones_map(versa_intf_zone_map: Dict[str, List[str]], v_logger: logging.Logger, versa_cfg: Any, args: Any) -> None:
    """
    Add interfaces, networks, and zones to the Versa configuration.

    Args:
        versa_intf_zone_map (Dict[str, List[str]]): A dictionary containing interface, network, and zone information.
        v_logger (logging.Logger): A logging module variable.
        versa_cfg (Any): A storage object for Versa Config.
        args (Any): Command line arguments.
    """
    for v_ifname, ifinfo in versa_intf_zone_map.items():
        if "#" in v_ifname:
            continue 
        tnt = ifinfo[7]
        cur_tnt = versa_cfg.get_tenant(tnt, "0")
        v_logger.info(f"{args.zone_file}:{ifinfo[8]}: adding versa interface {v_ifname} to tenant {tnt}; network {ifinfo[2]}; zone {ifinfo[1]}; pan interface {ifinfo[0]}")
        versa_cfg.add_network_and_interface(ifinfo[2], v_ifname)

        if ifinfo[2]:
            cur_tnt.add_zone_network(ifinfo[1], ifinfo[2], ifinfo[8])
        else:
            cur_tnt.add_zone_interface(ifinfo[1], v_ifname, ifinfo[8])
    
    return versa_cfg


def populate_predefined_applications_map(app_csv, app_fh: Any, versa_cfg: Any):
    """
    Populate predefined applications from a CSV file into a dictionary.

    Args:
        app_csv (csv.reader): Contents of the applications file.
        app_fh (Any): File handle for the applications file.
        versa_cfg (Any): Storage object for Versa Config.

    Returns:
        Tuple[Dict[str, List[str]], Dict[str, Application], Any]: A tuple containing the predef_apps dictionary, predef_app_map dictionary, and the updated versa_cfg object.
    """
    predef_apps: Dict[str, List[str]] = {}
    predef_app_map: Dict[str, Application] = {}

    for row in app_csv:
        if len(row) > 0 and len(row[0]) > 0:
            try:
                int(row[0])
            except ValueError:
                continue

            appname = row[3]
            predef_apps[appname] = row
            cur_app = Application(appname, INPUT_LINE_NUM, True)
            predef_app_map[appname] = cur_app

    app_fh.close()
    versa_cfg.set_predef_app_map(predef_app_map)
    return predef_apps, predef_app_map, versa_cfg


def populate_predefined_url_categories_map(url_root, predef_apps: Any, versa_cfg) -> Tuple[Any, Dict[str, URLCategory]]:
    """
    Populate predefined URL categories from an XML file into a dictionary.

    Args:
        url_root (Element): Root element of the URL categories XML file.
        url_fh (Any): File handle for the URL categories file.
        versa_cfg (Any): Storage object for Versa Config.

    Returns:
        Tuple[Any, Dict[str, URLCategory]]: A tuple containing the updated versa_cfg object and the predef_url_categories_map dictionary.
    """

    predef_url_categories_map = {}
    for c in url_root.findall("./categories/entity/subtype"):
        url_cat_name = c.text
        predef_apps[url_cat_name] = c
        predef_url_categories_map[url_cat_name] = URLCategory(url_cat_name, INPUT_LINE_NUM, True)
    versa_cfg.set_predef_url_cat_map(predef_url_categories_map)
    return versa_cfg, predef_url_categories_map


def populate_predefined_countries_map(countries_csv, countries_fh: Any, versa_cfg: Any) -> Tuple[Any, Dict[str, list]]:
    """
    Populate predefined countries from a CSV file into a dictionary.

    Args:
        countries_csv (csv.reader): Contents of the countries file.
        countries_fh (Any): File handle for the countries file.
        versa_cfg (Any): Storage object for Versa Config.

    Returns:
        Tuple[Any, Dict[str, list]]: A tuple containing the updated versa_cfg object and the predef_countries dictionary.
    """
    predef_countries_map: Dict[str, list] = {}
    for row in countries_csv:
        if len(row) >= 5:
            code = row[-4].strip()
            predef_countries_map[code] = row
    countries_fh.close()
    versa_cfg.set_predef_countries_map(predef_countries_map)
    return versa_cfg, predef_countries_map


def load_application_objects_into_tenant(tnt_xml, tnt: Any, v_logger: logging.Logger) -> None:
    """Load application objects into a tenant.

    Args:
        _tnt_xml (Element): The XML element containing the application objects.
        _tnt (Any): The tenant object to add the application objects to.
        _v_logger (logging.Logger): The logger object for logging messages.
    """
    # Process application objects
    print("Loading application objects into tenant...")
    applications = tnt_xml.findall("./application/entry")
    for app in applications:
        application_name = (app.attrib["name"].replace(" ", "_")).upper()
        if application_name in tnt.application_map:
            continue 
        cur_app = Application(application_name, INPUT_LINE_NUM, False)
        desc = app.find("./description")
        if desc is not None and desc.text is not None:
            desc.text = clean_string(desc.text)
            cur_app.set_description(desc.text, INPUT_LINE_NUM)
        v_logger.info(f"Tenant {tnt.name}: Adding Application {cur_app.name} to current tenant")
        tnt.add_application(cur_app, INPUT_LINE_NUM)


def load_application_groups_into_tenant(tnt_xml, tnt: Any, v_logger: logging.Logger, predef_app_map: Dict[str, Any]) -> None:
    """Load application groups into a tenant.

    Args:
        _tnt_xml (Element): The XML element containing the application groups.
        _tnt (Any): The tenant object to add the application groups to.
        _v_logger (logging.Logger): The logger object for logging messages.
        _predef_app_map (Dict[str, Any]): A dictionary mapping predefined application names to their objects.
    """
    # Process application groups
    print("Loading application groups into tenant...")
    app_groups = tnt_xml.findall("./application-group/entry")
    for ag in app_groups:
        agname = ag.attrib["name"].replace(" ", "_")
        if agname in tnt.address_group_map:
            continue
        cur_app_grp = tnt.get_application_group(agname)
        if cur_app_grp is None:
            cur_app_grp = ApplicationGroup(agname, INPUT_LINE_NUM, False)
            tnt.add_application_group(cur_app_grp, INPUT_LINE_NUM)

        ag_members = ag.findall("./members/member")
        for m in ag_members:
            # check if the application is user defined application
            application_name = m.text.replace(" ", "_").upper()
            member_added = False
            
            app = tnt.get_application(application_name)

            sh_tnt = tnt.get_shared_tenant()
            if app is not None:
                v_logger.info(
                    f"Tenant {tnt.name}: Adding application group '{agname}'"
                    + f" with custom application member '{application_name}'"
                )
                cur_app_grp.add_application(app, INPUT_LINE_NUM)
                member_added = True

            if not member_added:
                app_grp = tnt.get_application_group(application_name)
                if app_grp is not None:
                    v_logger.info(
                        f"Tenant {tnt.name}: Adding application group '{agname}'"
                        + f" with custom application group member '{application_name}'"
                    )
                    cur_app_grp.add_application_group(app_grp, INPUT_LINE_NUM)
                    member_added = True

            if not member_added and sh_tnt is not None:
                app = sh_tnt.get_application(application_name)
                if app is not None:
                    v_logger.info(
                        f"Tenant {tnt.name}: Adding application group '{agname}'"
                        + f" with shared application member '{application_name}'"
                    )
                    cur_app_grp.add_application(app, INPUT_LINE_NUM)
                    member_added = True
                else:
                    app_grp = sh_tnt.get_application_group(application_name)
                    if app_grp is not None:
                        v_logger.info(
                            f"Tenant {tnt.name}: Adding application group '{agname}'"
                            + f" with shared application group member '{application_name}'"
                        )
                        cur_app_grp.add_application_group(app_grp, INPUT_LINE_NUM)
                        member_added = True

            if not member_added:
                # check if the application is predefined application
                if application_name in predef_app_map:
                    app = predef_app_map[application_name]
                    v_logger.info(
                        f"Tenant {tnt.name}: Adding application group '{agname}'"
                        + f" with predefined application member '{application_name}'"
                    )
                    cur_app_grp.add_application(app, INPUT_LINE_NUM)
                    member_added = True

            if not member_added:
                v_logger.error(
                    f"Tenant {tnt.name}: Adding application group '{agname}'"
                    + f" with unknown application member '{application_name}'"
                )


def load_application_filters_into_tenant(tnt_xml, tnt: Any, v_logger: logging.Logger, predef_subfamilies: Dict[str, Any]) -> None:
    """Load application filters from an XML element into a tenant.

    Args:
        tnt_xml (Element): An XML element containing application filter information.
        tnt (Any): A tenant object.
        v_logger (logging.Logger): A logger object for logging messages.
        predef_subfamilies (Dict[str, Any]): A dictionary of predefined subfamilies.
    """
    print("Loading application filters into tenant...")
    app_filters = tnt_xml.findall("./application-filter/entry")
    for app_filter in app_filters:
        afname = app_filter.attrib["name"].replace(" ", "_")
        if afname in tnt.application_filter_map:
            continue
        cur_app_filter = tnt.get_application_filter(afname)
        if cur_app_filter is None:
            cur_app_filter = ApplicationFilter(afname, INPUT_LINE_NUM, False)
            tnt.add_application_filter(cur_app_filter, INPUT_LINE_NUM)

        cat = app_filter.findall("./category/member")
        for c in cat:
            cur_app_filter.add_application_filter("family", c.text.strip(), INPUT_LINE_NUM)

        subcat = app_filter.findall("./subcategory/member")
        for c in subcat:
            sc = c.text.strip()
            if sc in list(predef_subfamilies.keys()):
                cur_app_filter.add_application_filter("subfamily", c.text.strip(), INPUT_LINE_NUM)
            else:
                v_logger.error(
                    f"Tenant {tnt.name}; application filter {cur_app_filter.name}; subfamily {sc} not found"
                )

        risk = app_filter.findall("./risk/member")
        for c in risk:
            cur_app_filter.add_application_filter("risk", c.text.strip(), INPUT_LINE_NUM)

        productivity = app_filter.findall("./productivity/member")
        for c in productivity:
            cur_app_filter.add_application_filter("productivity", c.text.strip(), INPUT_LINE_NUM)

        tag = app_filter.findall("./tag/member")
        for c in tag:
            cur_app_filter.add_application_filter("tag", c.text.strip(), INPUT_LINE_NUM)


def load_address_objects_into_tenant(tnt_xml, tnt: Any, v_logger: logging.Logger) -> None:
    """Load address objects from an XML element into a tenant.

    Args:
        tnt_xml (Element): An XML element containing address information.
        tnt (Any): A tenant object.
        v_logger (logging.Logger): A logger object for logging messages.
    """
    # Process address objects
    print("Loading address_objects into tenant...")
    addresses = tnt_xml.findall("./address/entry")
    for addr in addresses:
        address_name = addr.attrib["name"].replace(" ", "_")
        if address_name in tnt.address_map:
            continue
        cur_addr = Address(address_name, INPUT_LINE_NUM, False)
        ip_netmask = addr.find("./ip-netmask")
        desc = addr.find("./description")
        ip_ra = addr.find("./ip-range")
        if desc is not None and desc.text is not None:
            desc.text = clean_string(desc.text)
            cur_addr.set_description(desc.text, INPUT_LINE_NUM)
        add_flag = False
        if ip_netmask is not None:
            cur_addr.set_addr_value(ip_netmask.text.replace(" ", "_"), INPUT_LINE_NUM)
            cur_addr.set_addr_type(AddressType.IP_V4_PREFIX, INPUT_LINE_NUM)
            add_flag = True
        if ip_ra is not None:
            cur_addr.set_addr_value(ip_ra.text.replace(" ", "_"), INPUT_LINE_NUM)
            cur_addr.set_addr_type(AddressType.IP_V4_RANGE, INPUT_LINE_NUM)
            add_flag = True
        if not add_flag:
            fqdn = addr.find("./fqdn")
            if fqdn is not None:
                cur_addr.set_addr_value(fqdn.text, INPUT_LINE_NUM)
                cur_addr.set_addr_type(AddressType.FQDN, INPUT_LINE_NUM)
                add_flag = True
        if not add_flag:
            v_logger.error(f"Tenant {tnt.name}: Address {cur_addr.name} unsupported")
            continue

        v_logger.info(f"Tenant {tnt.name}: Adding Address {cur_addr.name} to current tenant")
        tnt.add_address(cur_addr, INPUT_LINE_NUM)


def load_address_group_objects_into_tenant(tnt_xml, tnt: Any, v_logger: logging.Logger) -> None:
    """Load address group objects from an XML element into a tenant.

    Args:
        tnt_xml (Element): An XML element containing address group information.
        tnt (Any): A tenant object.
        v_logger (logging.Logger): A logger object for logging messages.
    """
    print("Loading address groups into tenant...")
    addr_groups = tnt_xml.findall("./address-group/entry")
    for addr_group in addr_groups:
        agname = addr_group.attrib["name"].replace(" ", "_")
        if agname in tnt.address_group_map:
            continue
        cur_addr_grp = tnt.get_address_group(agname)
        if cur_addr_grp is None:
            cur_addr_grp = AddressGroup(agname, INPUT_LINE_NUM, False)
            tnt.add_address_group(cur_addr_grp, INPUT_LINE_NUM)
        desc = addr_group.find("./description")
        if desc is not None and desc.text is not None:
            desc.text = clean_string(desc.text)
            cur_addr_grp.set_description(desc.text, INPUT_LINE_NUM)

        ag_members = addr_group.findall("./members/member")
        for m in ag_members:
            addr = m.text.replace(" ", "_")
            v_logger.info(f"tenant {tnt.name}: adding address group '{agname}' with address member '{addr}'")
            cur_addr_grp.add_address(addr, INPUT_LINE_NUM)

        ag_members = addr_group.findall("./static/member")
        for m in ag_members:
            addr = m.text.replace(" ", "_")
            v_logger.info(f"tenant {tnt.name}: adding address group '{agname}' with address member '{addr}'")
            cur_addr_grp.add_address(addr, INPUT_LINE_NUM)


def load_external_address_group_objects_into_tenant(tnt_xml, tnt: Any, v_logger: logging.Logger) -> None:
    """Load external address group objects from an XML element into a tenant.

    Args:
        tnt_xml (Element): An XML element containing external address group information.
        tnt (Any): A tenant object.
        v_logger (logging.Logger): A logger object for logging messages.
    """
    print("Loading external address group objects into tenant...")
    addr_groups = tnt_xml.findall("./external-list/entry")
    for ag in addr_groups:
        entry = ag.find("type/ip")
        if entry is not None:
            ag_name = ag.attrib["name"].replace(" ", "_")
            cur_addr_grp = tnt.get_address_group(ag_name) or tnt.add_address_group(AddressGroup(ag_name, INPUT_LINE_NUM, False), INPUT_LINE_NUM)

            desc = ag.find("./description")
            if desc is not None and desc.text is not None:
                desc.text = clean_string(desc.text)
                cur_addr_grp.set_description(desc.text, INPUT_LINE_NUM)

            url = entry.find("./url").text
            file_name = url.split("/")[-1]
            v_logger.info(f"Tenant {tnt.name}: Adding address group '{cur_addr_grp.name}' with file name '{file_name}'")
            cur_addr_grp.add_filename(file_name, INPUT_LINE_NUM)


def load_url_category_objects_into_tenant(tnt_xml, tnt: Any, v_logger: logging.Logger) -> None:
    """Load URL category objects from an XML element into a tenant.

    Args:
        tnt_xml (Element): An XML element containing URL category information.
        tnt (Any): A tenant object.
        v_logger (logging.Logger): A logger object for logging messages.
    """
    print("Loading URL categories into tenant...")
    url_categories = tnt_xml.findall("./profiles/custom-url-category/entry")
    for uc in url_categories:
        uc_name = uc.attrib["name"].replace(" ", "_")
        if uc_name in tnt.url_categories_map:
            continue
        cur_uc = URLCategory(uc_name, INPUT_LINE_NUM, False)

        desc = uc.find("./description")
        if desc is not None and desc.text is not None:
            desc.text = clean_string(desc.text)
            cur_uc.set_description(desc.text, INPUT_LINE_NUM)

        urls = uc.findall("./list/member")
        for url in urls:
            url_str = url.text.strip()
            if "*" in url_str:
                cur_uc.add_pattern(url_str.replace("*", ".*"))
            else:
                cur_uc.add_host(url_str)

        v_logger.info(f"Tenant {tnt.name}: Adding URL category '{cur_uc.name}' to current tenant")
        tnt.add_url_category(cur_uc, INPUT_LINE_NUM)


def load_external_url_category_objects_into_tenant(tnt_xml, tnt: Any, v_logger: logging.Logger) -> None:
    """Load external URL category objects from an XML element into a tenant.

    Args:
        tnt_xml (Element): An XML element containing external URL category information.
        tnt (Any): A tenant object.
        v_logger (logging.Logger): A logger object for logging messages.
    """
    print("Loading external url category objects into tenant...")
    url_categories = tnt_xml.findall("./external-list/entry")
    for url_cat in url_categories:
        entry = url_cat.find("type/url")
        if entry is not None:
            url_cat_name = url_cat.attrib["name"].replace(" ", "_")
            cur_url_cat = tnt.get_url_category(url_cat_name) or tnt.add_url_category(URLCategory(url_cat_name, INPUT_LINE_NUM, False), INPUT_LINE_NUM)

            desc = entry.find("./description")
            if desc is not None and desc.text is not None:
                desc.text = clean_string(desc.text)
                cur_url_cat.set_description(desc.text, INPUT_LINE_NUM)

            url = entry.find("./url").text
            ix = url.rfind("/")
            fn = url[ix + 1 :]
            v_logger.info(f"Tenant {tnt.name}: Adding URL category '{cur_url_cat.name}' with file name '{fn}'")
            cur_url_cat.set_filename(fn, INPUT_LINE_NUM)


def load_service_objects_into_tenant(tnt_xml, tnt: Any, v_logger: logging.Logger) -> None:
    """Load service objects from an XML element into a tenant.

    Args:
        tnt_xml (Element): An XML element containing service information.
        tnt (Any): A tenant object.
        v_logger (logging.Logger): A logger object for logging messages.
    """
    print("Loading service objects into tenant...")
    services = tnt_xml.findall("./service/entry")
    for svc in services:
        service_name = svc.attrib["name"].replace(" ", "_")
        if service_name in tnt.service_map:
            continue
        cur_svc = Service(service_name, INPUT_LINE_NUM, False)

        desc = svc.find("./description")
        if desc is not None and desc.text is not None:
            desc.text = clean_string(desc.text)
            cur_svc.set_description(desc.text, INPUT_LINE_NUM)

        proto = svc.find("./protocol/*")
        if proto is not None:
            port = proto.find("port").text
            cur_svc.set_proto(proto.tag, INPUT_LINE_NUM)
            cur_svc.set_port(port, INPUT_LINE_NUM)

        v_logger.info(f"Tenant {tnt.name}: Adding Service {service_name}")
        tnt.add_service(cur_svc, INPUT_LINE_NUM)


def load_service_group_objects_into_tenant(tnt_xml, tnt: Any, v_logger: logging.Logger) -> None:
    """Load service group objects from an XML element into a tenant.

    Args:
        tnt_xml (Element): An XML element containing service group information.
        tnt (Any): A tenant object.
        v_logger (logging.Logger): A logger object for logging messages.
    """
    print("Loading service group objects into tenant...")
    svc_groups = tnt_xml.findall("./service-group/entry")
    for svc_group in svc_groups:
        sgname = svc_group.attrib["name"].replace(" ", "_")

        cur_svc_grp = tnt.get_service_group(sgname)
        if cur_svc_grp is None:
            cur_svc_grp = ServiceGroup(sgname, INPUT_LINE_NUM, False)
            tnt.add_service_group(cur_svc_grp, INPUT_LINE_NUM)

        sg_members = svc_group.findall("./members/member")
        for member in sg_members:
            svc = member.text
            v_logger.info(f"tenant {tnt}: adding service group '{sgname}' with service member '{svc}'")
            cur_svc_grp.add_service(svc, INPUT_LINE_NUM)


def load_schedule_objects_into_tenant(tnt_xml, tnt: Any, v_logger: logging.Logger) -> None:
    """Load schedule objects from an XML element into a tenant.

    Args:
        tnt_xml (Element): An XML element containing schedule information.
        tnt (Any): A tenant object.
        v_logger (logging.Logger): A logger object for logging messages.
    """
    print("Loading schedule objects into tenant...")
    for s in tnt_xml.findall("./schedule/entry"):
        schedule_name = s.attrib["name"].replace(" ", "_")
        cur_sched = Schedule(schedule_name, INPUT_LINE_NUM, False, False)

        nr = s.findall("./schedule-type/non-recurring/member")
        for dt in nr:
            end_date_str = dt.text.split("-")[1].split("@")[0].strip()
            end_date = datetime.strptime(end_date_str, "%Y/%m/%d").date()
            if end_date >= datetime.now().date():
                cur_sched.add_non_recurring_day_time(dt.text.strip(), INPUT_LINE_NUM)

        daily = s.findall("./schedule-type/recurring/daily/member")
        for d in daily:
            cur_sched.add_recurring_day_time("daily", d.text.strip(), INPUT_LINE_NUM)

        weekly = s.findall("./schedule-type/recurring/weekly/*")
        for w in weekly:
            for t in w.findall("./member"):
                cur_sched.add_recurring_day_time(w.tag, t.text.strip(), INPUT_LINE_NUM)

        if len(cur_sched.non_recur_days_times) > 0  or cur_sched.schedule_type.name != "NON_RECURRING":
            v_logger.info(f"Tenant {tnt.name}: Adding Schedule {schedule_name}")
            tnt.add_schedule(cur_sched, INPUT_LINE_NUM)


def process_rule_address_match(vr, cur_tnt: versa.Tenant.Tenant, amap: Dict[str, Any], is_src_match: bool, v_logger: logging.Logger, predef_countries: Dict[str, Any]) -> None:
    """
    Process the address match for a NextGenFirewallRule.

    Args:
        vr (versa.NextGenFirewallRule): The NextGenFirewallRule object.
        cur_tnt (versa.Tenant.Tenant): The current tenant object.
        amap (dict): A dictionary containing address information.
        is_src_match (bool): A boolean indicating whether the match is for the source address.
        v_logger (logging.Logger): A logging module variable.
        predef_countries (dict): A dictionary containing predefined country information.
    """
    sh_tnt = cur_tnt.get_shared_tenant()
    for addr in amap:
        add_flag = False
        ao = cur_tnt.get_address(addr)
        if ao is not None:
            v_logger.info(f"tenant {cur_tnt.name}: adding ngfw rule '{vr.name}' with src/dst address '{addr}'")
            if is_src_match:
                vr.add_src_addr(addr, INPUT_LINE_NUM)
            else:
                vr.add_dst_addr(addr, INPUT_LINE_NUM)
            add_flag = True

        if not add_flag:
            ago = cur_tnt.get_address_group(addr)
            if ago is not None:
                v_logger.info(f"tenant {cur_tnt.name}: adding ngfw rule '{vr.name}' with src/dst address group '{addr}'")
                if is_src_match:
                    vr.add_src_addr_grp(addr, INPUT_LINE_NUM)
                else:
                    vr.add_dst_addr_grp(addr, INPUT_LINE_NUM)
                add_flag = True

        if not add_flag:
            ao = sh_tnt.get_address(addr)
            if ao is not None:
                v_logger.info(f"tenant {cur_tnt.name}: adding ngfw rule '{vr.name}' with src/dst address (shared) '{addr}'")
                if is_src_match:
                    vr.add_src_addr(addr, INPUT_LINE_NUM)
                else:
                    vr.add_dst_addr(addr, INPUT_LINE_NUM)
                add_flag = True

        if not add_flag:
            ago = sh_tnt.get_address_group(addr)
            if ago is not None:
                v_logger.info(f"tenant {cur_tnt.name}: adding ngfw rule '{vr.name}' with src/dst address group (shared) '{addr}'")
                if is_src_match:
                    vr.add_src_addr_grp(addr, INPUT_LINE_NUM)
                else:
                    vr.add_dst_addr_grp(addr, INPUT_LINE_NUM)
                add_flag = True

        if not add_flag:
            try:
                if "/" in addr:
                    cur_addr = Address(addr, INPUT_LINE_NUM, False)
                    cur_addr.set_addr_value(addr, INPUT_LINE_NUM)
                else:
                    cur_addr = Address(addr, INPUT_LINE_NUM, False)
                    cur_addr.set_addr_value(addr + "/32", INPUT_LINE_NUM)
                cur_addr.set_addr_type(AddressType.IP_V4_PREFIX, INPUT_LINE_NUM)
                v_logger.info(f"Tenant {cur_tnt.name}: Adding Address {cur_addr.name} to current tenant")
                cur_tnt.add_address(cur_addr, INPUT_LINE_NUM)
                if is_src_match:
                    vr.add_src_addr(addr, INPUT_LINE_NUM)
                else:
                    vr.add_dst_addr(addr, INPUT_LINE_NUM)
                add_flag = True
            except:
                v_logger.error(f"Tenant {cur_tnt.name}: while adding rule {vr.name} to current tenant, error while parsing address")
        
        if not add_flag:
            if addr in predef_countries:
                if is_src_match:
                    vr.add_src_addr_region(addr, INPUT_LINE_NUM)
                else:
                    vr.add_dst_addr_region(addr, INPUT_LINE_NUM)

        if not add_flag:
            v_logger.error(f"tenant {cur_tnt.name}: while adding ngfw rule '{vr.name}' no address or address group found with name '{addr}'")


def clean_string(input_string: str) -> str:
    """remove any character that is not a-z, A-Z, 0-9, -, _ from a string.
    """
    return re.sub(r'[^a-zA-Z0-9\-_]', '', input_string)


def get_element_path(root, element) -> Tuple[str, str]:
    """Get the full path of an element in an XML tree.

    Args:
        root (etree.Element): The root element of the XML tree.
        element (etree.Element): The element to get the path for.

    Returns:
        Tuple[str, str]: A tuple containing the full path of the element in the XML tree, as well as the path without attribute values.
    """
    path_tag: List[str] = []
    path_tag_name: List[str] = []
    while element is not root:
        tag = element.tag
        name = element.get("name", "")
        tag_and_name = f"{tag}[{name}]" if name else tag
        path_tag.insert(0, tag)
        path_tag_name.insert(0, tag_and_name)
        element = element.getparent()
    return ("/".join(path_tag_name), "/".join(path_tag))
    

def load_shared_config(shared_xml, shared_tnt, v_logger,
                        predef_app_map: Dict, predef_subfamilies_map: Dict, predef_countries_map, predef_url_categories_map) -> None:
    if shared_xml is None:
        return

    # Define list of functions to load objects into tenant
    object_loaders = [
        load_application_objects_into_tenant,
        load_service_objects_into_tenant,
        load_service_group_objects_into_tenant,
        load_schedule_objects_into_tenant,
        load_url_category_objects_into_tenant,
        load_address_objects_into_tenant,
        load_external_address_group_objects_into_tenant,
        load_external_url_category_objects_into_tenant,
        load_address_group_objects_into_tenant
    ]

    # Iterate through list of object loaders and call each function
    for loader in object_loaders:
        if callable(loader):
            loader(shared_xml, shared_tnt, v_logger)
    load_application_groups_into_tenant(shared_xml, shared_tnt, v_logger, predef_app_map)
    load_application_filters_into_tenant(shared_xml, shared_tnt, v_logger, predef_subfamilies_map)
    load_rules_into_tenant(shared_xml, shared_tnt, v_logger,predef_countries_map)    


def load_objects_into_tenant(v: Any, cur_tnt, predef_app_map: Dict[str, Application], predef_subfamilies_map, predef_countries: Dict[str, list], v_logger: Any) -> None:
    """
    Load various objects into a tenant.

    Args:
        v (Any): Storage object for Versa Config.
        cur_tnt (Tenant): The tenant to load the objects into.
        predef_app_map (Dict[str, Application]): A dictionary containing predefined application information.
        predef_subfamilies (Dict[str, SubFamily]): A dictionary containing predefined subfamily information.
        predef_countries (Dict[str, list]): A dictionary containing predefined country information.
        v_logger (Any): A logging module variable.

    Returns:
        None
    """
    # Process applications
    load_application_objects_into_tenant(v, cur_tnt, v_logger)

    # Process application groups
    load_application_groups_into_tenant(v, cur_tnt, v_logger, predef_app_map)

    # Process application filters
    load_application_filters_into_tenant(v, cur_tnt, v_logger, predef_subfamilies_map)

    # Process custom url categories
    load_url_category_objects_into_tenant(v, cur_tnt, v_logger)

    # Process address objects
    load_address_objects_into_tenant(v, cur_tnt, v_logger)

    # Process address group objects
    load_address_group_objects_into_tenant(v, cur_tnt, v_logger)

    # Process external list adddress objects
    load_external_address_group_objects_into_tenant(v, cur_tnt, v_logger)

    # Process external list url category objects
    load_external_url_category_objects_into_tenant(v, cur_tnt, v_logger)

    # Process service objects
    load_service_objects_into_tenant(v, cur_tnt, v_logger)

    # Process service group objects
    load_service_group_objects_into_tenant(v, cur_tnt, v_logger)

    # Process schedule objects
    load_schedule_objects_into_tenant(v, cur_tnt, v_logger)


def populate_predefined_subfamilies_map(subfamilies_csv, subfamilies_fh: Any, versa_cfg: Any) -> Tuple[Any, Dict[str, list]]:
    """
    Populate predefined subfamilies from a CSV file into a dictionary.

    Args:
        subfamilies_csv (csv.reader): Contents of the subfamilies file.
        subfamilies_fh (Any): File handle for the subfamilies file.
        versa_cfg (Any): Storage object for Versa Config.

    Returns:
        Tuple[Any, Dict[str, list]]: A tuple containing the updated versa_cfg object and the predef_subfamilies dictionary.
    """
    predef_subfamilies_map: Dict[str, list] = {row[0]: row for row in subfamilies_csv}
    subfamilies_fh.close()
    versa_cfg.set_predef_subfamilies_map(predef_subfamilies_map)
    return versa_cfg, predef_subfamilies_map


def load_rules_into_tenant(v, cur_tnt, v_logger, predef_countries):
    # Process security rules
    cur_ngfw = NextGenFirewall(cur_tnt.name + "_policy", INPUT_LINE_NUM, False)
    cur_tnt.set_next_gen_firewall(cur_ngfw, INPUT_LINE_NUM)

    rules = v.findall("./pre-rulebase/security/rules/entry")
    for r in rules:
        rname = r.attrib["name"].replace(" ", "_")
        vr = NextGenFirewallRule(rname, INPUT_LINE_NUM, False)
        vr.set_tenant(cur_tnt)
        cur_ngfw.add_rule(vr)

        # Process source zone match
        src_zones = [sz.text.replace(" ", "_") for sz in r.findall("./from/member")]
        if len(src_zones) > 0 and "any" not in src_zones:
            vr.set_src_zone_map({sz: INPUT_LINE_NUM for sz in src_zones})

        # Process destination zone match
        dst_zones = [dz.text.replace(" ", "_") for dz in r.findall("./to/member")]
        if len(dst_zones) > 0 and "any" not in dst_zones:
            vr.set_dst_zone_map({dz: INPUT_LINE_NUM for dz in dst_zones})

        # Process source address match
        src_addresses = [sa.text.replace(" ", "_") for sa in r.findall("./source/member")]
        if len(src_addresses) > 0 and "any" not in src_addresses:
            process_rule_address_match(vr, cur_tnt, {sa: INPUT_LINE_NUM for sa in src_addresses}, True, v_logger, predef_countries)

        # Process destination address match
        dst_addresses = [da.text.replace(" ", "_") for da in r.findall("./destination/member")]
        if len(dst_addresses) > 0 and "any" not in dst_addresses:
            process_rule_address_match(vr, cur_tnt, {da: INPUT_LINE_NUM for da in dst_addresses}, False, v_logger, predef_countries)

        # Process service match
        services = [svc.text.replace(" ", "_") for svc in r.findall("./service/member")]
        if len(services) > 0 and "any" not in services:
            vr.set_service_map({svc: INPUT_LINE_NUM for svc in services})

        # Process service group match
        service_groups = [sg.text.replace(" ", "_") for sg in r.findall("./service-group/member")]
        if len(service_groups) > 0 and "any" not in service_groups:
            for sg in service_groups:
                vr.add_service(sg, INPUT_LINE_NUM)

        # Process schedule match
        schedule = r.find("./schedule")
        if schedule is not None:
            vr.set_schedule(schedule.text.strip().replace(" ", "_"), INPUT_LINE_NUM)

        # Process application match
        applications = [app.text.replace(" ", "_") for app in r.findall("./application/member")]
        if len(applications) > 0 and "any" not in applications:
            vr.set_application_map({app: INPUT_LINE_NUM for app in applications})

        # Process url-category match
        url_categories = [uc.text.replace(" ", "_") for uc in r.findall("./category/member")]
        if len(url_categories) > 0 and "any" not in url_categories:
            vr.set_url_category_map({uc: INPUT_LINE_NUM for uc in url_categories})

        # Process action match
        action = r.find("./action")
        if action is not None:
            astr = action.text.strip()
            if astr == "allow":
                vr.set_action(FirewallRuleAction.ALLOW, INPUT_LINE_NUM)
            elif astr == "deny":
                vr.set_action(FirewallRuleAction.DENY, INPUT_LINE_NUM)


def main(args_list: list) -> bool:
    """main _summary_

    Args:
        args (list): Command line arguments

    Returns:
        bool: True if successful, False otherwise
    """
    tnt_xlate_map: Dict = {}
    predef_apps: Dict = {}
    predef_app_map: Dict = {}

    print("")
    print("Starting...")
    print("--------------------------------")
    print("Parsing commandline arguments...")
    args = parse_args(args_list)
    print("Setting up the logger...")
    v_logger = the_logger(args)
    
    print("Creating output directory...")
    if not create_output_dir(args):
        return False
    
    print("Opening 3rd party config file...")
    xml_root = open_3rd_party_config_file(args)
    
    if args.create_interface_list:
        print("Creating zone to interface file")
        create_zone_interface_file(args, xml_root)
        print("!!!Created zone/interface file!!!")
        print(f"!!!Edit {args.zone_file} then run script again without -cil!!!")
        print("Exiting")
        return False
    
    if args.template_file_name != None:
       print("Reading Versa Template File")
       args.template_name = get_template_name(args.template_file_name)

    
    print("Importing predefined files...")
    app_csv, app_fh = open_predefined_applications(args)
    url_root = open_predefined_URL_categories_XML(args)
    countries_csv, countries_fh = open_predefined_countries_file(args)
    subfamilies_csv, subfamilies_fh = open_predefined_subfamilies_file(args)
    
    zone_csv, zone_fh = open_zone_interface_file(args)
    
    print("Opening output files...")
    pan_config_file_name, out_fh = open_output_files(args)
                
    versa_cfg = VersaConfig("VersaCfg_From_PAN_" + pan_config_file_name)
    versa_cfg.set_logger(v_logger)

    print("Populating Maps...")
    versa_cfg, tnt_xlate_map, versa_intf_zone_map = populate_zone_interface_map(zone_csv, zone_fh, versa_cfg, tnt_xlate_map)
    populate_interfaces_networks_zones_map(versa_intf_zone_map, v_logger, versa_cfg, args)
    predef_apps, predef_app_map, versa_cfg = populate_predefined_applications_map(app_csv, app_fh, versa_cfg)
    versa_cfg, predef_url_categories_map = populate_predefined_url_categories_map(url_root, predef_apps, versa_cfg)
    versa_cfg, predef_countries_map = populate_predefined_countries_map(countries_csv, countries_fh, versa_cfg)
    versa_cfg, predef_subfamilies_map = populate_predefined_subfamilies_map(subfamilies_csv, subfamilies_fh, versa_cfg)

    # Load the shared vsys config into the Provider-DataStore tenant
    print("Adding tenant to Versa configuration file...")
    versa_cfg.add_tenant(args.org_name, "0")
    shared_tnt = versa_cfg.get_tenant(args.org_name, "0")
    shared_xml = xml_root.find("./shared")
    tnt_xlate_map["shared"] = [args.org_name]
    versa_cfg.set_tenant_xlate_map(tnt_xlate_map)
    
    print("Loading shared configuration...")
    load_shared_config(shared_xml, shared_tnt, v_logger, predef_app_map, predef_subfamilies_map, predef_countries_map,predef_url_categories_map)

    # Process all tenants from the pan cfg file
    vsys_list = xml_root.findall("./devices/entry/vsys/entry")
    print("Processing tenants...")
    for v in vsys_list:
        # Get current tenant
        src_tnt = v.attrib["name"].replace(" ", "_")
        tnt, _ = tnt_xlate_map[src_tnt]
        cur_tnt = versa_cfg.get_tenant(tnt, "0")
        cur_tnt.set_shared_tenant(shared_tnt)

        # Load objects and rules into tenant
        load_objects_into_tenant(v, cur_tnt, predef_app_map, predef_subfamilies_map, predef_countries_map, v_logger)
        load_rules_into_tenant(v, cur_tnt,v_logger, predef_countries_map)        

    # Replace address and service groups with their respective members
    print("Replacing address group with their respective members...")
    versa_cfg.replace_address_by_address_group()
    print("Replacing service group with their respective members...")
    versa_cfg.replace_service_group_by_service_members()
    
    # Check and write configuration
    versa_cfg.check_config(STRICT_CHECKS)
    print(f"Writing configuration file {out_fh.name}")
    versa_cfg.write_config(tnt_xlate_map, args.template_name, args.device_name, out_fh)

    out_fh.close()
    return True


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
