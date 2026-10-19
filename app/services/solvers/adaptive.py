"""The adaptive hybrid heuristic of Papară and Nimineț (2025), re-implemented from its pseudocode.

Nearest-neighbour construction with availability checks at the estimated arrival time:
when the closest unvisited stop is not available (its hard window is closed), the heuristic
waits for it as long as the waiting does not exceed the travel time to the second-closest
stop; beyond that it temporarily excludes the stop and moves on, clearing the exclusions
after every successful visit. The original waits in one-minute increments and jumps to the
next working day past closing time; on the working-time line the same waiting is obtained
in closed form (schedule.wait_for_window), which changes nothing in the decisions. The
heuristic sees hard windows only, as the original saw node unavailability.
"""

from __future__ import annotations

from app import constants as c
from app.models import Instance, Preference
from app.services.schedule import S_PER_H, SERVICE_H, wait_for_window
from app.services.solvers.base import BaseSolver


class AdaptiveSolver(BaseSolver):
    name = "adaptive"
    description = "Adaptive nearest-neighbour heuristic with availability checks (Papară & Nimineț, 2025), hard windows only"
    uses_windows = True

    def build_route(self, instance: Instance, preferences: dict[int, Preference], **params) -> list[int]:
        return adaptive_route(instance, preferences)


def adaptive_route(instance: Instance, preferences: dict[int, Preference]) -> list[int]:
    d, travel = instance.distance_m, instance.duration_s
    unvisited = {n.id for n in instance.stops}
    route, excluded, current, t = [], set(), c.DEPOT_NODE_ID, 0.0
    while unvisited:
        candidates = unvisited - excluded
        if not candidates:                     # everything left is excluded: start over from the current stop
            excluded.clear()
            candidates = set(unvisited)
        nearest = min(candidates, key=lambda j: (d[current][j], j))
        others = candidates - {nearest}
        second_travel_h = min(travel[current][j] for j in others) / S_PER_H if others else None
        arrival = t + travel[current][nearest] / S_PER_H
        wait = _wait(arrival, preferences.get(nearest))
        if second_travel_h is not None and wait > second_travel_h:
            excluded.add(nearest)              # too long to wait: try the next-closest stop first
            continue
        route.append(nearest)
        unvisited.remove(nearest)
        excluded.clear()
        current, t = nearest, arrival + wait + SERVICE_H
    return route


def _wait(arrival: float, pref: Preference | None) -> float:
    if pref is None or not (pref.hard and pref.has_window):
        return 0.0
    return wait_for_window(arrival, pref.start_h, pref.end_h)
