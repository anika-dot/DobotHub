'''
Custom exceptions for the Dobot API.

DobotError
DobotConnectionError
DobotProtocolError
DobotTimeoutError
DobotAlarmError
...

'''


class DobotError(Exception):
    """Base class for all DobotHub errors."""

class DobotConnectionError(DobotError):
    """Dobot not found or serial connection failed."""