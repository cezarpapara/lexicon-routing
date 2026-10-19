"""The dispatcher's executed sequence, replayed as recorded (real trips only)."""

from __future__ import annotations

from app.models import Instance, Preference
from app.services.solvers.base import BaseSolver


class DispatcherSolver(BaseSolver):
    name = "dispatcher"
    description = "Stops in the order executed by the store dispatcher (manual plan)"
    read_only = True

    def build_route(self, instance: Instance, preferences: dict[int, Preference], **params) -> list[int]:
        if not instance.dispatcher_route:
            raise ValueError(f"{instance.id} has no dispatcher sequence (synthetic instance)")
        return list(instance.dispatcher_route)
