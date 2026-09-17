# Setup and Validation Record

HLS + LLM Independent Study, Fall 2026
Advisor: Prof. Naher
Period covered: September 3 to September 17, 2026

This file records everything built and measured before the research kernel
(GEMM) was started. It is the source for the paper's methods, setup, and
validation sections.

---

## 1. Research question

To what extent can a large language model generate and iteratively optimize
High-Level Synthesis (HLS) implementations of ML inference kernels, using FPGA
synthesis feedback (latency, resource utilization, power) as its signal?

The distinguishing feature from prior LLM-for-HLS work is the closed loop
(synthesis report back into the prompt) and a human-optimized baseline written
by the same person under the same tool constraints.

## 2. Experimental design

One kernel: fixed-size general matrix multiply (GEMM), 32x32 int16 to start,
scaling to 64x64.

Four arms, all evaluated through the same pipeline:

| Arm | Description | Author |
|---|---|---|
| 1. Naive | Triple loop, interface pragmas only, no compute pragmas | Human |
| 2. Hand-optimized | Iterated against synthesis reports until plateau | Human |
| 3. LLM zero-shot | Naive code in, one optimized version out, no feedback | LLM |
| 4. LLM with feedback | Naive code in; synthesize; feed metrics back; revise; repeat N rounds | LLM |

Arm 2 is completed before arms 3 and 4 are run, so the human baseline is
independent of LLM output.

Every design point from every arm produces one row in `results/results.csv`.
No metric is recorded by hand.

### Pragma boundary

All kernels carry identical AXI interface pragmas (`m_axi` on array ports with
separate bundles, `s_axilite` on scalar ports and `return`). These are fixed
plumbing and are outside the optimization space. "Naive" means no compute
pragmas: no `PIPELINE`, `UNROLL`, `ARRAY_PARTITION`, `DATAFLOW`, or
`LOOP_FLATTEN`. Only compute pragmas and loop structure may differ between arms.

## 3. Target hardware

| Item | Value |
|---|---|
| Board | Digilent Arty Z7-20 |
| Device | AMD Zynq-7020, part `xc7z020clg400-1` |
| Processing system | Dual ARM Cortex-A9, 512 MB DDR3 |
| Programmable logic | 53,200 LUTs, 106,400 FFs, 220 DSP48, 140 BRAM (36 Kb) |
| Clock target for HLS | 10 ns (100 MHz), `PERIOD=10` in the Makefile |
| Host connection | Micro-USB (JTAG + UART), no Ethernet |

Board received from Prof. Naher on September 8, 2026.

## 4. Toolchain

| Tool | Version | Location |
|---|---|---|
| Vivado ML Standard | 2025.2 | `C:\AMDDesignTools\2025.2` |
| Vitis HLS (unified IDE) | 2025.2 | same |
| Vitis Embedded Development | 2025.2 | `C:\Users\wwa228\Desktop\2025.2` (added Sep 15) |
| GNU Make | GnuWin32 | Windows PATH |
| Python | 3.14 via `py` launcher | for `extract_metrics.py` and pyserial |
| Serial terminal | pyserial `miniterm` | `py -m serial.tools.miniterm COM7 115200` |

Vivado 2015.4 was considered and rejected on September 3 because it predates
Vitis HLS and its device support and report formats differ from current tools.

### 2025.2-specific workarounds (recorded because they cost time)

1. There is no `vitis_hls` executable. HLS runs in batch mode as
   `vitis-run --mode hls --tcl scripts/run_hls.tcl`.
2. `-tclargs` is not forwarded to the Tcl script. The Makefile passes kernel
   name, part, period, and label as environment variables; the Tcl reads them
   with `$::env(...)`.
3. The Tcl uses the `open_component` flow. Outputs land under `hls/`; synthesis
   reports under `hls/syn/report/`.
