"""Instances: from the source delivery days to routing instances with customer messages.

Source (data/source/DAY_n): the anonymised delivery days published with the compact-routing
dataset (nodes with the dispatcher's trips, symmetric road matrices, cached Concorde tours).
`build_instances` turns every dispatcher trip with at least MIN_TRIP_STOPS stops into one
single-vehicle instance (data/instances/<trip_id>): the depot and the stops of the trip,
their sub-matrices, the dispatcher's sequence, the Concorde tour, and one customer message
per stop. Messages are drawn from the bank so that the category mix of constants.py holds
in expectation and, for stops whose message states an interval, the interval contains the
hour at which the dispatcher's own sequence reaches the stop: the executed plan is taken
as evidence of the constraints the dispatcher knew about.
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

from app import constants as c
from app.config import get_settings
from app.models import Instance, Node
from app.services import corpus, schedule


# ----------------------------------------------------------------------------- source days

def list_source_days(folder: Path | None = None) -> list[str]:
    folder = folder or get_settings().source_dir
    return sorted(p.name for p in folder.iterdir() if p.is_dir() and (p / c.NODES_FILE).is_file())


def load_day(day: str, folder: Path | None = None) -> tuple[list[dict], list[list[int]], list[list[int]]]:
    folder = (folder or get_settings().source_dir) / day
    with open(folder / c.NODES_FILE, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return rows, _read_matrix(folder / c.DISTANCE_FILE), _read_matrix(folder / c.DURATION_FILE)


def dispatcher_trips(rows: list[dict]) -> dict[str, list[int]]:
    """Trip id -> source node ids in the dispatcher's order."""
    trips: dict[str, list[tuple[int, int]]] = {}
    for r in rows:
        if r["trip_id"]:
            trips.setdefault(r["trip_id"], []).append((int(r["stop_seq"]), int(r["id"])))
    return {trip: [node for _, node in sorted(stops)] for trip, stops in trips.items()}


# ----------------------------------------------------------------------------- build

def build_instances(seed: int = c.CORPUS_SEED, min_stops: int = c.MIN_TRIP_STOPS) -> list[str]:
    settings = get_settings()
    built = []
    for day in list_source_days():
        rows, distance, duration = load_day(day)
        for trip_id, stops in dispatcher_trips(rows).items():
            if len(stops) < min_stops:
                continue
            instance = _trip_instance(trip_id, rows, stops, distance, duration)
            assign_messages(instance, anchor_route=instance.dispatcher_route, seed=f"{seed}:{trip_id}")
            folder = settings.instances_dir / trip_id
            write_instance(folder, instance)
            tour = _concorde_tour(settings.source_dir / day / "concorde", trip_id, stops)
            if tour:
                (folder / c.CONCORDE_TOUR_FILE).write_text(" ".join(map(str, tour)) + "\n")
            built.append(trip_id)
    return built


def _trip_instance(trip_id: str, rows: list[dict], stops: list[int], distance, duration) -> Instance:
    source_ids = [c.DEPOT_NODE_ID] + sorted(stops)
    local = {src: k for k, src in enumerate(source_ids)}
    by_id = {int(r["id"]): r for r in rows}
    nodes = [Node(id=local[src], lat=float(by_id[src]["lat"]), lon=float(by_id[src]["lon"]),
                  stop_seq=int(by_id[src]["stop_seq"]) if by_id[src]["stop_seq"] else None) for src in source_ids]
    sub = lambda m: [[m[a][b] for b in source_ids] for a in source_ids]
    return Instance(id=trip_id, nodes=nodes, distance_m=sub(distance), duration_s=sub(duration),
                    dispatcher_route=[local[src] for src in stops])


def _concorde_tour(folder: Path, trip_id: str, stops: list[int]) -> list[int]:
    """Cached Concorde tour of the trip in the new local ids (stops only, depot removed), [] if absent."""
    sol, mapping = folder / f"{trip_id}.sol", folder / f"{trip_id}.map.csv"
    if not (sol.is_file() and mapping.is_file()):
        return []
    from app.services.solvers.concorde import parse_tour, rotate_to_depot   # local import: avoids a cycle
    with open(mapping, newline="") as fh:
        to_source = {int(r["local_id"]): int(r["node_id"]) for r in csv.DictReader(fh)}
    tour = [to_source[k] for k in rotate_to_depot(parse_tour(sol.read_text()))]
    local = {src: k for k, src in enumerate([c.DEPOT_NODE_ID] + sorted(stops))}
    return [local[src] for src in tour[1:]]


