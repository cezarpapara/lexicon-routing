import pytest

from app import constants as c
from app.models import Preference, Solution
from app.services import corpus, extractors, metrics, schedule
from app.services.solvers.guided import LocalSearch


def test_clock_wraps_to_the_next_working_day():
    assert schedule.clock(0.0) == 8.0
    assert schedule.clock(8.5) == 16.5
    assert schedule.clock(9.0) == 8.0 and schedule.day_of(9.0) == 2


def test_waiting_for_hard_windows():
    assert schedule.wait_for_window(1.0, 10.0, 12.0) == pytest.approx(1.0)       # 09:00 -> wait until 10:00
    assert schedule.wait_for_window(3.0, 10.0, 12.0) == 0.0                      # 11:00 inside
    assert schedule.wait_for_window(6.0, 10.0, 12.0) == pytest.approx(3.0 + 2.0)  # 14:00 -> next day 10:00


def test_violation_is_distance_to_interval():
    pref = Preference(start_h=10.0, end_h=12.0, urgency=0.5)
    assert schedule.violation_h(9.0, pref) == 1.0
    assert schedule.violation_h(11.0, pref) == 0.0
    assert schedule.violation_h(12.5, pref) == 0.5
    assert schedule.violation_h(12.5, Preference()) == 0.0


def test_schedule_waits_only_for_hard_windows(instance):
    prefs = {1: Preference(start_h=10.0, end_h=12.0, urgency=1.0, band="binding", hard=True),
             2: Preference(start_h=13.0, end_h=17.0, urgency=0.5, band="strong", hard=False)}
    timing = schedule.build(instance, [1, 2], prefs)
    assert timing.visits[0].clock_h == pytest.approx(10.0)          # waited for the window to open
    assert timing.waiting_h > 0
    assert timing.visits[1].wait_h == 0.0                            # soft preference: no waiting


def test_composite_cost_matches_local_search_objective(instance):
    prefs = extractors.lexicon_preferences(instance)
    route = instance.dispatcher_route
    expected = schedule.composite_cost_ron(schedule.build(instance, route, prefs), prefs)
    assert LocalSearch(instance, prefs).cost(route) == pytest.approx(expected)


def test_evaluation_against_references(instance):
    prefs = extractors.lexicon_preferences(instance)
    solution = Solution(solver="x", instance_id=instance.id, route=instance.dispatcher_route, preferences=prefs)
    evaluation = metrics.evaluate(instance, solution, corpus.references(instance))
    assert evaluation.stated == 6 and 0 <= evaluation.met <= 6
    assert evaluation.composite_cost_ron == pytest.approx(
        evaluation.monetary_cost_ron + c.PENALTY_PER_HOUR_RON * evaluation.penalty_h, abs=0.05)
    assert set(evaluation.by_band) == set(c.BANDS)
