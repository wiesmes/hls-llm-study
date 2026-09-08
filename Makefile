# One command in, one CSV row out.
#
#   make bench KERNEL=vecadd
#
# Requires vitis-run (Vivado/Vitis 2025.2) and GNU make on PATH.

# Arty Z7-20 (Zynq-7020, CLG400 package)
PART   ?= xc7z020clg400-1
# target clock period in ns (10ns = 100 MHz)
PERIOD ?= 10

KERNEL ?= vecadd
LABEL  ?= $(KERNEL)_naive

KDIR   := kernels/$(KERNEL)
SRC    := $(KDIR)/$(KERNEL).cpp
TB     := $(KDIR)/tb_$(KERNEL).cpp
PROJ   := build/$(KERNEL)_$(LABEL)
CSV    := results/results.csv

.PHONY: bench clean check-part

# HLS 2025.2 rewrites the design-file path relative to the project dir but
# resolves it from the working dir, so we must run from inside the project.
# PROJ is always build/<name>, hence the fixed ../../ prefixes.
bench: check-part
	@mkdir -p $(PROJ) results
	cd $(PROJ) && \
	HLS_TOP=$(KERNEL) HLS_SRC=../../$(SRC) HLS_TB=../../$(TB) HLS_PART=$(PART) \
	HLS_PERIOD=$(PERIOD) HLS_PROJ=. \
	vitis-run --mode hls --tcl ../../scripts/run_hls.tcl
	py scripts/extract_metrics.py $(PROJ) $(KERNEL) $(LABEL) $(CSV)
	
check-part:
	@if [ "$(PART)" = "xc7a100tcsg324-1" ]; then \
		echo ">>> WARNING: PART is still the placeholder. Confirm your board's"; \
		echo ">>> actual part number and update the Makefile before trusting"; \
		echo ">>> any resource or power numbers."; \
	fi

clean:
	rm -rf build vitis_hls.log *.log