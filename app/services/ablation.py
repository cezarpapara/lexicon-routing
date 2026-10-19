"""Ablation of the proposed method on one instance: one component removed or replaced at a time.

All variants are evaluated with the same reference preferences and the same penalty rate,
so that the differences come from the search alone: the moves (relocate / swap), the
ranking of the candidates, the urgency weighting, the extractor (lexicon / oracle / LLM),
the penalty rate used inside the search and the starting route.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app import constants as c
from app.config import get_settings
from app.models import Instance, Preference, Solution
from app.services import benchmark, corpus, data, extractors, metrics
from app.services.metrics import Evaluation
from app.services.solvers import DISPATCHER, NEAREST, ORTOOLS, SolverRegistry
from app.services.solvers.guided import GuidedSolver


class AblationResult(BaseModel):
    run_id: str
    instance_id: str
    variants: list[Evaluation]        # `solver` holds the variant name
    skipped: dict[str, str]


def run(instance_id: str, time_limit_s: int = c.ORTOOLS_TIME_LIMIT_S) -> AblationResult:
    instance = data.load_instance(instance_id)
    references = corpus.references(instance)
    lexicon_prefs = extractors.preferences(instance, extractors.LEXICON)
    baseline = SolverRegistry.get(ORTOOLS).solve(instance, lexicon_prefs, time_limit_s=time_limit_s)
    variants, skipped = [], {}

    def add(name: str, solution: Solution) -> None:
        evaluation = metrics.evaluate(instance, solution, references)
        variants.append(evaluation.model_copy(update={"solver": name}))

    add("OR-Tools baseline (no refinement)", baseline)
    add("Proposed, full", _guided(instance, lexicon_prefs, baseline))
    add("Start from OR-Tools only", _single(instance, lexicon_prefs, baseline))
    if instance.dispatcher_route:
        add("Start from the dispatcher's sequence only", _single(instance, lexicon_prefs, SolverRegistry.get(DISPATCHER).solve(instance, lexicon_prefs)))
    add("Start from nearest neighbour only", _single(instance, lexicon_prefs, SolverRegistry.get(NEAREST).solve(instance, lexicon_prefs)))
    add("No 2-opt phase", _guided(instance, lexicon_prefs, baseline, moves=("relocate", "swap")))
    add("Relocate and 2-opt only (no swap)", _guided(instance, lexicon_prefs, baseline, moves=("relocate", "two_opt")))
    add("Swap and 2-opt only (no relocate)", _guided(instance, lexicon_prefs, baseline, moves=("swap", "two_opt")))
    add("2-opt only (no preference moves)", _guided(instance, lexicon_prefs, baseline, moves=("two_opt",)))
    add("Unranked candidates", _guided(instance, lexicon_prefs, baseline, ranked=False))
    add("Unweighted violations (u_i = 1)", _guided(instance, lexicon_prefs, baseline, weighted=False))
    add("Penalty rate lambda = 0.5 c_t in the search", _guided(instance, lexicon_prefs, baseline, penalty_per_hour=0.5 * c.PENALTY_PER_HOUR_RON))
    add("Penalty rate lambda = 2 c_t in the search", _guided(instance, lexicon_prefs, baseline, penalty_per_hour=2 * c.PENALTY_PER_HOUR_RON))
    oracle_prefs = extractors.preferences(instance, extractors.ORACLE)
    oracle_baseline = SolverRegistry.get(ORTOOLS).solve(instance, oracle_prefs, time_limit_s=time_limit_s)
    add("Oracle extraction (reference labels)", _guided(instance, oracle_prefs, oracle_baseline))
    try:
        llm_prefs = extractors.preferences(instance, extractors.LLM)
        llm_baseline = SolverRegistry.get(ORTOOLS).solve(instance, llm_prefs, time_limit_s=time_limit_s)
        add(f"LLM extraction ({get_settings().GEMINI_MODEL})", _guided(instance, llm_prefs, llm_baseline))
    except (RuntimeError, OSError, ValueError) as exc:
        skipped["llm"] = str(exc)
    result = AblationResult(run_id=f"{datetime.now():%Y%m%d_%H%M%S}_{instance_id}", instance_id=instance_id,
                            variants=variants, skipped=skipped)
    folder = get_settings().results_dir / result.run_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "ablation.json").write_text(result.model_dump_json(indent=2))
    return result


def _guided(instance: Instance, preferences: dict[int, Preference], baseline: Solution, **params) -> Solution:
    """The full method: both starts (solver's route and the dispatcher's, when recorded), best kept."""
    return benchmark.solve_guided(instance, preferences, baseline, **params)


def _single(instance: Instance, preferences: dict[int, Preference], initial: Solution) -> Solution:
    return GuidedSolver().solve(instance, preferences, initial=initial)


def list_results() -> list[str]:
    folder = get_settings().results_dir
    if not folder.is_dir():
        return []
    return sorted(p.name for p in folder.iterdir() if (p / "ablation.json").is_file())


def load_result(run_id: str) -> AblationResult:
    return AblationResult.model_validate_json((get_settings().results_dir / run_id / "ablation.json").read_text())
