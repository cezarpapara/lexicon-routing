from __future__ import annotations

import time
from abc import ABC, abstractmethod

from app.models import Instance, Preference, Solution


class BaseSolver(ABC):
    """Every solver turns an instance and the extracted preferences into one route.

    `uses_windows` documents what the method can see: distance-only methods ignore the
    preferences entirely, window-aware methods honour the hard windows, and the proposed
    method also uses the soft preferences and their urgency.
    """

    name: str
    description: str = ""
    uses_windows: bool = False
    uses_soft: bool = False
    read_only: bool = False   # True = replays a recorded decision, cannot plan new instances

    @abstractmethod
    def build_route(self, instance: Instance, preferences: dict[int, Preference], **params) -> list[int]:
        """Return the stop ids in visiting order (depot excluded)."""

    def solve(self, instance: Instance, preferences: dict[int, Preference], **params) -> Solution:
        start = time.perf_counter()
        route = self.build_route(instance, preferences, **params)
        if sorted(route) != [n.id for n in instance.stops]:
            raise ValueError(f"{self.name}: route {route} is not a permutation of the stops of {instance.id}")
        return Solution(solver=self.name, instance_id=instance.id, route=route, preferences=preferences,
                        runtime_s=time.perf_counter() - start, params=params)

    def info(self) -> dict:
        return {"name": self.name, "description": self.description, "uses_windows": self.uses_windows,
                "uses_soft": self.uses_soft, "read_only": self.read_only}


class SolverRegistry:
    _solvers: dict[str, BaseSolver] = {}

    @classmethod
    def register(cls, solver: BaseSolver) -> None:
        cls._solvers[solver.name] = solver

    @classmethod
    def get(cls, name: str) -> BaseSolver:
        if name not in cls._solvers:
            raise KeyError(f"Unknown solver '{name}'. Available: {sorted(cls._solvers)}")
        return cls._solvers[name]

    @classmethod
    def all(cls) -> dict[str, BaseSolver]:
        return dict(cls._solvers)
