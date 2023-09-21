MIN_DEPTH = 3  # minimum click depth
MAX_DEPTH = 10  # maximum click depth
MIN_WAIT = 20  # minimum amount of time allowed between HTTP requests
MAX_WAIT = 30  # maximum amount of time to wait between HTTP requests
DEBUG = True  # set to True to enable useful console output

#Denial of service settings
CREATE_DOS_TRAFFIC = True  # set to True to create DOS traffic
CREATE_DOS_TRAFFIC_EVERY_X_TIMES = 10 
DOS_DST_IP = ("192.168.1.1/24") # Enter Target/Destination IP Address with Subnet 192.168.1.1/24
DOS_DST_PORT = ("444") # Enter TCP Destination Port
DOS_DURATION_SEC = 30  # Enter time duration (in sec) for which traffic is to be generated
DOS_SOURCE_ADDRESS = ("192.168.0.1")  # Enter Source IP Address for spoofing traffic

# must use a valid user agent or sites will hate you
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"
)

# Use this single item list to test how a site responds to this crawler
# be sure to comment out the list below it.
# ROOT_URLS = ["https:///digg.com/"]

RULE_SPECIFIC_URLS = [ #URLs that match to a specific rule
    #Policies
        #TG-DNS-Allow (Allow) #Allows access to DNS. No specific URL
        #TG-LDAP-Allow (Allow) #Allows access to port 389 & 636
            "https://192.168.1.100:389",
            "https://192.168.1.100:636",
        #TG-Run-IP-Filter-Profile(Deny) (Please place these app/url into TG-Bad-Events Address Group)     
            "https://58.96.82.68",
            "https://103.240.252.59",
            "https://103.43.140.104",
            "https://103.48.139.139",
            "https://119.41.206.123",
            "https://15.204.168.1",
            "https://157.245.201.168",
            "https://163.123.143.173",
            "https://193.42.33.70",
            "https://2.56.58.81",
            "https://2.56.58.85",
            "https://2.56.58.88",
            "https://2.56.58.93",
            "https://210.140.43.55",
            "https://219.117.221.11",
            "https://223.73.35.54",
            "https://43.131.61.151",
            "https://43.134.111.101",
            "https://43.153.135.112",
            "https://43.163.198.174",
            "https://45.116.226.132",
            "https://45.116.226.134",
            "https://45.116.226.137",
            "https://45.116.226.138",
            "https://45.117.140.211",
            "https://94.205.22.95",
            "https://103.48.139.91",      
        #TG-Run-DNS-Filter-Profile (Block) (Please place these app/url into Security Polices rule TG-Run-DNS-Filter-Profile)
            "https://gitlab.com/",
            "https://www.deezer.com/us/",
        #TG-Run-AV-Profile (Recommended Action) (Please place these app/url into Security Polices rule TG-Run-AV-Profile)
            "https://www.eicar.org/download-anti-malware-testfile/",
            "https://secure.eicar.org/eicar_com.zip",
            "http://http-evader.semantic-gap.de/-BGJhmNoDFOy1TQD0tk0P96wLE-2pTBXgrg==",
        #TG-Run-File-Filter-Profile (Block) (Please place these app/url into Security Polices rule TG-Run-File-Filter-Profile)
            "https://github.com/nmmapper/python3-nmap/archive/refs/heads/master.zip",
            "https://github.com/nmmapper/python3-nmap/tree/0e3d16637ff2a3f8aa2e10ab7c4255685946e8c5/nmap3",
            "https://github.com/versa-networks/libcli/archive/refs/heads/stable.zip",
            "https://versanetworks.box.com/s/e8p1bxvil4xxbjdh8ardv7l5ame85n5c",
        #TG-Run-Vulnerability-Profile (Please place these app/url into Security Polices rule TG-Run-Vulnerability-Profile)
            "http://http-evader.semantic-gap.de/",
            "http://http-evader.semantic-gap.de/#xhr_eicar",
            "http://http-evader.semantic-gap.de/#xhr_novirus",
            "http://http-evader.semantic-gap.de/#js",
            "http://http-evader.semantic-gap.de/#js",
            "http://37.221.199.196",
            "http://http-evader.semantic-gap.de/-BGJhmNoDFOy1TQD0tk0P96wLE-2pTBXgrg==",
            "http://testmyids.com/",
        #TG-Run-ATP-Profile (Please place these app/url into Security Polices rule TG-Run-ATP-Profile)
            "https://secure.eicar.org/eicar.com.txt",
        #TG-Run-CASB-Profile (Please place these app/url into Security Polices rule TG-Run-CASB-Profile)
            "https://reddit.com/",
        #TG-Run-DLP-Profile (Please place these app/url into Security Polices rule TG-Run-DLP-Profile)
            
        #TG-QUIC (Deny) #Denies access to UDP on port 80 and 443
            "https://www.facebook.com",
            "https://www.google.com",
        #TG-Allow-Business-App-Filters (Allow) #Allows access to AWS, Facebook, Google-Earth
            "https://www.aws.amazon.com/",
            "https://www.facebook.com",
            "https://earth.google.com",
        #TG-Deny-Non-Business-App-Filters (Deny) #Denies access to Amazon-Apps, Social-Media, Facebook, Sharepoint_Online connection on 80 or 443
            #  Amazon-Apps
                "https://www.aws.amazon.com/console/",
                "https://app.chime.aws/meetings",
                "https://www.primevideo.com/",
                "https://music.amazon.in/",
            # Social-Media-Apps
                "https://www.facebook.com",
                "https://tinder.com",
                "http://www.orkut.com/",
            #Facebook_Video
            # Non-Business Apps
                "https://www.01net.com",
                "https://baidu.com",
                "https://www.bitlord.com",
                "https://www.cartoonnetwork.com",
        #TG-Deny-High-Risk-Apps
            # High Risk Apps
                "https://www.brightcove.com",
                "https://www.2shared.com/",
                "https://www.4tube.com/",
                "https://www.gigatribe.com/", ]

