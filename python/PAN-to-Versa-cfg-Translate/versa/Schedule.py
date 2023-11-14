#! /usr/bin/python
#  Schedule.py - Versa Schedule definition
#
#  This file has the definition of a network address object, that can be used
#  in any policy configuration on the Versa FlexVNF.
#
#  Copyright (c) 2023, Versa Networks, Inc.
#  All rights reserved.
#

from enum import Enum
from versa.ConfigObject import ConfigObject


class ScheduleObjectType(Enum):
    RECURRING = 1
    NON_RECURRING = 2


class Schedule(ConfigObject):
    """
    Represents a schedule in the configuration.

    This class inherits from ConfigObject and adds additional attributes specific to schedules.

    Args:
        ConfigObject (class): The base class for configuration objects. It provides common attributes for all configuration objects, such as name, source line, and predefined flag.
    """

    def __init__(self, _name, _name_src_line, _is_predefined, _is_recurring):
        """
        Initializes a new instance of the Schedule class.

        Args:
            _name (str): The name of the schedule.
            _name_src_line (int): The source line where the name is defined.
            _is_predefined (bool): A flag indicating whether the schedule is predefined.
            _is_recurring (bool): A flag indicating whether the schedule is recurring.
        """
        super().__init__(_name, _name_src_line, _is_predefined)
        self.schedule_type = ScheduleObjectType.RECURRING if _is_recurring else ScheduleObjectType.NON_RECURRING
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

    def listsAreEqual(self, a, b) -> bool:
        """
        Checks if two lists are equal.

        This method checks if two lists are equal by comparing if each element of one list is present in the other.

        Args:
            a (List[Any]): The first list to compare.
            b (List[Any]): The second list to compare.

        Returns:
            bool: True if the lists are equal, False otherwise.
        """
        for x in a:
            if x not in b:
                return False
        for x in b:
            if x not in a:
                return False
        return True

    def equals(self, _other: "Schedule") -> bool:
        """
        Checks if the current instance is equal to another instance of the Schedule class.

        This method checks if the current instance is equal to another instance by comparing their schedule types and the keys of their recurring maps or their non-recurring days and times.

        Args:
            _other (Schedule): The other instance to compare with.

        Returns:
            bool: True if the instances are equal, False otherwise.
        """
        if self.schedule_type != _other.schedule_type:
            return False
        if self.schedule_type == ScheduleObjectType.RECURRING:
            if not self.listsAreEqual(self.recur_map.keys(), _other.recur_map.keys()):
                return False
            # XXX-TODO: compare the time stamps of the recurring days
        elif self.schedule_type == ScheduleObjectType.NON_RECURRING:
            if not self.listsAreEqual(self.non_recur_days_times, _other.non_recur_days_times):
                return False
        return True

    def write_config(self, output_vd_cfg, _cfg_fh, _indent):
        """
        Writes the configuration of the schedule to a file.

        This method writes the configuration of the schedule to a file. The configuration is indented by a specified amount and may include a "schedule" prefix depending on the value of `output_vd_cfg`.

        Args:
            output_vd_cfg (bool): If True, a "schedule" prefix is included in the output.
            _cfg_fh (TextIO): The file handle to write the configuration to.
            _indent (str): The string to use for indentation.

        """
        vd_str = "schedule " if output_vd_cfg else ""
        output = [f"{_indent}{vd_str}{self.name} {{"]

        if self.schedule_type == ScheduleObjectType.NON_RECURRING and self.non_recur_days_times:
            non_recur_times = ",".join(nrtime for nrtime, _ in self.non_recur_days_times)
            output.append(f"{_indent}    non-recurring {non_recur_times};")

        elif self.schedule_type == ScheduleObjectType.RECURRING and self.recur_map:
            for rday, rtimes in self.recur_map.items():
                output.append(f"{_indent}    recurring {rday} {{")
                output.extend(f"{_indent}    {rdt_src_line}" for rtime, rdt_src_line in rtimes if rtime)

                if rtimes:
                    times_of_day = ",".join(rtime for rtime, _ in rtimes if rtime)
                    output.append(f"{_indent}    time-of-day {times_of_day};")

                output.append(f"{_indent}    }}")

        output.append(f"{_indent}}}")

        print('\n'.join(output), file=_cfg_fh)