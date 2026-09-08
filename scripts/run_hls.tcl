# Batch-mode Vitis HLS run. No GUI, ever.
#
# Usage (called by the Makefile, which sets these environment variables):
#   HLS_TOP HLS_SRC HLS_TB HLS_PART HLS_PERIOD HLS_PROJ
#   vitis-run --mode hls --tcl scripts/run_hls.tcl

set top      $::env(HLS_TOP)
set src      $::env(HLS_SRC)
set tb       $::env(HLS_TB)
set part     $::env(HLS_PART)
set period   $::env(HLS_PERIOD)
set proj_dir $::env(HLS_PROJ)

# Absolute paths everywhere. HLS mangles relative paths for nested
# project directories and silently drops the design file from csim.
open_component -reset [file normalize $proj_dir] -flow_target vivado
set_top $top
add_files [file normalize $src]
add_files -tb [file normalize $tb]
set_part $part
create_clock -period $period -name default

# 1. Correctness gate.
csim_design

# 2. Synthesis.
csynth_design

close_component
exit