REPUTATION_URLS = [ # URLS of specific Reputation
    # Trustworthy (Allow)
        "https://cricbuzz.com",
    # Moderate risk (Alert)
        "https://adform.com",
    # Supicious (Block)
        "https://www.prochoiceamerica.org/",
    # High-Risk (Block)
        "http://www.proxify.com/",
        ]   

CATEGORY_URLS = [
    #Business applications
        "https://www.office.com/launch/powerpoint",
        "https://versanetworks.sharepoint.com/",
        "https://outlook.office.com/mail/inbox",
        "https://www.office.com/launch/excel",
        "https://teams.microsoft.com/",
        "https://www.mcafee.com/en-in/index.html",
        "https://www.webex.com/",
        "https://adobe.com",
    # Shopping URLS (Ask)
        "https://www.amazon.com",
        "https://www.flipkart.com",
        "https://www.myntra.com",
    # Social Media URLS (Justify)
        "https://www.facebook.com",
        "https://www.instagram.com",
        "https://www.twitter.com",
        "https://www.whatsapp.com",
        "https://telegram.org",
    # Job Search URLS (Allow)
        "https://www.linkedin.com",
        "https://www.naukri.com",
        "https://www.monster.com",
    # Google-Apps
        "https://www.gmail.com",
        "https://drive.google.com",
        "https://analytics.google.com/analytics/web/",
    # Web-Browsing
        "https://www.mail2000.co",
        "https://mail.ru/",
        "https://www.anz.com.au",
    # Auction URLs
        "https://www.ebay.com",
    # Dating URLs
        "https://www.match.com",
    # Gambling URLs
        "https://www.bet365.com",
    # Hacking URLs
    #Peer to Peer
    # Proxy avoid and anonymizers
        "https://www.kproxy.com",
    # Weapons URLs
        "https://www.grabagun.com",
    # Adult-sites
        "https://www.playboy.com",
    # Malware URLs
        "https://astalavista.box.sk",
]

GENERAL_URLS = [ # URLS to browse, may not match to specific rule
    "https://digg.com/",
    "https://www.yahoo.com",
    "https://www.reddit.com",
    "http://www.cnn.com",
    "http://www.ebay.com",
    "https://en.wikipedia.org/wiki/Main_Page",
    "https://austin.craigslist.org/",
    "https://www.flipkart.com",
    "https://www.facebook.com/games/",
    "https://www.whatsapp.com",
    "https://www.instagram.com",
    "https://www.bittorrent.com",
    "https://www.kproxy.com",
    "https://www.ndtv.com",
    "https://www.youtube.com",
    "https://www.netflix.com",
    "https://versanetworks.sharepoint.com/",
    "https://www.office.com/launch/powerpoint",
    "https://outlook.office.com/mail/inbox",
    "https://www.office.com/launch/excel",
    "https://teams.microsoft.com/",
    "https://groups.google.com/my-groups",
]
                

DOS_TRAFFIC_PROFILES = [
    # Comment out profile you do not want to run
    "TCP Scan",
    "UDP Scan",
    "HostSweep Flood",
    "TCP Flood",
    "UDP Flood",
    "ICMP Flood",
    "SCTP Flood",
    "Other-IP Flood",
    "ICMP Fragmention",
    "ICMP Ping Zero ID",
    "Non-SYN TCP",
    "IP Spoofing",
    "IP Fragmention",
    "Record-Route",
    "Strict-SRC-Routing",
    "Loose-SRC-Routing ",
    "Timestamp",
]

# List of items to not follow
# Items can be a URL "https://t.co" or simple string to check for "amazon"
IGNORE_LIST = [
    "https://t.co",
    "t.umblr.com",
    "messenger.com",
    "itunes.apple.com",
    "l.facebook.com",
    "bit.ly",
    "mediawiki",
    ".css",
    ".ico",
    ".xml",
    "intent/tweet",
    "twitter.com/share",
    "signup",
    "login",
    "dialog/feed?",
    ".png",
    ".jpg",
    ".json",
    ".svg",
    ".gif",
    "zendesk",
    "clickserve",
]