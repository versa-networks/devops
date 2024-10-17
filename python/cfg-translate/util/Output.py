#
#  VersaConfig.py - Versa Config definition
# 
#  This file has the definition of full Versa configuration.
# 
#  Copyright (c) 2017, Versa Networks, Inc.
#  All rights reserved.
#

from __future__ import print_function


out_line = 1
src_line_map = { }

def print_output(_src_line_ranges, _indent, _cfg_line, _out_fh):

    cur_out_start_line = out_line

    print('%s# src lines: ' % ( _indent ), end='', file=_out_fh)
    for sl in _src_line_ranges:
        print(' %s' % ( sl ), end='', file=_out_fh)
    print('', file=_out_fh)

    print('%s%s' % ( _indent, _cfg_line ), file=_out_fh)
    out_line = out_line + 3



def print_annotation(_anno_fh):
    print('  {', file=_anno_fh)
    print('    %s: "%s"' % ( _indent, _cfg_line ), file=_anno_fh)
    print('  }', file=_anno_fh)



