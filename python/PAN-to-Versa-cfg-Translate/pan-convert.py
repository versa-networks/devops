#!/usr/bin/python
#  pan-convert.py - Convert Palo Alto config to Versa config
#
#  This file has the code to translate Palo Alto config to Versa config
#
#  Copyright (c) 2023, Versa Networks, Inc.
#  All rights reserved.
# Primary Objects:
# 1. Tenants
#    a. shared
#    b. All other tenants
# Secondary Objects:
# 1. Address
# 2. AddressGroup
# 3. Application
# 4. ApplicationGroup
# 5. ApplicationFilter
# 6. FirewallRule
# 7. NextGenFirewall
# 8. NextGenFirewallRule
# 9. Schedule
# 10. Service
# 11. ServiceGroup
# 12. URLCategory


import argparse
import csv
import logging
import os
import re
import sys
from argparse import Namespace
from datetime import datetime
from typing import Any, Dict, List, Optional, TextIO, Tuple, Union

from lxml import etree as ET

import versa
from versa.Address import Address, AddressType
from versa.AddressGroup import AddressGroup
from versa.application import Application, AppMatchRules
from versa.ApplicationFilter import ApplicationFilter
from versa.ApplicationGroup import ApplicationGroup
from versa.FirewallRule import FirewallRuleAction
from versa.NextGenFirewall import NextGenFirewall
from versa.NextGenFirewallRule import NextGenFirewallRule
from versa.Schedule import Schedule
from versa.Service import Service
from versa.ServiceGroup import ServiceGroup
from versa.URLCategory import URLCategory
from versa.VersaConfig import VersaConfig

import validate_versa_config_file as validate_cfg

# Constants
LOG_FILENAME = "versa-cfg-translate.log"
"""str: Log file name."""

STRICT_CHECKS = False
"""bool: Enable strict checks."""

INPUT_LINE_NUM = 0  # This is unused and should be removed in the future
"""int: Input line number."""


def clean_string(input_string: str, spaces: bool) -> str:
    """
    Cleans the input string by removing any character that is not a-z, A-Z, 0-9, -, _, or space (if spaces is True).
    Args:
        input_string (str): The string to be cleaned.
        spaces (bool): If True, spaces are allowed in the cleaned string. If False, spaces are removed.
    Returns:
        str: The cleaned string, containing only a-z, A-Z, 0-9, -, _ characters and possibly spaces.
    """
    return re.sub(f"[^a-zA-Z0-9-_{' ' if spaces else ''}]", "", input_string)


def parse_args(args_list: list) -> Namespace:
    """
    Parse command-line arguments.

    This function uses argparse to parse command-line arguments. The arguments include paths to various input files,
    options for output, and other configuration parameters.

    Args:
        args_list (list): List of command-line arguments.

    Returns:
        argparse.Namespace: Namespace object with the following attributes:
            - pan_config_file: Path to Palo Alto config file in XML format.
            - zone_file: Path to zone/interface CSV file.
            - app_file: Path to Versa predefined applications CSV file.
            - subfamilies_file: Path to Versa application subfamilies CSV file.
            - url_file: Path to Versa predefined URL categories XML file.
            - countries_file: Path to Versa predefined countries XML file.
            - template_file_name: Template name.
            - device_name: Device name.
            - output_dir: Path to output directory.
            - versa_paths_file: Path to Versa path segments file.
            - org_name: Organization name.
            - template_name: Versa Template name.
            - create_interface_list: Flag to create Interface List File.
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
        "-f",
        "--families_file",
        dest="families_file",
        action="store",
        help="Path to Versa application families CSV file",
        default="Predefined/app_families.csv",
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
        "-at",
        "--app_tags_file",
        dest="app_tags_file",
        action="store",
        help="Path to Versa application tags CSV file",
        default="Predefined/app_tags.csv",
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
        "-cil",
        "--create_interface_list",
        dest="create_interface_list",
        action="store_true",
        help="Create Interface List File",
    )
    args = parser.parse_args(args_list)

    return args


def the_logger(args: Namespace) -> logging.Logger:
    """
    Create a logger object and configure it to write logs to a file.

    This function creates a logger object, sets its level to DEBUG, and adds a file handler that writes logs to a file
    in the output directory specified in the command-line arguments. The log file is named according to the LOG_FILENAME
    constant. If there is an error creating the logger or the file handler, the function prints an error message and
    exits the program.

    Args:
        args (argparse.Namespace): Command-line arguments. The output_dir attribute specifies the directory where the
        log file will be created.
    Returns:
        logging.Logger: Logger object configured to write logs to a file in the output directory. If there is an error
        creating the logger or the file handler, the function will exit the program and will not return a value.
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
    except Exception as e_tl:
        print(f"Error: Unable to create logger with {log_path}")
        print(f"Error Details: {e_tl}")
        sys.exit(1)
    return logger


def create_output_dir(args: Namespace) -> bool:
    """
    Create the output directory if it doesn't exist.

    Args:
        args (Namespace): Command-line arguments. Expected to have an 'output_dir' attribute
                          which contains the path to the output directory as a string.
    Returns:
        str: The absolute path to the output directory.
    Exits:
        If 'output_dir' is not specified in 'args', or if there is an error creating the directory,
        the function will print an error message and exit the program with status code 1.
    """
    if not args.output_dir:
        print("Error: Please specify the output directory path")
        sys.exit(1)

    try:
        os.makedirs(args.output_dir, exist_ok=True)
    except OSError as e_cod:
        print(f"Error creating output directory: {args.output_dir}")
        print(f"Error Details: {e_cod}")
        print("Please enter a valid directory path where the output files will be written")
        sys.exit(1)

    return True


def open_3rd_party_config_file(args: Namespace):
    """
    Open and parse an XML file.

    Args:
        args (argparse.Namespace): Command-line arguments.
    Returns:
        Optional[Element]: XML root element, or None if there was an error.
    """
    try:
        with open(args.pan_config_file, "r", encoding="utf-8") as xml_file:
            xml_tree = ET.parse(xml_file)
            return xml_tree.getroot()
    except FileNotFoundError:
        print(f"Error: input file {args.pan_config_file} not found")
    except ET.ParseError as e_o3pcf:
        print(f"Error: unable to parse XML input file {args.pan_config_file}")
        print(f"Error Details: {e_o3pcf}")
    except Exception as e_o3pcf:
        print(f"Error: Unexpected error with file {args.pan_config_file}")
        print(f"Error Details: {e_o3pcf}")
    return None


def create_zone_interface_file(args: argparse.Namespace, xml_root) -> None:
    """
    Create a CSV file containing zone and interface information.

    Args:
        args (argparse.Namespace): Command-line arguments.
        xml_root (ET.Element): Root element of the XML tree.
    """
    if not args.zone_file:
        return

    try:
        with open(args.zone_file, "w", encoding="utf-8") as zone_interface_fh:
            print(
                "#3rd_Party_Interface,3rd_Party_Zone_Name,Versa_Zone_Name,Versa_Interface_Name,Versa_Paired_Interface_Name,Versa_VRF_Name,3rd_Party_Vsys_Name,Versa_Tenant_Name",
                file=zone_interface_fh,
            )

            zone_list: List[Dict[str, Union[str, int]]] = []
            count: int = 0

            for element in xml_root.xpath(".//*[devices]/descendant::zone", namespaces=xml_root.nsmap):
                for subelements in element:
                    zone_name: str = subelements.get("name").upper()
                    for k in subelements.iter("member"):
                        pan_interface: str = k.text

                        if any(row["3rd_Party_Zone_Name"] == zone_name for row in zone_list):
                            continue

                        match = re.search(r"\.\d{1,10}", pan_interface)
                        matched_text: str = match.group(0) if match else ""

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

                        print(
                            f"{pan_interface},{zone_name},{args.org_name}-{zone_name},{versa_interface_name},{versa_paired_interface_name},{args.org_name}-LAN-VR,vsys1,{args.org_name}",
                            file=zone_interface_fh,
                        )
                        count += 1

    except Exception as e_czif:
        print(f"Error: unable to open zone/interface csv file {args.zone_file} for writing")
        print(f"Error Details: {e_czif}")
        sys.exit(1)


