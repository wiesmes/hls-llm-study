#!/usr/bin/env bash
# Run independent experiments, retaining each harness exit code.
set -u
if [[ $# -ne 2 || ! $1 =~ ^[0-9]+$ || ! $2 =~ ^[0-9]+$ ]]; then
    echo "Usage: bash scripts/run_batch.sh METRICS_ONLY_COUNT FULL_COUNT" >&2
    exit 2
fi
metrics=$((10#$1))
full=$((10#$2))
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." || exit 1
export PATH="$PATH:/c/Program Files (x86)/GnuWin32/bin:/c/AMDDesignTools/2025.2/Vitis/bin"
mkdir -p results logs/batch || exit 1
next=metrics_only
while (( metrics > 0 || full > 0 )); do
    if [[ $next == metrics_only ]] && (( metrics > 0 )) || (( full == 0 )); then
        condition=metrics_only
        metrics=$((metrics - 1))
        next=full
    else
        condition=full
        full=$((full - 1))
        next=metrics_only
    fi
    start=$(date --iso-8601=seconds)
    output=$(mktemp) || exit 1
    py -u scripts/harness.py "$condition" > "$output" 2>&1
    code=$?
    end=$(date --iso-8601=seconds)
    cat "$output"
    run_id=$(sed -n 's/^Run ID: //p' "$output" | head -n 1 | tr -d '\r')
    if [[ -n $run_id ]]; then
        cp "$output" "logs/batch/${run_id}.log"
    fi
    printf 'start=%s\tend=%s\tcondition=%s\trun_id=%s\texit_code=%s\n' \
        "$start" "$end" "$condition" "${run_id:-unknown}" "$code" >> results/batch_log.txt
    rm -f -- "$output"
done
