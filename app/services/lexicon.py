"""Urgency scoring with the domain lexicon (Section 3 of the paper).

The lexicon L = {(w_k, phi_k)} lists terms and expressions with an urgency weight in
[-0.6, 0.8]: binding markers ("must", "only", "no other option"), preference markers
("prefer", "I need", "at work"), mild markers ("if possible", "please") and flexibility
markers with negative weight ("any time", "no rush"). The strongest positive marker sets
the level of a message and the flexibility markers attenuate it,

    u = min(1, max(0, max_{k in M+} phi_k + sum_{k in M-} phi_k)),

so that a polite message with several weak markers does not outrank a single binding one.
Hedges ("not a must", "no drama") form a fourth category: they state that a wish is not
binding without withdrawing it, so they cap the score at their weight instead of lowering
it. Longer expressions are matched first and a matched span is not matched again, so
"i would prefer" does not also count as "prefer", and "not a must" hides "must".
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app import constants as c
from app.config import get_settings


@dataclass(frozen=True)
class Term:
    text: str
    weight: float
    category: str


@dataclass(frozen=True)
class Match:
    term: Term
    start: int
    end: int


def load_lexicon(path: Path | None = None) -> list[Term]:
    path = path or get_settings().lexicon_dir / c.LEXICON_FILE
    with open(path, newline="", encoding="utf-8") as fh:
        terms = [Term(r["term"].strip().lower(), float(r["weight"]), r["category"].strip()) for r in csv.DictReader(fh)]
    return sorted(terms, key=lambda t: -len(t.text))       # longest first


@lru_cache
def _patterns(lexicon_path: str | None) -> tuple[tuple[Term, re.Pattern], ...]:
    terms = load_lexicon(Path(lexicon_path) if lexicon_path else None)
    return tuple((t, re.compile(rf"(?<![a-z']){re.escape(t.text)}(?![a-z'])")) for t in terms)


def normalise(message: str) -> str:
    text = message.lower().replace("’", "'")
    return re.sub(r"\s+", " ", text).strip()


def find_terms(message: str, lexicon_path: Path | None = None) -> list[Match]:
    """Lexicon terms found in the message, longest first, without overlapping spans."""
    text = normalise(message)
    taken = [False] * len(text)
    matches: list[Match] = []
    for term, pattern in _patterns(str(lexicon_path) if lexicon_path else None):
        for m in pattern.finditer(text):
            if any(taken[m.start():m.end()]):
                continue
            for i in range(m.start(), m.end()):
                taken[i] = True
            matches.append(Match(term, m.start(), m.end()))
    return sorted(matches, key=lambda x: x.start)


HEDGE = "hedge"


def urgency(message: str, lexicon_path: Path | None = None) -> float:
    terms = [m.term for m in find_terms(message, lexicon_path)]
    strongest = max((t.weight for t in terms if t.category != HEDGE and t.weight > 0), default=0.0)
    attenuation = sum(t.weight for t in terms if t.weight < 0)
    cap = min((t.weight for t in terms if t.category == HEDGE), default=1.0)
    return round(min(cap, max(0.0, strongest + attenuation)), 3)


def band_of(u: float) -> str:
    """Urgency band by the lower bounds in constants (flexible < mild < strong < binding)."""
    band = c.BANDS[0]
    for name in c.BANDS:
        if u >= c.BAND_LOWER_BOUND[name]:
            band = name
    return band
