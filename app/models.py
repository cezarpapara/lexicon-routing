"""Domain models shared by data loading, extraction, solvers, metrics and the API."""

from __future__ import annotations

from functools import cached_property

from pydantic import BaseModel, Field

from app import constants as c


class Preference(BaseModel):
    """Temporal preference of one customer: an interval in clock hours and an urgency in [0, 1].

    `start_h`/`end_h` are None when the message states no interval. `hard` marks a binding
    preference, enforced as a time window; every other preference is soft and only penalised.
    """

    start_h: float | None = None
    end_h: float | None = None
    urgency: float = 0.0
    band: str = "flexible"
    hard: bool = False

    @property
    def has_window(self) -> bool:
        return self.start_h is not None and self.end_h is not None

    @classmethod
    def none(cls) -> "Preference":
        return cls()


class Node(BaseModel):
    """Depot (id 0) or customer stop (id >= 1). Node ids are 0-based, as in Concorde.

    The reference fields (`band`, `ref_start_h`, `ref_end_h`) are the labels under which the
    message was written; they are the ground truth of the evaluation and are never read by the
    solvers, which only see what an extractor derives from `message`.
    """

    id: int
    lat: float
    lon: float
    message: str = ""
    band: str = "none"
    ref_start_h: float | None = None
    ref_end_h: float | None = None
    message_id: int | None = None      # bank message the text was instantiated from
    stop_seq: int | None = None        # dispatcher's position, real trips only

    @property
    def is_depot(self) -> bool:
        return self.id == c.DEPOT_NODE_ID

    def reference(self) -> Preference:
        return Preference(start_h=self.ref_start_h, end_h=self.ref_end_h, urgency=c.BAND_URGENCY[self.band],
                          band=self.band, hard=self.band == c.HARD_BAND)


class Instance(BaseModel):
    id: str
    nodes: list[Node]
    distance_m: list[list[int]]   # symmetric road distances, metres
    duration_s: list[list[int]]   # symmetric road travel times, seconds
    dispatcher_route: list[int] = Field(default_factory=list)   # stop ids in executed order, real trips only

    @cached_property
    def stops(self) -> list[Node]:
        return [n for n in self.nodes if not n.is_depot]

    @property
    def size(self) -> int:
        return len(self.nodes)

    def node(self, node_id: int) -> Node:
        return self.nodes[node_id]

    def references(self) -> dict[int, Preference]:
        return {n.id: n.reference() for n in self.stops}


class Solution(BaseModel):
    """One depot-to-depot route with the preferences the solver was given (needed to replay its schedule)."""

    solver: str
    instance_id: str
    route: list[int]
    preferences: dict[int, Preference] = Field(default_factory=dict)
    runtime_s: float = 0.0
    params: dict = Field(default_factory=dict)
