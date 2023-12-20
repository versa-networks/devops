#!/usr/bin/python
#
# written by Rob Kauffman
#
# using parts from
#  Web Traffic Generator
#     https://github.com/ecapuano/web-traffic-generator
#     by @eric_capuano
#  Traffic Generation for App-ID-URL-Categories-Reputations
#     https://github.com/versa-networks/devops/tree/master/python/Security%20Automation%20-%20Traffic%20Generation%20for%20App-ID-URL-Categories-Reputations
#     by Swetha Ragunath
#  Security Automation Script to Generate Zone-DoS Traffic Validation
#     https://github.com/versa-networks/devops/tree/7f68a474f55febea49ff6612fdae45db32bed76e/python/Security%20Automation%20Script%20to%20Generate%20Zone-DoS%20Traffic%20Validation
#     by Swetha Ragunath
#
#
"""
Creates web traffice based on a list of URLs.

"""

# Standard library imports
import logging
import random
import re
import signal
import subprocess
import sys
import time
from typing import List

# Third party imports
from dataclasses import dataclass
import lxml.etree as ET
import requests

# Local application imports
import config

# Disable warnings
requests.packages.urllib3.disable_warnings()


class Colors():
    """
    This class defines color codes for different text colors.
    It's used to print colored text to the console for better readability.
    """
    BLACK = "\033[90m"
    BLUE = "\033[34m"
    CYAN = "\033[96m"
    GREEN = "\033[32m"
    GREY= "\033[90m"
    MAGENTA = "\033[95m"
    NONE = "\033[0m"
    PURPLE = "\033[95m"
    RED = "\033[91m"
    WHITE = '\033[97m'
    YELLOW = "\033[93m"


@dataclass
class URLClass:
    """
    A class to represent a URL.

    Attributes
    ----------
    url : str
        The actual URL.
    kind : str
        The kind of the URL.
    rule : str
        The rule associated with the URL.
    action : str
        The action associated with the URL.
    reputation : str
        The reputation of the URL.
    category : str
        The category of the URL.
    source_line : int
        The line number in the source file where the URL is found.
    source_url : str
        The source URL where the URL is found.
    """

    url: str
    kind: str
    rule: str
    action: str
    reputation: str
    category: str
    source_line: int
    source_url: str

    def __str__(self):
        """
        Returns a string representation of the URLClass object.

        Returns
        -------
        str
            A string representation of the URLClass object.
        """
        return f"URL: {self.url}, Kind: {self.kind}, Rule: {self.rule},  Action: {self.action}, Reputation: {self.reputation}, Category: {self.category}, Source Line: {self.source_line}, Source URL: {self.source_url}"

def hr_bytes(bytes_, suffix="B"):
    """Provides a more legible byte format"""
    bits = 1024.0
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(bytes_) < bits:
            return f"{bytes_:.1f}{unit}{suffix}"
        bytes_ /= bits
    return f"{bytes_:.1f}Y{suffix}"


def do_request(url_class, data_meter, good_requests, bad_requests, depth):
    """A method which loads a page"""

    print(f"{Colors.PURPLE}  Requesting page:  {url_class.url}\n"
        f"    @                 {time.strftime('%H:%M:%S', time.localtime())}\n"
        f"    Kind:             {url_class.kind}\n"
        f"    Rule:             {url_class.rule}\n"
        f"    Action:           {url_class.action}\n"
        f"    Reputation:       {url_class.reputation}\n"
        f"    Category:         {url_class.category}\n"
        f"    Source Line:      {url_class.source_line}\n"
        f"    Source:           {url_class.source_url}\n"
        f"    Depth:            {depth}")

    headers = {"user-agent": config.USER_AGENT}

    try:
        r = requests.get(url_class.url, headers=headers, timeout=30, verify=False)
        page_size = len(r.content)
        data_meter += page_size

        print(f"{Colors.PURPLE}    Page size:        {hr_bytes(page_size)}")

        status = r.status_code
        if status != 200:
            bad_requests += 1
            print(f"{Colors.RED}    Response Code:    {status} and Reason {r.reason}")
            if status == 429:
                print(f"{Colors.RED}    Response Code:    {status} and Reason {r.reason}",) # We're making requests too frequently... sleeping longer...")
                config.MIN_WAIT += 10
                config.MAX_WAIT += 10
        else:
            print(f"{Colors.PURPLE}    Response Code:    {status} and Reason {r.reason}")
            good_requests += 1

        return r, data_meter, good_requests, bad_requests

    except (requests.exceptions.RequestException, requests.exceptions.Timeout) as do_req_err:
        # Prevent 100% CPU loop in a net down situation
        print(f"{Colors.RED}    Error:            {do_req_err}", Colors.NONE)
        bad_requests += 1
        time.sleep(30)
        # Return None as the request failed
        return None, data_meter, good_requests, bad_requests


