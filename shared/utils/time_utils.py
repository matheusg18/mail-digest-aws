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
