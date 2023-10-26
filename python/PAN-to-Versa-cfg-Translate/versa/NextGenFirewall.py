#!/usr/bin/python
#  NextGenFirewall.py - Versa Next Gen Firewall definition
#
#  This file has the definition of the Next Generation Firewall.
#
#  Copyright (c) 2017, Versa Networks, Inc.
#  All rights reserved.
# pylint: disable=invalid-name


from versa.Firewall import Firewall
from versa.NetworkFunction import NetworkFunctionType


class NextGenFirewall(Firewall):
    """NextGenFirewall
    This file has the definition of the Next Generation Firewall.

    Args:
        Firewall (_type_): _description_
    """

    def __init__(self, _name, _name_src_line, _is_predefined):
        super().__init__(_name, _name_src_line, _is_predefined)
        self.vnf_type = NetworkFunctionType.NEXT_GEN_FIREWALL