def assign_messages(instance: Instance, anchor_route: list[int], seed: str | int) -> None:
    """One bank message per stop; intervals contain the clock hour at which `anchor_route` reaches the stop."""
    rng = random.Random(seed)
    bank = corpus.load_bank()
    timing = schedule.build(instance, anchor_route, {})
    anchor = {v.node: min(v.clock_h, c.WORKING_DAY_END_H - 0.1) for v in timing.visits}
    for node in instance.stops:
        category = corpus.draw_category(rng)
        message = corpus.message_for(category, rng, anchor[node.id] if category not in ("flexible", "none") else None, bank)
        node.message, node.band, node.message_id = message.text, message.category, message.message_id
        node.ref_start_h, node.ref_end_h = message.start_h, message.end_h


# ----------------------------------------------------------------------------- instance files

def list_instances(folder: Path | None = None) -> list[str]:
    folder = folder or get_settings().instances_dir
    if not folder.is_dir():
        return []
    return sorted(p.name for p in folder.iterdir() if p.is_dir() and (p / c.NODES_FILE).is_file())


def instance_dir(instance_id: str) -> Path:
    return get_settings().instances_dir / instance_id


def load_instance(instance_id: str, folder: Path | None = None) -> Instance:
    folder = (folder or get_settings().instances_dir) / instance_id
    if not (folder / c.NODES_FILE).is_file():
        raise FileNotFoundError(f"Unknown instance '{instance_id}' ({folder})")
    with open(folder / c.NODES_FILE, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    nodes = [Node(id=int(r["id"]), lat=float(r["lat"]), lon=float(r["lon"]), message=r["message"], band=r["band"] or "none",
                  ref_start_h=float(r["ref_start_h"]) if r["ref_start_h"] else None,
                  ref_end_h=float(r["ref_end_h"]) if r["ref_end_h"] else None,
                  message_id=int(r["message_id"]) if r["message_id"] else None,
                  stop_seq=int(r["stop_seq"]) if r["stop_seq"] else None) for r in rows]
    ordered = sorted((n for n in nodes if n.stop_seq is not None), key=lambda n: n.stop_seq)
    return Instance(id=instance_id, nodes=nodes, distance_m=_read_matrix(folder / c.DISTANCE_FILE),
                    duration_s=_read_matrix(folder / c.DURATION_FILE), dispatcher_route=[n.id for n in ordered])


def write_instance(folder: Path, instance: Instance) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    with open(folder / c.NODES_FILE, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["id", "lat", "lon", "stop_seq", "message_id", "band", "ref_start_h", "ref_end_h", "message"])
        for n in instance.nodes:
            writer.writerow([n.id, n.lat, n.lon, n.stop_seq if n.stop_seq is not None else "",
                             n.message_id if n.message_id is not None else "", n.band if not n.is_depot else "",
                             n.ref_start_h if n.ref_start_h is not None else "", n.ref_end_h if n.ref_end_h is not None else "",
                             n.message])
    _write_matrix(folder / c.DISTANCE_FILE, instance.distance_m)
    _write_matrix(folder / c.DURATION_FILE, instance.duration_s)


def concorde_tour(instance_id: str) -> list[int] | None:
    path = instance_dir(instance_id) / c.CONCORDE_TOUR_FILE
    return [int(t) for t in path.read_text().split()] if path.is_file() else None


def _read_matrix(path: Path) -> list[list[int]]:
    """Labelled square matrix: header 'id,0,1,...' and the node id as first column of every row."""
    with open(path, newline="") as fh:
        rows = [row for row in csv.reader(fh) if row]
    return [[int(float(v)) for v in row[1:]] for row in rows[1:]]


def _write_matrix(path: Path, matrix: list[list[int]]) -> None:
    with open(path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["id", *range(len(matrix))])
        for i, row in enumerate(matrix):
            writer.writerow([i, *row])
