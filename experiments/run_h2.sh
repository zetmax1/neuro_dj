#!/usr/bin/env bash
# Start the H2 pass detached, so it survives the shell that launched it.
#
# A full pass takes hours (the bounded grid search alone is ~16 minutes per
# fold on the full dataset), which is longer than an interactive session
# reliably lasts.
#
#   experiments/run_h2.sh quick     # 500 learners, 3 epochs
#   experiments/run_h2.sh full      # the whole dataset
#   experiments/run_h2.sh both      # quick, then full
#
# Progress: tail -f experiments/.runs/h2-<mode>.log
#
# Why systemd-run and not setsid. The first detached pass died at 15:48 on
# 2026-10-06 without a "finished" line: the kernel's OOM killer took the
# python process, and because setsid leaves a process in the cgroup of
# whatever launched it — there, a browser's scope — systemd then tore down
# that whole scope, the bash wrapper with it. The run inherited the browser's
# oom_score_adj (200) as well, so it was the first thing chosen. A transient
# user unit gives the run its own cgroup, the user manager's OOM score, and
# OOMPolicy=continue keeps the wrapper alive to log the exit status if python
# is killed anyway. setsid remains as a fallback where there is no user
# systemd, and says so.
#
# Environment (for tests and debugging):
#   H2_PY        interpreter            (default experiments/.venv/bin/python)
#   H2_LOGS      log directory          (default experiments/.runs)
#   H2_LAUNCHER  systemd | setsid | inline   (default: systemd if available)
set -euo pipefail

cd "$(dirname "$0")/.."
MODE="${1:-both}"
PY="${H2_PY:-experiments/.venv/bin/python}"
LOGS="${H2_LOGS:-experiments/.runs}"
mkdir -p "$LOGS"

if [[ ! -x "$PY" ]]; then
    echo "$PY is missing; see experiments/README.md" >&2
    exit 2
fi

run() {
    local name="$1"; shift
    echo "[$(date -Is)] starting $name: $*" >> "$LOGS/h2-$name.log"
    # The status is captured before anything else runs: $(date -Is) in the
    # line below executes first and would reset $? to its own success, so a
    # failed run reported "exit 0" and the chain carried on as if it had
    # worked. `|| status=$?` keeps a non-zero exit from ending the shell
    # before the line is written.
    local status=0
    "$PY" -u -W ignore -m experiments.h2 "$@" >> "$LOGS/h2-$name.log" 2>&1 || status=$?
    echo "[$(date -Is)] finished $name (exit $status)" >> "$LOGS/h2-$name.log"
    return $status
}

case "$MODE" in
    quick) CHAIN="run quick --quick" ;;
    full)  CHAIN="run full" ;;
    both)  CHAIN="run quick --quick && run full" ;;
    *) echo "usage: $0 {quick|full|both}" >&2; exit 2 ;;
esac
BODY="$(declare -f run); LOGS='$LOGS' PY='$PY'; $CHAIN"

LAUNCHER="${H2_LAUNCHER:-}"
if [[ -z "$LAUNCHER" ]]; then
    if command -v systemd-run >/dev/null 2>&1 && systemctl --user show-environment >/dev/null 2>&1; then
        LAUNCHER=systemd
    else
        LAUNCHER=setsid
    fi
fi

case "$LAUNCHER" in
    systemd)
        UNIT="neurolearn-h2-$MODE-$(date +%Y%m%d-%H%M%S)"
        ENV_ARGS=()
        [[ -n "${NEUROLEARN_DATA:-}" ]] && ENV_ARGS+=(--setenv=NEUROLEARN_DATA="$NEUROLEARN_DATA")
        systemd-run --user --collect --quiet --same-dir --unit="$UNIT" \
            -p OOMPolicy=continue -p OOMScoreAdjust=100 \
            "${ENV_ARGS[@]}" bash -c "$BODY"
        echo "started ($MODE) as user unit $UNIT. Progress: tail -f $LOGS/h2-*.log"
        echo "  status: systemctl --user status $UNIT"
        ;;
    setsid)
        echo "warning: no user systemd; setsid keeps the run in this shell's cgroup" >&2
        setsid nohup bash -c "$BODY" </dev/null >/dev/null 2>&1 &
        echo "started ($MODE), detached. Progress: tail -f $LOGS/h2-*.log"
        ;;
    inline)
        bash -c "$BODY"
        ;;
    *) echo "unknown H2_LAUNCHER: $LAUNCHER" >&2; exit 2 ;;
esac