def get_versa_template_data(template_file_name: str) -> Optional[Tuple[str, str, str, str]]:
    """
    Extract template, organization names, services, and service node groups from a file.

    Args:
        template_file_name (str): The name of the template file.
    Raises:
        FileNotFoundError: If the template file is not found.
        ValueError: If unable to parse the template file.
    Returns:
        Optional[Tuple[str, str, str, str]]: The names of the template, organization, services, and service node groups, or None if not found.
    """
    try:
        with open(template_file_name, "r", encoding="utf-8") as file:
            content = file.read()

        template_match = re.search(r"template\s+(.*?)\s+\{", content)
        org_name_match = re.search(r"org\s+(.*?)\s+\{", content)
        org_services_match = re.search(r"services\s+\[\s+(.*?)\s+\]", content)
        service_node_groups_match = re.search(r"(service-node-groups\s+\{.*?\})", content, re.DOTALL)

        template_name = template_match.group(1) if template_match else None
        org_name = org_name_match.group(1) if org_name_match else None
        org_services = org_services_match.group(1) if org_services_match else None
        service_node_groups = service_node_groups_match.group(1) if service_node_groups_match else None

        if not template_name or not org_name or not org_services or not service_node_groups:
            raise ValueError(f"Unable to parse the file {template_file_name}")

        return template_name, org_name, org_services, service_node_groups

    except FileNotFoundError as exc:
        raise FileNotFoundError(f"File {template_file_name} not found.") from exc


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

    try:
        versa_configuration_fh = open(outfile, "w+", encoding="utf-8")
    except OSError as e_oof:
        print("Error: unable to open output files for writing")
        print(f"Error Details: {e_oof}")
        sys.exit(1)

    return pan_config_file_name, versa_configuration_fh


def populate_zone_interface_map(args, versa_cfg: Any, tnt_xlate_map: Dict[str, List[str]]):
    """
    Populate the interface zone map from a CSV file.

    Args:
        args: Command-line arguments. Expected to have a 'zone_file' attribute
              which contains the path to the zone file as a string.
        versa_cfg (Any): Storage object for Versa Config.
        tnt_xlate_map (Dict[str, List[str]]): A dictionary containing tenant translation information.
    Returns:
        Tuple[Any, Dict[str, List[str]], Dict[str, List[str]]]: A tuple containing the updated versa_cfg object, tnt_xlate_map dictionary, and the versa_intf_zone_map dictionary.
    """
    print("    Zone/Interface")

    if not args.zone_file:
        print("Error: Please specify the interface/zone CSV file")
        return versa_cfg, tnt_xlate_map, {}

    pan_intf_zone_map: Dict[str, List[str]] = {}
    versa_intf_zone_map: Dict[str, List[str]] = {}
    cur_line_num: int = 0

    try:
        with open(args.zone_file, "r", encoding="utf-8") as zone_interface_fh:
            zone_interface_csv_reader = csv.reader(zone_interface_fh)
            for zone_interface_csv_row in zone_interface_csv_reader:
                cur_line_num += 1

                if zone_interface_csv_row[0].startswith("#") or len(zone_interface_csv_row) < 4:
                    continue

                pan_intf_zone_map[zone_interface_csv_row[0]] = zone_interface_csv_row
                versa_intf_zone_map[zone_interface_csv_row[3]] = zone_interface_csv_row + [str(cur_line_num)]

                src_tnt, tnt = zone_interface_csv_row[6], zone_interface_csv_row[7]
                if not versa_cfg.has_tenant(tnt):
                    versa_cfg.add_tenant(tnt)
                    tnt_xlate_map[src_tnt] = [tnt]
    except OSError as e_ozif:
        print(f"Error: unable to open zone/interface CSV file {args.zone_file} for reading")
        print(f"Error Details: {e_ozif}")
        return versa_cfg, tnt_xlate_map, {}

    return versa_cfg, tnt_xlate_map, versa_intf_zone_map


def populate_predefined_applications_map(args, versa_cfg: Any) -> Tuple[Any, Dict[str, Application], Dict[str, List[str]]]:
    """
    Populate predefined applications from a CSV file into a dictionary.

    Args:
        args: Command-line arguments. Expected to have an 'app_file' attribute
              which contains the path to the applications file as a string.
        versa_cfg (Any): Storage object for Versa Config.
    Returns:
        Tuple[Any, Dict[str, Application], Dict[str, List[str]]]: A tuple containing the updated versa_cfg object, predefined_app_map dictionary, and the predefined_apps dictionary.
    """
    print("    Applications")

    if not args.app_file:
        print("Please specify the predefined applications CSV file")
        sys.exit(1)

    predefined_apps: Dict[str, List[str]] = {}
    predefined_app_map: Dict[str, Application] = {}

    try:
        with open(args.app_file, "r", encoding="utf-8") as predefined_apps_fh:
            predefined_apps_csv_reader = csv.reader(predefined_apps_fh)
            for predefined_apps_csv_row in predefined_apps_csv_reader:
                if predefined_apps_csv_row and not predefined_apps_csv_row[0].startswith("#"):
                    if len(predefined_apps_csv_row) > 0 and len(predefined_apps_csv_row[0]) > 0:
                        try:
                            int(predefined_apps_csv_row[0])
                        except ValueError:
                            continue

                        app_name = predefined_apps_csv_row[3]
                        predefined_apps[app_name] = predefined_apps_csv_row
                        cur_app = Application(app_name, True)
                        predefined_app_map[app_name] = cur_app
    except OSError as e_opa:
        print(f"Error: unable to open predefined applications CSV file {args.app_file} for reading")
        print(f"Error Details: {e_opa}")
        sys.exit(1)
    except csv.Error as e_opa:
        print(f"Error: unable to parse predefined applications CSV file {args.app_file}")
        print(f"Error Details: {e_opa}")
        sys.exit(1)

    versa_cfg.set_predef_app_map(predefined_app_map)
    return versa_cfg, predefined_app_map, predefined_apps