def get_links(web_page, ignore_list, source_url):
    """A method which returns all links from page, less IGNORE_LIST links"""

    pattern = r"(?:href\=\")(https?:\/\/[^\"]+)(?:\")"
    links = re.findall(pattern, str(web_page.content))
    valid_links = []
    for link in links:
        if not any(ignore in link for ignore in ignore_list):
            temp_url = URLClass(link, "undefined", "undefined", "undefined", "undefined", "undefined", "N/A", source_url)
            valid_links.append(temp_url)

    return valid_links


def recursive_browse(url_class, depth, ignore_list, data_meter, good_requests, bad_requests):
    """
    Recursively browses a given URL up to a specified depth.

    This function makes a request to the given URL, scrapes the page for valid links,
    and then recursively calls itself on a random link from the scraped links. The recursion
    continues until the specified depth is reached.

    Parameters:
        url (str): The URL to start browsing from.
        depth (int): The depth of recursion. If depth is 0, the function will just load the page at the URL.

    Returns:
        None
    """

    if depth == 0:  # base case: depth of zero, load page
        web_page, data_meter, good_requests, bad_requests = do_request(url_class, data_meter, good_requests, bad_requests, depth)
        return data_meter, good_requests, bad_requests, depth

    # recursive case: load page, browse random link, decrement depth
    web_page, data_meter, good_requests, bad_requests = do_request(url_class, data_meter, good_requests, bad_requests, depth)  # load current page

    # give up if error loading page
    if not web_page:
        print(f"{Colors.YELLOW}    IGNORE_LISTing: page error {url_class.url}")
        ignore_list.append(url_class.url)
        return data_meter, good_requests, bad_requests, depth

    # scrape page for links not in IGNORE_LIST
    print(f"{Colors.NONE}\n    Scraping {url_class.url} for links")
    valid_links = get_links(web_page, ignore_list, url_class.url)
    print(f"{Colors.NONE}      Found {len(valid_links)} valid links")

    # give up if no links to browse
    if not valid_links:
        print(f"{Colors.YELLOW}    Stopping and IGNORE_LISTing: no links {url_class.url}")
        ignore_list.append(url_class.url)
        return data_meter, good_requests, bad_requests, depth

    # sleep and then recursively browse
    sleep_time = random.randrange(config.MIN_WAIT, config.MAX_WAIT)
    print(f"\n  Pausing for {sleep_time} seconds...")
    time.sleep(sleep_time)

    data_meter, good_requests, bad_requests, depth = recursive_browse(random.choice(valid_links), depth - 1, ignore_list, data_meter, good_requests, bad_requests)
    return  data_meter, good_requests, bad_requests, depth


def dos_creation(value):
    """
    This function initiates a Denial of Service (DOS) attack based on the provided value.

    It uses a dictionary to map attack types to their corresponding command-line commands and signals.
    If the provided value matches an attack type, the function starts the attack, waits for a specified duration,
    then sends a signal to terminate the attack.

    Parameters:
        value (str): The type of DOS attack to initiate. Must be a key in the 'attacks' dictionary.

    Raises:
        subprocess.CalledProcessError: If there's an error while executing the command-line command.
    """
    attacks = {
        "TCP Scan": [["nmap", "-sS", config.DOS_DST_IP], signal.SIGTERM],
        "UDP Scan": [["nmap", "-sU", config.DOS_DST_IP, "-min-rate 600"], signal.SIGINT],
        "HostSweep Flood": [["nmap", "-sn", config.DOS_DST_IP + "/24"], signal.SIGINT],
        "TCP Flood": [["hping3", "-S", config.DOS_DST_IP, "-p", config.DOS_DST_PORT, "--faster"], signal.SIGINT],
        "UDP Flood": [["hping3", "-2", config.DOS_DST_IP, "--faster"], signal.SIGINT],
        "ICMP Flood": [["hping3", "-1", config.DOS_DST_IP, "--fast", "--icmp-ipsrc", config.DOS_SOURCE_ADDRESS], signal.SIGINT],
        "SCTP Flood": [["hping3", "-n", config.DOS_DST_IP, "-0", "--ipproto", "132", "--flood", "--destport", "7654"], signal.SIGINT],
        "Other-IP Flood": [["hping3", "-n", config.DOS_DST_IP, "-0", "--ipproto", "47", "--flood", "--destport", "7654"], signal.SIGINT],
        "ICMP Fragmention": [["hping3", config.DOS_DST_IP, "-x", "--icmp"], signal.SIGINT],
        "ICMP Ping Zero ID": [["hping3", "-1", config.DOS_DST_IP, "--icmp-ipid", "0"], signal.SIGINT],
        "Non-SYN TCP": [["hping3", "-R", config.DOS_DST_IP], signal.SIGINT],
        "IP Spoofing": [["hping3", "-1", config.DOS_DST_IP, "-a", config.DOS_SOURCE_ADDRESS], signal.SIGINT],
        "IP Fragmentation": [["hping3", "-S", config.DOS_DST_IP, "-f"], signal.SIGINT],
        "Record-Route": [["hping3", config.DOS_DST_IP, "--rroute", "--icmp"], signal.SIGINT],
        "Strict-SRC-Routing": [["nping", "--tcp", config.DOS_DST_IP, "--ip-options", "S", "--rate", "100", "-c", "1000000"], signal.SIGINT],
        "Loose-SRC-Routing": [["nping", "--tcp", config.DOS_DST_IP, "--ip-options", "L", "--rate", "100", "-c", "1000000"], signal.SIGINT],
        "Timestamp": [["nping", "--tcp", config.DOS_DST_IP, "--ip-options", "T", "--rate", "100", "-c", "1000000"], signal.SIGINT],
        # Add other attacks here...
    }

    if value in attacks:
        print((" Starting " + value + " ").center(92, "~"))
        p = subprocess.Popen(attacks[value][0])
        print(" Automatically terminates in", config.DOS_DURATION_SEC, "seconds")
        time.sleep(config.DOS_DURATION_SEC)
        p.send_signal(attacks[value][1])
        p.terminate()
        print((" Terminating " + value).center(92, "~"))
    else:
        print("Invalid attack type")


