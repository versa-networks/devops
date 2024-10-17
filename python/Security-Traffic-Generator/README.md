# Security-Traffic-Generator

## Purpose

A traffic generator that creates "organic" traffic with specific traffic that triggers the included Versa Networks NGFW rules. In addition, the tool creates quick simulations of respective Zone-Protection and DOS "attacks." This can be used during the following scenarios:

```Demos
Log creation for demos
Security testing for NGFW, Zone Protection, and DoS Protection
Quick Functional testing on new releases
```

The tool tries to cover all possible scenarios to demonstrate NGFW, Zone-Protection, & DoS-related tests using Python. There will also be a Service Template, which can be cloned/exported to any environment for re-usability.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

Linux (Tested on Ubuntu 22.04)
Python3 with modules
  requests, re, time, random, subprocess, signal, http.client (You should have all of these)

hping3 – sudo apt install hping
nmap – sudo apt install nmap

### Installing

#### Configuration

All configuration takes place in config.py and are very simple

##### Settings

- `MIN_DEPTH = 3`, `MAX_DEPTH = 10`,  Starting from each root URL (i.e.: <www.yahoo.com>), our generator will click to a depth randomly selected between MIN_DEPTH and MAX_DEPTH.

The interval between every HTTP GET requests is chosen at random between the following two variables...

- `MIN_WAIT = 20` Wait a minimum of `20` seconds between requests... Be careful with making requests too quickly, as that tends to piss off web servers.
- `MAX_WAIT = 30` I think you get the point.

- `DEBUG = True` A poor man's logger. Set to `True` for verbose real-time printing to the console for debugging or development. I'll incorporate proper logging later on (maybe).

Denial of service settings

- `CREATE_DOS_TRAFFIC = True`  Set to True to create DOS traffic
- `CREATE_DOS_TRAFFIC_EVERY_X_TIMES = 10` How often to create DOS traffic
- `DOS_DST_IP = ("192.168.1.1/24")` Enter Target/Destination IP Address with Subnet 192.168.1.1/24
- `DOS_DST_PORT = ("444")` Enter TCP Destination Port
- `DOS_DURATION_SEC = 30`  Enter the time duration (in seconds) for which traffic is to be generated
- `DOS_SOURCE_ADDRESS = ("192.168.0.1")`  Enter Source IP Address for spoofing traffic

User Agent

- `userAgent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3).......'` The user-agent of our headless browser hands over to the web server. You can leave it set to the default, but feel free to change it. I would strongly suggest using a common/valid one, or else you'll likely get rate-limited quickly.

URLS

All URL lists will be randomly combined into a single list. The script will work through this single list until all URLs have been attempted then, the lists above will be randomly combined into a new single list. You can comment out any URLs you do not want to use

- `RULE_SPECIFIC_URLS = [url1,url2,url3]` The list of rule URLs under comments for which NGFW rule it should trigger
- `REPUTATION_URLS = [url1,url2,url3]` The list of URLs that fall into a specific reputation.
- `CATEGORY_URLS = [url1,url2,url3]` The list of  URLs that fall into a specific category.
- `GENERAL_URLS = [url1,url2,url3]` The list of root URLs to start from when browsing.

DOS Traffic Profiles

- `DOS_TRAFFIC_PROFILES = [Simulated attack type 1, Simulated attack type 2]` A list of simulated attack types. Comment out any you do not want to test.

Blacklists of items

- `blacklist = [".gif", "intent/tweet", "badlink", etc...]` A blacklist of strings that we check every link against. If the link contains any of the strings in this list, it's discarded. Useful to avoid things that are not traffic-generator friendly, like "Tweet this!" links or links to image files.

#### Traffic & Attack generator system

1. Install the prerequisites
2. Copy config.py and Traffic_Generator.py to a directory on the generator system

#### Importing Traffic-Generator-NFGW.cfg as a service template into a tenant

How to use

1. Edit config.py and replace \<Org Name\> with the org name you are trying this in.
2. Create a service template in the org called Traffic-Generator-NGFW
3. Import the Traffic-Generator-NGFW.cfg into the service template.
4. Assign the Service Template to the Device Group you want to test this on and commit the template
5. The config file includes a Zone Protection Profile called TG-ZP-Profile.  This will need to be assigned to the zone from which the attacks are coming.

## Execution

On the Traffic & Attack Generator System, run the following command:
`sudo python3 Traffic_Generator.py`

## Versioning

For the versions available, see the [tags on this repository](https://github.com/your/project/tags)

## Authors

Written by Rob Kauffman and borrowed heavliy from scripts mentioned in acknowledgments

## License

This project is licensed under the MIT License.

## Acknowledgments

Big thanks to

[Web Traffic Generator](https://github.com/ecapuano/web-traffic-generator) by @eric_capuano

[Traffic Generation for App-ID-URL-Categories-Reputations](https://github.com/versa-networks/devops/tree/master/python/Security%20Automation%20-%20Traffic%20Generation%20for%20App-ID-URL-Categories-Reputations) by Swetha Ragunath

[Security Automation Script to Generate Zone-DoS Traffic Validation](https://github.com/versa-networks/devops/tree/7f68a474f55febea49ff6612fdae45db32bed76e/python/Security%20Automation%20Script%20to%20Generate%20Zone-DoS%20Traffic%20Validation) by Swetha Ragunath