def populate_predefined_url_categories_map(args, predefined_apps, versa_cfg) -> Tuple[Any, Dict[str, URLCategory]]:
    """
    Populate predefined URL categories from an XML file into a dictionary.

    Args:
        args: Command-line arguments. Expected to have a 'url_file' attribute
              which contains the path to the URL categories file as a string.
        versa_cfg (Any): Storage object for Versa Config.
    Returns:
        Tuple[Any, Dict[str, URLCategory]]: A tuple containing the updated versa_cfg object and the predefined_url_categories_map dictionary.
    """
    print("    URL categories")

    if not args.url_file:
        print("Please specify the predefined URL categories file")
        return versa_cfg, {}

    predefined_url_categories_map = {}
    try:
        tree = ET.parse(args.url_file)
        predefined_url_categories_xml_root = tree.getroot()
        for url_categories in predefined_url_categories_xml_root.findall("./categories/entity/subtype"):
            url_categories_name = url_categories.text
            predefined_apps[url_categories_name] = url_categories
            predefined_url_categories_map[url_categories_name] = URLCategory(url_categories_name, True)
    except ET.ParseError as e_opuc:
        print(f"Error: unable to parse URL categories XML file {args.url_file}")
        print(f"Error Details: {e_opuc}")
        return versa_cfg, {}
    except OSError as e_opuc:
        print(f"Error: unable to open URL categories XML file {args.url_file} for reading")
        print(f"Error Details: {e_opuc}")
        return versa_cfg, {}

    versa_cfg.set_predef_url_cat_map(predefined_url_categories_map)
    return versa_cfg, predefined_url_categories_map


def populate_predefined_countries_map(args, versa_cfg: Any) -> Tuple[Any, Dict[str, list]]:
    """
    Populate predefined countries from a CSV file into a dictionary.

    Args:
        args: Command-line arguments. Expected to have a 'countries_file' attribute
              which contains the path to the countries file as a string.
        versa_cfg (Any): Storage object for Versa Config.
    Returns:
        Tuple[Any, Dict[str, list]]: A tuple containing the updated versa_cfg object and the predefined_countries_map dictionary.
    """
    print("    Countries")

    if not args.countries_file:
        print("Please specify the predefined countries file")
        return versa_cfg, {}

    predefined_countries_map: Dict[str, list] = {}
    try:
        with open(args.countries_file, "r", encoding="utf-8") as predefined_countries_fh:
            predefined_countries_csv_reader = csv.reader(predefined_countries_fh)
            for row in predefined_countries_csv_reader:
                if row and not row[0].startswith("#"):
                    code = row[1].strip()
                    predefined_countries_map[code] = row
    except FileNotFoundError:
        print(f"Error: countries CSV file {args.countries_file} not found")
        return versa_cfg, {}
    except Exception as e_opcf:
        print(f"Error: unable to open countries CSV file {args.countries_file} for reading")
        print(f"Error Details: {e_opcf}")
        return versa_cfg, {}

    versa_cfg.set_predef_countries_map(predefined_countries_map)
    return versa_cfg, predefined_countries_map


def populate_predefined_families_map(args, versa_cfg: Any) -> Tuple[Any, Dict[str, list]]:
    """
    Populate predefined families from a CSV file into a dictionary.

    Args:
        args: Command-line arguments. Expected to have a 'families_file' attribute
              which contains the path to the families file as a string.
        versa_cfg (Any): Storage object for Versa Config.
    Returns:
        Tuple[Any, Dict[str, list]]: A tuple containing the updated versa_cfg object and the predefined_families_map dictionary.
    """
    print("    Families")

    if not args.families_file:
        print("Please specify the predefined families categories file")
        return versa_cfg, {}

    predefined_families_map: Dict[str, list] = {}
    try:
        with open(args.families_file, "r", encoding="utf-8") as predefined_app_families_fh:
            predefined_app_families_csv_reader = csv.reader(predefined_app_families_fh)
            for predefined_app_csv_row in predefined_app_families_csv_reader:
                if predefined_app_csv_row and not predefined_app_csv_row[0].startswith("#"):
                    family = predefined_app_csv_row[0]
                    predefined_families_map[family] = predefined_app_csv_row[1:]
    except FileNotFoundError:
        print(f"Error: families CSV file {args.families_file} not found")
        return versa_cfg, {}
    except Exception as e_opff:
        print(f"Error: unable to open families CSV file {args.families_file} for reading")
        print(f"Error Details: {e_opff}")
        return versa_cfg, {}

    versa_cfg.set_predef_families_map(predefined_families_map)
    return versa_cfg, predefined_families_map


def populate_predefined_subfamilies_map(args, versa_cfg: Any) -> Tuple[Any, Dict[str, list]]:
    """
    Populate predefined subfamilies from a CSV file into a dictionary.

    Args:
        args: Command-line arguments. Expected to have a 'subfamilies_file' attribute
              which contains the path to the subfamilies file as a string.
        versa_cfg (Any): Storage object for Versa Config.
    Returns:
        Tuple[Any, Dict[str, list]]: A tuple containing the updated versa_cfg object and the predefined_subfamilies_map dictionary.
    """
    print("    Subfamilies")

    if not args.subfamilies_file:
        print("Please specify the predefined sub families categories file")
        return versa_cfg, {}

    predefined_subfamilies_map: Dict[str, list] = {}
    try:
        with open(args.subfamilies_file, "r", encoding="utf-8") as predefined_app_subfamilies_fh:
            predefined_app_subfamilies_csv_reader = csv.reader(predefined_app_subfamilies_fh)
            for row in predefined_app_subfamilies_csv_reader:
                if row and not row[0].startswith("#"):
                    subfamily = row[0]
                    predefined_subfamilies_map[subfamily] = row[1:]
    except FileNotFoundError:
        print(f"Error: subfamilies CSV file {args.subfamilies_file} not found")
        return versa_cfg, {}
    except Exception as e_opsf:
        print(f"Error: unable to open subfamilies CSV file {args.subfamilies_file} for reading")
        print(f"Error Details: {e_opsf}")
        return versa_cfg, {}

    versa_cfg.set_predef_subfamilies_map(predefined_subfamilies_map)
    return versa_cfg, predefined_subfamilies_map


def populate_predefined_app_tags_map(args, versa_cfg: Any) -> Tuple[Any, Dict[str, list]]:
    """
    Populate predefined app tags from a CSV file into a dictionary.

    Args:
        args: Command-line arguments. Expected to have an 'app_tags_file' attribute
              which contains the path to the app tags file as a string.
        versa_cfg (Any): Storage object for Versa Config.
    Returns:
        Tuple[Any, Dict[str, list]]: A tuple containing the updated versa_cfg object and the predefined_app_tags_map dictionary.
    """
    print("    Tags")

    if not args.app_tags_file:
        print("Please specify the predefined app tags file")
        return versa_cfg, {}

    predefined_app_tags_map: Dict[str, list] = {}
    try:
        with open(args.app_tags_file, "r", encoding="utf-8") as predefined_app_tags_fh:
            predefined_app_tags_csv_reader = csv.reader(predefined_app_tags_fh)
            for row in predefined_app_tags_csv_reader:
                if row and not row[0].startswith("#"):
                    app_tags = row[0]
                    predefined_app_tags_map[app_tags] = row[1:]
    except FileNotFoundError:
        print(f"Error: app tags CSV file {args.app_tags_file} not found")
        return versa_cfg, {}
    except Exception as e_opatf:
        print(f"Error: unable to open app tags CSV file {args.app_tags_file} for reading")
        print(f"Error Details: {e_opatf}")
        return versa_cfg, {}

    versa_cfg.set_predef_app_tags_map(predefined_app_tags_map)
    return versa_cfg, predefined_app_tags_map


def get_key(my_dict: dict, val: Any) -> Any:
    """
    Returns the key in a dictionary for a given value.

    Args:
        my_dict (dict): The dictionary to search.
        val (Any): The value to find the key for.
    Returns:
        Any: The key for the given value.
    Raises:
        ValueError: If the value is not found in the dictionary.
    """
    for key, value in my_dict.items():
        if val in value:
            return key
    return ""


