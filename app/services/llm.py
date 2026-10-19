"""Large language model as an alternative preference extractor (Google Gemini API).

Messages are sent in batches with a fixed instruction asking for the interval, the urgency
and the binding flag as JSON; the answers are cached per message text under
data/corpus/llm/<model>.json so that every later run is deterministic and offline.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import time

import httpx

from app import constants as c
from app.config import get_settings
from app.models import Preference
from app.services import lexicon

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
BATCH_SIZE = 10
ATTEMPTS = 2               # tries per request; a batch that still times out is split in two, a single message that fails is recorded as unread
UNREAD = {"window_start": None, "window_end": None, "urgency": 0, "binding": False, "unread": True}

INSTRUCTION = """You read short messages that customers of a home-improvement retailer left on their delivery orders.
For each message decide, from the text alone and without guessing beyond what is written:
- "window_start": earliest acceptable delivery hour as "HH:MM" (24-hour clock), or null if none is stated;
- "window_end": latest acceptable delivery hour as "HH:MM", or null if none is stated;
- "urgency": a number in [0, 1]: 0 = fully flexible or no temporal information, 0.25 = mild wish,
  0.5 = clear preference, 1 = binding constraint the customer cannot move;
- "binding": true if the interval is stated as non-negotiable, else false.
Deliveries happen between 08:00 and 17:00; a bare hour from 1 to 7 means the afternoon.
Named periods: morning = 08:00-12:00, noon/lunchtime = 11:00-14:00, afternoon = 13:00-17:00, late afternoon = 15:00-17:00.
Answer with a JSON array of objects {"id", "window_start", "window_end", "urgency", "binding"}, one per message, nothing else.

Messages:
"""


def extract_many(messages: dict[int, str], model: str | None = None) -> dict[int, Preference]:
    settings = get_settings()
    model = model or settings.GEMINI_MODEL
    cache = _load_cache(model)
    pending = {key: text for key, text in messages.items() if _digest(text) not in cache}
    keys = list(pending)
    for k in range(0, len(keys), BATCH_SIZE):
        batch = {key: pending[key] for key in keys[k:k + BATCH_SIZE]}
        for key, answer in _ask_resilient(batch, model, settings).items():
            cache[_digest(batch[key])] = answer
        _save_cache(model, cache)
    return {key: _to_preference(cache[_digest(text)]) for key, text in messages.items()}


def _ask_resilient(batch: dict[int, str], model: str, settings) -> dict[int, dict]:
    """Answers for a batch; on a time-out or a malformed answer the batch is halved, a lone failing message is marked unread."""
    try:
        return _ask(batch, model, settings)
    except (httpx.TimeoutException, httpx.TransportError, RuntimeError, ValueError, KeyError) as exc:
        if len(batch) == 1:
            key = next(iter(batch))
            print(f"  LLM: message {key} left unread ({type(exc).__name__})")
            return {key: dict(UNREAD)}
        keys = list(batch)
        half = len(keys) // 2
        answers = _ask_resilient({k: batch[k] for k in keys[:half]}, model, settings)
        answers.update(_ask_resilient({k: batch[k] for k in keys[half:]}, model, settings))
        return answers


def _ask(batch: dict[int, str], model: str, settings) -> dict[int, dict]:
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set (put it in .env.local)")
    listing = "\n".join(f'{key}: "{text}"' for key, text in batch.items())
    body = {"contents": [{"parts": [{"text": INSTRUCTION + listing}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json",
                                 **({"thinkingConfig": {"thinkingBudget": settings.GEMINI_THINKING_BUDGET}}
                                    if settings.GEMINI_THINKING_BUDGET >= 0 else {})}}
    response = _post(ENDPOINT.format(model=model), settings.GEMINI_API_KEY, body, settings.GEMINI_TIMEOUT_S)
    text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    answers = {int(a["id"]): a for a in json.loads(text)}
    missing = set(batch) - set(answers)
    if missing:
        raise RuntimeError(f"{model} returned no answer for messages {sorted(missing)}")
    return answers


def _post(url: str, key: str, body: dict, timeout_s: int) -> httpx.Response:
    """One request with retries: a slow answer or a transient error (429, 5xx) is retried, anything else raises."""
    for attempt in range(1, ATTEMPTS + 1):
        try:
            response = httpx.post(url, params={"key": key}, json=body, timeout=timeout_s)
            if response.status_code == 429 or response.status_code >= 500:
                raise httpx.HTTPStatusError(f"HTTP {response.status_code}", request=response.request, response=response)
            response.raise_for_status()
            return response
        except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as exc:
            if attempt == ATTEMPTS or (isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code < 429):
                raise
            time.sleep(5 * attempt)
    raise RuntimeError("unreachable")


def _to_preference(answer: dict) -> Preference:
    start, end = _hour(answer.get("window_start")), _hour(answer.get("window_end"))
    if start is not None or end is not None:
        start = c.WORKING_DAY_START_H if start is None else max(start, c.WORKING_DAY_START_H)
        end = c.WORKING_DAY_END_H if end is None else min(end, c.WORKING_DAY_END_H)
        if start >= end:
            start = end = None
    u = round(min(1.0, max(0.0, float(answer.get("urgency") or 0.0))), 3) if start is not None else 0.0
    band = lexicon.band_of(u)
    if answer.get("binding"):
        band = c.HARD_BAND
    elif band == c.HARD_BAND:
        band = "strong"                # the model's binding flag, not the score alone, decides the hard windows
    return Preference(start_h=start, end_h=end, urgency=u, band=band, hard=band == c.HARD_BAND and start is not None)


def _hour(text) -> float | None:
    if not text:
        return None
    h, m = (str(text).split(":") + ["0"])[:2]
    return int(h) + int(m) / 60


def _digest(text: str) -> str:
    return hashlib.sha1(text.strip().encode("utf-8")).hexdigest()


def _cache_path(model: str) -> Path:
    folder = get_settings().corpus_dir / "llm"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{model}.json"


def _load_cache(model: str) -> dict[str, dict]:
    path = _cache_path(model)
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def _save_cache(model: str, cache: dict[str, dict]) -> None:
    _cache_path(model).write_text(json.dumps(cache, indent=1, sort_keys=True), encoding="utf-8")
