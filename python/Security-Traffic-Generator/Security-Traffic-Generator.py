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

 
import requests
requests.packages.urllib3.disable_warnings() 
import re
import time
import random
import subprocess
import signal
import config
from http.client import responses

class Colors:
    RED = '\033[91m'
    YELLOW = '\033[93m'
    PURPLE = '\033[95m'
    GREEN = '\033[32m'
    BLUE = '\033[34m'
    NONE = '\033[0m'


def debug_print(message, color=Colors.NONE):
    """ A method which prints if DEBUG is set """
    if config.DEBUG:
        print(color + message + Colors.NONE)


def hr_bytes(bytes_, suffix='B', si=False):
    """ A method providing a more legible byte format """

    bits = 1024.0 if si else 1000.0

    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(bytes_) < bits:
            return "{:.1f}{}{}".format(bytes_, unit, suffix)
        bytes_ /= bits
    return "{:.1f}{}{}".format(bytes_, 'Y', suffix)


def do_request(url):
    """ A method which loads a page """

    global data_meter
    global good_requests
    global bad_requests

    debug_print("  Requesting page...".format(url))

    headers = {'user-agent': config.USER_AGENT}

    try:
        r = requests.get(url, headers=headers, timeout=30, verify=False)
    except:
        # Prevent 100% CPU loop in a net down situation
        time.sleep(30)
        return False

    page_size = len(r.content)
    data_meter += page_size

    debug_print("  Page size: {}".format(hr_bytes(page_size)))
    debug_print("  Data meter: {}".format(hr_bytes(data_meter)))

    status = r.status_code

    if (status != 200):
        bad_requests += 1
        debug_print("  Response status Code: {} and Reason {}".format(r.status_code,r.reason), Colors.RED)
        if (status == 429):
            debug_print(
                "  We're making requests too frequently... sleeping longer...")
            config.MIN_WAIT += 10
            config.MAX_WAIT += 10
    else:
        good_requests += 1

    debug_print("  Good requests: {}".format(good_requests))
    debug_print("  Bad reqeusts: {}".format(bad_requests))

    return r


def get_links(page):
    """ A method which returns all links from page, less IGNORE_LIST links """

    pattern = r"(?:href\=\")(https?:\/\/[^\"]+)(?:\")"
    links = re.findall(pattern, str(page.content))
    valid_links = [link for link in links if not any(
        b in link for b in config.IGNORE_LIST)]
    return valid_links


def recursive_browse(url, depth):
    """ A method which recursively browses URLs, using given depth """
    # Base: load current page and return
    # Recursively: load page, pick random link and browse with decremented depth

    debug_print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    debug_print("Recursively browsing [{}] ~~~ [depth = {}]".format(url, depth))

    if not depth:  # base case: depth of zero, load page
        do_request(url)
        return
    else:  # recursive case: load page, browse random link, decrement depth
        page = do_request(url)  # load current page
        # give up if error loading page
        if not page:
            debug_print("  Stopping and IGNORE_LISTing: page error".format(url), Colors.YELLOW)
            config.IGNORE_LIST.append(url)
            return

        # scrape page for links not in IGNORE_LIST
        debug_print("  Scraping page for links".format(url))
        valid_links = get_links(page)
        debug_print("  Found {} valid links".format(len(valid_links)))

        # give up if no links to browse
        if not valid_links:
            debug_print("  Stopping and IGNORE_LISTing: no links".format(url), Colors.YELLOW)
            config.IGNORE_LIST.append(url)
            return

        # sleep and then recursively browse
        sleep_time = random.randrange(config.MIN_WAIT, config.MAX_WAIT)
        debug_print("  Pausing for {} seconds...".format(sleep_time))
        time.sleep(sleep_time)
        

        recursive_browse(random.choice(valid_links), depth - 1)