def get_text_and_clean(element) -> Optional[str]:
    """
    Extracts text from an XML element and cleans it.

    Args:
        element (_Element, optional): The XML element to extract text from.
    Returns:
        str, optional: The cleaned text, or None if the element is None or contains no text.
    """
    if element is not None and element.text is not None:
        return clean_string(element.text, True)
    return None


def add_tag(app_tags: List[str], tag: str, predefined_app_tags_map: Dict[str, str]) -> None:
    """
    Adds a tag to the beginning of the app_tags list if it's not already present.

    This function first retrieves the key associated with the given tag from the
    predefined_app_tags_map. If this key is not already in the app_tags list, it's
    inserted at the beginning of the list.

    Args:
        app_tags (List[str]): The list of application tags.
        tag (str): The tag to add.
        predefined_app_tags_map (Dict[str, str]): The mapping of predefined application tags.
    Returns:
        None
    """
    key = get_key(predefined_app_tags_map, tag)
    if key not in app_tags:
        app_tags.insert(0, key)


def handle_port(port: str):
    """
    Handles different formats of port values and returns a tuple of port value, port low, and port high.

    If the port value is "dynamic", it returns "any" as the port value and two empty strings as port low and high.
    If the port value does not contain a "-", it returns the port value and two empty strings as port low and high.
    If the port value contains a "-", it splits the value into port low and high and returns two empty strings as the port value.

    Parameters:
        port (str): The port value in one of the following formats: "dynamic", "port", or "port_low-port_high".
    Returns:
        Tuple[str, str, str]: A tuple containing the port value, port low, and port high. The port value is "any" or the port value if it does not contain a "-", and it's an empty string otherwise.
        The port low and high are empty strings if the port value is "dynamic" or does not contain a "-", and they are the split port value otherwise.
    """
    if port == "dynamic":
        return "any", "", ""
    elif "-" not in port:
        return port, "", ""
    else:
        port_low, port_high = port.split("-")
        return "", port_low, port_high


def load_zones_networks_interfaces(versa_intf_zone_map: Dict[str, List[str]], v_logger: logging.Logger, versa_cfg: Any, args: Any) -> None:
    """
    Add interfaces, networks, and zones to the Versa configuration.

    Args:
        versa_intf_zone_map (Dict[str, List[str]]): A dictionary containing interface, network, and zone information.
        v_logger (logging.Logger): A logging module variable.
        versa_cfg (Any): A storage object for Versa Config.
        args (Any): Command line arguments.
    """
    print("    Zones, Networks, Interfaces")
    for v_ifname, ifinfo in versa_intf_zone_map.items():
        if "#" in v_ifname:
            continue
        tnt = ifinfo[7]
        cur_tnt = versa_cfg.get_tenant(tnt)
        v_logger.info(f"{args.zone_file}:{ifinfo[8]}: adding versa interface {v_ifname} to tenant {tnt}; network {ifinfo[2]}; zone {ifinfo[1]}; pan interface {ifinfo[0]}")
        versa_cfg.add_interface_to_network(ifinfo[2], v_ifname)

        if ifinfo[2]:
            cur_tnt.add_zone_network(ifinfo[1], ifinfo[2], ifinfo[8])
        else:
            cur_tnt.add_zone_interface(ifinfo[1], v_ifname, ifinfo[8])

    return versa_cfg


def load_application_objects(tnt_xml, tnt: Any, v_logger: logging.Logger, _, predefined_families_map: Dict[str, Any], predefined_subfamilies_map: Dict[str, Any], predefined_app_tags_map: Dict[str, Any]) -> None:
    """
    Load application objects into a tenant from an XML document.

    This function iterates over the application entries in the XML document, creates an `Application` object for each entry,
    and adds the object to a tenant. It also sets various properties on the `Application` object based on the XML entry.

    Args:
        tnt_xml (_Element): The XML element containing the application objects.
        tnt (Any): The tenant object to add the application objects to.
        v_logger (logging.Logger): The logger object for logging messages.
        predefined_app_map (Dict[str, Any]): Predefined application map.
        predefined_families_map (Dict[str, Any]): Predefined families map.
        predefined_subfamilies_map (Dict[str, Any]): Predefined subfamilies map.
        predefined_app_tags_map (Dict[str, Any]): Predefined application tags map.

    This function also handles the following application properties:
        - Description
        - Category
        - Subcategory
        - Risk
        - Evasive behavior
        - Bandwidth consumption
        - Usage by malware
        - File transfer capability
        - Known vulnerabilities
        - Ability to tunnel other applications
        - Misuse potential
        - Pervasive use
        - File type identification
        - Virus identification
        - Data identification
        - Technology
    """
    print("    Applications")

    applications = tnt_xml.xpath("./application/entry")
    tags = {
        "evasive-behavior",
        "consume-big-bandwidth",
        "used-by-malware",
        "able-to-transfer-file",
        "has-known-vulnerability",
        "tunnel-other-application",
        "tunnel-applications",
        "prone-to-misuse",
        "pervasive-use",
        "file-type-ident",
        "virus-ident",
        "data-ident",
    }

    for app in applications:
        app_tags: List[str] = []
        application_name = (clean_string(app.attrib["name"], False)).upper()

        # This may not work as expected for application mapping
        if application_name in tnt.application_map:
            continue
        cur_app = Application(application_name, False)

        cur_app_desc_text = get_text_and_clean(app.find("./description"))
        if cur_app_desc_text:
            cur_app.set_description(cur_app_desc_text)

        cur_app_category_text = get_text_and_clean(app.find("./category"))
        if cur_app_category_text:
            add_tag(app_tags, cur_app_category_text, predefined_app_tags_map)
            versa_family = get_key(predefined_families_map, cur_app_category_text)
            cur_app.set_family(versa_family)

        cur_app_subcategory_text = get_text_and_clean(app.find("./subcategory"))
        if cur_app_subcategory_text:
            add_tag(app_tags, cur_app_subcategory_text, predefined_app_tags_map)
            versa_subfamily = get_key(predefined_subfamilies_map, cur_app_subcategory_text)
            cur_app.set_subfamily(versa_subfamily)

        cur_app_risk_value = get_text_and_clean(app.find("./risk"))
        if cur_app_risk_value:
            cur_app.set_risk(cur_app_risk_value)

        for tag in tags:
            tag_element = app.find(f"./{tag}")
            if tag_element is not None and tag_element.text == "yes":
                add_tag(app_tags, tag, predefined_app_tags_map)

        cur_app_technology_text = get_text_and_clean(app.find("./technology"))
        if cur_app_technology_text:
            add_tag(app_tags, cur_app_technology_text, predefined_app_tags_map)
            cur_app.set_tag(" ".join(app_tags))
        else:
            cur_app.set_tag("Data")

        cur_app.set_precedence("100")
        cur_app.set_app_timeout("0")
        cur_app.set_app_match_ips(True)

        # Gather Port Members that define the application. I am unable to find the every possible configuration options so this code may not be 100% accurate
        protocol_map = {"tcp": 6, "udp": 17, "icmp": 1}
        app_default_members = app.xpath("./default/port/member")
        member_count = 0

        for member in app_default_members:
            app_match_rule_name = clean_string(member.text, False)
            protocol, port = member.text.split("/")
            protocol = protocol_map.get(protocol, "")
            (
                destination_port_value,
                destination_port_low,
                destination_port_high,
            ) = handle_port(port)

            app_match_rule = AppMatchRules(app_match_rule_name, False)
            app_match_rule.set_protocol(protocol)
            app_match_rule.set_destination_port_value(str(destination_port_value))
            if destination_port_low:
                app_match_rule.set_destination_port_low(int(destination_port_low))
            if destination_port_high:
                app_match_rule.set_destination_port_high(int(destination_port_high))

            cur_app.attach_app_match_rule(app_match_rule)
            member_count += 1

        v_logger.info(f"Tenant {tnt.name}: Adding Application {cur_app.name} to current tenant")
        tnt.add_application(cur_app)


