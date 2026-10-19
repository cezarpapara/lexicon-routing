"""Evaluation of a route against the reference preferences (what the customers actually meant).

Every route is timed by schedule.py with the preferences its solver was given (so that the
vehicle waits for the windows the solver treated as hard) and then scored against the
reference preferences of the instance:

    D  distance [km]                       T  working time incl. waiting [h]
    C_m = c_d D + c_t T                    monetary cost [RON]
    P = sum_i u_i p_i                      urgency-weighted violation [h], reference u_i
    C = C_m + lambda P                     composite cost [RON]

plus the share of stated intervals that are met (overall and per band) and the number of
binding preferences missed, which can only happen when the extractor did not recognise
them as binding.
"""

from __future__ import annotations

from pydantic import BaseModel

from app import constants as c
from app.models import Instance, Preference, Solution
from app.services import schedule


class BandStats(BaseModel):
    stated: int
    met: int


class Evaluation(BaseModel):
    solver: str
    instance_id: str
    stops: int
    distance_km: float
    duration_h: float
    waiting_h: float
    days: int
    monetary_cost_ron: float
    penalty_h: float
    composite_cost_ron: float
    stated: int                 # stops whose reference preference states an interval
    met: int                    # ... of which the delivery falls inside it
    satisfaction_pct: float
    by_band: dict[str, BandStats]
    binding_missed: int
    runtime_s: float


def evaluate(instance: Instance, solution: Solution, references: dict[int, Preference],
             penalty_per_hour: float = c.PENALTY_PER_HOUR_RON) -> Evaluation:
    timing = schedule.build(instance, solution.route, solution.preferences)
    by_band = {band: BandStats(stated=0, met=0) for band in c.BANDS}
    penalty, binding_missed = 0.0, 0
    for visit in timing.visits:
        ref = references[visit.node]
        if not ref.has_window:
            continue
        p = schedule.violation_h(visit.clock_h, ref)
        penalty += ref.urgency * p
        by_band[ref.band].stated += 1
        by_band[ref.band].met += p == 0
        binding_missed += ref.band == c.HARD_BAND and p > 0
    stated = sum(b.stated for b in by_band.values())
    met = sum(b.met for b in by_band.values())
    monetary = schedule.monetary_cost_ron(timing)
    return Evaluation(
        solver=solution.solver, instance_id=instance.id, stops=len(solution.route),
        distance_km=round(timing.distance_km, 2), duration_h=round(timing.duration_h, 2),
        waiting_h=round(timing.waiting_h, 2), days=max((v.day for v in timing.visits), default=1),
        monetary_cost_ron=round(monetary, 2), penalty_h=round(penalty, 2),
        composite_cost_ron=round(monetary + penalty_per_hour * penalty, 2),
        stated=stated, met=met, satisfaction_pct=round(100 * met / stated, 1) if stated else 100.0,
        by_band=by_band, binding_missed=binding_missed, runtime_s=round(solution.runtime_s, 2),
    )
