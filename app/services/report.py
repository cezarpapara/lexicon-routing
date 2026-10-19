"""Tables and figures of the paper from the latest benchmark and ablation run of every instance."""

from __future__ import annotations

import csv
import statistics
from pathlib import Path

from app import constants as c
from app.config import get_settings
from app.services import ablation, benchmark, quality
from app.services.solvers import DISPATCHER, ORDER, ORTOOLS

COLUMNS = ["distance_km", "duration_h", "waiting_h", "monetary_cost_ron", "penalty_h", "composite_cost_ron",
           "satisfaction_pct", "binding_missed", "runtime_s"]
LABELS = {"dispatcher": "Dispatcher", "nearest": "Nearest neighbour", "concorde": "Concorde", "ortools": "OR-Tools (windows)",
          "adaptive": "Adaptive heuristic (2025)", "guided": "Proposed"}


def build(run_ids: list[str] | None = None) -> Path:
    folder = get_settings().results_dir / "report"
    folder.mkdir(parents=True, exist_ok=True)
    runs = run_ids or list(benchmark.latest_runs().values())
    results = [benchmark.load_result(r) for r in runs]
    rows = _rows(results)
    _write_csv(folder / "per_instance.csv", rows)
    real = [r for r in rows if not r["instance_id"].startswith("SYN_")]
    synthetic = [r for r in rows if r["instance_id"].startswith("SYN_")]
    lines = ["# Results", ""]
    if real:
        lines += ["## Real trips: mean over instances, change relative to the dispatcher's plan", "",
                  *_table(_summary(real, reference=DISPATCHER)), ""]
        lines += ["## Real trips: preference satisfaction by band (% of stated intervals met)", "",
                  *_table(_bands(results, real_only=True)), ""]
    if synthetic:
        lines += ["## Synthetic instances: mean over seeds per size, change relative to OR-Tools", ""]
        for size in sorted({int(r["instance_id"].split("_")[1]) for r in synthetic}):
            subset = [r for r in synthetic if int(r["instance_id"].split("_")[1]) == size]
            lines += [f"### {size} stops ({len({r['instance_id'] for r in subset})} instances)", "",
                      *_table(_summary(subset, reference=ORTOOLS)), ""]
        _figure(synthetic, folder / "composite_by_size.png")
    ablations = [ablation.load_result(r) for r in ablation.list_results()]
    if ablations:
        lines += ["## Ablation: mean over instances", "", *_table(_ablation_table(ablations)), ""]
    lines += ["## Extraction quality on the corpus", "", *_table(_quality_table()), ""]
    (folder / "report.md").write_text("\n".join(lines))
    return folder


# ----------------------------------------------------------------------------- tables

def _rows(results: list[benchmark.BenchmarkResult]) -> list[dict]:
    rows = []
    for result in results:
        for e in result.evaluations:
            rows.append({"instance_id": result.instance_id, "stops": result.stops, "extractor": result.extractor,
                         "solver": e.solver, **{k: getattr(e, k) for k in COLUMNS}})
    return rows


def _summary(rows: list[dict], reference: str) -> list[dict]:
    """Mean of every column per solver; the change columns compare instance by instance with `reference`."""
    solvers = [s for s in ORDER if any(r["solver"] == s for r in rows)]
    by_instance = {}
    for r in rows:
        by_instance.setdefault(r["instance_id"], {})[r["solver"]] = r
    table = []
    for solver in solvers:
        mine = [r for r in rows if r["solver"] == solver]
        entry = {"configuration": LABELS.get(solver, solver), "instances": len(mine)}
        entry.update({k: round(statistics.fmean(r[k] for r in mine), 2) for k in COLUMNS})
        for key, label in (("monetary_cost_ron", "dC_m_pct"), ("composite_cost_ron", "dC_pct")):
            changes = [100 * (by_instance[i][solver][key] / by_instance[i][reference][key] - 1)
                       for i in by_instance if solver in by_instance[i] and reference in by_instance[i]]
            entry[label] = round(statistics.fmean(changes), 1) if changes else ""
        table.append(entry)
    return table


