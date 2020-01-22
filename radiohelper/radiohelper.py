"""A library of shared functions that are used by radio Rx and Tx scripts.

increment_serial_number_with_wrap(serial_number, wrap_at=0x10000)
"""


def increment_number_with_wrap(number: int, wrap_at=0x10000):
    """Increments an number and returns the modulo of the result.

    Arguments:
    serial_number -- An number to be incremented

    Keyword Arguments:
    wrap_at -- Used to take the modulo of the incremented serial number (default 0x10000)
    """
    try:
        return (number + 1) % wrap_at
    except (ValueError, TypeError) as e:
        raise TypeError('number and wrap_at must be numbers') from e
