"""Preference extraction: message -> (preferred interval, urgency, band).

The interval comes from a small set of pattern rules applied in order of specificity:
explicit two-sided intervals ("between 10 and 12", "from 9 to 11", "10-12"), one-sided
bounds ("after 3 pm", "not before 15:00", "until noon", "by 4"), named periods of the day
("morning", "afternoon", "around noon", "late afternoon") and, as a last resort, a point
in time ("around 2") widened by one hour on each side. Hours between 1 and 7 without an
am/pm marker are read as afternoon hours, the reading a dispatcher would make on a
delivery day that starts at 08:00. Intervals are clipped to the working day.

The urgency comes from the lexicon (see lexicon.py) and is set to zero when no interval was
found, since an urgency without an interval cannot be acted upon; the band of the urgency
decides whether the interval is a hard window (binding band) or a soft preference.
"""

from __future__ import annotations

import re
from pathlib import Path

from app import constants as c
from app.models import Preference
from app.services import lexicon

_TIME = r"(?<![\d:])(\d{1,2})(?::(\d{2}))?\s*(am|pm|a\.m\.|p\.m\.|o'?clock)?(?!\s*(?:min\b|minutes|%|\d))"
_TWO_SIDED = [
    re.compile(rf"between {_TIME} and {_TIME}"),
    re.compile(rf"from {_TIME} (?:to|until|till|-|–) {_TIME}"),
    re.compile(rf"in the {_TIME} ?(?:-|–|to) ?{_TIME} slot"),
    re.compile(rf"{_TIME} ?(?:-|–|to) ?{_TIME}"),
]
_AFTER = re.compile(rf"(?:after|not before|no earlier than|starting at|starting from|later than|past|from) {_TIME}(?: onwards| on)?")
_ONWARDS = re.compile(rf"{_TIME} onwards")
_BEFORE = re.compile(rf"(?:before|until|till|by|no later than|at the latest|not after|not later than|up to|latest) {_TIME}")
_POINT = re.compile(rf"(?:at|around|about) {_TIME}")
_NAMED = [   # checked in this order; the first period mentioned in the message wins
    ("late_afternoon", re.compile(r"late afternoon|late in the afternoon|end of the day|towards the end|later in the day|evening")),
    ("afternoon", re.compile(r"afternoon|after lunch|after noon")),
    ("morning", re.compile(r"morning|before noon|before lunch|first thing|early in the day")),
    ("noon", re.compile(r"noon|lunchtime|lunch time|lunch break|midday|lunch")),
]


def hour_of(h: str, minutes: str | None, marker: str | None) -> float | None:
    """Clock hour of a time token, or None when it cannot be a time of day."""
    hour = int(h) + (int(minutes) / 60 if minutes else 0.0)
    marker = (marker or "").replace(".", "")
    if marker == "pm" and hour < 12:
        hour += 12
    elif marker != "am" and 1 <= hour <= 7:
        hour += 12
    return hour if 0 <= hour < 24 else None


def interval(message: str) -> tuple[float | None, float | None]:
    """Preferred interval in clock hours, clipped to the working day; (None, None) if none stated."""
    text = lexicon.normalise(message)
    for pattern in _TWO_SIDED:
        for m in pattern.finditer(text):
            a, b = hour_of(*m.groups()[0:3]), hour_of(*m.groups()[3:6])
            if a is not None and b is not None and a < b:
                return _clip(a, b)
    starts, text = _consume(_AFTER, text)
    more, text = _consume(_ONWARDS, text)
    ends, text = _consume(_BEFORE, text)
    start = min(starts + more) if starts + more else None
    end = max(ends) if ends else None
    if start is not None or end is not None:
        return _clip(start if start is not None else c.WORKING_DAY_START_H, end if end is not None else c.WORKING_DAY_END_H)
    named = [(m.start(), period) for period, pattern in _NAMED for m in [pattern.search(text)] if m]
    if named:
        return c.NAMED_PERIODS[min(named)[1]]
    for m in _POINT.finditer(text):
        if (hour := hour_of(*m.groups()[0:3])) is not None:
            return _clip(hour - 1, hour + 1)
    return None, None


def _consume(pattern: re.Pattern, text: str) -> tuple[list[float], str]:
    """Hours of every match of `pattern`; the matched spans are blanked so later rules skip them."""
    hours = []
    for m in pattern.finditer(text):
        if (hour := hour_of(*m.groups()[0:3])) is not None:
            hours.append(hour)
    return hours, pattern.sub(lambda m: " " * len(m.group(0)), text)


def _clip(start: float, end: float) -> tuple[float | None, float | None]:
    start, end = max(start, c.WORKING_DAY_START_H), min(end, c.WORKING_DAY_END_H)
    return (start, end) if start < end else (None, None)


def extract(message: str, lexicon_path: Path | None = None) -> Preference:
    """A message without an interval carries no operational constraint, whatever its wording: u = 0."""
    start, end = interval(message)
    u = lexicon.urgency(message, lexicon_path) if start is not None else 0.0
    band = lexicon.band_of(u)
    return Preference(start_h=start, end_h=end, urgency=u, band=band, hard=band == c.HARD_BAND and start is not None)


def extract_all(messages: dict[int, str], lexicon_path: Path | None = None) -> dict[int, Preference]:
    return {key: extract(text, lexicon_path) for key, text in messages.items()}
