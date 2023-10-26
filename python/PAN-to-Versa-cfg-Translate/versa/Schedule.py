#! /usr/bin/python
#  Schedule.py - Versa Schedule definition
#
#  This file has the definition of a network address object, that can be used
#  in any policy configuration on the Versa FlexVNF.
#
#  Copyright (c) 2017, Versa Networks, Inc.
#  All rights reserved.
#
#  pylint: disable=invalid-name

from enum import Enum
from versa.ConfigObject import ConfigObject


class ScheduleObjectType(Enum):
    RECURRING = 1
    NON_RECURRING = 2


class Schedule(ConfigObject):
    """Schedule _summary_

    Args:
        ConfigObject (_type_): _description_
    """

    def __init__(self, _name, _name_src_line, _is_predefined, _is_recurring):
        super().__init__(_name, _name_src_line, _is_predefined)
        if _is_recurring:
            self.schedule_type = ScheduleObjectType.RECURRING
        else:
            self.schedule_type = ScheduleObjectType.NON_RECURRING
        self.non_recur_days_times = []
        self.recur_map = {}

    def add_non_recurring_day_time(self, _day_time, _day_time_src_line):
        self.non_recur_days_times.append([_day_time, _day_time_src_line])

    def add_recurring_day_time(self, _recur_day, _recur_time, _recur_day_time_src_line):
        if _recur_day in self.recur_map:
            self.recur_map[_recur_day].append([_recur_time, _recur_day_time_src_line])
        else:
            self.recur_map[_recur_day] = [[_recur_time, _recur_day_time_src_line]]

    def set_recurring_map(self, _recur_map, _recur_map_src_line):
        self.recur_map = _recur_map
        self.recur_map_src_line = _recur_map_src_line

    def listsAreEqual(self, a, b):
        """listsAreEqual _summary_

        Args:
            a (_type_): _description_
            b (_type_): _description_

        Returns:
            _type_: _description_
        """
        for x in a:
            if x not in b:
                return False
        for x in b:
            if x not in a:
                return False
        return True

    def equals(self, _other):
        """equals _summary_

        Args:
            _other (_type_): _description_

        Returns:
            _type_: _description_
        """
        if self.schedule_type != _other.schedule_type:
            return False
        if self.schedule_type == ScheduleObjectType.RECURRING:
            if not self.listsAreEqual(list(self.recur_map.keys()), list(_other.recur_map.keys())):
                return False
            # XXX-TODO: compare the time stamps of the recurring days
        elif self.schedule_type == ScheduleObjectType.NON_RECURRING:
            if not self.listsAreEqual(self.non_recur_days_times, _other.non_recur_days_times):
                return False
        return True

    def write_config(self, output_vd_cfg, _cfg_fh, _log_fh, _indent):
        """write_config _summary_

        Args:
            output_vd_cfg (_type_): _description_
            _cfg_fh (_type_): _description_
            _log_fh (_type_): _description_
            _indent (_type_): _description_
        """
        if output_vd_cfg:
            vd_str = "schedule "
        else:
            vd_str = ""
        print(f"{_indent}        {vd_str}{self.name} {{", file=_cfg_fh)
        if self.schedule_type == ScheduleObjectType.NON_RECURRING:
            if len(self.non_recur_days_times) > 0:
                print(f"{_indent}            non-recurring ", end="", file=_cfg_fh)
                first = True
                for [nrtime, nrdt_src_line] in self.non_recur_days_times:
                    if first:
                        first = False
                    else:
                        print(",", end="", file=_cfg_fh)
                    print(f"{nrtime}", end="", file=_cfg_fh)
                print(";", file=_cfg_fh)
        elif self.schedule_type == ScheduleObjectType.RECURRING:
            if len(self.recur_map) > 0:
                for rday, rtimes in self.recur_map.items():
                    print(f"{_indent}            recurring {rday} {{", file=_cfg_fh)

                    print(f"{_indent}                # src lines: ", end="", file=_cfg_fh)
                    for [rtime, rdt_src_line] in rtimes:
                        print(f"{rdt_src_line} ", end="", file=_cfg_fh)
                    print("", file=_cfg_fh)

                    if len(rtimes) > 0:
                        first = True
                        write_sc = False
                        for [rtime, rdt_src_line] in rtimes:
                            if len(rtime) == 0:
                                continue
                            write_sc = True
                            if first:
                                print(
                                    f"{_indent}                time-of-day ",
                                    end="",
                                    file=_cfg_fh,
                                )
                                first = False
                            else:
                                print(",", end="", file=_cfg_fh)
                            print(f"{rtime}", end="", file=_cfg_fh)
                        if write_sc:
                            print(";", file=_cfg_fh)

                    print(f"{_indent}            }}", file=_cfg_fh)

        print(f"{_indent}        }}", file=_cfg_fh)