4. HLS relativizes the `syn.file` setting and silently drops the design file
   from C simulation when the project directory is nested. The Makefile works
   around this by running `vitis-run` from inside the project directory.
5. Export Hardware from the Vivado GUI fails with "Unable to get BIN file" when
   "Include bitstream/binary" is selected, because Zynq-7000 runs produce only
   a `.bit`. The `.xsa` was written from the Tcl console instead:
   `write_hw_platform -fixed -include_bit -force -file <path>.xsa`
6. The Vitis Unified IDE serial monitor would not open on this machine.
   pyserial's miniterm was used instead.
7. The initial Vitis install (Vivado ML Standard edition) does not include
   Vitis Embedded Development, so no Platform or Application components were
   available. Added via `xsetup.exe` > Add Design Tools or Devices > upgrade to
   Vitis Unified Software Platform > tick Vitis Embedded Development. Required
   admin rights.

## 5. Measurement pipeline

Repository: `wiesmes/hls-llm-study` (private).

```
kernels/<name>/              kernel .cpp, header, testbench
scripts/run_hls.tcl          batch Vitis HLS driver
scripts/extract_metrics.py   report XML -> one CSV row
results/results.csv          every design point ever measured
notebook/                    one file per work session
```

Command: `make bench KERNEL=<name> [LABEL=<label>]`

Flow per invocation:

1. `csim_design`: compile kernel and testbench with g++, run. The testbench
   returns non-zero on any mismatch against a plain C reference, which fails
   csim and aborts the flow. This is the correctness gate.
2. `csynth_design`: synthesize to RTL, produce `csynth.xml`.
3. `extract_metrics.py`: parse timing, latency, interval, and resource fields
   into a CSV row with a timestamp and label.

A design that computes the wrong answer never reaches synthesis and never
produces a row. This is deliberate: a wrong design can have excellent latency.

### CSV schema

```
label, timestamp, top, part, target_period_ns, estimated_period_ns,
latency_min, latency_max, interval_min, lut, ff, bram, dsp, uram
```

### Validation kernel: vecadd

`vecadd` adds two 256-element float arrays. It exists only to prove the
pipeline works end to end and to bring up the board. It is not part of the
study and its numbers are not a baseline for GEMM.

First pipeline row, September 8, 2026:

| Field | Value | Meaning |
|---|---|---|
| target_period_ns | 10.00 | requested 100 MHz clock |
| estimated_period_ns | 7.256 | tool estimates the circuit could run at ~138 MHz |
| latency_min / max | 262 / 262 | one call takes 262 cycles (256 loop + 6 overhead), 2.62 us at 100 MHz |
| interval_min | 256 | a new call can start every 256 cycles; calls do not overlap |
| lut | 492 | 0.9% of the device |
| ff | 297 | 0.3% of the device |
| bram | 0 | arrays live in DDR, not on-chip |
| dsp | 2 | used by the floating-point adder |
| uram | 0 | device has none |

Interpretation: the naive vecadd already achieves one addition per cycle,
which is the ceiling without unrolling, and unrolling would be bound by DDR
bandwidth. There is effectively no optimization space, which is why vecadd is a
pipeline test and not a research kernel.

## 6. Board deployment (vecadd)

Goal set by Prof. Naher: show a synthesized HLS kernel running on the physical
board.

### Hardware flow (September 8 and 15)

1. Added interface pragmas to `vecadd.cpp` and re-synthesized.
2. `export_design -format ip_catalog` packaged the kernel as an IP at
   `vitis_ws\vecadd\vecadd\hls\impl\ip`.
3. Vivado project `C:\Users\wwa228\vivado_ws\vecadd_arty`, board files for
   Arty Z7-20 from the Vivado board store.
4. Block design `design_1`: Zynq7 Processing System (board preset, M_AXI_GP0
   and S_AXI_HP0 enabled, FCLK_CLK0 at 100 MHz), `vecadd_0`, AXI interconnects
   from connection automation. Control path: PS GP0 to `vecadd_0/s_axi_control`.
   Data path: `vecadd_0/m_axi_gmem0/1/2` to PS HP0 to DDR.
