#!/usr/bin/python
#  NetworkFunction.py - Versa Network Function definition
#
#  This file has the definition of any configuration of a Network
#  Function (VNF or PNF), that is supported by the Versa FlexVNF.
#
#  Copyright (c) 2023, Versa Networks, Inc.
#  All rights reserved.

from enum import Enum
from versa.ConfigObject import ConfigObject


class NetworkFunctionType(Enum):
    SDWAN = 1
    NAT = 2
    STATEFUL_FIREWALL = 3
    NEXT_GEN_FIREWALL = 4


class NetworkFunction(ConfigObject):
    """
    This class represents a Network Function. It inherits from the ConfigObject class
    and sets the network function type.
    """

    def __init__(self, name: str, name_src_line: int, is_predefined: bool, vnf_type: NetworkFunctionType):
        super().__init__(name, name_src_line, is_predefined)
        self.vnf_type = vnf_type
