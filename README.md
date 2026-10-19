# lexicon-routing

Lexicon-guided route refinement for last-mile delivery under soft temporal preferences: code,
message corpus, instances and experiments of the paper

> C.-M. Papară, L.-M. Antal and V. Nimineț, "Lexicon-Guided Route Refinement for Last-Mile Delivery
> Under Soft Temporal Preferences," *BRAIN. Broad Research in Artificial Intelligence and
> Neuroscience* (submitted, 2026).

Academic, non-commercial use only — see [License](#license). Cite with [CITATION.cff](CITATION.cff).

## What it does

Customers of a home-delivery service leave short free-text messages on their orders ("preferably in
the morning", "only after 3 pm, I'm at work", "any time works"). The application

1. reads every message with a domain **urgency lexicon** and a small set of interval rules and turns
   it into a preferred delivery interval [ê, l̂] and an urgency score u ∈ [0, 1]
   (`app/services/lexicon.py`, `app/services/extraction.py`, lexicon in `data/lexicon/`);
2. treats the binding preferences (u ≥ 0.7) as hard time windows and the others as soft preferences;
3. plans the delivery route under one objective, defined once in `app/services/schedule.py`:

```
C = 3.17 RON/km · D + 126.52 RON/h · T + λ · Σ_i u_i · p_i        λ = 126.52 RON/h
    D  distance          T  working time from departure to return, waiting for hard windows included
    p_i  hours between the delivery at stop i and its preferred interval (0 inside it)
```

| Configuration | Sees | Implemented in |
|---|---|---|
| `dispatcher` | the store dispatcher's executed order (real trips) | `solvers/dispatcher.py` |
| `nearest`    | distance only (nearest-neighbour construction) | `solvers/nearest_neighbour.py` |
| `concorde`   | distance only (exact TSP, Concorde via NEOS) | `solvers/concorde.py`, `neos.py` |
| `ortools`    | hard windows (OR-Tools, monetary objective) | `solvers/ortools_tw.py` |
| `adaptive`   | hard windows (adaptive heuristic of Papară & Nimineț, 2025, re-implemented) | `solvers/adaptive.py` |
| `guided`     | hard windows **and** soft preferences with their urgency (proposed) | `solvers/guided.py` |

Every route is timed by the same simulator (the vehicle waits for the hard windows it was told about)
and scored against the *reference* preferences, i.e. what the customers meant, so that extraction
errors count against the method that made them. All constants are in `app/constants.py`.

## Project structure

```
app/
  cli.py                 every command below (python -m app.cli <command>)
  main.py, controllers/  FastAPI API (same services over HTTP, Swagger at /docs)
  constants.py           cost rates, penalty rate, working day, bands, category mix, time limits
  config.py              settings from .env / .env.local
  models.py              Preference, Node, Instance, Solution
  services/
    lexicon.py           urgency lexicon: matching and scoring
    extraction.py        interval rules; message -> Preference
    llm.py               the same extraction by a large language model (Gemini API, cached)
    extractors.py        lexicon | llm | oracle (reference labels)
    corpus.py            message bank, instantiation, corpus files, reference labels
    quality.py           extraction quality (detection, boundary error, Spearman, band agreement)
    data.py              source days -> one instance per dispatcher trip (messages anchored on the executed plan)
    synth.py             synthetic instances (messages anchored on a hidden random sequence)
    schedule.py          working-time line, waiting rule, cost terms
    solvers/             the six configurations
    metrics.py           evaluation against the reference preferences
    benchmark.py         all configurations on one instance
    ablation.py          variants of the proposed method
    report.py            tables of the paper (data/results/report)
    neos.py              Concorde on the NEOS Server
data/
  source/                the five anonymised delivery days of the compact-routing dataset (CC BY-NC 4.0)
  lexicon/               urgency_lexicon.csv
  corpus/                bank.json (message bank), corpus.csv, annotation_template.csv, reference.csv (annotation)
  instances/             DAY_d_TRUCK_t_TRIP_k (real trips, ≥ 4 stops) and SYN_<stops>_<seed>
  results/               one folder per run (gitignored) except results/report/ (tables of the paper)
scripts/run_experiments.sh   every experiment of the paper, step by step (see Reproducing the paper)
paper/                   make_results.py, make_figures.py: the numbers and figures of the paper from data/results
docker/, docker-compose.yml, requirements.txt, tests/
```

### Instances (`data/instances/<id>/`)

| File | Content |
|---|---|
| `nodes.csv` | node 0 = depot; stops with `lat, lon` (rounded, a delivery area), the dispatcher's `stop_seq` (real trips), the `message`, and the labels the message was written under: `message_id`, `band`, `ref_start_h`, `ref_end_h` |
| `distance.csv`, `duration.csv` | symmetric matrices in metres / seconds (road matrices for the real trips, scaled great-circle for the synthetic ones) |
| `concorde_tour.txt` | the exact minimum-distance tour (Concorde); `concorde.tsp` / `concorde.sol` for instances solved on NEOS |

The labels in `nodes.csv` are never read by the solvers; they are the reference of the evaluation.

## Requirements

- **Docker Desktop** (recommended) — nothing else is needed to reproduce the paper;
  or **Python 3.12** with `pip install -r requirements.txt` (OR-Tools 9.15, FastAPI, pydantic, matplotlib).
- Internet access only for new Concorde runs (NEOS Server, `NEOS_EMAIL` in `.env.local`) and for the
  LLM extractor (`GEMINI_API_KEY` in `.env.local`). The shipped instances contain the Concorde tours and
  the LLM answers are cached under `data/corpus/llm/`, so reproducing the tables works offline.

## Setup and run

```bash
git clone https://github.com/cezarpapara/lexicon-routing.git
cd lexicon-routing
docker compose up --build -d          # API at http://localhost:8001/docs
docker compose exec app-python sh     # shell inside the container; run the commands below there
pytest                                # 25 tests
```

## Reproducing the paper

One script runs every experiment of the paper, in order, inside the running container, and logs each
step to `data/results/logs/<step>.log`:

```bash
bash scripts/run_experiments.sh all            # check corpus build synth benchmark ablation report (2-3 h)
bash scripts/run_experiments.sh llm concorde   # optional: the LLM extractor (needs GEMINI_API_KEY) and the
                                               # exact tours of the synthetic instances (needs NEOS_EMAIL)
ONLY=SYN_ bash scripts/run_experiments.sh benchmark   # a step can be re-run on its own, here on the synthetic
                                               # instances only, e.g. after `concorde` for the Concorde row
```

| step | what it runs | what it produces | used in the paper |
|---|---|---|---|
| `check` | `pytest`; prints whether the API keys are set | — | — |
| `corpus` | `corpus`, `extract` | `data/corpus/corpus.csv`; extraction quality of the lexicon against `reference.csv` | Table 4, Fig. 2 |
| `build` | `build` | `data/instances/DAY_*`: the real trips with ≥ 4 stops, messages anchored on the executed plan | Section 4.5 |
| `synth` | `synth n --seed s` for n ∈ {25, 50, 100, 250, 500, 1000}, s ∈ {1, 2, 3} | `data/instances/SYN_n_s` | Section 4.5 |
| `benchmark` | `benchmark <instance>` for every instance | `data/results/<run>/benchmark.json`: all configurations, evaluated with the reference preferences | Tables 5-6, Figs 3-5 |
| `ablation` | `ablation <instance>` for `DAY_*` and `SYN_100_*` | `data/results/<run>/ablation.json`: one component removed or replaced at a time | Table 7, Fig. 6 |
| `llm` | `extract --extractor llm`, then `ablation` again | `data/corpus/llm/<model>.json` (cached answers); the LLM row of the ablation | Table 4, Table 7 |
| `concorde` | `concorde <instance>` for `SYN_*` on NEOS | `concorde_tour.txt` in each instance folder; then re-run `benchmark` for the Concorde row | Table 6 |
| `report` | `report` | `data/results/report/report.md`, `per_instance.csv` | all tables |

The numbers and figures of the paper are then collected from these files with the scripts in
[`paper/`](paper/README.md) (`make_results.py` → `paper/results.json`, `make_figures.py` → `paper/figs/`).

The same steps by hand, inside the container (`docker compose exec app-python sh`):

```bash
python -m app.cli corpus                       # corpus.csv + annotation_template.csv from the bank
python -m app.cli extract                      # Table: extraction quality of the lexicon on the corpus
python -m app.cli extract --extractor llm      # same for the LLM (needs GEMINI_API_KEY, answers cached)
python -m app.cli build                        # real trips -> data/instances (messages anchored on the executed plan)
for n in 25 50 100 250 500 1000; do for s in 1 2 3; do python -m app.cli synth $n --seed $s; done; done
for i in $(python -m app.cli instances); do python -m app.cli benchmark $i; done     # Tables: all configurations
for i in $(python -m app.cli instances | grep -E 'DAY_|SYN_100_'); do python -m app.cli ablation $i; done   # Table: ablation
python -m app.cli report                       # data/results/report/{report.md,per_instance.csv}
```

`benchmark` never contacts the network: on a synthetic instance the Concorde row is skipped until its tour
exists (`concorde SYN_<n>_<s>`, which submits the instance to NEOS and caches the tour).
Runtimes on a laptop: 30 s per OR-Tools run, under a second for the refinement on a real trip, up to
10 minutes per start on the 1000-stop instances (the refinement is capped at 600 s).

### Other commands

```bash
python -m app.cli messages DAY_4_TRUCK_4_TRIP_1          # messages with the extracted and reference preferences
python -m app.cli solve DAY_4_TRUCK_4_TRIP_1 guided      # one solver, one instance [--extractor lexicon|llm|oracle]
python -m app.cli concorde SYN_250_2                     # (re)solve an instance on NEOS
```

## Annotating the corpus

`data/corpus/annotation_template.csv` lists the 250 instantiated messages of the bank. The reviewed
labels are in `data/corpus/reference.csv`: `window_start`, `window_end` (HH:MM, or empty when the
message states no interval) and `band` (`none`, `flexible`, `mild`, `strong`, `binding`), obtained by
reading every message against `data/corpus/ANNOTATION_GUIDE.md` without looking at the lexicon.
`extract` and the routing evaluation use `reference.csv` when it is present and the bank labels
otherwise. To redo the review, fill the template and save it as `reference.csv`.

## License

Code: PolyForm Noncommercial License 1.0.0 (see LICENSE). Data (`data/source`, `data/corpus`,
`data/lexicon`, `data/instances`, `data/results/report`): CC BY-NC 4.0 (see LICENSE-DATA). The delivery
days in `data/source` are the anonymised dataset published with the compact-routing repository
(https://github.com/cezarpapara/compact-routing), reused under its license; the customer messages are
synthetic and were written by the authors — no real customer text is included.
