from app.services.solvers.adaptive import AdaptiveSolver
from app.services.solvers.base import BaseSolver, SolverRegistry
from app.services.solvers.concorde import ConcordeSolver
from app.services.solvers.dispatcher import DispatcherSolver
from app.services.solvers.guided import GuidedSolver
from app.services.solvers.nearest_neighbour import NearestNeighbourSolver
from app.services.solvers.ortools_tw import OrToolsWindowsSolver

DISPATCHER, NEAREST, CONCORDE, ORTOOLS, ADAPTIVE, GUIDED = "dispatcher", "nearest", "concorde", "ortools", "adaptive", "guided"
ORDER = (DISPATCHER, NEAREST, CONCORDE, ORTOOLS, ADAPTIVE, GUIDED)


def auto_register_all() -> None:
    for solver in (DispatcherSolver(), NearestNeighbourSolver(), ConcordeSolver(), OrToolsWindowsSolver(),
                   AdaptiveSolver(), GuidedSolver()):
        SolverRegistry.register(solver)


__all__ = ["BaseSolver", "SolverRegistry", "auto_register_all", "ORDER",
           "DISPATCHER", "NEAREST", "CONCORDE", "ORTOOLS", "ADAPTIVE", "GUIDED"]
