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
#   experiments/run_h2.sh bounds-quick | bounds-full | bounds-both
#                                   # D55, experiments.h2_bounds, the same way
#   experiments/run_h2.sh frozen-quick | frozen-full | frozen-both
#                                   # D60, experiments.h2_frozen, the same way
#   experiments/run_h2.sh h1-quick | h1-full | h1-both
#   experiments/run_h2.sh h3-quick | h3-full | h3-both
#                                   # D61, Junyi: experiments.h1 / experiments.h3
#   experiments/run_h2.sh junyi-quick | junyi-full | junyi-both
#                                   # both hypotheses of D61, h1 then h3
#
# The Junyi modes read a 2.6 GB log, so the inventory pass alone takes a while
# and the log lines of each pass show its progress (D61). They take no
# --reference: H1 and H3 reproduce nothing of H2, they are different
# hypotheses on a different dataset.
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
#   H2_SAMPLE_SECONDS  memory sample interval  (default 60)
#   H2_REFERENCE  the H2 result the bounds and frozen modes must reproduce
#                 (D58, D59, D60); passed as --reference, and those runs refuse
#                 to start without it
#   H2_WORKERS    processes for the parameter fits, passed as --workers. Without
#                 it the module picks min(8, cpu/2), which on this machine is 8;
#                 the fits of the full dataset need ~0.25 GiB each, so the count
#                 is chosen from the memory the run may take (D59)
#
# What the log shows, so the cause of the next stop can be read without the
# journal. The full pass of 2026-10-06 stopped at 16:53 and the bounds pass at
# 22:55 with no "finished" line, and by the time anyone looked the journal was
# gone (the machine was reinstalled the next day). Now:
# - every SAMPLE seconds a "memory:" line — the python process's RSS and peak
#   (VmHWM), its children's RSS added in, MemAvailable and SwapFree — so a
#   run that dies of memory pressure leaves the pressure in its own log;
# - "finished <stage> (exit N)" with the sampled peak, from the wrapper;
# - under systemd, "unit … ended:" from ExecStopPost, which systemd runs
#   however the unit ends — killed, OOM-killed, or stopped with the session —
#   with SERVICE_RESULT, EXIT_CODE and EXIT_STATUS, and the unit's own
#   Result and ExecMainStatus. A log with neither of the last two lines is a
#   machine that went down.
set -euo pipefail

cd "$(dirname "$0")/.."
MODE="${1:-both}"
PY="${H2_PY:-experiments/.venv/bin/python}"
LOGS="${H2_LOGS:-experiments/.runs}"
SAMPLE="${H2_SAMPLE_SECONDS:-60}"
mkdir -p "$LOGS"

# ExecStopPost of the unit below: write how the unit ended into the log of
# the stage it was running. Called by systemd, not by hand.
if [[ "$MODE" == "__ended" ]]; then
    UNIT="$2"
    STAGE="$(cat "$LOGS/.stage-$UNIT" 2>/dev/null || echo unit)"
    SHOWN="$(systemctl --user show -p Result -p ExecMainStatus "$UNIT" 2>/dev/null | paste -sd' ' || true)"
    echo "[$(date -Is)] unit $UNIT ended: SERVICE_RESULT=${SERVICE_RESULT:-?}" \
         "EXIT_CODE=${EXIT_CODE:-?} EXIT_STATUS=${EXIT_STATUS:-?}; ${SHOWN:-unit state unavailable}" \
         >> "$LOGS/h2-$STAGE.log"
    rm -f "$LOGS/.stage-$UNIT"
    exit 0
fi

if [[ ! -x "$PY" ]]; then
    echo "$PY is missing; see experiments/README.md" >&2
    exit 2
fi