def load_service_objects(tnt_xml, tnt: Any, v_logger: logging.Logger) -> None:
    """
    Load service objects from an XML element into a tenant.

    Args:
        tnt_xml (Element): An XML element containing service information.
        tnt (Any): A tenant object.
        v_logger (logging.Logger): A logger object for logging messages.
    """
    print("    Services")
    services = tnt_xml.findall("./service/entry")
    for svc in services:
        svc_name = clean_string(svc.attrib["name"], False)
        if svc_name in tnt.service_map:
            continue
        cur_svc = Service(svc_name, False)

        cur_svc_desc = svc.find("./description")
        if cur_svc_desc is not None and cur_svc_desc.text is not None:
            cur_svc_desc.text = clean_string(cur_svc_desc.text, False)
            cur_svc.set_description(cur_svc_desc.text)

        cur_svc_proto = svc.find("./protocol/*")
        if cur_svc_proto is not None:
            cur_svc_port = cur_svc_proto.find("port").text
            cur_svc.set_proto(cur_svc_proto.tag)
            cur_svc.set_port(cur_svc_port)

        v_logger.info(f"Tenant {tnt.name}: Adding Service {svc_name}")
        tnt.add_service(cur_svc)


def load_service_group_objects(tnt_xml, tnt: Any, v_logger: logging.Logger) -> None:
    """
    Load service group objects from an XML element into a tenant.

    Args:
        tnt_xml (Element): An XML element containing service group information.
        tnt (Any): A tenant object.
        v_logger (logging.Logger): A logger object for logging messages.
    """
    print("    Service groups")
    svc_groups = tnt_xml.findall("./service-group/entry")
    for svc_group in svc_groups:
        svc_group_name = clean_string(svc_group.attrib["name"], False)

        cur_svc_group = tnt.get_service_group(svc_group_name)
        if cur_svc_group is None:
            cur_svc_group = ServiceGroup(svc_group_name, False)
            tnt.add_service_group(cur_svc_group)

        svc_group_members = svc_group.findall("./members/member")
        for member in svc_group_members:
            svc_group_member = member.text
            v_logger.info(f"tenant {tnt}: adding service group '{svc_group_name}' with service member '{svc_group_member}'")
            cur_svc_group.add_service(svc_group_member)


def load_schedule_objects(tnt_xml, tnt: Any, v_logger: logging.Logger) -> None:
    """
    Load schedule objects from an XML element into a tenant.

    Args:
        tnt_xml (Element): An XML element containing schedule information.
        tnt (Any): A tenant object.
        v_logger (logging.Logger): A logger object for logging messages.
    """
    print("    Schedules")
    for schedule in tnt_xml.findall("./schedule/entry"):
        schedule_name = clean_string(schedule.attrib["name"], False)
        cur_sched = Schedule(schedule_name, False, False)

        nonrecurring_schedule = schedule.findall("./schedule-type/non-recurring/member")
        for date_time_member in nonrecurring_schedule:
            end_date_str = date_time_member.text.split("-")[1].split("@")[0].strip()
            end_date = datetime.strptime(end_date_str, "%Y/%m/%d").date()
            if end_date >= datetime.now().date():
                cur_sched.add_non_recurring_day_time(date_time_member.text.strip())

        daily_schedule = schedule.findall("./schedule-type/recurring/daily/member")
        for day_member in daily_schedule:
            cur_sched.add_recurring_day_time("daily", day_member.text.strip())

        weekly_schedule = schedule.findall("./schedule-type/recurring/weekly/*")
        for weekly_member in weekly_schedule:
            for time_member in weekly_member.findall("./member"):
                cur_sched.add_recurring_day_time(weekly_member.tag, time_member.text.strip())

        if len(cur_sched.non_recur_days_times) > 0 or cur_sched.schedule_type.name != "NON_RECURRING":
            v_logger.info(f"Tenant {tnt.name}: Adding Schedule {schedule_name}")
            tnt.add_schedule(cur_sched)


def load_url_category_objects(tnt_xml, tnt: Any, v_logger: logging.Logger) -> None:
    """
    Load URL category objects from an XML element into a tenant.

    Args:
        tnt_xml (Element): An XML element containing URL category information.
        tnt (Any): A tenant object.
        v_logger (logging.Logger): A logger object for logging messages.
    """
    print("    URL categories")
    url_categories = tnt_xml.findall("./profiles/custom-url-category/entry")
    for url_category in url_categories:
        uc_name = clean_string(url_category.attrib["name"], False)
        if uc_name in tnt.url_categories_map:
            continue
        cur_url_category_object = URLCategory(uc_name, False)

        url_category_desc = url_category.find("./description")
        if url_category_desc is not None and url_category_desc.text is not None:
            url_category_desc.text = clean_string(url_category_desc.text, True)
            cur_url_category_object.set_description(url_category_desc.text)

        url_category_members = url_category.findall("./list/member")
        for url_category_member in url_category_members:
            url_category_member_str = url_category_member.text.strip()
            if "*" in url_category_member_str:
                cur_url_category_object.add_pattern(url_category_member_str.replace("*", ".*"))
            else:
                cur_url_category_object.add_host(url_category_member_str)

        v_logger.info(f"Tenant {tnt.name}: Adding URL category '{cur_url_category_object.name}' to current tenant")
        tnt.add_url_category(cur_url_category_object)


def load_address_objects(_tnt_xml, _tnt: Any, v_logger) -> None:
    """
    Load address objects from an XML element into a tenant.

    Args:
        tnt_xml (Element): An XML element containing address information.
        tnt (Any): A tenant object.
        v_logger (logging.Logger): A logger object for logging messages.
    """
    # Process address objects
    print("    Addresses")
    # Process address objects
    addresses = _tnt_xml.findall("./address/entry")
    for addr in addresses:
        addr_name = clean_string(addr.attrib["name"], False)
        cur_addr = Address(addr_name, False)
        ip_netmask = addr.find("./ip-netmask")
        add_flag = False
        if ip_netmask is not None:
            cur_addr.set_addr_value(clean_string(ip_netmask.text, False))
            cur_addr.set_addr_type(AddressType.IP_V4_PREFIX)
            add_flag = True

        if not add_flag:
            addr_fqdn = addr.find("./fqdn")
            if addr_fqdn is not None:
                cur_addr.set_addr_value(addr_fqdn.text)
                cur_addr.set_addr_type(AddressType.FQDN)
                add_flag = True

        if not add_flag:
            v_logger.error(f"Tenant {_tnt.name}: Address {cur_addr.name} unsupported")
            continue

        v_logger.info(f"Tenant {_tnt.name}: Adding Address {cur_addr.name} to current tenant")
        _tnt.add_address(cur_addr)


