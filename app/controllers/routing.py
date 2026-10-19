from fastapi import APIRouter, HTTPException, Query

from app.services import benchmark, corpus, data, extraction, extractors, metrics
from app.services.solvers import SolverRegistry

router = APIRouter(prefix="/api/v1", tags=["Routing"])


@router.get("/solvers", summary="List registered solvers")
async def list_solvers():
    return [s.info() for s in SolverRegistry.all().values()]


@router.get("/instances", summary="List available instances")
async def list_instances():
    return data.list_instances()


@router.get("/extract", summary="Preference extracted from one message by the lexicon")
async def extract(message: str = Query(..., description="Customer message, e.g. 'only after 3 pm, I'm at work'")):
    return extraction.extract(message)


@router.post("/solve", summary="Run one solver on one instance and evaluate the route")
async def solve(
    instance: str = Query(..., description="Instance id, e.g. DAY_4_TRUCK_4_TRIP_1"),
    solver: str = Query(..., description="Solver name from /solvers"),
    extractor: str = Query("lexicon", description="lexicon | llm | oracle"),
):
    try:
        inst = data.load_instance(instance)
        preferences = extractors.preferences(inst, extractor)
        solution = SolverRegistry.get(solver).solve(inst, preferences)
    except (FileNotFoundError, KeyError, ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"evaluation": metrics.evaluate(inst, solution, corpus.references(inst)), "solution": solution}


@router.post("/benchmark", summary="Run every configuration on one instance")
async def run_benchmark(instance: str = Query(...), extractor: str = Query("lexicon")):
    try:
        result = benchmark.run(instance, extractor=extractor)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return result.model_dump(exclude={"solutions"})


@router.get("/results", summary="List benchmark runs")
async def list_results():
    return benchmark.list_results()


@router.get("/results/{run_id}", summary="Load one benchmark run")
async def get_result(run_id: str):
    try:
        return benchmark.load_result(run_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Unknown run '{run_id}'")
