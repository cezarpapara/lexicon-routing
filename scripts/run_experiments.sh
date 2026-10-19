#!/usr/bin/env bash
# Runs the experiments of the paper, step by step, inside the running Docker container.
#
#   scripts/run_experiments.sh all            every step below, in order
#   scripts/run_experiments.sh <step> [...]   one or more steps: check corpus build synth benchmark ablation llm concorde report
#   ONLY=SYN_ scripts/run_experiments.sh benchmark   restrict benchmark / ablation / concorde to the instances matching a pattern
#
# Each step appends its output to data/results/logs/<step>.log. Results land in data/results/<run_id>/
# (benchmark.json, ablation.json), data/results/report/ (report.md, per_instance.csv) and
# data/corpus/llm/<model>.json (cached Gemini answers). Steps are idempotent: a step can be re-run.
set -euo pipefail

cd "$(dirname "$0")/.."
LOG_DIR=data/results/logs
mkdir -p "$LOG_DIR"

run() {                                    # run <python -m app.cli ...> inside the container
  docker compose exec -T app-python "$@"
}

step_check() {                             # tests + the two API keys
  run pytest -q
  run python -c "from app.config import get_settings as s; print('NEOS_EMAIL set:', bool(s().NEOS_EMAIL), '| GEMINI_API_KEY set:', bool(s().GEMINI_API_KEY), '| model:', s().GEMINI_MODEL)"
}

step_corpus() {                            # corpus.csv + annotation_template.csv; extraction quality (Table 4, Fig. 2)
  run python -m app.cli corpus
  run python -m app.cli extract
}

step_build() {                             # the 18 real trips -> data/instances/DAY_*
  run python -m app.cli build
}

step_synth() {                             # 18 synthetic instances -> data/instances/SYN_<n>_<seed>
  for n in 25 50 100 250 500 1000; do
    for s in 1 2 3; do run python -m app.cli synth "$n" --seed "$s"; done
  done
  run python -m app.cli instances
}

instances() {                              # instance ids, optionally filtered by $ONLY (a grep pattern)
  run python -m app.cli instances | grep -E "${ONLY:-.}"
}

step_benchmark() {                         # all configurations on every instance (Tables 5-6, Figs 3-5)
  for i in $(instances); do
    echo "== benchmark $i $(date +%H:%M:%S)"
    run python -m app.cli benchmark "$i"
  done
}

step_ablation() {                          # variants of the method on the real trips and SYN_100_* (Table 7, Fig. 6)
  for i in $(instances | grep -E 'DAY_|SYN_100_'); do
    echo "== ablation $i $(date +%H:%M:%S)"
    run python -m app.cli ablation "$i"
  done
}

step_llm() {                               # Gemini reads the corpus (answers cached), then the LLM row of the ablation
  run python -m app.cli extract --extractor llm || echo "   LLM extraction failed; the ablation will skip the LLM row"
  step_ablation
}

step_concorde() {                          # exact tours of the synthetic instances on NEOS (optional, slow)
  for i in $(instances | grep SYN_); do
    echo "== concorde $i $(date +%H:%M:%S)"
    run python -m app.cli concorde "$i" || echo "   NEOS failed for $i, skipped"
  done
}

step_report() {                            # data/results/report/{report.md, per_instance.csv}
  run python -m app.cli report
}

STEPS="check corpus build synth benchmark ablation report"
[ "$#" -gt 0 ] || { echo "usage: $0 all | step ..."; exit 1; }
[ "$1" = all ] && set -- $STEPS
for step in "$@"; do
  echo "##### $step  $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_DIR/$step.log"
  "step_$step" 2>&1 | tee -a "$LOG_DIR/$step.log"
done
echo "##### done $(date '+%Y-%m-%d %H:%M:%S')"
