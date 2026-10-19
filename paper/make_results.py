"""Collects the numbers of the paper (tables and figures) from the latest runs into paper/results.json.

Run from the repository root after `report`: python paper/make_results.py
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from app import constants as c                      # noqa: E402
from app.services import ablation, benchmark, quality  # noqa: E402
from app.services.solvers import ORDER                # noqa: E402

LABELS = {"dispatcher": "Dispatcher", "nearest": "Nearest neighbour", "concorde": "Concorde", "ortools": "OR-Tools (windows)",
          "adaptive": "Adaptive heuristic (2025)", "guided": "Proposed"}


def fmean(values, digits=1):
    values = list(values)
    return round(statistics.fmean(values), digits) if values else None


def load(prefix: str):
    runs = {k: v for k, v in benchmark.latest_runs().items() if k.startswith(prefix)}
    return {k: benchmark.load_result(v) for k, v in sorted(runs.items())}


def config_means(results, reference: str):
    out = []
    for solver in ORDER:
        evals = [e for r in results.values() for e in r.evaluations if e.solver == solver]
        if not evals:
            continue
        changes_m, changes = [], []
        for r in results.values():
            mine = next((e for e in r.evaluations if e.solver == solver), None)
            ref = next((e for e in r.evaluations if e.solver == reference), None)
            if mine and ref:
                changes_m.append(100 * (mine.monetary_cost_ron / ref.monetary_cost_ron - 1))
                changes.append(100 * (mine.composite_cost_ron / ref.composite_cost_ron - 1))
        out.append({
            "solver": solver, "label": LABELS[solver], "n": len(evals),
            "distance": fmean(e.distance_km for e in evals), "duration": fmean((e.duration_h for e in evals), 2),
            "waiting": fmean((e.waiting_h for e in evals), 2), "monetary": fmean(e.monetary_cost_ron for e in evals),
            "penalty": fmean((e.penalty_h for e in evals), 2), "composite": fmean(e.composite_cost_ron for e in evals),
            "satisfaction": fmean(e.satisfaction_pct for e in evals), "bindingMissed": sum(e.binding_missed for e in evals),
            "runtime": fmean((e.runtime_s for e in evals), 2), "dMonetary": fmean(changes_m), "dComposite": fmean(changes),
            "days": max(e.days for e in evals),
        })
    return out


def bands(results):
    totals = {}
    for r in results.values():
        for e in r.evaluations:
            for band, stats in e.by_band.items():
                cell = totals.setdefault(e.solver, {}).setdefault(band, [0, 0])
                cell[0] += stats.stated
                cell[1] += stats.met
    return [{"solver": s, "label": LABELS[s], **{b: {"stated": totals[s][b][0], "met": totals[s][b][1],
             "pct": round(100 * totals[s][b][1] / totals[s][b][0], 1) if totals[s][b][0] else None} for b in c.BANDS}}
            for s in ORDER if s in totals]


def per_instance(results):
    rows = []
    for inst, r in results.items():
        by = {e.solver: e for e in r.evaluations}
        rows.append({"instance": inst, "stops": r.stops,
                     **{s: {"composite": by[s].composite_cost_ron, "monetary": by[s].monetary_cost_ron, "distance": by[s].distance_km,
                            "satisfaction": by[s].satisfaction_pct, "penalty": by[s].penalty_h} for s in by}})
    return rows


def synthetic_by_size(results):
    sizes = sorted({r.stops for r in results.values()})
    out = []
    for n in sizes:
        subset = {k: v for k, v in results.items() if v.stops == n}
        out.append({"stops": n, "instances": len(subset), "configs": config_means(subset, "ortools")})
    return out


def ablation_table(prefix: str):
    results = [ablation.load_result(r) for r in ablation.list_results()]
    latest = {}
    for r in results:
        if r.instance_id.startswith(prefix):
            latest[r.instance_id] = r
    results = list(latest.values())
    if not results:
        return [], 0
    names = []
    for r in results:
        for v in r.variants:
            if v.solver not in names:
                names.append(v.solver)
    table = []
    for name in names:
        mine = [v for r in results for v in r.variants if v.solver == name]
        base = {r.instance_id: next(v for v in r.variants if v.solver == "Proposed, full") for r in results}
        changes = [100 * (v.composite_cost_ron / base[r.instance_id].composite_cost_ron - 1) for r in results for v in r.variants if v.solver == name]
        table.append({"variant": name, "n": len(mine), "composite": fmean(v.composite_cost_ron for v in mine),
                      "monetary": fmean(v.monetary_cost_ron for v in mine), "penalty": fmean((v.penalty_h for v in mine), 2),
                      "satisfaction": fmean(v.satisfaction_pct for v in mine), "bindingMissed": sum(v.binding_missed for v in mine),
                      "runtime": fmean((v.runtime_s for v in mine), 2), "dComposite": fmean(changes)})
    return table, len(results)


def main():
    real, synth = load("DAY_"), load("SYN_")
    lex = quality.assess_lexicon()
    try:
        llm = quality.assess_llm().model_dump()
    except Exception:
        llm = None
    real_cfg = config_means(real, "dispatcher")
    guided = next(x for x in real_cfg if x["solver"] == "guided")
    ortools_cfg = next(x for x in real_cfg if x["solver"] == "ortools")
    pair = [(next(e for e in r.evaluations if e.solver == "guided"), next(e for e in r.evaluations if e.solver == "ortools")) for r in real.values()]
    guided_vs_ortools_real = fmean(100 * (g.composite_cost_ron / o.composite_cost_ron - 1) for g, o in pair)
    synth_pairs = [(next(e for e in r.evaluations if e.solver == "guided"), next(e for e in r.evaluations if e.solver == "ortools"))
                   for r in synth.values() if any(e.solver == "guided" for e in r.evaluations)]
    guided_vs_ortools_synth = fmean(100 * (g.composite_cost_ron / o.composite_cost_ron - 1) for g, o in synth_pairs)
    abl, abl_n = ablation_table("DAY_")
    abl_s, abl_s_n = ablation_table("SYN_")
    out = {
        "lexicon": {**lex.model_dump(), "bandAccuracyPct": round(100 * lex.band_accuracy, 1)},
        "llm": llm,
        "real": {"instances": len(real), "meanStops": fmean((r.stops for r in real.values()), 1), "configs": real_cfg, "bands": bands(real),
                 "perInstance": per_instance(real), "guidedVsOrtoolsPct": abs(guided_vs_ortools_real) if guided_vs_ortools_real is not None else None,
                 "guidedVsOrtoolsSigned": guided_vs_ortools_real,
                 "guidedVsDispatcherPct": abs(guided["dComposite"]), "guidedSatisfaction": guided["satisfaction"],
                 "ortoolsSatisfaction": ortools_cfg["satisfaction"]},
        "synth": {"instances": len(synth), "bySize": synthetic_by_size(synth),
                  "guidedVsOrtoolsPct": abs(guided_vs_ortools_synth) if guided_vs_ortools_synth is not None else None},
        "ablation": {"instances": abl_n, "variants": abl, "synthInstances": abl_s_n, "synthVariants": abl_s},
    }
    (HERE / "results.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in out["real"].items() if k not in ("perInstance", "bands", "configs")}, indent=1))
    print("synthetic:", out["synth"]["guidedVsOrtoolsPct"], "ablation instances:", abl_n)


if __name__ == "__main__":
    main()
