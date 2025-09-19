"""
Module to hold common utilities.
"""

from datetime import datetime, timezone, timedelta


def get_text_split_into_lines(text: str) -> list[str]:
    """
    Safely text lines into an array of lines.

    Args:
        text (str): The text to split into an array.

    Returns:
        list[str]: An array of the text by lines. Cleans the start and end of each line.

    Basic splitting
    >>> get_text_split_into_lines("a\\nb\\nc")
    ['a', 'b', 'c']

    Trims leading/trailing whitespace on each line
    >>> get_text_split_into_lines("  a  \\n\\tb\\t")
    ['a', 'b']

    Preserves empty last line when text ends with a newline
    >>> get_text_split_into_lines("a\\n")
    ['a', '']

    Empty string produces a single empty line
    >>> get_text_split_into_lines("")
    ['']

    None returns an empty list
    >>> get_text_split_into_lines(None)
    []

    Windows-style newlines are handled and carriage returns are stripped
    >>> get_text_split_into_lines("a\\r\\nb\\r\\n")
    ['a', 'b', '']

    Whitespace-only lines become empty strings
    >>> get_text_split_into_lines(" \\n\\t")
    ['', '']
    """
    # sourcery skip: assign-if-exp, inline-immediately-returned-variable, inline-variable, reintroduce-else
    if text is None:
        return []

    lines = text.split("\n")
    lines = [line.strip() for line in lines]

    return lines


def get_formatted_time(time: datetime) -> str:
    """
    Uniformly format time .

    Args:
        time (datetime): The time we want to format.

    Returns:
        str: A string of the date/time formatted for consistency.

    Basic formatting
    >>> get_formatted_time(datetime(2024, 1, 2, 3, 4, 5))
    '2024-01-02 03:04:05UTC'

    Zero-padding for all components
    >>> get_formatted_time(datetime(2001, 2, 3, 4, 5, 6))
    '2001-02-03 04:05:06UTC'

    Microseconds are ignored
    >>> get_formatted_time(datetime(1999, 12, 31, 23, 59, 59, 987654))
    '1999-12-31 23:59:59UTC'

    Timezone info is not reflected; fields are used as-is
    >>> get_formatted_time(datetime(2020, 6, 1, 12, 0, 0, tzinfo=timezone(timedelta(hours=-5))))
    '2020-06-01 12:00:00UTC'
    """
    return f"{time:%Y-%m-%d %H:%M:%S}UTC"


def tab_text(text: str, tab_count: int = 1) -> str:
    """
    Indent each line of text with a consistent number of leading tabs.
    Trims leading/trailing whitespace on each line before indenting.

    Args:
        text (str): The text with inconsistent leading whitespace.
        tab_count (int, optional): Number of tabs to prefix per line. Any value less than zero is treated as 0.

    Returns:
        str: The string reconstructed with consistent tabbing.

    Basic indentation with one tab
    >>> tab_text("a\\nb\\nc")
    '\\ta\\n\\tb\\n\\tc'

    Custom tab count
    >>> tab_text("x\\ny", 2)
    '\\t\\tx\\n\\t\\ty'

    Negative tab count treated as 0 (no indentation)
    >>> tab_text("a", -5)
    'a'

    Trims leading/trailing whitespace on each line
    >>> tab_text("  a  \\n\\tb\\t", 1)
    '\\ta\\n\\tb'

    Windows-style newlines are handled and carriage returns are stripped
    >>> tab_text("a\\r\\nb\\r\\n", 1)
    '\\ta\\n\\tb\\n\\t'

    None returns an empty string
    >>> tab_text(None)
    ''
    """
    if text is None:
        return ""

    tab_count = max(tab_count, 0)
    lines = get_text_split_into_lines(text)
    tabs = "\t" * tab_count
    lines = [f"{tabs}{line}" for line in lines]

    return "\n".join(lines)


def get_singular_or_plural(value, unit):
    """
    Returns the value with a singular
    or plural form.
    """

    as_int = int(value)

    # Get rid of the decimal in
    # values like 1.0
    if as_int == value:
        value = as_int

    result = f"{str(value)} {unit}"

    if value != 1:
        result += "s"

    return result


def get_time_text(number_of_seconds):
    """
    Returns the amount of time in the appropriate unit.
    >>> get_time_text(-1)
    'No time'
    >>> get_time_text(0)
    'No time'
    >>> get_time_text(1)
    '1 second'
    >>> get_time_text(30)
    '30 seconds'
    >>> get_time_text(59)
    '59 seconds'
    >>> get_time_text(60)
    '1 minute'
    >>> get_time_text(90)
    '1 minute'
    >>> get_time_text(120)
    '2 minutes'
    >>> get_time_text(600)
    '10 minutes'
    >>> get_time_text((60 * 60) - 1)
    '59 minutes'
    >>> get_time_text(60 * 60)
    '1 hour'
    >>> get_time_text((60 * 60) + 1)
    '1 hour'
    >>> get_time_text((60 * 60) * 1.5)
    '1.5 hours'
    >>> get_time_text((60 * 60) * 2)
    '2 hours'
    >>> get_time_text((60 * 60) * 23)
    '23 hours'
    >>> get_time_text((60 * 60) * 24)
    '1 day'
    >>> get_time_text((60 * 60) * 36)
    '1.5 days'
    >>> get_time_text((60 * 60) * 36.1234)
    '1.5 days'
    >>> get_time_text((60 * 60) * 48)
    '2 days'
    """

    if number_of_seconds <= 0:
        return "No time"

    if number_of_seconds < 60:
        return get_singular_or_plural(int(number_of_seconds), "second")

    number_of_minutes = number_of_seconds / 60

    if number_of_minutes < 60:
        return get_singular_or_plural(int(number_of_minutes), "minute")

    number_of_hours = round(number_of_minutes / 60.0, 1)

    if number_of_hours < 24:
        return get_singular_or_plural(number_of_hours, "hour")

    number_of_days = round(number_of_hours / 24.0, 1)

    return get_singular_or_plural(number_of_days, "day")


def escape(text):
    """
    Replaces escape sequences do they can be printed.

    Funny story. PyDoc can't unit test strings with a CR or LF...
    It gives a white space error.

    >>> escape("text")
    'text'
    >>> escape("")
    ''
    """

    return str(text).replace("\r", "\\r").replace("\n", "\\n").replace("\x1a", "\\x1a")


def get_cleaned_phone_number(dirty_number):
    """
    Removes any text from the phone number that
    could cause the command to not work.

    >>> get_cleaned_phone_number('"2061234567"')
    '2061234567'
    >>> get_cleaned_phone_number('+2061234567')
    '2061234567'
    >>> get_cleaned_phone_number('""+2061234567')
    '2061234567'
    >>> get_cleaned_phone_number('2061234567')
    '2061234567'
    >>> get_cleaned_phone_number('(206) 123-4567')
    '2061234567'
    >>> get_cleaned_phone_number(None)
    """
    if dirty_number is not None:
        return (
            dirty_number.replace("+", "")
            .replace("(", "")
            .replace(")", "")
            .replace("-", "")
            .replace(" ", "")
            .replace('"', "")
        )
    return None


if __name__ == "__main__":
    import doctest

    print("Starting tests.")

    doctest.testmod()

    print("Tests finished")
