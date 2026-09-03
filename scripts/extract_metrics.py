#!/usr/bin/env python3
"""
Parse a Vitis HLS csynth XML report into one row of results.csv.

Usage:
  python3 extract_metrics.py <proj_dir> <top> <label> <results_csv>

<label> is how this design point is identified in the paper, e.g.
  vecadd_naive, conv2d_naive, conv2d_hand_v7, conv2d_llm_s3_iter2
"""

import csv
import os
import sys
import datetime
import xml.etree.ElementTree as ET

FIELDS = [
    "label", "timestamp", "top", "part", "target_period_ns",
    "estimated_period_ns", "latency_min", "latency_max", "interval_min",
    "lut", "ff", "bram", "dsp", "uram",
]


def text(root, path):
    node = root.find(path)
    return node.text.strip() if node is not None and node.text else ""


def main():
    if len(sys.argv) != 5:
        print(__doc__)
        sys.exit(2)

    proj_dir, top, label, out_csv = sys.argv[1:5]

    report = os.path.join(
        proj_dir, "solution1", "syn", "report", f"{top}_csynth.xml"
    )
    if not os.path.exists(report):
        # Older/newer tool versions nest reports differently; look for it.
        for dirpath, _, files in os.walk(proj_dir):
            for f in files:
                if f == f"{top}_csynth.xml":
                    report = os.path.join(dirpath, f)
                    break
    if not os.path.exists(report):
        sys.exit(f"ERROR: could not find {top}_csynth.xml under {proj_dir}")

    root = ET.parse(report).getroot()

    row = {
        "label": label,
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "top": top,
        "part": text(root, "./UserAssignments/Part"),
        "target_period_ns": text(root, "./UserAssignments/TargetClockPeriod"),
        "estimated_period_ns": text(
            root, "./PerformanceEstimates/SummaryOfTimingAnalysis/EstimatedClockPeriod"),
        "latency_min": text(
            root, "./PerformanceEstimates/SummaryOfOverallLatency/Best-caseLatency"),
        "latency_max": text(
            root, "./PerformanceEstimates/SummaryOfOverallLatency/Worst-caseLatency"),
        "interval_min": text(
            root, "./PerformanceEstimates/SummaryOfOverallLatency/Interval-min"),
        "lut": text(root, "./AreaEstimates/Resources/LUT"),
        "ff": text(root, "./AreaEstimates/Resources/FF"),
        "bram": text(root, "./AreaEstimates/Resources/BRAM_18K"),
        "dsp": text(root, "./AreaEstimates/Resources/DSP"),
        "uram": text(root, "./AreaEstimates/Resources/URAM"),
    }

    new_file = not os.path.exists(out_csv)
    with open(out_csv, "a", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow(row)

    print(f"Appended '{label}' to {out_csv}")
    for k in ("latency_max", "interval_min", "lut", "ff", "bram", "dsp"):
        print(f"  {k:20s} {row[k]}")


if __name__ == "__main__":
    main()
