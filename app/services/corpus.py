"""The message bank, its instantiation into customer messages and the reference labels.

The bank (data/corpus/bank.json) holds short customer messages written by the authors in
five categories: binding constraint, strong preference, mild preference, explicit
flexibility and no temporal information. Messages with an interval carry hour
placeholders ({a}, {b}) or name a period of the day, so that one bank message can be
instantiated with the hours of a given stop. Every instantiated message keeps the id of
its bank message and the labels it was written under (category, interval); those labels
are the reference of the extraction evaluation and of the routing evaluation, unless the
reviewed annotation of the bank (data/corpus/reference.csv) is present, in which case
the annotated band and interval shape replace the bank labels.
"""

from __future__ import annotations

import csv
import json
import math
import random
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app import constants as c
from app.config import get_settings
from app.models import Instance, Node, Preference

CATEGORIES = tuple(c.CATEGORY_MIX)
WINDOW_WIDTHS_H = (2, 3)
BOUND_SLACK_H = 1        # a one-sided bound is stated at most this far from the anchored hour
HOUR_STYLES = ("24h", "12h", "ampm", "colon")


@dataclass(frozen=True)
class BankMessage:
    id: int
    category: str
    shape: str          # two_sided | after | before | named | none
    text: str
    period: str | None = None

    def can_contain(self, hour: float) -> bool:
        """Whether an instantiation of this message can have a window containing `hour`."""
        if self.shape == "two_sided" or self.shape == "none":
            return True
        if self.shape == "after":
            return hour >= c.WORKING_DAY_START_H + 1
        if self.shape == "before":
            return hour <= c.WORKING_DAY_END_H - 1
        start, end = c.NAMED_PERIODS[self.period]
        return start <= hour <= end


@dataclass(frozen=True)
class Instantiated:
    message_id: int
    category: str
    text: str
    start_h: float | None
    end_h: float | None


@lru_cache
def load_bank(path: Path | None = None) -> tuple[BankMessage, ...]:
    path = path or get_settings().corpus_dir / c.BANK_FILE
    entries = json.loads(Path(path).read_text(encoding="utf-8"))
    return tuple(BankMessage(e["id"], e["category"], e["shape"], e["text"], e.get("period")) for e in entries)


# ----------------------------------------------------------------------------- instantiation

def instantiate(message: BankMessage, rng: random.Random, anchor_h: float | None = None) -> Instantiated:
    """Fill the hour placeholders; with an anchor, the interval is chosen to contain that clock hour."""
    lo, hi = c.WORKING_DAY_START_H, c.WORKING_DAY_END_H
    style = rng.choice(HOUR_STYLES)
    start = end = None
    text = message.text
    if message.shape == "two_sided":
        width = rng.choice(WINDOW_WIDTHS_H)
        if anchor_h is None:
            start = rng.randint(int(lo), int(hi) - width)
        else:
            start = rng.randint(max(int(lo), math.ceil(anchor_h) - width), min(int(hi) - width, math.floor(anchor_h)))
        end = start + width
        text = text.replace("{a}", _hour_text(start, style)).replace("{b}", _hour_text(end, style))
    elif message.shape == "after":
        latest = int(hi) - 1 if anchor_h is None else max(int(lo) + 1, min(int(hi) - 1, math.floor(anchor_h)))
        start = rng.randint(int(lo) + 1 if anchor_h is None else max(int(lo) + 1, latest - BOUND_SLACK_H), latest)
        end = hi
        text = text.replace("{a}", _hour_text(start, style))
    elif message.shape == "before":
        earliest = int(lo) + 1 if anchor_h is None else min(int(hi) - 1, max(int(lo) + 1, math.ceil(anchor_h)))
        start = lo
        end = rng.randint(earliest, int(hi) - 1 if anchor_h is None else min(int(hi) - 1, earliest + BOUND_SLACK_H))
        text = text.replace("{b}", _hour_text(end, style))
    elif message.shape == "named":
        start, end = c.NAMED_PERIODS[message.period]
    return Instantiated(message.id, message.category, text, float(start) if start is not None else None,
                        float(end) if end is not None else None)


def _hour_text(hour: int, style: str) -> str:
    if style == "24h":
        return str(hour)
    if style == "colon":
        return f"{hour}:00"
    twelve = hour - 12 if hour > 12 else hour
    if style == "12h":
        return str(twelve)
    return f"{twelve} {'pm' if hour >= 12 else 'am'}"


def draw_category(rng: random.Random) -> str:
    return rng.choices(CATEGORIES, weights=[c.CATEGORY_MIX[k] for k in CATEGORIES])[0]


def message_for(category: str, rng: random.Random, anchor_h: float | None, bank: tuple[BankMessage, ...]) -> Instantiated:
    """A random bank message of the category that can contain the anchor, instantiated."""
    candidates = [m for m in bank if m.category == category and (anchor_h is None or m.can_contain(anchor_h))]
    return instantiate(rng.choice(candidates), rng, anchor_h)


# ----------------------------------------------------------------------------- corpus files

def write_corpus(seed: int = c.CORPUS_SEED, folder: Path | None = None) -> list[Path]:
    """Instantiate every bank message once (random hours): corpus.csv + the annotation template."""
    folder = folder or get_settings().corpus_dir
    rng = random.Random(seed)
    rows = [instantiate(m, rng) for m in load_bank()]
    corpus = folder / c.CORPUS_FILE
    with open(corpus, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["id", "message", "category", "window_start", "window_end"])
        for r in rows:
            writer.writerow([r.message_id, r.text, r.category, _hhmm(r.start_h), _hhmm(r.end_h)])
    template = folder / c.ANNOTATION_TEMPLATE_FILE
    with open(template, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["id", "message", "window_start", "window_end", "band"])
        for r in rows:
            writer.writerow([r.message_id, r.text, "", "", ""])
    return [corpus, template]


def read_corpus(folder: Path | None = None) -> list[dict]:
    folder = folder or get_settings().corpus_dir
    with open(folder / c.CORPUS_FILE, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _hhmm(hour: float | None) -> str:
    return "" if hour is None else f"{int(hour):02d}:{int(round((hour % 1) * 60)):02d}"


def parse_hhmm(text: str) -> float | None:
    text = (text or "").strip()
    if not text:
        return None
    h, m = (text.split(":") + ["0"])[:2]
    return int(h) + int(m) / 60


# ----------------------------------------------------------------------------- reference labels

@lru_cache
def annotation(folder: Path | None = None) -> dict[int, dict]:
    """The reviewed annotation of the bank (reference.csv), keyed by message id; {} if absent."""
    path = (folder or get_settings().corpus_dir) / c.REFERENCE_FILE
    if not path.is_file():
        return {}
    with open(path, newline="", encoding="utf-8") as fh:
        return {int(r["id"]): r for r in csv.DictReader(fh) if r.get("band")}


def reference_of(node: Node) -> Preference:
    """Reference preference of a stop: the bank labels, with the band from the annotation when available."""
    pref = node.reference()
    annotated = annotation().get(node.message_id) if node.message_id is not None else None
    if annotated is None:
        return pref
    band = annotated["band"].strip().lower()
    has_window = bool(annotated.get("window_start") or annotated.get("window_end"))
    start, end = (pref.start_h, pref.end_h) if has_window else (None, None)
    return Preference(start_h=start, end_h=end, urgency=c.BAND_URGENCY[band], band=band,
                      hard=band == c.HARD_BAND and start is not None)


def references(instance: Instance) -> dict[int, Preference]:
    return {n.id: reference_of(n) for n in instance.stops}