memory() {
    # One "memory:" line for process $1, sizes in kB. Children (worker
    # processes) are added into tree_rss; the peak of the sampled tree is kept
    # in $2 for the "finished" line.
    local pid="$1" peak_file="$2" rss hwm children tree avail swap peak
    rss="$(awk '/^VmRSS:/{print $2}' "/proc/$pid/status" 2>/dev/null)"
    hwm="$(awk '/^VmHWM:/{print $2}' "/proc/$pid/status" 2>/dev/null)"
    [[ -n "$rss" ]] || return 0
    children="$(ps -o rss= --ppid "$pid" 2>/dev/null | awk '{s+=$1} END{print s+0}')"
    tree=$(( rss + children ))
    avail="$(awk '/^MemAvailable:/{print $2}' /proc/meminfo)"
    swap="$(awk '/^SwapFree:/{print $2}' /proc/meminfo)"
    peak="$(cat "$peak_file" 2>/dev/null || echo 0)"
    (( tree > peak )) && echo "$tree" > "$peak_file"
    echo "[$(date -Is)] memory: rss_kb=$rss hwm_kb=${hwm:-?} tree_rss_kb=$tree" \
         "mem_available_kb=$avail swap_free_kb=$swap"
}

sample() {
    # Every $SAMPLE seconds until process $1 exits. The sleep is a child that
    # TERM takes down with the loop, so stopping the sampler is immediate.
    local pid="$1" peak_file="$2" nap
    trap 'kill "$nap" 2>/dev/null; exit 0' TERM
    while kill -0 "$pid" 2>/dev/null; do
        memory "$pid" "$peak_file"
        sleep "$SAMPLE" & nap=$!
        wait "$nap"
    done
}

run() {
    local name="$1" module="$2"; shift 2
    local log="$LOGS/h2-$name.log" peak_file="$LOGS/.peak-$name"
    echo "[$(date -Is)] starting $name: $*" >> "$log"
    [[ -n "${UNIT:-}" ]] && echo "$name" > "$LOGS/.stage-$UNIT"
    # The status is captured before anything else runs: $(date -Is) in the
    # line below executes first and would reset $? to its own success, so a
    # failed run reported "exit 0" and the chain carried on as if it had
    # worked. `|| status=$?` keeps a non-zero exit from ending the shell
    # before the line is written.
    local status=0 pid sampler peak
    echo 0 > "$peak_file"
    "$PY" -u -W ignore -m "$module" "$@" >> "$log" 2>&1 &
    pid=$!
    sample "$pid" "$peak_file" >> "$log" 2>&1 &
    sampler=$!
    wait "$pid" || status=$?
    kill "$sampler" 2>/dev/null || true
    wait "$sampler" 2>/dev/null || true
    peak="$(cat "$peak_file" 2>/dev/null || echo 0)"
    rm -f "$peak_file"
    echo "[$(date -Is)] finished $name (exit $status); peak sampled tree_rss_kb=$peak" >> "$log"
    return $status
}

