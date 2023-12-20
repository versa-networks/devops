"""
This module defines constants for validating input.
"""

NAME_MAX_LENGTH = 31
"""int: The maximum length of a name."""

NAME_VALID_REGEX = r"^[a-zA-Z0-9_-]+$"
"""str: The regex pattern that a valid name must match. Only alphanumeric, hyphen, and underscore are allowed."""

DESC_MAX_LENGTH = 127
"""int: The maximum length of a description."""

DESC_VALID_REGEX = r"^[a-zA-Z0-9_-\s]+$"
"""str: The regex pattern that a valid description must match. Only alphanumeric, hyphen, underscore, and space are allowed."""

VLAN_ID_MIN_VALUE = 1
"""int: The minimum VLAN ID."""

VLAN_ID_MAX_VALUE = 4094
"""int: The maximum VLAN ID."""

TIME_PATTERN = r"^([01]\d|2[0-3]):([0-5]\d)$"
"""str: The regex pattern that a valid HH:MM (24-hour format) must match."""

MAC_ADDRESS_VALID_REGEX = r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
"""str: The regex pattern that a valid MAC address must match."""

MAC_ADDRESS_WILDCARD_MASKVALID_REGEX = r"^([0Ff]{2}[:-]){5}([0Ff]{2})$"
"""str: The regex pattern that a valid MAC address with wildcard mask must match."""

IPV4_ADDR_CIDR_REGEX = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/([0-9]|[1-2][0-9]|3[0-2])$"
"""str: A regular expression that matches an IPv4 address with any CIDR from /0 to /32. """

IPV4_ADDR_WILDCARD_MASK = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
"""
str: A regular expression that matches an IPv4 address followed by a '/' and another valid IPv4 address which represents the wildcard mask.

The bits in the mask can be on (1) or off (0). Only the bits that are enabled in the mask are used to determine whether an IPv4 address matches. When a bit in a wildcard mask is on, that bit must match. 
When a bit in a wildcard mask is off, it is considered as a "don't care" bit and is disregarded for purposes of address matching. 
For example, the IPv4 address and mask 192.168.3.100/255.255.3.255 matches any IPv4 address 192.168.x.100, where, for x, the first 6 bits can be on (1) or off (0) and the last two bits must be on (11). 
Note that in a wildcard mask, at least one bit must be on."""

IPV4_ADDR_RANGE = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}-(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
"""str: A regular expression that matches an IPv4 address range. """

FQDN_REGEX = r"^(?=.{1,253}\.$)((?!-)[A-Za-z0-9-]{1,63}(?<!-)\.)+[A-Za-z]{2,63}\.$"
"""
str: 

Evaluate the address match using an IP address returned in a DNS query that resolves the fully qualified domain name (FQDN) into an IP address. The FQDN cannot contain any wildcard characters.
Ensure that you also configure a routing instance through which the DNS server is reachable so that the VOS device can resolve the FQDN.
"""

IPV6_ADDR_REGEX = r"^(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}$"
"""
A regular expression that matches a valid IPv6 address.
Each part can consist of one to four hexadecimal digits.
"""

IPV6_ADDR_WILDCARD_MASK = r"^(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}\/(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}$"
"""
A regular expression that matches an IPv6 address followed by a '/' and another valid IPv6 address which represents the wildcard mask.
Each part can consist of one to four hexadecimal digits.
"""

APPLICATION_PRODUCTIVITY_SCORES = [1, 2, 3, 4, 5]
""" List: Predefined productivity scores with 5 being most productive and 1 being least productive."""

APPLICATION_RISK_SCORES = [1, 2, 3, 4, 5]
""" List: Predefined risk scores with 5 being most risky and 1 being least risky."""

APPLICATION_TIMEOUTS = {"low": 1, "high": 15999999}
""" List: Predefined application timeouts with 15999999 being the maximum timeout value and 1 being the miniumum."""

APPLICATION_PRECEDENCE = {"low": 0, "high": 65535}

APPLICATION_FAMILY_NAMES = ["Business-system", "Collaboration", "General-internet", "Media", "Networking"]
""" List: Predefined application family names. These are broad categories that applications can fall under."""

APPLICATION_SUBFAMILY_NAMES = ["antivirus","application-service","audio_video","authentication","behavioral","compression","database","encrypted",
                               "encrypted-tunnel","erp","file-server","file-transfer","forum","game","instant-messaging","internet-utility","mail",
                               "microsoft-office","middleware","network-management","network-service","peer-to-peer","printer","routing","security-service",
                               "standard","telephony","terminal","thin-client","tunneling","unknown","wap","web","webmail",]
""" List: Predefined application subfamily names. These are more specific categories that applications can fall under, within their broader family."""

APPLICATION_TAGS = ["aaa", "adult_content", "advertising", "analytics", "anonymizer", "audio_chat", "basic", "blog", "cdn", "chat", "classified_ads", "cloud_services",
                    "db", "dea_mail", "ebook_reader", "email", "enterprise", "file_mngt", "file_transfer", "forum", "gaming", "im_mc", "iot", "mm_streaming", "mobile",
                    "networking", "news_portal", "p2p", "remote_access", "scada", "social_network", "standardized", "transportation", "update", "video_chat", "voip",
                    "vpn_tun", "web", "web_ecom", "web_search", "web_sites", "webmail", "v_audio_stream", "v_av", "v_business", "v_cloud", "v_data", "v_ips",
                    "v_non_business", "v_video_stream", "vs_anonymizer", "vs_bandwidth", "vs_dataleak", "vs_evasive", "vs_filetransfer", "vs_malware", "vs_misused",
                    "vs_tunnel", "vs_vulnerable"]
""" List: Predefined application tags. These are additional descriptors that can be associated with an application."""
