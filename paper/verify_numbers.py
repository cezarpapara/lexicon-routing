"""Independent check of paper/results.json against the raw result files.

Recomputes, with plain Python and without the application's aggregation code, every aggregate that the
paper reports (means per configuration, relative changes, satisfaction by band, synthetic sizes, ablation
means) directly from data/results/*/benchmark.json and ablation.json, and compares them with
paper/results.json. Also checks the identities behind every evaluation (monetary and composite cost) and
that every solution is a permutation of the stops.

    python paper/verify_numbers.py
"""

import csv
import glob
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = json.loads((ROOT / "paper" / "results.json").read_text())
C_D, C_T = 3.17, 126.52
ORDER = ["dispatcher", "nearest", "concorde", "ortools", "adaptive", "guided"]
problems = []


def check(name, mine, theirs, tol=0.051):
    if mine is None and theirs is None:
        return
    if mine is None or theirs is None or abs(mine - theirs) > tol:
        problems.append(f"{name}: recomputed {mine} vs results.json {theirs}")


def latest(kind):
    runs = {}
    for path in sorted(glob.glob(str(ROOT / "data" / "results" / "*" / f"{kind}.json"))):
        j = json.loads(Path(path).read_text())
        runs[j["instance_id"]] = j          # sorted by run id (timestamp) -> the last one wins
    return runs


def mean(values, digits=1):
    values = list(values)
    return round(statistics.fmean(values), digits) if values else None


bench = latest("benchmark")
real = {k: v for k, v in bench.items() if k.startswith("DAY_")}
synth = {k: v for k, v in bench.items() if k.startswith("SYN_")}
print(f"benchmark runs: {len(real)} real, {len(synth)} synthetic")

# --- 1. identities and permutations in every evaluation
for inst, j in bench.items():
    n = j["stops"]
    for e in j["evaluations"]:
        if abs(C_D * e["distance_km"] + C_T * e["duration_h"] - e["monetary_cost_ron"]) > 0.7:
            problems.append(f"{inst}/{e['solver']}: C_m != c_d D + c_t T")
        if abs(e["monetary_cost_ron"] + C_T * e["penalty_h"] - e["composite_cost_ron"]) > 0.7:
            problems.append(f"{inst}/{e['solver']}: C != C_m + lambda * sum(u p)")
        if e["met"] > e["stated"] or (e["stated"] and abs(100 * e["met"] / e["stated"] - e["satisfaction_pct"]) > 0.06):
            problems.append(f"{inst}/{e['solver']}: satisfaction_pct inconsistent")
    for s in j.get("solutions", []):
        route = s["route"] if isinstance(s, dict) else None
        if route is not None and sorted(route) != list(range(1, n + 1)):
            problems.append(f"{inst}/{s.get('solver')}: route is not a permutation of the stops")


# --- 2. real trips: Table 5 and the headline numbers
def config_rows(runs, ref):
    rows = {}
    for solver in ORDER:
        ev = [e for r in runs.values() for e in r["evaluations"] if e["solver"] == solver]
        if not ev:
            continue
        dm, dc = [], []
        for r in runs.values():
            mine = next((e for e in r["evaluations"] if e["solver"] == solver), None)
            base = next((e for e in r["evaluations"] if e["solver"] == ref), None)
            if mine and base:
                dm.append(100 * (mine["monetary_cost_ron"] / base["monetary_cost_ron"] - 1))
                dc.append(100 * (mine["composite_cost_ron"] / base["composite_cost_ron"] - 1))
        rows[solver] = dict(distance=mean(e["distance_km"] for e in ev), duration=mean((e["duration_h"] for e in ev), 2),
                            waiting=mean((e["waiting_h"] for e in ev), 2), monetary=mean(e["monetary_cost_ron"] for e in ev),
                            penalty=mean((e["penalty_h"] for e in ev), 2), composite=mean(e["composite_cost_ron"] for e in ev),
                            satisfaction=mean(e["satisfaction_pct"] for e in ev), bindingMissed=sum(e["binding_missed"] for e in ev),
                            runtime=mean((e["runtime_s"] for e in ev), 2), dMonetary=mean(dm), dComposite=mean(dc))
    return rows


