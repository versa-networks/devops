#!/usr/bin/python
#  NextGenFirewall.py - Versa Next Gen Firewall definition
#
#  This file has the definition of the Next Generation Firewall.
#
#  Copyright (c) 2023, Versa Networks, Inc.
#  All rights reserved.


from versa.Firewall import Firewall
from versa.NetworkFunction import NetworkFunctionType


class NextGenFirewall(Firewall):
    """
    This class represents a Next Generation Firewall. It inherits from the Firewall class
    and sets the network function type to NEXT_GEN_FIREWALL.
    """

    def __init__(self, _name: str, _is_predefined: bool):
        super().__init__(_name, _is_predefined)
        self.vnf_type = NetworkFunctionType.NEXT_GEN_FIREWALL