5. Address map: `vecadd_0/s_axi_control` at `0x40000000`, range 64 KB.
6. Synthesis, implementation, bitstream. Timing met: WNS +1.314 ns at 100 MHz.
7. `.xsa` exported with bitstream (see workaround 5).
8. Bitstream programmed over JTAG from Vivado Hardware Manager. Log line:
   `INFO: [Labtools 27-3164] End of startup status: HIGH` (DONE asserted).

### Software flow (September 15 to 17)

1. Vitis platform component from `design_1_wrapper.xsa`, OS standalone,
   processor `ps7_cortexa9_0`. The platform build picked up the HLS-generated
   `xvecadd` driver automatically (`xvecadd.h`, `xvecadd_hw.h` in the platform
   include directory) and defined `XPAR_XVECADD_0_BASEADDR 0x40000000`.
2. Application `Hello`: first a UART Hello World (confirmed over COM7), then
   `main.c` replaced with the vecadd driver program.
3. Driver program structure: fill `a[i]=i`, `b[i]=10i`, `c[i]=-1` in DDR;
   `Xil_DCacheFlushRange` on all three; `XVecadd_Set_a/b/c` with the DDR
   addresses; `XVecadd_Start`; poll `XVecadd_IsDone`;
   `Xil_DCacheInvalidateRange` on `c`; compare against `a[i]+b[i]` on the ARM.

### Result (September 17, 2026)

```
vecadd on Arty Z7-20
started
c[0] = 0
c[1] = 11
c[2] = 22
c[3] = 33
c[4] = 44
...
c[255] = 2805
PASS: all 256 results match
```

All 256 outputs computed by the accelerator matched the ARM reference.

### Known issue

On September 16 the same program hung after printing its header, stuck polling
`ap_done`. On September 17 it passed without code changes other than added
diagnostic prints. Cause not determined. Candidates: a stuck AXI transaction
from an earlier run cleared by power cycle, or the board mid-way through the
factory QSPI demo when Vitis took over. Repeat runs should be done before
trusting stability. The Address Editor mapping of all three `m_axi_gmem` ports
to `HP0_DDR_LOWOCM` has not been visually verified.

## 7. What the board is for in this study

Metrics for all four arms come from synthesis reports via `make bench`. The
board is used (a) once at the end to run the final hand-optimized and
LLM-optimized GEMM on silicon and confirm correctness, and (b) as a bug check
if an LLM design passes simulation and synthesis but is suspected of an
interface-level fault. Interface hangs and cache-coherence faults are not
visible in synthesis reports; vecadd's September 16 hang is an example of the
class.

## 8. Open items

- Power measurement is not wired up. Needs Vivado implementation plus
  `report_power` with a SAIF from RTL co-simulation.
- `extract_metrics.py` still targets the older `solution1/` report path and
  must be moved to `hls/syn/report/`.
- Deliberately break the vecadd testbench, confirm the flow fails and writes no
  row, restore. Not yet done.
- Commit `main.c` (board driver) to the repo.
- Verify the Address Editor mapping for the three `gmem` ports.

## 9. Session log

| Date | Work |
|---|---|
| Sep 3 | Research question, four-arm design, repo scaffold, decided against Vivado 2015.4 |
| Sep 8 | Toolchain installed and worked around; first CSV row; board received; interface pragmas; IP export; block design; bitstream |
| Sep 12 | Board parts (SD card, 12 V adapter); board powers on with factory demo |
| Sep 15 | Bitstream regenerated; `.xsa` exported; JTAG programming; Vitis Embedded installed; platform built; Hello World over UART |
| Sep 16 | vecadd driver program hangs polling `ap_done` |
| Sep 17 | vecadd driver program passes, 256/256 correct |