def load_external_url_category_objects(tnt_xml, tnt: Any, v_logger: logging.Logger) -> None:
    """
    Load external URL category objects from an XML element into a tenant.

    Args:
        tnt_xml (Element): An XML element containing external URL category information.
        tnt (Any): A tenant object.
        v_logger (logging.Logger): A logger object for logging messages.
    """
    print("    External URL categories")
    url_categories = tnt_xml.findall("./external-list/entry")
    for url_category in url_categories:
        entry = url_category.find("type/url")
        if entry is not None:
            url_category_name = clean_string(url_category.attrib["name"], False)
            cur_url_category = tnt.get_url_category(url_category_name) or tnt.add_url_category(URLCategory(url_category_name, False))

            url_category_desc = entry.find("./description")
            if url_category_desc is not None and url_category_desc.text is not None:
                url_category_desc.text = clean_string(url_category_desc.text, True)
                cur_url_category.set_description(url_category_desc.text)

            url = entry.find("./url").text
            ix = url.rfind("/")
            fn = url[ix + 1 :]
            v_logger.info(f"Tenant {tnt.name}: Adding URL category '{cur_url_category.name}' with file name '{fn}'")
            cur_url_category.set_filename(fn)


def load_address_group_objects(tnt_xml, tnt: Any, v_logger: logging.Logger) -> None:
    """
    Load address group objects from an XML element into a tenant.

    Args:
        tnt_xml (Element): An XML element containing address group information.
        tnt (Any): A tenant object.
        v_logger (logging.Logger): A logger object for logging messages.
    """
    print("    Address groups")
    addr_groups = tnt_xml.findall("./address-group/entry")
    for addr_group in addr_groups:
        address_group_name = clean_string(addr_group.attrib["name"], False)
        if address_group_name in tnt.address_group_map:
            continue
        cur_addr_grp = tnt.get_address_group(address_group_name)
        if cur_addr_grp is None:
            cur_addr_grp = AddressGroup(address_group_name, False)
            tnt.add_address_group(cur_addr_grp)
        addr_group_desc = addr_group.find("./description")
        if addr_group_desc is not None and addr_group_desc.text is not None:
            addr_group_desc.text = clean_string(addr_group_desc.text, True)
            cur_addr_grp.set_description(addr_group_desc.text)

        address_group_members = addr_group.findall("./members/member")
        for address_group_member in address_group_members:
            addr = clean_string(address_group_member.text, False)
            v_logger.info(f"tenant {tnt.name}: adding address group '{address_group_name}' with address member '{addr}'")
            cur_addr_grp.add_address(addr)

        address_group_members = addr_group.findall("./static/member")
        for address_group_member in address_group_members:
            addr = clean_string(address_group_member.text, False)
            v_logger.info(f"tenant {tnt.name}: adding address group '{address_group_name}' with address member '{addr}'")
            cur_addr_grp.add_address(addr)


def load_application_groups(tnt_xml, tnt: Any, v_logger: logging.Logger, predefined_app_map: Dict[str, Any]) -> None:
    """
    Load application groups into a tenant.

    Args:
        _tnt_xml (Element): The XML element containing the application groups.
        _tnt (Any): The tenant object to add the application groups to.
        _v_logger (logging.Logger): The logger object for logging messages.
        _predefined_app_map (Dict[str, Any]): A dictionary mapping predefined application names to their objects.
    """
    # Process application groups
    print("    Application groups")
    app_groups = tnt_xml.findall("./application-group/entry")
    for app_group in app_groups:
        app_group_name = clean_string(app_group.attrib["name"], False)
        if app_group_name in tnt.address_group_map:
            continue
        cur_app_grp = tnt.get_application_group(app_group_name)
        if cur_app_grp is None:
            cur_app_grp = ApplicationGroup(app_group_name, False)
            tnt.add_application_group(cur_app_grp)

        app_group_members = app_group.findall("./members/member")
        for app_group_member in app_group_members:
            # check if the application is user defined application
            application_name = clean_string(app_group_member.text, False).upper()
            member_added = False

            cur_app = tnt.get_application(application_name)

            sh_tnt = tnt.get_shared_tenant()
            if cur_app is not None:
                v_logger.info(f"Tenant {tnt.name}: Adding application group '{app_group_name}' with custom application member '{application_name}'")
                cur_app_grp.add_application(cur_app)
                member_added = True

            if not member_added:
                app_grp = tnt.get_application_group(application_name)
                if app_grp is not None:
                    v_logger.info(f"Tenant {tnt.name}: Adding application group '{app_group_name}' with custom application group member '{application_name}'")
                    cur_app_grp.add_application_group(app_grp)
                    member_added = True

            if not member_added and sh_tnt is not None:
                cur_app = sh_tnt.get_application(application_name)
                if cur_app is not None:
                    v_logger.info(f"Tenant {tnt.name}: Adding application group '{app_group_name}' with shared application member '{application_name}'")
                    cur_app_grp.add_application(cur_app)
                    member_added = True
                else:
                    app_grp = sh_tnt.get_application_group(application_name)
                    if app_grp is not None:
                        v_logger.info(f"Tenant {tnt.name}: Adding application group '{app_group_name}' with shared application group member '{application_name}'")
                        cur_app_grp.add_application_group(app_grp)
                        member_added = True

            if not member_added:
                # check if the application is predefined application
                if application_name in predefined_app_map:
                    cur_app = predefined_app_map[application_name]
                    v_logger.info(f"Tenant {tnt.name}: Adding application group '{app_group_name}' with predefined application member '{application_name}'")
                    cur_app_grp.add_application(cur_app)
                    member_added = True

            if not member_added:
                v_logger.error(f"Tenant {tnt.name}: Adding application group '{app_group_name}' with unknown application member '{application_name}'")


def load_application_filters(tnt_xml, tnt: Any, v_logger: logging.Logger, predefined_subfamilies_map: Dict[str, Any]) -> None:
    """
    Load application filters from an XML element into a tenant.

    Args:
        tnt_xml (Element): An XML element containing application filter information.
        tnt (Any): A tenant object.
        v_logger (logging.Logger): A logger object for logging messages.
        predefined_subfamilies_map (Dict[str, Any]): A dictionary of predefined subfamilies.
    """
    print("    Application filters")
    app_filters = tnt_xml.findall("./application-filter/entry")
    for app_filter in app_filters:
        app_filter_name = clean_string(app_filter.attrib["name"], False)
        if app_filter_name in tnt.application_filter_map:
            continue
        cur_app_filter = tnt.get_application_filter(app_filter_name)
        if cur_app_filter is None:
            cur_app_filter = ApplicationFilter(app_filter_name, False)
            tnt.add_application_filter(cur_app_filter)

        category_memebers = app_filter.findall("./category/member")
        for category_member in category_memebers:
            cur_app_filter.add_application_filter("family", category_member.text.strip())

        subcategory_members = app_filter.findall("./subcategory/member")
        for subcategory_member in subcategory_members:
            sc = subcategory_member.text.strip()
            if sc in list(predefined_subfamilies_map.keys()):
                cur_app_filter.add_application_filter("subfamily", subcategory_members.text.strip())
            else:
                v_logger.error(f"Tenant {tnt.name}; application filter {cur_app_filter.name}; subfamily {subcategory_members} not found")

        risk_members = app_filter.findall("./risk/member")
        for risk_member in risk_members:
            cur_app_filter.add_application_filter("risk", risk_member.text.strip())

        productivity_members = app_filter.findall("./productivity/member")
        for productivity_member in productivity_members:
            cur_app_filter.add_application_filter("productivity", productivity_member.text.strip())

        tag_members = app_filter.findall("./tag/member")
        for tag_member in tag_members:
            cur_app_filter.add_application_filter("tag", tag_member.text.strip())


