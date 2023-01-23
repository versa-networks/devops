#
#  NetworkFunction.py - Versa Network Function definition
# 
#  This file has the definition of any configuration of a Network
#  Function (VNF or PNF), that is supported by the Versa FlexVNF.
# 
#  Copyright (c) 2017, Versa Networks, Inc.
#  All rights reserved.
#

from versa.ConfigObject import ConfigObject
from enum import Enum



class NetworkFunctionType(Enum):
    SDWAN = 1
    NAT = 2
    STATEFUL_FIREWALL = 3
    NEXT_GEN_FIREWALL = 4


class NetworkFunction(ConfigObject):

    def __init__(self, _name, _name_src_line, _is_predefined, _vnf_type):
        super(NetworkFunction, self).__init__(_name,
                                              _name_src_line, _is_predefined)
        self.vnf_type = _vnf_type




