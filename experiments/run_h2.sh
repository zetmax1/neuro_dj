#!/usr/bin/env bash
# Start the H2 pass detached, so it survives the shell that launched it.
#
# A full pass takes hours (the bounded grid search alone is ~16 minutes per
# fold on the full dataset), which is longer than an interactive session
# reliably lasts. setsid puts it in its own session: closing the terminal, or
# the agent that started it going away, does not take the run with it.
#
#   experiments/run_h2.sh quick     # 500 learners, 3 epochs
#   experiments/run_h2.sh full      # the whole dataset
#   experiments/run_h2.sh both      # quick, then full
#
# Progress: tail -f experiments/.runs/h2-<mode>.log
set -euo pipefail

cd "$(dirname "$0")/.."
MODE="${1:-both}"
PY=experiments/.venv/bin/python
LOGS=experiments/.runs
mkdir -p "$LOGS"

if [[ ! -x "$PY" ]]; then
    echo "experiments/.venv is missing; see experiments/README.md" >&2
    exit 2
fi

run() {
    local name="$1"; shift
    echo "[$(date -Is)] starting $name: $*" >> "$LOGS/h2-$name.log"
    # The status is captured before anything else runs: $(date -Is) in the
    # line below executes first and would reset $? to its own success, so a
    # failed run reported "exit 0" and the chain carried on as if it had
    # worked.
    "$PY" -u -W ignore -m experiments.h2 "$@" >> "$LOGS/h2-$name.log" 2>&1
    local status=$?
    echo "[$(date -Is)] finished $name (exit $status)" >> "$LOGS/h2-$name.log"
    return $status
}

case "$MODE" in
    quick) setsid nohup bash -c "$(declare -f run); LOGS=$LOGS PY=$PY; run quick --quick" </dev/null >/dev/null 2>&1 & ;;
    full)  setsid nohup bash -c "$(declare -f run); LOGS=$LOGS PY=$PY; run full" </dev/null >/dev/null 2>&1 & ;;
    both)  setsid nohup bash -c "$(declare -f run); LOGS=$LOGS PY=$PY; run quick --quick && run full" </dev/null >/dev/null 2>&1 & ;;
    *) echo "usage: $0 {quick|full|both}" >&2; exit 2 ;;
esac

echo "started ($MODE), detached. Progress: tail -f $LOGS/h2-*.log"
