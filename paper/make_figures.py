"""Figures of the paper (PNG, 300 dpi, colour with distinct markers so that they also read in black and white)."""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "figs"
sys.path.insert(0, str(ROOT))

from app import constants as c                          # noqa: E402
from app.services import benchmark, corpus, data, extractors, schedule  # noqa: E402

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8,
                     "legend.fontsize": 7, "xtick.labelsize": 7, "ytick.labelsize": 7, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 100})

COLOUR = {"dispatcher": "#000000", "nearest": "#56B4E9", "concorde": "#E69F00", "ortools": "#0072B2",
          "adaptive": "#CC79A7", "guided": "#009E73"}
MARKER = {"dispatcher": "P", "nearest": "s", "concorde": "^", "ortools": "o", "adaptive": "D", "guided": "*"}
STYLE = {"dispatcher": "-", "nearest": ":", "concorde": "-.", "ortools": "--", "adaptive": (0, (3, 1, 1, 1)), "guided": "-"}
LABEL = {"dispatcher": "Dispatcher", "nearest": "Nearest neighbour", "concorde": "Concorde", "ortools": "OR-Tools (windows)",
         "adaptive": "Adaptive heuristic (2025)", "guided": "Proposed"}
BAND_COLOUR = {"none": "#BBBBBB", "flexible": "#999999", "mild": "#56B4E9", "strong": "#E69F00", "binding": "#D55E00"}

results = json.loads((Path(__file__).resolve().parent / "results.json").read_text())


def save(fig, name):
    OUT.mkdir(exist_ok=True)
    fig.savefig(OUT / name, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("written", OUT / name)


# ----------------------------------------------------------------------------- Figure 1: framework
def framework():
    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    ax.set_xlim(0, 100), ax.set_ylim(0, 44), ax.axis("off")
    boxes = [
        (1, 15, 18, 14, "Customer\nmessages\n(free text)", "#F0F0F0"),
        (25, 25, 21, 13, "Urgency lexicon\nscore uᵢ, band", "#DDEBF7"),
        (25, 4, 21, 13, "Interval rules\n[êᵢ, l̂ᵢ]", "#DDEBF7"),
        (49, 14, 25, 16, "Preferences\nbinding → hard window\nothers → soft, weight uᵢ", "#E2F0D9"),
        (79, 25, 20, 13, "Time-window solver\nhard windows,\nmonetary cost", "#FFF2CC"),
        (79, 4, 20, 13, "Guided refinement\ncomposite cost C", "#FFF2CC"),
    ]
    for x, y, w, h, text, colour in boxes:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.2", fc=colour, ec="#444444", lw=0.8))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=7, linespacing=1.25)
    arrows = [((19.3, 22), (24.7, 31.5)), ((19.3, 22), (24.7, 10.5)), ((46.3, 31.5), (48.7, 23.5)), ((46.3, 10.5), (48.7, 20.5)),
              ((74.3, 22), (78.7, 31.5)), ((74.3, 22), (78.7, 10.5)), ((89, 24.7), (89, 17.3))]
    for (x0, y0), (x1, y1) in arrows:
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=9, lw=0.8, color="#444444", shrinkA=0, shrinkB=0))
    ax.text(35.5, 42, "Stage 1: extraction", ha="center", fontsize=8, fontweight="bold")
    ax.text(89, 42, "Stage 2: routing", ha="center", fontsize=8, fontweight="bold")
    ax.text(62, 42, "", ha="center")
    save(fig, "fig1_framework.png")


# ----------------------------------------------------------------------------- Figure 2: extraction quality
def extraction():
    conf = results["lexicon"]["confusion"]
    bands = ["flexible", "mild", "strong", "binding"]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9), gridspec_kw={"width_ratios": [1, 1.25]})
    ax = axes[0]
    matrix = [[conf[r][col] for col in bands] for r in bands]
    im = ax.imshow(matrix, cmap="Blues", vmin=0, vmax=max(max(r) for r in matrix))
    for i, r in enumerate(bands):
        for j, col in enumerate(bands):
            v = matrix[i][j]
            ax.text(j, i, str(v), ha="center", va="center", fontsize=8, color="white" if v > 45 else "black")
    ax.set_xticks(range(4), bands), ax.set_yticks(range(4), ["flexible / none", "mild", "strong", "binding"])
    ax.set_xlabel("band assigned by the lexicon"), ax.set_ylabel("reference band")
    ax.set_title("Band agreement (250 messages)")
    for spine in ax.spines.values():
        spine.set_visible(False)
    # right: urgency score per reference band (strip plot)
    ax = axes[1]
    refs, _ = __import__("app.services.quality", fromlist=["x"]).corpus_references()
    from app.services import extraction as ex, quality
    msgs = quality.corpus_messages()
    import random
    rng = random.Random(1)
    positions = {"flexible": 0, "none": 0, "mild": 1, "strong": 2, "binding": 3}
    for key in sorted(refs):
        u = ex.extract(msgs[key]).urgency
        band = refs[key].band
        ax.scatter(positions[band] + rng.uniform(-0.28, 0.28), u, s=12, color=BAND_COLOUR[band], alpha=0.75, edgecolor="none")
    for y, lab in ((0.2, "mild"), (0.45, "strong"), (0.7, "binding")):
        ax.axhline(y, color="#888888", lw=0.6, ls="--")
        ax.text(3.45, y + 0.012, f"{lab} ≥ {y}", fontsize=6, color="#555555", ha="right")
    ax.set_xticks(range(4), ["flexible / none", "mild", "strong", "binding"])
    ax.set_xlabel("reference band"), ax.set_ylabel("lexicon urgency score u")
    ax.set_ylim(-0.03, 1.03), ax.set_title(f"Urgency score by reference band (ρ = {results['lexicon']['spearman']:.2f})")
    fig.tight_layout()
    save(fig, "fig2_extraction.png")


