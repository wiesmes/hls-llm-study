# One command in, one CSV row out.
#
#   make bench KERNEL=vecadd
#
# EDIT PART BELOW before your first run. Everything is meaningless without it.

PART   ?= xc7a100tcsg324-1     # <-- REPLACE with your lab board's part number
PERIOD ?= 10                   # target clock period in ns (10ns = 100 MHz)

KERNEL ?= vecadd
LABEL  ?= $(KERNEL)_naive

KDIR   := kernels/$(KERNEL)
SRC    := $(KDIR)/$(KERNEL).cpp
TB     := $(KDIR)/tb_$(KERNEL).cpp
PROJ   := build/$(KERNEL)_$(LABEL)
CSV    := results/results.csv

.PHONY: bench clean check-part

bench: check-part
	@mkdir -p build results
	vitis_hls -f scripts/run_hls.tcl -tclargs \
		$(KERNEL) $(SRC) $(TB) $(PART) $(PERIOD) $(PROJ)
	python3 scripts/extract_metrics.py $(PROJ) $(KERNEL) $(LABEL) $(CSV)

check-part:
	@if [ "$(PART)" = "xc7a100tcsg324-1" ]; then \
		echo ">>> WARNING: PART is still the placeholder. Confirm your board's"; \
		echo ">>> actual part number and update the Makefile before trusting"; \
		echo ">>> any resource or power numbers."; \
	fi

clean:
	rm -rf build vitis_hls.log *.log
