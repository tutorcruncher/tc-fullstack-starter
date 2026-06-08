import re
from datetime import datetime, time


def escape_like(value: str) -> str:
    r"""Escape special LIKE pattern characters (%, _, \) for safe use in SQL LIKE queries."""
    return re.sub(r'([%_\\])', r'\\\1', value)


def inclusive_end_of_day(dt: datetime) -> datetime:
    """Bump a date-only datetime (time == 00:00:00) to end-of-day; pass through otherwise.

    Used for inclusive upper-bound date filters: ``created_to=2024-03-15`` should include
    records from the whole of March 15th, whereas an explicit time (``2024-03-15T10:00:00``)
    is preserved verbatim so callers can express sub-day cutoffs.
    """
    if dt.time() == time(0, 0, 0):
        return dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    return dt


def sanitize_for_postgres(data):
    r"""Recursively sanitize data to remove characters that PostgreSQL cannot handle.

    This removes:
    - Null bytes (\x00) which PostgreSQL text/JSONB cannot store
    - Other C0 control characters (except tab, newline and carriage return)

    Args:
        data: Any JSON-serializable data (dict, list, str, int, float, bool, None)

    Returns:
        Sanitized version of the data with problematic characters removed
    """
    if isinstance(data, str):
        sanitized = data.replace('\x00', '')
        sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', sanitized)
        return sanitized
    elif isinstance(data, dict):
        return {key: sanitize_for_postgres(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_for_postgres(item) for item in data]
    else:
        return data