H2=experiments.h2
BOUNDS=experiments.h2_bounds
FROZEN=experiments.h2_frozen
H1=experiments.h1
H3=experiments.h3
REF=""
[[ -n "${H2_REFERENCE:-}" ]] && REF="--reference $H2_REFERENCE"
POOL=""
[[ -n "${H2_WORKERS:-}" ]] && POOL="--workers $H2_WORKERS"
case "$MODE" in
    quick) CHAIN="run quick $H2 --quick $POOL" ;;
    full)  CHAIN="run full $H2 $POOL" ;;
    both)  CHAIN="run quick $H2 --quick $POOL && run full $H2 $POOL" ;;
    bounds-quick) CHAIN="run bounds-quick $BOUNDS --quick $REF $POOL" ;;
    bounds-full)  CHAIN="run bounds-full $BOUNDS $REF $POOL" ;;
    bounds-both) CHAIN="run bounds-quick $BOUNDS --quick $REF $POOL && run bounds-full $BOUNDS $REF $POOL" ;;
    frozen-quick) CHAIN="run frozen-quick $FROZEN --quick $REF $POOL" ;;
    frozen-full)  CHAIN="run frozen-full $FROZEN $REF $POOL" ;;
    frozen-both) CHAIN="run frozen-quick $FROZEN --quick $REF $POOL && run frozen-full $FROZEN $REF $POOL" ;;
    h1-quick) CHAIN="run h1-quick $H1 --quick $POOL" ;;
    h1-full)  CHAIN="run h1-full $H1 $POOL" ;;
    h1-both)  CHAIN="run h1-quick $H1 --quick $POOL && run h1-full $H1 $POOL" ;;
    h3-quick) CHAIN="run h3-quick $H3 --quick $POOL" ;;
    h3-full)  CHAIN="run h3-full $H3 $POOL" ;;
    h3-both)  CHAIN="run h3-quick $H3 --quick $POOL && run h3-full $H3 $POOL" ;;
    junyi-quick) CHAIN="run h1-quick $H1 --quick $POOL && run h3-quick $H3 --quick $POOL" ;;
    junyi-full)  CHAIN="run h1-full $H1 $POOL && run h3-full $H3 $POOL" ;;
    junyi-both)  CHAIN="run h1-quick $H1 --quick $POOL && run h3-quick $H3 --quick $POOL \
                        && run h1-full $H1 $POOL && run h3-full $H3 $POOL" ;;
    *) echo "usage: $0 {quick|full|both|bounds-quick|bounds-full|bounds-both|frozen-quick|frozen-full|frozen-both|h1-quick|h1-full|h1-both|h3-quick|h3-full|h3-both|junyi-quick|junyi-full|junyi-both}" >&2; exit 2 ;;
esac

LAUNCHER="${H2_LAUNCHER:-}"
if [[ -z "$LAUNCHER" ]]; then
    if command -v systemd-run >/dev/null 2>&1 && systemctl --user show-environment >/dev/null 2>&1; then
        LAUNCHER=systemd
    else
        LAUNCHER=setsid
    fi
fi
UNIT=""
[[ "$LAUNCHER" == systemd ]] && UNIT="neurolearn-h2-$MODE-$(date +%Y%m%d-%H%M%S)"
BODY="$(declare -f memory sample run); LOGS='$LOGS' PY='$PY' SAMPLE='$SAMPLE' UNIT='$UNIT'; $CHAIN"

case "$LAUNCHER" in
    systemd)
        ENV_ARGS=(--setenv=H2_LOGS="$LOGS")
        # The body is shell, not a unit file line: systemd would otherwise
        # expand $VAR and turn $$ into $ before bash ever saw it.
        systemd-run --help 2>/dev/null | grep -q -- --expand-environment \
            && ENV_ARGS+=(--expand-environment=no)
        [[ -n "${NEUROLEARN_DATA:-}" ]] && ENV_ARGS+=(--setenv=NEUROLEARN_DATA="$NEUROLEARN_DATA")
        # The full H2 pass of 2026-10-08 died with the laptop's battery; a
        # suspend would stop a run just as surely. systemd-inhibit holds a
        # sleep/idle block for as long as the body runs (tested from a user
        # unit on this machine). Without it the run still starts, and says so.
        INHIBIT=()
        if command -v systemd-inhibit >/dev/null 2>&1; then
            INHIBIT=(systemd-inhibit --what=sleep:idle --who="$UNIT" --why="NeuroLearn experiment run" --mode=block)
        else
            echo "warning: systemd-inhibit not found; the machine may sleep during the run" >&2
        fi
        systemd-run --user --collect --quiet --same-dir --unit="$UNIT" \
            -p OOMPolicy=continue -p OOMScoreAdjust=100 \
            -p ExecStopPost="/bin/bash $PWD/experiments/run_h2.sh __ended $UNIT" \
            "${ENV_ARGS[@]}" "${INHIBIT[@]}" bash -c "$BODY"
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