def _bands(results: list[benchmark.BenchmarkResult], real_only: bool) -> list[dict]:
    totals: dict[str, dict[str, list[int]]] = {}
    for result in results:
        if real_only and result.instance_id.startswith("SYN_"):
            continue
        for e in result.evaluations:
            for band, stats in e.by_band.items():
                cell = totals.setdefault(e.solver, {}).setdefault(band, [0, 0])
                cell[0] += stats.stated
                cell[1] += stats.met
    table = []
    for solver in [s for s in ORDER if s in totals]:
        entry = {"configuration": LABELS.get(solver, solver)}
        for band in c.BANDS:
            stated, met = totals[solver].get(band, [0, 0])
            entry[band] = f"{100 * met / stated:.1f} ({met}/{stated})" if stated else "-"
        table.append(entry)
    return table


def _ablation_table(results: list[ablation.AblationResult]) -> list[dict]:
    names = []
    for result in results:
        for v in result.variants:
            if v.solver not in names:
                names.append(v.solver)
    table = []
    for name in names:
        mine = [v for r in results for v in r.variants if v.solver == name]
        table.append({"variant": name, "instances": len(mine),
                      **{k: round(statistics.fmean(getattr(v, k) for v in mine), 2)
                         for k in ("composite_cost_ron", "monetary_cost_ron", "penalty_h", "satisfaction_pct", "binding_missed", "runtime_s")}})
    return table


def _quality_table() -> list[dict]:
    table = []
    try:
        table.append(quality.assess_lexicon().model_dump(exclude={"confusion"}))
    except FileNotFoundError:
        return table
    try:
        table.append(quality.assess_llm().model_dump(exclude={"confusion"}))
    except (RuntimeError, OSError, ValueError):
        pass
    return table


def _table(rows: list[dict]) -> list[str]:
    if not rows:
        return ["(no data)"]
    keys = list(rows[0])
    lines = ["| " + " | ".join(keys) + " |", "|" + "---|" * len(keys)]
    lines += ["| " + " | ".join(str(r.get(k, "")) for k in keys) + " |" for r in rows]
    return lines


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


# ----------------------------------------------------------------------------- figure

def _figure(rows: list[dict], path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    sizes = sorted({int(r["instance_id"].split("_")[1]) for r in rows})
    markers = {"nearest": "s", "concorde": "^", "ortools": "o", "adaptive": "D", "guided": "*"}
    styles = {"nearest": ":", "concorde": "-.", "ortools": "--", "adaptive": (0, (3, 1, 1, 1)), "guided": "-"}
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4))
    for solver in [s for s in ORDER if any(r["solver"] == s for r in rows)]:
        means = [statistics.fmean(r["composite_cost_ron"] for r in rows if r["solver"] == solver and int(r["instance_id"].split("_")[1]) == n) for n in sizes]
        times = [statistics.fmean(r["runtime_s"] for r in rows if r["solver"] == solver and int(r["instance_id"].split("_")[1]) == n) for n in sizes]
        axes[0].plot(sizes, means, marker=markers.get(solver, "o"), linestyle=styles.get(solver, "-"), color="black", label=LABELS.get(solver, solver), markersize=6)
        axes[1].plot(sizes, [max(t, 1e-3) for t in times], marker=markers.get(solver, "o"), linestyle=styles.get(solver, "-"), color="black", label=LABELS.get(solver, solver), markersize=6)
    axes[0].set_xlabel("stops"), axes[0].set_ylabel("composite cost C (RON)"), axes[0].set_xscale("log"), axes[0].set_yscale("log")
    axes[1].set_xlabel("stops"), axes[1].set_ylabel("execution time (s)"), axes[1].set_xscale("log"), axes[1].set_yscale("log")
    axes[0].legend(fontsize=8, frameon=False)
    for ax in axes:
        ax.grid(True, which="major", linewidth=0.4, alpha=0.5)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
