# Batch-mode Vitis HLS run. No GUI, ever.
#
# Usage:
#   vitis_hls -f run_hls.tcl -tclargs <top> <src.cpp> <tb.cpp> <part> <period_ns> <proj_dir>

set top      [lindex $argv 0]
set src      [lindex $argv 1]
set tb       [lindex $argv 2]
set part     [lindex $argv 3]
set period   [lindex $argv 4]
set proj_dir [lindex $argv 5]

open_project -reset $proj_dir
set_top $top
add_files $src
add_files -tb $tb

open_solution -reset "solution1" -flow_target vivado
set_part $part
create_clock -period $period -name default

# 1. Correctness gate. If the testbench returns non-zero, this errors out
#    and synthesis below never runs.
csim_design

# 2. Synthesis. Produces the latency / resource report we parse.
csynth_design

close_project
exit
