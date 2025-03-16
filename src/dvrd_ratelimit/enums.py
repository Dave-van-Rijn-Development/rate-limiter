from enum import IntEnum


class Duration(IntEnum):
    # Durations in seconds
    SECOND = 1
    MINUTE = SECOND * 60
    HOUR = MINUTE * 60