def process_rule_address_match(versa_rule_object, cur_tnt: versa.Tenant.Tenant, address_map: Dict[str, Any], is_src_match: bool, v_logger: logging.Logger, predef_countries: Dict[str, Any]) -> None:
    """
    Process the address match for a NextGenFirewallRule.

    Args:
        versa_rule_object (versa.NextGenFirewallRule): The NextGenFirewallRule object.
        cur_tnt (versa.Tenant.Tenant): The current tenant object.
        address_map (dict): A dictionary containing address information. The keys are address names and the values are irrelevant.
        is_src_match (bool): A boolean indicating whether the match is for the source address.
        v_logger (logging.Logger): A logging module variable.
        predef_countries (dict): A dictionary containing predefined country information. The keys are country names and the values are irrelevant.
    Logs:
        Information about the addition of addresses or address groups to the NextGenFirewallRule.
        Error message if no address or address group is found with the given name.
        Error message if there is an error while parsing the address.

    """
    sh_tnt = cur_tnt.get_shared_tenant()
    for addr in address_map:
        add_flag = False
        addr_object = cur_tnt.get_address(addr)
        if addr_object is not None:
            v_logger.info(f"tenant {cur_tnt.name}: adding ngfw rule '{versa_rule_object.name}' with src/dst address '{addr}'")
            if is_src_match:
                versa_rule_object.add_src_addr(addr)
            else:
                versa_rule_object.add_dst_addr(addr)
            add_flag = True

        if not add_flag:
            addr_group_object = cur_tnt.get_address_group(addr)
            if addr_group_object is not None:
                v_logger.info(f"tenant {cur_tnt.name}: adding ngfw rule '{versa_rule_object.name}' with src/dst address group '{addr}'")
                if is_src_match:
                    versa_rule_object.add_src_addr_grp(addr)
                else:
                    versa_rule_object.add_dst_addr_grp(addr)
                add_flag = True

        if not add_flag:
            addr_object = sh_tnt.get_address(addr)
            if addr_object is not None:
                v_logger.info(f"tenant {cur_tnt.name}: adding ngfw rule '{versa_rule_object.name}' with src/dst address (shared) '{addr}'")
                if is_src_match:
                    versa_rule_object.add_src_addr(addr)
                else:
                    versa_rule_object.add_dst_addr(addr)
                add_flag = True

        if not add_flag:
            addr_group_object = sh_tnt.get_address_group(addr)
            if addr_group_object is not None:
                v_logger.info(f"tenant {cur_tnt.name}: adding ngfw rule '{versa_rule_object.name}' with src/dst address group (shared) '{addr}'")
                if is_src_match:
                    versa_rule_object.add_src_addr_grp(addr)
                else:
                    versa_rule_object.add_dst_addr_grp(addr)
                add_flag = True

        if not add_flag:
            try:
                if "/" in addr:
                    cur_addr = Address(addr, False)
                    cur_addr.set_addr_value(addr)
                else:
                    cur_addr = Address(addr, False)
                    cur_addr.set_addr_value(addr + "/32")
                cur_addr.set_addr_type(AddressType.IP_V4_PREFIX)
                v_logger.info(f"Tenant {cur_tnt.name}: Adding Address {cur_addr.name} to current tenant")
                cur_tnt.add_address(cur_addr)
                if is_src_match:
                    versa_rule_object.add_src_addr(addr)
                else:
                    versa_rule_object.add_dst_addr(addr)
                add_flag = True
            except Exception as e_pram:
                v_logger.error(f"Tenant {cur_tnt.name}: while adding rule {versa_rule_object.name} to current tenant, error while parsing address: {e_pram}")

        if not add_flag:
            if addr in predef_countries:
                if is_src_match:
                    versa_rule_object.add_src_addr_region(addr)
                else:
                    versa_rule_object.add_dst_addr_region(addr)

        if not add_flag:
            v_logger.error(f"tenant {cur_tnt.name}: while adding ngfw rule '{versa_rule_object.name}' no address or address group found with name '{addr}'")


