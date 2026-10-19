"""Lexicon-guided route refinement (Algorithm 1 of the paper).

The baseline route of the window-aware solver is refined under the composite cost
    C = c_d * D + c_t * T + lambda * sum_i u_i * p_i,
where the urgency u_i and the preferred interval of every stop come from the extractor.
Each pass ranks the stops by their weighted violation u_i * p_i, so that the search first
moves the stops that contribute most to the penalty; every candidate is relocated to the
positions next to its nearest neighbours (all positions on small instances) and the first
improving relocation is accepted. When no relocation improves the cost the best pairwise
swap of a candidate with a neighbour is tried. A pass ends with a cost-driven phase, a
2-opt sweep under the same composite cost, which removes detours the preference moves
left behind. Hard windows are honoured by construction, since the schedule of every
candidate route waits for them, so no separate feasibility filter is needed. The search
stops at a local optimum or after MAX_PASSES passes. When a manual plan exists the search
is run from it as well as from the solver's route, and the better local optimum is kept.
"""

from __future__ import annotations

import time

from app import constants as c
from app.models import Instance, Preference, Solution
from app.services.schedule import S_PER_H, SERVICE_H
from app.services.solvers.base import BaseSolver
from app.services.solvers.ortools_tw import OrToolsWindowsSolver

MOVES = ("relocate", "swap", "two_opt")


class GuidedSolver(BaseSolver):
    name = "guided"
    description = "Proposed: OR-Tools baseline refined by a lexicon-guided local search on the composite cost (relocate, swap, 2-opt)"
    uses_windows = True
    uses_soft = True

    def solve(self, instance: Instance, preferences: dict[int, Preference], **params) -> Solution:
        """Accepts `initial` (a Solution or a route) besides the ablation switches of LocalSearch."""
        initial = params.pop("initial", None)
        if initial is None:
            initial = OrToolsWindowsSolver().solve(instance, preferences, time_limit_s=params.get("time_limit_s", c.ORTOOLS_TIME_LIMIT_S)).route
        self._initial = list(initial.route if isinstance(initial, Solution) else initial)
        return super().solve(instance, preferences, **params)

    def build_route(self, instance: Instance, preferences: dict[int, Preference], **params) -> list[int]:
        search = LocalSearch(instance, preferences, penalty_per_hour=params.get("penalty_per_hour", c.PENALTY_PER_HOUR_RON),
                             moves=params.get("moves", MOVES), ranked=params.get("ranked", True),
                             weighted=params.get("weighted", True), time_limit_s=params.get("search_time_limit_s", c.SEARCH_TIME_LIMIT_S))
        return search.improve(self._initial)


