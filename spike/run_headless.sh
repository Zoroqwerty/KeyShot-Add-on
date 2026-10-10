#!/usr/bin/env bash
# Repeat the spike in fresh headless KeyShot processes, then summarize.
#
#   KEYSHOT_HEADLESS="/path/to/KeyShot's headless executable" ./run_headless.sh 20 E1,E2,E3
#
# The headless executable path and its argument format are NOT verified for macOS: check the
# KeyShot manual page "Headless Scripting" for your version and set KEYSHOT_HEADLESS_ARGS if the
# script flag differs from "-script".
set -uo pipefail

RUNS="${1:-10}"
EXPERIMENTS="${2:-E1,E2,E3,E6,E7}"
HERE="$(cd "$(dirname "$0")" && pwd)"
: "${KEYSHOT_HEADLESS:?Set KEYSHOT_HEADLESS to the KeyShot headless executable}"
ARGS="${KEYSHOT_HEADLESS_ARGS:--script}"

for i in $(seq 1 "$RUNS"); do
  echo "=== run $i / $RUNS ($EXPERIMENTS)"
  JLE_SPIKE_HOME="$HERE" JLE_SPIKE_EXPERIMENTS="$EXPERIMENTS" \
    "$KEYSHOT_HEADLESS" $ARGS "$HERE/JLE Spike - Run All.py" || echo "run $i exited with status $?"
done

python3 "$HERE/summarize.py"
