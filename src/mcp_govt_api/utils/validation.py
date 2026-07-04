"""Input validation utilities for tool parameters.

Provides reusable validators for common parameter types: limits,
US state codes, dates, and geographic coordinates.  Each validator
either returns a sanitised value or raises ``ValueError`` with a
user-friendly message.
"""

from __future__ import annotations

from datetime import datetime

# All 50 US states + DC + common territories
VALID_STATE_CODES: frozenset[str] = frozenset({
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC", "PR", "VI", "GU", "AS", "MP",
})


def validate_limit(limit: int, max_val: int = 100, default: int = 10) -> int:
    """Clamp *limit* to a valid range [1, *max_val*].

    If *limit* is ``None`` the *default* is returned.  Values below 1 are
    clamped to 1; values above *max_val* are clamped to *max_val*.

    Returns:
        A valid integer limit.

    Raises:
        ValueError: If *limit* is not an integer (and not ``None``).
    """
    if limit is None:
        return default
    if not isinstance(limit, int):
        raise ValueError(f"limit must be an integer, got {type(limit).__name__}")
    if limit < 1:
        return 1
    if limit > max_val:
        return max_val
    return limit


def validate_state_code(state: str) -> str:
    """Validate and normalise a US state abbreviation.

    Returns:
        The uppercase two-letter state code.

    Raises:
        ValueError: If *state* is not a recognised code.
    """
    if not isinstance(state, str) or not state.strip():
        raise ValueError("State code must be a non-empty string.")
    code = state.strip().upper()
    if len(code) != 2:
        raise ValueError(
            f"State code must be exactly 2 letters, got '{state}'."
        )
    if code not in VALID_STATE_CODES:
        raise ValueError(
            f"'{code}' is not a valid US state or territory code."
        )
    return code


def validate_date(date_str: str, fmt: str = "%Y-%m-%d") -> str:
    """Validate that *date_str* matches *fmt*.

    Returns:
        The original *date_str* (stripped) on success.

    Raises:
        ValueError: If parsing fails.
    """
    if not isinstance(date_str, str) or not date_str.strip():
        raise ValueError("Date string must be a non-empty string.")
    date_str = date_str.strip()
    try:
        datetime.strptime(date_str, fmt)
    except ValueError as exc:
        raise ValueError(
            f"Invalid date '{date_str}'. Expected format: {fmt}"
        ) from exc
    return date_str


def validate_latitude(lat: float) -> float:
    """Validate that *lat* is in [-90, 90].

    Returns:
        The latitude as a float.

    Raises:
        ValueError: If out of range or not a number.
    """
    try:
        lat = float(lat)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Latitude must be a number, got {lat!r}.") from exc
    if lat < -90 or lat > 90:
        raise ValueError(
            f"Latitude must be between -90 and 90, got {lat}."
        )
    return lat


def validate_longitude(lon: float) -> float:
    """Validate that *lon* is in [-180, 180].

    Returns:
        The longitude as a float.

    Raises:
        ValueError: If out of range or not a number.
    """
    try:
        lon = float(lon)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Longitude must be a number, got {lon!r}.") from exc
    if lon < -180 or lon > 180:
        raise ValueError(
            f"Longitude must be between -180 and 180, got {lon}."
        )
    return lon


def validate_magnitude(value: float) -> float:
    """Validate earthquake magnitude is in [0, 10].

    Returns:
        The magnitude as a float.

    Raises:
        ValueError: If out of range or not a number.
    """
    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Magnitude must be a number, got {value!r}.") from exc
    if value < 0 or value > 10:
        raise ValueError(
            f"Magnitude must be between 0 and 10, got {value}."
        )
    return value
