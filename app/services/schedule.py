"""Timing of a route on the working-time line and the cost terms derived from it.

Time is measured in working hours since the departure from the depot at the start of the
working day (08:00). The line contains working hours only: hour H (the length of the working
day) is the start of the next day, so `clock(t)` returns the wall-clock hour of any instant.

Along a route the vehicle drives (travel time), unloads (service time) and waits only for the
hard windows of binding customers: when it arrives before the window opens it waits for the
opening, when it arrives after the window closed it waits for the opening on the next day
(a failed delivery, re-attempted in the morning). Soft preferences never cause waiting; the
deviation of the arrival time from the preferred interval is the preference violation p_i.
"""

from __future__ import annotations

from pydantic import BaseModel

from app import constants as c
from app.models import Instance, Preference

S_PER_H = 3600.0
M_PER_KM = 1000.0
SERVICE_H = c.SERVICE_TIME_MIN / 60


class Visit(BaseModel):
    node: int
    arrival_h: float      # on the working-time line
    wait_h: float
    clock_h: float        # wall-clock hour of the delivery start
    day: int              # 1-based working day of the delivery


class Schedule(BaseModel):
    route: list[int]
    visits: list[Visit]
    distance_km: float
    duration_h: float     # working time from departure to return, waiting included
    waiting_h: float


def clock(t: float) -> float:
    return c.WORKING_DAY_START_H + t % c.WORKING_DAY_HOURS


def day_of(t: float) -> int:
    return int(t // c.WORKING_DAY_HOURS) + 1


def wait_for_window(t: float, start_h: float, end_h: float) -> float:
    """Working hours to wait at instant t so that the delivery starts inside [start_h, end_h]."""
    hour = clock(t)
    if start_h <= hour <= end_h:
        return 0.0
    if hour < start_h:
        return start_h - hour
    return (c.WORKING_DAY_END_H - hour) + (start_h - c.WORKING_DAY_START_H)   # next morning


def violation_h(hour: float, preference: Preference) -> float:
    """Distance, in hours, from the delivery hour to the preferred interval (0 inside it)."""
    if not preference.has_window:
        return 0.0
    return max(0.0, preference.start_h - hour) + max(0.0, hour - preference.end_h)


def build(instance: Instance, route: list[int], preferences: dict[int, Preference]) -> Schedule:
    """Timing of `route` when the vehicle honours the hard windows in `preferences` by waiting."""
    t, distance_m, waiting, visits = 0.0, 0, 0.0, []
    previous = c.DEPOT_NODE_ID
    for node in route:
        distance_m += instance.distance_m[previous][node]
        t += instance.duration_s[previous][node] / S_PER_H
        pref = preferences.get(node)
        wait = wait_for_window(t, pref.start_h, pref.end_h) if pref is not None and pref.hard and pref.has_window else 0.0
        t += wait
        waiting += wait
        visits.append(Visit(node=node, arrival_h=t - wait, wait_h=wait, clock_h=clock(t), day=day_of(t)))
        t += SERVICE_H
        previous = node
    distance_m += instance.distance_m[previous][c.DEPOT_NODE_ID]
    t += instance.duration_s[previous][c.DEPOT_NODE_ID] / S_PER_H
    return Schedule(route=list(route), visits=visits, distance_km=distance_m / M_PER_KM, duration_h=t, waiting_h=waiting)


def penalty_h(schedule: Schedule, preferences: dict[int, Preference]) -> float:
    """Urgency-weighted preference violation, sum_i u_i * p_i, in hours."""
    return sum(preferences[v.node].urgency * violation_h(v.clock_h, preferences[v.node])
               for v in schedule.visits if v.node in preferences)


def monetary_cost_ron(schedule: Schedule) -> float:
    return c.COST_PER_KM_RON * schedule.distance_km + c.COST_PER_HOUR_RON * schedule.duration_h


def composite_cost_ron(schedule: Schedule, preferences: dict[int, Preference],
                       penalty_per_hour: float = c.PENALTY_PER_HOUR_RON) -> float:
    return monetary_cost_ron(schedule) + penalty_per_hour * penalty_h(schedule, preferences)
