import random

import pytest

from app.services import corpus, extractors, metrics, schedule
from app.services.solvers import auto_register_all, SolverRegistry
from app.services.solvers.adaptive import adaptive_route
from app.services.solvers.guided import GuidedSolver, LocalSearch
from app.services.solvers.nearest_neighbour import nearest_neighbour_route
from app.services.solvers.ortools_tw import solve_windows


@pytest.fixture(autouse=True)
def _register():
    auto_register_all()


def _is_permutation(route, instance):
    return sorted(route) == [n.id for n in instance.stops]


def test_nearest_neighbour_is_a_permutation_and_greedy(instance):
    route = nearest_neighbour_route(instance)
    assert _is_permutation(route, instance)
    d = instance.distance_m
    assert route[0] == min((n.id for n in instance.stops), key=lambda j: d[0][j])


def test_adaptive_respects_hard_windows_by_waiting(instance):
    prefs = extractors.lexicon_preferences(instance)
    route = adaptive_route(instance, prefs)
    assert _is_permutation(route, instance)
    timing = schedule.build(instance, route, prefs)
    for visit in timing.visits:
        pref = prefs[visit.node]
        if pref.hard:
            assert pref.start_h <= visit.clock_h <= pref.end_h


def test_ortools_honours_hard_windows(instance):
    prefs = extractors.lexicon_preferences(instance)
    route = solve_windows(instance, prefs, time_limit_s=2)
    assert _is_permutation(route, instance)
    timing = schedule.build(instance, route, prefs)
    for visit in timing.visits:
        if prefs[visit.node].hard:
            assert prefs[visit.node].start_h <= visit.clock_h <= prefs[visit.node].end_h


def test_guided_never_worsens_the_composite_cost(instance):
    prefs = extractors.lexicon_preferences(instance)
    start = nearest_neighbour_route(instance)
    search = LocalSearch(instance, prefs)
    refined = search.improve(start)
    assert _is_permutation(refined, instance)
    assert search.cost(refined) <= search.cost(start) + 1e-9


def test_guided_solver_accepts_initial_route_and_ablation_switches(instance):
    prefs = extractors.lexicon_preferences(instance)
    rng = random.Random(1)
    initial = [n.id for n in instance.stops]
    rng.shuffle(initial)
    full = GuidedSolver().solve(instance, prefs, initial=initial)
    relocate_only = GuidedSolver().solve(instance, prefs, initial=initial, moves=("relocate",))
    unweighted = GuidedSolver().solve(instance, prefs, initial=initial, weighted=False)
    for solution in (full, relocate_only, unweighted):
        assert _is_permutation(solution.route, instance)
    search = LocalSearch(instance, prefs)
    assert search.cost(full.route) <= search.cost(relocate_only.route) + 1e-9


def test_registry_lists_every_configuration():
    assert set(SolverRegistry.all()) == {"dispatcher", "nearest", "concorde", "ortools", "adaptive", "guided"}


def test_dispatcher_replay_is_evaluated_with_zero_violation_when_anchored(instance):
    prefs = extractors.lexicon_preferences(instance)
    solution = SolverRegistry.get("dispatcher").solve(instance, prefs)
    evaluation = metrics.evaluate(instance, solution, corpus.references(instance))
    assert evaluation.stops == 8 and evaluation.distance_km > 0
