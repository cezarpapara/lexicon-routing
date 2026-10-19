"""Synthetic instances for the scalability test, generated from the real stops.

Stops are sampled with replacement from the stops of all source days and their coordinates
are jittered by Gaussian noise so that no real delivery area is reproduced. The matrices are
great-circle distances scaled by a road detour factor and travel times at a constant speed,
so that the test is reproducible offline. No dispatcher plan exists: the messages are
anchored on a random reference sequence, never disclosed to the solvers, which only
guarantees that a schedule honouring every stated interval exists and favours no method.
"""

from __future__ import annotations

import math
import random

from app import constants as c
from app.config import get_settings
from app.models import Instance, Node
from app.services import data

JITTER_M = 300.0               # standard deviation of the coordinate noise, metres
DETOUR_FACTOR = 1.3            # road distance / great-circle distance, typical for regional road networks
SPEED_KMH = 45.0               # average speed used for the synthetic travel times
M_PER_DEG_LAT = 111_320.0


def generate(n_stops: int, seed: int) -> str:
    settings = get_settings()
    days = [data.load_day(d)[0] for d in data.list_source_days()]
    if not days:
        raise FileNotFoundError("No source days in data/source")
    rng = random.Random(seed)
    pool = [r for rows in days for r in rows if r["trip_id"]]
    depot = next(r for r in days[0] if int(r["id"]) == c.DEPOT_NODE_ID)
    nodes = [Node(id=c.DEPOT_NODE_ID, lat=float(depot["lat"]), lon=float(depot["lon"]))]
    for k in range(n_stops):
        source = rng.choice(pool)
        lat, lon = float(source["lat"]), float(source["lon"])
        lat += rng.gauss(0, JITTER_M / M_PER_DEG_LAT)
        lon += rng.gauss(0, JITTER_M / (M_PER_DEG_LAT * math.cos(math.radians(lat))))
        nodes.append(Node(id=k + 1, lat=round(lat, 6), lon=round(lon, 6)))
    coords = [(n.lat, n.lon) for n in nodes]
    distance, duration = haversine_matrices(coords)
    instance_id = f"SYN_{n_stops}_{seed}"
    instance = Instance(id=instance_id, nodes=nodes, distance_m=distance, duration_s=duration)
    reference = [n.id for n in instance.stops]
    rng.shuffle(reference)
    data.assign_messages(instance, anchor_route=reference, seed=f"{c.CORPUS_SEED}:{instance_id}")
    data.write_instance(settings.instances_dir / instance_id, instance)
    return instance_id


def haversine_matrices(coords):
    n = len(coords)
    distance = [[0] * n for _ in range(n)]
    duration = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            m = int(round(DETOUR_FACTOR * _haversine_m(coords[i], coords[j])))
            distance[i][j] = distance[j][i] = m
            duration[i][j] = duration[j][i] = int(round(m / (SPEED_KMH * 1000 / 3600)))
    return distance, duration


def _haversine_m(a, b) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6_371_000 * math.asin(math.sqrt(h))