def DOS_creation(value):
    #value = "TCP Scan" #Set to test value to test specific attack
    
    if value=="TCP Scan":
        print((" Starting " + value + " ").center(92, '~'))
        #os.system('nmap -sS config.DOS_DST_IP')
        p=subprocess.Popen(["nmap","-sS",config.DOS_DST_IP])
        debug_print("nmap -sS " + config.DOS_DST_IP)
        print(" Scan automatically terminates in",config.DOS_DURATION_SEC,"seconds")
        time.sleep(config.DOS_DURATION_SEC)
        p.send_signal(signal.SIGTERM)
        p.terminate()
        print((" Terminating " + value).center(92, '~'))

    if value=="UDP Scan":
        print((" Starting " + value + " ").center(92, '~'))
        p=subprocess.Popen(["nmap","-sU",config.DOS_DST_IP,"-min-rate 600"])
        debug_print("nmap -sU "+ config.DOS_DST_IP)
        print(" Scan automatically terminates in",config.DOS_DURATION_SEC,"seconds")
        time.sleep(config.DOS_DURATION_SEC)
        p.send_signal(signal.SIGINT)
        p.terminate()
        print((" Terminating " + value).center(92, '~'))
        
    if value=="HostSweep Flood":
        print((" Starting " + value + " ").center(92, '~'))
        p=subprocess.Popen(["nmap","-sn",config.DOS_DST_IP+"/24"])
        debug_print("nmap -sn " + config.DOS_DST_IP + "/24")
        print(" Scan automatically terminates in",config.DOS_DURATION_SEC,"seconds")
        time.sleep(config.DOS_DURATION_SEC)
        p.send_signal(signal.SIGINT)
        p.terminate()
        print((" Terminating " + value).center(92, '~'))

    if value=="TCP Flood":
        print((" Starting " + value + " ").center(92, '~'))
        p=subprocess.Popen(["hping3","-S",config.DOS_DST_IP,"-p",config.DOS_DST_PORT,"--faster"])
        debug_print("hping3 -S " + config.DOS_DST_IP + " -p " + config.DOS_DST_PORT + " --faster")
        print(" Flood automatically terminates in",config.DOS_DURATION_SEC,"seconds")
        time.sleep(config.DOS_DURATION_SEC)
        p.send_signal(signal.SIGINT)
        p.terminate()
        print((" Terminating " + value).center(92, '~'))

    if value=="UDP Flood":
        print((" Starting " + value + " ").center(92, '~'))
        p=subprocess.Popen(["hping3","-2",config.DOS_DST_IP,"--faster"])
        debug_print("hping3 -2 " + config.DOS_DST_IP + " --faster")
        print(" Flood automatically terminates in",config.DOS_DURATION_SEC,"seconds")
        time.sleep(config.DOS_DURATION_SEC)
        p.send_signal(signal.SIGINT)
        p.terminate()
        print((" Terminating " + value).center(92, '~'))

    if value=="ICMP Flood":
        print((" Starting " + value + " ").center(92, '~'))
        for i in range(20,220):
            p=subprocess.Popen(["hping3","-1",config.DOS_DST_IP,"--fast","--icmp-ipsrc",config.DOS_SOURCE_ADDRESS],stdout=subprocess. DEVNULL,stderr=subprocess. DEVNULL)
        debug_print("hping3 -1 " + config.DOS_DST_IP + " --fast --icmp-ipsrc " + config.DOS_SOURCE_ADDRESS)    
        #print(" Flood automatically terminates within",config.DOS_DURATION_SEC,"seconds")
        #time.sleep(config.DOS_DURATION_SEC)
        p.send_signal(signal.SIGINT)
        p.terminate()
        q=subprocess.Popen(["killall","hping3"])
        print((" Terminating " + value).center(92, '~'))

    if value=="SCTP Flood":
        print((" Starting " + value + " ").center(92, '~'))
        p=subprocess.Popen(["hping3","-n",config.DOS_DST_IP,"-0","--ipproto","132","--flood","--destport","7654"])
        debug_print("hping3 -n " + config.DOS_DST_IP + " -0 --ipproto 132 --flood --destport 7654")
        print(" Flood automatically terminates in",config.DOS_DURATION_SEC,"seconds")
        time.sleep(config.DOS_DURATION_SEC)
        p.send_signal(signal.SIGINT)
        p.terminate()
        print((" Terminating " + value).center(92, '~'))

    if value=="Other-IP Flood":
        print((" Starting " + value + " ").center(92, '~'))
        p=subprocess.Popen(["hping3","-n",config.DOS_DST_IP,"-0","--ipproto","47","--flood","--destport","7654"])
        debug_print("hping3 -n " + config.DOS_DST_IP + " -0 --ipproto 47 --flood --destport 7654")
        print(" Flood automatically terminates in",config.DOS_DURATION_SEC,"seconds")
        time.sleep(config.DOS_DURATION_SEC)
        p.send_signal(signal.SIGINT)
        p.terminate()
        print((" Terminating " + value).center(92, '~'))

    if value=="ICMP Fragmention":
        print((" Starting " + value + " ").center(92, '~'))
        p=subprocess.Popen(["hping3",config.DOS_DST_IP,"-x","--icmp"],stdout=subprocess. DEVNULL,stderr=subprocess. DEVNULL)
        debug_print("hping3 " + config.DOS_DST_IP + "-x --icmp")
        print(" Traffic automatically terminates in",config.DOS_DURATION_SEC,"seconds")
        time.sleep(config.DOS_DURATION_SEC)
        p.send_signal(signal.SIGINT)
        p.terminate()
        print((" Terminating " + value).center(92, '~'))

    if value=="ICMP Ping Zero ID":
        print((" Starting " + value + " ").center(92, '~'))
        p=subprocess.Popen(["hping3","-1",config.DOS_DST_IP,"--icmp-ipid","0"],stdout=subprocess. DEVNULL,stderr=subprocess. DEVNULL)
        debug_print("hping3 -1" + config.DOS_DST_IP + "--icmp-ipid 0")
        print(" Traffic automatically terminates in",config.DOS_DURATION_SEC,"seconds")
        time.sleep(config.DOS_DURATION_SEC)
        p.send_signal(signal.SIGINT)
        p.terminate()
        print((" Terminating " + value).center(92, '~'))

    if value=="Non-SYN TCP":
        print((" Starting " + value + " ").center(92, '~'))
        p=subprocess.Popen(["hping3","-R",config.DOS_DST_IP],stdout=subprocess. DEVNULL,stderr=subprocess. DEVNULL)
        debug_print("hping3 -R" + config.DOS_DST_IP)
        print(" Traffic automatically terminates in",config.DOS_DURATION_SEC,"seconds")
        time.sleep(config.DOS_DURATION_SEC)
        p.send_signal(signal.SIGINT)
        p.terminate()
        print((" Terminating " + value).center(92, '~'))

    if value=="IP Spoofing":
        print((" Starting " + value + " ").center(92, '~'))
        p=subprocess.Popen(["hping3","-1",config.DOS_DST_IP,"-a",config.DOS_SOURCE_ADDRESS],stdout=subprocess. DEVNULL,stderr=subprocess. DEVNULL)
        debug_print("hping3 -1 " + config.DOS_DST_IP + " -a " + config.DOS_SOURCE_ADDRESS)
        print(" Traffic automatically terminates in",config.DOS_DURATION_SEC,"seconds")
        time.sleep(config.DOS_DURATION_SEC)
        p.send_signal(signal.SIGINT)
        p.terminate()
        print((" Terminating " + value).center(92, '~'))

    if value=="IP Fragmentation":
        print((" Starting " + value + " ").center(92, '~'))
        p=subprocess.Popen(["hping3","-S",config.DOS_DST_IP,"-f"],stdout=subprocess. DEVNULL,stderr=subprocess. DEVNULL)
        debug_print("hping3 -S" + config.DOS_DST_IP + "-f")
        print(" Traffic automatically terminates in",config.DOS_DURATION_SEC,"seconds")
        time.sleep(config.DOS_DURATION_SEC)
        p.send_signal(signal.SIGINT)
        p.terminate()
        print((" Terminating " + value).center(92, '~'))

    if value=="Record-Route":
        print((" Starting " + value + " ").center(92, '~'))
        p=subprocess.Popen(["hping3",config.DOS_DST_IP,"--rroute","--icmp"],stdout=subprocess. DEVNULL,stderr=subprocess. DEVNULL)
        debug_print("hping3 " + config.DOS_DST_IP + "--rroute --icmp")
        print(" Traffic automatically terminates in",config.DOS_DURATION_SEC,"seconds")
        time.sleep(config.DOS_DURATION_SEC)
        p.send_signal(signal.SIGINT)
        p.terminate()
        print((" Terminating " + value).center(92, '~'))

    if value=="Strict-SRC-Routing":
        print((" Starting " + value + " ").center(92, '~'))
        p=subprocess.Popen(["nping","--tcp",config.DOS_DST_IP,"--ip-options","S","--rate","100","-c","1000000"],stdout=subprocess. DEVNULL,stderr=subprocess. DEVNULL)
        debug_print("nping --tcp" + config.DOS_DST_IP + "--ip-options S --rate 100 -c 1000000")
        print(" Traffic automatically terminates in",config.DOS_DURATION_SEC,"seconds")
        time.sleep(config.DOS_DURATION_SEC)
        p.send_signal(signal.SIGINT)
        p.terminate()
        print((" Terminating " + value).center(92, '~'))

    if value=="Loose-SRC-Routing":
        print((" Starting " + value + " ").center(92, '~'))
        p=subprocess.Popen(["nping","--tcp",config.DOS_DST_IP,"--ip-options","L","--rate","100","-c","1000000"],stdout=subprocess. DEVNULL,stderr=subprocess. DEVNULL)
        debug_print("nping --tcp" + config.DOS_DST_IP + "--ip-options L --rate 100 -c 1000000")
        print(" Traffic automatically terminates in",config.DOS_DURATION_SEC,"seconds")
        time.sleep(config.DOS_DURATION_SEC)
        p.send_signal(signal.SIGINT)
        p.terminate()
        print((" Terminating " + value).center(92, '~'))

    if value=="Timestamp":
        print((" Starting " + value + " ").center(92, '~'))
        p=subprocess.Popen(["nping","--tcp",config.DOS_DST_IP,"--ip-options","T","--rate","100","-c","1000000"],stdout=subprocess. DEVNULL,stderr=subprocess. DEVNULL)
        debug_print("nping --tcp" + config.DOS_DST_IP + "--ip-options T --rate 100 -c 1000000")
        print(" Traffic automatically terminates in",config.DOS_DURATION_SEC,"seconds")
        time.sleep(config.DOS_DURATION_SEC)
        p.send_signal(signal.SIGINT)
        p.terminate()
        print((" Terminating " + value).center(92, '~'))


