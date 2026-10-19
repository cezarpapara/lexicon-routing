"""All configurations on one instance, evaluated against the reference preferences and stored as a run."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

from app import constants as c
from app.config import get_settings
from app.models import Instance, Preference, Solution
from app.services import corpus, data, extractors, metrics
from app.services.metrics import Evaluation
from app.services.solvers import CONCORDE, DISPATCHER, GUIDED, ORDER, ORTOOLS, SolverRegistry
from app.services.solvers.guided import MOVES, LocalSearch


class BenchmarkResult(BaseModel):
    run_id: str
    instance_id: str
    extractor: str
    stops: int
    evaluations: list[Evaluation]
    solutions: list[Solution]
    skipped: dict[str, str]


def run(instance_id: str, extractor: str = extractors.LEXICON, solvers: tuple[str, ...] = ORDER,
        time_limit_s: int = c.ORTOOLS_TIME_LIMIT_S, penalty_per_hour: float = c.PENALTY_PER_HOUR_RON) -> BenchmarkResult:
    instance = data.load_instance(instance_id)
    preferences = extractors.preferences(instance, extractor)
    references = corpus.references(instance)
    evaluations, solutions, skipped = [], [], {}
    baseline: Solution | None = None
    for name in solvers:
        try:
            solution = _solve(name, instance, preferences, baseline, time_limit_s, penalty_per_hour)
        except (ValueError, FileNotFoundError, RuntimeError, OSError) as exc:
            skipped[name] = str(exc)
            continue
        if name == ORTOOLS:
            baseline = solution
        solutions.append(solution)
        evaluations.append(metrics.evaluate(instance, solution, references, penalty_per_hour))
    result = BenchmarkResult(run_id=f"{datetime.now():%Y%m%d_%H%M%S}_{instance_id}", instance_id=instance_id,
                             extractor=extractor, stops=len(instance.stops), evaluations=evaluations,
                             solutions=solutions, skipped=skipped)
    _save(result)
    return result


def _solve(name: str, instance: Instance, preferences: dict[int, Preference], baseline: Solution | None,
           time_limit_s: int, penalty_per_hour: float) -> Solution:
    solver = SolverRegistry.get(name)
    if name == ORTOOLS:
        return solver.solve(instance, preferences, time_limit_s=time_limit_s)
    if name == GUIDED:
        return solve_guided(instance, preferences, baseline, penalty_per_hour, time_limit_s)
    if name == CONCORDE and not (data.instance_dir(instance.id) / c.CONCORDE_TOUR_FILE).is_file():
        raise FileNotFoundError(f"no Concorde tour cached for {instance.id}: run `concorde {instance.id}` first (NEOS)")
    return solver.solve(instance, preferences)


def solve_guided(instance: Instance, preferences: dict[int, Preference], baseline: Solution | None,
                 penalty_per_hour: float = c.PENALTY_PER_HOUR_RON, time_limit_s: int = c.ORTOOLS_TIME_LIMIT_S, **params) -> Solution:
    """Algorithm 1 from the solver's route and, when recorded, from the dispatcher's; the better local optimum is kept."""
    solver = SolverRegistry.get(GUIDED)
    starts = {"ortools": baseline if baseline is not None else SolverRegistry.get(ORTOOLS).solve(instance, preferences, time_limit_s=time_limit_s)}
    if instance.dispatcher_route:
        starts["dispatcher"] = SolverRegistry.get(DISPATCHER).solve(instance, preferences)
    search = LocalSearch(instance, preferences, penalty_per_hour=penalty_per_hour, moves=params.get("moves", MOVES),
                         ranked=params.get("ranked", True), weighted=params.get("weighted", True))
    best, best_cost, best_start, runtime = None, float("inf"), None, 0.0
    for start, initial in starts.items():
        solution = solver.solve(instance, preferences, initial=initial, penalty_per_hour=penalty_per_hour, **params)
        runtime += solution.runtime_s
        cost = search.cost(solution.route)
        if cost < best_cost:
            best, best_cost, best_start = solution, cost, start
    return best.model_copy(update={"runtime_s": runtime, "params": {**best.params, "start": best_start}})


def _save(result: BenchmarkResult) -> Path:
    folder = get_settings().results_dir / result.run_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "benchmark.json").write_text(result.model_dump_json(indent=2))
    return folder


def list_results() -> list[str]:
    folder = get_settings().results_dir
    if not folder.is_dir():
        return []
    return sorted(p.name for p in folder.iterdir() if (p / "benchmark.json").is_file())


def load_result(run_id: str) -> BenchmarkResult:
    path = get_settings().results_dir / run_id / "benchmark.json"
    if not path.is_file():
        raise FileNotFoundError(f"Unknown run '{run_id}'")
    return BenchmarkResult.model_validate_json(path.read_text())


def latest_runs(instance_ids: list[str] | None = None) -> dict[str, str]:
    """Latest benchmark run per instance (instance id -> run id)."""
    latest = {}
    for run_id in list_results():
        instance_id = run_id.split("_", 2)[2]
        if instance_ids is None or instance_id in instance_ids:
            latest[instance_id] = run_id
    return latest

