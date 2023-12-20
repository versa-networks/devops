"""
Configuration file for the web crawler.

This file contains various settings and lists of URLs for the web crawler to use.

Settings include:
- MIN_DEPTH: Minimum click depth.
- MAX_DEPTH: Maximum click depth.
- MIN_WAIT: Minimum amount of time allowed between HTTP requests.
- MAX_WAIT: Maximum amount of time to wait between HTTP requests.
- CREATE_DOS_TRAFFIC: Whether to create Denial of Service (DoS) traffic.
- CREATE_DOS_TRAFFIC_EVERY_X_TIMES: Frequency of DoS traffic creation.
- DOS_DST_IP: Target IP address for DoS traffic.
- DOS_DST_PORT: Target port for DoS traffic.
- DOS_DURATION_SEC: Duration for which traffic is to be generated.
- DOS_SOURCE_ADDRESS: Source IP address for spoofing traffic.
- USER_AGENT: User agent string to use for HTTP requests.
- URLS_FILE_NAME: File name for list of URLs to crawl.

"""
MIN_DEPTH = 3  # minimum click depth
MAX_DEPTH = 10  # maximum click depth
MIN_WAIT = 20  # minimum amount of time allowed between HTTP requests
MAX_WAIT = 30  # maximum amount of time to wait between HTTP requests

#Denial of service settings
CREATE_DOS_TRAFFIC = True  # set to True to create DOS traffic
CREATE_DOS_TRAFFIC_EVERY_X_TIMES = 10
DOS_DST_IP = "192.168.1.1/24" # Enter Target/Destination IP Address with Subnet 192.168.1.1/24
DOS_DST_PORT = "444" # Enter TCP Destination Port
DOS_DURATION_SEC = 30  # Enter time duration (in sec) for which traffic is to be generated
DOS_SOURCE_ADDRESS = "192.168.0.1"  # Enter Source IP Address for spoofing traffic

# must use a valid user agent or sites will hate you
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"
)

URLS_FILE_NAME = "./python/Security-Traffic-Generator/URLS.xml"  # file name for list of URLs to crawl
