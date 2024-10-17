#
#  ConfigObject.py - Versa ConfigObject definition
# 
#  This file has the definition of any configuration, that is supported
#  by the Versa FlexVNF.
# 
#  Copyright (c) 2017, Versa Networks, Inc.
#  All rights reserved.
#

from enum import Enum



class ConfigObjectType(Enum):
    PRE_DEFINED = 1
    USER_DEFINED = 2

class ConfigObject(object):

    def __init__(self, _name, _name_src_line, _is_predefined):
        self.name = _name
        self.name_src_line = _name_src_line
        if (_is_predefined):
            self.obj_type = ConfigObjectType.PRE_DEFINED
        else:
            self.obj_type = ConfigObjectType.USER_DEFINED

    def is_predefined(self):
        return self.obj_type == ConfigObjectType.PRE_DEFINED

    def get_name(self):
        return self.name

    def set_name(self, _name, _name_src_line):
        self.name = _name
        self.name_src_line = _name_src_line

    def set_desc(self, _desc, _desc_src_line):
        self.desc = _desc
        self.desc_src_line = _desc_src_line



