"""OR-Tools baseline: the TSP with hard time windows, soft preferences ignored.

The routing model has one vehicle, the monetary objective of the paper (distance cost on
the arcs, time cost on the span of the time dimension, so that waiting is paid like
driving) and a time window on every stop whose preference is binding. The search starts
from the route of the adaptive construction, which is window-feasible by construction, and
improves it by guided local search within the time limit. Time runs on the
working-time line of schedule.py; a window is therefore the union of one interval per
working day of the horizon, expressed by removing the gaps from the domain of the time
variable of the stop. Soft preferences are not part of the model, which is what a
conventional solver would receive when only the explicit constraints are encoded.
"""

from __future__ import annotations

import math

from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from app import constants as c
from app.models import Instance, Preference
from app.services import schedule
from app.services.schedule import S_PER_H, SERVICE_H
from app.services.solvers.adaptive import adaptive_route
from app.services.solvers.base import BaseSolver

SERVICE_S = int(SERVICE_H * S_PER_H)
DAY_S = int(c.WORKING_DAY_HOURS * S_PER_H)
LNS_STEP_LIMIT_S = 5      # one large-neighbourhood step; the 100 ms default aborts the search on 1000-stop models


class OrToolsWindowsSolver(BaseSolver):
    name = "ortools"
    description = "OR-Tools TSP with hard time windows (binding customers), monetary objective, soft preferences ignored"
    uses_windows = True

    def build_route(self, instance: Instance, preferences: dict[int, Preference], **params) -> list[int]:
        time_limit = int(params.get("time_limit_s", c.ORTOOLS_TIME_LIMIT_S))
        return solve_windows(instance, preferences, time_limit)


def solve_windows(instance: Instance, preferences: dict[int, Preference], time_limit_s: int) -> list[int]:
    """Guided local search from a window-feasible seed route (the adaptive construction), within the time limit."""
    n = instance.size
    seed = adaptive_route(instance, preferences)
    horizon_s = horizon_seconds(instance, seed, preferences)
    manager = pywrapcp.RoutingIndexManager(n, 1, c.DEPOT_NODE_ID)
    routing = pywrapcp.RoutingModel(manager)

    def distance_cost(from_index: int, to_index: int) -> int:
        i, j = manager.IndexToNode(from_index), manager.IndexToNode(to_index)
        return int(round(c.COST_PER_KM_RON * instance.distance_m[i][j] / 1000 * c.COST_SCALE))

    def transit(from_index: int, to_index: int) -> int:
        i, j = manager.IndexToNode(from_index), manager.IndexToNode(to_index)
        return instance.duration_s[i][j] + (0 if i == c.DEPOT_NODE_ID else SERVICE_S)

    routing.SetArcCostEvaluatorOfAllVehicles(routing.RegisterTransitCallback(distance_cost))
    routing.AddDimension(routing.RegisterTransitCallback(transit), horizon_s, horizon_s, True, "Time")
    time_dim = routing.GetDimensionOrDie("Time")
    time_dim.SetSpanCostCoefficientForAllVehicles(int(round(c.COST_PER_HOUR_RON / S_PER_H * c.COST_SCALE)))
    for node, pref in preferences.items():
        if pref.hard and pref.has_window:
            _apply_window(time_dim.CumulVar(manager.NodeToIndex(node)), pref, horizon_s)

    search = pywrapcp.DefaultRoutingSearchParameters()
    search.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search.time_limit.FromSeconds(time_limit_s)
    search.lns_time_limit.FromSeconds(LNS_STEP_LIMIT_S)
    routing.CloseModelWithParameters(search)
    initial = routing.ReadAssignmentFromRoutes([seed], True)
    assignment = routing.SolveFromAssignmentWithParameters(initial, search) if initial is not None else routing.SolveWithParameters(search)
    if assignment is None:
        raise RuntimeError(f"OR-Tools found no feasible route for {instance.id} within {time_limit_s} s")
    route, index = [], routing.Start(0)
    while not routing.IsEnd(index):
        node = manager.IndexToNode(index)
        if node != c.DEPOT_NODE_ID:
            route.append(node)
        index = assignment.Value(routing.NextVar(index))
    return route


def horizon_seconds(instance: Instance, seed: list[int], preferences: dict[int, Preference]) -> int:
    """Working days available to the model: twice the duration of the seed route, plus two days."""
    duration_s = schedule.build(instance, seed, preferences).duration_h * S_PER_H
    return (2 * math.ceil(duration_s / DAY_S) + 2) * DAY_S


def _apply_window(cumul, pref: Preference, horizon_s: int) -> None:
    """Restrict the time variable to [start, end] of the window on every working day of the horizon."""
    open_s = int(round((pref.start_h - c.WORKING_DAY_START_H) * S_PER_H))
    close_s = int(round((pref.end_h - c.WORKING_DAY_START_H) * S_PER_H))
    if close_s >= DAY_S:
        close_s = DAY_S - 1          # 17:00 exactly belongs to the next morning on the working-time line
    days = horizon_s // DAY_S
    if open_s > 0:
        cumul.RemoveInterval(0, open_s - 1)
    for k in range(days):
        gap_start, gap_end = k * DAY_S + close_s + 1, (k + 1) * DAY_S + open_s - 1
        if gap_start <= gap_end:
            cumul.RemoveInterval(gap_start, min(gap_end, horizon_s))
