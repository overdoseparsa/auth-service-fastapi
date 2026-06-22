from datetime import datetime, timezone


def _utc_now() -> datetime:
    "returns the current UTC datetime"
    return datetime.now(timezone.utc)


def convert_datetime_timestamp(dt: datetime) -> float:
    "for converting a datetime to a Unix timestamp"
    return dt.timestamp()


def convert_timestamp_datetime(ts: float) -> datetime:
    "for converting a Unix timestamp to a datetime"
    return datetime.fromtimestamp(ts, timezone.utc)
