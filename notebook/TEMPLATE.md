# Session: 2026-09-03 (Tue)

## Goal for today
Get a working modern HLS toolchain installed and set up the project repo.
Nothing measured today counts -- this is infrastructure week.

## What I did
- Checked the existing FPGA toolchain on my machine: Vivado 2015.4.
  Decided against using it (see Decisions).
- Started the install of Vivado ML Standard 2025.2 via the AMD Unified
  Web Installer.
  - Components selected: Vivado Design Suite (includes Vitis HLS), DocNav,
    cable drivers, license management.
  - Deselected: Vitis Model Composer, Vitis Embedded Development,
    Power Design Manager.
  - Device families selected: 7 Series, SoCs (Zynq-7000).
- Created the project repo `hls-llm-study` and pushed the harness scaffold
  to GitHub (private). 10 files, first commit 5239d77.
  - Structure: kernels/, scripts/, results/, notebook/
  - Contains a throwaway `vecadd` kernel used only to prove the flow works.
- Read through every file in the scaffold so I can explain what each one
  does: the .h is the contract between kernel and testbench, the .cpp is
  the naive (pragma-free) design, the testbench is the correctness gate,
  run_hls.tcl drives the tool in batch mode, extract_metrics.py turns the
  report XML into one CSV row, the Makefile ties it together.

## What broke / what surprised me
- Nothing broke, but two naming traps cost time:
  - Vitis HLS ships *inside* the Vivado install, not under "Vitis Core
    Development Kit". Selecting Vitis would have pulled the wrong product.
  - "Vitis Embedded Installer" on the Stand-Alone tab is unrelated to HLS.
- Had to reset my AMD account password before the installer would
  authenticate.

## Numbers recorded
None. results.csv is still empty. Expected -- no kernel has been
synthesized yet.

## Decisions made
- **Not using Vivado 2015.4.** An LLM will emit modern pragmas
  (`pipeline II=`, `dataflow`, `bind_op`, current ap_fixed idioms) that a
  2015-era tool does not support. Since functional-failure rate of
  LLM-generated designs is a headline metric, running on 2015.4 would
  measure tool-version mismatch rather than LLM optimization ability.
  That would be a fatal confound.
- **Targeting 2025.2, not 2026.1.** From 2026.1 AMD replaced the free
  Vivado ML Standard edition with a Design Edition + free "Vivado Basic"
  license. 2025.2 is the last release using the well-documented free
  Standard path.
- **Not buying an FPGA board for the research.** All metrics in the study
  come from synthesis and implementation reports; no result depends on
  physical hardware. Board-level power measurement would require per-rail
  current sensing and realistic stimulus -- a separate project that would
  consume the weeks budgeted for the actual experiment. May buy a board
  separately for learning, kept outside research hours.

## Open questions
- **Lab board / part number unknown.** Blocks the week 3 part selection.
  Need to check what the ECE lab actually has before targeting a device.
- Part choice should be driven by whether the optimization space is
  interesting (enough DSPs that aggressive unrolling doesn't hit a wall),
  not by what hardware I happen to own.
- Repo currently lives on the Desktop. If that path is OneDrive-synced,
  move it before running synthesis -- sync locking build files mid-run
  causes hard-to-diagnose failures.

## Next session starts with
1. `vitis_hls -version` to confirm the install and PATH work.
2. `make bench KERNEL=vecadd PART=<placeholder>` -- prove the flow runs
   end to end and writes one row to results.csv. Numbers are throwaway.
3. Deliberately break the testbench golden answer, confirm the run fails
   and writes NO row, then revert. An untested gate is not a gate.

---
Tool versions: Vitis HLS 2025.2 (installing)  Vivado 2025.2 (installing)
Part number: NOT YET SELECTED
