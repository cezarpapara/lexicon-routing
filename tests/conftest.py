"""Shared fixtures: a small instance with straight-line matrices and hand-written messages (no network)."""

from __future__ import annotations

import pytest

from app.models import Instance, Node
from app.services.synth import haversine_matrices

DEPOT = (46.5600, 26.9100)   # placeholder depot, Bacău area

# (lat, lon, message, band, ref_start_h, ref_end_h, message_id)
STOPS = [
    (46.5700, 26.9200, "Only between 10 and 12, I'm at work otherwise, no other option.", "binding", 10.0, 12.0, 1),
    (46.5750, 26.9300, "I would prefer the afternoon, I'm at work in the morning.", "strong", 13.0, 17.0, 87),
    (46.5650, 26.9400, "If possible before 10, but not a must.", "mild", 8.0, 10.0, 129),
    (46.6500, 26.8000, "Any time works, I'm home all day.", "flexible", None, None, 161),
    (46.6600, 26.7900, "Second floor, no elevator, thanks.", "none", None, None, 213),
    (46.6400, 26.7700, "Must be after 3 pm, nobody home before, cannot be moved.", "binding", 15.0, 17.0, 16),
    (46.4800, 27.0500, "preferably in the morning, afternoons im not home", "strong", 8.0, 12.0, 85),
    (46.4700, 27.0700, "Ideally around noon, if it works for you.", "mild", 11.0, 14.0, 146),
]


@pytest.fixture
def instance() -> Instance:
    nodes = [Node(id=0, lat=DEPOT[0], lon=DEPOT[1])]
    for i, (lat, lon, message, band, start, end, message_id) in enumerate(STOPS, start=1):
        nodes.append(Node(id=i, lat=lat, lon=lon, message=message, band=band, ref_start_h=start, ref_end_h=end,
                          message_id=message_id, stop_seq=i))
    distance, duration = haversine_matrices([(n.lat, n.lon) for n in nodes])
    return Instance(id="TEST", nodes=nodes, distance_m=distance, duration_s=duration, dispatcher_route=list(range(1, 9)))