rows = config_rows(real, "dispatcher")
for cfg in RESULTS["real"]["configs"]:
    for key, val in rows[cfg["solver"]].items():
        check(f"Table 5 {cfg['solver']}.{key}", val, cfg[key])
check("real.instances", len(real), RESULTS["real"]["instances"])
check("real.meanStops", mean((r["stops"] for r in real.values()), 1), RESULTS["real"]["meanStops"])
check("abstract/conclusions: guided vs dispatcher %", abs(rows["guided"]["dComposite"]), RESULTS["real"]["guidedVsDispatcherPct"])
g_o = mean(100 * (next(e for e in r["evaluations"] if e["solver"] == "guided")["composite_cost_ron"] /
                 next(e for e in r["evaluations"] if e["solver"] == "ortools")["composite_cost_ron"] - 1) for r in real.values())
check("conclusions: guided vs OR-Tools % (real)", abs(g_o), RESULTS["real"]["guidedVsOrtoolsPct"])
below = sum(1 for r in real.values() if next(e for e in r["evaluations"] if e["solver"] == "guided")["composite_cost_ron"]
            <= next(e for e in r["evaluations"] if e["solver"] == "dispatcher")["composite_cost_ron"] + 0.005)
print("real trips with proposed <= dispatcher (text 5.2):", below, "of", len(real))

# bands (Table 5 text / Figure 3 right)
for b in RESULTS["real"]["bands"]:
    for band in ("mild", "strong", "binding"):
        stated = sum(e["by_band"][band]["stated"] for r in real.values() for e in r["evaluations"] if e["solver"] == b["solver"])
        met = sum(e["by_band"][band]["met"] for r in real.values() for e in r["evaluations"] if e["solver"] == b["solver"])
        check(f"bands {b['solver']}.{band}.stated", stated, b[band]["stated"])
        check(f"bands {b['solver']}.{band}.met", met, b[band]["met"])
        if stated:
            check(f"bands {b['solver']}.{band}.pct", round(100 * met / stated, 1), b[band]["pct"])

# --- 3. synthetic: Table 6
by_size = {}
for inst, r in synth.items():
    by_size.setdefault(int(inst.split("_")[1]), {})[inst] = r
for s in RESULTS["synth"]["bySize"]:
    rows = config_rows(by_size[s["stops"]], "ortools")
    for cfg in s["configs"]:
        for key in ("monetary", "penalty", "composite", "satisfaction", "bindingMissed", "dComposite", "runtime", "waiting", "distance"):
            check(f"Table 6 {s['stops']} {cfg['solver']}.{key}", rows[cfg["solver"]][key], cfg[key])
pairs = [(next(e for e in r["evaluations"] if e["solver"] == "guided"), next(e for e in r["evaluations"] if e["solver"] == "ortools")) for r in synth.values()]
check("abstract/conclusions: guided vs OR-Tools % (synthetic, mean of 18 instances)",
      abs(mean(100 * (g["composite_cost_ron"] / o["composite_cost_ron"] - 1) for g, o in pairs)), RESULTS["synth"]["guidedVsOrtoolsPct"])

