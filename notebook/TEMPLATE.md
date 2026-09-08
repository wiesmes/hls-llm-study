# Session: 2026-09-08 (Tue)

## Goal for today
Identify the lab board, get a working 2025.2 toolchain, and prove the
harness runs end to end on `vecadd`.

## What I did
- Received the lab board from Prof. Naher: **Digilent Arty Z7-20**
  (chip marking ZYNQ-7000 / 20 / CLG400). Part number is
  `xc7z020clg400-1`. Same Zynq-7020 silicon as the Zedboard in a
  different package. The Artix-7 concern from last week is moot.
- Got admin rights on the lab machine.
- Found that the 2026-09-03 install had only produced an empty stub at
  `C:\Xilinx\2025.2\Vitis\bin` (no admin rights at the time). Reinstalled
  Vivado ML Standard 2025.2 cleanly to `C:\AMDDesignTools\2025.2`.
  - Selected: Vivado, Vitis HLS, cable drivers. Zynq-7000 devices only.
  - Deselected: Vitis Model Composer, DocNav, license management,
    all other device families. ~17 GB download, ~45 GB on disk.
- Installed GNU Make 3.81 via `winget install GnuWin32.Make` (Git Bash
  does not ship `make`).
- Found three Pythons already installed (3.10, 3.13, 3.14) but none on
  PATH for Git Bash. Using the `py` launcher instead of `python3`.
- Cloned `Digilent/vivado-boards` (shallow) for the Arty Z7-20 board
  files. Not yet copied into the Vivado install.
- Ported `run_hls.tcl` and the Makefile to the 2025.2 command set
  (see Decisions). First successful `make bench KERNEL=vecadd`.
- Built the same `vecadd` component in the Vitis Unified IDE to see the
  report and schedule viewer. Confirmed identical results to the batch
  flow. The IDE workspace is `C:\Users\wwa228\vitis_ws`, outside the repo.

## What broke / what surprised me
- **`vitis_hls` no longer exists in 2025.2.** HLS is invoked as
  `vitis-run --mode hls --tcl <script>`, from `<install>\Vitis\bin`, even
  with a Vivado-only install. Last week's note about "Vitis HLS ships
  inside Vivado" was right about the installer checkbox and wrong about
  the binary.
- **`vitis-run` does not forward `-tclargs`.** `$argv` inside the script
  holds the launcher's own flags. Switched to passing the six inputs as
  environment variables and reading them with `$::env(...)`.
- **HLS silently drops the design file from csim** when the project
  directory is nested (`build/<name>`). It rewrites `syn.file` relative to
  the project dir but resolves it from the working dir, so
  `../../kernels/...` points nowhere and the testbench links against
  nothing. Absolute paths in `add_files` did not help; the rewrite happens
  after. Workaround: `cd` into the project dir before calling `vitis-run`,
  with `HLS_PROJ=.` and `../../` prefixes on the source paths. Cost about
  90 minutes to isolate.
- The classic `open_project` / `open_solution` flow still runs but warns
  it is unsupported for IDE use. Moved to `open_component`, which writes
  `hls/` instead of `solution1/`. `extract_metrics.py` found the report
  without changes.
- The IDE's "Open Summary Folder" doubles the path when pointed at a
  component it did not create. Building a fresh component inside the
  IDE works fine.
- Git Bash `HOME` is set to `AppData\Roaming\SPB_Data` by some Cadence
  tool, so `~` is not my user folder. Use `/c/Users/wwa228` explicitly.

## Numbers recorded
First row in `results/results.csv`, label `vecadd_naive`,
part `xc7z020clg400-1`, 10 ns clock:

| latency_max | interval_min | lut | ff | bram | dsp | est. Fmax |
|---|---|---|---|---|---|---|
| 262 | 256 | 492 | 297 | 0 | 2 | 137.82 MHz |

Note: HLS auto-pipelined the loop to II=1 with no pragmas present. The
"naive" baseline is less naive than the source comment claims. Ports came
out as `ap_memory`, which the Zynq PS cannot drive.

## Decisions made
- **Part locked: `xc7z020clg400-1`.** Driven by the board the lab
  provided, and it happens to be the 220-DSP device I wanted.
- **Research kernel: fixed-size GEMM.** Hand-optimized first as the human
  baseline, then the LLM loop. Deepest pragma space of any ML kernel,
  documented baselines on Zynq-7020, trivial correctness check against
  NumPy. Conv2D is the fallback. `dot` is a warm-up only.
- **Prof. Naher's first milestone: `vecadd` running on the board by
  Thursday 2026-09-11.** Board bring-up is now on the path, not a side
  activity.
