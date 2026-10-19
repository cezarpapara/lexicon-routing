"""Command line entry points: python -m app.cli <command>."""

from __future__ import annotations

import argparse

from app import constants as c
from app.services import benchmark, data
from app.services.solvers import ORDER, SolverRegistry, auto_register_all


def main() -> None:
    parser = argparse.ArgumentParser(prog="lexicon-routing")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("corpus", help="instantiate the message bank: corpus.csv + annotation_template.csv")
    commands.add_parser("build", help="source days -> one instance per dispatcher trip, with customer messages")
    synth = commands.add_parser("synth", help="synthetic instance sampled from the real stops (offline matrices)")
    synth.add_argument("stops", type=int)
    synth.add_argument("--seed", type=int, default=1)
    commands.add_parser("instances", help="list available instances")
    extract = commands.add_parser("extract", help="extraction quality of an extractor on the corpus")
    extract.add_argument("--extractor", default="lexicon", choices=("lexicon", "llm"))
    show = commands.add_parser("messages", help="messages of an instance with the extracted and reference preferences")
    show.add_argument("instance")
    solve = commands.add_parser("solve", help="run one solver on one instance")
    solve.add_argument("instance")
    solve.add_argument("solver", choices=ORDER)
    solve.add_argument("--extractor", default="lexicon", choices=("lexicon", "llm", "oracle"))
    bench = commands.add_parser("benchmark", help="run all configurations on one instance")
    bench.add_argument("instance")
    bench.add_argument("--extractor", default="lexicon", choices=("lexicon", "llm", "oracle"))
    bench.add_argument("--time-limit", type=int, default=c.ORTOOLS_TIME_LIMIT_S, help="OR-Tools time limit (s)")
    concorde = commands.add_parser("concorde", help="solve an instance on NEOS (cached as concorde.sol / concorde_tour.txt)")
    concorde.add_argument("instance")
    ablation = commands.add_parser("ablation", help="variants of the proposed method on one instance")
    ablation.add_argument("instance")
    ablation.add_argument("--time-limit", type=int, default=c.ORTOOLS_TIME_LIMIT_S)
    report = commands.add_parser("report", help="tables + figure over the latest run of every instance")
    report.add_argument("runs", nargs="*", help="run ids (default: latest per instance)")

    args = parser.parse_args()
    auto_register_all()
    {"corpus": _corpus, "build": _build, "synth": _synth, "instances": _instances, "extract": _extract, "messages": _messages,
     "solve": _solve, "benchmark": _benchmark, "concorde": _concorde, "ablation": _ablation, "report": _report}[args.command](args)


def _corpus(_) -> None:
    from app.services.corpus import write_corpus
    print("written:", *write_corpus())


def _build(_) -> None:
    print("built:", ", ".join(data.build_instances()))


def _synth(args) -> None:
    from app.services.synth import generate
    print("built:", generate(args.stops, args.seed))


def _instances(_) -> None:
    print("\n".join(data.list_instances()))


def _extract(args) -> None:
    from app.services import quality
    result = quality.assess_lexicon() if args.extractor == "lexicon" else quality.assess_llm()
    print(result.model_dump_json(indent=2))


def _messages(args) -> None:
    from app.services import corpus, extractors
    instance = data.load_instance(args.instance)
    extracted, references = extractors.preferences(instance), corpus.references(instance)
    for node in instance.stops:
        e, r = extracted[node.id], references[node.id]
        print(f"{node.id:>4}  ref={r.band:<8} [{_hour(r.start_h)}-{_hour(r.end_h)}]  "
              f"lex={e.band:<8} u={e.urgency:.2f} [{_hour(e.start_h)}-{_hour(e.end_h)}]  {node.message}")


def _hour(h: float | None) -> str:
    return "  -  " if h is None else f"{int(h):02d}:{int(round((h % 1) * 60)):02d}"


def _solve(args) -> None:
    from app.services import corpus, extractors, metrics
    instance = data.load_instance(args.instance)
    preferences = extractors.preferences(instance, args.extractor)
    solution = SolverRegistry.get(args.solver).solve(instance, preferences)
    print("route:", " ".join(map(str, solution.route)))
    print(metrics.evaluate(instance, solution, corpus.references(instance)).model_dump_json(indent=2))


def _benchmark(args) -> None:
    result = benchmark.run(args.instance, extractor=args.extractor, time_limit_s=args.time_limit)
    print(f"run {result.run_id}: skipped={result.skipped}")
    for e in result.evaluations:
        print(f"{e.solver:<11} D={e.distance_km:>8.2f} km  T={e.duration_h:>6.2f} h  wait={e.waiting_h:>5.2f} h  "
              f"C_m={e.monetary_cost_ron:>9.2f}  P={e.penalty_h:>6.2f} h  C={e.composite_cost_ron:>9.2f} RON  "
              f"met={e.met}/{e.stated} ({e.satisfaction_pct}%)  binding missed={e.binding_missed}  {e.runtime_s} s")


def _concorde(args) -> None:
    from app.services.solvers.concorde import solve_on_neos
    instance = data.load_instance(args.instance)
    tour = solve_on_neos(instance, data.instance_dir(args.instance))
    (data.instance_dir(args.instance) / c.CONCORDE_TOUR_FILE).write_text(" ".join(map(str, tour)) + "\n")
    print("tour:", " ".join(map(str, tour)))


def _ablation(args) -> None:
    from app.services.ablation import run
    result = run(args.instance, time_limit_s=args.time_limit)
    for v in result.variants:
        print(f"{v.solver:<40} C={v.composite_cost_ron:>9.2f}  C_m={v.monetary_cost_ron:>9.2f}  P={v.penalty_h:>6.2f} h  "
              f"met={v.satisfaction_pct}%  binding missed={v.binding_missed}  {v.runtime_s} s")
    if result.skipped:
        print("skipped:", result.skipped)


def _report(args) -> None:
    from app.services.report import build
    folder = build(args.runs or None)
    print((folder / "report.md").read_text())


if __name__ == "__main__":
    main()