if __name__ == "__main__":

    # Initialize global variables
    data_meter = 0
    good_requests = 0
    bad_requests = 0
    loopcount = 0
    ALL_URLS = config.RULE_SPECIFIC_URLS + config.CATEGORY_URLS + config.REPUTATION_URLS +config.GENERAL_URLS
    working_url_list = ALL_URLS[:] #Creates a new working url list
    working_dos_traffic_profiles = config.DOS_TRAFFIC_PROFILES[:] #Creates a new dos traffic profiles list
    
    print(Colors.GREEN + "\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~" + Colors.NONE)
    print(Colors.GREEN + "Traffic generator started")
    print(Colors.GREEN + "This script will run indefinitely. Ctrl+C to stop." + Colors.NONE)
    print(Colors.GREEN + "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n" + Colors.NONE)
    print(Colors.BLUE + "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~" + Colors.NONE)
    print(Colors.BLUE + "Running Denial of Service (DOS) attacks once every {} URL requests.".format(config.CREATE_DOS_TRAFFIC_EVERY_X_TIMES) + Colors.NONE)
    print(Colors.BLUE + "Diving between 3 and {} links deep into {} root URLs,".format(config.MAX_DEPTH, len(ALL_URLS)) + Colors.NONE)
    print(Colors.BLUE + "Waiting between {} and {} seconds between requests. ".format(config.MIN_WAIT, config.MAX_WAIT) + Colors.NONE)
    print(Colors.BLUE + "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~" + Colors.NONE)
    
    while True:
        loopcount += 1
        debug_print("\nLoop Count: {}".format(loopcount),Colors.GREEN)
        if config.CREATE_DOS_TRAFFIC and ((loopcount % config.CREATE_DOS_TRAFFIC_EVERY_X_TIMES) == 0):            
            debug_print("\nRandomly selection one of {} DOS Traffic attacks".format(len(config.DOS_TRAFFIC_PROFILES)), Colors.RED)
            random.shuffle(working_dos_traffic_profiles)
            random_dos_traffic = working_dos_traffic_profiles.pop()
            if len(working_dos_traffic_profiles) == 0:
                working_dos_traffic_profiles = config.DOS_TRAFFIC_PROFILES[:] #Creates a new dos traffic profiles list
            DOS_creation(random_dos_traffic)
            
        debug_print("\nRandomly selecting one of {} Root URLs".format(len(ALL_URLS)), Colors.PURPLE)

        random.shuffle(working_url_list)
        random_url = working_url_list.pop()
        if len(working_url_list) == 0:
            working_url_list = ALL_URLS[:] #Creates a new working url list
    
        depth = random.choice(range(config.MIN_DEPTH, config.MAX_DEPTH))
    
        recursive_browse(random_url, depth)