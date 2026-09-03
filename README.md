# HLS + LLM Independent Study

Measuring harness for the study:
**To what extent can an LLM generate and iteratively optimize HLS
implementations of ML inference kernels using FPGA synthesis feedback?**

## What this repo is

A pipeline that takes a `.cpp` kernel, checks it computes the right answer,
synthesizes it to hardware, and appends one row of metrics to
`results/results.csv`. Every design point in the paper — naive, hand-optimized,
and LLM-generated — goes through this same path. Nothing is measured by hand.

## Layout

```
kernels/<name>/     kernel source, header, and testbench
scripts/run_hls.tcl batch-mode Vitis HLS driver (no GUI)
scripts/extract_metrics.py   report XML -> CSV row
results/results.csv every design point ever measured
notebook/           one file per work session
build/              generated, gitignored
```

## Before the first run

Open the `Makefile` and set `PART` to your lab board's actual part number.
Resource and power numbers mean nothing without it. Confirm the part is
included in the free/Standard edition device set.

## Usage

```bash
make bench KERNEL=vecadd
make bench KERNEL=conv2d LABEL=conv2d_hand_v7
```

`vecadd` is a throwaway kernel that exists only to prove the harness works.
It is not part of the study.

## The correctness gate

`tb_<kernel>.cpp` returns non-zero on mismatch, which makes `csim_design` fail
and stops the flow before synthesis. This is deliberate: a design that computes
garbage can look excellent on latency, and must never contribute a row to
`results.csv`.

## Week 1 checklist

- [ ] Vitis HLS + Vivado installed
- [ ] Lab board identified; part number recorded here: `____________`
- [ ] Part confirmed present in free edition device list
- [ ] `make bench KERNEL=vecadd` runs start to finish without opening the GUI
- [ ] `results/results.csv` contains one row
- [ ] Deliberately break the testbench (change the golden answer), confirm the
      run fails and writes no row, then change it back
- [ ] Repo pushed, notebook entries written for both sessions

The last checklist item matters as much as the others. An untested gate is not
a gate.

## Still open

- Power measurement is not wired up yet. That needs Vivado implementation plus
  `report_power` with a SAIF, and lands in weeks 3–4.
- The real kernel (conv2d or GEMM) is not chosen yet. Week 3.
