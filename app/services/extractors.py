"""The three ways a solver can be given the customers' preferences.

    lexicon  - the proposed extraction (lexicon urgency + interval rules) from the messages
    llm      - a large language model reading the same messages (alternative extractor)
    oracle   - the reference labels themselves (upper bound: extraction without error)
"""

from __future__ import annotations

from typing import Callable

from app.models import Instance, Preference
from app.services import corpus, extraction

LEXICON, LLM, ORACLE = "lexicon", "llm", "oracle"


def messages_of(instance: Instance) -> dict[int, str]:
    return {n.id: n.message for n in instance.stops}


def lexicon_preferences(instance: Instance) -> dict[int, Preference]:
    return extraction.extract_all(messages_of(instance))


def llm_preferences(instance: Instance) -> dict[int, Preference]:
    from app.services import llm       # local import: httpx and the API key are only needed here
    return llm.extract_many(messages_of(instance))


def oracle_preferences(instance: Instance) -> dict[int, Preference]:
    return corpus.references(instance)


EXTRACTORS: dict[str, Callable[[Instance], dict[int, Preference]]] = {
    LEXICON: lexicon_preferences, LLM: llm_preferences, ORACLE: oracle_preferences,
}


def preferences(instance: Instance, extractor: str = LEXICON) -> dict[int, Preference]:
    if extractor not in EXTRACTORS:
        raise KeyError(f"Unknown extractor '{extractor}'. Available: {sorted(EXTRACTORS)}")
    return EXTRACTORS[extractor](instance)