def main() -> None:
    """
    This is the main function that drives the traffic generator script.

    It initializes several global variables, prints some initial information,
    and then enters an infinite loop. In each iteration of the loop, it may
    perform a Denial of Service (DOS) attack based on the configuration,
    and then it randomly selects a URL from a list and recursively browses it.

    The function handles KeyboardInterrupt exceptions to allow the script to be
    stopped by the user using Ctrl+C.

    Global variables used:
        data_meter: A counter for the total amount of data transferred.
        good_requests: A counter for the number of successful requests.
        bad_requests: A counter for the number of failed requests.
        loopcount: A counter for the number of loop iterations.
        all_urls: A list of all URLs to be browsed.

    Raises:
        KeyboardInterrupt: When the script is stopped by the user.
    """

    data_meter: int = 0
    good_requests: int = 0
    bad_requests: int = 0
    loopcount: int = 0

    try:
        parser = ET.XMLParser(remove_blank_text=True, encoding="utf-8", remove_comments=True)
        urls_xml = ET.parse(config.URLS_FILE_NAME, parser=parser)
        urls_root = urls_xml.getroot()
    except ET.ParseError as xml_parse_err:
        print(f"Failed to parse XML file: {config.URLS_FILE_NAME}")
        print(f"Error: {xml_parse_err}")
        sys.exit("Program terminated due to XML parsing error.")
    except FileNotFoundError:
        print(f"File not found: {config.URLS_FILE_NAME}")
        sys.exit("Program terminated due to missing file.")

    general_urls = []
    for general_url in urls_root.xpath(".//GeneralURLs"):
        for url in general_url.xpath(".//url"):
            temp_url = URLClass(url.text, "General URL", "Undefined", "Undefined", "Undefined", "Undefined", url.sourceline, "URLS.xml")
            general_urls.append(temp_url)
            #print(temp_url)

    """url: str
    kind: str
    rule: str
    action: str
    reputation: str
    category: str
    source_line: int
    source_url: str"""

    rule_specific_urls = []
    for rule_specific_url in urls_root.xpath(".//RuleSpecificURLs"):
        for traffic_generator_policy in rule_specific_url.xpath(".//Traffic_Generator_Policies"):
            for policy in traffic_generator_policy.xpath(".//TGP"):
                action = policy.xpath(".//action")[0].text if policy.xpath(".//action") else "Undefined"
                for url in policy.xpath(".//url"):
                    temp_url = URLClass(url.text, "Rule Specific URL", policy.attrib["name"], action, "Undefined", "Undefined", url.sourceline, "URLS.xml")
                    rule_specific_urls.append(temp_url)
                    #print(temp_url)

    rebutation_urls = []
    for reputation_url in urls_root.xpath(".//ReputationURLs"):
        for reputation in reputation_url.xpath(".//Reputation"):
            action = reputation.xpath(".//action")[0].text if reputation.xpath(".//action") else "Undefined"
            for url in reputation.xpath(".//url"):
                temp_url = URLClass(url.text, "Reputation URL", "Undefined", action, reputation.attrib["name"], "Undefined", url.sourceline, "URLS.xml")
            rebutation_urls.append(temp_url)
            #print(temp_url)

    category_urls = []
    for category_url in urls_root.xpath(".//CategoryURLs"):
        for category in category_url.xpath(".//category"):
            action = category.xpath(".//action")[0].text if category.xpath(".//action") else "Undefined"
            for url in category.xpath(".//url"):
                temp_url = URLClass(url.text, "Category URL", "Undefined", action, "Undefined", category.attrib["name"], url.sourceline, "URLS.xml")
            category_urls.append(temp_url)
            #print(temp_url)

    dos_traffic_profiles: List[str] = [entry.text for entry in urls_root.xpath(".//DOSTrafficProfiles")[0]]
    working_dos_traffic_profiles: List[str] = dos_traffic_profiles[:]  # Creates a new dos traffic profiles list
    random.shuffle(working_dos_traffic_profiles)

    ignore_list = [entry.text for entry in urls_root.xpath(".//IgnoreList")[0]]

    all_urls: List[URLClass] = general_urls + rule_specific_urls + rebutation_urls + category_urls
    working_url_list: List[URLClass] = all_urls[:]  # Creates a new working url list
    random.shuffle(working_url_list)

    print(f"{Colors.GREEN}\n{'~'*92}")
    print("Traffic generator started")
    print("This script will run indefinitely. Ctrl+C to stop.")
    print(f"{'~'*92}\n{Colors.NONE}")
    print(f"{Colors.BLUE}{'~'*92}")
    print(f"Running Denial of Service (DOS) attacks once every {config.CREATE_DOS_TRAFFIC_EVERY_X_TIMES} URL requests.")
    print(f"Diving between 3 and {config.MAX_DEPTH} links deep into {len(all_urls)} root URLs,")
    print(f"Waiting between {config.MIN_WAIT} and {config.MAX_WAIT} seconds between requests.")
    print(f"{'~'*92}{Colors.NONE}")

    try:
        while True:
            loopcount += 1
            print(f"{Colors.NONE}\nLoop Count: {loopcount}")
            if config.CREATE_DOS_TRAFFIC and ((loopcount % config.CREATE_DOS_TRAFFIC_EVERY_X_TIMES) == 0):
                print(f"\nRandomly selection one of {len(dos_traffic_profiles)} DOS Traffic attacks", Colors.RED)
                if not working_dos_traffic_profiles:
                    working_dos_traffic_profiles = dos_traffic_profiles[:]  # Creates a new dos traffic profiles list
                    random.shuffle(working_dos_traffic_profiles)
                random_dos_traffic = working_dos_traffic_profiles.pop()

                dos_creation(random_dos_traffic)

            match = re.search(r'[^/]+$', config.URLS_FILE_NAME)
            url_filename = match.group() if match else "unknown file"

            print(f"\nRandomly selecting one of {len(all_urls)} URLs from {url_filename} with {len(working_url_list)} remaining", Colors.PURPLE)

            if not working_url_list:
                working_url_list = all_urls[:]  # Creates a new working url list
                random.shuffle(working_url_list)
            random_url = working_url_list.pop()

            depth = random.choice(range(config.MIN_DEPTH, config.MAX_DEPTH))
            print(f"{Colors.PURPLE}{'~'*92}")
            print(
                f'{Colors.PURPLE}Recursively browsing from {random_url.url} up to {depth} links deep'
            )
            data_meter, good_requests, bad_requests, depth = recursive_browse(random_url, depth, ignore_list, data_meter, good_requests, bad_requests)
            print(
                f'{Colors.PURPLE}Finished recursive browsing from {random_url.url}'
            )
            print(f"{Colors.PURPLE}{'~'*92}")
            print("")
            print(f"{Colors.GREEN}Good requests:    {good_requests}", Colors.NONE)
            print(f"{Colors.RED}Bad reqeusts:     {bad_requests}", Colors.NONE)
            print(f"{Colors.NONE}Total Data DL'd:  {hr_bytes(data_meter)}", Colors.NONE)
    except KeyboardInterrupt:
        print("\nScript stopped by user. Exiting...")


if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO)
        main()
    except KeyboardInterrupt:
        logging.info("Execution interrupted by user")
    except requests.exceptions.RequestException as req_e:
        logging.error("An error occurred during a network request: %s", req_e)
    except ET.ParseError as parse_err:
        logging.error("An error occurred during XML parsing: %s", parse_err)
    except FileNotFoundError:
        logging.error("File not found: %s", config.URLS_FILE_NAME)
