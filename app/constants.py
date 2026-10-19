"""Single source of truth for every modelling constant used in the paper.

Values marked with a source are taken from the cited reference and must not be
changed without updating the Methodology section of the paper.
"""

# --- Monetary cost coefficients (UNTRR / CNR road-transport reference report) ---
COST_PER_KM_RON = 3.17
COST_PER_HOUR_RON = 126.52

# --- Preference penalty: one hour of deviation from a customer's preferred interval, at full
#     urgency, is valued as one hour of vehicle time (lambda = c_t); no calibration involved.
PENALTY_PER_HOUR_RON = COST_PER_HOUR_RON

# --- Operations (store schedule and dispatcher estimate) ---
SERVICE_TIME_MIN = 15          # constant unloading time per stop
WORKING_DAY_START_H = 8.0      # 08:00
WORKING_DAY_END_H = 17.0       # 17:00
WORKING_DAY_HOURS = WORKING_DAY_END_H - WORKING_DAY_START_H
MIN_TRIP_STOPS = 4             # dispatcher trips with fewer stops are not used as instances

# --- Urgency bands (lower bound of the lexicon score u) and the reference urgency of each band ---
BANDS = ("flexible", "mild", "strong", "binding")
BAND_LOWER_BOUND = {"flexible": 0.0, "mild": 0.2, "strong": 0.45, "binding": 0.7}
BAND_URGENCY = {"none": 0.0, "flexible": 0.0, "mild": 0.25, "strong": 0.5, "binding": 1.0}
HARD_BAND = "binding"          # a binding preference becomes a hard time window

# --- Named periods of the day used in messages (clock hours) ---
NAMED_PERIODS = {
    "morning": (8.0, 12.0),
    "noon": (11.0, 14.0),
    "afternoon": (13.0, 17.0),
    "late_afternoon": (15.0, 17.0),
}

# --- Corpus: share of each message category among the stops of an instance ---
CATEGORY_MIX = {"binding": 0.20, "strong": 0.25, "mild": 0.20, "flexible": 0.20, "none": 0.15}
CORPUS_SEED = 2026

# --- Heuristics ---
ORTOOLS_TIME_LIMIT_S = 30
COST_SCALE = 1000              # RON -> integer milli-RON for OR-Tools (time cost = 35 per second)
CANDIDATE_POSITIONS = 25       # relocation positions tried per node on large instances (all if n is smaller)
MAX_PASSES = 200               # upper bound on local-search passes
SEARCH_TIME_LIMIT_S = 600      # cap on one run of the refinement (reached only on the largest instances)

# --- Concorde (TSP/concorde.c and HELDKARP/heldkarp.c in the Concorde sources) ---
CONCORDE_HELD_KARP_MAX_NODES = 9     # instances with fewer than 10 nodes go to the Held-Karp code ...
CONCORDE_HELD_KARP_MAX_EDGE = 32767  # ... which rejects edge weights above 2^15 ("edge too long")

# --- Data layout ---
DEPOT_NODE_ID = 0
NODES_FILE = "nodes.csv"
DISTANCE_FILE = "distance.csv"
DURATION_FILE = "duration.csv"
CONCORDE_TOUR_FILE = "concorde_tour.txt"
CONCORDE_TSP_FILE = "concorde.tsp"
CONCORDE_SOL_FILE = "concorde.sol"
BANK_FILE = "bank.json"
CORPUS_FILE = "corpus.csv"
ANNOTATION_TEMPLATE_FILE = "annotation_template.csv"
REFERENCE_FILE = "reference.csv"
LEXICON_FILE = "urgency_lexicon.csv"
