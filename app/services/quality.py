"""Extraction quality on the corpus: an extractor against the reference labels.

    interval detection   precision / recall / F1 of "the message states an interval"
    boundary error       mean absolute error of the two bounds, in minutes, where both agree an interval exists
    urgency agreement    Spearman rank correlation between the extracted urgency and the reference urgency
    band agreement       accuracy and confusion matrix over the four bands (flexible, mild, strong, binding)

The reference of a message is its bank label (category and interval) or, when the
reviewed annotation of the bank exists, the annotated band and interval.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from app import constants as c
from app.models import Preference
from app.services import corpus, extraction


class Quality(BaseModel):
    extractor: str
    messages: int
    reference: str                       # "annotation" or "bank labels"
    precision: float
    recall: float
    f1: float
    boundary_mae_min: float
    spearman: float
    band_accuracy: float
    confusion: dict[str, dict[str, int]]  # reference band -> extracted band -> count


def corpus_references(folder: Path | None = None) -> tuple[dict[int, Preference], str]:
    """Reference preference of every corpus message (keyed by message id) and where it comes from."""
    annotated = corpus.annotation(folder)
    refs = {}
    for row in corpus.read_corpus(folder):
        key = int(row["id"])
        start, end = corpus.parse_hhmm(row["window_start"]), corpus.parse_hhmm(row["window_end"])
        band = row["category"]
        if key in annotated:
            band = annotated[key]["band"].strip().lower()
            start, end = corpus.parse_hhmm(annotated[key]["window_start"]), corpus.parse_hhmm(annotated[key]["window_end"])
        refs[key] = Preference(start_h=start, end_h=end, urgency=c.BAND_URGENCY[band], band=band,
                               hard=band == c.HARD_BAND and start is not None)
    return refs, "annotation" if annotated else "bank labels"


def corpus_messages(folder: Path | None = None) -> dict[int, str]:
    return {int(r["id"]): r["message"] for r in corpus.read_corpus(folder)}


def assess(extracted: dict[int, Preference], references: dict[int, Preference], extractor: str, source: str) -> Quality:
    keys = sorted(references)
    tp = sum(extracted[k].has_window and references[k].has_window for k in keys)
    fp = sum(extracted[k].has_window and not references[k].has_window for k in keys)
    fn = sum(not extracted[k].has_window and references[k].has_window for k in keys)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    agreed = [k for k in keys if extracted[k].has_window and references[k].has_window]
    mae = (sum(abs(extracted[k].start_h - references[k].start_h) + abs(extracted[k].end_h - references[k].end_h)
               for k in agreed) / (2 * len(agreed)) * 60) if agreed else 0.0
    rho = spearman([extracted[k].urgency for k in keys], [references[k].urgency for k in keys])
    confusion = {r: {e: 0 for e in c.BANDS} for r in c.BANDS}
    for k in keys:
        confusion[_band(references[k])][_band(extracted[k])] += 1
    accuracy = sum(confusion[b][b] for b in c.BANDS) / len(keys)
    return Quality(extractor=extractor, messages=len(keys), reference=source, precision=round(precision, 3),
                   recall=round(recall, 3), f1=round(f1, 3), boundary_mae_min=round(mae, 1), spearman=round(rho, 3),
                   band_accuracy=round(accuracy, 3), confusion=confusion)


def assess_lexicon(folder: Path | None = None) -> Quality:
    references, source = corpus_references(folder)
    extracted = extraction.extract_all(corpus_messages(folder))
    return assess(extracted, references, "lexicon", source)


def assess_llm(folder: Path | None = None) -> Quality:
    from app.services import llm
    references, source = corpus_references(folder)
    extracted = llm.extract_many(corpus_messages(folder))
    return assess(extracted, references, "llm", source)


def _band(pref: Preference) -> str:
    return "flexible" if pref.band == "none" else pref.band


def spearman(x: list[float], y: list[float]) -> float:
    rx, ry = _ranks(x), _ranks(y)
    n = len(x)
    mx, my = sum(rx) / n, sum(ry) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    vx, vy = sum((a - mx) ** 2 for a in rx), sum((b - my) ** 2 for b in ry)
    return cov / (vx * vy) ** 0.5 if vx and vy else 0.0


def _ranks(values: list[float]) -> list[float]:
    """Average ranks (ties share the mean of their positions)."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return ranks