# ----------------------------------------------------------------------------- Figure 3: real trips
def real_trips():
    cfgs = results["real"]["configs"]
    bands = results["real"]["bands"]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8), gridspec_kw={"width_ratios": [1.1, 1]})
    ax = axes[0]
    names = [x["solver"] for x in cfgs]
    ax.bar(range(len(cfgs)), [x["dMonetary"] for x in cfgs], width=0.38, color=[COLOUR[n] for n in names], alpha=0.45, label="monetary cost Cₘ")
    ax.bar([i + 0.4 for i in range(len(cfgs))], [x["dComposite"] for x in cfgs], width=0.38, color=[COLOUR[n] for n in names], label="composite cost C")
    ax.axhline(0, color="black", lw=0.8)
    short = {"dispatcher": "Dispat-\ncher", "nearest": "Nearest\nneighbour", "concorde": "Concorde", "ortools": "OR-Tools\n(windows)", "adaptive": "Adaptive\n(2025)", "guided": "Proposed"}
    ax.set_xticks([i + 0.2 for i in range(len(cfgs))], [short[n] for n in names], fontsize=6.2)
    ax.set_xlim(-0.5, len(cfgs))
    ax.set_ylabel("change vs. the dispatcher's plan (%)")
    ax.set_title("Cost relative to the manual plan (18 trips)")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(fc="#777777", alpha=0.45, label="monetary cost"), Patch(fc="#777777", label="composite cost")], frameon=False, loc="upper right")
    ax = axes[1]
    order = ["mild", "strong", "binding"]
    width = 0.13
    for k, b in enumerate(bands):
        vals = [b[band]["pct"] or 0 for band in order]
        ax.bar([i + (k - 2.5) * width for i in range(3)], vals, width=width, color=COLOUR[b["solver"]], label=LABEL[b["solver"]])
    ax.set_xticks(range(3), order), ax.set_ylim(0, 105), ax.set_ylabel("stated intervals met (%)")
    ax.set_title("Preference satisfaction by band")
    ax.legend(frameon=False, fontsize=6, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.16))
    fig.tight_layout()
    save(fig, "fig3_real.png")


# ----------------------------------------------------------------------------- Figure 4: example routes
def routes(instance_id="DAY_4_TRUCK_4_TRIP_1"):
    run = benchmark.latest_runs().get(instance_id)
    if not run:
        return
    result = benchmark.load_result(run)
    instance = data.load_instance(instance_id)
    refs = corpus.references(instance)
    solutions = {s.solver: s for s in result.solutions}
    evals = {e.solver: e for e in result.evaluations}
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.3))
    for ax, name in zip(axes, ("dispatcher", "concorde", "guided")):
        sol = solutions[name]
        path = [c.DEPOT_NODE_ID, *sol.route, c.DEPOT_NODE_ID]
        xs = [instance.node(n).lon for n in path]
        ys = [instance.node(n).lat for n in path]
        ax.plot(xs, ys, color=COLOUR[name], lw=1.2, zorder=1)
        for k in range(len(path) - 1):
            ax.annotate("", xy=((xs[k] + xs[k + 1]) / 2, (ys[k] + ys[k + 1]) / 2), xytext=(xs[k], ys[k]),
                        arrowprops=dict(arrowstyle="-|>", color=COLOUR[name], lw=0.8, mutation_scale=7), zorder=2)
        timing = schedule.build(instance, sol.route, sol.preferences)
        for v in timing.visits:
            node = instance.node(v.node)
            ref = refs[v.node]
            met = (not ref.has_window) or schedule.violation_h(v.clock_h, ref) == 0
            ax.scatter(node.lon, node.lat, s=60, color=BAND_COLOUR[ref.band], edgecolor="black" if met else "#D55E00",
                       linewidth=0.6 if met else 1.6, zorder=3)
            ax.text(node.lon, node.lat, f" {int(v.clock_h):02d}:{int(round((v.clock_h % 1) * 60)):02d}", fontsize=6.5, va="bottom", zorder=4)
        depot = instance.node(c.DEPOT_NODE_ID)
        ax.scatter(depot.lon, depot.lat, marker="*", s=110, color="black", zorder=5)
        e = evals[name]
        ax.set_title(f"{LABEL[name]}\nC = {e.composite_cost_ron:.0f} RON, met {e.met}/{e.stated}", fontsize=8.5)
        ax.set_xticks([]), ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(True), spine.set_color("#BBBBBB")
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], marker="o", ls="", color=BAND_COLOUR[b], markeredgecolor="black", markersize=5, label=b) for b in ("flexible", "mild", "strong", "binding")]
    handles.append(Line2D([], [], marker="o", ls="", color="white", markeredgecolor="#D55E00", markeredgewidth=1.6, markersize=5, label="interval missed"))
    handles.append(Line2D([], [], marker="*", ls="", color="black", markersize=8, label="depot"))
    fig.legend(handles=handles, loc="lower center", ncol=6, frameon=False, fontsize=7.5, bbox_to_anchor=(0.5, -0.03))
    fig.tight_layout()
    save(fig, "fig4_routes.png")


