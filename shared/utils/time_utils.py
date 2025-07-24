from datetime import datetime


def format_to_iso_date(date: datetime) -> str:
    """
    Formats a datetime object to an ISO date string in the format YYYY-MM-DD.

    Args:
        date (datetime): The datetime object to format.

    Returns:
        str: The formatted date string.
    """
    return date.strftime("%Y-%m-%d")


def format_to_iso_datetime(date: datetime) -> str:
    """
    Formats a datetime object to an ISO datetime string in the format YYYY-MM-DDTHH:MM:SS.

    Args:
        date (datetime): The datetime object to format.

    Returns:
        str: The formatted datetime string.
    """
    return date.strftime("%Y-%m-%dT%H:%M:%S")


def from_iso_datetime(iso_datetime_str: str) -> datetime:
    """
    Parses an ISO datetime string and returns a datetime object.

    Args:
        iso_str (str): The ISO datetime string to parse.

    Returns:
        datetime: The parsed datetime object.
    """
    return datetime.fromisoformat(iso_datetime_str)
