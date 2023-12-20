"""
This module defines data classes for representing schedules.

Classes:
    TimeOfDay: Represents a specific time of day.
    Recurring: Represents a recurring schedule.
    Schedule: Represents a schedule with non-recurring and recurring parts.
"""
from dataclasses import dataclass
import re
from typing import List
import constants as CONSTANT

VALID_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


@dataclass
class TimeOfDay:
    """
    Represents a specific time of day.

    Attributes:
        start_time (str): The start time in the format 'HH:MM'.
        end_time (str): The end time in the format 'HH:MM'.
    """

    start_time: str
    end_time: str

    def __post_init__(self):
        if not re.match(CONSTANT.TIME_PATTERN, self.start_time):
            raise ValueError(f"Invalid start time: {self.start_time}. Time must be in the format HH:MM (24-hour format).")
        if not re.match(CONSTANT.TIME_PATTERN, self.end_time):
            raise ValueError(f"Invalid end time: {self.end_time}. Time must be in the format HH:MM (24-hour format).")


@dataclass
class Recurring:
    """
    Represents a recurring schedule.

    Attributes:
        day (str): The day of the week.
        time_of_day (TimeOfDay): The time of day.
    """

    day: str  # Must be monday, tuesday, wednesday, thursday, friday, saturday, or sunday
    time_of_day: TimeOfDay

    def __post_init__(self):
        if self.day.lower() not in VALID_DAYS:
            raise ValueError(f"Invalid day: {self.day}. Day must be one of {VALID_DAYS}.")


@dataclass
class Schedule:
    """
    Represents a schedule with non-recurring and recurring parts.

    Attributes:
        name (str): The name of the schedule.
        description (str): The description of the schedule.
        tag (List[str]): The tags associated with the schedule.
        non_recurring (List[str]): The non-recurring parts of the schedule.
        recurring (List[Recurring]): The recurring parts of the schedule.
    """

    name: str
    description: str
    tag: List[str]
    non_recurring: List[str]
    recurring: List[Recurring]


"""
examples

schedule Schedule-Non-Recurring {
    description   Desc;
    tag           [ Tag ];
    non-recurring 2023/11/30@00:15-2023/12/09@03:00,2023/12/01@00:00-2024/01/03@03:00;
}
schedule Schedule-Recuring-Daily {
    description Desc;
    tag         [ Tag ];
    recurring daily {
        time-of-day 00:00-00:15;
    }
}
schedule Schedule-Recuring-Weekly {
    description Desc;
    tag         [ Tag ];
    recurring monday {
        time-of-day 00:00-00:00;
    }
    recurring tuesday {
        time-of-day 00:00-01:00;
    }
    recurring wednesday {
        time-of-day 03:15-00:00;
    }
    recurring thursday {
        time-of-day 00:00-02:00;
    }
    recurring friday {
        time-of-day 02:15-00:00;
    }
    recurring saturday {
        time-of-day 00:00-03:15;
    }
    recurring sunday {
        time-of-day 00:00-14:45;
    }
}    
"""