# ----------------------------------------------------------------------------- Figure 5: synthetic
def synthetic():
    sizes = results["synth"]["bySize"]
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.5))
    for name in ("nearest", "concorde", "ortools", "adaptive", "guided"):
        pts = [(s["stops"], next((x for x in s["configs"] if x["solver"] == name), None)) for s in sizes]
        pts = [(n, x) for n, x in pts if x]
        if not pts:
            continue
        kw = dict(marker=MARKER[name], linestyle=STYLE[name], color=COLOUR[name], label=LABEL[name], markersize=5, lw=1.1)
        axes[0].plot([n for n, _ in pts], [x["composite"] for _, x in pts], **kw)
        axes[1].plot([n for n, _ in pts], [x["satisfaction"] for _, x in pts], **kw)
        axes[2].plot([n for n, _ in pts], [max(x["runtime"], 1e-2) for _, x in pts], **kw)
    for ax, ylabel, title in zip(axes, ("composite cost C (RON)", "stated intervals met (%)", "execution time (s)"),
                                 ("Composite cost", "Preference satisfaction", "Execution time")):
        ax.set_xscale("log"), ax.set_xlabel("stops"), ax.set_ylabel(ylabel), ax.set_title(title)
        ax.grid(True, which="major", lw=0.4, alpha=0.4)
    axes[0].set_yscale("log"), axes[2].set_yscale("log")
    axes[0].legend(frameon=False, fontsize=6)
    fig.tight_layout()
    save(fig, "fig5_synthetic.png")


# ----------------------------------------------------------------------------- Figure 6: ablation
def ablation():
    real = results["ablation"]["variants"]
    synth = results["ablation"].get("synthVariants") or []
    names = [v["variant"] for v in real if v["variant"] != "Proposed, full"]
    short = {"OR-Tools baseline (no refinement)": "baseline (no refinement)", "Start from OR-Tools only": "start: OR-Tools only",
             "Start from the dispatcher's sequence only": "start: dispatcher only", "Start from nearest neighbour only": "start: nearest neighbour",
             "No 2-opt phase": "no 2-opt phase", "Relocate and 2-opt only (no swap)": "no swap", "Swap and 2-opt only (no relocate)": "no relocate",
             "2-opt only (no preference moves)": "no preference moves", "Unranked candidates": "unranked candidates",
             "Unweighted violations (u_i = 1)": "unweighted (uᵢ = 1)", "Penalty rate lambda = 0.5 c_t in the search": "λ = 0.5 cₜ in the search",
             "Penalty rate lambda = 2 c_t in the search": "λ = 2 cₜ in the search", "Oracle extraction (reference labels)": "oracle extraction",
             "LLM extraction (gemini-3.8-flash)": "language model extraction"}
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    ys = range(len(names))
    rv = {v["variant"]: v for v in real}
    sv = {v["variant"]: v for v in synth}
    ax.barh([y + 0.2 for y in ys], [rv[n]["dComposite"] for n in names], height=0.38, color="#0072B2", label="real trips (18)")
    if synth:
        ax.barh([y - 0.2 for y in ys], [sv.get(n, {}).get("dComposite") or 0 for n in names], height=0.38, color="#E69F00", label="synthetic, 100 stops (3)")
    ax.axvline(0, color="black", lw=0.8)
    ax.set_yticks(list(ys), [short.get(n, n) for n in names]), ax.invert_yaxis()
    ax.set_xlabel("change of the composite cost relative to the full method (%)")
    ax.legend(frameon=False, loc="lower right")
    ax.grid(True, axis="x", lw=0.4, alpha=0.4)
    fig.tight_layout()
    save(fig, "fig6_ablation.png")


if __name__ == "__main__":
    framework(), extraction(), real_trips(), routes(), synthetic(), ablation()
