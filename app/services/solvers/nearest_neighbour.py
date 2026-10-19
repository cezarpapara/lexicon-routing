"""Nearest-neighbour construction: from the depot, always drive to the closest unvisited stop."""

from __future__ import annotations

from app import constants as c
from app.models import Instance, Preference
from app.services.solvers.base import BaseSolver


class NearestNeighbourSolver(BaseSolver):
    name = "nearest"
    description = "Nearest-neighbour tour on road distance (time-unaware greedy construction)"

    def build_route(self, instance: Instance, preferences: dict[int, Preference], **params) -> list[int]:
        return nearest_neighbour_route(instance)


def nearest_neighbour_route(instance: Instance, excluded: set[int] | None = None) -> list[int]:
    d = instance.distance_m
    unvisited = {n.id for n in instance.stops} - (excluded or set())
    route, current = [], c.DEPOT_NODE_ID
    while unvisited:
        current = min(unvisited, key=lambda j: (d[current][j], j))
        route.append(current)
        unvisited.remove(current)
    return route