- **Software side for the board demo: PYNQ**, not bare-metal Vitis.
  Boots Linux + Jupyter from microSD; loading a bitstream and calling the
  IP is a few lines of Python. Bare-metal over JTAG is plan B if no SD
  card materializes.
- **Vitis IDE is for reports only.** All builds that produce numbers go
  through `make bench`. Nothing in `vitis_ws` is authoritative.

## Open questions
- Need a microSD card (8 GB+), a USB card reader, a micro-USB data cable,
  and a network path to the board (USB-Ethernet adapter or lab switch).
  Emailed Prof. Naher. A friend's Zedboard kit has the card and cable.
- Power measurement is still undecided. If it becomes a fight, drop to
  latency + resource and note power as future work.
- API credits, compute access, venue, and grading are still unasked.
  Waiting for the Thursday meeting.
- `check-part` in the Makefile still compares against the old
  `xc7a100tcsg324-1` placeholder. Harmless, but it no longer guards
  anything. Fix or delete.

## Next session starts with
1. Add AXI interface pragmas to `vecadd.cpp` (`m_axi` on a/b/c,
   `s_axilite` on control). Run with `LABEL=vecadd_axi` so the naive
   row stays clean. Confirm the log shows `m_axi` / `s_axilite`.
2. Package the IP (`export_design -format ip_catalog`, or the Package
   step in the IDE). Output: `<component>/hls/impl/ip`.
3. Copy `vivado-boards/new/board_files/arty-z7-20` into
   `C:\AMDDesignTools\2025.2\Vivado\data\boards\board_files`.
4. Vivado: new project on Arty Z7-20, add IP repo, block design with
   Zynq PS + vecadd, connection automation, wrapper, bitstream.
   Collect `.bit` and `.hwh`.
5. Flash the PYNQ Arty Z7-20 image to the SD card once one exists.
6. Still owed from last week: deliberately break the golden answer and
   confirm `make bench` writes no row.

---
Tool versions: Vivado ML Standard 2025.2, HLS via `vitis-run` 2025.2,
GNU Make 3.81 (GnuWin32), Python via `py` launcher
Install root: `C:\AMDDesignTools\2025.2`
Part number: `xc7z020clg400-1` (Arty Z7-20)
PATH line for Git Bash:
`export PATH="/c/Program Files (x86)/GnuWin32/bin:/c/AMDDesignTools/2025.2/Vitis/bin:/c/AMDDesignTools/2025.2/Vivado/bin:$PATH"`








# Session: 2026-09-03 (Wed)

> Corrections added 2026-09-08 are marked **[corrected]**. The original
> reasoning is kept because the mistakes are instructive.

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
  - **[corrected]** This install never completed. Without admin rights it
    left an empty `C:\Xilinx\2025.2\Vitis\bin` and nothing else. Redone
    on 2026-09-08 to `C:\AMDDesignTools\2025.2`.
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
    **[corrected]** Right checkbox, wrong conclusion about the binary:
    in 2025.2 there is no `vitis_hls` executable at all. HLS runs as
    `vitis-run --mode hls`.
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
  **[corrected]** Still not buying one, but the lab provided an Arty Z7-20
  and Prof. Naher wants a board demo first, so bring-up is on the path
  after all. The point about power measurement stands.

## Open questions
- **Lab board / part number unknown.** Blocks the week 3 part selection.
  Need to check what the ECE lab actually has before targeting a device.
  **[corrected]** Resolved 2026-09-08: Arty Z7-20, `xc7z020clg400-1`.
- Part choice should be driven by whether the optimization space is
  interesting (enough DSPs that aggressive unrolling doesn't hit a wall),
  not by what hardware I happen to own.
- Repo currently lives on the Desktop. If that path is OneDrive-synced,
  move it before running synthesis -- sync locking build files mid-run
  causes hard-to-diagnose failures.
  **[corrected]** Desktop is local, not OneDrive-synced. Builds ran fine.
  The Vitis IDE workspace initially landed in OneDrive and was moved.

## Next session starts with
1. `vitis_hls -version` to confirm the install and PATH work.
   **[corrected]** No such binary. The equivalent check is
   `which vitis-run`.
2. `make bench KERNEL=vecadd PART=<placeholder>` -- prove the flow runs
   end to end and writes one row to results.csv. Numbers are throwaway.
   **[corrected]** Done 2026-09-08, with the real part.
3. Deliberately break the testbench golden answer, confirm the run fails
   and writes NO row, then revert. An untested gate is not a gate.
   **[corrected]** Still not done. Carried forward.

---
Tool versions: Vitis HLS 2025.2 (installing)  Vivado 2025.2 (installing)
Part number: NOT YET SELECTED