def get_element_path(root, element) -> Tuple[str, str]:
    """
    Get the full path of an element in an XML tree.

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


def load_rules_into_tenant(xml, cur_tnt, v_logger, predef_countries):
    """
    Load security rules from an XML element into a Tenant object.

    This function processes security rules from the XML element and loads them into a NextGenFirewall object associated with the Tenant. It handles various types of matches
    including source zone, destination zone, source address, destination address, service, service group, schedule, application, url-category, and action.

    Args:
        xml (Element): XML element containing security rules.
        cur_tnt (Tenant): Tenant object to load rules into.
        v_logger (logging.Logger): Logger object for logging.
        predef_countries (dict): Dictionary mapping predefined country names to country objects.
    Returns:
        None
    """

    # Process security rules
    print("    Security rules")
    cur_ngfw = NextGenFirewall(cur_tnt.name + "_policy", False)
    cur_tnt.set_next_gen_firewall(cur_ngfw)

    rules = xml.xpath(".//security/rules/entry")
    for rule in rules:
        rule_name = clean_string(rule.attrib["name"], False)
        versa_rule_object = NextGenFirewallRule(rule_name, False)
        versa_rule_object.set_tenant(cur_tnt)
        cur_ngfw.add_rule(versa_rule_object)

        # Process source zone match
        src_zones = [clean_string(sz.text, False) for sz in rule.findall("./from/member")]
        if len(src_zones) > 0 and "any" not in src_zones:
            versa_rule_object.set_src_zone_map({sz: 0 for sz in src_zones})

        # Process destination zone match
        dst_zones = [clean_string(dz.text, False) for dz in rule.findall("./to/member")]
        if len(dst_zones) > 0 and "any" not in dst_zones:
            versa_rule_object.set_dst_zone_map({dz: 0 for dz in dst_zones})

        # Process source address match
        src_addresses = [clean_string(sa.text, False) for sa in rule.findall("./source/member")]
        if len(src_addresses) > 0 and "any" not in src_addresses:
            process_rule_address_match(
                versa_rule_object,
                cur_tnt,
                {sa: 0 for sa in src_addresses},
                True,
                v_logger,
                predef_countries,
            )

        # Process destination address match
        dst_addresses = [clean_string(da.text, False) for da in rule.findall("./destination/member")]
        if len(dst_addresses) > 0 and "any" not in dst_addresses:
            process_rule_address_match(
                versa_rule_object,
                cur_tnt,
                {da: 0 for da in dst_addresses},
                False,
                v_logger,
                predef_countries,
            )

        # Process service match
        services = [clean_string(svc.text, False) for svc in rule.findall("./service/member")]
        if len(services) > 0 and "any" not in services:
            versa_rule_object.set_service_map({svc: 0 for svc in services})

        # Process service group match
        service_groups = [clean_string(sg.text, False) for sg in rule.findall("./service-group/member")]
        if len(service_groups) > 0 and "any" not in service_groups:
            for sg in service_groups:
                versa_rule_object.add_service(sg)

        # Process schedule match
        schedule = rule.find("./schedule")
        if schedule is not None:
            versa_rule_object.set_schedule(clean_string(schedule.text.strip(), False))

        # Process application match
        applications = [clean_string(app.text, False) for app in rule.findall("./application/member")]
        if len(applications) > 0 and "any" not in applications:
            versa_rule_object.set_application_map({app: 0 for app in applications})

        # Process url-category match
        url_categories = [clean_string(uc.text, False) for uc in rule.findall("./category/member")]
        if len(url_categories) > 0 and "any" not in url_categories:
            versa_rule_object.set_url_category_map({uc: 0 for uc in url_categories})

        # Process action match
        action = rule.find("./action")
        if action is not None:
            astr = action.text.strip()
            if astr == "allow":
                versa_rule_object.set_action(FirewallRuleAction.ALLOW)
            elif astr == "deny":
                versa_rule_object.set_action(FirewallRuleAction.DENY)


def load_config(
    xml,
    tnt: Any,
    v_logger: logging.Logger,
    predefined_app_map: Dict[str, Any],
    predefined_families_map: Dict[str, Any],
    predefined_subfamilies_map: Dict[str, Any],
    predefined_app_tags_map: Dict[str, Any],
    predefined_countries_map: Dict[str, Any],
    _,
) -> None:
    """
    Load configuration data from an XML element into a Tenant object.

    This function uses a list of loader functions to load various types of objects (applications, services, etc.) into the Tenant object.
    If the XML element is None, the function returns without doing anything.

    Args:
        xml (Optional[Element]): XML element containing configuration data. If this is None, the function returns
        without doing anything.
        tnt (Tenant): Tenant object to load data into.
        v_logger (logging.Logger): Logger object for logging.
        predefined_app_map (Dict[str, Any]): Dictionary mapping predefined application names to application objects.
        predefined_families_map (Dict[str, Any]): Dictionary mapping predefined subfamily names to subfamily objects.
        predefined_subfamilies_map (Dict[str, Any]): Dictionary mapping predefined subfamily names to subfamily objects.
        predefined_countries_map (Dict[str, Any]): Dictionary mapping predefined country names to country objects.
        predefined_url_categories_map (Dict[str, Any]): Dictionary mapping predefined URL category names to URL
        category objects.
    Returns:
        None
    """
    if xml is None:
        return

    # Define list of functions to load objects into tenant
    object_loaders = [
        load_service_objects,
        load_service_group_objects,
        load_address_objects,
        load_address_group_objects,
        load_url_category_objects,
        load_external_url_category_objects,
        load_schedule_objects,
    ]

    # Iterate through list of object loaders and call each function
    for loader in object_loaders:
        if callable(loader):
            loader(xml, tnt, v_logger)
    load_application_objects(
        xml,
        tnt,
        v_logger,
        predefined_app_map,
        predefined_families_map,
        predefined_subfamilies_map,
        predefined_app_tags_map,
    )
    load_application_groups(xml, tnt, v_logger, predefined_app_map)
    load_application_filters(xml, tnt, v_logger, predefined_subfamilies_map)
    if xml.tag == "devices":
        load_rules_into_tenant(xml, tnt, v_logger, predefined_countries_map)


def main(args_list: list) -> bool:
    """
    Main function to convert Palo Alto configuration to Versa configuration.

    This function parses command line arguments, sets up the logger, creates the output directory, opens the Palo Alto config file, imports predefined files, populates maps, loads shared and
    tenant-specific configurations, replaces address and service groups with their respective members, checks the configuration, and writes the Versa configuration file.

    Args:
        args_list (list): List of command line arguments.

    Returns:
        bool: True if the conversion is successful, False otherwise.
    """
    tnt_xlate_map: Dict = {}
    predefined_apps: Dict = {}
    predefined_app_map: Dict = {}

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

    print("Creating Versa Configuration file...")
    pan_config_file_name, versa_configuration_fh = open_output_files(args)

    print("Opening Palo Alto config file...")
    xml_root = open_3rd_party_config_file(args)

    if args.template_file_name:
        print("Reading Versa Template File")
        template_data = get_versa_template_data(args.template_file_name)
        if template_data:
            (
                args.template_name,
                args.org_name,
                args.org_services,
                args.service_node_groups,
            ) = template_data

    if args.create_interface_list:
        print("Creating zone to interface file")
        create_zone_interface_file(args, xml_root)
        print("!!!Created zone/interface file!!!")
        print(f"!!!Edit {args.zone_file} then run script again without -cil!!!")
        print("Exiting...")
        return False

    versa_cfg = VersaConfig("Versa_config_based_on-" + pan_config_file_name)
    versa_cfg.set_logger(v_logger)

    print("\nPopulating Maps...")
    versa_cfg, tnt_xlate_map, versa_intf_zone_map = populate_zone_interface_map(args, versa_cfg, tnt_xlate_map)
    versa_cfg, predefined_app_map, predefined_apps = populate_predefined_applications_map(args, versa_cfg)
    versa_cfg, predefined_url_categories_map = populate_predefined_url_categories_map(args, predefined_apps, versa_cfg)
    versa_cfg, predefined_countries_map = populate_predefined_countries_map(args, versa_cfg)
    versa_cfg, predefined_families_map = populate_predefined_families_map(args, versa_cfg)
    versa_cfg, predefined_subfamilies_map = populate_predefined_subfamilies_map(args, versa_cfg)
    versa_cfg, predefined_app_tags_map = populate_predefined_app_tags_map(args, versa_cfg)

    # Load the shared vsys config into the Provider-DataStore tenant
    print(f"\nAdding tenant, {args.org_name}, to Versa configuration object...")
    versa_cfg.add_tenant(args.org_name)
    shared_tnt = versa_cfg.get_tenant(args.org_name)
    shared_xml = xml_root.find("./shared")
    tnt_xlate_map["shared"] = [args.org_name]
    versa_cfg.set_tenant_xlate_map(tnt_xlate_map)

    print("Loading shared configuration...")
    load_zones_networks_interfaces(versa_intf_zone_map, v_logger, versa_cfg, args)
    load_config(
        shared_xml,
        shared_tnt,
        v_logger,
        predefined_app_map,
        predefined_families_map,
        predefined_subfamilies_map,
        predefined_app_tags_map,
        predefined_countries_map,
        predefined_url_categories_map,
    )

    cur_tnt = versa_cfg.get_tenant(args.org_name)
    cur_tnt.set_shared_tenant(shared_tnt)
    devices_xml = xml_root.find("./devices")

    print(f"\nLoading configuration into tenant, {args.org_name}...")
    # Load objects into tenant
    load_config(
        devices_xml,
        cur_tnt,
        v_logger,
        predefined_app_map,
        predefined_families_map,
        predefined_subfamilies_map,
        predefined_app_tags_map,
        predefined_countries_map,
        predefined_url_categories_map,
    )

    # Check and write configuration
    versa_cfg.check_config(STRICT_CHECKS)
    print(f"\nWriting configuration file {versa_configuration_fh.name}")
    versa_cfg.write_config(
        tnt_xlate_map,
        args.template_name,
        args.device_name,
        versa_configuration_fh,
        args,
    )

    print("Checking configuration file for errors...")
    lines = versa_configuration_fh.readlines()

    validation_checks = {validate_cfg.check_parentheses: "Parentheses check", validate_cfg.check_indentation: "Indentation check"}

    for check, message in validation_checks.items():
        if check(lines):
            print(f"    {message} passed")
        else:
            print(f"    {message} failed")

    versa_configuration_fh.close()

    return True


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)