# --- 4. ablation: Table 7
abl = latest("ablation")
for prefix, key, nkey in (("DAY_", "variants", "instances"), ("SYN_", "synthVariants", "synthInstances")):
    runs = {k: v for k, v in abl.items() if k.startswith(prefix)}
    check(f"ablation {prefix} instances", len(runs), RESULTS["ablation"][nkey])
    for v in RESULTS["ablation"][key]:
        mine = [next((x for x in r["variants"] if x["solver"] == v["variant"]), None) for r in runs.values()]
        full = [next(x for x in r["variants"] if x["solver"] == "Proposed, full") for r in runs.values()]
        mine_full = [(m, f) for m, f in zip(mine, full) if m]
        check(f"Table 7 {prefix}{v['variant']}.composite", mean(m["composite_cost_ron"] for m, _ in mine_full), v["composite"])
        check(f"Table 7 {prefix}{v['variant']}.satisfaction", mean(m["satisfaction_pct"] for m, _ in mine_full), v["satisfaction"])
        check(f"Table 7 {prefix}{v['variant']}.dComposite", mean(100 * (m["composite_cost_ron"] / f["composite_cost_ron"] - 1) for m, f in mine_full), v["dComposite"])

# --- 5. extraction quality: Table 4 (metrics recomputed from the per-message comparison)
import sys
sys.path.insert(0, str(ROOT))
from app.services import extraction, lexicon as lex_mod          # the extractor under test; the metrics below are recomputed here
from app.services.llm import _digest, _to_preference

ref = {int(r["id"]): r for r in csv.DictReader(open(ROOT / "data/corpus/reference.csv", encoding="utf-8"))}
msgs = {int(r["id"]): r["message"] for r in csv.DictReader(open(ROOT / "data/corpus/corpus.csv", encoding="utf-8"))}
cache = json.loads((ROOT / "data/corpus/llm/gemini-3.8-flash.json").read_text())
BAND_U = {"none": 0, "flexible": 0, "mild": 0.25, "strong": 0.5, "binding": 1}


def hhmm(s):
    return None if not s else int(s[:2]) + int(s[3:5]) / 60


def metrics(pred):
    tp = fp = fn = 0
    errs, xs, ys, agree = [], [], [], 0
    for i, r in ref.items():
        p = pred[i]
        has_ref = bool(r["window_start"] or r["window_end"])
        has_pred = p.start_h is not None
        tp += has_ref and has_pred; fp += (not has_ref) and has_pred; fn += has_ref and (not has_pred)
        if has_ref and has_pred:
            errs += [abs(p.start_h - hhmm(r["window_start"])) * 60, abs(p.end_h - hhmm(r["window_end"])) * 60]
        xs.append(p.urgency); ys.append(BAND_U[r["band"]])
        rb = "flexible" if r["band"] in ("none", "flexible") else r["band"]
        agree += (p.band == rb)
    prec, rec = tp / (tp + fp), tp / (tp + fn)
    # Spearman with average ranks
    def ranks(v):
        order = sorted(range(len(v)), key=lambda k: v[k]); rk = [0] * len(v); k = 0
        while k < len(v):
            j = k
            while j + 1 < len(v) and v[order[j + 1]] == v[order[k]]: j += 1
            for m in range(k, j + 1): rk[order[m]] = (k + j) / 2 + 1
            k = j + 1
        return rk
    rx, ry = ranks(xs), ranks(ys); mx, my = statistics.fmean(rx), statistics.fmean(ry)
    rho = sum((a - mx) * (b - my) for a, b in zip(rx, ry)) / (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return dict(precision=round(prec, 3), recall=round(rec, 3), f1=round(2 * prec * rec / (prec + rec), 3),
                boundary_mae_min=round(statistics.fmean(errs), 1), spearman=round(rho, 3), band_accuracy=round(agree / len(ref), 3))


lex_pred = {i: extraction.extract(m) for i, m in msgs.items()}
llm_pred = {i: _to_preference(cache[_digest(m)]) for i, m in msgs.items()}
for name, pred, key in (("lexicon", lex_pred, "lexicon"), ("Gemini", llm_pred, "llm")):
    for k, v in metrics(pred).items():
        check(f"Table 4 {name}.{k}", v, RESULTS[key][k], tol=0.0015 if k != "boundary_mae_min" else 0.06)

print("checks with a difference:", len(problems))
for p in problems:
    print("  ", p)
print("OK" if not problems else "DIFFERENCES FOUND")