class LocalSearch:
    def __init__(self, instance: Instance, preferences: dict[int, Preference], penalty_per_hour: float = c.PENALTY_PER_HOUR_RON,
                 moves: tuple[str, ...] = MOVES, ranked: bool = True, weighted: bool = True, time_limit_s: float | None = None):
        self.instance = instance
        self.moves = tuple(moves)
        self.ranked = ranked               # ablation: candidates in route order instead of by u_i * p_i
        self.penalty_per_hour = penalty_per_hour
        self.deadline = time.perf_counter() + time_limit_s if time_limit_s else None
        n = instance.size
        self.d, self.t = instance.distance_m, instance.duration_s
        self.start = [None] * n
        self.end = [None] * n
        self.hard = [False] * n
        self.u = [0.0] * n
        for node, pref in preferences.items():
            if pref.has_window:
                self.start[node], self.end[node], self.hard[node] = pref.start_h, pref.end_h, pref.hard
                self.u[node] = pref.urgency if weighted else 1.0     # ablation: every stated interval weighs the same
        self.neighbours = _nearest_lists(instance, c.CANDIDATE_POSITIONS)

    # ------------------------------------------------------------------ driver

    def improve(self, route: list[int]) -> list[int]:
        best, best_cost = list(route), self.cost(route)
        for _ in range(c.MAX_PASSES):
            improved = False
            for node in self.candidates(best):
                if self._timed_out():
                    return best
                if "relocate" in self.moves:
                    result = self._first_improving_relocation(best, best_cost, node)
                    if result is not None:
                        best, best_cost, improved = *result, True
                        continue
                if "swap" in self.moves:
                    result = self._best_swap(best, best_cost, node)
                    if result is not None:
                        best, best_cost, improved = *result, True
            if "two_opt" in self.moves:
                result = self._first_improving_two_opt(best, best_cost)
                while result is not None and not self._timed_out():
                    best, best_cost, improved = *result, True
                    result = self._first_improving_two_opt(best, best_cost)
            if not improved:
                break
        return best

    def candidates(self, route: list[int]) -> list[int]:
        """Stops with a positive weighted violation, ranked by u_i * p_i (or in route order)."""
        violations = self.violations(route)
        nodes = [v for v in route if violations[v] > 0]
        return sorted(nodes, key=lambda v: -violations[v]) if self.ranked else nodes

    # ------------------------------------------------------------------ moves

    def _first_improving_relocation(self, route: list[int], route_cost: float, node: int) -> tuple[list[int], float] | None:
        without = [v for v in route if v != node]
        for position in self._positions(without, node):
            candidate = without[:position] + [node] + without[position:]
            cost = self.cost(candidate)
            if cost < route_cost - 1e-9:
                return candidate, cost
        return None

    def _best_swap(self, route: list[int], route_cost: float, node: int) -> tuple[list[int], float] | None:
        index = {v: k for k, v in enumerate(route)}
        best, best_cost = None, route_cost - 1e-9
        for other in self._swap_partners(node):
            candidate = list(route)
            candidate[index[node]], candidate[index[other]] = other, node
            cost = self.cost(candidate)
            if cost < best_cost:
                best, best_cost = candidate, cost
        return (best, best_cost) if best is not None else None

    def _first_improving_two_opt(self, route: list[int], route_cost: float) -> tuple[list[int], float] | None:
        """Reverse the segment between two edges; on large instances only edges towards near neighbours."""
        path = [c.DEPOT_NODE_ID, *route, c.DEPOT_NODE_ID]
        index = {v: k for k, v in enumerate(path)}
        n = len(route)
        for i in range(n):
            partners = range(i + 1, n) if n < c.CANDIDATE_POSITIONS else sorted(index[w] for w in self.neighbours[path[i + 1]] if index[w] > i + 1)
            for j in partners:
                candidate = path[1:i + 1] + path[i + 1:j + 1][::-1] + path[j + 1:-1]
                cost = self.cost(candidate)
                if cost < route_cost - 1e-9:
                    return candidate, cost
        return None

    def _positions(self, without: list[int], node: int) -> list[int]:
        """Insertion positions: all of them on small instances, else right after each near neighbour and first."""
        if len(without) < c.CANDIDATE_POSITIONS:
            return list(range(len(without) + 1))
        index = {v: k for k, v in enumerate(without)}
        positions = {0} | {index[w] + 1 for w in self.neighbours[node] if w in index}
        return sorted(positions)

    def _swap_partners(self, node: int) -> list[int]:
        return self.neighbours[node]

    # ------------------------------------------------------------------ objective (schedule.py, without objects)

    def cost(self, route: list[int]) -> float:
        distance_m, t, penalty = 0, 0.0, 0.0
        previous = c.DEPOT_NODE_ID
        for node in route:
            distance_m += self.d[previous][node]
            t += self.t[previous][node] / S_PER_H
            hour = c.WORKING_DAY_START_H + t % c.WORKING_DAY_HOURS
            start, end = self.start[node], self.end[node]
            if start is not None:
                if self.hard[node]:
                    t += _wait(hour, start, end)
                elif self.u[node] > 0:
                    penalty += self.u[node] * (max(0.0, start - hour) + max(0.0, hour - end))
            t += SERVICE_H
            previous = node
        distance_m += self.d[previous][c.DEPOT_NODE_ID]
        t += self.t[previous][c.DEPOT_NODE_ID] / S_PER_H
        return c.COST_PER_KM_RON * distance_m / 1000 + c.COST_PER_HOUR_RON * t + self.penalty_per_hour * penalty

    def violations(self, route: list[int]) -> dict[int, float]:
        """u_i * p_i per stop; hard windows never contribute because the schedule waits for them."""
        result, t, previous = {}, 0.0, c.DEPOT_NODE_ID
        for node in route:
            t += self.t[previous][node] / S_PER_H
            hour = c.WORKING_DAY_START_H + t % c.WORKING_DAY_HOURS
            start, end = self.start[node], self.end[node]
            result[node] = 0.0
            if start is not None:
                if self.hard[node]:
                    t += _wait(hour, start, end)
                else:
                    result[node] = self.u[node] * (max(0.0, start - hour) + max(0.0, hour - end))
            t += SERVICE_H
            previous = node
        return result

    def _timed_out(self) -> bool:
        return self.deadline is not None and time.perf_counter() > self.deadline


def _wait(hour: float, start: float, end: float) -> float:
    if start <= hour <= end:
        return 0.0
    if hour < start:
        return start - hour
    return (c.WORKING_DAY_END_H - hour) + (start - c.WORKING_DAY_START_H)


def _nearest_lists(instance: Instance, k: int) -> dict[int, list[int]]:
    """The k stops closest to every stop (all of them when the instance is small)."""
    stops = [n.id for n in instance.stops]
    lists = {}
    for node in stops:
        others = sorted((s for s in stops if s != node), key=lambda s: instance.distance_m[node][s])
        lists[node] = others if len(stops) - 1 < k else others[:k]
    return lists
