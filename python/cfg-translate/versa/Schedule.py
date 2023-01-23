#
#  Schedule.py - Versa Schedule definition
# 
#  This file has the definition of a network address object, that can be used
#  in any policy configuration on the Versa FlexVNF.
# 
#  Copyright (c) 2017, Versa Networks, Inc.
#  All rights reserved.
#

from __future__ import print_function
from versa.ConfigObject import ConfigObject
from enum import Enum


class ScheduleObjectType(Enum):
    RECURRING = 1
    NON_RECURRING = 2

class Schedule(ConfigObject):

    def __init__(self, _name, _name_src_line, _is_predefined, _is_recurring):
        super(Schedule, self).__init__(
                                  _name, _name_src_line, _is_predefined)
        if (_is_recurring):
            self.schedule_type = ScheduleObjectType.RECURRING
        else:
            self.schedule_type = ScheduleObjectType.NON_RECURRING
        self.non_recur_days_times = [ ]
        self.recur_map = { }


    def add_non_recurring_day_time(self, _day_time, _day_time_src_line):
        self.non_recur_days_times.append( \
                            [ _day_time, _day_time_src_line ] )


    def add_recurring_day_time(self, _recur_day,
                               _recur_time, _recur_day_time_src_line):
        if (_recur_day in self.recur_map):
            self.recur_map[_recur_day].append( \
                                [_recur_time, _recur_day_time_src_line ] )
        else:
            self.recur_map[_recur_day] = \
                                [ [_recur_time, _recur_day_time_src_line ] ]

    def set_recurring_map(self, _recur_map, _recur_map_src_line):
        self.recur_map = _recur_map
        self.recur_map_src_line = _recur_map_src_line

    def listsAreEqual(self, a, b):
        for x in a:
            if x not in b:
                return False
        for x in b:
            if x not in a:
                return False
        return True

    def equals(self, _other):
        if (self.schedule_type != _other.schedule_type):
            return False
        if (self.schedule_type == ScheduleObjectType.RECURRING):
            if (not self.listsAreEqual(self.recur_map.keys(),
                                       _other.recur_map.keys())):
                return False
            # XXX-TODO: compare the time stamps of the recurring days
        elif (self.schedule_type == ScheduleObjectType.NON_RECURRING):
            if (not self.listsAreEqual(self.non_recur_days_times,
                                       _other.non_recur_days_times)):
                return False
        return True

    def write_config(self, output_vd_cfg, _cfg_fh, _log_fh, _indent):
        if (output_vd_cfg):
            vd_str = 'schedule '
        else:
            vd_str = ''
        print('%s        %s%s {' % ( _indent, vd_str, self.name ), file=_cfg_fh)
        if (self.schedule_type == ScheduleObjectType.NON_RECURRING):
            if (len(self.non_recur_days_times) > 0):
                print('%s            non-recurring ' %
                      ( _indent ), end='', file=_cfg_fh)
                first = True
                for [nrtime, nrdt_src_line] in self.non_recur_days_times:
                    if (first):
                        first = False
                    else:
                        print(',', end='', file=_cfg_fh)
                    print('%s' % nrtime, end='', file=_cfg_fh)
                print(';', file=_cfg_fh)
        elif (self.schedule_type == ScheduleObjectType.RECURRING):
            if (len(self.recur_map) > 0):
                for rday, rtimes in self.recur_map.iteritems():
                    print('%s            recurring %s {' % ( _indent, rday ),
                          file=_cfg_fh)

                    print('%s                # src lines: ' % ( _indent ),
                          end='', file=_cfg_fh)
                    for [rtime, rdt_src_line] in rtimes:
                        print('%s ' % rdt_src_line, end='', file=_cfg_fh)
                    print('', file=_cfg_fh)

                    if (len(rtimes) > 0):
                        first = True
                        write_sc = False
                        for [rtime, rdt_src_line] in rtimes:
                            if (len(rtime) == 0):
                                continue
                            write_sc = True
                            if (first):
                                print('%s                time-of-day ' % ( _indent),
                                      end='', file=_cfg_fh)
                                first = False
                            else:
                                print(',', end='', file=_cfg_fh)
                            print('%s' % rtime, end='', file=_cfg_fh)
                        if (write_sc):
                            print(';', file=_cfg_fh)

                    print('%s            }' % ( _indent ),
                          file=_cfg_fh)

        print('%s        }' % ( _indent ), file=_cfg_fh)




