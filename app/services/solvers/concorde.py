"""Distance-optimal reference: the exact symmetric TSP tour of the instance, solved by Concorde.

Real trips reuse the tours cached with the source dataset (data/instances/<id>/concorde_tour.txt,
written by `build`). Synthetic instances are exported as TSPLIB files and solved on the NEOS
Server the first time they are needed; the NEOS log is cached as concorde.sol and the tour
as concorde_tour.txt, so that reproducing the tables never needs the network again.
"""

from __future__ import annotations

import re
from pathlib import Path

from app import constants as c
from app.models import Instance, Preference
from app.services import neos
from app.services.data import instance_dir
from app.services.solvers.base import BaseSolver

_EDGE_LINE = re.compile(r"^\s*(\d+)\s+(\d+)\s+-?\d+\s*$")


class ConcordeSolver(BaseSolver):
    name = "concorde"
    description = "Exact minimum-distance tour (Concorde with CPLEX), time-unaware"

    def build_route(self, instance: Instance, preferences: dict[int, Preference], **params) -> list[int]:
        folder = instance_dir(instance.id)
        cached = folder / c.CONCORDE_TOUR_FILE
        if cached.is_file():
            return [int(t) for t in cached.read_text().split()]
        tour = solve_on_neos(instance, folder)
        cached.write_text(" ".join(map(str, tour)) + "\n")
        return tour


def solve_on_neos(instance: Instance, folder: Path) -> list[int]:
    """Concorde tour of the instance (stops only, from the depot), via a cached .sol or a NEOS run."""
    sol = folder / c.CONCORDE_SOL_FILE
    if not (sol.is_file() and parse_tour(sol.read_text())):
        tsp = folder / c.CONCORDE_TSP_FILE
        tsp.write_text(tsplib(instance))
        text = neos.solve_tsp(tsp.read_text())
        if not parse_tour(text):
            raise RuntimeError(f"Concorde returned no tour for {instance.id}: {_error_summary(text)}")
        sol.write_text(text)
    tour = rotate_to_depot(parse_tour(sol.read_text()))
    if sorted(tour) != list(range(instance.size)):
        raise ValueError(f"{sol}: tour is not a permutation of the {instance.size} nodes")
    return tour[1:]


def tsplib(instance: Instance) -> str:
    """TSPLIB text of the metre matrix; small instances are scaled down for Concorde's Held-Karp code."""
    n = instance.size
    scale = 1
    if n <= c.CONCORDE_HELD_KARP_MAX_NODES:
        largest = max(max(row) for row in instance.distance_m)
        scale = -(-largest // c.CONCORDE_HELD_KARP_MAX_EDGE)      # smallest integer divisor that fits
    lines = [f"NAME: {instance.id}", "TYPE: TSP", f"COMMENT: edge weights = road metres / {scale}", f"DIMENSION: {n}",
             "EDGE_WEIGHT_TYPE: EXPLICIT", "EDGE_WEIGHT_FORMAT: LOWER_DIAG_ROW", "EDGE_WEIGHT_SECTION"]
    lines += [" ".join(str(instance.distance_m[i][j] // scale) for j in range(i + 1)) for i in range(n)]
    return "\n".join(lines) + "\nEOF\n"


def parse_tour(text: str) -> list[int]:
    """Tour from a Concorde output (NEOS log with 'Solution file output', or a bare tour file); [] if none."""
    lines = text.splitlines()
    edges = [(int(m.group(1)), int(m.group(2))) for m in map(_EDGE_LINE.match, lines) if m]
    if edges:
        return [a for a, _ in edges]
    if "Solution file output" in text:     # NEOS log without a tour = Concorde failed
        return []
    numbers = [int(tok) for line in lines for tok in line.split() if tok.lstrip("-").isdigit()]
    return numbers[1:] if numbers and numbers[0] == len(numbers) - 1 else numbers


def _error_summary(text: str) -> str:
    errors = [line.strip() for line in text.splitlines() if "failed" in line or "Error" in line or "too long" in line]
    return "; ".join(errors) or "no 'Solution file output' section"


def rotate_to_depot(tour: list[int]) -> list[int]:
    start = tour.index(c.DEPOT_NODE_ID)
    return tour[start:] + tour[:start]
